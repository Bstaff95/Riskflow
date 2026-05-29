from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, replace
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
DEFAULT_CONCEPT_SCOREBOARD_PATH = Path("research/lab_loop/concept_scoreboard.yaml")

TERMINAL_STATUSES = {"promoted", "demoted", "archived", "failed", "blocked_by_evidence"}
RUNNABLE_STATUSES = {"new", "encoded", "tested", "tested_needs_fresh_data", "needs_encoding"}
BRANCH_DECISIONS = {"promote", "refine", "broaden", "pair", "invert", "archive", "agent_review"}


@dataclass(frozen=True)
class LabLoopOptions:
    queue_path: Path = DEFAULT_QUEUE_PATH
    runtime_queue_path: Path = DEFAULT_RUNTIME_QUEUE_PATH
    state_path: Path = DEFAULT_STATE_PATH
    lock_path: Path = DEFAULT_LOCK_PATH
    report_root: Path = DEFAULT_REPORT_ROOT
    generated_grid_dir: Path = DEFAULT_GENERATED_GRID_DIR
    concept_scoreboard_path: Path = DEFAULT_CONCEPT_SCOREBOARD_PATH
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
    checkpoint_interval: int = 5
    resume: bool = False
    dry_run: bool = False
    auto_refine: bool = True


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


def git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


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


def build_refinement_grid(row: pd.Series, *, family_suffix: str, max_mutated_numeric_params: int = 3) -> dict[str, Any]:
    params = parse_params(row.get("params"))
    params.pop("timeframe", None)
    parameter_grid: dict[str, list[Any]] = {}
    mutated_numeric_count = 0
    for key, value in params.items():
        if isinstance(value, bool):
            parameter_grid[key] = [value]
        elif isinstance(value, int) and not isinstance(value, bool):
            if mutated_numeric_count < max_mutated_numeric_params:
                parameter_grid[key] = _numeric_mutations(key, value)
                mutated_numeric_count += 1
            else:
                parameter_grid[key] = [value]
        elif isinstance(value, float):
            if mutated_numeric_count < max_mutated_numeric_params:
                parameter_grid[key] = _numeric_mutations(key, value)
                mutated_numeric_count += 1
            else:
                parameter_grid[key] = [value]
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

    child_id = safe_child_hypothesis_id(hypothesis, loop_number=loop_number)
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


def root_hypothesis_id(hypothesis_id: str) -> str:
    return hypothesis_id.split("_child_", 1)[0]


def safe_child_hypothesis_id(hypothesis: dict[str, Any], *, loop_number: int) -> str:
    parent_id = str(hypothesis.get("id", "hypothesis"))
    root = root_hypothesis_id(parent_id)
    safe_root = re.sub(r"[^A-Za-z0-9_]+", "_", root).strip("_") or "hypothesis"
    safe_root = safe_root[:64]
    generation = int(hypothesis.get("generation", 0) or 0) + 1
    digest = f"{abs(hash(parent_id)) % 100_000_000:08d}"
    return f"{safe_root}_child_g{generation:03d}_l{loop_number:04d}_{digest}"


def loop_history_entry(
    *,
    loop_number: int,
    hypothesis: dict[str, Any],
    decision: dict[str, Any],
    child: dict[str, Any] | None,
    report_dir: Path,
    errors: int,
) -> dict[str, Any]:
    hypothesis_id = str(hypothesis.get("id", ""))
    return {
        "loop_number": loop_number,
        "hypothesis_id": hypothesis_id,
        "root_hypothesis_id": root_hypothesis_id(hypothesis_id),
        "generation": int(hypothesis.get("generation", 0) or 0),
        "track": hypothesis.get("track"),
        "decision": decision.get("decision"),
        "reason": decision.get("reason"),
        "survivor_count": int(decision.get("survivor_count", 0) or 0),
        "useful_count": int(decision.get("useful_count", 0) or 0),
        "next_hypothesis_id": child.get("id") if child else "",
        "report_dir": str(report_dir),
        "errors": errors,
        "created_at": utc_now_iso(),
    }


