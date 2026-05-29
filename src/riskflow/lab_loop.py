from __future__ import annotations

import json
import math
import shutil
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .baskets import build_equal_weight_return_index_frame
from .compression import calculate_compression_features
from .config import UniverseConfig, load_universe_config
from .data_loader import load_universe_ohlcv
from .grammar_search import (
    GRAMMAR_SEARCH_MODEL,
    run_grammar_search,
    strict_baseline_referee,
    timeframe_cooldown,
)
from .indicator_engine import calculate_indicator
from .mtf import normalize_timeframe
from .reports import export_grammar_search_reports
from .signal_grammar import calculate_signal_grammar_features
from .setup_quality import calculate_setup_quality
from .states import classify_state_frame


LAB_LOOP_MODEL = "riskflow_lab_loop_runner_v0"
DEFAULT_QUEUE_PATH = Path("research/lab_loop/hypothesis_queue.yaml")
DEFAULT_RUNTIME_QUEUE_PATH = Path("research/lab_loop/runtime_queue.yaml")
DEFAULT_STATE_PATH = Path("research/lab_loop/lab_state.json")
DEFAULT_FAILURE_LOG_PATH = Path("research/lab_loop/failure_log.jsonl")
DEFAULT_LOCK_PATH = Path("research/lab_loop/lab_loop.lock")
DEFAULT_REPORT_ROOT = Path("reports/lab_loop")
DEFAULT_GENERATED_GRID_DIR = Path("research/lab_loop/generated_grids")

TERMINAL_STATUSES = {"promoted", "demoted", "archived", "failed", "blocked_by_evidence"}
RUNNABLE_STATUSES = {"new", "encoded", "tested", "tested_needs_fresh_data", "needs_encoding"}


@dataclass(frozen=True)
class LabLoopOptions:
    queue_path: Path = DEFAULT_QUEUE_PATH
    runtime_queue_path: Path = DEFAULT_RUNTIME_QUEUE_PATH
    state_path: Path = DEFAULT_STATE_PATH
    lock_path: Path = DEFAULT_LOCK_PATH
    report_root: Path = DEFAULT_REPORT_ROOT
    generated_grid_dir: Path = DEFAULT_GENERATED_GRID_DIR
    config_path: Path = Path("configs/meme_universe.yaml")
    data_dir: Path = Path("data/raw")
    timeframes: tuple[str, ...] = ("1d", "12h", "4h", "1h")
    max_loops: int = 1
    max_hours: float | None = None
    min_sample_size: int = 20
    entry_lag_bars: int = 1
    cooldown_bars: int | None = None
    strict_referee: bool = True
    strict_null_iterations: int = 300
    strict_random_seed: int = 29
    resume: bool = False
    dry_run: bool = False


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(path)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def atomic_write_yaml(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, yaml.safe_dump(payload, sort_keys=False))


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{source} must contain a YAML mapping")
    return data


def load_lab_queue(path: str | Path = DEFAULT_QUEUE_PATH) -> dict[str, Any]:
    data = load_yaml_file(path)
    errors = validate_lab_queue(data)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid lab queue {path}: {joined}")
    return data


