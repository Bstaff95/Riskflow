from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .lab_loop import (
    BULLISH_POSITIVE_OBJECTIVE,
    DEFAULT_CONCEPT_SCOREBOARD_PATH,
    DEFAULT_REPORT_ROOT,
    DEFAULT_RUNTIME_QUEUE_PATH,
    DEFAULT_STATE_PATH,
    atomic_write_json,
    atomic_write_text,
    atomic_write_yaml,
    canonical_hypothesis_root,
    lineage_fingerprint,
    load_lab_queue,
    load_lab_state,
    load_yaml_file,
    validate_lab_queue,
)


DIRECTOR_MODEL = "riskflow_lab_director_v0"
EVIDENCE_MART_MODEL = "riskflow_lab_director_evidence_mart_v0"
BELIEF_GRAPH_MODEL = "riskflow_lab_director_belief_graph_v0"
EXPERIMENT_PLAN_MODEL = "riskflow_lab_director_experiment_plan_v0"
DIRECTOR_QUEUE_MODEL = "riskflow_lab_loop_hypothesis_queue_v0"

DEFAULT_DIRECTOR_REPORT_ROOT = Path("reports/lab_director")
DEFAULT_DIRECTOR_QUEUE_PATH = Path("research/lab_loop/director_candidate_queue.yaml")
DEFAULT_DIRECTOR_GRID_DIR = Path("research/lab_loop/generated_grids/director")

PROMISING_TIERS = {"path_watchlist", "asymmetric_candidate", "strict_validated"}
SUPPORTING_DECISIONS = {"refine", "bullish_path_watchlist", "promote"}
VALID_RESEARCH_STAGES = {
    "discovery",
    "causal_decomposition",
    "validation",
    "counterexample",
    "translation",
    "archive",
}


@dataclass(frozen=True)
class LabDirectorOptions:
    state_path: Path = DEFAULT_STATE_PATH
    runtime_queue_path: Path = DEFAULT_RUNTIME_QUEUE_PATH
    concept_scoreboard_path: Path = DEFAULT_CONCEPT_SCOREBOARD_PATH
    evidence_ledger_path: Path = Path("research/lab_loop/evidence_ledger.yaml")
    report_root: Path = DEFAULT_REPORT_ROOT
    director_report_root: Path = DEFAULT_DIRECTOR_REPORT_ROOT
    output_queue_path: Path = DEFAULT_DIRECTOR_QUEUE_PATH
    generated_grid_dir: Path = DEFAULT_DIRECTOR_GRID_DIR
    objective: str = BULLISH_POSITIVE_OBJECTIVE
    max_new_hypotheses: int = 30
    source_root: Path = Path(".")
    apply: bool = False
    apply_to_runtime: bool = False


def utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_slug(value: str, *, max_length: int = 96) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value).strip().lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return (slug or "director_item")[:max_length].rstrip("_")