def analyze_recent_loops(history: list[dict[str, Any]], *, checkpoint_interval: int = 5) -> dict[str, Any]:
    recent = history[-checkpoint_interval:]
    loop_count = len(recent)
    root_counts: dict[str, int] = {}
    track_counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}
    for entry in recent:
        root = str(entry.get("root_hypothesis_id", ""))
        track = str(entry.get("track", ""))
        decision = str(entry.get("decision", ""))
        root_counts[root] = root_counts.get(root, 0) + 1
        track_counts[track] = track_counts.get(track, 0) + 1
        decision_counts[decision] = decision_counts.get(decision, 0) + 1

    dominant_root = max(root_counts, key=root_counts.get) if root_counts else ""
    dominant_root_share = (root_counts.get(dominant_root, 0) / loop_count) if loop_count else 0.0
    promoted = decision_counts.get("promote", 0)
    refined = decision_counts.get("refine", 0)
    archived_or_failed = decision_counts.get("archive", 0) + decision_counts.get("failed", 0)
    error_total = sum(int(entry.get("errors", 0) or 0) for entry in recent)
    total_survivors = sum(int(entry.get("survivor_count", 0) or 0) for entry in recent)
    max_generation = max((int(entry.get("generation", 0) or 0) for entry in recent), default=0)

    doing_well: list[str] = []
    not_doing_well: list[str] = []
    interventions: list[str] = []
    mission_questions: list[str] = []

    if promoted:
        doing_well.append(f"{promoted}/{loop_count} recent loops promoted strict survivors.")
    if total_survivors:
        doing_well.append(f"Recent loops found {total_survivors} strict survivor rows.")
    if refined:
        doing_well.append(f"{refined}/{loop_count} recent loops found useful non-strict evidence to refine.")
    if error_total == 0 and loop_count:
        doing_well.append("Runner reliability is good: no errors in the recent checkpoint window.")
    if "warning" in track_counts:
        mission_questions.append("Warning/avoidance evidence is being tested.")
    if "bullish_setup" in track_counts:
        mission_questions.append("Bullish setup journey evidence is being tested.")
    if "bullish_setup" not in track_counts and loop_count >= 3:
        not_doing_well.append("Mission gap: recent loops did not test bullish setup journeys.")
        interventions.append("boost_bullish_setup_track")
    if "warning" in track_counts and "bullish_setup" not in track_counts:
        not_doing_well.append("Recent learning is skewed toward avoiding bad trades, not finding best long setups.")
    if "gradient_translation" in track_counts:
        mission_questions.append("Gradient translation is being touched, but should remain evidence-gated.")
    if dominant_root_share >= 0.8 and loop_count >= 3:
        not_doing_well.append(
            f"Research is over-exploiting one branch: {dominant_root} appeared in {root_counts[dominant_root]}/{loop_count} loops."
        )
        interventions.append("cool_latest_child_and_boost_alternatives")
        interventions.append("force_root_rotation")
    if max_generation >= 4:
        not_doing_well.append(
            f"Research is deep in one refinement lineage, with generation depth {max_generation}."
        )
        interventions.append("cool_latest_child_and_boost_alternatives")
        interventions.append("cap_lineage_depth")
    if archived_or_failed >= max(3, loop_count):
        not_doing_well.append("Recent loops are mostly dead ends or failures.")
        interventions.append("broaden_search")
    if error_total:
        not_doing_well.append(f"Recent loops logged {error_total} error(s); reliability needs attention before scaling.")
        interventions.append("reliability_pause")
    if len(track_counts) == 1 and loop_count >= 3:
        only_track = next(iter(track_counts))
        not_doing_well.append(f"Recent loops stayed on one track: {only_track}.")
        interventions.append("boost_other_tracks")
        interventions.append("force_track_rotation")
    if promoted == loop_count and dominant_root_share >= 0.8 and loop_count >= 3:
        not_doing_well.append(
            "Even though evidence is strong, the lab is mostly confirming one idea instead of broadening mission coverage."
        )
    if "warning" in track_counts and total_survivors:
        mission_questions.append("Next useful question: can this warning improve invalidation or entry filtering?")
    if not doing_well:
        doing_well.append("The runner completed checkpoint loops without crashing.")
    if not not_doing_well:
        not_doing_well.append("No major process weakness detected in this checkpoint.")
    if not mission_questions:
        mission_questions.append("No mission-specific learning theme was detected; broaden the next checkpoint window.")

    return {
        "checkpoint_at_loop": recent[-1].get("loop_number") if recent else 0,
        "loop_count": loop_count,
        "root_counts": root_counts,
        "track_counts": track_counts,
        "decision_counts": decision_counts,
        "dominant_root": dominant_root,
        "dominant_root_share": dominant_root_share,
        "doing_well": doing_well,
        "not_doing_well": not_doing_well,
        "mission_questions": mission_questions,
        "interventions": sorted(set(interventions)),
        "recent_hypothesis_ids": [entry.get("hypothesis_id") for entry in recent],
    }


