from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .lab_loop import atomic_write_text, atomic_write_yaml, load_yaml_file
from .lab_ops import (
    LAB_OPS_REPORT_ROOT,
    LAB_OPS_RUNTIME_ROOT,
    LabOpsOptions,
    run_lab_ops_report,
    run_lab_ops_run,
    run_lab_ops_status,
)


CEO_MANIFEST_MODEL = "riskflow_ceo_manifest_v0"
CEO_COMPANY_STATUS_MODEL = "riskflow_ceo_company_status_v0"
CEO_PRODUCT_DELTA_MODEL = "riskflow_ceo_product_delta_scoreboard_v0"
CEO_CHAMPION_CHALLENGER_ACTION_PLAN_MODEL = "riskflow_ceo_champion_challenger_action_plan_v0"
CEO_CHAMPION_CHALLENGER_RESULTS_MODEL = "riskflow_ceo_champion_challenger_results_v0"
CEO_ACTION_RESULT_MODEL = "riskflow_ceo_binding_action_result_v0"
CEO_CAPABILITY_GAP_MODEL = "riskflow_ceo_capability_gap_v0"
CEO_SELF_AUDIT_MODEL = "riskflow_ceo_self_audit_v0"
CEO_INFRA_DELTA_MODEL = "riskflow_ceo_research_infra_delta_v0"
CEO_UNDERSTANDING_DELTA_MODEL = "riskflow_ceo_understanding_delta_v0"
CEO_RISK_REGISTER_MODEL = "riskflow_ceo_risk_register_v0"
CEO_KNOWLEDGE_GRAPH_DELTA_MODEL = "riskflow_ceo_knowledge_graph_delta_v0"
CEO_HEARTBEAT_STATUS_MODEL = "riskflow_ceo_heartbeat_status_v0"
CEO_STOP_MODEL = "riskflow_ceo_stop_request_v0"

CEO_REPORT_ROOT = Path("reports/ceo_runs")

PRODUCT_LANES = {
    "bullish_permission",
    "warning_blocker",
    "invalidation",
    "reset_quality",
    "gradient_interpretation",
    "path_management",
    "cross_asset_regime",
}

TERMINAL_TRUE_BLOCKERS = {
    "missing_market_data",
    "state_corrupt",
    "artifact_hygiene_required",
    "director_audit_failed",
    "meta_audit_failed",
    "governed_recovery_audit_failed",
}

HEARTBEAT_CONTINUE_DECISIONS = {
    "run_champion_challenger",
    "patch_research_infra",
    "continue_governed_research",
    "broaden_hypothesis_source",
}


@dataclass(frozen=True)
class CeoOpsOptions:
    objective: str = "bullish-positive"
    run_id: str | None = None
    lab_run_id: str | None = None
    queue_path: Path = Path("research/lab_loop/hypothesis_queue.yaml")
    config_path: Path = Path("configs/meme_universe.yaml")
    data_dir: Path = Path("data/raw")
    timeframes: tuple[str, ...] = ("1d", "12h", "4h", "1h")
    block_epochs: int = 2
    epoch_size: int = 5
    max_hours: float | None = None
    min_sample_size: int = 20
    entry_lag_bars: int = 1
    cooldown_bars: int | None = None
    strict_referee: bool = True
    strict_null_iterations: int = 300
    strict_random_seed: int = 29
    checkpoint_interval: int = 5
    apply: bool = False
    resume: bool = False
    dry_run: bool = False
    source_root: Path = Path(".")
    report_root: Path = CEO_REPORT_ROOT
    lab_ops_report_root: Path = LAB_OPS_REPORT_ROOT
    lab_ops_runtime_root: Path = LAB_OPS_RUNTIME_ROOT
    max_new_hypotheses: int = 30


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_ceo_run_id(objective: str = "bullish-positive") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = "".join(ch if ch.isalnum() else "_" for ch in objective.lower()).strip("_")
    return f"ceo_{stamp}_{slug or 'riskflow'}"


def resolve_ceo_run_id(options: CeoOpsOptions) -> str:
    return options.run_id or make_ceo_run_id(options.objective)


def resolve_lab_run_id(options: CeoOpsOptions, ceo_run_id: str) -> str:
    return options.lab_run_id or f"{ceo_run_id}_lab"


def ceo_dir(options: CeoOpsOptions, ceo_run_id: str) -> Path:
    return options.report_root / ceo_run_id


def ceo_stop_path(options: CeoOpsOptions, ceo_run_id: str) -> Path:
    return ceo_dir(options, ceo_run_id) / "stop.request"


def ceo_heartbeat_status_path(options: CeoOpsOptions, ceo_run_id: str) -> Path:
    return ceo_dir(options, ceo_run_id) / "heartbeat_status.yaml"


def ceo_action_ledger_path(options: CeoOpsOptions, ceo_run_id: str) -> Path:
    return ceo_dir(options, ceo_run_id) / "ceo_action_ledger.jsonl"


def _lab_runtime_root(options: CeoOpsOptions, lab_run_id: str) -> Path:
    return options.lab_ops_runtime_root / lab_run_id


def lab_stop_path(options: CeoOpsOptions, lab_run_id: str) -> Path:
    return _lab_runtime_root(options, lab_run_id) / "stop.request"


def _lab_state_exists(options: CeoOpsOptions, lab_run_id: str) -> bool:
    root = _lab_runtime_root(options, lab_run_id)
    return (root / "lab_state.json").exists() or (root / "runtime_queue.yaml").exists()


def is_stop_requested(options: CeoOpsOptions, ceo_run_id: str, lab_run_id: str) -> bool:
    return ceo_stop_path(options, ceo_run_id).exists() or lab_stop_path(options, lab_run_id).exists()


def _latest_child(path: Path, pattern: str) -> Path | None:
    if not path.exists():
        return None
    matches = sorted(path.glob(pattern), key=lambda item: item.stat().st_mtime)
    return matches[-1] if matches else None


def _load_yaml_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = load_yaml_file(path)
    return payload if isinstance(payload, dict) else {}


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