def validate_lab_queue(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("model") != "riskflow_lab_loop_hypothesis_queue_v0":
        errors.append("model must be riskflow_lab_loop_hypothesis_queue_v0")
    queue = data.get("queue")
    if not isinstance(queue, list):
        errors.append("queue must be a list")
        return errors

    seen_ids: set[str] = set()
    for index, item in enumerate(queue):
        label = f"queue[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        item_id = item.get("id")
        if not item_id or not isinstance(item_id, str):
            errors.append(f"{label}.id is required")
        elif item_id in seen_ids:
            errors.append(f"{label}.id duplicates {item_id}")
        else:
            seen_ids.add(item_id)
        if item.get("track") not in {"bullish_setup", "warning", "gradient_translation", "mtf_context"}:
            errors.append(f"{label}.track is invalid")
        if not item.get("status"):
            errors.append(f"{label}.status is required")
        if "priority" not in item:
            errors.append(f"{label}.priority is required")
        if not item.get("hypothesis"):
            errors.append(f"{label}.hypothesis is required")
        primitives = item.get("measurable_primitives", [])
        if primitives is not None and not isinstance(primitives, list):
            errors.append(f"{label}.measurable_primitives must be a list")
    return errors


def initialize_runtime_queue(options: LabLoopOptions) -> dict[str, Any]:
    if options.resume and options.runtime_queue_path.exists():
        return load_lab_queue(options.runtime_queue_path)
    queue = load_lab_queue(options.queue_path)
    queue["runtime_source_queue"] = str(options.queue_path)
    queue["runtime_created_at"] = utc_now_iso()
    atomic_write_yaml(options.runtime_queue_path, queue)
    return queue


def load_lab_state(path: str | Path = DEFAULT_STATE_PATH) -> dict[str, Any]:
    state_path = Path(path)
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def data_fingerprint(data_dir: str | Path, timeframes: tuple[str, ...]) -> str:
    root = Path(data_dir)
    rows: list[str] = []
    for timeframe in timeframes:
        for path in sorted(root.glob(f"*_{timeframe}.csv")):
            stat = path.stat()
            rows.append(f"{path.name}:{stat.st_size}:{int(stat.st_mtime)}")
    return str(abs(hash("|".join(rows))))


def select_next_hypothesis(queue: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any] | None:
    state = state or {}
    completed_ids = set(state.get("completed_hypothesis_ids", []))
    active_loop_number = int(state.get("last_completed_loop", 0)) + 1
    candidates: list[dict[str, Any]] = []
    for item in queue.get("queue", []):
        status = str(item.get("status", "new"))
        if status in TERMINAL_STATUSES:
            continue
        if status not in RUNNABLE_STATUSES and "source" not in item:
            continue
        if item.get("id") in completed_ids:
            continue
        cooldown_until = item.get("cooldown_until_loop")
        if cooldown_until is not None and int(cooldown_until) > active_loop_number:
            continue
        candidates.append(item)
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda item: (
            0 if is_executable_hypothesis(item) else 1,
            int(item.get("priority", 9999)),
            int(item.get("generation", 0)),
        ),
    )[0]


def is_executable_hypothesis(hypothesis: dict[str, Any]) -> bool:
    source = hypothesis.get("source")
    return bool(source) and Path(str(source)).suffix.lower() in {".yaml", ".yml"}


def load_analysis_frames_by_timeframe(
    *,
    config_path: str | Path,
    data_dir: str | Path,
    timeframes: tuple[str, ...],
) -> tuple[Any, dict[str, dict[str, pd.DataFrame]], list[str]]:
    universe = load_universe_config(config_path)
    analysis_by_timeframe: dict[str, dict[str, pd.DataFrame]] = {}
    warnings: list[str] = []
    for timeframe in timeframes:
        raw_frames, load_warnings = load_universe_ohlcv(universe, data_dir=data_dir, timeframe=timeframe)
        warnings.extend(f"{timeframe}: {warning}" for warning in load_warnings)
        if not raw_frames:
            warnings.append(f"{timeframe}: no usable CSV files found in {Path(data_dir)}")
            analysis_by_timeframe[timeframe] = {}
            continue
        analysis_frames, _basket, analysis_warnings = build_lab_analysis_frames(universe, raw_frames)
        warnings.extend(f"{timeframe}: {warning}" for warning in analysis_warnings)
        analysis_by_timeframe[timeframe] = analysis_frames
    return universe, analysis_by_timeframe, warnings