def apply_checkpoint_interventions(
    queue: dict[str, Any],
    checkpoint: dict[str, Any],
    *,
    completed_hypothesis_ids: set[str],
    latest_child_id: str | None,
) -> list[str]:
    actions: list[str] = []
    interventions = set(checkpoint.get("interventions", []))
    if not interventions:
        return actions

    checkpoint_loop = int(checkpoint.get("checkpoint_at_loop", 0) or 0)
    rotation_cooldown_until = checkpoint_loop + max(5, int(checkpoint.get("loop_count", 0) or 0) * 2)
    dominant_root = str(checkpoint.get("dominant_root", ""))
    dominant_tracks = {
        str(track)
        for track, count in dict(checkpoint.get("track_counts", {})).items()
        if count == int(checkpoint.get("loop_count", 0) or 0)
    }
    for item in queue.get("queue", []):
        item_id = str(item.get("id", ""))
        if item_id in completed_hypothesis_ids:
            continue
        status = str(item.get("status", "new"))
        if status in TERMINAL_STATUSES:
            continue
        item_root = root_hypothesis_id(item_id)
        if (
            item_root == dominant_root
            and {"force_root_rotation", "cap_lineage_depth"} & interventions
        ):
            old_priority = int(item.get("priority", 999))
            item["cooldown_until_loop"] = max(
                int(item.get("cooldown_until_loop", 0) or 0),
                rotation_cooldown_until,
            )
            item["priority"] = old_priority + 200
            item["checkpoint_note"] = "Cooled by forced root rotation after checkpoint over-exploitation."
            actions.append(
                f"force-cooled dominant root {item_id} until loop {rotation_cooldown_until} "
                f"priority {old_priority}->{item['priority']}"
            )
            continue
        if (
            item.get("track") in dominant_tracks
            and "force_track_rotation" in interventions
            and item_root == dominant_root
        ):
            old_priority = int(item.get("priority", 999))
            item["cooldown_until_loop"] = max(
                int(item.get("cooldown_until_loop", 0) or 0),
                rotation_cooldown_until,
            )
            item["priority"] = old_priority + 100
            item["checkpoint_note"] = "Cooled by forced track rotation after single-track drift."
            actions.append(
                f"force-cooled dominant track {item_id} until loop {rotation_cooldown_until} "
                f"priority {old_priority}->{item['priority']}"
            )
            continue
        if item_id == latest_child_id and "cool_latest_child_and_boost_alternatives" in interventions:
            item["cooldown_until_loop"] = checkpoint_loop + 3
            item["priority"] = int(item.get("priority", 999)) + 50
            item["checkpoint_note"] = "Cooled because checkpoint detected narrow mission coverage."
            actions.append(f"cooled {item_id} until loop {checkpoint_loop + 3}")
            continue
        if item_root == dominant_root:
            continue
        if "boost_bullish_setup_track" in interventions and item.get("track") == "bullish_setup":
            old_priority = int(item.get("priority", 999))
            item["priority"] = 1
            item["checkpoint_note"] = "Boosted because checkpoint detected no recent bullish setup research."
            actions.append(f"boosted bullish setup {item_id} priority {old_priority}->{item['priority']}")
            continue
        if is_executable_hypothesis(item):
            old_priority = int(item.get("priority", 999))
            item["priority"] = 1 if {"force_root_rotation", "force_track_rotation"} & interventions else max(1, old_priority - 25)
            item["checkpoint_note"] = "Boosted as executable mission-coverage alternative."
            actions.append(f"boosted executable alternative {item_id} priority {old_priority}->{item['priority']}")
        elif "boost_other_tracks" in interventions:
            old_priority = int(item.get("priority", 999))
            item["priority"] = 1 if "force_track_rotation" in interventions else max(1, old_priority - 5)
            item["checkpoint_note"] = "Boosted for encoding because checkpoint detected single-track drift."
            actions.append(f"boosted non-executable alternative {item_id} priority {old_priority}->{item['priority']}")
    if not actions:
        actions.append("no queue intervention available; all alternatives were completed, terminal, or non-actionable")
    return actions