def _append_action_ledger(options: CeoOpsOptions, ceo_run_id: str, entry: dict[str, Any]) -> Path:
    path = ceo_action_ledger_path(options, ceo_run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_json_safe(entry), sort_keys=True) + "\n")
    return path


def _read_action_ledger(options: CeoOpsOptions, ceo_run_id: str) -> list[dict[str, Any]]:
    path = ceo_action_ledger_path(options, ceo_run_id)
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def _lab_root(options: CeoOpsOptions, lab_run_id: str) -> Path:
    return options.lab_ops_report_root / lab_run_id


def _latest_governance_dir(options: CeoOpsOptions, lab_run_id: str) -> Path | None:
    return _latest_child(_lab_root(options, lab_run_id) / "governance", "block_*")


def _load_latest_governance(options: CeoOpsOptions, lab_run_id: str) -> dict[str, Any]:
    root = _latest_governance_dir(options, lab_run_id)
    if root is None:
        return {"paths": {}}
    return {
        "blocker_audit": _load_yaml_if_exists(root / "blocker_audit.yaml"),
        "lane_assignment": _load_yaml_if_exists(root / "lane_assignment.yaml"),
        "validation_governance": _load_yaml_if_exists(root / "validation_decision.yaml"),
        "research_map": _load_yaml_if_exists(root / "research_map.yaml"),
        "paths": {
            "root": root,
            "blocker_audit": root / "blocker_audit.yaml",
            "lane_assignment": root / "lane_assignment.yaml",
            "validation_governance": root / "validation_decision.yaml",
            "research_map": root / "research_map.yaml",
        },
    }


def _load_lab_status(options: CeoOpsOptions, lab_run_id: str) -> dict[str, Any]:
    return _load_yaml_if_exists(_lab_root(options, lab_run_id) / "latest_status.yaml")


def _load_lab_manifest(options: CeoOpsOptions, lab_run_id: str) -> dict[str, Any]:
    return _load_yaml_if_exists(_lab_root(options, lab_run_id) / "run_manifest.yaml")


def _next_block_number(options: CeoOpsOptions, ceo_run_id: str) -> int:
    root = ceo_dir(options, ceo_run_id)
    if not root.exists():
        return 1
    existing = sorted(root.glob("executive_decision_packet_*.md"))
    return len(existing) + 1


def build_ceo_manifest(options: CeoOpsOptions, ceo_run_id: str, lab_run_id: str) -> dict[str, Any]:
    return {
        "model": CEO_MANIFEST_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "objective": options.objective,
        "default_block_epochs": options.block_epochs,
        "default_epoch_size": options.epoch_size,
        "timeframes": list(options.timeframes),
        "strict_referee": options.strict_referee,
        "governed_lab_ops": True,
        "commit_policy": "never_auto_commit",
        "production_change_policy": "proposal_only",
        "production_effect": "none",
    }