def _safe_slug_with_hash(value: str, *, max_length: int = 96) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value).strip().lower()).strip("_")
    slug = re.sub(r"_+", "_", slug) or "director_item"
    if len(slug) <= max_length:
        return slug
    token = lineage_fingerprint(slug, "safe_slug")[:8]
    prefix_length = max(1, max_length - len(token) - 1)
    return f"{slug[:prefix_length].rstrip('_')}_{token}"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_yaml_file(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    number = _as_float(value)
    return int(number) if number is not None else 0


def _loop_number(loop_dir: Path) -> int:
    try:
        return int(loop_dir.name.split("_", 1)[1])
    except (IndexError, ValueError):
        return 0


def _latest_session_id(options: LabDirectorOptions) -> str:
    state = _read_json(options.state_path)
    session_id = str(state.get("session_id", "") or "")
    if session_id:
        return session_id
    sessions = sorted(options.report_root.glob("**/session_*"), key=lambda path: path.stat().st_mtime)
    if sessions:
        return sessions[-1].name.replace("session_", "", 1)
    return "ad_hoc"


def _director_output_dir(options: LabDirectorOptions, session_id: str) -> Path:
    return options.director_report_root / session_id


def _source_path(value: str | None, source_root: Path) -> str:
    if not value:
        return ""
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((source_root / path).as_posix())


def _discovery_stage(evidence: dict[str, Any], hypothesis: dict[str, Any]) -> str:
    stage = str(hypothesis.get("research_stage") or hypothesis.get("research_gate_stage") or "")
    if stage == "attribution":
        return "causal_decomposition"
    if stage in VALID_RESEARCH_STAGES:
        return stage
    decision = str(evidence.get("decision", ""))
    if decision == "bullish_path_watchlist":
        return "discovery"
    if str(evidence.get("contract_tier", "")) == "strict_validated":
        return "validation"
    if str(evidence.get("contract_tier", "")) == "blocker":
        return "counterexample"
    return "discovery"


def _failure_mode(evidence: dict[str, Any]) -> str:
    failures = evidence.get("contract_failures")
    if isinstance(failures, list) and failures:
        return str(failures[0])
    return str(evidence.get("failure_reason", "") or evidence.get("decision_reason", ""))


def _mart_row_from_loop(loop_dir: Path, options: LabDirectorOptions) -> dict[str, Any]:
    evidence_path = loop_dir / "bullish_evidence.yaml"
    evidence = _read_yaml(evidence_path)
    hypothesis = _read_yaml(loop_dir / "hypothesis.yaml")
    manifest = _read_yaml(loop_dir / "grammar_search_manifest.yaml")
    hypothesis_id = str(evidence.get("hypothesis_id") or hypothesis.get("id") or loop_dir.name)
    root_id = str(hypothesis.get("root_id") or canonical_hypothesis_root(hypothesis or {"id": hypothesis_id}))
    if not root_id:
        root_id = hypothesis_id
    source_grid = str(hypothesis.get("source") or manifest.get("source_grid") or "")
    terminal_return = _as_float(evidence.get("terminal_median_relative_return"))
    hit_rate = _as_float(evidence.get("hit_rate"))
    mfe_mae = _as_float(evidence.get("mfe_mae_ratio"))
    drawdown = _as_float(evidence.get("median_max_drawdown"))
    edge_cluster = _as_float(evidence.get("edge_vs_cluster"))
    p_value = _as_float(evidence.get("matched_null_p_value"))
    validation_status = str(evidence.get("validation_status", ""))
    contract_tier = str(evidence.get("contract_tier", ""))
    decision = str(evidence.get("decision", ""))
    trial_id = f"loop_{_loop_number(loop_dir):04d}:{hypothesis_id}"
    return {
        "trial_id": trial_id,
        "loop_number": _loop_number(loop_dir),
        "hypothesis_id": hypothesis_id,
        "root_id": root_id,
        "lineage_fingerprint": str(hypothesis.get("lineage_fingerprint", "")),
        "track": str(evidence.get("track") or hypothesis.get("track", "")),
        "claim_type": str(evidence.get("claim_type") or hypothesis.get("claim_type", "")),
        "setup_class": str(evidence.get("setup_class") or hypothesis.get("setup_class", "")),
        "detector": str(evidence.get("primary_detector") or hypothesis.get("primary_detector", "")),
        "timeframe": str(evidence.get("candidate_timeframe", "")),
        "discovery_stage": _discovery_stage(evidence, hypothesis),
        "contract_tier": contract_tier,
        "decision": decision,
        "failure_mode": _failure_mode(evidence),
        "median_forward_relative_return": terminal_return,
        "edge_vs_unconditional": _as_float(evidence.get("edge_vs_unconditional")),
        "edge_vs_cluster": edge_cluster,
        "hit_rate": hit_rate,
        "mfe_mae_ratio": mfe_mae,
        "median_drawdown": drawdown,
        "asymmetry_score": _as_float(evidence.get("asymmetry_score")) or 0.0,
        "sample_size": _as_int(evidence.get("sample_size")),
        "unique_symbols": _as_int(evidence.get("unique_symbols")),
        "event_clusters": _as_int(evidence.get("unique_event_clusters")),
        "time_split_pass": validation_status == "time_split_supported",
        "matched_null_pass": p_value is not None and p_value < 0.05,
        "same_cluster_pass": edge_cluster is not None and edge_cluster > 0,
        "strict_survivor_count": _as_int(evidence.get("strict_positive_survivors")),
        "strict_negative_survivor_count": _as_int(evidence.get("strict_negative_survivors")),
        "positive_useful_rows": _as_int(evidence.get("positive_useful_rows")),
        "passes_bullish_contract": bool(evidence.get("passes_bullish_contract")),
        "source_grid_path": source_grid,
        "source_report_dir": str(loop_dir),
        "bullish_evidence_path": str(evidence_path),
        "ranked_csv_path": str(loop_dir / "grammar_search_ranked.csv"),
        "strict_referee_csv_path": str(loop_dir / "strict_referee.csv"),
    }


def build_evidence_mart(options: LabDirectorOptions) -> dict[str, Any]:
    """Normalize lab-loop artifacts into one director-readable evidence table."""
    rows: list[dict[str, Any]] = []
    for evidence_path in sorted(options.report_root.glob("**/loop_*/bullish_evidence.yaml")):
        rows.append(_mart_row_from_loop(evidence_path.parent, options))

    rows.sort(key=lambda row: (int(row.get("loop_number", 0)), str(row.get("hypothesis_id", ""))))
    session_id = _latest_session_id(options)
    return {
        "model": EVIDENCE_MART_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": session_id,
        "row_count": len(rows),
        "inputs": {
            "report_root": str(options.report_root),
            "state_path": str(options.state_path),
            "runtime_queue_path": str(options.runtime_queue_path),
            "concept_scoreboard_path": str(options.concept_scoreboard_path),
            "evidence_ledger_path": str(options.evidence_ledger_path),
        },
        "rows": rows,
    }


def write_evidence_mart(mart: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = output_dir / "evidence_mart.yaml"
    csv_path = output_dir / "evidence_mart.csv"
    atomic_write_yaml(yaml_path, mart)
    rows = mart.get("rows", [])
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return {"yaml": yaml_path, "csv": csv_path}


def _claim_kind(rows: list[dict[str, Any]]) -> str:
    claim_types = Counter(str(row.get("claim_type", "")) for row in rows)
    setup_class = str(rows[0].get("setup_class", "")) if rows else ""
    if "warning_blocker" in claim_types:
        return "blocker"
    if "bullish_permission" in claim_types:
        return "permission"
    if "fresh_leader" in setup_class:
        return "permission"
    if "failed_weakness" in setup_class:
        return "permission"
    if "bullish_entry" in claim_types:
        return "entry"
    return "path_management"


def _suspected_drivers(rows: list[dict[str, Any]]) -> list[str]:
    text = " ".join(str(row.get("setup_class", "")) + " " + str(row.get("hypothesis_id", "")) for row in rows)
    drivers: list[str] = []
    mapping = {
        "reset_depth": ("deep_reset", "recent_signal_low", "reset"),
        "reclaim_timing": ("reclaim", "viscosity"),
        "compression": ("compression",),
        "warning_filter": ("warning_absent", "warning_filter"),
        "parent_context": ("parent", "benchmark", "regime"),
        "fresh_leadership": ("fresh_leader", "leader"),
        "timeframe_regime": ("1d", "4h", "12h", "timeframe"),
    }
    for driver, tokens in mapping.items():
        if any(token in text for token in tokens):
            drivers.append(driver)
    return drivers or ["unknown_driver"]


def _best_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def sort_key(row: dict[str, Any]) -> tuple[float, float, float, int]:
        return (
            _as_float(row.get("asymmetry_score")) or 0.0,
            _as_float(row.get("median_forward_relative_return")) or -999.0,
            _as_float(row.get("mfe_mae_ratio")) or -999.0,
            int(row.get("sample_size", 0) or 0),
        )

    return sorted(rows, key=sort_key, reverse=True)[0]


def _evidence_level(rows: list[dict[str, Any]]) -> str:
    if any(bool(row.get("passes_bullish_contract")) or row.get("contract_tier") == "strict_validated" for row in rows):
        return "L3_attributed"
    if any(row.get("contract_tier") in {"asymmetric_candidate", "path_watchlist"} for row in rows):
        return "L2_discovered"
    if any(row.get("contract_tier") == "blocker" for row in rows):
        return "rejected"
    return "L1_seen"


def _known_failures(rows: list[dict[str, Any]]) -> list[str]:
    failures = sorted(
        {
            str(row.get("failure_mode", ""))
            for row in rows
            if str(row.get("failure_mode", "")).strip()
        }
    )
    if any(int(row.get("event_clusters", 0) or 0) > 0 and int(row.get("event_clusters", 0) or 0) < 8 for row in rows):
        failures.append("cluster_concentrated")
    if not any(row.get("contract_tier") == "strict_validated" for row in rows):
        failures.append("no_strict_validated_contract")
    return sorted(set(failures))


def _next_required_tests(rows: list[dict[str, Any]], level: str) -> list[str]:
    drivers = set(_suspected_drivers(rows))
    tests: list[str] = []
    if level in {"L2_discovered", "L3_attributed"}:
        if "reset_depth" in drivers:
            tests.append("ablate_reset_depth")
        if "reclaim_timing" in drivers:
            tests.append("ablate_reclaim_timing")
        if "compression" in drivers:
            tests.append("test_compression_dependency")
        if "warning_filter" in drivers:
            tests.append("test_warning_filter_dependency")
        if "parent_context" in drivers:
            tests.append("test_parent_context_dependency")
        tests.extend(["direction_flip_counterexample", "entry_lag_sensitivity", "cooldown_sensitivity"])
    if level == "L3_attributed":
        tests.append("fresh_split_validation")
    else:
        tests.append("strict_validation")
    if any(int(row.get("event_clusters", 0) or 0) < 8 for row in rows):
        tests.append("increase_event_cluster_diversity")
    return sorted(set(tests))


def _confidence_score(rows: list[dict[str, Any]], level: str) -> int:
    score = 0.0
    for row in rows:
        tier = row.get("contract_tier")
        if tier == "path_watchlist":
            score += 6
        elif tier == "asymmetric_candidate":
            score += 11
        elif tier == "strict_validated":
            score += 22
        terminal = _as_float(row.get("median_forward_relative_return")) or 0.0
        hit_rate = _as_float(row.get("hit_rate")) or 0.0
        mfe_mae = _as_float(row.get("mfe_mae_ratio")) or 0.0
        sample = int(row.get("sample_size", 0) or 0)
        clusters = int(row.get("event_clusters", 0) or 0)
        score += min(max(terminal, 0.0) * 120, 12)
        score += min(max(hit_rate - 0.40, 0.0) * 25, 8)
        score += min(max(mfe_mae - 1.0, 0.0) * 3, 10)
        score += min(sample / 10, 6)
        score += min(clusters / 4, 6)
        if clusters and clusters < 8:
            score -= 10
        if row.get("decision") == "archive":
            score -= 5
    if level in {"L1_seen", "rejected"}:
        score = min(score, 30)
    if level == "L2_discovered":
        score = min(score, 60)
    if level == "L3_attributed":
        score = min(score, 80)
    return int(max(0, min(round(score), 100)))


def _belief_claim(setup_class: str, timeframe: str, rows: list[dict[str, Any]]) -> str:
    kind = _claim_kind(rows)
    label = setup_class.replace("_", " ") or "Riskflow setup"
    suffix = f" on {timeframe}" if timeframe else ""
    if kind == "entry":
        return f"{label} may improve bullish entry path quality{suffix}."
    if kind == "permission":
        return f"{label} may be more useful as a bullish permission/filter condition{suffix}."
    if kind == "blocker":
        return f"{label} may identify blocker conditions rather than standalone long entries{suffix}."
    return f"{label} may improve bullish path management{suffix}."


def build_belief_graph(mart: dict[str, Any]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in mart.get("rows", []):
        setup_class = str(row.get("setup_class") or row.get("root_id") or "unknown_setup")
        timeframe = str(row.get("timeframe") or "mixed")
        groups[(setup_class, timeframe)].append(row)

    beliefs: list[dict[str, Any]] = []
    for (setup_class, timeframe), rows in sorted(groups.items()):
        level = _evidence_level(rows)
        best = _best_row(rows)
        support = [
            row
            for row in rows
            if row.get("contract_tier") in PROMISING_TIERS or row.get("decision") in SUPPORTING_DECISIONS
        ]
        contradictions = [
            row
            for row in rows
            if row.get("contract_tier") in {"archive", "blocker"} or row.get("decision") == "archive"
        ]
        claim_id = _safe_slug(f"{setup_class}_{timeframe}")
        confidence = _confidence_score(rows, level)
        status = "promising_unvalidated" if level in {"L2_discovered", "L3_attributed"} else "archived"
        if level == "rejected":
            status = "rejected"
        belief = {
            "claim_id": claim_id,
            "plain_english_claim": _belief_claim(setup_class, timeframe, rows),
            "claim_kind": _claim_kind(rows),
            "status": status,
            "setup_class": setup_class,
            "timeframes": sorted({str(row.get("timeframe") or "mixed") for row in rows}),
            "root_ids": sorted({str(row.get("root_id", "")) for row in rows if row.get("root_id")}),
            "evidence_level": level,
            "confidence_score": confidence,
            "known_failure_modes": _known_failures(rows),
            "suspected_drivers": _suspected_drivers(rows),
            "supporting_trials": [row["trial_id"] for row in support],
            "contradicting_trials": [row["trial_id"] for row in contradictions],
            "evidence_refs": [
                {
                    "trial_id": row["trial_id"],
                    "loop_number": row.get("loop_number"),
                    "hypothesis_id": row.get("hypothesis_id"),
                    "contract_tier": row.get("contract_tier"),
                    "decision": row.get("decision"),
                    "report_dir": row.get("source_report_dir"),
                }
                for row in rows[:20]
            ],
            "best_trial": {
                "trial_id": best.get("trial_id"),
                "hypothesis_id": best.get("hypothesis_id"),
                "source_grid_path": best.get("source_grid_path"),
                "source_report_dir": best.get("source_report_dir"),
                "contract_tier": best.get("contract_tier"),
                "median_forward_relative_return": best.get("median_forward_relative_return"),
                "hit_rate": best.get("hit_rate"),
                "mfe_mae_ratio": best.get("mfe_mae_ratio"),
                "sample_size": best.get("sample_size"),
                "unique_symbols": best.get("unique_symbols"),
                "event_clusters": best.get("event_clusters"),
            },
            "next_required_tests": _next_required_tests(rows, level),
            "promotion_blockers": [
                blocker
                for blocker in _known_failures(rows)
                if blocker in {"no_strict_validated_contract", "cluster_concentrated"}
            ],
            "product_translation_status": "not_eligible" if level != "L4_validated" else "sidecar_candidate",
            "do_not_repeat": sorted(
                {
                    str(row.get("root_id", ""))
                    for row in rows
                    if row.get("contract_tier") == "archive" and row.get("root_id")
                }
            ),
        }
        beliefs.append(belief)

    beliefs.sort(key=lambda item: (int(item.get("confidence_score", 0)), len(item.get("supporting_trials", []))), reverse=True)
    return {
        "model": BELIEF_GRAPH_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": mart.get("session_id", "ad_hoc"),
        "belief_count": len(beliefs),
        "beliefs": beliefs,
    }


def write_belief_graph(graph: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "belief_graph.yaml"
    atomic_write_yaml(path, graph)
    return path


def _listify_param_grid(parameter_grid: dict[str, Any]) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    for key, value in parameter_grid.items():
        if isinstance(value, list):
            result[key] = list(value)
        else:
            result[key] = [value]
    return result


def _load_source_family(source_grid_path: str, source_root: Path) -> dict[str, Any] | None:
    if not source_grid_path:
        return None
    path = Path(source_grid_path)
    if not path.is_absolute():
        path = source_root / path
    if not path.exists():
        return None
    payload = _read_yaml(path)
    families = payload.get("families", [])
    if not isinstance(families, list) or not families:
        return None
    family = families[0]
    return family if isinstance(family, dict) else None


def _first_param(parameter_grid: dict[str, list[Any]], key: str) -> Any:
    values = parameter_grid.get(key, [])
    return values[0] if values else None


def _director_specs_for_belief(belief: dict[str, Any], family: dict[str, Any]) -> list[dict[str, Any]]:
    parameter_grid = _listify_param_grid(family.get("parameter_grid", {}))
    direction = str(family.get("direction", "positive"))
    opposite = "negative" if direction == "positive" else "positive"
    specs: list[dict[str, Any]] = []

    if "min_recent_signal_low" in parameter_grid:
        base = _as_float(_first_param(parameter_grid, "min_recent_signal_low")) or -1.0
        specs.append(
            {
                "name": "ablate_reset_depth",
                "stage": "causal_decomposition",
                "discovery_mode": "attribution",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {"min_recent_signal_low": sorted({base, -1.0, -0.5})},
                "question": "Does reset depth drive the positive path, or does a looser reset behave the same?",
                "failure_mode": "reset_depth_not_causal",
                "expected_information_gain": 0.90,
            }
        )
    if "trigger" in parameter_grid:
        specs.append(
            {
                "name": "ablate_reclaim_timing",
                "stage": "causal_decomposition",
                "discovery_mode": "attribution",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {"trigger": ["zero_reclaim", "viscosity_reclaim"]},
                "question": "Does the edge require viscosity reclaim timing, or does any reclaim work?",
                "failure_mode": "reclaim_timing_not_causal",
                "expected_information_gain": 0.88,
            }
        )
    if "min_compression" in parameter_grid:
        specs.append(
            {
                "name": "compression_dependency",
                "stage": "causal_decomposition",
                "discovery_mode": "attribution",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {"min_compression": [0.0, _first_param(parameter_grid, "min_compression")]},
                "question": "Is compression required for the path edge?",
                "failure_mode": "compression_not_causal",
                "expected_information_gain": 0.82,
            }
        )
    if "require_warning_absent" in parameter_grid:
        specs.append(
            {
                "name": "warning_filter_dependency",
                "stage": "causal_decomposition",
                "discovery_mode": "attribution",
                "claim_type": "bullish_permission",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {"require_warning_absent": [False]},
                "question": "Does warning absence improve the setup, or is it unnecessary filtering?",
                "failure_mode": "warning_filter_not_causal",
                "expected_information_gain": 0.86,
            }
        )
    if "min_benchmark_return" in parameter_grid or "min_relative_slope" in parameter_grid:
        updates: dict[str, Any] = {}
        if "min_benchmark_return" in parameter_grid:
            updates["min_benchmark_return"] = [0.0, 0.02]
        if "min_relative_slope" in parameter_grid:
            base_slope = _as_float(_first_param(parameter_grid, "min_relative_slope")) or 0.05
            updates["min_relative_slope"] = sorted({0.0, round(base_slope / 2, 4), base_slope})
        specs.append(
            {
                "name": "parent_context_dependency",
                "stage": "causal_decomposition",
                "discovery_mode": "attribution",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": updates,
                "question": "Does parent/relative context drive the setup edge?",
                "failure_mode": "parent_context_not_causal",
                "expected_information_gain": 0.80,
            }
        )

    specs.extend(
        [
            {
                "name": "validation_lag1_frozen",
                "stage": "validation",
                "discovery_mode": "validation",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {},
                "entry_lag_bars": 1,
                "question": "Does the frozen rule preserve its baseline lag-1 path behavior after first-stage controls?",
                "failure_mode": "baseline_lag_not_stable",
                "expected_information_gain": 0.74,
            },
            {
                "name": "validation_lag0",
                "stage": "validation",
                "discovery_mode": "validation",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {},
                "entry_lag_bars": 0,
                "question": "Does the frozen rule survive entry lag 0?",
                "failure_mode": "lag_sensitive",
                "expected_information_gain": 0.72,
            },
            {
                "name": "validation_lag2",
                "stage": "validation",
                "discovery_mode": "validation",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {},
                "entry_lag_bars": 2,
                "question": "Does the frozen rule survive entry lag 2?",
                "failure_mode": "lag_sensitive",
                "expected_information_gain": 0.72,
            },
            {
                "name": "validation_cooldown60",
                "stage": "validation",
                "discovery_mode": "validation",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {},
                "cooldown_bars": 60,
                "question": "Does the frozen rule survive 60-bar cooldown stress?",
                "failure_mode": "cooldown_sensitive",
                "expected_information_gain": 0.70,
            },
            {
                "name": "validation_cooldown30",
                "stage": "validation",
                "discovery_mode": "validation",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {},
                "cooldown_bars": 30,
                "question": "Does the frozen rule survive a moderate 30-bar cooldown stress?",
                "failure_mode": "cooldown_sensitive",
                "expected_information_gain": 0.69,
            },
            {
                "name": "direction_flip_counterexample",
                "stage": "counterexample",
                "discovery_mode": "counterexample",
                "claim_type": "warning_blocker" if opposite == "negative" else "control",
                "track": "warning" if opposite == "negative" else "bullish_setup",
                "direction": opposite,
                "updates": {},
                "question": "Does the same frozen shape have sign-specific behavior?",
                "failure_mode": "direction_not_specific",
                "expected_information_gain": 0.75,
            },
            {
                "name": "timeframe_transfer",
                "stage": "validation",
                "discovery_mode": "validation",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {},
                "timeframes": ["12h", "4h"],
                "question": "Does the setup transfer outside its best timeframe?",
                "failure_mode": "timeframe_not_transferable",
                "expected_information_gain": 0.68,
            },
            {
                "name": "timeframe_transfer_1h",
                "stage": "validation",
                "discovery_mode": "validation",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": {},
                "timeframes": ["1h"],
                "question": "Does the setup collapse on 1h, or is it portable to lower-timeframe structure?",
                "failure_mode": "timeframe_not_transferable",
                "expected_information_gain": 0.62,
            },
        ]
    )
    counter_updates: dict[str, Any] = {}
    if "require_warning_absent" in parameter_grid:
        counter_updates["require_warning_absent"] = [False]
    if "min_benchmark_return" in parameter_grid:
        counter_updates["min_benchmark_return"] = [-0.05, 0.0]
    if "min_relative_slope" in parameter_grid:
        counter_updates["min_relative_slope"] = [-0.05, 0.0]
    if "min_compression" in parameter_grid:
        counter_updates["min_compression"] = [0.0]
    if counter_updates:
        specs.append(
            {
                "name": "falsification_relaxed_context",
                "stage": "counterexample",
                "discovery_mode": "counterexample",
                "claim_type": "control",
                "track": "bullish_setup",
                "direction": direction,
                "updates": counter_updates,
                "question": "Does the setup still work when warning/context/compression constraints are relaxed?",
                "failure_mode": "context_filters_not_causal",
                "expected_information_gain": 0.73,
            }
        )
    return specs


def _grid_for_spec(family: dict[str, Any], spec: dict[str, Any], family_id: str) -> dict[str, Any]:
    parameter_grid = _listify_param_grid(family.get("parameter_grid", {}))
    for key, value in spec.get("updates", {}).items():
        parameter_grid[key] = list(value) if isinstance(value, list) else [value]
    return {
        "model": "riskflow_grammar_search_v0",
        "generated_from": "riskflow_lab_director_v0",
        "families": [
            {
                "family_id": family_id,
                "direction": spec.get("direction", family.get("direction", "positive")),
                "detector": family.get("detector"),
                "description": spec.get("question", "Director-generated experiment."),
                "parameter_grid": parameter_grid,
            }
        ],
    }


def design_experiments(
    belief_graph: dict[str, Any],
    *,
    output_queue_path: Path,
    generated_grid_dir: Path,
    max_new_hypotheses: int,
    source_root: Path = Path("."),
    existing_hypothesis_ids: set[str] | None = None,
) -> dict[str, Any]:
    generated_grid_dir.mkdir(parents=True, exist_ok=True)
    existing_hypothesis_ids = existing_hypothesis_ids or set()
    candidate_beliefs = [
        belief
        for belief in belief_graph.get("beliefs", [])
        if belief.get("status") == "promising_unvalidated" and belief.get("evidence_level") in {"L2_discovered", "L3_attributed"}
    ]
    candidate_beliefs.sort(key=lambda belief: int(belief.get("confidence_score", 0)), reverse=True)

    queue_items: list[dict[str, Any]] = []
    experiments: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    priority = 1
    for belief in candidate_beliefs:
        if len(queue_items) >= max_new_hypotheses:
            break
        best = belief.get("best_trial", {})
        family = _load_source_family(str(best.get("source_grid_path", "")), source_root)
        if not family:
            skipped.append({"claim_id": str(belief.get("claim_id", "")), "reason": "missing_source_grid"})
            continue
        specs = _director_specs_for_belief(belief, family)
        for spec in specs:
            if len(queue_items) >= max_new_hypotheses:
                break
            claim_id = str(belief.get("claim_id", "belief"))
            item_id = _safe_slug_with_hash(f"director_{claim_id}_{spec['name']}", max_length=96)
            if item_id in existing_hypothesis_ids:
                skipped.append({"claim_id": claim_id, "reason": f"already_seen:{item_id}"})
                continue
            family_id = _safe_slug_with_hash(f"{family.get('family_id', claim_id)}_{spec['name']}", max_length=120)
            grid = _grid_for_spec(family, spec, family_id)
            grid_path = generated_grid_dir / f"{item_id}.yaml"
            atomic_write_yaml(grid_path, grid)
            root_ids = list(belief.get("root_ids", []))
            root_id = str((root_ids[0] if root_ids else "") or claim_id)
            lineage = lineage_fingerprint(root_id, claim_id, item_id, spec["name"], "director")
            queue_item = {
                "id": item_id,
                "root_id": root_id,
                "lineage_fingerprint": lineage,
                "track": spec["track"],
                "status": "new",
                "promotion_level": "L1_encoded",
                "priority": priority,
                "source": str(grid_path),
                "hypothesis": spec["question"],
                "claim_type": spec["claim_type"],
                "setup_class": belief.get("setup_class", ""),
                "discovery_mode": spec["discovery_mode"],
                "research_stage": spec["stage"],
                "source_belief_id": claim_id,
                "research_question": spec["question"],
                "expected_information_gain": spec["expected_information_gain"],
                "expected_failure_mode": spec["failure_mode"],
                "required_controls": sorted(set(belief.get("next_required_tests", []))),
                "measurable_primitives": sorted(set(belief.get("suspected_drivers", [])) | {spec["stage"]}),
                "branch_budget": {"max_generation": 1},
                "path_objective": {
                    "min_sample_size": 30,
                    "min_unique_symbols": 12,
                    "min_event_clusters": 12,
                    "min_hit_rate": 0.55,
                    "asymmetric_min_hit_rate": 0.40,
                    "asymmetric_min_terminal_relative_return": 0.03,
                    "min_mfe_mae_ratio": 1.50,
                    "asymmetric_min_mfe_mae_ratio": 1.60,
                    "max_median_drawdown": -0.35,
                },
                "production_effect": "none",
                "next_action": "Run as a director-designed second-stage research test.",
            }
            if "entry_lag_bars" in spec:
                queue_item["entry_lag_bars"] = int(spec["entry_lag_bars"])
            if "cooldown_bars" in spec:
                queue_item["cooldown_bars"] = int(spec["cooldown_bars"])
            if "timeframes" in spec:
                queue_item["timeframes"] = list(spec["timeframes"])
            queue_items.append(queue_item)
            experiments.append(
                {
                    "experiment_id": item_id,
                    "source_belief_id": claim_id,
                    "experiment_type": spec["stage"],
                    "hypothesis": spec["question"],
                    "frozen_rule_shape": str(best.get("source_grid_path", "")),
                    "generated_grid_path": str(grid_path),
                    "generated_queue_path": str(output_queue_path),
                    "success_criteria": "Improves or preserves bullish contract tier with better attribution.",
                    "failure_criteria": spec["failure_mode"],
                }
            )
            priority += 1

    queue = {
        "model": DIRECTOR_QUEUE_MODEL,
        "date": utc_now_iso().split("T", 1)[0],
        "generated_from": DIRECTOR_MODEL,
        "production_effect": "none",
        "default_timeframes": ["1d", "12h", "4h", "1h"],
        "default_outcome": "forward_relative_return_vs_basket",
        "strict_referee_required": True,
        "queue": queue_items,
    }
    stop_reason = ""
    if not queue_items:
        stop_reason = "no_valid_director_experiments"
        if skipped:
            stop_reason = "missing_source_grids_for_promising_beliefs"
    return {
        "model": EXPERIMENT_PLAN_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": belief_graph.get("session_id", "ad_hoc"),
        "research_mode": "decompose_promising_family" if queue_items else "stop_research_saturated",
        "stop_reason": stop_reason,
        "experiments": experiments,
        "skipped": skipped,
        "generated_queue": queue,
        "output_queue_path": str(output_queue_path),
    }


def audit_director_plan(plan: dict[str, Any], *, source_root: Path = Path(".")) -> dict[str, Any]:
    queue = plan.get("generated_queue", {})
    errors = validate_lab_queue(queue, validate_sources=True, source_root=source_root)
    root_counts = Counter(str(item.get("root_id", "")) for item in queue.get("queue", []))
    for index, item in enumerate(queue.get("queue", [])):
        label = f"queue[{index}]"
        for field in ("research_stage", "root_id", "claim_type", "setup_class", "expected_failure_mode", "research_question"):
            if not item.get(field):
                errors.append(f"{label}.{field} is required by lab-director")
        if item.get("research_stage") not in VALID_RESEARCH_STAGES:
            errors.append(f"{label}.research_stage is invalid")
        if item.get("production_effect") not in {None, "none"}:
            errors.append(f"{label}.production_effect must remain none")
        if item.get("formula_change_required"):
            errors.append(f"{label}.formula_change_required is not allowed")
    total = max(1, len(queue.get("queue", [])))
    for root_id, count in root_counts.items():
        if len(root_counts) > 1 and total >= 10 and count / total > 0.5:
            errors.append(f"root {root_id} exceeds director root concentration cap")
    return {
        "model": "riskflow_lab_director_audit_v0",
        "generated_at": utc_now_iso(),
        "passed": not errors,
        "errors": errors,
    }


def _report_lines(
    *,
    mart: dict[str, Any],
    belief_graph: dict[str, Any],
    plan: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
) -> list[str]:
    lines = [
        "# Riskflow Lab Director Report",
        "",
        f"Generated: {utc_now_iso()}",
        f"Session: {mart.get('session_id', 'ad_hoc')}",
        f"Evidence rows: {mart.get('row_count', 0)}",
        f"Beliefs: {belief_graph.get('belief_count', 0)}",
        "",
        "## Top Beliefs",
        "",
    ]
    for belief in belief_graph.get("beliefs", [])[:10]:
        best = belief.get("best_trial", {})
        lines.append(
            "- "
            f"{belief.get('claim_id')}: {belief.get('evidence_level')} "
            f"confidence={belief.get('confidence_score')} "
            f"tier={best.get('contract_tier')} "
            f"ret={best.get('median_forward_relative_return')} "
            f"hit={best.get('hit_rate')} "
            f"next={', '.join(belief.get('next_required_tests', [])[:4])}"
        )
    if not belief_graph.get("beliefs"):
        lines.append("- No beliefs generated from current evidence.")
    if plan is not None:
        lines.extend(
            [
                "",
                "## Next Experiment Plan",
                "",
                f"Mode: {plan.get('research_mode')}",
                f"Stop reason: {plan.get('stop_reason') or ''}",
                f"Generated experiments: {len(plan.get('experiments', []))}",
            ]
        )
        for experiment in plan.get("experiments", [])[:12]:
            lines.append(f"- {experiment.get('experiment_id')}: {experiment.get('hypothesis')}")
    if audit is not None:
        lines.extend(["", "## Audit", "", f"Passed: {audit.get('passed')}"])
        for error in audit.get("errors", []):
            lines.append(f"- {error}")
    return lines


def write_director_report(
    output_dir: Path,
    *,
    mart: dict[str, Any],
    belief_graph: dict[str, Any],
    plan: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
) -> Path:
    path = output_dir / "director_report.md"
    atomic_write_text(path, "\n".join(_report_lines(mart=mart, belief_graph=belief_graph, plan=plan, audit=audit)) + "\n")
    return path


def run_director_inspect(options: LabDirectorOptions) -> dict[str, Any]:
    mart = build_evidence_mart(options)
    belief_graph = build_belief_graph(mart)
    output_dir = _director_output_dir(options, str(mart.get("session_id", "ad_hoc")))
    mart_paths = write_evidence_mart(mart, output_dir)
    belief_path = write_belief_graph(belief_graph, output_dir)
    report_path = write_director_report(output_dir, mart=mart, belief_graph=belief_graph)
    return {
        "mart": mart,
        "belief_graph": belief_graph,
        "paths": {
            "output_dir": output_dir,
            "evidence_mart_yaml": mart_paths["yaml"],
            "evidence_mart_csv": mart_paths["csv"],
            "belief_graph": belief_path,
            "report": report_path,
        },
    }


def _write_plan_artifacts(
    options: LabDirectorOptions,
    output_dir: Path,
    plan: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Path]:
    plan_path = output_dir / "next_experiment_plan.yaml"
    proposed_queue_path = output_dir / "director_candidate_queue.yaml"
    audit_path = output_dir / "director_audit.yaml"
    atomic_write_yaml(plan_path, plan)
    atomic_write_yaml(proposed_queue_path, plan.get("generated_queue", {}))
    atomic_write_yaml(audit_path, audit)
    paths = {"plan": plan_path, "proposed_queue": proposed_queue_path, "audit": audit_path}
    if options.apply:
        options.output_queue_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_yaml(options.output_queue_path, plan.get("generated_queue", {}))
        paths["applied_queue"] = options.output_queue_path
    return paths


def append_queue_to_runtime(runtime_queue_path: Path, director_queue: dict[str, Any]) -> int:
    runtime = load_lab_queue(runtime_queue_path) if runtime_queue_path.exists() else {"model": DIRECTOR_QUEUE_MODEL, "queue": []}
    existing_ids = {str(item.get("id", "")) for item in runtime.get("queue", [])}
    added = 0
    for item in director_queue.get("queue", []):
        item_id = str(item.get("id", ""))
        if not item_id or item_id in existing_ids:
            continue
        runtime.setdefault("queue", []).append(item)
        existing_ids.add(item_id)
        added += 1
    if added:
        atomic_write_yaml(runtime_queue_path, runtime)
    return added


def run_director_plan_next(options: LabDirectorOptions) -> dict[str, Any]:
    inspect_result = run_director_inspect(options)
    mart = inspect_result["mart"]
    belief_graph = inspect_result["belief_graph"]
    output_dir = Path(inspect_result["paths"]["output_dir"])
    grid_dir = (
        options.generated_grid_dir / str(mart.get("session_id", "ad_hoc"))
        if options.apply
        else output_dir / "generated_grids"
    )
    queue_path = options.output_queue_path if options.apply else output_dir / "director_candidate_queue.yaml"
    existing_hypothesis_ids: set[str] = set()
    if options.runtime_queue_path.exists():
        try:
            runtime_queue = load_lab_queue(options.runtime_queue_path)
        except Exception:
            runtime_queue = {"queue": []}
        existing_hypothesis_ids.update(str(item.get("id", "")) for item in runtime_queue.get("queue", []))
    state = load_lab_state(options.state_path)
    existing_hypothesis_ids.update(str(item) for item in state.get("completed_hypothesis_ids", []))
    plan = design_experiments(
        belief_graph,
        output_queue_path=queue_path,
        generated_grid_dir=grid_dir,
        max_new_hypotheses=options.max_new_hypotheses,
        source_root=options.source_root,
        existing_hypothesis_ids=existing_hypothesis_ids,
    )
    audit = audit_director_plan(plan, source_root=options.source_root)
    if options.apply and not audit["passed"]:
        plan["stop_reason"] = "director_audit_failed"
    paths = _write_plan_artifacts(options, output_dir, plan, audit)
    runtime_added = 0
    if options.apply and options.apply_to_runtime and audit["passed"]:
        runtime_added = append_queue_to_runtime(options.runtime_queue_path, plan.get("generated_queue", {}))
    report_path = write_director_report(output_dir, mart=mart, belief_graph=belief_graph, plan=plan, audit=audit)
    return {
        "mart": mart,
        "belief_graph": belief_graph,
        "plan": plan,
        "audit": audit,
        "runtime_added": runtime_added,
        "paths": {**inspect_result["paths"], **paths, "report": report_path},
    }