def build_lab_analysis_frames(
    universe: UniverseConfig,
    raw_frames: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], pd.Series, list[str]]:
    """Build enough analysis columns for grammar-search without importing CLI helpers."""
    warnings: list[str] = []
    closes = {symbol: frame["close"] for symbol, frame in raw_frames.items()}
    basket_frame = build_equal_weight_return_index_frame(
        closes,
        min_active_members=universe.min_active_members,
        name=universe.benchmark.name,
    )
    basket = basket_frame["basket_index"].rename(universe.benchmark.name)
    if basket.dropna().empty:
        warnings.append(
            f"Benchmark {universe.benchmark.name} has no valid values. "
            f"Check min_active_members={universe.min_active_members} and CSV overlap."
        )

    analysis_frames: dict[str, pd.DataFrame] = {}
    for asset in universe.assets:
        raw = raw_frames.get(asset.symbol)
        if raw is None:
            continue
        indicator = calculate_indicator(
            raw["close"],
            basket,
            settings=universe.indicator_settings,
            weights=universe.weights,
        )
        indicator["benchmark_used"] = universe.benchmark.name
        indicator["benchmark_name"] = universe.benchmark.name
        compression = calculate_compression_features(raw, settings=universe.compression_settings)
        analysis = indicator.join(compression, how="left")
        analysis["volume"] = raw["volume"].reindex(analysis.index)
        state_details = classify_state_frame(analysis)
        analysis = analysis.join(state_details, how="left")
        setup_quality = calculate_setup_quality(analysis)
        analysis = analysis.join(setup_quality, how="left")
        grammar_features = calculate_signal_grammar_features(analysis)
        analysis = analysis.join(grammar_features, how="left")
        if "opportunity_score_v0" in analysis.columns:
            analysis["opportunity_score"] = analysis["opportunity_score_v0"]
        analysis_frames[asset.symbol] = analysis

    return analysis_frames, basket, warnings


def useful_rows(ranked: pd.DataFrame) -> pd.DataFrame:
    if ranked.empty or "classification" not in ranked.columns:
        return pd.DataFrame()
    return ranked[ranked["classification"].isin(["useful", "watchlist"])].copy()


def strict_survivor_rows(strict_referee: pd.DataFrame) -> pd.DataFrame:
    if strict_referee.empty or "strict_survivor" not in strict_referee.columns:
        return pd.DataFrame()
    return strict_referee[strict_referee["strict_survivor"] == True].copy()  # noqa: E712


def decide_loop_outcome(ranked: pd.DataFrame, strict_referee: pd.DataFrame | None = None) -> dict[str, Any]:
    strict_referee = strict_referee if strict_referee is not None else pd.DataFrame()
    survivors = strict_survivor_rows(strict_referee)
    useful = useful_rows(ranked)
    if not survivors.empty:
        return {
            "decision": "promote",
            "promotion_level": "L3_strict_survivor",
            "status": "needs_agent_review",
            "reason": f"{len(survivors)} strict survivor(s)",
            "survivor_count": int(len(survivors)),
            "useful_count": int(len(useful)),
        }
    if not useful.empty:
        return {
            "decision": "refine",
            "promotion_level": "L2_discovered",
            "status": "tested",
            "reason": f"{len(useful)} useful/watchlist variant(s), no strict survivor",
            "survivor_count": 0,
            "useful_count": int(len(useful)),
        }
    return {
        "decision": "archive",
        "promotion_level": "L1_encoded",
        "status": "archived",
        "reason": "no useful/watchlist variants",
        "survivor_count": 0,
        "useful_count": 0,
    }