def build_company_status(options: CeoOpsOptions, ceo_run_id: str, lab_run_id: str) -> dict[str, Any]:
    lab_status = _load_lab_status(options, lab_run_id)
    lab_manifest = _load_lab_manifest(options, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    lane_assignment = governance.get("lane_assignment", {})
    validation = governance.get("validation_governance", {})
    research_map = governance.get("research_map", {})
    stop_reason = str(lab_status.get("stop_reason") or lab_manifest.get("stop_reason") or "")
    open_lanes = list(lane_assignment.get("open_lanes", []) or lab_status.get("governance", {}).get("open_lanes", []) or [])
    true_blocker = stop_reason in TERMINAL_TRUE_BLOCKERS
    if stop_reason in {"request_fresh_data", "governed_recovery_no_supported_specs"} and open_lanes:
        true_blocker = False
    return {
        "model": CEO_COMPANY_STATUS_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "objective": options.objective,
        "stop_requested": is_stop_requested(options, ceo_run_id, lab_run_id),
        "lab_status": {
            "status": lab_status.get("status", lab_manifest.get("status", "unknown")),
            "stop_reason": stop_reason,
            "completed_epochs": lab_status.get("completed_epochs", lab_manifest.get("completed_epochs", 0)),
            "completed_blocks": lab_status.get("completed_blocks", lab_manifest.get("completed_blocks", 0)),
            "last_completed_loop": lab_status.get("last_completed_loop"),
            "latest_process_score": lab_status.get("latest_process_score"),
            "latest_intervention": lab_status.get("latest_intervention"),
        },
        "governance": {
            "open_lanes": open_lanes,
            "all_lanes_blocked": lane_assignment.get("all_lanes_blocked", lab_status.get("governance", {}).get("all_lanes_blocked")),
            "lane_counts": lane_assignment.get("lane_counts", {}),
            "validation_decision_counts": validation.get("decision_counts", {}),
            "product_change_allowed": bool(validation.get("product_change_allowed", False)),
        },
        "research_map": {
            "node_count": len(research_map.get("nodes", []) or []),
            "edge_count": len(research_map.get("edges", []) or []),
            "validation_debt": research_map.get("views", {}).get("validation_debt", []),
            "product_ready_candidates": research_map.get("views", {}).get("product_ready_candidates", []),
        },
        "true_blocker": true_blocker,
        "production_effect": "none",
    }


def build_heartbeat_status(
    options: CeoOpsOptions,
    ceo_run_id: str,
    lab_run_id: str,
    *,
    block_number: int,
    company_status: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    decision_kind = str(decision.get("decision", "unknown"))
    stop_requested = is_stop_requested(options, ceo_run_id, lab_run_id)
    true_blocker = bool(company_status.get("true_blocker"))
    production_promotion_required = bool(company_status.get("governance", {}).get("product_change_allowed"))
    continue_recommended = (
        decision_kind in HEARTBEAT_CONTINUE_DECISIONS
        and not stop_requested
        and not true_blocker
        and not production_promotion_required
    )
    if decision_kind == "request_fresh_data":
        next_action = "Refresh or broaden the market data snapshot before continuing automated research."
    elif stop_requested:
        next_action = "Stop requested. Do not run another CEO block until the stop request is removed or replaced."
    elif true_blocker:
        next_action = "Resolve the true blocker before continuing automated research."
    elif production_promotion_required:
        next_action = "Write a promotion proposal and wait for explicit user approval before continuing production-facing work."
    else:
        next_action = _next_block_plan(decision)
    return {
        "model": CEO_HEARTBEAT_STATUS_MODEL,
        "generated_at": utc_now_iso(),
        "last_wake_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "last_block_number": block_number,
        "last_decision": decision_kind,
        "last_decision_rationale": decision.get("rationale", ""),
        "continue_recommended": continue_recommended,
        "stop_recommended": not continue_recommended,
        "stop_requested": stop_requested,
        "true_blocker": true_blocker,
        "production_promotion_required": production_promotion_required,
        "lab_status": company_status.get("lab_status", {}),
        "next_recommended_action": next_action,
        "stop_request_paths": {
            "ceo": str(ceo_stop_path(options, ceo_run_id)),
            "lab": str(lab_stop_path(options, lab_run_id)),
        },
        "production_effect": "none",
    }


def build_product_delta_scoreboard(governance: dict[str, Any]) -> dict[str, Any]:
    lane_assignment = governance.get("lane_assignment", {})
    validation = governance.get("validation_governance", {})
    decisions_by_id = {str(item.get("belief_id", "")): item for item in validation.get("decisions", []) or []}
    candidates: list[dict[str, Any]] = []
    for assignment in lane_assignment.get("assignments", []) or []:
        lane = str(assignment.get("lane", ""))
        belief_id = str(assignment.get("belief_id", ""))
        decision = decisions_by_id.get(belief_id, {})
        if lane not in PRODUCT_LANES or decision.get("decision") == "archive":
            continue
        candidates.append(
            {
                "belief_id": belief_id,
                "product_role": lane,
                "current_gate": decision.get("current_gate", ""),
                "validation_decision": decision.get("decision", ""),
                "evidence_level": assignment.get("evidence_level"),
                "confidence_score": assignment.get("confidence_score"),
                "champion": "core_signal_v0",
                "challenger": f"core_signal_v0_plus_{belief_id}",
                "comparison_status": "needs_champion_challenger",
                "production_effect": "none",
            }
        )
    return {
        "model": CEO_PRODUCT_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "champion": "core_signal_v0",
        "candidate_count": len(candidates),
        "chart_facing_value_status": "candidate_pipeline" if candidates else "no_product_delta_yet",
        "candidates": candidates,
        "required_metrics": [
            "forward_relative_return_vs_basket",
            "hit_rate",
            "mfe_mae",
            "max_drawdown",
            "missed_upside_cost",
            "avoided_downside_benefit",
            "event_diversity",
            "lag_sensitivity",
            "cooldown_sensitivity",
        ],
        "production_effect": "none",
    }


def build_champion_challenger_action_plan(product_delta: dict[str, Any]) -> dict[str, Any]:
    candidates = product_delta.get("candidates", []) or []
    work_items: list[dict[str, Any]] = []
    priority_by_role = {
        "warning_blocker": 1,
        "reset_quality": 2,
        "bullish_permission": 3,
        "gradient_interpretation": 4,
        "path_management": 5,
        "cross_asset_regime": 6,
        "invalidation": 7,
    }
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            priority_by_role.get(str(item.get("product_role", "")), 99),
            -(float(item.get("confidence_score") or 0)),
            str(item.get("belief_id", "")),
        ),
    )
    for index, candidate in enumerate(sorted_candidates, start=1):
        if candidate.get("comparison_status") != "needs_champion_challenger":
            continue
        work_items.append(
            {
                "priority": index,
                "belief_id": candidate.get("belief_id"),
                "product_role": candidate.get("product_role"),
                "champion": candidate.get("champion", "core_signal_v0"),
                "challenger": candidate.get("challenger"),
                "current_gate": candidate.get("current_gate"),
                "validation_decision": candidate.get("validation_decision"),
                "evidence_level": candidate.get("evidence_level"),
                "confidence_score": candidate.get("confidence_score"),
                "required_metrics": product_delta.get("required_metrics", []),
                "required_controls": [
                    "forward_relative_return_vs_basket",
                    "event_diversity",
                    "lag_sensitivity",
                    "cooldown_sensitivity",
                    "missed_upside_cost",
                    "avoided_downside_benefit",
                ],
                "minimum_decision": "compare_against_core_signal_v0_before_more_recovery_expansion",
                "production_effect": "none",
            }
        )
    return {
        "model": CEO_CHAMPION_CHALLENGER_ACTION_PLAN_MODEL,
        "generated_at": utc_now_iso(),
        "status": "ready" if work_items else "no_candidates",
        "champion": product_delta.get("champion", "core_signal_v0"),
        "candidate_count": len(work_items),
        "work_items": work_items,
        "next_action": (
            "run_top_priority_product_delta_comparisons"
            if work_items
            else "broaden_product_candidate_source"
        ),
        "production_effect": "none",
    }


def build_champion_challenger_results(action_plan: dict[str, Any], *, top_n: int | None = None) -> dict[str, Any]:
    work_items = list(action_plan.get("work_items", []) or [])
    if top_n is not None:
        work_items = work_items[: max(0, top_n)]
    results: list[dict[str, Any]] = []
    missing_metric_sources: list[str] = []
    for item in work_items:
        belief_id = str(item.get("belief_id", ""))
        metric_sources = item.get("metric_sources", []) or item.get("evidence_sources", []) or []
        status = "metric_source_missing" if not metric_sources else "ready_for_metric_comparison"
        if status == "metric_source_missing":
            missing_metric_sources.append(belief_id)
        results.append(
            {
                "belief_id": belief_id,
                "product_role": item.get("product_role"),
                "champion": item.get("champion", action_plan.get("champion", "core_signal_v0")),
                "challenger": item.get("challenger"),
                "comparison_status": status,
                "required_metrics": item.get("required_metrics", []),
                "required_controls": item.get("required_controls", []),
                "available_metric_sources": metric_sources,
                "decision": (
                    "capability_gap_required"
                    if status == "metric_source_missing"
                    else "run_metric_comparison_from_sources"
                ),
                "production_effect": "none",
            }
        )
    status = "no_candidates"
    if results and missing_metric_sources:
        status = "blocked_missing_metric_sources"
    elif results:
        status = "ready_for_metric_comparison"
    return {
        "model": CEO_CHAMPION_CHALLENGER_RESULTS_MODEL,
        "generated_at": utc_now_iso(),
        "status": status,
        "candidate_count": len(results),
        "missing_metric_source_count": len(missing_metric_sources),
        "missing_metric_sources": missing_metric_sources,
        "results": results,
        "next_action": (
            "build_product_delta_metric_source_extractor"
            if missing_metric_sources
            else "run_metric_comparison_from_sources"
            if results
            else "broaden_product_candidate_source"
        ),
        "production_effect": "none",
    }