def write_checkpoint_report(path: Path, checkpoint: dict[str, Any], actions: list[str]) -> None:
    lines = [
        f"# Lab Loop Checkpoint {checkpoint.get('checkpoint_at_loop')}",
        "",
        f"Generated: {utc_now_iso()}",
        "",
        "## What Is Working",
        *[f"- {item}" for item in checkpoint.get("doing_well", [])],
        "",
        "## What Is Not Working",
        *[f"- {item}" for item in checkpoint.get("not_doing_well", [])],
        "",
        "## Mission Questions",
        *[f"- {item}" for item in checkpoint.get("mission_questions", [])],
        "",
        "## Interventions",
        *[f"- {item}" for item in actions],
        "",
        "## Recent Roots",
        "```json",
        json.dumps(checkpoint.get("root_counts", {}), indent=2, sort_keys=True),
        "```",
        "",
        "## Recent Decisions",
        "```json",
        json.dumps(checkpoint.get("decision_counts", {}), indent=2, sort_keys=True),
        "```",
        "",
    ]
    atomic_write_text(path, "\n".join(lines))


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
    checkpoint = state.get("last_checkpoint", {})
    epoch = state.get("last_epoch", {})
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
            f"Last Checkpoint: {checkpoint.get('report', '')}",
            f"Last Epoch: {epoch.get('summary', '')}",
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


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _to_int(value: Any) -> int:
    number = _to_float(value)
    return int(number) if number is not None else 0