def parse_params(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _numeric_mutations(key: str, value: int | float) -> list[int | float]:
    if isinstance(value, bool):
        return [value]
    if isinstance(value, int):
        step = max(1, int(round(abs(value) * 0.25)))
        values = [value - step, value, value + step]
        if any(token in key for token in ["window", "lookback", "bars", "count"]):
            values = [max(1, int(candidate)) for candidate in values]
        return sorted(set(int(candidate) for candidate in values))
    if not math.isfinite(float(value)):
        return [value]
    step = max(abs(float(value)) * 0.25, 0.05)
    return sorted({round(float(value) - step, 6), round(float(value), 6), round(float(value) + step, 6)})


def build_refinement_grid(row: pd.Series, *, family_suffix: str) -> dict[str, Any]:
    params = parse_params(row.get("params"))
    params.pop("timeframe", None)
    parameter_grid: dict[str, list[Any]] = {}
    for key, value in params.items():
        if isinstance(value, bool):
            parameter_grid[key] = [value]
        elif isinstance(value, int) and not isinstance(value, bool):
            parameter_grid[key] = _numeric_mutations(key, value)
        elif isinstance(value, float):
            parameter_grid[key] = _numeric_mutations(key, value)
        else:
            parameter_grid[key] = [value]
    return {
        "model": GRAMMAR_SEARCH_MODEL,
        "families": [
            {
                "family_id": f"{row.get('family_id')}_{family_suffix}",
                "direction": row.get("direction"),
                "detector": row.get("detector"),
                "description": f"Autogenerated refinement from lab-loop survivor {row.get('variant_id')}.",
                "parameter_grid": parameter_grid,
            }
        ],
    }


def create_next_hypothesis(
    *,
    queue: dict[str, Any],
    hypothesis: dict[str, Any],
    ranked: pd.DataFrame,
    strict_referee: pd.DataFrame,
    options: LabLoopOptions,
    session_id: str,
    loop_number: int,
) -> dict[str, Any] | None:
    candidates = strict_survivor_rows(strict_referee)
    if candidates.empty:
        candidates = useful_rows(ranked)
    if candidates.empty:
        return None
    candidate = candidates.iloc[0]
    if "params" not in candidate and "variant_id" in candidate and not ranked.empty:
        match = ranked[ranked["variant_id"] == candidate["variant_id"]]
        if not match.empty:
            candidate = match.iloc[0]
    if "params" not in candidate:
        return None

    child_id = f"{hypothesis['id']}_child_{loop_number:04d}"
    existing_ids = {item.get("id") for item in queue.get("queue", [])}
    if child_id in existing_ids:
        return None

    grid = build_refinement_grid(candidate, family_suffix=f"loop_{loop_number:04d}")
    grid_path = options.generated_grid_dir / session_id / f"{child_id}.yaml"
    atomic_write_yaml(grid_path, grid)
    child = {
        "id": child_id,
        "track": hypothesis.get("track", "warning"),
        "status": "new",
        "promotion_level": "L1_encoded",
        "priority": int(hypothesis.get("priority", 100)) + 10,
        "parent_id": hypothesis.get("id"),
        "generation": int(hypothesis.get("generation", 0)) + 1,
        "created_from": "strict_survivor" if not strict_survivor_rows(strict_referee).empty else "useful_variant",
        "mutation_type": "narrow",
        "source": str(grid_path),
        "hypothesis": f"Refine {hypothesis.get('id')} around best current evidence.",
        "measurable_primitives": hypothesis.get("measurable_primitives", []),
        "expected_outcome": hypothesis.get("expected_outcome"),
        "next_action": "Run autogenerated refinement grid and compare against parent evidence.",
    }
    queue.setdefault("queue", []).append(child)
    return child


def update_hypothesis(queue: dict[str, Any], hypothesis_id: str, updates: dict[str, Any]) -> None:
    for item in queue.get("queue", []):
        if item.get("id") == hypothesis_id:
            item.update(updates)
            return
    raise KeyError(f"Unknown hypothesis id: {hypothesis_id}")


def write_loop_summary(
    path: Path,
    *,
    hypothesis: dict[str, Any],
    decision: dict[str, Any],
    ranked: pd.DataFrame,
    strict_referee: pd.DataFrame,
    child: dict[str, Any] | None,
    warnings: list[str],
) -> None:
    top_columns = [
        "variant_id",
        "family_id",
        "timeframe",
        "direction",
        "classification",
        "sample_size",
        "unique_symbols",
        "unique_event_clusters",
        "rank_score",
        "median_forward_relative_return_secondary",
    ]
    top = ranked[[column for column in top_columns if column in ranked.columns]].head(10) if not ranked.empty else pd.DataFrame()
    strict_cols = [
        "variant_id",
        "family_id",
        "timeframe",
        "strict_survivor",
        "matched_null_p_value",
        "matched_null_directional_edge",
    ]
    strict_top = (
        strict_referee[[column for column in strict_cols if column in strict_referee.columns]].head(10)
        if not strict_referee.empty
        else pd.DataFrame()
    )
    lines = [
        f"# Lab Loop Summary: {hypothesis.get('id')}",
        "",
        f"Generated: {utc_now_iso()}",
        f"Track: {hypothesis.get('track')}",
        f"Decision: {decision.get('decision')}",
        f"Promotion Level: {decision.get('promotion_level')}",
        f"Reason: {decision.get('reason')}",
        "",
        "## Hypothesis",
        str(hypothesis.get("hypothesis", "")),
        "",
        "## Top Candidates",
        "```text\n" + top.to_string(index=False) + "\n```" if not top.empty else "_None._",
        "",
        "## Strict Referee",
        "```text\n" + strict_top.to_string(index=False) + "\n```" if not strict_top.empty else "_None._",
        "",
        "## Next Hypothesis",
        child.get("id") if child else "_None generated._",
    ]
    if warnings:
        lines.extend(["", "## Warnings", *[f"- {warning}" for warning in warnings[:25]]])
    atomic_write_text(path, "\n".join(lines) + "\n")


def latest_status_text(state: dict[str, Any]) -> str:
    last = state.get("last_loop_summary", {})
    return "\n".join(
        [
            "# Riskflow Lab Loop Status",
            "",
            f"Updated: {utc_now_iso()}",
            f"Session: {state.get('session_id', '')}",
            f"Status: {state.get('status', '')}",
            f"Last Completed Loop: {state.get('last_completed_loop', 0)}",
            f"Current Hypothesis: {last.get('hypothesis_id', '')}",
            f"Decision: {last.get('decision', '')}",
            f"Reason: {last.get('reason', '')}",
            f"Next Hypothesis: {last.get('next_hypothesis_id', '')}",
            f"Report: {last.get('report_dir', '')}",
            f"Errors: {last.get('errors', 0)}",
            "",
        ]
    )


def append_failure(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def acquire_lock(path: Path) -> str:
    token = uuid.uuid4().hex
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps({"token": token, "created_at": utc_now_iso()}) + "\n")
    except FileExistsError as exc:
        raise RuntimeError(f"lab-loop lock already exists at {path}; another runner may be active") from exc
    return token


def release_lock(path: Path, token: str) -> None:
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if payload.get("token") == token:
        path.unlink()


def run_lab_loop(options: LabLoopOptions) -> dict[str, Any]:
    if options.max_loops < 1:
        raise ValueError("max_loops must be >= 1")

    lock_token = acquire_lock(options.lock_path)
    try:
        return _run_lab_loop_locked(options)
    finally:
        release_lock(options.lock_path, lock_token)


def _run_lab_loop_locked(options: LabLoopOptions) -> dict[str, Any]:

    start_time = time.monotonic()
    normalized_timeframes = tuple(normalize_timeframe(timeframe) for timeframe in options.timeframes)
    queue = initialize_runtime_queue(options)
    state = load_lab_state(options.state_path)
    session_id = state.get("session_id") if options.resume and state.get("session_id") else uuid.uuid4().hex[:12]
    report_session_dir = options.report_root / datetime.now().strftime("%Y-%m-%d") / f"session_{session_id}"
    state.update(
        {
            "model": LAB_LOOP_MODEL,
            "session_id": session_id,
            "status": "running",
            "started_at": state.get("started_at", utc_now_iso()),
            "updated_at": utc_now_iso(),
            "runner_version": LAB_LOOP_MODEL,
            "queue_path": str(options.queue_path),
            "runtime_queue_path": str(options.runtime_queue_path),
            "data_fingerprint": data_fingerprint(options.data_dir, normalized_timeframes),
        }
    )
    state.setdefault("last_completed_loop", 0)
    state.setdefault("completed_hypothesis_ids", [])
    atomic_write_json(options.state_path, state)

    universe = None
    analysis_by_timeframe: dict[str, dict[str, pd.DataFrame]] = {}
    data_warnings: list[str] = []
    if not options.dry_run:
        universe, analysis_by_timeframe, data_warnings = load_analysis_frames_by_timeframe(
            config_path=options.config_path,
            data_dir=options.data_dir,
            timeframes=normalized_timeframes,
        )

    completed_this_run = 0
    errors = 0
    while completed_this_run < options.max_loops:
        if options.max_hours is not None and (time.monotonic() - start_time) / 3600.0 >= options.max_hours:
            break
        hypothesis = select_next_hypothesis(queue, state)
        if hypothesis is None:
            state["status"] = "completed_no_runnable_hypotheses"
            break

        loop_number = int(state.get("last_completed_loop", 0)) + 1
        loop_dir = report_session_dir / f"loop_{loop_number:04d}"
        loop_dir.mkdir(parents=True, exist_ok=True)
        state.update(
            {
                "active_loop": loop_number,
                "current_loop_step": "started",
                "active_hypothesis_id": hypothesis.get("id"),
                "updated_at": utc_now_iso(),
            }
        )
        atomic_write_json(options.state_path, state)

        try:
            source = hypothesis.get("source")
            if not source or not is_executable_hypothesis(hypothesis):
                decision = {
                    "decision": "broaden",
                    "promotion_level": hypothesis.get("promotion_level", "L0_registered"),
                    "status": "needs_encoding",
                    "reason": "hypothesis has no executable YAML source grid yet",
                    "survivor_count": 0,
                    "useful_count": 0,
                }
                child = None
                ranked = pd.DataFrame()
                strict = pd.DataFrame()
                write_loop_summary(
                    loop_dir / "summary.md",
                    hypothesis=hypothesis,
                    decision=decision,
                    ranked=ranked,
                    strict_referee=strict,
                    child=child,
                    warnings=[],
                )
            elif options.dry_run:
                decision = {
                    "decision": "dry_run",
                    "promotion_level": hypothesis.get("promotion_level", "L0_registered"),
                    "status": hypothesis.get("status"),
                    "reason": f"would run source grid {source}",
                    "survivor_count": 0,
                    "useful_count": 0,
                }
                child = None
                ranked = pd.DataFrame()
                strict = pd.DataFrame()
                write_loop_summary(
                    loop_dir / "summary.md",
                    hypothesis=hypothesis,
                    decision=decision,
                    ranked=ranked,
                    strict_referee=strict,
                    child=child,
                    warnings=[],
                )
            else:
                grid_path = Path(source)
                if not grid_path.exists():
                    raise FileNotFoundError(f"hypothesis source grid does not exist: {grid_path}")
                shutil.copy2(grid_path, loop_dir / "hypothesis.yaml")
                cooldowns = (
                    {timeframe: int(options.cooldown_bars) for timeframe in normalized_timeframes}
                    if options.cooldown_bars is not None
                    else None
                )
                summary, records, ranked, family_summary, variants = run_grammar_search(
                    analysis_by_timeframe,
                    grid_path=grid_path,
                    timeframes=normalized_timeframes,
                    benchmark_name=universe.benchmark.name if universe is not None else "MEME_BASKET",
                    min_sample_size=options.min_sample_size,
                    entry_lag_bars=options.entry_lag_bars,
                    cooldown_bars_by_timeframe=cooldowns,
                )
                manifest = {
                    "model": LAB_LOOP_MODEL,
                    "search_model": GRAMMAR_SEARCH_MODEL,
                    "hypothesis_id": hypothesis.get("id"),
                    "source_grid": str(grid_path),
                    "timeframes": list(normalized_timeframes),
                    "min_sample_size": options.min_sample_size,
                    "entry_lag_bars": options.entry_lag_bars,
                    "cooldown_bars_by_timeframe": cooldowns
                    or {timeframe: timeframe_cooldown(timeframe) for timeframe in normalized_timeframes},
                    "variant_count": len(variants),
                    "record_count": int(len(records)),
                    "started_at": state.get("updated_at"),
                    "completed_at": utc_now_iso(),
                }
                export_grammar_search_reports(
                    summary,
                    records,
                    ranked,
                    family_summary,
                    manifest,
                    universe,
                    warnings=data_warnings,
                    report_dir=loop_dir,
                    obsidian_dir=Path("obsidian"),
                )
                strict = pd.DataFrame()
                if options.strict_referee:
                    strict = strict_baseline_referee(
                        ranked,
                        records,
                        analysis_by_timeframe,
                        entry_lag_bars=options.entry_lag_bars,
                        null_iterations=options.strict_null_iterations,
                        random_seed=options.strict_random_seed + loop_number,
                    )
                    strict.to_csv(loop_dir / "strict_referee.csv", index=False)
                ranked.to_csv(loop_dir / "ranked.csv", index=False)
                decision = decide_loop_outcome(ranked, strict)
                child = create_next_hypothesis(
                    queue=queue,
                    hypothesis=hypothesis,
                    ranked=ranked,
                    strict_referee=strict,
                    options=options,
                    session_id=session_id,
                    loop_number=loop_number,
                )
                if child:
                    atomic_write_yaml(loop_dir / "next_hypotheses.yaml", {"queue": [child]})
                else:
                    atomic_write_yaml(loop_dir / "next_hypotheses.yaml", {"queue": []})
                write_loop_summary(
                    loop_dir / "summary.md",
                    hypothesis=hypothesis,
                    decision=decision,
                    ranked=ranked,
                    strict_referee=strict,
                    child=child,
                    warnings=data_warnings,
                )

            update_hypothesis(
                queue,
                str(hypothesis["id"]),
                {
                    "status": decision.get("status"),
                    "promotion_level": decision.get("promotion_level"),
                    "last_tested_at": utc_now_iso(),
                    "last_decision": decision.get("decision"),
                    "last_decision_reason": decision.get("reason"),
                },
            )
            atomic_write_yaml(options.runtime_queue_path, queue)
            state["last_completed_loop"] = loop_number
            state["completed_hypothesis_ids"] = sorted(
                set(state.get("completed_hypothesis_ids", [])) | {str(hypothesis["id"])}
            )
            state["active_loop"] = None
            state["current_loop_step"] = "completed"
            state["last_loop_summary"] = {
                "hypothesis_id": hypothesis.get("id"),
                "decision": decision.get("decision"),
                "reason": decision.get("reason"),
                "next_hypothesis_id": child.get("id") if child else "",
                "report_dir": str(loop_dir),
                "errors": errors,
            }
            state["updated_at"] = utc_now_iso()
            atomic_write_json(options.state_path, state)
            atomic_write_text(options.report_root / "latest_status.md", latest_status_text(state))
            completed_this_run += 1
        except Exception as exc:  # pragma: no cover - exercised by integration usage
            errors += 1
            failure = {
                "timestamp": utc_now_iso(),
                "loop_number": loop_number,
                "hypothesis_id": hypothesis.get("id"),
                "error": str(exc),
                "report_dir": str(loop_dir),
            }
            atomic_write_json(loop_dir / "failure.json", failure)
            append_failure(DEFAULT_FAILURE_LOG_PATH, failure)
            update_hypothesis(
                queue,
                str(hypothesis["id"]),
                {
                    "status": "failed",
                    "last_tested_at": utc_now_iso(),
                    "last_decision": "failed",
                    "last_decision_reason": str(exc),
                },
            )
            atomic_write_yaml(options.runtime_queue_path, queue)
            state["last_completed_loop"] = loop_number
            state["active_loop"] = None
            state["current_loop_step"] = "failed"
            state["last_loop_summary"] = {
                "hypothesis_id": hypothesis.get("id"),
                "decision": "failed",
                "reason": str(exc),
                "next_hypothesis_id": "",
                "report_dir": str(loop_dir),
                "errors": errors,
            }
            atomic_write_json(options.state_path, state)
            atomic_write_text(options.report_root / "latest_status.md", latest_status_text(state))
            completed_this_run += 1

    state["status"] = state.get("status") if state.get("status") == "completed_no_runnable_hypotheses" else "completed"
    state["updated_at"] = utc_now_iso()
    state["completed_this_run"] = completed_this_run
    state["errors_this_run"] = errors
    atomic_write_json(options.state_path, state)
    atomic_write_text(options.report_root / "latest_status.md", latest_status_text(state))
    return state


def lab_loop_status(state_path: str | Path = DEFAULT_STATE_PATH) -> str:
    state = load_lab_state(state_path)
    if not state:
        return "No lab-loop state found."
    return latest_status_text(state)