def build_capability_gap(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    decision: str,
    missing_capability: str,
    reason: str,
    required_command: str,
    acceptance_criteria: list[str],
) -> dict[str, Any]:
    return {
        "model": CEO_CAPABILITY_GAP_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": decision,
        "missing_capability": missing_capability,
        "reason": reason,
        "required_command": required_command,
        "acceptance_criteria": acceptance_criteria,
        "autonomy_allowed": "research_infra_only",
        "forbidden_changes": [
            "core_signal_v0",
            "Pine_or_TradingView_defaults",
            "production_scores",
            "production_rankings",
            "production_states",
            "production_alerts",
        ],
        "production_effect": "none",
    }


def build_ceo_self_audit(action_result: dict[str, Any], ledger_entries: list[dict[str, Any]]) -> dict[str, Any]:
    recent = ledger_entries[-3:]
    repeated_decisions = len(recent) >= 2 and len({entry.get("decision") for entry in recent}) == 1
    no_progress = [
        entry
        for entry in recent
        if entry.get("status") in {"blocked", "capability_gap", "no_candidates"}
        or entry.get("meaningful_progress") is False
    ]
    return {
        "model": CEO_SELF_AUDIT_MODEL,
        "generated_at": utc_now_iso(),
        "latest_decision": action_result.get("decision"),
        "latest_action": action_result.get("action_taken"),
        "latest_status": action_result.get("status"),
        "recent_action_count": len(recent),
        "repeated_decision_detected": repeated_decisions,
        "recent_no_progress_count": len(no_progress),
        "intervention_required": repeated_decisions and len(no_progress) >= 2,
        "intervention": (
            "build_missing_capability_or_change_strategy_before_more_lab_blocks"
            if repeated_decisions and len(no_progress) >= 2
            else "continue_with_bound_action_dispatch"
        ),
        "production_effect": "none",
    }


def build_research_infra_delta(company_status: dict[str, Any], governance: dict[str, Any]) -> dict[str, Any]:
    lab_status = company_status.get("lab_status", {})
    artifacts_present = {
        "blocker_audit": bool(governance.get("blocker_audit")),
        "lane_assignment": bool(governance.get("lane_assignment")),
        "validation_governance": bool(governance.get("validation_governance")),
        "research_map": bool(governance.get("research_map")),
    }
    repeated_gap = lab_status.get("stop_reason") in {"no_runnable_and_no_valid_director_plan", "governed_recovery_no_supported_specs"}
    return {
        "model": CEO_INFRA_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "block_completed": bool(lab_status.get("completed_epochs", 0)),
        "governance_artifacts_present": artifacts_present,
        "process_score": lab_status.get("latest_process_score"),
        "latest_intervention": lab_status.get("latest_intervention"),
        "infra_delta_status": "needs_recovery_expansion" if repeated_gap else "observed",
        "recommended_infra_action": "expand_recursive_lane_recovery" if repeated_gap else "continue_bounded_ceo_blocks",
        "production_effect": "none",
    }


def build_understanding_delta(governance: dict[str, Any]) -> dict[str, Any]:
    research_map = governance.get("research_map", {})
    views = research_map.get("views", {}) or {}
    lane_assignment = governance.get("lane_assignment", {})
    validation = governance.get("validation_governance", {})
    return {
        "model": CEO_UNDERSTANDING_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "lane_counts": lane_assignment.get("lane_counts", {}),
        "open_lanes": lane_assignment.get("open_lanes", []),
        "validation_debt": views.get("validation_debt", []),
        "saturated_families": views.get("saturated_families", []),
        "top_open_questions": views.get("top_open_questions", []),
        "validation_decision_counts": validation.get("decision_counts", {}),
        "understanding_delta_status": "mapped" if research_map else "needs_research_map",
        "production_effect": "none",
    }


def build_risk_register(company_status: dict[str, Any], product_delta: dict[str, Any]) -> dict[str, Any]:
    lab_status = company_status.get("lab_status", {})
    risks: list[dict[str, Any]] = []
    if lab_status.get("completed_epochs", 0) and not product_delta.get("candidate_count"):
        risks.append(
            {
                "risk": "fake_progress",
                "severity": "high",
                "evidence": "research block completed without chart-facing candidate pipeline",
                "mitigation": "force champion/challenger or broaden product-role hypotheses",
            }
        )
    if lab_status.get("latest_intervention") == "request_fresh_data":
        risks.append(
            {
                "risk": "stale_or_insufficient_data",
                "severity": "medium",
                "evidence": "lab-meta requested fresh data",
                "mitigation": "import fresh TradingView data before promotion claims",
            }
        )
    if company_status.get("governance", {}).get("product_change_allowed"):
        risks.append(
            {
                "risk": "unexpected_product_change_permission",
                "severity": "critical",
                "evidence": "validation governance should not allow automatic product changes",
                "mitigation": "block production mutation and require user-approved promotion note",
            }
        )
    risks.append(
        {
            "risk": "production_mutation",
            "severity": "controlled",
            "evidence": "CEO mode keeps production_effect none",
            "mitigation": "promotion proposals only",
        }
    )
    return {
        "model": CEO_RISK_REGISTER_MODEL,
        "generated_at": utc_now_iso(),
        "risk_count": len(risks),
        "risks": risks,
        "production_effect": "none",
    }