def _read_report_csv(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if not source.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(source)
    except Exception:
        return pd.DataFrame()


def concept_root_from_entry(entry: dict[str, Any]) -> str:
    root = str(entry.get("root_hypothesis_id") or entry.get("hypothesis_id") or "")
    return root_hypothesis_id(root)


def _best_report_row(ranked: pd.DataFrame, strict: pd.DataFrame) -> dict[str, Any]:
    source = strict if not strict.empty else ranked
    if source.empty:
        return {}
    if "rank_score" in source.columns:
        scored = source.copy()
        scored["_rank_score_numeric"] = pd.to_numeric(scored["rank_score"], errors="coerce")
        scored = scored.sort_values("_rank_score_numeric", ascending=False, na_position="last")
        return scored.iloc[0].drop(labels=["_rank_score_numeric"], errors="ignore").to_dict()
    return source.iloc[0].to_dict()


def summarize_epoch_concepts(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    concepts: dict[str, dict[str, Any]] = {}
    for entry in entries:
        root = concept_root_from_entry(entry)
        report_dir = Path(str(entry.get("report_dir", "")))
        ranked = _read_report_csv(report_dir / "ranked.csv")
        strict = _read_report_csv(report_dir / "strict_referee.csv")
        best = _best_report_row(ranked, strict)
        concept = concepts.setdefault(
            root,
            {
                "concept_id": root,
                "track": entry.get("track", ""),
                "loops": 0,
                "latest_loop": 0,
                "decisions": {},
                "strict_survivors": 0,
                "useful_or_watchlist": 0,
                "unique_symbols": 0,
                "event_clusters": 0,
                "best_timeframe": "",
                "best_rank_score": None,
                "best_median_relative_return": None,
                "validation_status": "",
                "latest_decision": "",
                "branch_decision": "",
                "novelty_score": 0,
            },
        )
        concept["loops"] += 1
        concept["latest_loop"] = max(int(concept["latest_loop"]), int(entry.get("loop_number", 0) or 0))
        decision = str(entry.get("decision", ""))
        concept["decisions"][decision] = int(concept["decisions"].get(decision, 0)) + 1
        concept["strict_survivors"] += int(entry.get("survivor_count", 0) or 0)
        concept["useful_or_watchlist"] += int(entry.get("useful_count", 0) or 0)
        concept["latest_decision"] = decision
        concept["unique_symbols"] = max(concept["unique_symbols"], _to_int(best.get("unique_symbols")))
        concept["event_clusters"] = max(concept["event_clusters"], _to_int(best.get("unique_event_clusters")))
        rank_score = _to_float(best.get("rank_score"))
        if rank_score is not None and (
            concept["best_rank_score"] is None or rank_score > float(concept["best_rank_score"])
        ):
            concept["best_rank_score"] = rank_score
            concept["best_timeframe"] = str(best.get("timeframe", ""))
            concept["validation_status"] = str(best.get("validation_status", ""))
            concept["best_median_relative_return"] = _to_float(
                best.get("event_median_terminal_relative_return")
                or best.get("median_forward_relative_return_secondary")
                or best.get("median_forward_relative_return_30")
            )

    for concept in concepts.values():
        concept["branch_decision"] = decide_epoch_branch(concept)
        concept["novelty_score"] = estimate_epoch_novelty(concept)
    return sorted(concepts.values(), key=lambda item: (item["branch_decision"], item["concept_id"]))


def decide_epoch_branch(concept: dict[str, Any]) -> str:
    decisions = dict(concept.get("decisions", {}))
    if decisions.get("failed") or decisions.get("archive"):
        return "archive"
    if int(concept.get("strict_survivors", 0) or 0) > 0:
        return "promote"
    if int(concept.get("useful_or_watchlist", 0) or 0) > 0:
        return "agent_review" if int(concept.get("loops", 0) or 0) > 1 else "refine"
    if decisions.get("broaden") or decisions.get("dry_run"):
        return "broaden"
    return "archive"


def estimate_epoch_novelty(concept: dict[str, Any]) -> int:
    score = 3
    if int(concept.get("loops", 0) or 0) == 1:
        score += 2
    if concept.get("track") in {"bullish_setup", "mtf_context"}:
        score += 2
    if concept.get("branch_decision") in {"pair", "invert", "agent_review"}:
        score += 2
    if int(concept.get("strict_survivors", 0) or 0) > 0:
        score += 1
    return max(0, min(10, score))


def _epoch_csv_rows(entries: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for entry in entries:
        rows.append(
            {
                "loop_number": entry.get("loop_number"),
                "hypothesis_id": entry.get("hypothesis_id"),
                "concept_id": concept_root_from_entry(entry),
                "track": entry.get("track"),
                "decision": entry.get("decision"),
                "reason": entry.get("reason"),
                "survivor_count": entry.get("survivor_count"),
                "useful_count": entry.get("useful_count"),
                "generation": entry.get("generation"),
                "report_dir": entry.get("report_dir"),
            }
        )
    return pd.DataFrame(rows)


def write_epoch_reports(
    *,
    state: dict[str, Any],
    options: LabLoopOptions,
    entries: list[dict[str, Any]],
    epoch_number: int,
    epoch_size: int,
) -> dict[str, str]:
    report_session_dir = Path(str(state.get("report_session_dir") or ""))
    if not report_session_dir:
        report_session_dir = options.report_root / datetime.now().strftime("%Y-%m-%d") / f"session_{state.get('session_id')}"
    epoch_id = f"epoch_{epoch_number:04d}"
    epoch_dir = report_session_dir / "epochs" / epoch_id
    epoch_dir.mkdir(parents=True, exist_ok=True)

    concepts = summarize_epoch_concepts(entries)
    concepts_df = pd.DataFrame(concepts)
    tested_df = _epoch_csv_rows(entries)
    branch_decisions = {
        "model": "riskflow_lab_loop_epoch_branch_decisions_v0",
        "epoch": epoch_id,
        "decisions": [
            {
                "concept_id": concept["concept_id"],
                "decision": concept["branch_decision"],
                "latest_loop": concept["latest_loop"],
                "reason": _branch_reason(concept),
            }
            for concept in concepts
        ],
    }
    suggestions = {
        "model": "riskflow_lab_loop_next_epoch_suggestions_v0",
        "epoch": epoch_id,
        "applied": False,
        "suggestions": [
            {
                "concept_id": concept["concept_id"],
                "track": concept["track"],
                "suggested_decision": concept["branch_decision"],
                "novelty_score": concept["novelty_score"],
                "next_action": _suggest_next_action(concept),
            }
            for concept in concepts
            if concept["branch_decision"] != "archive"
        ],
    }
    manifest = {
        "model": "riskflow_lab_loop_epoch_manifest_v0",
        "epoch": epoch_id,
        "session_id": state.get("session_id"),
        "generated_at": utc_now_iso(),
        "git_commit": git_commit(),
        "data_fingerprint": state.get("data_fingerprint", ""),
        "loop_start": min((int(entry.get("loop_number", 0) or 0) for entry in entries), default=0),
        "loop_end": max((int(entry.get("loop_number", 0) or 0) for entry in entries), default=0),
        "requested_epoch_size": epoch_size,
        "completed_loops": len(entries),
        "strict_referee": options.strict_referee,
        "strict_null_iterations": options.strict_null_iterations,
        "errors": sum(int(entry.get("errors", 0) or 0) for entry in entries),
        "strict_survivors": sum(int(entry.get("survivor_count", 0) or 0) for entry in entries),
        "useful_or_watchlist": sum(int(entry.get("useful_count", 0) or 0) for entry in entries),
        "tested_hypotheses_csv": str(epoch_dir / "tested_hypotheses.csv"),
        "concept_scoreboard_csv": str(epoch_dir / "concept_scoreboard.csv"),
        "branch_decisions_yaml": str(epoch_dir / "branch_decisions.yaml"),
        "next_epoch_suggestions_yaml": str(epoch_dir / "next_epoch_suggestions.yaml"),
    }

    tested_df.to_csv(epoch_dir / "tested_hypotheses.csv", index=False)
    concepts_df.to_csv(epoch_dir / "concept_scoreboard.csv", index=False)
    atomic_write_yaml(epoch_dir / "branch_decisions.yaml", branch_decisions)
    atomic_write_yaml(epoch_dir / "next_epoch_suggestions.yaml", suggestions)
    atomic_write_json(epoch_dir / "epoch_manifest.json", manifest)
    write_epoch_summary(epoch_dir / "epoch_summary.md", manifest, concepts, suggestions)
    update_concept_scoreboard(options.concept_scoreboard_path, concepts)

    return {
        "epoch": epoch_id,
        "epoch_dir": str(epoch_dir),
        "manifest": str(epoch_dir / "epoch_manifest.json"),
        "summary": str(epoch_dir / "epoch_summary.md"),
        "branch_decisions": str(epoch_dir / "branch_decisions.yaml"),
        "next_epoch_suggestions": str(epoch_dir / "next_epoch_suggestions.yaml"),
    }


def _branch_reason(concept: dict[str, Any]) -> str:
    if concept["branch_decision"] == "promote":
        return f"{concept['strict_survivors']} strict survivor row(s) found in this epoch."
    if concept["branch_decision"] == "agent_review":
        return "Useful/watchlist evidence exists, but repeated refinement needs supervisor review."
    if concept["branch_decision"] == "refine":
        return "Useful/watchlist evidence exists without strict survivors."
    if concept["branch_decision"] == "broaden":
        return "Concept is not executable or was only dry-run; broaden/encode before testing."
    return "No useful strict or watchlist evidence survived this epoch."


def _suggest_next_action(concept: dict[str, Any]) -> str:
    decision = concept["branch_decision"]
    if decision == "promote":
        return "Freeze the current rule shape and run validation/fresh-data checks before more refinement."
    if decision == "agent_review":
        return "Codex should review evidence and decide whether to pair, invert, refine, or archive."
    if decision == "refine":
        return "Create one bounded follow-up, then require supervisor review."
    if decision == "broaden":
        return "Encode a broader measurable version or split the idea into staged primitives."
    return "Archive unless new data or agent review reopens the branch."


def write_epoch_summary(
    path: Path,
    manifest: dict[str, Any],
    concepts: list[dict[str, Any]],
    suggestions: dict[str, Any],
) -> None:
    decision_counts: dict[str, int] = {}
    for concept in concepts:
        decision = str(concept.get("branch_decision", ""))
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    suggestion_lines = [
        f"- {item['concept_id']}: {item['suggested_decision']} "
        f"(novelty {item['novelty_score']}) - {item['next_action']}"
        for item in suggestions.get("suggestions", [])
    ] or ["- None. Codex should add high-novelty concepts before another epoch."]
    lines = [
        f"# Lab Epoch Summary: {manifest['epoch']}",
        "",
        f"Generated: {manifest['generated_at']}",
        f"Session: {manifest.get('session_id', '')}",
        f"Loops: {manifest.get('loop_start')} - {manifest.get('loop_end')}",
        f"Completed Loops: {manifest.get('completed_loops')}",
        f"Strict Survivors: {manifest.get('strict_survivors')}",
        f"Useful/Watchlist Rows: {manifest.get('useful_or_watchlist')}",
        "",
        "## What Was Tested",
        *[
            f"- {concept['concept_id']} ({concept['track']}): "
            f"{concept['loops']} loop(s), latest decision {concept['latest_decision']}"
            for concept in concepts
        ],
        "",
        "## Branch Decisions",
        *[
            f"- {concept['concept_id']}: {concept['branch_decision']} - {_branch_reason(concept)}"
            for concept in concepts
        ],
        "",
        "## Decision Mix",
        "```json",
        json.dumps(decision_counts, indent=2, sort_keys=True),
        "```",
        "",
        "## Next Epoch Suggestions",
        *suggestion_lines,
        "",
        "## Supervisor Note",
        "Codex should review this epoch before starting another batch. Do not treat same-sample refinements as validation.",
        "",
    ]
    atomic_write_text(path, "\n".join(lines))


def update_concept_scoreboard(path: Path, concepts: list[dict[str, Any]]) -> None:
    existing = load_yaml_file(path) if path.exists() else {"model": "riskflow_lab_loop_concept_scoreboard_v0", "concepts": {}}
    scoreboard = existing.get("concepts", {})
    if not isinstance(scoreboard, dict):
        scoreboard = {}
    for concept in concepts:
        concept_id = str(concept["concept_id"])
        prior = scoreboard.get(concept_id, {})
        scoreboard[concept_id] = {
            **prior,
            "track": concept.get("track", prior.get("track", "")),
            "current_promotion_level": _promotion_from_branch_decision(concept["branch_decision"]),
            "best_timeframe": concept.get("best_timeframe") or prior.get("best_timeframe", ""),
            "unique_symbols": max(_to_int(prior.get("unique_symbols")), _to_int(concept.get("unique_symbols"))),
            "event_clusters": max(_to_int(prior.get("event_clusters")), _to_int(concept.get("event_clusters"))),
            "strict_survivors": _to_int(prior.get("strict_survivors")) + _to_int(concept.get("strict_survivors")),
            "useful_or_watchlist": _to_int(prior.get("useful_or_watchlist")) + _to_int(concept.get("useful_or_watchlist")),
            "best_rank_score": concept.get("best_rank_score", prior.get("best_rank_score")),
            "best_median_relative_return": concept.get(
                "best_median_relative_return", prior.get("best_median_relative_return")
            ),
            "validation_status": concept.get("validation_status") or prior.get("validation_status", ""),
            "latest_decision": concept.get("branch_decision"),
            "latest_loop": concept.get("latest_loop"),
            "retirement_reason": _branch_reason(concept) if concept.get("branch_decision") == "archive" else "",
            "updated_at": utc_now_iso(),
        }
    atomic_write_yaml(
        path,
        {
            "model": "riskflow_lab_loop_concept_scoreboard_v0",
            "updated_at": utc_now_iso(),
            "concepts": scoreboard,
        },
    )


def _promotion_from_branch_decision(decision: str) -> str:
    if decision == "promote":
        return "L3_strict_survivor"
    if decision in {"refine", "agent_review", "pair", "invert"}:
        return "L2_discovered"
    if decision == "archive":
        return "archived"
    return "L1_encoded"


def run_lab_epoch(options: LabLoopOptions, *, epoch_size: int = 5) -> dict[str, Any]:
    if epoch_size < 3 or epoch_size > 10:
        raise ValueError("epoch_size must be between 3 and 10")
    starting_state = load_lab_state(options.state_path) if options.resume else {}
    start_loop = int(starting_state.get("last_completed_loop", 0) or 0)
    epoch_options = replace(options, max_loops=epoch_size, auto_refine=False)
    state = run_lab_loop(epoch_options)
    entries = [
        entry
        for entry in state.get("loop_history", [])
        if start_loop < int(entry.get("loop_number", 0) or 0) <= int(state.get("last_completed_loop", 0) or 0)
    ]
    epoch_number = len(state.get("epochs", [])) + 1
    reports = write_epoch_reports(
        state=state,
        options=epoch_options,
        entries=entries,
        epoch_number=epoch_number,
        epoch_size=epoch_size,
    )
    state.setdefault("epochs", []).append(reports)
    state["last_epoch"] = reports
    state["updated_at"] = utc_now_iso()
    atomic_write_json(options.state_path, state)
    atomic_write_text(options.report_root / "latest_status.md", latest_status_text(state))
    return state


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
    state = load_lab_state(options.state_path) if options.resume else {}
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
            "report_session_dir": str(report_session_dir),
            "data_fingerprint": data_fingerprint(options.data_dir, normalized_timeframes),
        }
    )
    state.setdefault("last_completed_loop", 0)
    state.setdefault("completed_hypothesis_ids", [])
    state.setdefault("loop_history", [])
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
                child = (
                    create_next_hypothesis(
                        queue=queue,
                        hypothesis=hypothesis,
                        ranked=ranked,
                        strict_referee=strict,
                        options=options,
                        session_id=session_id,
                        loop_number=loop_number,
                    )
                    if options.auto_refine
                    else None
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
            history_entry = loop_history_entry(
                loop_number=loop_number,
                hypothesis=hypothesis,
                decision=decision,
                child=child,
                report_dir=loop_dir,
                errors=errors,
            )
            state.setdefault("loop_history", []).append(history_entry)
            if options.checkpoint_interval and loop_number % options.checkpoint_interval == 0:
                checkpoint = analyze_recent_loops(
                    state.get("loop_history", []),
                    checkpoint_interval=options.checkpoint_interval,
                )
                actions = apply_checkpoint_interventions(
                    queue,
                    checkpoint,
                    completed_hypothesis_ids=set(state.get("completed_hypothesis_ids", [])),
                    latest_child_id=child.get("id") if child else "",
                )
                checkpoint_dir = report_session_dir / "checkpoints"
                checkpoint_path = checkpoint_dir / f"checkpoint_loop_{loop_number:04d}.md"
                write_checkpoint_report(checkpoint_path, checkpoint, actions)
                state["last_checkpoint"] = {
                    **checkpoint,
                    "actions": actions,
                    "report": str(checkpoint_path),
                }
                atomic_write_yaml(options.runtime_queue_path, queue)
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
            state.setdefault("loop_history", []).append(
                loop_history_entry(
                    loop_number=loop_number,
                    hypothesis=hypothesis,
                    decision={
                        "decision": "failed",
                        "reason": str(exc),
                        "survivor_count": 0,
                        "useful_count": 0,
                    },
                    child=None,
                    report_dir=loop_dir,
                    errors=errors,
                )
            )
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