def build_knowledge_graph_delta(governance: dict[str, Any]) -> dict[str, Any]:
    research_map = governance.get("research_map", {})
    views = research_map.get("views", {}) or {}
    candidates = list(views.get("product_ready_candidates", []) or [])
    validation_debt = list(views.get("validation_debt", []) or [])
    saturated = list(views.get("saturated_families", []) or [])
    return {
        "model": CEO_KNOWLEDGE_GRAPH_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "recommended_obsidian_summaries": [
            {"type": "product_candidate", "id": item, "reason": "candidate needs curated executive memory"}
            for item in candidates[:10]
        ]
        + [
            {"type": "validation_debt", "id": item, "reason": "open validation debt should be remembered"}
            for item in validation_debt[:10]
        ]
        + [
            {"type": "dead_branch", "id": item, "reason": "saturated family should not be blindly repeated"}
            for item in saturated[:10]
        ],
        "evidence_contract": [
            "run_id",
            "hypothesis_id",
            "variant_id",
            "source_csv_or_yaml",
            "evidence_level",
            "promotion_level",
            "product_role",
            "next_required_test",
        ],
        "production_effect": "none",
    }


def choose_executive_decision(
    company_status: dict[str, Any],
    product_delta: dict[str, Any],
    infra_delta: dict[str, Any],
) -> dict[str, Any]:
    lab_status = company_status.get("lab_status", {})
    open_lanes = company_status.get("governance", {}).get("open_lanes", [])
    stop_reason = str(lab_status.get("stop_reason", ""))
    if company_status.get("true_blocker"):
        decision = "stop_true_blocker"
        rationale = f"Lab stopped on true blocker: {stop_reason}"
    elif product_delta.get("candidate_count"):
        decision = "run_champion_challenger"
        rationale = "There are chart-facing candidates, but they need base-vs-challenger product-delta evidence."
    elif infra_delta.get("infra_delta_status") == "needs_recovery_expansion":
        decision = "patch_research_infra"
        rationale = "Open lanes remain, but recovery could not generate supported follow-ups."
    elif open_lanes:
        decision = "continue_governed_research"
        rationale = "Open governed lanes remain available for bounded CEO supervision."
    elif stop_reason == "request_fresh_data":
        decision = "request_fresh_data"
        rationale = "Evidence cannot advance without a fresher or broader data snapshot."
    else:
        decision = "broaden_hypothesis_source"
        rationale = "No chart-facing candidate or open lane was found; broaden sources before more brute force."
    return {
        "decision": decision,
        "rationale": rationale,
        "production_effect": "none",
    }


def _write_manifest(options: CeoOpsOptions, ceo_run_id: str, lab_run_id: str) -> Path:
    path = ceo_dir(options, ceo_run_id) / "ceo_manifest.yaml"
    atomic_write_yaml(path, build_ceo_manifest(options, ceo_run_id, lab_run_id))
    return path


def _write_artifact_set(
    options: CeoOpsOptions,
    ceo_run_id: str,
    lab_run_id: str,
    *,
    block_number: int,
    company_status: dict[str, Any],
    product_delta: dict[str, Any],
    infra_delta: dict[str, Any],
    understanding_delta: dict[str, Any],
    risk_register: dict[str, Any],
    knowledge_graph_delta: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Path]:
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "company_status": root / "company_status.yaml",
        "product_delta": root / "product_delta_scoreboard.yaml",
        "champion_challenger_action_plan": root / "champion_challenger_action_plan.yaml",
        "infra_delta": root / "research_infra_delta.yaml",
        "understanding_delta": root / "understanding_delta.yaml",
        "risk_register": root / "risk_register.yaml",
        "knowledge_graph_delta": root / "knowledge_graph_delta.yaml",
        "decision_packet": root / f"executive_decision_packet_{block_number:04d}.md",
        "latest_decision_packet": root / "executive_decision_packet.md",
        "promotion_candidates": root / "promotion_candidates.md",
        "heartbeat_status": root / "heartbeat_status.yaml",
    }
    atomic_write_yaml(paths["company_status"], company_status)
    atomic_write_yaml(paths["product_delta"], product_delta)
    atomic_write_yaml(paths["champion_challenger_action_plan"], build_champion_challenger_action_plan(product_delta))
    atomic_write_yaml(paths["infra_delta"], infra_delta)
    atomic_write_yaml(paths["understanding_delta"], understanding_delta)
    atomic_write_yaml(paths["risk_register"], risk_register)
    atomic_write_yaml(paths["knowledge_graph_delta"], knowledge_graph_delta)
    packet = render_executive_decision_packet(
        ceo_run_id=ceo_run_id,
        block_number=block_number,
        company_status=company_status,
        product_delta=product_delta,
        infra_delta=infra_delta,
        understanding_delta=understanding_delta,
        risk_register=risk_register,
        decision=decision,
    )
    atomic_write_text(paths["decision_packet"], packet)
    atomic_write_text(paths["latest_decision_packet"], packet)
    atomic_write_text(paths["promotion_candidates"], render_promotion_candidates(product_delta))
    atomic_write_yaml(
        paths["heartbeat_status"],
        build_heartbeat_status(
            options,
            ceo_run_id,
            lab_run_id,
            block_number=block_number,
            company_status=company_status,
            decision=decision,
        ),
    )
    return paths


def render_promotion_candidates(product_delta: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Promotion Candidates",
        "",
        "Production changes are not allowed automatically. Items here are shadow candidates only.",
        "",
    ]
    candidates = product_delta.get("candidates", []) or []
    if not candidates:
        lines.append("- No chart-facing candidates identified yet.")
    for candidate in candidates:
        lines.append(
            "- "
            f"{candidate.get('belief_id')} "
            f"role={candidate.get('product_role')} "
            f"gate={candidate.get('current_gate')} "
            f"status={candidate.get('comparison_status')}"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_executive_decision_packet(
    *,
    ceo_run_id: str,
    block_number: int,
    company_status: dict[str, Any],
    product_delta: dict[str, Any],
    infra_delta: dict[str, Any],
    understanding_delta: dict[str, Any],
    risk_register: dict[str, Any],
    decision: dict[str, Any],
) -> str:
    lab_status = company_status.get("lab_status", {})
    governance = company_status.get("governance", {})
    lines = [
        "# Riskflow CEO Decision Packet",
        "",
        f"Run: {ceo_run_id}",
        f"Block: {block_number}",
        f"Generated: {utc_now_iso()}",
        "",
        "## Block Summary",
        "",
        f"- Objective: {company_status.get('objective')}",
        f"- Lab run: {company_status.get('lab_run_id')}",
        f"- Lab status: {lab_status.get('status')}",
        f"- Stop reason: {lab_status.get('stop_reason') or 'none'}",
        f"- Completed epochs: {lab_status.get('completed_epochs', 0)}",
        f"- Last completed loop: {lab_status.get('last_completed_loop')}",
        "",
        "## CEO Diagnosis",
        "",
        f"- Research infra: {infra_delta.get('infra_delta_status')}",
        f"- Understanding: {understanding_delta.get('understanding_delta_status')}",
        f"- Chart-facing value: {product_delta.get('chart_facing_value_status')}",
        f"- True blocker: {company_status.get('true_blocker')}",
        "",
        "## Evidence Review",
        "",
        f"- Open lanes: {', '.join(governance.get('open_lanes', []) or []) or 'none'}",
        f"- Lane counts: {governance.get('lane_counts', {})}",
        f"- Validation decisions: {governance.get('validation_decision_counts', {})}",
        f"- Validation debt: {understanding_delta.get('validation_debt', [])[:10]}",
        f"- Saturated families: {understanding_delta.get('saturated_families', [])[:10]}",
        "",
        "## Product Translation",
        "",
        f"- Champion: {product_delta.get('champion')}",
        f"- Candidate count: {product_delta.get('candidate_count')}",
        f"- Product-delta status: {product_delta.get('chart_facing_value_status')}",
        "- Production effect: none",
        "",
        "## Risk Register",
        "",
    ]
    for risk in risk_register.get("risks", []) or []:
        lines.append(f"- {risk.get('risk')}: {risk.get('severity')} - {risk.get('mitigation')}")
    lines.extend(
        [
            "",
            "## Executive Decision",
            "",
            f"- Decision: {decision.get('decision')}",
            f"- Rationale: {decision.get('rationale')}",
            "",
            "## Next Block Plan",
            "",
            _next_block_plan(decision),
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _next_block_plan(decision: dict[str, Any]) -> str:
    kind = decision.get("decision")
    if kind == "run_champion_challenger":
        return "Run product-delta champion/challenger tests for the listed shadow candidates before adding more infrastructure."
    if kind == "patch_research_infra":
        return "Patch recursive lane recovery or broaden recovery specs, run tests, then rerun one CEO block."
    if kind == "continue_governed_research":
        return "Run one more bounded governed CEO block and inspect the next decision packet."
    if kind == "request_fresh_data":
        return "Import or curate fresh OHLCV data before treating same-sample evidence as validation."
    if kind == "stop_true_blocker":
        return "Stop autonomous work and resolve the true blocker before continuing."
    if kind == "stop_requested":
        return "Stop autonomous work until the CEO and lab stop requests are intentionally cleared."
    return "Broaden the hypothesis source through Obsidian, visual review, web research, or agent critique."


def _lab_ops_options(options: CeoOpsOptions, lab_run_id: str) -> LabOpsOptions:
    return LabOpsOptions(
        objective=options.objective,
        run_id=lab_run_id,
        queue_path=options.queue_path,
        config_path=options.config_path,
        data_dir=options.data_dir,
        timeframes=options.timeframes,
        max_epochs=options.block_epochs,
        epoch_size=options.epoch_size,
        director_checkpoint_epochs=options.block_epochs,
        max_hours=options.max_hours,
        min_sample_size=options.min_sample_size,
        entry_lag_bars=options.entry_lag_bars,
        cooldown_bars=options.cooldown_bars,
        strict_referee=options.strict_referee,
        strict_null_iterations=options.strict_null_iterations,
        strict_random_seed=options.strict_random_seed,
        checkpoint_interval=options.checkpoint_interval,
        apply=options.apply,
        resume=options.resume,
        dry_run=options.dry_run,
        governed=True,
        source_root=options.source_root,
        report_root=options.lab_ops_report_root,
        runtime_root=options.lab_ops_runtime_root,
        max_new_hypotheses=options.max_new_hypotheses,
    )


def _write_binding_action_result(
    options: CeoOpsOptions,
    ceo_run_id: str,
    lab_run_id: str,
    action_result: dict[str, Any],
) -> dict[str, Path]:
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    action_result_path = root / "binding_action_result.yaml"
    ledger_path = _append_action_ledger(options, ceo_run_id, action_result)
    ledger_entries = _read_action_ledger(options, ceo_run_id)
    self_audit = build_ceo_self_audit(action_result, ledger_entries)
    self_audit_path = root / "ceo_self_audit.yaml"
    atomic_write_yaml(action_result_path, _json_safe(action_result))
    atomic_write_yaml(self_audit_path, self_audit)
    return {
        "binding_action_result": action_result_path,
        "action_ledger": ledger_path,
        "self_audit": self_audit_path,
    }


def render_champion_challenger_report(results: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Champion/Challenger Results",
        "",
        f"Generated: {results.get('generated_at')}",
        f"Status: {results.get('status')}",
        f"Candidate count: {results.get('candidate_count')}",
        f"Missing metric sources: {results.get('missing_metric_source_count')}",
        "",
        "## Results",
        "",
    ]
    for item in results.get("results", []) or []:
        lines.append(
            "- "
            f"{item.get('belief_id')} "
            f"role={item.get('product_role')} "
            f"champion={item.get('champion')} "
            f"challenger={item.get('challenger')} "
            f"status={item.get('comparison_status')} "
            f"decision={item.get('decision')}"
        )
    if not results.get("results"):
        lines.append("- No candidates were available for comparison.")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This artifact does not promote or alter production Riskflow behavior.",
            "If metric sources are missing, CEO mode must build the missing research-infra command before claiming product evidence.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_champion_challenger(options: CeoOpsOptions, *, top_n: int | None = None) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo champion-challenger requires --apply")
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    action_plan_path = root / "champion_challenger_action_plan.yaml"
    action_plan = _load_yaml_if_exists(action_plan_path)
    if not action_plan:
        governance = _load_latest_governance(options, lab_run_id)
        product_delta = build_product_delta_scoreboard(governance)
        action_plan = build_champion_challenger_action_plan(product_delta)
        atomic_write_yaml(action_plan_path, action_plan)
    results = build_champion_challenger_results(action_plan, top_n=top_n)
    results_path = root / "champion_challenger_results.yaml"
    report_path = root / "champion_challenger_results.md"
    atomic_write_yaml(results_path, results)
    atomic_write_text(report_path, render_champion_challenger_report(results))
    capability_gap_path: Path | None = None
    if results.get("status") == "blocked_missing_metric_sources":
        gap = build_capability_gap(
            ceo_run_id=ceo_run_id,
            lab_run_id=lab_run_id,
            decision="run_champion_challenger",
            missing_capability="product_delta_metric_source_extractor",
            reason="Shadow candidates exist, but their action-plan work items do not carry source rows for metric comparison.",
            required_command="PYTHONPATH=src python3 -m riskflow ceo champion-challenger --run-id <run_id> --apply",
            acceptance_criteria=[
                "attach exact evidence CSV/YAML source paths to each work item",
                "compute role-specific champion/challenger deltas without changing production formulas",
                "write candidate-level missing-upside and avoided-downside metrics",
                "run tests that prove execute-next does not fall back to generic lab blocks for this decision",
            ],
        )
        capability_gap_path = root / "capability_gap.yaml"
        atomic_write_yaml(capability_gap_path, gap)
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_champion_challenger",
        "action_taken": "champion_challenger",
        "command_executed": "riskflow ceo champion-challenger",
        "status": "capability_gap" if capability_gap_path else results.get("status"),
        "meaningful_progress": bool(results.get("candidate_count")),
        "inputs": {"action_plan": action_plan_path},
        "outputs": {
            "results": results_path,
            "report": report_path,
            "capability_gap": capability_gap_path,
        },
        "next_allowed_actions": [results.get("next_action", "broaden_product_candidate_source")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"action_plan": action_plan_path, "results": results_path, "report": report_path})
    if capability_gap_path:
        paths["capability_gap"] = capability_gap_path
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "action_result": action_result,
        "results": results,
        "paths": paths,
    }


def run_ceo_status(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    status = build_company_status(options, ceo_run_id, lab_run_id)
    if root.exists():
        atomic_write_yaml(root / "company_status.yaml", status)
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "company_status": status}


def run_ceo_plan(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = _write_manifest(options, ceo_run_id, lab_run_id)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    plan = {
        "model": "riskflow_ceo_plan_v0",
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "objective": options.objective,
        "recommended_decision": decision,
        "next_command": (
            "PYTHONPATH=src python3 -m riskflow ceo execute-next "
            f"--run-id {ceo_run_id} --objective {options.objective} --apply"
        ),
        "production_effect": "none",
    }
    plan_path = root / "ceo_plan.yaml"
    atomic_write_yaml(plan_path, plan)
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "plan": plan, "paths": {"manifest": manifest_path, "plan": plan_path}}


def run_ceo_run_block(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo run-block requires --apply")
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    if is_stop_requested(options, ceo_run_id, lab_run_id):
        raise RuntimeError("ceo stop requested; remove stop.request files before running another block")
    block_options = replace(options, resume=True) if _lab_state_exists(options, lab_run_id) and not options.resume else options
    _write_manifest(block_options, ceo_run_id, lab_run_id)
    lab_result = run_lab_ops_run(_lab_ops_options(block_options, lab_run_id))
    review = run_ceo_review(block_options, ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "lab_result": lab_result, "review": review}


def run_ceo_execute_next(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo execute-next requires --apply")
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "executive_decision_packet.md").exists():
        run_ceo_review(options, ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    decision_kind = str(decision.get("decision", "unknown"))

    if is_stop_requested(options, ceo_run_id, lab_run_id):
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_stop_requested",
            "command_executed": None,
            "status": "blocked",
            "meaningful_progress": False,
            "reason": "stop.request exists",
            "next_allowed_actions": ["clear_stop_request_after_user_approval"],
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    if company_status.get("true_blocker"):
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_true_blocker",
            "command_executed": None,
            "status": "blocked",
            "meaningful_progress": False,
            "reason": decision.get("rationale", "true blocker"),
            "next_allowed_actions": ["resolve_true_blocker"],
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    if company_status.get("governance", {}).get("product_change_allowed"):
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_production_promotion_gate",
            "command_executed": None,
            "status": "blocked",
            "meaningful_progress": False,
            "reason": "validation governance indicates product_change_allowed",
            "next_allowed_actions": ["write_promotion_proposal_and_wait_for_user_approval"],
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    if decision_kind == "run_champion_challenger":
        return run_ceo_champion_challenger(options)

    if decision_kind == "continue_governed_research":
        block = run_ceo_run_block(options)
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "run_block",
            "command_executed": "riskflow ceo run-block",
            "status": block["lab_result"].get("status"),
            "meaningful_progress": True,
            "outputs": {"decision_packet": block["review"]["paths"].get("latest_decision_packet")},
            "next_allowed_actions": [block["review"]["decision"].get("decision")],
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        return {
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "action_result": action_result,
            "block": block,
            "paths": paths,
        }

    if decision_kind == "request_fresh_data":
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_fresh_data_required",
            "command_executed": None,
            "status": "blocked",
            "meaningful_progress": False,
            "reason": decision.get("rationale", "fresh data required"),
            "next_allowed_actions": ["import_or_curate_fresh_ohlcv_data"],
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    gap = build_capability_gap(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        decision=decision_kind,
        missing_capability=f"{decision_kind}_executor",
        reason=f"CEO decision {decision_kind} has no binding executor yet.",
        required_command=f"PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id {ceo_run_id} --apply",
        acceptance_criteria=[
            f"execute {decision_kind} without falling back to a generic lab block",
            "write binding_action_result.yaml and ceo_action_ledger.jsonl",
            "prove production_effect remains none",
            "add tests covering the new executor branch",
        ],
    )
    capability_gap_path = root / "capability_gap.yaml"
    atomic_write_yaml(capability_gap_path, gap)
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": decision_kind,
        "action_taken": "capability_gap_recorded",
        "command_executed": None,
        "status": "capability_gap",
        "meaningful_progress": True,
        "outputs": {"capability_gap": capability_gap_path},
        "next_allowed_actions": [f"build_{decision_kind}_executor"],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths["capability_gap"] = capability_gap_path
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}


def run_ceo_review(
    options: CeoOpsOptions,
    *,
    ceo_run_id: str | None = None,
    lab_run_id: str | None = None,
) -> dict[str, Any]:
    ceo_run_id = ceo_run_id or resolve_ceo_run_id(options)
    lab_run_id = lab_run_id or resolve_lab_run_id(options, ceo_run_id)
    _write_manifest(options, ceo_run_id, lab_run_id)
    block_number = _next_block_number(options, ceo_run_id)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    understanding_delta = build_understanding_delta(governance)
    risk_register = build_risk_register(company_status, product_delta)
    knowledge_graph_delta = build_knowledge_graph_delta(governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    paths = _write_artifact_set(
        options,
        ceo_run_id,
        lab_run_id,
        block_number=block_number,
        company_status=company_status,
        product_delta=product_delta,
        infra_delta=infra_delta,
        understanding_delta=understanding_delta,
        risk_register=risk_register,
        knowledge_graph_delta=knowledge_graph_delta,
        decision=decision,
    )
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "block_number": block_number,
        "decision": decision,
        "paths": paths,
        "company_status": company_status,
        "product_delta": product_delta,
    }


def run_ceo_report(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    latest_packet = root / "executive_decision_packet.md"
    if not latest_packet.exists():
        review = run_ceo_review(options, ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
        latest_packet = review["paths"]["latest_decision_packet"]
    else:
        review = {
            "decision": {"decision": "see_latest_decision_packet", "rationale": "Report used existing CEO decision packet."},
            "paths": {"latest_decision_packet": latest_packet},
        }
    try:
        lab_report = run_lab_ops_report(_lab_ops_options(options, lab_run_id), run_id=lab_run_id)["paths"]["report"]
    except Exception:
        lab_report = None
    packet_path = latest_packet
    lines = [
        "# Riskflow CEO Final Report",
        "",
        f"Run: {ceo_run_id}",
        f"Lab run: {lab_run_id}",
        f"Generated: {utc_now_iso()}",
        "",
        "## Executive Decision",
        "",
        f"- Decision: {review['decision'].get('decision')}",
        f"- Rationale: {review['decision'].get('rationale')}",
        "",
        "## Reports",
        "",
        f"- CEO packet: {packet_path}",
    ]
    if lab_report:
        lines.append(f"- Lab report: {lab_report}")
    lines.extend(["", packet_path.read_text(encoding="utf-8") if packet_path.exists() else ""])
    report_path = root / "final_ceo_report.md"
    atomic_write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "paths": {"report": report_path, **review["paths"]}}


def run_ceo_heartbeat_status(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    path = ceo_heartbeat_status_path(options, ceo_run_id)
    if path.exists():
        payload = _load_yaml_if_exists(path)
        return {
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "status": payload,
            "paths": {"heartbeat_status": path},
            "from_file": True,
        }
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    block_number = max(0, _next_block_number(options, ceo_run_id) - 1)
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": build_heartbeat_status(
            options,
            ceo_run_id,
            lab_run_id,
            block_number=block_number,
            company_status=company_status,
            decision=decision,
        ),
        "paths": {"heartbeat_status": path},
        "from_file": False,
    }


def run_ceo_stop(options: CeoOpsOptions, *, reason: str) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    cleaned_reason = reason.strip() or "user_requested"
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    lab_root = _lab_runtime_root(options, lab_run_id)
    lab_root.mkdir(parents=True, exist_ok=True)
    ceo_stop = ceo_stop_path(options, ceo_run_id)
    lab_stop = lab_stop_path(options, lab_run_id)
    atomic_write_text(ceo_stop, cleaned_reason + "\n")
    atomic_write_text(lab_stop, cleaned_reason + "\n")
    stop_payload = {
        "model": CEO_STOP_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "reason": cleaned_reason,
        "stop_request_paths": {"ceo": str(ceo_stop), "lab": str(lab_stop)},
        "production_effect": "none",
    }
    stop_status = root / "stop_status.yaml"
    atomic_write_yaml(stop_status, stop_payload)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    heartbeat = build_heartbeat_status(
        options,
        ceo_run_id,
        lab_run_id,
        block_number=max(0, _next_block_number(options, ceo_run_id) - 1),
        company_status=company_status,
        decision={
            "decision": "stop_requested",
            "rationale": f"CEO stop requested: {cleaned_reason}",
            "production_effect": "none",
        },
    )
    heartbeat_path = ceo_heartbeat_status_path(options, ceo_run_id)
    atomic_write_yaml(heartbeat_path, heartbeat)
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "reason": cleaned_reason,
        "paths": {"ceo_stop": ceo_stop, "lab_stop": lab_stop, "stop_status": stop_status, "heartbeat_status": heartbeat_path},
        "heartbeat_status": heartbeat,
    }


def run_ceo_lab_status_text(options: CeoOpsOptions) -> str:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    try:
        return run_lab_ops_status(_lab_ops_options(options, lab_run_id), run_id=lab_run_id)["status_text"]
    except Exception:
        return "No lab-ops status found."
