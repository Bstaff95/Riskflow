from __future__ import annotations

import csv
import hashlib
import json
import shlex
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import load_universe_config
from .data_loader import find_symbol_csv, load_ohlcv_csv
from .grammar_search import GRAMMAR_SEARCH_MODEL, run_grammar_search, strict_baseline_referee
from .lab_director import append_queue_to_runtime, audit_director_plan, design_lane_recovery_experiments
from .lab_loop import atomic_write_text, atomic_write_yaml, load_analysis_frames_by_timeframe, load_yaml_file
from .lab_ops import (
    LAB_OPS_REPORT_ROOT,
    LAB_OPS_RUNTIME_ROOT,
    LabOpsOptions,
    run_lab_ops_report,
    run_lab_ops_run,
    run_lab_ops_status,
)
from .obsidian_kg import build_knowledge_graph, compile_setup_journey_queue, load_obsidian_notes


CEO_MANIFEST_MODEL = "riskflow_ceo_manifest_v0"
CEO_COMPANY_STATUS_MODEL = "riskflow_ceo_company_status_v0"
CEO_PRODUCT_DELTA_MODEL = "riskflow_ceo_product_delta_scoreboard_v0"
CEO_CHAMPION_CHALLENGER_ACTION_PLAN_MODEL = "riskflow_ceo_champion_challenger_action_plan_v0"
CEO_CHAMPION_CHALLENGER_RESULTS_MODEL = "riskflow_ceo_champion_challenger_results_v0"
CEO_VISUAL_REVIEW_QUEUE_MODEL = "riskflow_ceo_visual_review_queue_v0"
CEO_FRESH_CONTROL_VALIDATION_PLAN_MODEL = "riskflow_ceo_fresh_control_validation_plan_v0"
CEO_ACTION_CONTRACT_MODEL = "riskflow_ceo_action_contract_v0"
CEO_DISPATCH_RECEIPT_MODEL = "riskflow_ceo_dispatch_receipt_v0"
CEO_ACTION_RESULT_MODEL = "riskflow_ceo_binding_action_result_v0"
CEO_ACTION_OUTCOME_CARD_MODEL = "riskflow_ceo_action_outcome_card_v0"
CEO_CAPABILITY_GAP_MODEL = "riskflow_ceo_capability_gap_v0"
CEO_CAPABILITY_BACKLOG_MODEL = "riskflow_ceo_capability_backlog_v0"
CEO_SELF_AUDIT_MODEL = "riskflow_ceo_self_audit_v0"
CEO_TRACE_GRADE_MODEL = "riskflow_ceo_trace_grade_v0"
CEO_FLIGHT_DASHBOARD_MODEL = "riskflow_ceo_flight_dashboard_v0"
CEO_OPERATING_DASHBOARD_MODEL = "riskflow_ceo_operating_dashboard_v0"
CEO_PROMOTION_PROPOSAL_MODEL = "riskflow_ceo_promotion_proposal_v0"
CEO_EVIDENCE_DEBT_REGISTER_MODEL = "riskflow_ceo_evidence_debt_register_v0"
CEO_APPROVAL_QUEUE_MODEL = "riskflow_ceo_approval_queue_v0"
CEO_APPROVAL_STATUS_MODEL = "riskflow_ceo_approval_status_v0"
CEO_APPROVAL_DECISION_MODEL = "riskflow_ceo_approval_decision_v0"
CEO_APPROVAL_APPLY_MODEL = "riskflow_ceo_approval_apply_v0"
CEO_EXECUTIVE_KPIS_MODEL = "riskflow_ceo_executive_kpis_v0"
CEO_HEARTBEAT_PLAN_MODEL = "riskflow_ceo_heartbeat_plan_v0"
CEO_HEARTBEAT_TICK_MODEL = "riskflow_ceo_heartbeat_tick_v0"
CEO_ROLE_REGISTRY_MODEL = "riskflow_ceo_role_registry_v0"
CEO_ROLE_TASK_QUEUE_MODEL = "riskflow_ceo_role_task_queue_v0"
CEO_ROLE_DISPATCH_MODEL = "riskflow_ceo_role_dispatch_v0"
CEO_ROLE_RESULT_MODEL = "riskflow_ceo_role_result_v0"
CEO_FRESH_DATA_PREFLIGHT_MODEL = "riskflow_ceo_fresh_data_preflight_v0"
CEO_FROZEN_CANDIDATE_VALIDATION_MODEL = "riskflow_ceo_frozen_candidate_validation_v0"
CEO_FROZEN_VALIDATION_EXECUTION_MODEL = "riskflow_ceo_frozen_validation_execution_v0"
CEO_FROZEN_VALIDATION_RERUN_MODEL = "riskflow_ceo_frozen_validation_rerun_v0"
CEO_FRESH_WITHHELD_VALIDATION_CONTRACT_MODEL = "riskflow_ceo_fresh_withheld_validation_contract_v0"
CEO_FRESH_WITHHELD_SNAPSHOT_MANIFEST_MODEL = "riskflow_ceo_fresh_withheld_snapshot_manifest_v0"
CEO_WITHHELD_SPLIT_MANIFEST_MODEL = "riskflow_ceo_withheld_split_manifest_v0"
CEO_FRESH_WITHHELD_VALIDATION_EXECUTION_MODEL = "riskflow_ceo_fresh_withheld_validation_execution_v0"
CEO_RESEARCH_INFRA_PATCH_PLAN_MODEL = "riskflow_ceo_research_infra_patch_plan_v0"
CEO_HYPOTHESIS_SOURCE_BROADENING_PLAN_MODEL = "riskflow_ceo_hypothesis_source_broadening_plan_v0"
CEO_INFRA_DELTA_MODEL = "riskflow_ceo_research_infra_delta_v0"
CEO_UNDERSTANDING_DELTA_MODEL = "riskflow_ceo_understanding_delta_v0"
CEO_RISK_REGISTER_MODEL = "riskflow_ceo_risk_register_v0"
CEO_KNOWLEDGE_GRAPH_DELTA_MODEL = "riskflow_ceo_knowledge_graph_delta_v0"
CEO_HEARTBEAT_STATUS_MODEL = "riskflow_ceo_heartbeat_status_v0"
CEO_STOP_MODEL = "riskflow_ceo_stop_request_v0"
CEO_EVAL_SUITE_MODEL = "riskflow_ceo_eval_suite_v0"
CEO_REPLAY_MODEL = "riskflow_ceo_replay_v0"
CEO_PORTFOLIO_ALLOCATOR_MODEL = "riskflow_ceo_portfolio_allocator_v0"
CEO_MISSION_SCORE_MODEL = "riskflow_ceo_mission_score_v0"
CEO_STRATEGY_CAPITAL_DASHBOARD_MODEL = "riskflow_ceo_strategy_capital_dashboard_v0"
CEO_RESUMPTION_BRIEF_MODEL = "riskflow_ceo_resumption_brief_v0"
CEO_ARTIFACT_COHERENCE_MODEL = "riskflow_ceo_artifact_coherence_v0"
CEO_RUN_INDEX_MODEL = "riskflow_ceo_run_index_v0"
CEO_BLOCKER_STACK_MODEL = "riskflow_ceo_blocker_stack_v0"
CEO_OPERATING_INCIDENT_REGISTER_MODEL = "riskflow_ceo_operating_incident_register_v0"
CEO_REPAIR_PLAN_MODEL = "riskflow_ceo_repair_plan_v0"
CEO_REPAIR_APPLY_MODEL = "riskflow_ceo_repair_apply_v0"
CEO_ACTION_BOARD_MODEL = "riskflow_ceo_action_board_v0"
CEO_OPERATOR_STEP_MODEL = "riskflow_ceo_operator_step_v0"
CEO_OPERATOR_BRIEF_MODEL = "riskflow_ceo_operator_brief_v0"
CEO_DECISION_QUALITY_MODEL = "riskflow_ceo_decision_quality_v0"
CEO_ORG_PROGRESS_SCORE_MODEL = "riskflow_ceo_org_progress_score_v0"
CEO_EVAL_FIXTURES_MODEL = "riskflow_ceo_eval_fixtures_v0"
CEO_MEMORY_DELTA_MODEL = "riskflow_ceo_memory_delta_v0"
CEO_GUARDRAIL_AUDIT_MODEL = "riskflow_ceo_guardrail_audit_v0"
CEO_PREFLIGHT_GATE_MODEL = "riskflow_ceo_preflight_gate_v0"
CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION = "defer_to_runtime_authority_surface"
CEO_FLIGHT_SAFETY_SCOPE = "flight_dashboard_only_not_dispatch_authority"
CEO_STRATEGY_SAFETY_SCOPE = "strategy_attention_only_not_dispatch_authority"
CEO_RUNTIME_AUTHORITY_NOTE = (
    "Dispatch authority is decided by ceo status, approval queue, action board, "
    "resumption brief, preflight gate, and dispatch receipt."
)
CEO_HARD_HANDOFF_SEMANTIC_ISSUES = {
    "live_stop_runtime_authority_mismatch",
    "manual_gate_has_runnable_actions",
    "manual_gate_primary_marked_executable",
    "manual_gate_decision_quality_selected_action_executable",
    "manual_gate_decision_quality_effective_action_executable",
}

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

MISSION_DIMENSIONS = (
    "bullish_permission",
    "warning_blocker",
    "invalidation",
    "reset_quality",
    "gradient_interpretation",
    "path_management",
    "cross_asset_regime",
    "archive_do_not_repeat",
)

MISSION_DIMENSION_LABELS = {
    "bullish_permission": "permission candidates that help say risk-on enough to care",
    "warning_blocker": "avoid/wait logic, missed-upside cost, and avoided-downside benefit",
    "invalidation": "conditions that prove the read failed or needs reset",
    "reset_quality": "hot-leader cooldown, constructive rebasing, and reclaim quality",
    "gradient_interpretation": "color/gradient changes, fading/reheating, and divergence quality",
    "path_management": "lag, cooldown, MFE/MAE, drawdown path, and staged journey quality",
    "cross_asset_regime": "symbol diversity, timeframe coverage, sector/basket/regime usefulness",
    "archive_do_not_repeat": "archived branches, repeated no-progress fingerprints, and stale loops",
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
    "run_fresh_or_control_validation_for_promising_shadow_challengers",
    "patch_research_infra",
    "continue_governed_research",
    "broaden_hypothesis_source",
}

CEO_NO_PROGRESS_STATUSES = {
    "blocked",
    "capability_gap",
    "no_candidates",
    "blocked_missing_metric_sources",
    "blocked_missing_champion_challenger_results",
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
    ceo_context: str = "external"
    ceo_authorized_action: str | None = None
    skip_eval_fixtures: bool = False


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


CEO_DIAGNOSTIC_CONTEXTS = {"diagnostic_refresh", "preflight_refresh"}
CEO_DIAGNOSTIC_ALLOWED_ACTIONS = {
    "run_fresh_withheld_validation_contract",
    "run_promotion_proposal",
    "run_evidence_debt_register",
}


def _with_ceo_context(
    options: CeoOpsOptions,
    *,
    context: str,
    action: str | None = None,
) -> CeoOpsOptions:
    return replace(options, ceo_context=context, ceo_authorized_action=action)


def _require_ceo_action_context(options: CeoOpsOptions, *, action: str, aliases: set[str] | None = None) -> None:
    allowed = {action, *(aliases or set())}
    if options.ceo_context in CEO_DIAGNOSTIC_CONTEXTS and action in CEO_DIAGNOSTIC_ALLOWED_ACTIONS:
        return
    if options.ceo_context in {"bound_dispatch", "guarded_direct"} and str(options.ceo_authorized_action) in allowed:
        return
    raise ValueError(f"ceo {action} requires bound dispatch, guarded direct preflight, or diagnostic context")


def _should_write_binding_action_result(options: CeoOpsOptions) -> bool:
    return options.ceo_context not in CEO_DIAGNOSTIC_CONTEXTS


def _ceo_approval_record_command(*, ceo_run_id: str, approval_id: str) -> str:
    return (
        "PYTHONPATH=src python3 -m riskflow ceo approval-record "
        f"--run-id {ceo_run_id} --approval-id {approval_id} "
        "--decision <approved|rejected> --user-confirmed"
    )


def _ceo_approval_apply_command(*, ceo_run_id: str, approval_id: str) -> str:
    return (
        "PYTHONPATH=src python3 -m riskflow ceo approval-apply "
        f"--run-id {ceo_run_id} --approval-id {approval_id} "
        "--user-confirmed --apply"
    )


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
    return _read_jsonl_entries(path)


def _read_jsonl_entries(path: Path) -> list[dict[str, Any]]:
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


def _latest_director_dir(options: CeoOpsOptions, lab_run_id: str) -> Path | None:
    return _latest_child(_lab_root(options, lab_run_id) / "director", "*")


def _lab_runtime_queue_path(options: CeoOpsOptions, lab_run_id: str) -> Path:
    return options.lab_ops_runtime_root / lab_run_id / "runtime_queue.yaml"


def _lab_runtime_state_path(options: CeoOpsOptions, lab_run_id: str) -> Path:
    return options.lab_ops_runtime_root / lab_run_id / "lab_state.json"


def _existing_lab_hypothesis_ids(options: CeoOpsOptions, lab_run_id: str) -> set[str]:
    ids: set[str] = set()
    runtime_queue = _load_yaml_if_exists(_lab_runtime_queue_path(options, lab_run_id))
    ids.update(str(item.get("id", "")) for item in runtime_queue.get("queue", []) or [] if item.get("id"))
    state_path = _lab_runtime_state_path(options, lab_run_id)
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
        ids.update(str(item) for item in state.get("completed_hypothesis_ids", []) or [])
    return ids


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
                "promotion_ceiling": "shadow_candidate",
                "fresh_or_frozen_validation_status": "not_run",
                "champion_metric_completeness": "not_evaluated",
                "product_language_allowed": False,
                "production_effect": "none",
            }
        )
    return {
        "model": CEO_PRODUCT_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "champion": "core_signal_v0",
        "candidate_count": len(candidates),
        "chart_facing_value_status": "shadow_product_candidate_pipeline" if candidates else "no_product_delta_yet",
        "promotion_ceiling": "shadow_candidate" if candidates else "none",
        "fresh_or_frozen_validation_status": "not_run",
        "champion_metric_completeness": "not_evaluated",
        "product_language_allowed": False,
        "product_evidence_status": "not_validated",
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
            else "broaden_hypothesis_source"
        ),
        "production_effect": "none",
    }


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _first_present(row: dict[str, Any], names: tuple[str, ...]) -> float | None:
    for name in names:
        value = _safe_float(row.get(name))
        if value is not None:
            return value
    return None


def _ranked_metric_summary(ranked_path: Path, *, product_role: str) -> dict[str, Any]:
    if not ranked_path.exists():
        return {}
    rows: list[dict[str, Any]] = []
    with ranked_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
    if not rows:
        return {}
    useful = [row for row in rows if str(row.get("classification", "")).lower() in {"useful", "watchlist"}]
    candidate_rows = useful or rows

    def avg(values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None

    medians = [
        value
        for row in candidate_rows
        if (value := _first_present(row, ("median_forward_relative_return_secondary", "median_forward_relative_return_30"))) is not None
    ]
    hit_rates = [
        value
        for row in candidate_rows
        if (value := _first_present(row, ("hit_rate_forward_relative_return_primary", "hit_rate_forward_relative_return_30"))) is not None
    ]
    drawdowns = [value for row in candidate_rows if (value := _safe_float(row.get("median_max_drawdown"))) is not None]
    mfes = [value for row in candidate_rows if (value := _safe_float(row.get("median_max_favorable_excursion"))) is not None]
    ratios = [value for row in candidate_rows if (value := _safe_float(row.get("median_mfe_mae_ratio"))) is not None]
    sample_sizes = [value for row in candidate_rows if (value := _safe_float(row.get("sample_size"))) is not None]
    unique_symbols = [value for row in candidate_rows if (value := _safe_float(row.get("unique_symbols"))) is not None]
    event_clusters = [value for row in candidate_rows if (value := _safe_float(row.get("unique_event_clusters"))) is not None]
    best_ranked = sorted(
        candidate_rows,
        key=lambda row: _safe_float(row.get("rank_score")) or 0.0,
        reverse=True,
    )[0]
    baseline_medians = [
        value
        for row in rows
        if (value := _first_present(row, ("median_forward_relative_return_secondary", "median_forward_relative_return_30"))) is not None
    ]
    baseline_hit_rates = [
        value
        for row in rows
        if (value := _first_present(row, ("hit_rate_forward_relative_return_primary", "hit_rate_forward_relative_return_30"))) is not None
    ]
    average_median = avg(medians)
    baseline_median = avg(baseline_medians)
    baseline_hit_rate = avg(baseline_hit_rates)
    best_median = max(medians) if medians else None
    worst_median = min(medians) if medians else None
    role = str(product_role)
    if role == "warning_blocker":
        challenger_for_delta = worst_median if worst_median is not None else average_median
        baseline_for_delta = baseline_median if baseline_median is not None else 0.0
        role_delta = (baseline_for_delta - challenger_for_delta) if challenger_for_delta is not None else None
        missed_upside_cost = max(0.0, best_median or 0.0)
        avoided_downside_benefit = max(0.0, role_delta or 0.0)
        role_decision = (
            "shadow_challenger_promising"
            if avoided_downside_benefit > 0 and missed_upside_cost <= avoided_downside_benefit
            else "needs_fresh_or_control_validation"
        )
    else:
        role_delta = (average_median - baseline_median) if average_median is not None and baseline_median is not None else None
        missed_upside_cost = None
        avoided_downside_benefit = None
        role_decision = (
            "shadow_challenger_promising"
            if role_delta is not None and role_delta > 0
            else "needs_fresh_or_control_validation"
        )
    return {
        "row_count": len(rows),
        "useful_or_watchlist_rows": len(useful),
        "best_variant_id": best_ranked.get("variant_id", ""),
        "best_family_id": best_ranked.get("family_id", ""),
        "timeframe": best_ranked.get("timeframe", ""),
        "classification": best_ranked.get("classification", ""),
        "rank_score": _safe_float(best_ranked.get("rank_score")),
        "median_forward_relative_return": average_median,
        "champion_baseline_median_forward_relative_return": baseline_median,
        "champion_baseline_hit_rate": baseline_hit_rate,
        "role_delta_vs_champion_baseline": role_delta,
        "best_median_forward_relative_return": best_median,
        "worst_median_forward_relative_return": worst_median,
        "hit_rate": avg(hit_rates),
        "median_max_drawdown": avg(drawdowns),
        "median_max_favorable_excursion": avg(mfes),
        "mfe_mae_ratio": avg(ratios),
        "sample_size": avg(sample_sizes),
        "unique_symbols": avg(unique_symbols),
        "event_diversity": avg(event_clusters),
        "missed_upside_cost": missed_upside_cost,
        "avoided_downside_benefit": avoided_downside_benefit,
        "role_decision": role_decision,
        "champion_baseline_method": "same_source_all_ranked_variants_proxy",
        "production_effect": "none",
    }


def _research_map_nodes_by_id(governance: dict[str, Any]) -> dict[str, dict[str, Any]]:
    research_map = governance.get("research_map", {}) or {}
    return {str(node.get("id", "")): node for node in research_map.get("nodes", []) or []}


def _loop_dirs_for_lab(options: CeoOpsOptions, lab_run_id: str) -> list[Path]:
    lab_loop_root = _lab_root(options, lab_run_id) / "lab_loop"
    if not lab_loop_root.exists():
        return []
    return sorted({path.parent for path in lab_loop_root.glob("**/bullish_evidence.yaml")})


def _loop_matches_roots(loop_dir: Path, root_ids: set[str], belief_id: str) -> bool:
    evidence = _load_yaml_if_exists(loop_dir / "bullish_evidence.yaml")
    hypothesis_id = str(evidence.get("hypothesis_id", ""))
    if hypothesis_id and hypothesis_id in root_ids:
        return True
    if hypothesis_id and belief_id and belief_id in hypothesis_id:
        return True
    hypothesis_path = loop_dir / "hypothesis.yaml"
    if not hypothesis_path.exists():
        return False
    text = hypothesis_path.read_text(encoding="utf-8")
    return any(root_id and root_id in text for root_id in root_ids)


def attach_metric_sources_to_action_plan(
    action_plan: dict[str, Any],
    governance: dict[str, Any],
    options: CeoOpsOptions,
    lab_run_id: str,
    *,
    max_sources_per_item: int = 5,
) -> dict[str, Any]:
    nodes_by_id = _research_map_nodes_by_id(governance)
    loop_dirs = _loop_dirs_for_lab(options, lab_run_id)
    enriched_items: list[dict[str, Any]] = []
    for item in action_plan.get("work_items", []) or []:
        belief_id = str(item.get("belief_id", ""))
        node = nodes_by_id.get(belief_id, {})
        root_ids = {str(root_id) for root_id in node.get("root_ids", []) or [] if root_id}
        matches = [loop_dir for loop_dir in loop_dirs if _loop_matches_roots(loop_dir, root_ids, belief_id)]
        sources: list[dict[str, Any]] = []
        for loop_dir in matches[:max_sources_per_item]:
            ranked_path = loop_dir / "grammar_search_ranked.csv"
            source = {
                "loop_dir": str(loop_dir),
                "hypothesis": str(loop_dir / "hypothesis.yaml"),
                "bullish_evidence": str(loop_dir / "bullish_evidence.yaml"),
                "ranked": str(ranked_path),
                "variant_records": str(loop_dir / "grammar_search_variant_records.csv"),
                "strict_referee": str(loop_dir / "strict_referee.csv"),
                "metric_summary": _ranked_metric_summary(ranked_path, product_role=str(item.get("product_role", ""))),
            }
            sources.append(source)
        enriched = dict(item)
        enriched["research_map_node"] = {
            "status": node.get("status", ""),
            "setup_class": node.get("setup_class", ""),
            "timeframes": node.get("timeframes", []),
            "root_id_count": len(root_ids),
        }
        enriched["metric_sources"] = sources
        enriched["source_match_status"] = "matched" if sources else "missing"
        enriched_items.append(enriched)
    enriched_plan = dict(action_plan)
    enriched_plan["work_items"] = enriched_items
    enriched_plan["metric_source_status"] = (
        "attached" if any(item.get("metric_sources") for item in enriched_items) else "missing"
    )
    enriched_plan["metric_source_count"] = sum(len(item.get("metric_sources", []) or []) for item in enriched_items)
    enriched_plan["production_effect"] = "none"
    return enriched_plan


def _product_metric_checklist(metric_summary: dict[str, Any], *, product_role: str) -> dict[str, Any]:
    checks = {
        "forward_relative_return_vs_basket": metric_summary.get("median_forward_relative_return") is not None,
        "champion_baseline_delta": metric_summary.get("role_delta_vs_champion_baseline") is not None,
        "hit_rate": metric_summary.get("hit_rate") is not None,
        "drawdown": metric_summary.get("median_max_drawdown") is not None,
        "mfe_mae": metric_summary.get("mfe_mae_ratio") is not None,
        "symbol_breadth": metric_summary.get("unique_symbols") is not None,
        "event_diversity": metric_summary.get("event_diversity") is not None,
    }
    if product_role == "warning_blocker":
        checks["missed_upside_cost"] = metric_summary.get("missed_upside_cost") is not None
        checks["avoided_downside_benefit"] = metric_summary.get("avoided_downside_benefit") is not None
    present = [name for name, value in checks.items() if value]
    missing = [name for name, value in checks.items() if not value]
    return {
        "present": present,
        "missing": missing,
        "complete": not missing,
        "completion_ratio": round(len(present) / len(checks), 3) if checks else 0.0,
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
        source_summaries = [source.get("metric_summary", {}) for source in metric_sources]
        source_decisions = {str(summary.get("role_decision", "")) for summary in source_summaries if summary}
        if "shadow_challenger_promising" in source_decisions:
            decision = "shadow_challenger_promising_needs_fresh_validation"
        elif status == "metric_source_missing":
            decision = "metric_source_extractor_required"
        else:
            decision = "needs_fresh_or_control_validation"
        metric_summary = metric_sources[0].get("metric_summary", {}) if metric_sources else {}
        product_role = str(item.get("product_role", ""))
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
                "metric_summary": metric_summary,
                "product_metric_checklist": _product_metric_checklist(metric_summary, product_role=product_role),
                "decision": decision,
                "production_effect": "none",
            }
        )
    status = "no_candidates"
    if results and len(missing_metric_sources) == len(results):
        status = "blocked_missing_metric_sources"
    elif results and missing_metric_sources:
        status = "shadow_comparison_partial_source_gaps"
    elif results:
        status = "shadow_comparison_complete"
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
            if results and len(missing_metric_sources) == len(results)
            else "run_fresh_or_control_validation_for_promising_shadow_challengers"
            if results
            else "broaden_hypothesis_source"
        ),
        "production_effect": "none",
    }


def _visual_review_focus(product_role: str) -> tuple[str, list[str]]:
    if product_role == "warning_blocker":
        return (
            "blocker_false_positive_and_avoided_downside_review",
            [
                "Was the warning visually legible before the downside move?",
                "Would this have blocked too many constructive resets?",
                "Is avoided downside larger than missed upside for the reviewed examples?",
            ],
        )
    if product_role == "reset_quality":
        return (
            "reset_quality_readability_review",
            [
                "Does the reset look like constructive cooling or unstable weakness?",
                "Is the oscillator still early enough to matter?",
                "Does the setup require a second base, retest, or reclaim confirmation?",
            ],
        )
    if product_role == "bullish_permission":
        return (
            "permission_signal_readability_review",
            [
                "Does the permission clue appear before obvious price confirmation?",
                "Does it avoid overheated late entries?",
                "Is relative strength improving versus the basket?",
            ],
        )
    return (
        "shadow_candidate_readability_review",
        [
            "Is the candidate visually readable on the oscillator?",
            "Does the chart match the claimed product role?",
            "What false-positive pattern should be archived?",
        ],
    )


def build_champion_challenger_visual_review_queue(results: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for result in results.get("results", []) or []:
        product_role = str(result.get("product_role", ""))
        focus, questions = _visual_review_focus(product_role)
        metric_summary = result.get("metric_summary", {}) or {}
        metric_sources = result.get("available_metric_sources", []) or []
        role_delta = _safe_float(metric_summary.get("role_delta_vs_champion_baseline")) or 0.0
        rank_score = _safe_float(metric_summary.get("rank_score")) or 0.0
        event_diversity = _safe_float(metric_summary.get("event_diversity")) or 0.0
        visual_priority_score = abs(role_delta) * 100.0 + rank_score + min(event_diversity, 50.0) * 0.1
        items.append(
            {
                "belief_id": result.get("belief_id"),
                "product_role": product_role,
                "champion": result.get("champion"),
                "challenger": result.get("challenger"),
                "decision": result.get("decision"),
                "review_status": "ready_for_visual_review" if metric_sources else "blocked_missing_metric_source",
                "review_focus": focus,
                "review_questions": questions,
                "visual_priority_score": round(visual_priority_score, 3),
                "metric_checklist": result.get("product_metric_checklist", {}),
                "metric_summary": metric_summary,
                "evidence_sources": [
                    {
                        "loop_dir": source.get("loop_dir"),
                        "ranked": source.get("ranked"),
                        "variant_records": source.get("variant_records"),
                        "strict_referee": source.get("strict_referee"),
                        "bullish_evidence": source.get("bullish_evidence"),
                    }
                    for source in metric_sources
                ],
                "required_labels": [
                    "visual_readability",
                    "product_role_match",
                    "false_positive_shape",
                    "promotion_blocker",
                ],
                "production_effect": "none",
            }
        )
    items = sorted(items, key=lambda item: float(item.get("visual_priority_score", 0.0) or 0.0), reverse=True)
    ready_count = len([item for item in items if item.get("review_status") == "ready_for_visual_review"])
    if not items:
        status = "no_candidates"
    elif ready_count == 0:
        status = "blocked_missing_metric_sources"
    elif ready_count < len(items):
        status = "ready_with_source_gaps"
    else:
        status = "ready"
    return {
        "model": CEO_VISUAL_REVIEW_QUEUE_MODEL,
        "generated_at": utc_now_iso(),
        "status": status,
        "candidate_count": len(items),
        "ready_count": ready_count,
        "items": items,
        "guardrail": "This queue requests visual review only. It does not validate or promote a product candidate.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_champion_challenger_visual_review_queue(queue: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Visual Review Queue",
        "",
        f"Generated: {queue.get('generated_at')}",
        f"Status: {queue.get('status')}",
        f"Ready: {queue.get('ready_count')}/{queue.get('candidate_count')}",
        "",
        "## Candidates",
        "",
    ]
    for item in queue.get("items", []) or []:
        lines.append(
            "- "
            f"{item.get('belief_id')} role={item.get('product_role')} "
            f"status={item.get('review_status')} focus={item.get('review_focus')} "
            f"priority={item.get('visual_priority_score')}"
        )
    if not queue.get("items"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(queue.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


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
        if entry.get("status") in CEO_NO_PROGRESS_STATUSES
        or entry.get("meaningful_progress") is False
    ]
    loop_meltdown = build_ceo_loop_meltdown_check(ledger_entries, action_result)
    intervention_required = (repeated_decisions and len(no_progress) >= 2) or bool(loop_meltdown["strategy_change_required"])
    return {
        "model": CEO_SELF_AUDIT_MODEL,
        "generated_at": utc_now_iso(),
        "latest_decision": action_result.get("decision"),
        "latest_action": action_result.get("action_taken"),
        "latest_status": action_result.get("status"),
        "recent_action_count": len(recent),
        "repeated_decision_detected": repeated_decisions,
        "recent_no_progress_count": len(no_progress),
        "loop_meltdown": loop_meltdown,
        "intervention_required": intervention_required,
        "intervention": (
            loop_meltdown["recommended_intervention"]
            if loop_meltdown["strategy_change_required"]
            else
            "build_missing_capability_or_change_strategy_before_more_lab_blocks"
            if repeated_decisions and len(no_progress) >= 2
            else CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION
        ),
        "production_effect": "none",
    }


def _action_evidence_provenance(action_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "command_executed": action_result.get("command_executed"),
        "input_artifacts": _json_safe(action_result.get("inputs", {}) or {}),
        "output_artifacts": _json_safe(action_result.get("outputs", {}) or {}),
        "status": action_result.get("status"),
        "next_allowed_actions": _json_safe(action_result.get("next_allowed_actions", []) or []),
    }


def _is_no_progress_action(entry: dict[str, Any]) -> bool:
    return entry.get("status") in CEO_NO_PROGRESS_STATUSES or entry.get("meaningful_progress") is False


def build_ceo_loop_meltdown_check(
    ledger_entries: list[dict[str, Any]],
    action_result: dict[str, Any],
    *,
    window: int = 5,
) -> dict[str, Any]:
    recent = ledger_entries[-window:]
    if not recent and action_result:
        recent = [action_result]
    current_decision = str(action_result.get("decision", ""))
    current_action = str(action_result.get("action_taken", ""))
    current_status = str(action_result.get("status", ""))
    current_fingerprint = (current_decision, current_action, current_status)
    decision_repeat_count = len([entry for entry in recent if str(entry.get("decision", "")) == current_decision])
    fingerprint_repeat_count = len(
        [
            entry
            for entry in recent
            if (
                str(entry.get("decision", "")),
                str(entry.get("action_taken", "")),
                str(entry.get("status", "")),
            )
            == current_fingerprint
        ]
    )
    no_progress_count = len([entry for entry in recent if _is_no_progress_action(entry)])
    manual_gate_count = len(
        [
            entry
            for entry in recent
            if str(entry.get("status", "")) == "manual_gate"
            or "import_or_curate_fresh_ohlcv_data" in [str(item) for item in entry.get("next_allowed_actions", []) or []]
        ]
    )
    capability_builder_count = len(
        [
            entry
            for entry in recent
            if any(str(item).startswith("build_") for item in entry.get("next_allowed_actions", []) or [])
        ]
    )
    strategy_change_required = (
        (fingerprint_repeat_count >= 2 and no_progress_count >= 2)
        or manual_gate_count >= 2
        or capability_builder_count >= 2
    )
    if manual_gate_count >= 2:
        recommended = "stop_for_manual_data_import"
    elif capability_builder_count >= 2:
        recommended = "build_missing_capability"
    elif strategy_change_required:
        recommended = "patch_research_infra_or_broaden_hypothesis_source"
    else:
        recommended = CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION
    severity = "clear"
    if strategy_change_required:
        severity = "fail" if fingerprint_repeat_count >= 3 or no_progress_count >= 3 else "warn"
    return {
        "window": window,
        "recent_action_count": len(recent),
        "current_fingerprint": list(current_fingerprint),
        "decision_repeat_count": decision_repeat_count,
        "fingerprint_repeat_count": fingerprint_repeat_count,
        "no_progress_count": no_progress_count,
        "manual_gate_count": manual_gate_count,
        "capability_builder_count": capability_builder_count,
        "strategy_change_required": strategy_change_required,
        "recommended_intervention": recommended,
        "severity": severity,
        "production_effect": "none",
    }


def _latest_prior_failure(
    ledger_entries: list[dict[str, Any]],
    action_result: dict[str, Any],
) -> dict[str, Any] | None:
    prior_entries = ledger_entries
    current_generated_at = action_result.get("generated_at")
    if prior_entries and current_generated_at and prior_entries[-1].get("generated_at") == current_generated_at:
        prior_entries = prior_entries[:-1]
    for entry in reversed(prior_entries):
        if _is_no_progress_action(entry):
            return entry
    return None


def build_failure_avoidance_check(
    ledger_entries: list[dict[str, Any]],
    action_result: dict[str, Any],
) -> dict[str, Any]:
    prior_failure = _latest_prior_failure(ledger_entries, action_result)
    current_is_failure = _is_no_progress_action(action_result)
    if not prior_failure:
        status = "not_applicable"
        repeated = False
    else:
        repeated = (
            current_is_failure
            and str(prior_failure.get("decision", "")) == str(action_result.get("decision", ""))
            and str(prior_failure.get("status", "")) == str(action_result.get("status", ""))
        )
        status = "repeated_prior_failure" if repeated else "avoided_prior_failure"
        if current_is_failure and not repeated:
            status = "new_failure_or_unresolved"
    return {
        "status": status,
        "repeated_prior_failure": repeated,
        "current_is_failure": current_is_failure,
        "prior_failure": (
            {
                "decision": prior_failure.get("decision"),
                "action_taken": prior_failure.get("action_taken"),
                "status": prior_failure.get("status"),
                "meaningful_progress": prior_failure.get("meaningful_progress"),
            }
            if prior_failure
            else {}
        ),
    }


def build_ceo_action_outcome_card(
    action_result: dict[str, Any],
    self_audit: dict[str, Any],
    ledger_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    status = str(action_result.get("status", ""))
    meaningful_progress = bool(action_result.get("meaningful_progress"))
    if meaningful_progress and status not in CEO_NO_PROGRESS_STATUSES:
        progress_class = "progress"
    elif meaningful_progress:
        progress_class = "infrastructure_or_gap_progress"
    else:
        progress_class = "no_progress"
    memory_delta_required = progress_class != "progress" or bool(self_audit.get("intervention_required"))
    next_actions = [str(item) for item in action_result.get("next_allowed_actions", []) or []]
    failure_avoidance = build_failure_avoidance_check(ledger_entries, action_result)
    return {
        "model": CEO_ACTION_OUTCOME_CARD_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": action_result.get("run_id"),
        "lab_run_id": action_result.get("lab_run_id"),
        "decision": action_result.get("decision"),
        "action_taken": action_result.get("action_taken"),
        "status": status,
        "progress_class": progress_class,
        "meaningful_progress": meaningful_progress,
        "next_allowed_actions": next_actions,
        "recent_action_count": min(3, len(ledger_entries)),
        "evidence_provenance": _action_evidence_provenance(action_result),
        "failure_avoidance": failure_avoidance,
        "product_evidence_delta": "none",
        "product_evidence_level": "not_evaluated",
        "missing_product_evidence": [
            "fresh_or_withheld_data_survival",
            "deterministic_product_metrics",
            "visual_review",
            "promotion_proposal_with_user_approval",
        ],
        "next_product_gate": "fresh_control_validation_or_visual_review_before_product_language",
        "product_language_allowed": False,
        "self_audit": {
            "repeated_decision_detected": bool(self_audit.get("repeated_decision_detected")),
            "recent_no_progress_count": self_audit.get("recent_no_progress_count", 0),
            "intervention_required": bool(self_audit.get("intervention_required")),
            "intervention": self_audit.get("intervention"),
        },
        "memory_delta_required": memory_delta_required,
        "memory_delta_hint": (
            "Write or update Obsidian no-repeat/capability context before repeating this action."
            if memory_delta_required
            else "No immediate memory repair required beyond normal artifact review."
        ),
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


def render_ceo_action_outcome_card(card: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Action Outcome Card",
        "",
        f"Generated: {card.get('generated_at')}",
        f"Run: {card.get('run_id')}",
        f"Lab run: {card.get('lab_run_id')}",
        f"Decision: {card.get('decision')}",
        f"Action taken: {card.get('action_taken')}",
        f"Status: {card.get('status')}",
        f"Progress class: {card.get('progress_class')}",
        f"Meaningful progress: {card.get('meaningful_progress')}",
        "",
        "## Next Actions",
        "",
    ]
    next_actions = card.get("next_allowed_actions", []) or []
    if next_actions:
        lines.extend(f"- {item}" for item in next_actions)
    else:
        lines.append("- none")
    provenance = card.get("evidence_provenance", {}) or {}
    lines.extend(
        [
            "",
            "## Evidence Provenance",
            "",
            f"- Command: {provenance.get('command_executed') or 'none'}",
            f"- Inputs: {provenance.get('input_artifacts') or {}}",
            f"- Outputs: {provenance.get('output_artifacts') or {}}",
            "",
            "## Product Evidence",
            "",
            f"- Delta: {card.get('product_evidence_delta')}",
            f"- Level: {card.get('product_evidence_level')}",
            f"- Next gate: {card.get('next_product_gate')}",
            f"- Product language allowed: {card.get('product_language_allowed')}",
        ]
    )
    failure = card.get("failure_avoidance", {}) or {}
    prior = failure.get("prior_failure", {}) or {}
    lines.extend(
        [
            "",
            "## Failure Avoidance",
            "",
            f"- Status: {failure.get('status')}",
            f"- Repeated prior failure: {failure.get('repeated_prior_failure')}",
            f"- Prior failure: {prior or 'none'}",
        ]
    )
    audit = card.get("self_audit", {}) or {}
    lines.extend(
        [
            "",
            "## Self Audit",
            "",
            f"- Repeated decision: {audit.get('repeated_decision_detected')}",
            f"- Recent no-progress count: {audit.get('recent_no_progress_count')}",
            f"- Intervention required: {audit.get('intervention_required')}",
            f"- Intervention: {audit.get('intervention')}",
            "",
            "## Memory",
            "",
            f"- Memory delta required: {card.get('memory_delta_required')}",
            f"- Hint: {card.get('memory_delta_hint')}",
            "",
            "## Guardrail",
            "",
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _contract_for_decision(decision_kind: str) -> dict[str, Any]:
    contracts = {
        "run_champion_challenger": {
            "allowed_command": "riskflow ceo champion-challenger",
            "allowed_scope": "shadow product-delta comparison only",
            "input_artifacts": ["product_delta_scoreboard.yaml", "champion_challenger_action_plan.yaml"],
            "expected_artifacts": ["champion_challenger_results.yaml", "champion_challenger_results.md"],
            "stop_conditions": ["missing metric sources", "no shadow candidates", "stop.request exists"],
        },
        "run_fresh_or_control_validation_for_promising_shadow_challengers": {
            "allowed_command": "riskflow ceo fresh-control-validation",
            "allowed_scope": "fresh/control validation planning only",
            "input_artifacts": ["champion_challenger_results.yaml"],
            "expected_artifacts": ["fresh_control_validation_plan.yaml", "fresh_control_validation_plan.md"],
            "stop_conditions": ["missing champion/challenger results", "fresh data required", "source gaps remain"],
        },
        "continue_governed_research": {
            "allowed_command": "riskflow ceo run-block",
            "allowed_scope": "one bounded governed lab block",
            "input_artifacts": ["executive_decision_packet.md", "lab ops runtime state"],
            "expected_artifacts": ["latest_status.yaml", "executive_decision_packet.md"],
            "stop_conditions": ["stop.request exists", "true blocker", "budget exhausted", "governance audit failed"],
        },
        "request_fresh_data": {
            "allowed_command": "riskflow ceo fresh-data-preflight",
            "allowed_scope": "inspect local data readiness before any manual fresh OHLCV import",
            "input_artifacts": ["fresh_control_validation_plan.yaml", "lab status"],
            "expected_artifacts": ["fresh_data_preflight.yaml", "fresh_data_preflight.md"],
            "stop_conditions": ["local data below min active members", "fresh data import still requires manual workflow"],
        },
        "run_frozen_candidate_validation": {
            "allowed_command": "riskflow ceo frozen-candidate-validation",
            "allowed_scope": "compile frozen validation specs from approved shadow candidates and local data readiness",
            "input_artifacts": ["fresh_control_validation_plan.yaml", "fresh_data_preflight.yaml"],
            "expected_artifacts": ["frozen_candidate_validation_plan.yaml", "frozen_candidate_validation_plan.md"],
            "stop_conditions": ["missing fresh/control plan", "fresh data preflight not safe", "no candidate specs"],
        },
        "run_frozen_validation_executor": {
            "allowed_command": "riskflow ceo frozen-validation-executor",
            "allowed_scope": "replay frozen specs against existing source artifacts only; no production promotion",
            "input_artifacts": ["frozen_candidate_validation_plan.yaml"],
            "expected_artifacts": ["frozen_validation_execution_result.yaml", "frozen_validation_execution_result.md"],
            "stop_conditions": ["missing frozen specs", "missing executable source artifacts", "source replay is not fresh proof"],
        },
        "run_frozen_validation_rerun": {
            "allowed_command": "riskflow ceo frozen-validation-rerun",
            "allowed_scope": "rerun frozen grammar-search adapter grid on local data; no production promotion",
            "input_artifacts": ["frozen_validation_rerun_grid.yaml"],
            "expected_artifacts": ["frozen_validation_rerun_result.yaml", "frozen_validation_rerun_result.md"],
            "stop_conditions": ["missing rerun grid", "missing local data", "rerun remains non-promotional without fresh or withheld snapshot rules"],
        },
        "run_fresh_withheld_validation_contract": {
            "allowed_command": "riskflow ceo fresh-withheld-validation-contract",
            "allowed_scope": "freeze fresh/withheld snapshot rules and pass/fail gates; no validation execution or promotion",
            "input_artifacts": ["frozen_candidate_validation_plan.yaml", "frozen_validation_rerun_result.yaml", "fresh_data_preflight.yaml"],
            "expected_artifacts": ["fresh_withheld_validation_contract.yaml", "fresh_withheld_validation_contract.md"],
            "stop_conditions": ["missing frozen plan", "missing adapter rerun evidence", "no safe local/fresh data context"],
        },
        "run_fresh_withheld_snapshot_manifest": {
            "allowed_command": "riskflow ceo fresh-withheld-snapshot-manifest",
            "allowed_scope": "write a fresh/withheld snapshot authority manifest draft; no validation execution or promotion",
            "input_artifacts": ["fresh_withheld_validation_contract.yaml", "fresh_data_preflight.yaml"],
            "expected_artifacts": ["fresh_withheld_snapshot_manifest.yaml", "fresh_withheld_snapshot_manifest.md"],
            "stop_conditions": ["missing ready contract", "missing safe preflight", "manual snapshot authority still required"],
        },
        "run_fresh_withheld_validation_executor": {
            "allowed_command": "riskflow ceo fresh-withheld-validation-executor",
            "allowed_scope": "manifest-gated fresh/withheld validation execution; must block if snapshot authority is missing",
            "input_artifacts": ["fresh_withheld_validation_contract.yaml", "fresh_withheld_snapshot_manifest.yaml"],
            "expected_artifacts": ["fresh_withheld_validation_execution_result.yaml", "fresh_withheld_validation_execution_result.md"],
            "stop_conditions": ["missing ready contract", "missing snapshot manifest", "snapshot overlaps source evidence", "production promotion requires approval"],
        },
        "import_or_curate_fresh_ohlcv_data": {
            "allowed_command": None,
            "allowed_scope": "manual data import/curation gate only",
            "input_artifacts": ["fresh_data_preflight.yaml"],
            "expected_artifacts": ["new or updated OHLCV CSV files outside CEO automation"],
            "stop_conditions": ["manual data export unavailable", "local CSVs remain below min active members"],
        },
        "patch_research_infra": {
            "allowed_command": "riskflow ceo patch-research-infra",
            "allowed_scope": "governed lane-recovery queue planning and runtime queue append only",
            "input_artifacts": ["evidence_mart.yaml", "belief_graph.yaml", "lane_assignment.yaml"],
            "expected_artifacts": ["research_infra_patch_plan.yaml", "research_infra_recovery_queue.yaml"],
            "stop_conditions": ["missing director inputs", "recovery audit failed", "no supported recovery specs"],
        },
        "broaden_hypothesis_source": {
            "allowed_command": "riskflow ceo broaden-hypothesis-source",
            "allowed_scope": "compile Obsidian/research source hypotheses into shadow runtime queue items only",
            "input_artifacts": ["obsidian wiki", "research/grammar"],
            "expected_artifacts": ["hypothesis_source_broadening_plan.yaml", "hypothesis_source_broadening_queue.yaml"],
            "stop_conditions": ["no broadening sources", "queue already contains compiled hypotheses"],
        },
        "resolve_ceo_self_audit_intervention": {
            "allowed_command": None,
            "allowed_scope": "route a self-audit intervention to one safe next action",
            "input_artifacts": ["ceo_self_audit.yaml", "ceo_action_ledger.jsonl", "binding_action_result.yaml"],
            "expected_artifacts": ["binding_action_result.yaml", "action_outcome_card.yaml"],
            "stop_conditions": ["same no-progress action would repeat", "no supported repair route"],
        },
    }
    return contracts.get(
        decision_kind,
        {
            "allowed_command": None,
            "allowed_scope": "record capability gap or stop without running generic research",
            "input_artifacts": ["executive_decision_packet.md", "company_status.yaml"],
            "expected_artifacts": ["capability_gap.yaml", "binding_action_result.yaml"],
            "stop_conditions": ["unsupported decision", "true blocker", "stop.request exists"],
        },
    )


def build_ceo_action_contract(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    decision: dict[str, Any],
) -> dict[str, Any]:
    decision_kind = str(decision.get("decision", "unknown"))
    details = _contract_for_decision(decision_kind)
    return {
        "model": CEO_ACTION_CONTRACT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": decision_kind,
        "rationale": decision.get("rationale", ""),
        "allowed_command": details["allowed_command"],
        "allowed_scope": details["allowed_scope"],
        "input_artifacts": details["input_artifacts"],
        "expected_artifacts": details["expected_artifacts"],
        "stop_conditions": details["stop_conditions"],
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


def render_ceo_action_contract(contract: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Action Contract",
        "",
        f"Generated: {contract.get('generated_at')}",
        f"Run: {contract.get('run_id')}",
        f"Lab run: {contract.get('lab_run_id')}",
        f"Decision: {contract.get('decision')}",
        f"Allowed command: {contract.get('allowed_command') or 'none'}",
        f"Allowed scope: {contract.get('allowed_scope')}",
        f"Production effect: {contract.get('production_effect')}",
        "",
        "## Expected Artifacts",
        "",
    ]
    lines.extend(f"- {item}" for item in contract.get("expected_artifacts", []) or [])
    lines.extend(["", "## Stop Conditions", ""])
    lines.extend(f"- {item}" for item in contract.get("stop_conditions", []) or [])
    lines.extend(["", "## Forbidden Changes", ""])
    lines.extend(f"- {item}" for item in contract.get("forbidden_changes", []) or [])
    return "\n".join(lines).rstrip() + "\n"


def _write_ceo_action_contract(
    options: CeoOpsOptions,
    ceo_run_id: str,
    lab_run_id: str,
    decision: dict[str, Any],
) -> dict[str, Path]:
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    contract = build_ceo_action_contract(ceo_run_id=ceo_run_id, lab_run_id=lab_run_id, decision=decision)
    contract_path = root / "action_contract.yaml"
    report_path = root / "action_contract.md"
    atomic_write_yaml(contract_path, contract)
    atomic_write_text(report_path, render_ceo_action_contract(contract))
    return {"action_contract": contract_path, "action_contract_report": report_path}


def _ceo_dispatch_artifact_fingerprint(path: Path) -> dict[str, Any]:
    payload = _load_yaml_if_exists(path) if path.suffix in {".yaml", ".yml"} else {}
    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": _file_sha256(path) if path.exists() and path.is_file() else "",
        "model": payload.get("model", ""),
        "generated_at": payload.get("generated_at", ""),
        "status": payload.get("status", ""),
    }


def _dispatch_receipt_reference(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": _file_sha256(path) if path.exists() and path.is_file() else "",
    }


def _binding_action_is_blocked_or_noop(action_result: dict[str, Any]) -> bool:
    action_status = str(action_result.get("status", ""))
    action_taken = str(action_result.get("action_taken", ""))
    return action_status in {"blocked", "manual_gate"} or action_taken in {"none", "blocked_preflight_gate"} or action_taken.startswith("blocked_")


def _receipt_can_back_binding_action(
    *,
    receipt: dict[str, Any],
    receipt_reference_path: Path,
    ceo_run_id: str,
    lab_run_id: str,
    action_result: dict[str, Any],
    expected_dispatch_mode: str,
) -> bool:
    if (
        receipt.get("model") != CEO_DISPATCH_RECEIPT_MODEL
        or receipt.get("run_id") != ceo_run_id
        or receipt.get("lab_run_id") != lab_run_id
        or receipt.get("decision") != action_result.get("decision")
    ):
        return False
    if not receipt_reference_path.exists() or receipt_reference_path.name == "dispatch_receipt.yaml":
        return False
    if receipt_reference_path.parent.name != "dispatch_receipts":
        return False
    accepted_dispatch_modes = {expected_dispatch_mode}
    if expected_dispatch_mode == "bound_dispatch":
        accepted_dispatch_modes.add("execute_next")
    if str(receipt.get("dispatch_mode", "")) not in accepted_dispatch_modes:
        return False
    if _binding_action_is_blocked_or_noop(action_result):
        return receipt.get("safe_to_dispatch") is False and receipt.get("status") == "dispatch_blocked"
    return receipt.get("safe_to_dispatch") is True and receipt.get("status") == "dispatch_allowed"


def _receipt_slug(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
    return slug or "unknown"


def _dispatch_trust_artifacts(root: Path) -> dict[str, Path]:
    return {
        "decision_packet": root / "executive_decision_packet.md",
        "action_contract": root / "action_contract.yaml",
        "preflight_gate": root / "preflight_gate.yaml",
        "trace_grade": root / "trace_grade.yaml",
        "ceo_replay": root / "ceo_replay.yaml",
        "ceo_eval_suite": root / "ceo_eval_suite.yaml",
        "guardrail_audit": root / "guardrail_audit.yaml",
        "memory_delta": root / "memory_delta.yaml",
        "approval_queue": root / "approval_queue.yaml",
        "approval_status": root / "approval_status.yaml",
        "mission_score": root / "mission_score.yaml",
        "strategy_capital_dashboard": root / "strategy_capital_dashboard.yaml",
        "artifact_coherence": root / "artifact_coherence.yaml",
        "resumption_brief": root / "resumption_brief.yaml",
    }


def build_ceo_dispatch_receipt(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    root: Path,
    decision: dict[str, Any],
    preflight_gate: dict[str, Any],
    approval_queue: dict[str, Any] | None = None,
    safe_to_dispatch: bool,
    reason: str,
    dispatch_mode: str,
    preflight_allows_repair: bool = False,
) -> dict[str, Any]:
    decision_kind = str(decision.get("decision", "unknown"))
    action_contract = _load_yaml_if_exists(root / "action_contract.yaml")
    contract_template = _contract_for_decision(decision_kind)
    blockers = [
        str(item.get("blocker", ""))
        for item in preflight_gate.get("blockers", []) or []
        if item.get("blocker")
    ]
    trust_artifacts = {
        name: _ceo_dispatch_artifact_fingerprint(path)
        for name, path in _dispatch_trust_artifacts(root).items()
    }
    return {
        "model": CEO_DISPATCH_RECEIPT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "dispatch_mode": dispatch_mode,
        "decision": decision_kind,
        "rationale": decision.get("rationale", ""),
        "allowed_command": action_contract.get("allowed_command", contract_template["allowed_command"]),
        "allowed_scope": action_contract.get("allowed_scope", contract_template["allowed_scope"]),
        "action_contract_source": "artifact" if action_contract else "decision_contract_template",
        "safe_to_dispatch": bool(safe_to_dispatch),
        "status": "dispatch_allowed" if safe_to_dispatch else "dispatch_blocked",
        "reason": reason,
        "preflight_status": preflight_gate.get("status", "not_run"),
        "preflight_safe_to_execute": preflight_gate.get("safe_to_execute", False),
        "preflight_allows_repair": preflight_allows_repair,
        "preflight_blockers": blockers,
        "pending_approval_count": int((approval_queue or {}).get("pending_count", 0) or 0),
        "trust_artifact_fingerprints": trust_artifacts,
        "guardrails": {
            "product_language_allowed": False,
            "production_effect": "none",
            "promotion_authority": "none",
            "forbidden_changes": action_contract.get(
                "forbidden_changes",
                [
                    "core_signal_v0",
                    "Pine_or_TradingView_defaults",
                    "production_scores",
                    "production_rankings",
                    "production_states",
                    "production_alerts",
                ],
            ),
        },
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_dispatch_receipt(receipt: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Dispatch Receipt",
        "",
        f"Generated: {receipt.get('generated_at')}",
        f"Receipt id: {receipt.get('receipt_id', '')}",
        f"Run: {receipt.get('run_id')}",
        f"Lab run: {receipt.get('lab_run_id')}",
        f"Mode: {receipt.get('dispatch_mode')}",
        f"Decision: {receipt.get('decision')}",
        f"Status: {receipt.get('status')}",
        f"Safe to dispatch: {receipt.get('safe_to_dispatch')}",
        f"Reason: {receipt.get('reason')}",
        f"Allowed command: {receipt.get('allowed_command') or 'none'}",
        f"Action contract source: {receipt.get('action_contract_source')}",
        f"Snapshot path: {receipt.get('snapshot_path', '')}",
        f"Preflight: {receipt.get('preflight_status')} safe={receipt.get('preflight_safe_to_execute')}",
        f"Preflight blockers: {receipt.get('preflight_blockers') or []}",
        f"Pending approvals: {receipt.get('pending_approval_count')}",
        "",
        "## Trust Artifacts",
        "",
    ]
    for name, item in (receipt.get("trust_artifact_fingerprints", {}) or {}).items():
        lines.append(
            f"- {name}: exists={item.get('exists')} status={item.get('status') or 'n/a'} "
            f"sha256={item.get('sha256') or 'missing'}"
        )
    lines.extend(
        [
            "",
            "Production effect: none.",
            "Product language allowed: false.",
            "Promotion authority: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _write_ceo_dispatch_receipt(
    options: CeoOpsOptions,
    ceo_run_id: str,
    lab_run_id: str,
    decision: dict[str, Any],
    *,
    preflight_gate: dict[str, Any],
    approval_queue: dict[str, Any] | None = None,
    safe_to_dispatch: bool,
    reason: str,
    dispatch_mode: str,
    preflight_allows_repair: bool = False,
) -> dict[str, Path]:
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    receipt = build_ceo_dispatch_receipt(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        root=root,
        decision=decision,
        preflight_gate=preflight_gate,
        approval_queue=approval_queue,
        safe_to_dispatch=safe_to_dispatch,
        reason=reason,
        dispatch_mode=dispatch_mode,
        preflight_allows_repair=preflight_allows_repair,
    )
    receipt_id = (
        f"{_receipt_slug(str(receipt.get('generated_at', utc_now_iso())))}"
        f"__{_receipt_slug(str(receipt.get('decision', 'unknown')))}"
        f"__{_receipt_slug(str(receipt.get('status', 'unknown')))}"
    )
    snapshot_dir = root / "dispatch_receipts"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / f"{receipt_id}.yaml"
    receipt["receipt_id"] = receipt_id
    receipt["latest_alias_path"] = str(root / "dispatch_receipt.yaml")
    receipt["snapshot_path"] = str(snapshot_path)
    path = root / "dispatch_receipt.yaml"
    report_path = root / "dispatch_receipt.md"
    atomic_write_yaml(snapshot_path, receipt)
    atomic_write_yaml(path, receipt)
    atomic_write_text(report_path, render_ceo_dispatch_receipt(receipt))
    return {"dispatch_receipt": path, "dispatch_receipt_snapshot": snapshot_path, "dispatch_receipt_report": report_path}


def build_ceo_trace_grade(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    root: Path,
    ledger_entries: list[dict[str, Any]],
    action_result: dict[str, Any],
    self_audit: dict[str, Any],
    heartbeat_status: dict[str, Any],
    company_status: dict[str, Any],
) -> dict[str, Any]:
    supported_next_actions = {
        "clear_stop_request_after_user_approval",
        "resolve_true_blocker",
        "write_promotion_proposal_and_wait_for_user_approval",
        "run_champion_challenger",
        "run_fresh_or_control_validation_for_promising_shadow_challengers",
        "continue_governed_research",
        "patch_research_infra",
        "broaden_hypothesis_source",
        "request_fresh_data",
        "run_frozen_candidate_validation",
        "run_frozen_validation_executor",
        "run_frozen_validation_rerun",
        "run_fresh_withheld_validation_contract",
        "repair_fresh_withheld_contract_inputs",
        "run_fresh_withheld_snapshot_manifest",
        "run_fresh_withheld_validation_executor",
        "import_or_curate_fresh_ohlcv_data",
        "resolve_ceo_self_audit_intervention",
        "stop",
    }
    manual_gate_next_actions = {
        "clear_stop_request_after_user_approval",
        "resolve_true_blocker",
        "write_promotion_proposal_and_wait_for_user_approval",
        "import_or_curate_fresh_ohlcv_data",
        "stop",
    }
    required_artifacts = {
        "heartbeat_status": root / "heartbeat_status.yaml",
        "binding_action_result": root / "binding_action_result.yaml",
        "ceo_action_ledger": root / "ceo_action_ledger.jsonl",
        "ceo_self_audit": root / "ceo_self_audit.yaml",
    }
    artifact_checks = {
        name: {"path": str(path), "exists": path.exists()}
        for name, path in required_artifacts.items()
    }
    action_contract_path = root / "action_contract.yaml"
    action_contract = _load_yaml_if_exists(action_contract_path)
    recent = ledger_entries[-3:]
    repeated_decision = len(recent) >= 2 and len({entry.get("decision") for entry in recent}) == 1
    no_progress_entries = [
        entry
        for entry in recent
        if _is_no_progress_action(entry)
    ]
    failure_avoidance = build_failure_avoidance_check(ledger_entries, action_result)
    loop_meltdown = build_ceo_loop_meltdown_check(ledger_entries, action_result)
    next_actions = [
        "broaden_hypothesis_source" if str(item) == "broaden_product_candidate_source" else str(item)
        for item in action_result.get("next_allowed_actions", []) or []
    ]
    unsupported_next_actions = [
        item
        for item in next_actions
        if item not in supported_next_actions and not item.startswith("build_")
    ]
    manual_next_actions = [item for item in next_actions if item in manual_gate_next_actions]
    manual_data_import_required = (
        str(action_result.get("status", "")) == "manual_gate"
        or str(action_result.get("decision", "")) == "import_or_curate_fresh_ohlcv_data"
        or "import_or_curate_fresh_ohlcv_data" in manual_next_actions
    )
    capability_builder_next_actions = [item for item in next_actions if item.startswith("build_")]
    bounded_executor_next_actions = [
        item
        for item in next_actions
        if item in supported_next_actions and item not in manual_gate_next_actions
    ]
    production_effects = [
        str(payload.get("production_effect", "none"))
        for payload in (action_result, self_audit, heartbeat_status, company_status)
        if isinstance(payload, dict)
    ]
    constraint_violations: list[str] = []
    if any(effect not in {"", "none"} for effect in production_effects):
        constraint_violations.append("non_none_production_effect")
    if company_status.get("governance", {}).get("product_change_allowed"):
        constraint_violations.append("product_change_allowed_requires_user_approval")
    if heartbeat_status.get("production_promotion_required"):
        constraint_violations.append("heartbeat_requires_production_promotion_approval")
    if action_contract and action_contract.get("production_effect") not in {None, "", "none"}:
        constraint_violations.append("action_contract_non_none_production_effect")
    contract_decision = str(action_contract.get("decision", "")) if action_contract else ""
    action_decision = str(action_result.get("decision", ""))
    contract_matches_action = not action_contract or not action_decision or contract_decision == action_decision

    criteria = {
        "artifact_completeness": all(item["exists"] for item in artifact_checks.values()),
        "action_contract_present": bool(action_contract),
        "action_contract_matches_action": contract_matches_action,
        "meaningful_progress": bool(action_result.get("meaningful_progress")),
        "evidence_moved": action_result.get("status")
        not in {*CEO_NO_PROGRESS_STATUSES, None},
        "duplicate_work": repeated_decision,
        "no_progress_count": len(no_progress_entries),
        "constraint_violation": bool(constraint_violations),
        "self_audit_intervention_required": bool(self_audit.get("intervention_required")),
        "next_action_supported": not unsupported_next_actions,
        "manual_gate_next_action_count": len(manual_next_actions),
        "manual_data_import_required": manual_data_import_required,
        "bounded_executor_next_action_count": len(bounded_executor_next_actions),
        "capability_builder_next_action_count": len(capability_builder_next_actions),
        "failure_avoidance_status": failure_avoidance["status"],
        "failure_avoidance_ok": not failure_avoidance["repeated_prior_failure"],
        "loop_meltdown_severity": loop_meltdown["severity"],
        "loop_meltdown_strategy_change_required": loop_meltdown["strategy_change_required"],
        "stop_requested": bool(heartbeat_status.get("stop_requested")),
        "true_blocker": bool(heartbeat_status.get("true_blocker") or company_status.get("true_blocker")),
    }
    issues: list[str] = []
    if not criteria["artifact_completeness"]:
        issues.append("missing_required_trace_artifact")
    if not criteria["action_contract_matches_action"]:
        issues.append("action_contract_mismatch")
    if criteria["duplicate_work"] and criteria["no_progress_count"] >= 2:
        issues.append("repeated_no_progress_decision")
    if criteria["constraint_violation"]:
        issues.extend(constraint_violations)
    if criteria["self_audit_intervention_required"]:
        issues.append("self_audit_intervention_required")
    if not criteria["next_action_supported"]:
        issues.append("unsupported_next_action")
    if criteria["manual_data_import_required"]:
        issues.append("manual_data_import_required")
    if action_result.get("status") == "capability_gap":
        issues.append("capability_gap_open")
    if action_result.get("status") == "blocked" and not criteria["stop_requested"]:
        issues.append("blocked_without_stop_request")
    if failure_avoidance["repeated_prior_failure"]:
        issues.append("repeated_prior_failure")
    if loop_meltdown["strategy_change_required"]:
        issues.append("loop_meltdown_strategy_change_required")

    score = 100
    score -= 20 * (not criteria["artifact_completeness"])
    score -= 15 * (not criteria["action_contract_matches_action"])
    score -= 20 * bool(criteria["duplicate_work"] and criteria["no_progress_count"] >= 2)
    score -= 25 * criteria["constraint_violation"]
    score -= 15 * criteria["self_audit_intervention_required"]
    score -= 15 * (not criteria["next_action_supported"])
    score -= 15 * failure_avoidance["repeated_prior_failure"]
    score -= 20 * loop_meltdown["strategy_change_required"]
    score -= 50 * criteria["manual_data_import_required"]
    score -= 10 * (action_result.get("status") == "capability_gap")
    score -= 10 * (action_result.get("status") == "blocked" and not criteria["stop_requested"])
    score = max(0, int(score))
    verdict = "pass" if score >= 85 and not issues else "warn" if score >= 60 else "fail"
    if criteria["manual_data_import_required"]:
        verdict = "fail"
    if criteria["stop_requested"]:
        recommended = "honor_stop_request"
    elif criteria["true_blocker"]:
        recommended = "resolve_true_blocker"
    elif loop_meltdown["strategy_change_required"]:
        recommended = loop_meltdown["recommended_intervention"]
    elif criteria["manual_data_import_required"]:
        recommended = "stop_for_manual_data_import"
    elif criteria["self_audit_intervention_required"] or unsupported_next_actions:
        recommended = "patch_research_infra_or_broaden_hypothesis_source"
    elif action_result.get("status") == "capability_gap":
        recommended = "build_missing_capability"
    elif not criteria["artifact_completeness"]:
        recommended = "repair_trace_artifacts"
    else:
        recommended = "continue_with_one_bound_ceo_action"
    return {
        "model": CEO_TRACE_GRADE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "score": score,
        "verdict": verdict,
        "trace_scope": "process_only",
        "product_evidence_status": "not_evaluated",
        "product_language_allowed": False,
        "criteria": criteria,
        "issues": issues,
        "artifact_checks": artifact_checks,
        "evidence_provenance": _action_evidence_provenance(action_result),
        "failure_avoidance": failure_avoidance,
        "loop_meltdown": loop_meltdown,
        "action_contract_path": str(action_contract_path) if action_contract else "",
        "recent_action_count": len(recent),
        "latest_decision": action_result.get("decision") or heartbeat_status.get("last_decision"),
        "latest_action": action_result.get("action_taken"),
        "latest_status": action_result.get("status"),
        "unsupported_next_actions": unsupported_next_actions,
        "manual_next_actions": manual_next_actions,
        "bounded_executor_next_actions": bounded_executor_next_actions,
        "capability_builder_next_actions": capability_builder_next_actions,
        "recommended_next_action": recommended,
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


def _decision_quality_expected_artifact(decision: str) -> str:
    mapping = {
        "stop_true_blocker": "stop request and blocker repair notes",
        "run_champion_challenger": "champion_challenger_results.yaml",
        "patch_research_infra": "research_infra_patch_plan.yaml",
        "continue_governed_research": "executive_decision_packet.md",
        "request_fresh_data": "fresh_data_preflight.yaml after CSV import",
        "broaden_hypothesis_source": "hypothesis_source_broadening_plan.yaml",
        "run_frozen_candidate_validation": "frozen_candidate_validation_plan.yaml",
        "run_frozen_validation_executor": "frozen_validation_execution_result.yaml",
        "run_frozen_validation_rerun": "frozen_validation_rerun_result.yaml",
        "run_fresh_withheld_validation_contract": "fresh_withheld_validation_contract.yaml",
        "run_fresh_withheld_snapshot_manifest": "fresh_withheld_snapshot_manifest.yaml",
        "run_fresh_withheld_validation_executor": "fresh_withheld_validation_execution_result.yaml",
        "run_fresh_or_control_validation_for_promising_shadow_challengers": "fresh_control_validation_plan.yaml",
        "import_or_curate_fresh_ohlcv_data": "fresh_data_preflight.yaml after CSV import",
    }
    return mapping.get(decision, "binding_action_result.yaml")


def _decision_quality_candidate(
    *,
    action_id: str,
    score: int,
    rationale: str,
    evidence: dict[str, Any],
    selected_action: str,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "score": int(score),
        "selected": action_id == selected_action,
        "rationale": rationale,
        "why_not_selected": "" if action_id == selected_action else "Lower current evidence priority than the selected action.",
        "expected_artifact": _decision_quality_expected_artifact(action_id),
        "evidence": evidence,
        "production_effect": "none",
    }


def _decision_quality_runtime_authority(
    action_board: dict[str, Any] | None,
    *,
    selected_action: str,
) -> dict[str, Any]:
    if not action_board:
        return {
            "runtime_authority_status": "unknown_action_board",
            "runtime_autonomy_mode": "unknown",
            "executable_next_action": "",
            "executable_next_command": "",
            "executable_next_command_kind": "",
            "runtime_authorized_strategic_route": "",
            "runtime_authorized_route_source": "",
            "effective_runtime_action": "",
            "effective_runtime_command": "",
            "effective_runtime_command_kind": "",
            "effective_runtime_can_execute_now": False,
            "runtime_blocked": True,
            "runtime_block_reason": "action_board_missing",
            "selected_strategic_route_advisory": selected_action,
            "executable_can_execute_now": False,
            "selected_action_is_executable_now": False,
            "selected_action_blocked_by": "action_board_missing",
            "selected_action_runtime_note": "Decision quality could not compare the selected route with an action board.",
        }
    primary = action_board.get("primary_action", {}) or {}
    board_status = str(action_board.get("status", ""))
    primary_action = str(primary.get("action_id", ""))
    command_kind = str(primary.get("command_kind", ""))
    command = str(primary.get("command", ""))
    manual_gate_active = board_status == "manual_gate_required" or primary.get("requires_manual_gate") is True
    can_execute = primary.get("can_execute_now") is True and not manual_gate_active
    command_tokens: list[str] = []
    try:
        command_tokens = shlex.split(command)
    except ValueError:
        command_tokens = []
    bounded_execute_next = (
        can_execute
        and command_kind == "bounded_dispatch"
        and primary_action == "resumption_brief_next_command"
        and "execute-next" in command_tokens
        and "riskflow" in command_tokens
        and "ceo" in command_tokens
    )
    authorized_strategic_route = str(primary.get("authorized_strategic_route", ""))
    authorized_route_source = str(primary.get("authorized_route_source", ""))
    selected_is_direct_action = bool(selected_action) and can_execute and primary_action == selected_action
    selected_is_authorized_route = (
        bool(selected_action)
        and bounded_execute_next
        and bool(authorized_strategic_route)
        and authorized_strategic_route == selected_action
    )
    selected_is_executable = selected_is_direct_action or selected_is_authorized_route
    if selected_is_executable:
        blocked_by = ""
        if authorized_strategic_route:
            runtime_note = (
                "The action board authorizes a bounded execute-next wrapper; decision quality names the "
                "strategic route expected behind that wrapper."
            )
        else:
            runtime_note = "The selected route is also the current executable action-board item."
    elif manual_gate_active:
        blocked_by = f"manual_gate_required:{primary_action or 'unknown_action'}"
        runtime_note = "A manual gate outranks the selected strategic route; do not execute autonomously."
    elif primary.get("needs_implementation"):
        blocked_by = f"implementation_repair_required:{primary_action or 'unknown_action'}"
        runtime_note = "An implementation repair outranks the selected strategic route."
    elif primary.get("diagnostic_only"):
        blocked_by = f"diagnostic_refresh_required:{primary_action or 'unknown_action'}"
        runtime_note = "A diagnostic refresh is the only current action-board item; it is not proof the selected route may execute."
    elif can_execute:
        blocked_by = f"different_executable_action:{primary_action or 'unknown_action'}"
        runtime_note = "The action board exposes a different bounded executable action than the selected strategic route."
    else:
        blocked_by = f"{board_status or 'no_action_board_status'}:{primary_action or 'none'}"
        runtime_note = "The action board does not currently authorize the selected strategic route."
    return {
        "runtime_authority_status": board_status or "unknown_action_board_status",
        "runtime_autonomy_mode": str(action_board.get("autonomy_mode", "")),
        "executable_next_action": primary_action,
        "executable_next_command": command,
        "executable_next_command_kind": command_kind,
        "runtime_authorized_strategic_route": authorized_strategic_route,
        "runtime_authorized_route_source": authorized_route_source,
        "effective_runtime_action": primary_action,
        "effective_runtime_command": command,
        "effective_runtime_command_kind": command_kind,
        "effective_runtime_can_execute_now": can_execute,
        "runtime_blocked": not can_execute,
        "runtime_block_reason": "" if can_execute else blocked_by,
        "selected_strategic_route_advisory": "" if selected_is_executable else selected_action,
        "executable_can_execute_now": can_execute,
        "selected_action_is_executable_now": selected_is_executable,
        "selected_action_blocked_by": blocked_by,
        "selected_action_runtime_note": runtime_note,
    }


def build_ceo_decision_quality(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    company_status: dict[str, Any],
    product_delta: dict[str, Any],
    infra_delta: dict[str, Any],
    decision: dict[str, Any],
    action_board: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lab_status = company_status.get("lab_status", {}) or {}
    governance = company_status.get("governance", {}) or {}
    selected_action = str(decision.get("decision", ""))
    open_lanes = list(governance.get("open_lanes", []) or [])
    candidate_count = int(product_delta.get("candidate_count", 0) or 0)
    stop_reason = str(lab_status.get("stop_reason", ""))
    true_blocker = bool(company_status.get("true_blocker"))
    needs_recovery = infra_delta.get("infra_delta_status") == "needs_recovery_expansion"
    candidates = [
        _decision_quality_candidate(
            action_id="stop_true_blocker",
            score=100 if true_blocker else 5,
            rationale="True blockers override all autonomous action." if true_blocker else "No true blocker is currently reported.",
            evidence={"true_blocker": true_blocker, "stop_reason": stop_reason},
            selected_action=selected_action,
        ),
        _decision_quality_candidate(
            action_id="run_champion_challenger",
            score=90 if candidate_count else 20,
            rationale="Chart-facing candidates need base-vs-challenger evidence." if candidate_count else "No chart-facing candidates are visible.",
            evidence={"candidate_count": candidate_count, "product_delta_status": product_delta.get("chart_facing_value_status")},
            selected_action=selected_action,
        ),
        _decision_quality_candidate(
            action_id="patch_research_infra",
            score=85 if needs_recovery else 25,
            rationale="Recovery expansion is needed before more governed research." if needs_recovery else "Research infrastructure is not the top bottleneck.",
            evidence={"infra_delta_status": infra_delta.get("infra_delta_status")},
            selected_action=selected_action,
        ),
        _decision_quality_candidate(
            action_id="continue_governed_research",
            score=75 if open_lanes else 15,
            rationale="Open governed lanes remain available." if open_lanes else "No open governed lanes are visible.",
            evidence={"open_lanes": open_lanes},
            selected_action=selected_action,
        ),
        _decision_quality_candidate(
            action_id="request_fresh_data",
            score=80 if stop_reason == "request_fresh_data" else 10,
            rationale="The run explicitly requested fresher or broader data." if stop_reason == "request_fresh_data" else "Fresh data is not the current stop reason.",
            evidence={"stop_reason": stop_reason},
            selected_action=selected_action,
        ),
        _decision_quality_candidate(
            action_id="broaden_hypothesis_source",
            score=60 if not candidate_count and not open_lanes else 15,
            rationale="No candidates or lanes remain, so source broadening should come next."
            if not candidate_count and not open_lanes
            else "Existing candidates or lanes should be exploited before broadening.",
            evidence={"candidate_count": candidate_count, "open_lane_count": len(open_lanes)},
            selected_action=selected_action,
        ),
    ]
    if selected_action and selected_action not in {str(item.get("action_id", "")) for item in candidates}:
        candidates.append(
            _decision_quality_candidate(
                action_id=selected_action,
                score=max([int(item.get("score", 0) or 0) for item in candidates] + [50]) + 5,
                rationale=str(decision.get("rationale", "Selected by previous action handoff or specialized dispatcher route.")),
                evidence={"selected_by": "decision_override_or_specialized_route"},
                selected_action=selected_action,
            )
        )
    candidates = sorted(candidates, key=lambda item: (-int(item.get("score", 0)), str(item.get("action_id", ""))))
    selected = next((item for item in candidates if item.get("selected")), candidates[0] if candidates else {})
    runner_up = next((item for item in candidates if not item.get("selected")), {})
    gap = int(selected.get("score", 0) or 0) - int(runner_up.get("score", 0) or 0)
    confidence = "high" if gap >= 20 else "medium" if gap >= 10 else "low"
    runtime_authority = _decision_quality_runtime_authority(action_board, selected_action=selected_action)
    quality = {
        "model": CEO_DECISION_QUALITY_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "decision_quality_written",
        "selected_action": selected_action,
        "selected_score": selected.get("score", 0),
        "runner_up_action": runner_up.get("action_id", ""),
        "runner_up_score": runner_up.get("score", 0),
        "confidence": confidence,
        "score_gap": gap,
        "selected_rationale": decision.get("rationale", selected.get("rationale", "")),
        "expected_artifact": _decision_quality_expected_artifact(selected_action),
        "stop_condition": (
            "Stop or request approval if action board, preflight, approval queue, dispatch receipt, replay, eval, "
            "or guardrail artifacts block the selected action."
        ),
        "alternatives": candidates,
        "evidence_refs": {
            "company_status": "company_status.yaml",
            "product_delta": "product_delta_scoreboard.yaml",
            "infra_delta": "research_infra_delta.yaml",
            "latest_action_result": "binding_action_result.yaml",
            "action_board": "action_board.yaml",
        },
        "guardrail": "Decision quality explains routing only. It does not approve execution, product language, or production changes.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }
    quality.update(runtime_authority)
    return quality


def render_ceo_decision_quality(quality: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Decision Quality",
        "",
        f"Generated: {quality.get('generated_at')}",
        f"Run: {quality.get('run_id')}",
        f"Lab run: {quality.get('lab_run_id')}",
        "",
        "## Runtime Authority",
        "",
        f"- Effective runtime action: {quality.get('effective_runtime_action') or 'none'}",
        f"- Effective runtime command kind: {quality.get('effective_runtime_command_kind') or 'none'}",
        f"- Effective runtime can execute now: {quality.get('effective_runtime_can_execute_now')}",
        f"- Runtime blocked: {quality.get('runtime_blocked')}",
        f"- Runtime block reason: {quality.get('runtime_block_reason') or 'none'}",
        f"- Effective runtime command: `{quality.get('effective_runtime_command') or ''}`",
        f"- Authority status: {quality.get('runtime_authority_status')}",
        f"- Autonomy mode: {quality.get('runtime_autonomy_mode')}",
        f"- Executable next action: {quality.get('executable_next_action') or 'none'}",
        f"- Executable command kind: {quality.get('executable_next_command_kind') or 'none'}",
        f"- Runtime authorized strategic route: {quality.get('runtime_authorized_strategic_route') or 'none'}",
        f"- Runtime authorized route source: {quality.get('runtime_authorized_route_source') or 'none'}",
        f"- Can execute now: {quality.get('executable_can_execute_now')}",
        f"- Selected action executable now: {quality.get('selected_action_is_executable_now')}",
        f"- Selected action blocked by: {quality.get('selected_action_blocked_by') or 'none'}",
        f"- Executable command: `{quality.get('executable_next_command') or ''}`",
        f"- Runtime note: {quality.get('selected_action_runtime_note')}",
        "",
        "## Strategic Selection",
        "",
        f"Selected action: {quality.get('selected_action')}",
        f"Selected strategic route advisory: {quality.get('selected_strategic_route_advisory') or 'none'}",
        f"Selected score: {quality.get('selected_score')}",
        f"Runner-up action: {quality.get('runner_up_action') or 'none'}",
        f"Runner-up score: {quality.get('runner_up_score')}",
        f"Confidence: {quality.get('confidence')}",
        f"Score gap: {quality.get('score_gap')}",
        f"Expected artifact: {quality.get('expected_artifact')}",
        f"Stop condition: {quality.get('stop_condition')}",
        "",
        "## Rationale",
        "",
        str(quality.get("selected_rationale", "")),
        "",
        "## Alternatives",
        "",
    ]
    for item in quality.get("alternatives", []) or []:
        lines.append(
            "- "
            f"{item.get('action_id')} score={item.get('score')} "
            f"selected={item.get('selected')} why_not={item.get('why_not_selected') or 'selected'}"
        )
    lines.extend(["", str(quality.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_decision_quality(
    options: CeoOpsOptions,
    *,
    action_board_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    decision = _decision_from_previous_next_action(_load_yaml_if_exists(root / "binding_action_result.yaml"), decision)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    action_board_result = action_board_result or run_ceo_action_board(diagnostic_options)
    quality = build_ceo_decision_quality(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        company_status=company_status,
        product_delta=product_delta,
        infra_delta=infra_delta,
        decision=decision,
        action_board=action_board_result["action_board"],
    )
    path = root / "decision_quality.yaml"
    report_path = root / "decision_quality.md"
    atomic_write_yaml(path, quality)
    atomic_write_text(report_path, render_ceo_decision_quality(quality))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision_quality": quality,
        "paths": {
            "decision_quality": path,
            "decision_quality_report": report_path,
            "action_board": action_board_result["paths"]["action_board"],
        },
    }


def _decision_from_previous_next_action(
    previous_action: dict[str, Any],
    default_decision: dict[str, Any],
) -> dict[str, Any]:
    next_actions = [
        "broaden_hypothesis_source" if str(item) == "broaden_product_candidate_source" else str(item)
        for item in previous_action.get("next_allowed_actions", []) or []
    ]
    if not next_actions:
        return default_decision
    if "patch_research_infra" in next_actions:
        return {
            "decision": "patch_research_infra",
            "rationale": "Previous CEO action requested a bounded research-infra recovery patch before more brute force.",
            "production_effect": "none",
        }
    if "broaden_hypothesis_source" in next_actions:
        return {
            "decision": "broaden_hypothesis_source",
            "rationale": "Previous CEO action requested broader hypothesis sources before repeating the same research family.",
            "production_effect": "none",
        }
    previous_decision = str(previous_action.get("decision", ""))
    previous_taken = str(previous_action.get("action_taken", ""))
    if (
        previous_decision == "run_champion_challenger"
        and "run_fresh_or_control_validation_for_promising_shadow_challengers" in next_actions
    ):
        return {
            "decision": "run_fresh_or_control_validation_for_promising_shadow_challengers",
            "rationale": "Previous champion/challenger action requested fresh/control validation before repeating comparison.",
            "production_effect": "none",
        }
    if previous_taken == "blocked_self_audit_intervention_required" and "resolve_ceo_self_audit_intervention" in next_actions:
        return {
            "decision": "resolve_ceo_self_audit_intervention",
            "rationale": "Previous CEO self-audit blocked repeated work and requires an intervention-routing action.",
            "production_effect": "none",
        }
    if previous_decision == "request_fresh_data" and "run_frozen_candidate_validation" in next_actions:
        return {
            "decision": "run_frozen_candidate_validation",
            "rationale": "Fresh data preflight is safe enough to compile frozen validation specs for the waiting shadow candidates.",
            "production_effect": "none",
        }
    if previous_decision == "run_frozen_candidate_validation" and "run_frozen_validation_executor" in next_actions:
        return {
            "decision": "run_frozen_validation_executor",
            "rationale": "Frozen validation specs are ready; run the guarded source-replay executor before any product language.",
            "production_effect": "none",
        }
    if previous_decision == "run_frozen_validation_executor" and "run_frozen_validation_rerun" in next_actions:
        return {
            "decision": "run_frozen_validation_rerun",
            "rationale": "Frozen source replay produced an executable adapter grid; rerun that adapter locally before requesting product language.",
            "production_effect": "none",
        }
    if previous_decision == "run_frozen_validation_rerun" and "run_fresh_withheld_validation_contract" in next_actions:
        return {
            "decision": "run_fresh_withheld_validation_contract",
            "rationale": "Frozen adapter rerun completed; freeze fresh/withheld snapshot rules and pass/fail gates before any validation executor.",
            "production_effect": "none",
        }
    if previous_decision == "run_fresh_withheld_validation_contract" and "repair_fresh_withheld_contract_inputs" in next_actions:
        return {
            "decision": "run_frozen_candidate_validation",
            "rationale": "Fresh/withheld contract is missing frozen validation inputs; rebuild the bounded frozen validation handoff before retrying the contract.",
            "production_effect": "none",
        }
    if previous_decision == "run_fresh_withheld_validation_contract" and "run_fresh_withheld_validation_executor" in next_actions:
        return {
            "decision": "run_fresh_withheld_validation_executor",
            "rationale": "Fresh/withheld validation contract is ready; run the manifest-gated executor or block if snapshot authority is missing.",
            "production_effect": "none",
        }
    if previous_decision == "run_fresh_withheld_validation_executor" and "run_fresh_withheld_snapshot_manifest" in next_actions:
        return {
            "decision": "run_fresh_withheld_snapshot_manifest",
            "rationale": "Fresh/withheld executor is blocked by missing snapshot authority; write the manifest draft before retrying.",
            "production_effect": "none",
        }
    if previous_decision == "request_fresh_data" and "import_or_curate_fresh_ohlcv_data" in next_actions:
        return {
            "decision": "import_or_curate_fresh_ohlcv_data",
            "rationale": "Fresh data preflight found local OHLCV coverage below the safe validation threshold.",
            "production_effect": "none",
        }
    if previous_decision != "run_fresh_or_control_validation_for_promising_shadow_challengers":
        return default_decision
    if "import_or_curate_fresh_ohlcv_data" in next_actions:
        return {
            "decision": "request_fresh_data",
            "rationale": "Fresh/control validation plan requires fresh or broader OHLCV data before product claims.",
            "production_effect": "none",
        }
    if "continue_governed_research" in next_actions:
        return {
            "decision": "continue_governed_research",
            "rationale": "Fresh/control validation plan routed the next step to governed control validation.",
            "production_effect": "none",
        }
    if "run_champion_challenger" in next_actions:
        return {
            "decision": "run_champion_challenger",
            "rationale": "Fresh/control validation plan found source gaps that require another champion/challenger source pass.",
            "production_effect": "none",
        }
    if "broaden_hypothesis_source" in next_actions:
        return {
            "decision": "broaden_hypothesis_source",
            "rationale": "Fresh/control validation plan found no runnable shadow candidates and needs broader sources.",
            "production_effect": "none",
        }
    return default_decision


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
        f"- Product language allowed: {product_delta.get('product_language_allowed')}",
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
        f"- Product evidence status: {product_delta.get('product_evidence_status')}",
        f"- Promotion ceiling: {product_delta.get('promotion_ceiling')}",
        f"- Fresh/frozen validation: {product_delta.get('fresh_or_frozen_validation_status')}",
        f"- Champion metric completeness: {product_delta.get('champion_metric_completeness')}",
        f"- Product language allowed: {product_delta.get('product_language_allowed')}",
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
    if kind == "run_fresh_or_control_validation_for_promising_shadow_challengers":
        return "Write a bounded fresh/control validation plan for promising shadow candidates before any product translation."
    if kind == "patch_research_infra":
        return "Patch recursive lane recovery or broaden recovery specs, run tests, then rerun one CEO block."
    if kind == "continue_governed_research":
        return "Run one more bounded governed CEO block and inspect the next decision packet."
    if kind == "request_fresh_data":
        return "Import or curate fresh OHLCV data before treating same-sample evidence as validation."
    if kind == "run_frozen_candidate_validation":
        return "Compile frozen validation specs from the prior plan and data preflight before any product language."
    if kind == "run_frozen_validation_executor":
        return "Replay frozen specs against existing source artifacts, then require fresh data before product language."
    if kind == "run_frozen_validation_rerun":
        return "Run the frozen adapter rerun grid locally, then build fresh/withheld snapshot rules and pass/fail thresholds before product language."
    if kind == "run_fresh_withheld_validation_contract":
        return "Write the fresh/withheld validation contract, then build the executor only from those frozen rules."
    if kind == "run_fresh_withheld_snapshot_manifest":
        return "Write the snapshot authority manifest draft; it still requires explicit fresh/withheld proof before validation can run."
    if kind == "run_fresh_withheld_validation_executor":
        return "Run the manifest-gated fresh/withheld executor; block if no valid snapshot manifest proves validation authority."
    if kind == "import_or_curate_fresh_ohlcv_data":
        return "Stop CEO automation at the manual data-import gate, then rerun fresh-data preflight after CSVs change."
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
    if not _should_write_binding_action_result(options):
        return {}
    dispatch_receipt_path = root / "dispatch_receipt.yaml"
    receipt_paths: dict[str, Path] = {}
    if (
        options.ceo_context in {"bound_dispatch", "guarded_direct"}
        and dispatch_receipt_path.exists()
        and "dispatch_receipt" not in action_result
    ):
        receipt = _load_yaml_if_exists(dispatch_receipt_path)
        receipt_reference_path = _resolve_report_ref_path(root, receipt.get("snapshot_path") or dispatch_receipt_path)
        if _receipt_can_back_binding_action(
            receipt=receipt,
            receipt_reference_path=receipt_reference_path,
            ceo_run_id=ceo_run_id,
            lab_run_id=lab_run_id,
            action_result=action_result,
            expected_dispatch_mode=options.ceo_context,
        ):
            action_result["dispatch_receipt"] = _dispatch_receipt_reference(receipt_reference_path)
    if options.ceo_context in {"bound_dispatch", "guarded_direct"} and "dispatch_receipt" not in action_result:
        preflight_gate = _load_yaml_if_exists(root / "preflight_gate.yaml")
        if (
            not preflight_gate
            and str(action_result.get("run_id", "")) == ceo_run_id
            and str(action_result.get("lab_run_id", "")) == lab_run_id
        ):
            preflight_result = run_ceo_preflight_gate(_with_ceo_context(options, context="preflight_refresh"))
            preflight_gate = preflight_result["preflight_gate"]
        action_contract_path = root / "action_contract.yaml"
        if not action_contract_path.exists():
            atomic_write_yaml(
                action_contract_path,
                build_ceo_action_contract(
                    ceo_run_id=ceo_run_id,
                    lab_run_id=lab_run_id,
                    decision=action_result,
                ),
            )
        if preflight_gate.get("safe_to_execute") is not True:
            if _binding_action_is_blocked_or_noop(action_result):
                receipt_paths = _write_ceo_dispatch_receipt(
                    options,
                    ceo_run_id,
                    lab_run_id,
                    action_result,
                    preflight_gate=preflight_gate,
                    approval_queue=_load_yaml_if_exists(root / "approval_queue.yaml"),
                    safe_to_dispatch=False,
                    reason=f"{options.ceo_context} action writer recorded blocked/no-op result after failed preflight",
                    dispatch_mode=options.ceo_context,
                )
                action_result["dispatch_receipt"] = _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"])
            else:
                raise ValueError("binding action requires a passing preflight gate before writing an immutable dispatch receipt")
        else:
            receipt_paths = _write_ceo_dispatch_receipt(
                options,
                ceo_run_id,
                lab_run_id,
                action_result,
                preflight_gate=preflight_gate,
                approval_queue=_load_yaml_if_exists(root / "approval_queue.yaml"),
                safe_to_dispatch=True,
                reason=f"{options.ceo_context} action writer required immutable dispatch receipt",
                dispatch_mode=options.ceo_context,
            )
            action_result["dispatch_receipt"] = _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"])
    action_result_path = root / "binding_action_result.yaml"
    ledger_path = _append_action_ledger(options, ceo_run_id, action_result)
    ledger_entries = _read_action_ledger(options, ceo_run_id)
    self_audit = build_ceo_self_audit(action_result, ledger_entries)
    self_audit_path = root / "ceo_self_audit.yaml"
    outcome_card = build_ceo_action_outcome_card(action_result, self_audit, ledger_entries)
    outcome_card_path = root / "action_outcome_card.yaml"
    outcome_card_report_path = root / "action_outcome_card.md"
    atomic_write_yaml(action_result_path, _json_safe(action_result))
    atomic_write_yaml(self_audit_path, self_audit)
    atomic_write_yaml(outcome_card_path, outcome_card)
    atomic_write_text(outcome_card_report_path, render_ceo_action_outcome_card(outcome_card))
    paths = {
        "binding_action_result": action_result_path,
        "action_ledger": ledger_path,
        "self_audit": self_audit_path,
        "action_outcome_card": outcome_card_path,
        "action_outcome_card_report": outcome_card_report_path,
    }
    paths.update(receipt_paths)
    return paths


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


def _fresh_control_required_tests(item: dict[str, Any], *, requires_fresh_data: bool) -> list[str]:
    role = str(item.get("product_role", ""))
    tests = [
        "freeze challenger rule shape before additional tuning",
        "rerun lag sensitivity on the frozen shape",
        "rerun cooldown sensitivity on the frozen shape",
        "confirm event diversity and symbol breadth",
    ]
    if role == "warning_blocker":
        tests.extend(
            [
                "measure avoided downside benefit versus missed upside cost",
                "review blocker false positives before product language",
            ]
        )
    else:
        tests.extend(
            [
                "compare forward relative returns versus core_signal_v0 baseline",
                "verify path quality does not come from same-cluster overfit",
            ]
        )
    if requires_fresh_data:
        tests.append("rerun the frozen shape after fresh OHLCV import or on a withheld split")
    return tests


def build_fresh_control_validation_plan(champion_results: dict[str, Any]) -> dict[str, Any]:
    work_items: list[dict[str, Any]] = []
    missing_source_ids: list[str] = []
    fresh_required_ids: list[str] = []
    candidate_decisions = {
        "shadow_challenger_promising_needs_fresh_validation",
        "needs_fresh_or_control_validation",
    }
    for result in champion_results.get("results", []) or []:
        decision = str(result.get("decision", ""))
        if decision not in candidate_decisions:
            continue
        belief_id = str(result.get("belief_id", ""))
        metric_sources = result.get("available_metric_sources", []) or []
        metric_summary = result.get("metric_summary", {}) or {}
        if not metric_summary and metric_sources:
            metric_summary = metric_sources[0].get("metric_summary", {}) or {}
        source_status = "matched" if metric_sources else "missing"
        if source_status == "missing":
            missing_source_ids.append(belief_id)
        requires_fresh_data = (
            decision == "shadow_challenger_promising_needs_fresh_validation"
            or metric_summary.get("champion_baseline_method") == "same_source_all_ranked_variants_proxy"
        )
        if requires_fresh_data:
            fresh_required_ids.append(belief_id)
        validation_route = "fresh_and_control_validation" if requires_fresh_data else "control_validation"
        work_items.append(
            {
                "priority": len(work_items) + 1,
                "belief_id": belief_id,
                "product_role": result.get("product_role"),
                "champion": result.get("champion", champion_results.get("champion", "core_signal_v0")),
                "challenger": result.get("challenger"),
                "champion_challenger_decision": decision,
                "validation_route": validation_route,
                "source_status": source_status,
                "source_count": len(metric_sources),
                "metric_summary": metric_summary,
                "evidence_sources": [
                    {
                        "loop_dir": source.get("loop_dir"),
                        "ranked": source.get("ranked"),
                        "bullish_evidence": source.get("bullish_evidence"),
                        "strict_referee": source.get("strict_referee"),
                    }
                    for source in metric_sources
                ],
                "required_tests": _fresh_control_required_tests(result, requires_fresh_data=requires_fresh_data),
                "promotion_ceiling_before_pass": "shadow_candidate",
                "validation_completed": False,
                "validation_result": "not_run",
                "candidate_status_after_plan": "shadow_only",
                "product_language_allowed": False,
                "production_effect": "none",
            }
        )
    if not work_items:
        status = "no_candidates"
        next_action = "broaden_hypothesis_source"
    elif missing_source_ids and len(missing_source_ids) == len(work_items):
        status = "blocked_missing_metric_sources"
        next_action = "run_champion_challenger"
    elif missing_source_ids:
        status = "validation_plan_ready_with_source_gaps"
        next_action = "run_champion_challenger"
    elif fresh_required_ids:
        status = "fresh_data_required"
        next_action = "import_or_curate_fresh_ohlcv_data"
    else:
        status = "control_validation_plan_ready"
        next_action = "continue_governed_research"
    return {
        "model": CEO_FRESH_CONTROL_VALIDATION_PLAN_MODEL,
        "generated_at": utc_now_iso(),
        "status": status,
        "candidate_count": len(work_items),
        "missing_source_count": len(missing_source_ids),
        "fresh_required_count": len(fresh_required_ids),
        "missing_source_ids": missing_source_ids,
        "fresh_required_ids": fresh_required_ids,
        "work_items": work_items,
        "next_action": next_action,
        "guardrail": "This plan does not validate or promote any product candidate by itself.",
        "validation_completed": False,
        "validation_result": "not_run",
        "candidate_status_after_plan": "shadow_only",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_fresh_control_validation_report(plan: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Fresh/Control Validation Plan",
        "",
        f"Generated: {plan.get('generated_at')}",
        f"Status: {plan.get('status')}",
        f"Candidate count: {plan.get('candidate_count')}",
        f"Missing source count: {plan.get('missing_source_count')}",
        f"Fresh-required count: {plan.get('fresh_required_count')}",
        f"Next action: {plan.get('next_action')}",
        f"Validation completed: {plan.get('validation_completed')}",
        f"Validation result: {plan.get('validation_result')}",
        f"Candidate status after plan: {plan.get('candidate_status_after_plan')}",
        f"Product language allowed: {plan.get('product_language_allowed')}",
        "",
        "## Work Items",
        "",
    ]
    for item in plan.get("work_items", []) or []:
        lines.append(
            "- "
            f"{item.get('belief_id')} "
            f"role={item.get('product_role')} "
            f"route={item.get('validation_route')} "
            f"sources={item.get('source_count')} "
            f"status={item.get('source_status')}"
        )
    if not plan.get("work_items"):
        lines.append("- No champion/challenger results require fresh/control validation.")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(plan.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _freshness_limit_days(timeframe: str) -> float:
    normalized = timeframe.lower()
    if normalized.endswith("h"):
        try:
            hours = float(normalized[:-1])
        except ValueError:
            hours = 24.0
        return max(2.0, hours / 24.0 * 6.0)
    if normalized.endswith("d"):
        try:
            days = float(normalized[:-1])
        except ValueError:
            days = 1.0
        return max(7.0, days * 4.0)
    if normalized.endswith("w"):
        try:
            weeks = float(normalized[:-1])
        except ValueError:
            weeks = 1.0
        return max(21.0, weeks * 14.0)
    return 14.0


def _timestamp_age_days(value: Any) -> float | None:
    if value is None:
        return None
    try:
        latest_dt = value.to_pydatetime()
    except AttributeError:
        latest_dt = value
    if not isinstance(latest_dt, datetime):
        return None
    if latest_dt.tzinfo is None:
        latest_dt = latest_dt.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - latest_dt.astimezone(timezone.utc)).total_seconds() / 86_400.0)


def build_fresh_data_preflight(options: CeoOpsOptions, *, ceo_run_id: str, lab_run_id: str) -> dict[str, Any]:
    universe = load_universe_config(options.config_path)
    timeframe_results: list[dict[str, Any]] = []
    for timeframe in options.timeframes:
        asset_results: list[dict[str, Any]] = []
        stale_limit = _freshness_limit_days(timeframe)
        active_count = 0
        stale_count = 0
        missing_count = 0
        load_failure_count = 0
        for asset in universe.assets:
            csv_path = find_symbol_csv(asset.symbol, options.data_dir, timeframe=timeframe)
            if csv_path is None:
                missing_count += 1
                asset_results.append(
                    {
                        "symbol": asset.symbol,
                        "status": "missing",
                        "path": "",
                        "row_count": 0,
                        "latest_date": "",
                        "age_days": None,
                    }
                )
                continue
            try:
                frame = load_ohlcv_csv(csv_path)
            except Exception as exc:
                load_failure_count += 1
                asset_results.append(
                    {
                        "symbol": asset.symbol,
                        "status": "load_failed",
                        "path": str(csv_path),
                        "row_count": 0,
                        "latest_date": "",
                        "age_days": None,
                        "error": str(exc),
                    }
                )
                continue
            row_count = int(len(frame))
            latest = frame.index.max() if row_count else None
            age_days = _timestamp_age_days(latest)
            stale = age_days is None or age_days > stale_limit
            status = "stale" if stale else "ready"
            if stale:
                stale_count += 1
            else:
                active_count += 1
            asset_results.append(
                {
                    "symbol": asset.symbol,
                    "status": status,
                    "path": str(csv_path),
                    "row_count": row_count,
                    "latest_date": str(latest) if latest is not None else "",
                    "data_sha256": _file_sha256(csv_path),
                    "age_days": round(age_days, 3) if age_days is not None else None,
                    "stale_limit_days": stale_limit,
                }
            )
        meets_min_active = active_count >= universe.min_active_members
        if active_count == 0:
            status = "no_ready_assets"
        elif not meets_min_active:
            status = "below_min_active_members"
        elif missing_count or stale_count or load_failure_count:
            status = "partial_ready"
        else:
            status = "ready"
        timeframe_results.append(
            {
                "timeframe": timeframe,
                "status": status,
                "asset_count": len(universe.assets),
                "active_count": active_count,
                "missing_count": missing_count,
                "stale_count": stale_count,
                "load_failure_count": load_failure_count,
                "min_active_members": universe.min_active_members,
                "meets_min_active_members": meets_min_active,
                "stale_limit_days": stale_limit,
                "assets": asset_results,
            }
        )
    overall_ready = all(item["status"] in {"ready", "partial_ready"} and item["meets_min_active_members"] for item in timeframe_results)
    if not timeframe_results:
        overall_status = "no_timeframes"
    elif overall_ready and all(item["status"] == "ready" for item in timeframe_results):
        overall_status = "ready"
    elif overall_ready:
        overall_status = "partial_ready"
    else:
        overall_status = "not_ready"
    return {
        "model": CEO_FRESH_DATA_PREFLIGHT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "config_path": str(options.config_path),
        "data_dir": str(options.data_dir),
        "universe": universe.name,
        "overall_status": overall_status,
        "safe_to_run_fresh_validation": overall_status in {"ready", "partial_ready"},
        "timeframes": timeframe_results,
        "next_action": "run_frozen_candidate_validation" if overall_status in {"ready", "partial_ready"} else "import_or_curate_fresh_ohlcv_data",
        "guardrail": "This preflight checks local data readiness only. It does not import data or validate any product candidate.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_fresh_data_preflight_report(preflight: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Fresh Data Preflight",
        "",
        f"Generated: {preflight.get('generated_at')}",
        f"Run: {preflight.get('run_id')}",
        f"Lab run: {preflight.get('lab_run_id')}",
        f"Universe: {preflight.get('universe')}",
        f"Data dir: {preflight.get('data_dir')}",
        f"Overall status: {preflight.get('overall_status')}",
        f"Safe to run fresh validation: {preflight.get('safe_to_run_fresh_validation')}",
        f"Next action: {preflight.get('next_action')}",
        "",
        "## Timeframes",
        "",
    ]
    for item in preflight.get("timeframes", []) or []:
        lines.append(
            "- "
            f"{item.get('timeframe')} status={item.get('status')} "
            f"active={item.get('active_count')}/{item.get('asset_count')} "
            f"missing={item.get('missing_count')} stale={item.get('stale_count')} "
            f"load_failed={item.get('load_failure_count')}"
        )
    if not preflight.get("timeframes"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(preflight.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_fresh_data_preflight(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="request_fresh_data",
        aliases={"fresh-data-preflight"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    preflight = build_fresh_data_preflight(options, ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
    path = root / "fresh_data_preflight.yaml"
    report_path = root / "fresh_data_preflight.md"
    atomic_write_yaml(path, preflight)
    atomic_write_text(report_path, render_fresh_data_preflight_report(preflight))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "request_fresh_data",
        "action_taken": "fresh_data_preflight",
        "command_executed": "riskflow ceo fresh-data-preflight",
        "status": preflight.get("overall_status"),
        "meaningful_progress": True,
        "inputs": {"config": options.config_path, "data_dir": options.data_dir},
        "outputs": {"preflight": path, "report": report_path},
        "next_allowed_actions": [preflight.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"preflight": path, "report": report_path})
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "preflight": preflight, "action_result": action_result, "paths": paths}


def _fresh_preflight_ready_context(preflight: dict[str, Any]) -> list[dict[str, Any]]:
    context: list[dict[str, Any]] = []
    for item in preflight.get("timeframes", []) or []:
        ready_symbols = [
            str(asset.get("symbol"))
            for asset in item.get("assets", []) or []
            if str(asset.get("status", "")) == "ready"
        ]
        context.append(
            {
                "timeframe": item.get("timeframe"),
                "status": item.get("status"),
                "ready_symbols": ready_symbols,
                "ready_symbol_count": len(ready_symbols),
                "active_count": item.get("active_count", 0),
                "asset_count": item.get("asset_count", 0),
                "missing_count": item.get("missing_count", 0),
                "stale_count": item.get("stale_count", 0),
                "load_failure_count": item.get("load_failure_count", 0),
                "min_active_members": item.get("min_active_members", 0),
                "meets_min_active_members": bool(item.get("meets_min_active_members")),
            }
        )
    return context


def _extract_frozen_execution_adapter(work_item: dict[str, Any]) -> dict[str, Any]:
    metric_summary = work_item.get("metric_summary", {}) or {}
    best_variant_id = str(metric_summary.get("best_variant_id", "") or "")
    checked_sources: list[str] = []
    if not best_variant_id:
        return {
            "adapter_status": "missing_best_variant_id",
            "adapter_type": None,
            "checked_sources": checked_sources,
            "production_effect": "none",
        }
    for source in work_item.get("evidence_sources", []) or []:
        if not isinstance(source, dict):
            continue
        variant_records_path = source.get("variant_records")
        if not variant_records_path:
            continue
        checked_sources.append(str(variant_records_path))
        for row in _csv_rows(variant_records_path):
            if row.get("variant_id") != best_variant_id:
                continue
            params: Any = row.get("params", "")
            try:
                params = json.loads(str(params)) if params else {}
            except json.JSONDecodeError:
                params = row.get("params", "")
            return {
                "adapter_status": "ready",
                "adapter_type": "grammar_search_variant_replay",
                "variant_id": best_variant_id,
                "family_id": row.get("family_id", ""),
                "detector": row.get("detector", ""),
                "direction": row.get("direction", ""),
                "timeframe": row.get("timeframe", ""),
                "benchmark": row.get("benchmark", ""),
                "params": params,
                "entry_lag_bars": row.get("entry_lag_bars", ""),
                "cooldown_bars": row.get("cooldown_bars", ""),
                "source_variant_records": str(variant_records_path),
                "production_effect": "none",
            }
    return {
        "adapter_status": "missing_variant_record",
        "adapter_type": "grammar_search_variant_replay",
        "variant_id": best_variant_id,
        "checked_sources": checked_sources,
        "production_effect": "none",
    }


def build_frozen_candidate_validation_plan(
    fresh_control_plan: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
    *,
    ceo_run_id: str,
    lab_run_id: str,
) -> dict[str, Any]:
    missing_inputs: list[str] = []
    if not fresh_control_plan:
        missing_inputs.append("fresh_control_validation_plan.yaml")
    if not fresh_data_preflight:
        missing_inputs.append("fresh_data_preflight.yaml")

    safe_preflight = bool(fresh_data_preflight.get("safe_to_run_fresh_validation"))
    data_context = _fresh_preflight_ready_context(fresh_data_preflight)
    eligible_timeframes = [
        str(item.get("timeframe"))
        for item in data_context
        if item.get("meets_min_active_members") and item.get("status") in {"ready", "partial_ready"}
    ]
    ready_symbols_by_timeframe = {
        str(item.get("timeframe")): item.get("ready_symbols", [])
        for item in data_context
        if item.get("meets_min_active_members")
    }
    work_items = list(fresh_control_plan.get("work_items", []) or []) if not missing_inputs else []
    specs: list[dict[str, Any]] = []
    for item in work_items:
        belief_id = str(item.get("belief_id", "unknown"))
        source_missing = str(item.get("source_status", "")) == "missing"
        spec_status = "blocked_missing_metric_source" if source_missing else "ready_for_execution"
        specs.append(
            {
                "spec_id": f"frozen_validation_{belief_id}",
                "belief_id": belief_id,
                "priority": item.get("priority"),
                "product_role": item.get("product_role"),
                "champion": item.get("champion", "core_signal_v0"),
                "challenger": item.get("challenger"),
                "validation_route": item.get("validation_route"),
                "status": spec_status,
                "eligible_timeframes": eligible_timeframes,
                "ready_symbols_by_timeframe": ready_symbols_by_timeframe,
                "frozen_shape_contract": {
                    "freeze_challenger_rule_shape": True,
                    "freeze_metric_interpretation": True,
                    "no_post_result_threshold_tuning": True,
                    "promotion_ceiling_before_pass": item.get("promotion_ceiling_before_pass", "shadow_candidate"),
                },
                "required_metrics": [
                    "forward_relative_return_vs_basket",
                    "hit_rate_forward_relative_return",
                    "median_max_drawdown",
                    "median_max_favorable_excursion",
                    "mfe_mae_ratio",
                    "symbol_breadth",
                    "event_diversity",
                ],
                "required_controls": item.get("required_controls", [])
                or [
                    "lag_sensitivity",
                    "cooldown_sensitivity",
                    "fresh_snapshot_or_withheld_split",
                    "event_cluster_deduplication",
                    "same_source_all_ranked_variants_proxy_check",
                ],
                "required_tests": item.get("required_tests", []),
                "evidence_sources": item.get("evidence_sources", []),
                "metric_summary_snapshot": item.get("metric_summary", {}),
                "execution_adapter": _extract_frozen_execution_adapter(item),
                "allowed_operations": [
                    "rerun the frozen challenger shape on eligible local data",
                    "run predeclared lag and cooldown controls",
                    "write validation artifacts for review",
                ],
                "disallowed_operations": [
                    "change production formulas",
                    "tune thresholds after inspecting validation results",
                    "claim product improvement before fresh/control metrics pass",
                ],
                "production_effect": "none",
            }
        )

    ready_spec_count = len([spec for spec in specs if spec.get("status") == "ready_for_execution"])
    if missing_inputs:
        status = "blocked_missing_inputs"
        next_action = (
            "run_fresh_or_control_validation_for_promising_shadow_challengers"
            if "fresh_control_validation_plan.yaml" in missing_inputs
            else "request_fresh_data"
        )
    elif not safe_preflight:
        status = "blocked_fresh_data_not_ready"
        next_action = fresh_data_preflight.get("next_action", "import_or_curate_fresh_ohlcv_data")
    elif not work_items:
        status = "no_candidates"
        next_action = "broaden_hypothesis_source"
    elif ready_spec_count == 0:
        status = "blocked_missing_metric_sources"
        next_action = "run_champion_challenger"
    elif ready_spec_count < len(specs):
        status = "frozen_validation_specs_ready_with_source_gaps"
        next_action = "run_frozen_validation_executor"
    else:
        status = "frozen_validation_specs_ready"
        next_action = "run_frozen_validation_executor"

    return {
        "model": CEO_FROZEN_CANDIDATE_VALIDATION_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "safe_to_execute_specs": status in {"frozen_validation_specs_ready", "frozen_validation_specs_ready_with_source_gaps"},
        "candidate_count": len(work_items),
        "spec_count": len(specs),
        "ready_spec_count": ready_spec_count,
        "missing_inputs": missing_inputs,
        "fresh_data_preflight_status": fresh_data_preflight.get("overall_status", ""),
        "data_readiness": data_context,
        "validation_specs": specs,
        "next_action": next_action,
        "execution_status": "scaffold_only",
        "guardrail": "This artifact freezes validation specs only. It does not promote candidates or change production formulas.",
        "validation_completed": False,
        "validation_result": "not_run",
        "candidate_status_after_plan": "shadow_only",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_frozen_candidate_validation_report(plan: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Frozen Candidate Validation Plan",
        "",
        f"Generated: {plan.get('generated_at')}",
        f"Status: {plan.get('status')}",
        f"Fresh data preflight status: {plan.get('fresh_data_preflight_status')}",
        f"Safe to execute specs: {plan.get('safe_to_execute_specs')}",
        f"Candidate count: {plan.get('candidate_count')}",
        f"Ready spec count: {plan.get('ready_spec_count')}/{plan.get('spec_count')}",
        f"Next action: {plan.get('next_action')}",
        "",
        "## Data Readiness",
        "",
    ]
    for item in plan.get("data_readiness", []) or []:
        lines.append(
            "- "
            f"{item.get('timeframe')} status={item.get('status')} "
            f"ready={item.get('ready_symbol_count')}/{item.get('asset_count')} "
            f"missing={item.get('missing_count')} stale={item.get('stale_count')} "
            f"load_failed={item.get('load_failure_count')}"
        )
    if not plan.get("data_readiness"):
        lines.append("- none")
    lines.extend(["", "## Specs", ""])
    for spec in plan.get("validation_specs", []) or []:
        lines.append(
            "- "
            f"{spec.get('spec_id')} belief={spec.get('belief_id')} "
            f"role={spec.get('product_role')} status={spec.get('status')} "
            f"timeframes={spec.get('eligible_timeframes')}"
        )
    if not plan.get("validation_specs"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(plan.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _csv_rows(path_value: Any) -> list[dict[str, str]]:
    path = Path(str(path_value or ""))
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _file_sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_report_ref_path(root: Path, value: Any) -> Path:
    path = Path(str(value or ""))
    if not str(value or ""):
        return path
    if path.is_absolute() or path.exists():
        return path
    root_relative = root / path
    if root_relative.exists():
        return root_relative
    return path


def _artifact_fingerprint_mismatches(
    *,
    owner: str,
    fingerprints: dict[str, Any],
    required_names: tuple[str, ...],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for name in required_names:
        item = fingerprints.get(name) if isinstance(fingerprints, dict) else None
        if not isinstance(item, dict):
            mismatches.append(
                {
                    "owner": owner,
                    "artifact": name,
                    "reason": "missing_recorded_fingerprint",
                    "expected_path": "",
                    "expected_sha256": "",
                    "actual_sha256": "",
                }
            )
            continue
        path_value = str(item.get("path", ""))
        path = Path(path_value) if path_value else Path()
        expected_exists = bool(item.get("exists"))
        expected_sha = str(item.get("sha256") or "")
        actual_exists = path.exists() if path_value else False
        actual_sha = _file_sha256(path) if actual_exists else ""
        if expected_exists != actual_exists:
            mismatches.append(
                {
                    "owner": owner,
                    "artifact": name,
                    "reason": "artifact_existence_changed",
                    "expected_path": path_value,
                    "expected_exists": expected_exists,
                    "actual_exists": actual_exists,
                    "expected_sha256": expected_sha,
                    "actual_sha256": actual_sha,
                }
            )
        elif expected_exists and not expected_sha:
            mismatches.append(
                {
                    "owner": owner,
                    "artifact": name,
                    "reason": "missing_expected_sha256",
                    "expected_path": path_value,
                    "expected_sha256": expected_sha,
                    "actual_sha256": actual_sha,
                }
            )
        elif expected_exists and expected_sha != actual_sha:
            mismatches.append(
                {
                    "owner": owner,
                    "artifact": name,
                    "reason": "sha256_changed",
                    "expected_path": path_value,
                    "expected_sha256": expected_sha,
                    "actual_sha256": actual_sha,
                }
            )
    return mismatches


def _active_asset_fingerprint_mismatches(snapshot_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for asset in snapshot_manifest.get("active_assets", []) or []:
        path_value = str(asset.get("path", "")).strip()
        expected_sha = str(asset.get("data_sha256", "")).strip()
        if not path_value or not expected_sha:
            continue
        path = Path(path_value)
        actual_exists = path.exists()
        actual_sha = _file_sha256(path) if actual_exists else ""
        if not actual_exists or actual_sha != expected_sha:
            mismatches.append(
                {
                    "owner": "fresh_withheld_snapshot_manifest",
                    "artifact": f"active_asset:{asset.get('symbol')}:{asset.get('timeframe')}",
                    "reason": "active_asset_fingerprint_mismatch",
                    "expected_path": path_value,
                    "expected_sha256": expected_sha,
                    "actual_exists": actual_exists,
                    "actual_sha256": actual_sha,
                }
            )
    return mismatches


def _nested_fingerprint_mismatches(
    *,
    owner: str,
    artifact: str,
    fingerprint: dict[str, Any],
) -> list[dict[str, Any]]:
    path_value = str(fingerprint.get("path", "")).strip()
    expected_sha = str(fingerprint.get("sha256", "")).strip()
    path = Path(path_value) if path_value else Path()
    actual_exists = path.exists() if path_value else False
    actual_sha = _file_sha256(path) if actual_exists else ""
    if not path_value or not expected_sha:
        return [
            {
                "owner": owner,
                "artifact": artifact,
                "reason": "missing_recorded_fingerprint",
                "expected_path": path_value,
                "expected_sha256": expected_sha,
                "actual_exists": actual_exists,
                "actual_sha256": actual_sha,
            }
        ]
    if not actual_exists or actual_sha != expected_sha:
        return [
            {
                "owner": owner,
                "artifact": artifact,
                "reason": "nested_fingerprint_mismatch",
                "expected_path": path_value,
                "expected_sha256": expected_sha,
                "actual_exists": actual_exists,
                "actual_sha256": actual_sha,
            }
        ]
    return []


def _column_truthy_count(frame: Any, column: str) -> int:
    if frame is None or not hasattr(frame, "columns") or column not in frame.columns:
        return 0
    return sum(1 for value in frame[column].tolist() if str(value).strip().lower() in {"true", "1", "yes", "y"})


def _unique_column_count(frame: Any, *columns: str) -> int:
    if frame is None or not hasattr(frame, "columns"):
        return 0
    for column in columns:
        if column in frame.columns:
            return int(frame[column].dropna().astype(str).nunique())
    return 0


def _max_numeric_column(frame: Any, *columns: str) -> int:
    if frame is None or not hasattr(frame, "columns"):
        return 0
    for column in columns:
        if column in frame.columns:
            values = [_safe_int(value) for value in frame[column].tolist()]
            values = [value for value in values if value is not None]
            return max(values) if values else 0
    return 0


def _column_present(frame: Any, *columns: str) -> bool:
    return bool(frame is not None and hasattr(frame, "columns") and any(column in frame.columns for column in columns))


def _max_float_column(frame: Any, *columns: str) -> float | None:
    if frame is None or not hasattr(frame, "columns"):
        return None
    for column in columns:
        if column in frame.columns:
            values: list[float] = []
            for value in frame[column].tolist():
                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    continue
            return max(values) if values else None
    return None


def _min_float_column(frame: Any, *columns: str) -> float | None:
    if frame is None or not hasattr(frame, "columns"):
        return None
    for column in columns:
        if column in frame.columns:
            values: list[float] = []
            for value in frame[column].tolist():
                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    continue
            return min(values) if values else None
    return None


def _column_pass_status(frame: Any, *columns: str) -> bool | None:
    if frame is None or not hasattr(frame, "columns"):
        return None
    pass_values = {"true", "1", "yes", "y", "pass", "passed", "ok", "accept", "accepted"}
    fail_values = {"false", "0", "no", "n", "fail", "failed", "blocked", "reject", "rejected"}
    observed = False
    for column in columns:
        if column not in frame.columns:
            continue
        for value in frame[column].tolist():
            normalized = str(value).strip().lower()
            if normalized in fail_values:
                return False
            if normalized in pass_values:
                observed = True
    return True if observed else None


def build_fresh_withheld_threshold_results(
    *,
    contract: dict[str, Any],
    records: Any = None,
    ranked: Any = None,
    strict: Any = None,
) -> dict[str, Any]:
    thresholds = contract.get("pass_fail_thresholds", {}) or {}
    min_symbols = _safe_int(thresholds.get("min_distinct_symbols")) or 0
    min_clusters = _safe_int(thresholds.get("min_event_clusters")) or 0
    strict_required = bool(thresholds.get("strict_referee_required", True))
    matched_null_required = bool(thresholds.get("matched_null_required"))
    directional_required = bool(thresholds.get("directional_forward_relative_return_required"))
    lag_required = bool(thresholds.get("lag_sensitivity_required"))
    cooldown_required = bool(thresholds.get("cooldown_sensitivity_required"))
    visual_required = bool(thresholds.get("visual_review_required_before_product_language"))
    matched_null_max_p_value = float(thresholds.get("matched_null_max_p_value", 0.05) or 0.05)
    min_forward_relative = float(
        thresholds.get("min_forward_relative_return", thresholds.get("min_median_forward_relative_return", 0.0)) or 0.0
    )
    strict_survivors = _column_truthy_count(strict, "strict_survivor")
    if strict_survivors == 0 and strict is not None and hasattr(strict, "__len__"):
        strict_survivors = int(len(strict)) if "strict_survivor" not in getattr(strict, "columns", []) else 0
    distinct_symbols = _unique_column_count(records, "symbol") or _max_numeric_column(ranked, "unique_symbols")
    event_clusters = _unique_column_count(records, "event_cluster_id", "event_cluster", "cluster_id") or _max_numeric_column(
        ranked,
        "unique_event_clusters",
        "event_clusters",
    )
    best_forward_relative = _max_float_column(
        ranked,
        "median_forward_relative_return_secondary",
        "median_forward_relative_return_primary",
        "mean_forward_relative_return_secondary",
        "mean_forward_relative_return_primary",
    )
    matched_null_status = _column_pass_status(strict, "matched_null_passed", "matched_null_status")
    matched_null_p_value = _min_float_column(strict, "matched_null_p_value")
    matched_null_observed = matched_null_status is not None or matched_null_p_value is not None or _column_present(
        strict,
        "matched_random_baseline_delta",
        "matched_null_delta",
    )
    if matched_null_status is not None:
        matched_null_passed = matched_null_status
    elif matched_null_p_value is not None:
        matched_null_passed = matched_null_p_value <= matched_null_max_p_value
    else:
        matched_null_passed = False
    directional_observed = best_forward_relative is not None
    directional_passed = bool(best_forward_relative is not None and best_forward_relative > min_forward_relative)
    lag_status = _column_pass_status(
        ranked,
        "lag_sensitivity_passed",
        "lag_sensitivity_status",
        "entry_lag_status",
    )
    cooldown_status = _column_pass_status(
        ranked,
        "cooldown_sensitivity_passed",
        "cooldown_sensitivity_status",
        "cooldown_status",
    )
    lag_observed = lag_status is not None or _column_present(ranked, "entry_lag_bars")
    cooldown_observed = cooldown_status is not None or _column_present(ranked, "cooldown_bars")
    lag_passed = bool(lag_status)
    cooldown_passed = bool(cooldown_status)
    checks = [
        {
            "name": "strict_referee_survivor",
            "required": strict_required,
            "observed": strict_survivors,
            "passed": (not strict_required) or strict_survivors > 0,
        },
        {
            "name": "min_distinct_symbols",
            "required": min_symbols,
            "observed": distinct_symbols,
            "passed": distinct_symbols >= min_symbols,
        },
        {
            "name": "min_event_clusters",
            "required": min_clusters,
            "observed": event_clusters,
            "passed": event_clusters >= min_clusters,
        },
        {
            "name": "matched_null_evaluated",
            "required": matched_null_required,
            "observed": {
                "evaluated": matched_null_observed,
                "min_p_value": matched_null_p_value,
                "max_allowed_p_value": matched_null_max_p_value,
                "explicit_status": matched_null_status,
            },
            "passed": (not matched_null_required) or bool(matched_null_passed),
        },
        {
            "name": "directional_forward_relative_return",
            "required": directional_required,
            "observed": {
                "best_forward_relative": best_forward_relative,
                "min_required": min_forward_relative,
                "evaluated": directional_observed,
            },
            "passed": (not directional_required) or directional_passed,
        },
        {
            "name": "lag_sensitivity_evaluated",
            "required": lag_required,
            "observed": {"evaluated": lag_observed, "explicit_status": lag_status},
            "passed": (not lag_required) or bool(lag_passed),
        },
        {
            "name": "cooldown_sensitivity_evaluated",
            "required": cooldown_required,
            "observed": {"evaluated": cooldown_observed, "explicit_status": cooldown_status},
            "passed": (not cooldown_required) or bool(cooldown_passed),
        },
        {
            "name": "visual_review_before_product_language",
            "required": visual_required,
            "observed": "product_language_blocked_by_executor",
            "passed": True,
        },
    ]
    passed = all(bool(check["passed"]) for check in checks)
    return {
        "status": "passed" if passed else "failed",
        "strict_survivor_rows": strict_survivors,
        "distinct_symbols": distinct_symbols,
        "event_clusters": event_clusters,
        "checks": checks,
        "product_language_allowed": False,
        "production_effect": "none",
    }


def _is_truthy_csv(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _source_replay_summary(source: dict[str, Any], best_variant_id: str) -> dict[str, Any]:
    strict_rows = _csv_rows(source.get("strict_referee"))
    variant_rows = _csv_rows(source.get("variant_records"))
    strict_for_best = [row for row in strict_rows if row.get("variant_id") == best_variant_id] if best_variant_id else []
    variant_for_best = [row for row in variant_rows if row.get("variant_id") == best_variant_id] if best_variant_id else []
    strict_survivors = [row for row in strict_rows if _is_truthy_csv(row.get("strict_survivor"))]
    best_strict_survivor = any(_is_truthy_csv(row.get("strict_survivor")) for row in strict_for_best)
    return {
        "source_status": "readable" if strict_rows or variant_rows else "missing_or_empty",
        "loop_dir": source.get("loop_dir"),
        "strict_referee": source.get("strict_referee"),
        "variant_records": source.get("variant_records"),
        "strict_referee_rows": len(strict_rows),
        "variant_record_rows": len(variant_rows),
        "strict_survivor_count": len(strict_survivors),
        "best_variant_id": best_variant_id,
        "best_variant_found_in_strict_referee": bool(strict_for_best),
        "best_variant_found_in_variant_records": bool(variant_for_best),
        "best_variant_strict_survivor": best_strict_survivor,
        "best_variant_event_count": len(variant_for_best),
        "best_variant_unique_symbols": len({row.get("symbol", "") for row in variant_for_best if row.get("symbol")}),
        "best_variant_unique_event_clusters": len(
            {row.get("event_cluster_id", "") for row in variant_for_best if row.get("event_cluster_id")}
        ),
        "production_effect": "none",
    }


def build_frozen_validation_execution_result(
    frozen_plan: dict[str, Any],
    *,
    ceo_run_id: str,
    lab_run_id: str,
) -> dict[str, Any]:
    specs = list(frozen_plan.get("validation_specs", []) or [])
    spec_results: list[dict[str, Any]] = []
    for spec in specs:
        status = str(spec.get("status", ""))
        best_variant_id = str((spec.get("metric_summary_snapshot", {}) or {}).get("best_variant_id", ""))
        source_summaries = [
            _source_replay_summary(source, best_variant_id)
            for source in spec.get("evidence_sources", []) or []
            if isinstance(source, dict)
        ]
        readable_sources = [item for item in source_summaries if item.get("source_status") == "readable"]
        best_source_survivors = [item for item in readable_sources if item.get("best_variant_strict_survivor")]
        if status != "ready_for_execution":
            result_status = "skipped_spec_not_ready"
            validation_result = "not_run"
        elif not readable_sources:
            result_status = "blocked_missing_executable_sources"
            validation_result = "blocked"
        elif best_source_survivors:
            result_status = "source_replay_passed_not_promotion_eligible"
            validation_result = "source_replay_passed"
        else:
            result_status = "source_replay_completed_no_strict_survivor"
            validation_result = "source_replay_failed"
        spec_results.append(
            {
                "spec_id": spec.get("spec_id"),
                "belief_id": spec.get("belief_id"),
                "product_role": spec.get("product_role"),
                "status": result_status,
                "validation_result": validation_result,
                "source_replay_scope": "existing_artifacts_only",
                "execution_adapter": spec.get("execution_adapter", {}),
                "source_count": len(source_summaries),
                "readable_source_count": len(readable_sources),
                "best_source_survivor_count": len(best_source_survivors),
                "source_summaries": source_summaries,
                "required_metrics": spec.get("required_metrics", []),
                "required_controls": spec.get("required_controls", []),
                "product_language_allowed": False,
                "production_effect": "none",
            }
        )
    executed = [item for item in spec_results if str(item.get("status", "")).startswith("source_replay_")]
    blocked = [item for item in spec_results if str(item.get("status", "")).startswith("blocked")]
    adapter_ready_count = len(
        [
            item
            for item in spec_results
            if (item.get("execution_adapter", {}) or {}).get("adapter_status") == "ready"
        ]
    )
    if not specs:
        status = "blocked_missing_frozen_specs"
        validation_result = "not_run"
        next_action = "riskflow ceo frozen-candidate-validation"
    elif executed and not blocked:
        status = "source_replay_completed"
        validation_result = "source_replay_only_not_promotion_eligible"
        next_action = "run_frozen_validation_rerun" if adapter_ready_count else "build_frozen_execution_adapter"
    elif executed:
        status = "source_replay_partial_with_source_gaps"
        validation_result = "source_replay_partial_not_promotion_eligible"
        next_action = "repair_missing_executable_sources"
    else:
        status = "blocked_missing_executable_sources"
        validation_result = "blocked"
        next_action = "repair_missing_executable_sources"
    return {
        "model": CEO_FROZEN_VALIDATION_EXECUTION_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "validation_completed": bool(executed),
        "validation_result": validation_result,
        "execution_scope": "source_artifact_replay_only",
        "spec_count": len(specs),
        "executed_spec_count": len(executed),
        "blocked_spec_count": len(blocked),
        "fresh_execution_contract": {
            "adapter_ready_count": adapter_ready_count,
            "adapter_required": True,
            "required_next_inputs": [
                "fresh_or_withheld_ohlcv_snapshot",
                "benchmark_or_basket_snapshot_matching_spec",
                "rerunnable_grammar_search_adapter",
                "predeclared pass/fail thresholds",
            ],
            "promotion_eligible_only_after": "fresh_or_withheld_validation_controls_pass",
            "production_effect": "none",
        },
        "spec_results": spec_results,
        "next_action": next_action,
        "guardrail": "Source replay checks existing artifacts only. It is not fresh validation and cannot authorize product language.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def build_frozen_validation_rerun_grid(execution_result: dict[str, Any]) -> dict[str, Any]:
    families: list[dict[str, Any]] = []
    candidate_specs: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    for spec_result in execution_result.get("spec_results", []) or []:
        adapter = spec_result.get("execution_adapter", {}) or {}
        if adapter.get("adapter_status") != "ready":
            continue
        family_id = str(adapter.get("family_id") or f"frozen_{_debt_slug(str(spec_result.get('belief_id', '')))}")
        if family_id not in seen_families:
            seen_families.add(family_id)
            params = adapter.get("params", {}) if isinstance(adapter.get("params"), dict) else {}
            parameter_grid = {str(key): [value] for key, value in params.items() if key != "timeframe"}
            families.append(
                {
                    "family_id": family_id,
                    "direction": adapter.get("direction", ""),
                    "detector": adapter.get("detector", ""),
                    "parameter_grid": parameter_grid,
                    "description": f"Frozen replay grid for {spec_result.get('belief_id')}",
                }
            )
        candidate_specs.append(
            {
                "spec_id": spec_result.get("spec_id"),
                "belief_id": spec_result.get("belief_id"),
                "family_id": family_id,
                "timeframe": adapter.get("timeframe", ""),
                "variant_id": adapter.get("variant_id", ""),
                "entry_lag_bars": adapter.get("entry_lag_bars", ""),
                "cooldown_bars": adapter.get("cooldown_bars", ""),
                "benchmark": adapter.get("benchmark", ""),
                "production_effect": "none",
            }
        )
    return {
        "model": GRAMMAR_SEARCH_MODEL,
        "generated_at": utc_now_iso(),
        "source_model": execution_result.get("model"),
        "status": "ready" if families else "no_adapter_ready_specs",
        "families": families,
        "candidate_specs": candidate_specs,
        "guardrail": "This grid is a rerun input only. Running it is not product promotion.",
        "production_effect": "none",
    }


def render_frozen_validation_execution_report(result: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Frozen Validation Execution Result",
        "",
        f"Generated: {result.get('generated_at')}",
        f"Status: {result.get('status')}",
        f"Execution scope: {result.get('execution_scope')}",
        f"Validation completed: {result.get('validation_completed')}",
        f"Validation result: {result.get('validation_result')}",
        f"Executed specs: {result.get('executed_spec_count')}/{result.get('spec_count')}",
        f"Next action: {result.get('next_action')}",
        "",
        "## Specs",
        "",
    ]
    for item in result.get("spec_results", []) or []:
        lines.append(
            "- "
            f"{item.get('spec_id')} belief={item.get('belief_id')} "
            f"status={item.get('status')} readable_sources={item.get('readable_source_count')}"
        )
    if not result.get("spec_results"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(result.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_frozen_validation_executor(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="run_frozen_validation_executor",
        aliases={"frozen-validation-executor"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / "frozen_candidate_validation_plan.yaml"
    frozen_plan = _load_yaml_if_exists(plan_path)
    result = build_frozen_validation_execution_result(frozen_plan, ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
    result_path = root / "frozen_validation_execution_result.yaml"
    report_path = root / "frozen_validation_execution_result.md"
    rerun_grid = build_frozen_validation_rerun_grid(result)
    rerun_grid_path = root / "frozen_validation_rerun_grid.yaml"
    atomic_write_yaml(result_path, result)
    atomic_write_text(report_path, render_frozen_validation_execution_report(result))
    atomic_write_yaml(rerun_grid_path, rerun_grid)
    if frozen_plan:
        updated_plan = dict(frozen_plan)
        updated_plan["execution_status"] = result.get("status")
        updated_plan["validation_completed"] = result.get("validation_completed")
        updated_plan["validation_result"] = result.get("validation_result")
        updated_plan["validation_execution_result"] = str(result_path)
        updated_plan["product_language_allowed"] = False
        atomic_write_yaml(plan_path, updated_plan)
        frozen_plan = updated_plan
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_frozen_validation_executor",
        "action_taken": "frozen_validation_source_replay",
        "command_executed": "riskflow ceo frozen-validation-executor",
        "status": result.get("status"),
        "meaningful_progress": bool(result.get("executed_spec_count")),
        "inputs": {"frozen_candidate_validation_plan": plan_path},
        "outputs": {"result": result_path, "report": report_path, "rerun_grid": rerun_grid_path},
        "next_allowed_actions": [result.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"result": result_path, "report": report_path, "rerun_grid": rerun_grid_path, "plan": plan_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "execution": result,
        "rerun_grid": rerun_grid,
        "plan": frozen_plan,
        "action_result": action_result,
        "paths": paths,
    }


def build_frozen_validation_rerun_result(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    grid: dict[str, Any],
    warnings: list[str],
    output_dir: Path,
    summary_rows: int = 0,
    record_rows: int = 0,
    ranked_rows: int = 0,
    strict_rows: int = 0,
    status: str | None = None,
    next_action: str | None = None,
) -> dict[str, Any]:
    families = list(grid.get("families", []) or [])
    candidate_specs = list(grid.get("candidate_specs", []) or [])
    payload_status = status or ("adapter_rerun_completed_not_promotion_eligible" if record_rows else "adapter_rerun_no_events")
    return {
        "model": CEO_FROZEN_VALIDATION_RERUN_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": payload_status,
        "execution_scope": "local_adapter_rerun_not_promotion_eligible",
        "family_count": len(families),
        "candidate_spec_count": len(candidate_specs),
        "summary_rows": summary_rows,
        "record_rows": record_rows,
        "ranked_rows": ranked_rows,
        "strict_referee_rows": strict_rows,
        "warnings": warnings,
        "output_dir": str(output_dir),
        "next_action": next_action
        or (
            "run_fresh_withheld_validation_contract"
            if payload_status == "adapter_rerun_completed_not_promotion_eligible"
            else "repair_frozen_validation_rerun_inputs"
        ),
        "guardrail": "Adapter rerun writes research artifacts only. It is not promotion-eligible without fresh/withheld snapshot rules and pass/fail thresholds.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_frozen_validation_rerun_report(result: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Frozen Validation Adapter Rerun",
        "",
        f"Generated: {result.get('generated_at')}",
        f"Status: {result.get('status')}",
        f"Execution scope: {result.get('execution_scope')}",
        f"Families: {result.get('family_count')}",
        f"Candidate specs: {result.get('candidate_spec_count')}",
        f"Records: {result.get('record_rows')}",
        f"Ranked rows: {result.get('ranked_rows')}",
        f"Strict referee rows: {result.get('strict_referee_rows')}",
        f"Next action: {result.get('next_action')}",
        "",
        "## Warnings",
        "",
    ]
    warnings = result.get("warnings", []) or []
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(result.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_frozen_validation_rerun(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="run_frozen_validation_rerun",
        aliases={"frozen-validation-rerun"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    grid_path = root / "frozen_validation_rerun_grid.yaml"
    grid = _load_yaml_if_exists(grid_path)
    output_dir = root / "frozen_validation_rerun"
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_plan_path = root / "frozen_candidate_validation_plan.yaml"
    frozen_plan = _load_yaml_if_exists(frozen_plan_path)
    warnings: list[str] = []
    if not grid:
        result = build_frozen_validation_rerun_result(
            ceo_run_id=ceo_run_id,
            lab_run_id=lab_run_id,
            grid={},
            warnings=["missing frozen_validation_rerun_grid.yaml"],
            output_dir=output_dir,
            status="blocked_missing_rerun_grid",
            next_action="riskflow ceo frozen-validation-executor",
        )
    elif not grid.get("families"):
        result = build_frozen_validation_rerun_result(
            ceo_run_id=ceo_run_id,
            lab_run_id=lab_run_id,
            grid=grid,
            warnings=["rerun grid has no adapter-ready families"],
            output_dir=output_dir,
            status="blocked_no_adapter_ready_specs",
            next_action="repair_frozen_execution_adapters",
        )
    else:
        candidate_specs = list(grid.get("candidate_specs", []) or [])
        timeframes = sorted({str(item.get("timeframe", "")).strip().lower() for item in candidate_specs if item.get("timeframe")})
        if not timeframes:
            timeframes = list(options.timeframes)
        entry_lags = {
            _safe_int(item.get("entry_lag_bars"))
            for item in candidate_specs
            if _safe_int(item.get("entry_lag_bars")) is not None
        }
        entry_lag = entry_lags.pop() if len(entry_lags) == 1 else options.entry_lag_bars
        if entry_lags:
            warnings.append("mixed entry lag values found; used options.entry_lag_bars")
        cooldowns = {
            str(item.get("timeframe", "")).strip().lower(): _safe_int(item.get("cooldown_bars"))
            for item in candidate_specs
            if item.get("timeframe") and _safe_int(item.get("cooldown_bars")) is not None
        }
        benchmarks = [str(item.get("benchmark", "")) for item in candidate_specs if item.get("benchmark")]
        benchmark_name = benchmarks[0] if benchmarks else "MEME_BASKET"
        universe, analysis, data_warnings = load_analysis_frames_by_timeframe(
            config_path=options.config_path,
            data_dir=options.data_dir,
            timeframes=tuple(timeframes),
        )
        warnings.extend(data_warnings)
        benchmark_name = benchmark_name or universe.benchmark.name
        if not any(frames for frames in analysis.values()):
            result = build_frozen_validation_rerun_result(
                ceo_run_id=ceo_run_id,
                lab_run_id=lab_run_id,
                grid=grid,
                warnings=warnings or ["no usable analysis frames"],
                output_dir=output_dir,
                status="blocked_no_analysis_frames",
                next_action="import_or_curate_fresh_ohlcv_data",
            )
        else:
            atomic_write_yaml(output_dir / "grid.yaml", grid)
            summary, records, ranked, family_summary, variants = run_grammar_search(
                analysis,
                grid_path=output_dir / "grid.yaml",
                timeframes=tuple(timeframes),
                benchmark_name=benchmark_name,
                min_sample_size=options.min_sample_size,
                entry_lag_bars=entry_lag,
                cooldown_bars_by_timeframe=cooldowns or None,
            )
            summary.to_csv(output_dir / "summary.csv", index=False)
            records.to_csv(output_dir / "records.csv", index=False)
            ranked.to_csv(output_dir / "ranked.csv", index=False)
            family_summary.to_csv(output_dir / "family_summary.csv", index=False)
            strict = strict_baseline_referee(
                ranked,
                records,
                analysis,
                entry_lag_bars=entry_lag,
                null_iterations=options.strict_null_iterations,
                random_seed=options.strict_random_seed,
            )
            strict.to_csv(output_dir / "strict_referee.csv", index=False)
            manifest = {
                "model": CEO_FROZEN_VALIDATION_RERUN_MODEL,
                "search_model": GRAMMAR_SEARCH_MODEL,
                "grid": str(grid_path),
                "timeframes": timeframes,
                "benchmark_name": benchmark_name,
                "entry_lag_bars": entry_lag,
                "cooldown_bars_by_timeframe": cooldowns,
                "variant_count": len(variants),
                "record_count": int(len(records)),
                "strict_referee_rows": int(len(strict)),
                "product_language_allowed": False,
                "production_effect": "none",
            }
            atomic_write_yaml(output_dir / "manifest.yaml", manifest)
            result = build_frozen_validation_rerun_result(
                ceo_run_id=ceo_run_id,
                lab_run_id=lab_run_id,
                grid=grid,
                warnings=warnings,
                output_dir=output_dir,
                summary_rows=int(len(summary)),
                record_rows=int(len(records)),
                ranked_rows=int(len(ranked)),
                strict_rows=int(len(strict)),
            )
    result_path = root / "frozen_validation_rerun_result.yaml"
    report_path = root / "frozen_validation_rerun_result.md"
    atomic_write_yaml(result_path, result)
    atomic_write_text(report_path, render_frozen_validation_rerun_report(result))
    if frozen_plan:
        updated_plan = dict(frozen_plan)
        updated_plan["validation_rerun_status"] = result.get("status")
        updated_plan["validation_rerun_result"] = str(result_path)
        updated_plan["validation_rerun_output_dir"] = str(output_dir)
        updated_plan["product_language_allowed"] = False
        atomic_write_yaml(frozen_plan_path, updated_plan)
        frozen_plan = updated_plan
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_frozen_validation_rerun",
        "action_taken": "frozen_validation_adapter_rerun",
        "command_executed": "riskflow ceo frozen-validation-rerun",
        "status": result.get("status"),
        "meaningful_progress": int(result.get("record_rows", 0) or 0) > 0,
        "inputs": {"rerun_grid": grid_path},
        "outputs": {"result": result_path, "report": report_path, "output_dir": output_dir},
        "next_allowed_actions": [result.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"result": result_path, "report": report_path, "output_dir": output_dir, "rerun_grid": grid_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "rerun": result,
        "plan": frozen_plan,
        "action_result": action_result,
        "paths": paths,
    }


def build_fresh_withheld_validation_contract(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    frozen_plan: dict[str, Any],
    rerun_result: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
) -> dict[str, Any]:
    missing_inputs: list[str] = []
    if not frozen_plan:
        missing_inputs.append("frozen_candidate_validation_plan.yaml")
    if not rerun_result:
        missing_inputs.append("frozen_validation_rerun_result.yaml")
    rerun_status = str(rerun_result.get("status", ""))
    safe_preflight = bool(fresh_data_preflight.get("safe_to_run_fresh_validation"))
    ready_specs = [
        spec
        for spec in frozen_plan.get("validation_specs", []) or []
        if spec.get("status") == "ready_for_execution"
    ]
    if missing_inputs:
        status = "blocked_missing_inputs"
        next_action = "repair_fresh_withheld_contract_inputs"
    elif not rerun_status.startswith("adapter_rerun_completed"):
        status = "blocked_adapter_rerun_not_completed"
        next_action = "run_frozen_validation_rerun"
    elif not safe_preflight:
        status = "blocked_missing_safe_snapshot_context"
        next_action = "request_fresh_data"
    else:
        status = "fresh_withheld_validation_contract_ready"
        next_action = "run_fresh_withheld_validation_executor"
    return {
        "model": CEO_FRESH_WITHHELD_VALIDATION_CONTRACT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "execution_scope": "contract_only_no_validation_execution",
        "missing_inputs": missing_inputs,
        "rerun_status": rerun_status,
        "safe_fresh_data_preflight": safe_preflight,
        "ready_spec_count": len(ready_specs),
        "candidate_spec_count": len(frozen_plan.get("validation_specs", []) or []),
        "snapshot_rules": [
            "freeze the exact grammar-search grid before reading fresh/withheld results",
            "use a fresh OHLCV snapshot or explicit withheld split that is not counted as source replay evidence",
            "lock benchmark/basket membership and symbol eligibility before execution",
            "record data directory, timeframes, active symbols, and benchmark snapshot in the executor manifest",
            "do not tune thresholds, cooldowns, entry lag, detectors, or params after seeing validation results",
        ],
        "pass_fail_thresholds": {
            "strict_referee_required": True,
            "matched_null_required": True,
            "min_distinct_symbols": 2,
            "min_event_clusters": 3,
            "directional_forward_relative_return_required": True,
            "lag_sensitivity_required": True,
            "cooldown_sensitivity_required": True,
            "visual_review_required_before_product_language": True,
        },
        "promotion_constraints": [
            "contract readiness is not validation",
            "executor output must remain shadow-only until a promotion proposal is approved by the user",
            "core_signal_v0, rankings, states, scores, alerts, Pine, and TradingView defaults remain unchanged",
        ],
        "source_artifacts": {
            "frozen_plan": "frozen_candidate_validation_plan.yaml" if frozen_plan else "",
            "rerun_result": "frozen_validation_rerun_result.yaml" if rerun_result else "",
            "fresh_data_preflight": "fresh_data_preflight.yaml" if fresh_data_preflight else "",
        },
        "next_action": next_action,
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_fresh_withheld_validation_contract(contract: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Fresh/Withheld Validation Contract",
        "",
        f"Generated: {contract.get('generated_at')}",
        f"Status: {contract.get('status')}",
        f"Execution scope: {contract.get('execution_scope')}",
        f"Ready specs: {contract.get('ready_spec_count')}/{contract.get('candidate_spec_count')}",
        f"Safe fresh data preflight: {contract.get('safe_fresh_data_preflight')}",
        f"Next action: {contract.get('next_action')}",
        "",
        "## Snapshot Rules",
        "",
    ]
    lines.extend(f"- {rule}" for rule in contract.get("snapshot_rules", []) or [])
    lines.extend(["", "## Pass/Fail Thresholds", ""])
    thresholds = contract.get("pass_fail_thresholds", {}) or {}
    lines.extend(f"- {key}: {value}" for key, value in thresholds.items())
    lines.extend(["", "## Promotion Constraints", ""])
    lines.extend(f"- {item}" for item in contract.get("promotion_constraints", []) or [])
    lines.extend(["", "## Artifact Fingerprints", ""])
    fingerprints = contract.get("artifact_fingerprints", {}) or {}
    if fingerprints:
        for name, item in fingerprints.items():
            lines.append(f"- {name}: exists={item.get('exists')} sha256={item.get('sha256') or 'missing'}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This contract freezes validation rules only. It does not execute validation or authorize product language.",
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_fresh_withheld_validation_contract(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="run_fresh_withheld_validation_contract",
        aliases={"fresh-withheld-validation-contract"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    frozen_plan = _load_yaml_if_exists(root / "frozen_candidate_validation_plan.yaml")
    rerun_result = _load_yaml_if_exists(root / "frozen_validation_rerun_result.yaml")
    fresh_data_preflight = _load_yaml_if_exists(root / "fresh_data_preflight.yaml")
    contract = build_fresh_withheld_validation_contract(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        frozen_plan=frozen_plan,
        rerun_result=rerun_result,
        fresh_data_preflight=fresh_data_preflight,
    )
    artifact_paths = {
        "frozen_plan": root / "frozen_candidate_validation_plan.yaml",
        "rerun_result": root / "frozen_validation_rerun_result.yaml",
        "fresh_data_preflight": root / "fresh_data_preflight.yaml",
        "rerun_grid": root / "frozen_validation_rerun_grid.yaml",
    }
    contract["artifact_fingerprints"] = {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": _file_sha256(path),
        }
        for name, path in artifact_paths.items()
    }
    contract_path = root / "fresh_withheld_validation_contract.yaml"
    report_path = root / "fresh_withheld_validation_contract.md"
    atomic_write_yaml(contract_path, contract)
    atomic_write_text(report_path, render_fresh_withheld_validation_contract(contract))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_fresh_withheld_validation_contract",
        "action_taken": "fresh_withheld_validation_contract",
        "command_executed": "riskflow ceo fresh-withheld-validation-contract",
        "status": contract.get("status"),
        "meaningful_progress": contract.get("status") == "fresh_withheld_validation_contract_ready",
        "inputs": {
            "frozen_plan": root / "frozen_candidate_validation_plan.yaml",
            "rerun_result": root / "frozen_validation_rerun_result.yaml",
            "fresh_data_preflight": root / "fresh_data_preflight.yaml",
        },
        "outputs": {"contract": contract_path, "report": report_path},
        "next_allowed_actions": [contract.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"contract": contract_path, "report": report_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "contract": contract,
        "action_result": action_result,
        "paths": paths,
    }


def build_fresh_withheld_snapshot_manifest(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    contract: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
) -> dict[str, Any]:
    contract_ready = contract.get("status") == "fresh_withheld_validation_contract_ready"
    safe_preflight = bool(fresh_data_preflight.get("safe_to_run_fresh_validation"))
    if not contract_ready:
        status = "blocked_contract_not_ready"
        next_action = "run_fresh_withheld_validation_contract"
    elif not safe_preflight:
        status = "blocked_missing_safe_preflight"
        next_action = "request_fresh_data"
    else:
        status = "draft_requires_manual_snapshot_authority"
        next_action = "declare_fresh_or_withheld_snapshot_authority"
    active_assets: list[dict[str, Any]] = []
    for timeframe in fresh_data_preflight.get("timeframes", []) or []:
        for asset in timeframe.get("assets", []) or []:
            if asset.get("status") == "ready":
                active_assets.append(
                    {
                        "timeframe": timeframe.get("timeframe", ""),
                        "symbol": asset.get("symbol", ""),
                        "path": asset.get("path", ""),
                        "latest_date": asset.get("latest_date", ""),
                        "row_count": asset.get("row_count", 0),
                        "data_sha256": asset.get("data_sha256", ""),
                    }
                )
    return {
        "model": CEO_FRESH_WITHHELD_SNAPSHOT_MANIFEST_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "snapshot_type": "",
        "snapshot_type_allowed_values": ["fresh", "withheld"],
        "snapshot_cutoff": "",
        "withheld_split_id": "",
        "source_evidence_cutoff": "",
        "overlap_with_source_evidence": None,
        "rule_shape_frozen": contract_ready,
        "contract_status": contract.get("status", ""),
        "fresh_data_preflight_status": fresh_data_preflight.get("overall_status", ""),
        "safe_fresh_data_preflight": safe_preflight,
        "active_asset_count": len(active_assets),
        "active_assets": active_assets,
        "required_manual_declarations": [
            "set snapshot_type to fresh or withheld",
            "set snapshot_cutoff for fresh snapshots or withheld_split_id for withheld splits",
            "set source_evidence_cutoff to the latest source-evidence date included in discovery/replay",
            "set overlap_with_source_evidence to false only after checking source evidence dates/splits",
            "confirm rule_shape_frozen remains true and contract fingerprints match",
            "record snapshot cutoff/import batch or withheld split definition",
        ],
        "next_action": next_action,
        "guardrail": "This manifest is snapshot authority, not validation. Leave fields unset when freshness or withheld status is not proven.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_fresh_withheld_snapshot_manifest(manifest: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Fresh/Withheld Snapshot Manifest",
        "",
        f"Generated: {manifest.get('generated_at')}",
        f"Status: {manifest.get('status')}",
        f"Snapshot type: {manifest.get('snapshot_type') or 'unset'}",
        f"Snapshot cutoff: {manifest.get('snapshot_cutoff') or 'unset'}",
        f"Withheld split id: {manifest.get('withheld_split_id') or 'unset'}",
        f"Source evidence cutoff: {manifest.get('source_evidence_cutoff') or 'unset'}",
        f"Overlap with source evidence: {manifest.get('overlap_with_source_evidence')}",
        f"Rule shape frozen: {manifest.get('rule_shape_frozen')}",
        f"Active assets: {manifest.get('active_asset_count')}",
        f"Next action: {manifest.get('next_action')}",
        "",
        "## Required Manual Declarations",
        "",
    ]
    lines.extend(f"- {item}" for item in manifest.get("required_manual_declarations", []) or [])
    lines.extend(["", "## Active Assets", ""])
    for asset in manifest.get("active_assets", []) or []:
        lines.append(
            "- "
            f"{asset.get('symbol')} {asset.get('timeframe')} "
            f"latest={asset.get('latest_date')} rows={asset.get('row_count')}"
        )
    if not manifest.get("active_assets"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(manifest.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_fresh_withheld_snapshot_manifest(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo fresh-withheld-snapshot-manifest requires --apply")
    _require_ceo_action_context(
        options,
        action="run_fresh_withheld_snapshot_manifest",
        aliases={"fresh-withheld-snapshot-manifest"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    contract = _load_yaml_if_exists(root / "fresh_withheld_validation_contract.yaml")
    fresh_data_preflight = _load_yaml_if_exists(root / "fresh_data_preflight.yaml")
    manifest = build_fresh_withheld_snapshot_manifest(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        contract=contract,
        fresh_data_preflight=fresh_data_preflight,
    )
    artifact_paths = {
        "contract": root / "fresh_withheld_validation_contract.yaml",
        "fresh_data_preflight": root / "fresh_data_preflight.yaml",
    }
    manifest["artifact_fingerprints"] = {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": _file_sha256(path),
        }
        for name, path in artifact_paths.items()
    }
    path = root / "fresh_withheld_snapshot_manifest.yaml"
    report_path = root / "fresh_withheld_snapshot_manifest.md"
    atomic_write_yaml(path, manifest)
    atomic_write_text(report_path, render_fresh_withheld_snapshot_manifest(manifest))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_fresh_withheld_snapshot_manifest",
        "action_taken": "fresh_withheld_snapshot_manifest",
        "command_executed": "riskflow ceo fresh-withheld-snapshot-manifest",
        "status": manifest.get("status"),
        "meaningful_progress": manifest.get("status") == "draft_requires_manual_snapshot_authority",
        "inputs": artifact_paths,
        "outputs": {"manifest": path, "report": report_path},
        "next_allowed_actions": [manifest.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"manifest": path, "report": report_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "manifest": manifest,
        "action_result": action_result,
        "paths": paths,
    }


def build_withheld_split_manifest(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    withheld_split_id: str,
    source_evidence_cutoff: str,
    description: str = "",
) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    if not withheld_split_id.strip():
        blocked_reasons.append("missing_withheld_split_id")
    if not source_evidence_cutoff.strip():
        blocked_reasons.append("missing_source_evidence_cutoff")
    elif _parse_iso_date(source_evidence_cutoff) is None:
        blocked_reasons.append("invalid_source_evidence_cutoff")
    return {
        "model": CEO_WITHHELD_SPLIT_MANIFEST_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "withheld_split_manifest_ready" if not blocked_reasons else "blocked_invalid_withheld_split_manifest",
        "withheld_split_id": withheld_split_id.strip(),
        "source_evidence_cutoff": source_evidence_cutoff.strip(),
        "description": description.strip(),
        "blocked_reasons": blocked_reasons,
        "guardrail": "This manifest declares withheld split authority only. It does not run validation or authorize product language.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_withheld_split_manifest(manifest: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Withheld Split Manifest",
        "",
        f"Generated: {manifest.get('generated_at')}",
        f"Status: {manifest.get('status')}",
        f"Withheld split id: {manifest.get('withheld_split_id') or 'unset'}",
        f"Source evidence cutoff: {manifest.get('source_evidence_cutoff') or 'unset'}",
        f"Description: {manifest.get('description') or 'none'}",
        "",
        "## Blocked Reasons",
        "",
    ]
    reasons = manifest.get("blocked_reasons", []) or []
    lines.extend(f"- {reason}" for reason in reasons) if reasons else lines.append("- none")
    lines.extend(["", "## Guardrail", "", str(manifest.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_withheld_split_manifest(
    options: CeoOpsOptions,
    *,
    withheld_split_id: str,
    source_evidence_cutoff: str,
    description: str = "",
) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo withheld-split-manifest requires --apply")
    _require_ceo_action_context(
        options,
        action="write_withheld_split_manifest",
        aliases={"withheld-split-manifest"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    manifest = build_withheld_split_manifest(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        withheld_split_id=withheld_split_id,
        source_evidence_cutoff=source_evidence_cutoff,
        description=description,
    )
    path = root / "withheld_split_manifest.yaml"
    report_path = root / "withheld_split_manifest.md"
    atomic_write_yaml(path, manifest)
    atomic_write_text(report_path, render_withheld_split_manifest(manifest))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "write_withheld_split_manifest",
        "action_taken": "withheld_split_manifest",
        "command_executed": "riskflow ceo withheld-split-manifest",
        "status": manifest.get("status"),
        "meaningful_progress": manifest.get("status") == "withheld_split_manifest_ready",
        "inputs": {
            "withheld_split_id": withheld_split_id,
            "source_evidence_cutoff": source_evidence_cutoff,
        },
        "outputs": {"manifest": path, "report": report_path},
        "next_allowed_actions": ["run_fresh_withheld_snapshot_manifest"],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"manifest": path, "report": report_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "manifest": manifest,
        "action_result": action_result,
        "paths": paths,
    }


def run_ceo_fresh_withheld_snapshot_declare(
    options: CeoOpsOptions,
    *,
    snapshot_type: str,
    source_evidence_cutoff: str,
    snapshot_cutoff: str = "",
    withheld_split_id: str = "",
    confirm_no_overlap: bool = False,
) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo fresh-withheld-snapshot-declare requires --apply")
    _require_ceo_action_context(
        options,
        action="declare_fresh_withheld_snapshot_authority",
        aliases={"fresh-withheld-snapshot-declare"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "fresh_withheld_snapshot_manifest.yaml"
    if not manifest_path.exists():
        run_ceo_fresh_withheld_snapshot_manifest(
            _with_ceo_context(options, context=options.ceo_context, action="fresh-withheld-snapshot-manifest")
        )
    manifest = _load_yaml_if_exists(manifest_path)
    normalized_type = snapshot_type.strip().lower()
    blocked_reasons: list[str] = []
    if normalized_type not in {"fresh", "withheld"}:
        blocked_reasons.append("snapshot_type_not_fresh_or_withheld")
    if normalized_type == "fresh" and not snapshot_cutoff:
        blocked_reasons.append("missing_snapshot_cutoff")
    if normalized_type == "withheld" and not withheld_split_id:
        blocked_reasons.append("missing_withheld_split_id")
    withheld_split_manifest: dict[str, Any] = {}
    if normalized_type == "withheld" and withheld_split_id:
        split_manifest_path = root / "withheld_split_manifest.yaml"
        split_manifest = _load_yaml_if_exists(split_manifest_path)
        if not split_manifest:
            blocked_reasons.append("missing_withheld_split_manifest")
        elif str(split_manifest.get("withheld_split_id", "")).strip() != withheld_split_id:
            blocked_reasons.append("withheld_split_id_not_in_manifest")
        elif split_manifest.get("status") != "withheld_split_manifest_ready":
            blocked_reasons.append("withheld_split_manifest_not_ready")
        elif str(split_manifest.get("source_evidence_cutoff", "")).strip() != source_evidence_cutoff:
            blocked_reasons.append("withheld_split_manifest_cutoff_mismatch")
        else:
            withheld_split_manifest = {
                "path": str(split_manifest_path),
                "exists": True,
                "sha256": _file_sha256(split_manifest_path),
                "withheld_split_id": withheld_split_id,
                "source_evidence_cutoff": source_evidence_cutoff,
            }
    if not source_evidence_cutoff:
        blocked_reasons.append("missing_source_evidence_cutoff")
    elif _parse_iso_date(source_evidence_cutoff) is None:
        blocked_reasons.append("invalid_source_evidence_cutoff")
    if not confirm_no_overlap:
        blocked_reasons.append("no_overlap_not_confirmed")
    if not manifest.get("rule_shape_frozen"):
        blocked_reasons.append("rule_shape_not_frozen")
    if not manifest.get("active_assets"):
        blocked_reasons.append("no_active_assets")
    blocked_reasons.extend(
        reason
        for reason in _fresh_snapshot_temporal_blockers(
            snapshot_type=normalized_type,
            source_evidence_cutoff=source_evidence_cutoff,
            snapshot_cutoff=snapshot_cutoff,
            active_assets=list(manifest.get("active_assets", []) or []),
        )
        if reason not in blocked_reasons
    )
    updated_manifest = dict(manifest)
    updated_manifest.update(
        {
            "snapshot_type": normalized_type,
            "snapshot_cutoff": snapshot_cutoff,
            "withheld_split_id": withheld_split_id,
            "withheld_split_manifest_valid": bool(withheld_split_manifest),
            "withheld_split_manifest": withheld_split_manifest,
            "source_evidence_cutoff": source_evidence_cutoff,
            "overlap_with_source_evidence": False if confirm_no_overlap else None,
            "status": "snapshot_authority_ready" if not blocked_reasons else "draft_requires_manual_snapshot_authority",
            "blocked_reasons": blocked_reasons,
            "next_action": "run_fresh_withheld_validation_executor"
            if not blocked_reasons
            else "repair_fresh_withheld_snapshot_manifest",
            "guardrail": (
                "Snapshot authority was declared from explicit CLI inputs. This does not execute validation or authorize product language."
            ),
            "product_language_allowed": False,
            "production_effect": "none",
        }
    )
    report_path = root / "fresh_withheld_snapshot_manifest.md"
    atomic_write_yaml(manifest_path, updated_manifest)
    atomic_write_text(report_path, render_fresh_withheld_snapshot_manifest(updated_manifest))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "declare_fresh_withheld_snapshot_authority",
        "action_taken": "fresh_withheld_snapshot_declaration",
        "command_executed": "riskflow ceo fresh-withheld-snapshot-declare",
        "status": updated_manifest.get("status"),
        "meaningful_progress": updated_manifest.get("status") == "snapshot_authority_ready",
        "inputs": {
            "snapshot_type": normalized_type,
            "snapshot_cutoff": snapshot_cutoff,
            "withheld_split_id": withheld_split_id,
            "source_evidence_cutoff": source_evidence_cutoff,
        },
        "outputs": {"manifest": manifest_path, "report": report_path},
        "next_allowed_actions": [updated_manifest.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"manifest": manifest_path, "report": report_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "manifest": updated_manifest,
        "action_result": action_result,
        "paths": paths,
    }


def build_fresh_withheld_validation_execution_result(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    contract: dict[str, Any],
    snapshot_manifest: dict[str, Any],
    artifact_fingerprint_mismatches: list[dict[str, Any]] | None = None,
    threshold_results: dict[str, Any] | None = None,
    output_dir: Path | None = None,
    summary_rows: int = 0,
    record_rows: int = 0,
    ranked_rows: int = 0,
    strict_rows: int = 0,
    warnings: list[str] | None = None,
    status: str | None = None,
    next_action: str | None = None,
) -> dict[str, Any]:
    contract_ready = contract.get("status") == "fresh_withheld_validation_contract_ready"
    snapshot_type = str(snapshot_manifest.get("snapshot_type", ""))
    snapshot_status = str(snapshot_manifest.get("status", ""))
    manifest_declares_valid = snapshot_type in {"fresh", "withheld"}
    overlap = bool(snapshot_manifest.get("overlap_with_source_evidence"))
    rule_shape_frozen = bool(snapshot_manifest.get("rule_shape_frozen"))
    manifest_status_ready = snapshot_status in {"ready", "snapshot_authority_ready"}
    active_assets = snapshot_manifest.get("active_assets", []) if snapshot_manifest else []
    has_active_assets = bool(active_assets)
    source_evidence_cutoff = str(snapshot_manifest.get("source_evidence_cutoff", "")).strip()
    snapshot_cutoff = str(snapshot_manifest.get("snapshot_cutoff", "")).strip()
    withheld_split_id = str(snapshot_manifest.get("withheld_split_id", "")).strip()
    has_snapshot_authority = (
        bool(snapshot_cutoff)
        if snapshot_type == "fresh"
        else bool(withheld_split_id) and snapshot_manifest.get("withheld_split_manifest_valid") is True
        if snapshot_type == "withheld"
        else False
    )
    has_source_evidence_boundary = bool(source_evidence_cutoff)
    temporal_blockers = _fresh_snapshot_temporal_blockers(
        snapshot_type=snapshot_type,
        source_evidence_cutoff=source_evidence_cutoff,
        snapshot_cutoff=snapshot_cutoff,
        active_assets=list(active_assets or []),
    )
    snapshot_valid = (
        bool(snapshot_manifest)
        and manifest_status_ready
        and manifest_declares_valid
        and has_active_assets
        and has_snapshot_authority
        and has_source_evidence_boundary
        and not overlap
        and rule_shape_frozen
        and not temporal_blockers
    )
    fingerprint_mismatches = artifact_fingerprint_mismatches or []
    threshold_results = threshold_results or {}
    thresholds_failed = threshold_results.get("status") == "failed"
    if status:
        resolved_status = status
        resolved_next_action = next_action or "repair_fresh_withheld_validation_execution_inputs"
    elif not contract_ready:
        resolved_status = "blocked_contract_not_ready"
        resolved_next_action = "run_fresh_withheld_validation_contract"
    elif not snapshot_manifest:
        resolved_status = "blocked_missing_snapshot_manifest"
        resolved_next_action = "run_fresh_withheld_snapshot_manifest"
    elif (
        not manifest_status_ready
        or not manifest_declares_valid
        or not has_active_assets
        or not has_snapshot_authority
        or not has_source_evidence_boundary
        or overlap
        or not rule_shape_frozen
        or temporal_blockers
    ):
        resolved_status = "blocked_invalid_snapshot_manifest"
        resolved_next_action = "repair_fresh_withheld_snapshot_manifest"
    elif fingerprint_mismatches:
        resolved_status = "blocked_artifact_fingerprint_mismatch"
        resolved_next_action = "repair_fresh_withheld_validation_artifact_lineage"
    elif thresholds_failed:
        resolved_status = "fresh_withheld_validation_failed_thresholds"
        resolved_next_action = "review_fresh_withheld_validation_results"
    else:
        resolved_status = "fresh_withheld_validation_executed_shadow_only"
        resolved_next_action = "review_fresh_withheld_validation_results"
    validation_completed = resolved_status == "fresh_withheld_validation_executed_shadow_only"
    validation_result = "not_run"
    if validation_completed:
        validation_result = (
            "fresh_withheld_validation_passed_shadow_only_not_promotion_eligible"
            if threshold_results.get("status") == "passed"
            else "fresh_withheld_execution_shadow_only_not_promotion_eligible"
        )
    elif resolved_status == "fresh_withheld_validation_failed_thresholds":
        validation_result = "fresh_withheld_validation_failed_thresholds"
    return {
        "model": CEO_FRESH_WITHHELD_VALIDATION_EXECUTION_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": resolved_status,
        "execution_scope": "manifest_gated_executor_no_production_promotion",
        "contract_status": contract.get("status", ""),
        "snapshot_manifest_status": snapshot_manifest.get("status", "") if snapshot_manifest else "",
        "snapshot_type": snapshot_type,
        "snapshot_cutoff": snapshot_cutoff,
        "withheld_split_id": withheld_split_id,
        "source_evidence_cutoff": source_evidence_cutoff,
        "active_asset_count": len(active_assets) if isinstance(active_assets, list) else 0,
        "snapshot_manifest_valid": snapshot_valid,
        "summary_rows": summary_rows,
        "record_rows": record_rows,
        "ranked_rows": ranked_rows,
        "strict_referee_rows": strict_rows,
        "threshold_results": threshold_results,
        "output_dir": str(output_dir) if output_dir else "",
        "validation_completed": validation_completed,
        "validation_result": validation_result,
        "warnings": warnings or [],
        "artifact_fingerprint_mismatches": fingerprint_mismatches,
        "blocked_reasons": [
            reason
            for reason, blocked in [
                ("contract_not_ready", not contract_ready),
                ("missing_snapshot_manifest", not snapshot_manifest),
                ("snapshot_manifest_status_not_ready", bool(snapshot_manifest) and not manifest_status_ready),
                ("snapshot_type_not_fresh_or_withheld", bool(snapshot_manifest) and not manifest_declares_valid),
                ("snapshot_manifest_has_no_active_assets", bool(snapshot_manifest) and not has_active_assets),
                ("missing_snapshot_authority_reference", bool(snapshot_manifest) and not has_snapshot_authority),
                (
                    "missing_withheld_split_manifest_authority",
                    bool(snapshot_manifest)
                    and snapshot_type == "withheld"
                    and bool(withheld_split_id)
                    and snapshot_manifest.get("withheld_split_manifest_valid") is not True,
                ),
                ("missing_source_evidence_boundary", bool(snapshot_manifest) and not has_source_evidence_boundary),
                ("snapshot_overlaps_source_evidence", bool(snapshot_manifest) and overlap),
                ("rule_shape_not_frozen", bool(snapshot_manifest) and not rule_shape_frozen),
                ("invalid_source_evidence_cutoff", "invalid_source_evidence_cutoff" in temporal_blockers),
                ("invalid_snapshot_cutoff", "invalid_snapshot_cutoff" in temporal_blockers),
                (
                    "snapshot_cutoff_not_after_source_evidence_cutoff",
                    "snapshot_cutoff_not_after_source_evidence_cutoff" in temporal_blockers,
                ),
                ("missing_active_asset_latest_dates", "missing_active_asset_latest_dates" in temporal_blockers),
                (
                    "active_assets_older_than_snapshot_cutoff",
                    "active_assets_older_than_snapshot_cutoff" in temporal_blockers,
                ),
                ("artifact_fingerprint_mismatch", bool(fingerprint_mismatches)),
                ("missing_frozen_validation_rerun_grid", resolved_status == "blocked_missing_rerun_grid"),
                ("no_analysis_frames", resolved_status == "blocked_no_analysis_frames"),
            ]
            if blocked
        ],
        "next_action": resolved_next_action,
        "guardrail": "This executor may only run against a valid fresh/withheld snapshot manifest and cannot promote product behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_fresh_withheld_validation_execution_report(result: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Fresh/Withheld Validation Execution Result",
        "",
        f"Generated: {result.get('generated_at')}",
        f"Status: {result.get('status')}",
        f"Execution scope: {result.get('execution_scope')}",
        f"Contract status: {result.get('contract_status')}",
        f"Snapshot type: {result.get('snapshot_type') or 'none'}",
        f"Snapshot cutoff: {result.get('snapshot_cutoff') or 'none'}",
        f"Withheld split id: {result.get('withheld_split_id') or 'none'}",
        f"Source evidence cutoff: {result.get('source_evidence_cutoff') or 'none'}",
        f"Active assets: {result.get('active_asset_count')}",
        f"Snapshot manifest valid: {result.get('snapshot_manifest_valid')}",
        f"Validation completed: {result.get('validation_completed')}",
        f"Validation result: {result.get('validation_result')}",
        f"Next action: {result.get('next_action')}",
        "",
        "## Blocked Reasons",
        "",
    ]
    reasons = result.get("blocked_reasons", []) or []
    lines.extend(f"- {reason}" for reason in reasons) if reasons else lines.append("- none")
    mismatches = result.get("artifact_fingerprint_mismatches", []) or []
    lines.extend(["", "## Artifact Fingerprint Mismatches", ""])
    if mismatches:
        for item in mismatches:
            lines.append(
                "- "
                f"{item.get('owner')}.{item.get('artifact')}: {item.get('reason')} "
                f"expected={item.get('expected_sha256') or 'missing'} "
                f"actual={item.get('actual_sha256') or 'missing'}"
            )
    else:
        lines.append("- none")
    thresholds = result.get("threshold_results", {}) or {}
    lines.extend(["", "## Threshold Results", ""])
    if thresholds:
        lines.append(f"- Status: {thresholds.get('status')}")
        lines.append(f"- Strict survivor rows: {thresholds.get('strict_survivor_rows')}")
        lines.append(f"- Distinct symbols: {thresholds.get('distinct_symbols')}")
        lines.append(f"- Event clusters: {thresholds.get('event_clusters')}")
        for item in thresholds.get("checks", []) or []:
            lines.append(
                "- "
                f"{item.get('name')}: observed={item.get('observed')} "
                f"required={item.get('required')} passed={item.get('passed')}"
            )
    else:
        lines.append("- not evaluated")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(result.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_fresh_withheld_validation_executor(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="run_fresh_withheld_validation_executor",
        aliases={"fresh-withheld-validation-executor"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    contract = _load_yaml_if_exists(root / "fresh_withheld_validation_contract.yaml")
    snapshot_manifest = _load_yaml_if_exists(root / "fresh_withheld_snapshot_manifest.yaml")
    artifact_fingerprint_mismatches: list[dict[str, Any]] = []
    if contract.get("status") == "fresh_withheld_validation_contract_ready" and snapshot_manifest:
        artifact_fingerprint_mismatches.extend(
            _artifact_fingerprint_mismatches(
                owner="fresh_withheld_validation_contract",
                fingerprints=contract.get("artifact_fingerprints", {}) or {},
                required_names=("frozen_plan", "rerun_result", "fresh_data_preflight", "rerun_grid"),
            )
        )
        artifact_fingerprint_mismatches.extend(
            _artifact_fingerprint_mismatches(
                owner="fresh_withheld_snapshot_manifest",
                fingerprints=snapshot_manifest.get("artifact_fingerprints", {}) or {},
                required_names=("contract", "fresh_data_preflight"),
            )
        )
        artifact_fingerprint_mismatches.extend(_active_asset_fingerprint_mismatches(snapshot_manifest))
        if snapshot_manifest.get("snapshot_type") == "withheld":
            artifact_fingerprint_mismatches.extend(
                _nested_fingerprint_mismatches(
                    owner="fresh_withheld_snapshot_manifest",
                    artifact="withheld_split_manifest",
                    fingerprint=snapshot_manifest.get("withheld_split_manifest", {}) or {},
                )
            )
    gate_result = build_fresh_withheld_validation_execution_result(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        contract=contract,
        snapshot_manifest=snapshot_manifest,
        artifact_fingerprint_mismatches=artifact_fingerprint_mismatches,
    )
    output_dir = root / "fresh_withheld_validation_execution"
    if gate_result.get("status") != "fresh_withheld_validation_executed_shadow_only":
        result = gate_result
    else:
        grid_path = root / "frozen_validation_rerun_grid.yaml"
        grid = _load_yaml_if_exists(grid_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        if not grid or not grid.get("families"):
            result = build_fresh_withheld_validation_execution_result(
                ceo_run_id=ceo_run_id,
                lab_run_id=lab_run_id,
                contract=contract,
                snapshot_manifest=snapshot_manifest,
                artifact_fingerprint_mismatches=artifact_fingerprint_mismatches,
                output_dir=output_dir,
                status="blocked_missing_rerun_grid",
                next_action="run_frozen_validation_executor",
            )
        else:
            candidate_specs = list(grid.get("candidate_specs", []) or [])
            manifest_timeframes = {
                str(item.get("timeframe", "")).strip().lower()
                for item in snapshot_manifest.get("active_assets", []) or []
                if item.get("timeframe")
            }
            grid_timeframes = {
                str(item.get("timeframe", "")).strip().lower()
                for item in candidate_specs
                if item.get("timeframe")
            }
            timeframes = sorted(manifest_timeframes or grid_timeframes) or list(options.timeframes)
            entry_lags = {
                _safe_int(item.get("entry_lag_bars"))
                for item in candidate_specs
                if _safe_int(item.get("entry_lag_bars")) is not None
            }
            entry_lag = entry_lags.pop() if len(entry_lags) == 1 else options.entry_lag_bars
            warnings: list[str] = []
            if entry_lags:
                warnings.append("mixed entry lag values found; used options.entry_lag_bars")
            cooldowns = {
                str(item.get("timeframe", "")).strip().lower(): _safe_int(item.get("cooldown_bars"))
                for item in candidate_specs
                if item.get("timeframe") and _safe_int(item.get("cooldown_bars")) is not None
            }
            benchmarks = [str(item.get("benchmark", "")) for item in candidate_specs if item.get("benchmark")]
            benchmark_name = benchmarks[0] if benchmarks else "MEME_BASKET"
            universe, analysis, data_warnings = load_analysis_frames_by_timeframe(
                config_path=options.config_path,
                data_dir=options.data_dir,
                timeframes=tuple(timeframes),
            )
            warnings.extend(data_warnings)
            benchmark_name = benchmark_name or universe.benchmark.name
            if not any(frames for frames in analysis.values()):
                result = build_fresh_withheld_validation_execution_result(
                    ceo_run_id=ceo_run_id,
                    lab_run_id=lab_run_id,
                    contract=contract,
                    snapshot_manifest=snapshot_manifest,
                    artifact_fingerprint_mismatches=artifact_fingerprint_mismatches,
                    output_dir=output_dir,
                    warnings=warnings or ["no usable analysis frames"],
                    status="blocked_no_analysis_frames",
                    next_action="import_or_curate_fresh_ohlcv_data",
                )
            else:
                atomic_write_yaml(output_dir / "grid.yaml", grid)
                summary, records, ranked, family_summary, variants = run_grammar_search(
                    analysis,
                    grid_path=output_dir / "grid.yaml",
                    timeframes=tuple(timeframes),
                    benchmark_name=benchmark_name,
                    min_sample_size=options.min_sample_size,
                    entry_lag_bars=entry_lag,
                    cooldown_bars_by_timeframe=cooldowns or None,
                )
                summary.to_csv(output_dir / "summary.csv", index=False)
                records.to_csv(output_dir / "records.csv", index=False)
                ranked.to_csv(output_dir / "ranked.csv", index=False)
                family_summary.to_csv(output_dir / "family_summary.csv", index=False)
                strict = strict_baseline_referee(
                    ranked,
                    records,
                    analysis,
                    entry_lag_bars=entry_lag,
                    null_iterations=options.strict_null_iterations,
                    random_seed=options.strict_random_seed,
                )
                strict.to_csv(output_dir / "strict_referee.csv", index=False)
                threshold_results = build_fresh_withheld_threshold_results(
                    contract=contract,
                    records=records,
                    ranked=ranked,
                    strict=strict,
                )
                manifest = {
                    "model": CEO_FRESH_WITHHELD_VALIDATION_EXECUTION_MODEL,
                    "search_model": GRAMMAR_SEARCH_MODEL,
                    "snapshot_manifest": str(root / "fresh_withheld_snapshot_manifest.yaml"),
                    "contract": str(root / "fresh_withheld_validation_contract.yaml"),
                    "grid": str(grid_path),
                    "timeframes": timeframes,
                    "benchmark_name": benchmark_name,
                    "entry_lag_bars": entry_lag,
                    "cooldown_bars_by_timeframe": cooldowns,
                    "variant_count": len(variants),
                    "record_count": int(len(records)),
                    "strict_referee_rows": int(len(strict)),
                    "threshold_status": threshold_results.get("status"),
                    "product_language_allowed": False,
                    "production_effect": "none",
                }
                atomic_write_yaml(output_dir / "manifest.yaml", manifest)
                result = build_fresh_withheld_validation_execution_result(
                    ceo_run_id=ceo_run_id,
                    lab_run_id=lab_run_id,
                    contract=contract,
                    snapshot_manifest=snapshot_manifest,
                    artifact_fingerprint_mismatches=artifact_fingerprint_mismatches,
                    threshold_results=threshold_results,
                    output_dir=output_dir,
                    summary_rows=int(len(summary)),
                    record_rows=int(len(records)),
                    ranked_rows=int(len(ranked)),
                    strict_rows=int(len(strict)),
                    warnings=warnings,
                )
    result_path = root / "fresh_withheld_validation_execution_result.yaml"
    report_path = root / "fresh_withheld_validation_execution_result.md"
    atomic_write_yaml(result_path, result)
    atomic_write_text(report_path, render_fresh_withheld_validation_execution_report(result))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_fresh_withheld_validation_executor",
        "action_taken": "fresh_withheld_validation_executor",
        "command_executed": "riskflow ceo fresh-withheld-validation-executor",
        "status": result.get("status"),
        "meaningful_progress": result.get("status")
        in {
            "fresh_withheld_validation_executed_shadow_only",
            "fresh_withheld_validation_failed_thresholds",
        },
        "inputs": {
            "contract": root / "fresh_withheld_validation_contract.yaml",
            "snapshot_manifest": root / "fresh_withheld_snapshot_manifest.yaml",
        },
        "outputs": {"result": result_path, "report": report_path},
        "next_allowed_actions": [result.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"result": result_path, "report": report_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "execution": result,
        "action_result": action_result,
        "paths": paths,
    }


def run_ceo_frozen_candidate_validation(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="run_frozen_candidate_validation",
        aliases={"frozen-candidate-validation"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    fresh_control_plan = _load_yaml_if_exists(root / "fresh_control_validation_plan.yaml")
    fresh_data_preflight = _load_yaml_if_exists(root / "fresh_data_preflight.yaml")
    plan = build_frozen_candidate_validation_plan(
        fresh_control_plan,
        fresh_data_preflight,
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    path = root / "frozen_candidate_validation_plan.yaml"
    report_path = root / "frozen_candidate_validation_plan.md"
    atomic_write_yaml(path, plan)
    atomic_write_text(report_path, render_frozen_candidate_validation_report(plan))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_frozen_candidate_validation",
        "action_taken": "frozen_candidate_validation_scaffold",
        "command_executed": "riskflow ceo frozen-candidate-validation",
        "status": plan.get("status"),
        "meaningful_progress": plan.get("status")
        in {"frozen_validation_specs_ready", "frozen_validation_specs_ready_with_source_gaps"},
        "inputs": {
            "fresh_control_validation_plan": root / "fresh_control_validation_plan.yaml",
            "fresh_data_preflight": root / "fresh_data_preflight.yaml",
        },
        "outputs": {"plan": path, "report": report_path},
        "next_allowed_actions": [plan.get("next_action")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"plan": path, "report": report_path})
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "plan": plan, "action_result": action_result, "paths": paths}


def render_ceo_research_infra_patch_report(plan: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Research-Infra Patch Plan",
        "",
        f"Generated: {plan.get('generated_at')}",
        f"Status: {plan.get('status')}",
        f"Generated recovery items: {plan.get('generated_count')}",
        f"Runtime queue additions: {plan.get('runtime_added')}",
        f"Audit passed: {plan.get('audit_passed')}",
        f"Next action: {plan.get('next_action')}",
        "",
        "## Input Artifacts",
        "",
    ]
    inputs = plan.get("input_artifacts", {}) or {}
    if inputs:
        lines.extend(f"- {key}: {value}" for key, value in inputs.items())
    else:
        lines.append("- none")
    lane_plan = plan.get("lane_recovery_plan", {}) or {}
    blocked = lane_plan.get("blocked_lanes", []) or []
    if blocked:
        lines.extend(["", "## Blocked Lanes", ""])
        lines.extend(f"- {item.get('belief_id')} lane={item.get('lane')} reason={item.get('reason')}" for item in blocked)
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(plan.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_patch_research_infra(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo patch-research-infra requires --apply")
    _require_ceo_action_context(
        options,
        action="patch_research_infra",
        aliases={"patch-research-infra"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    governance = _load_latest_governance(options, lab_run_id)
    director_dir = _latest_director_dir(options, lab_run_id)
    mart_path = director_dir / "evidence_mart.yaml" if director_dir else None
    belief_path = director_dir / "belief_graph.yaml" if director_dir else None
    lane_assignment_path = governance.get("paths", {}).get("lane_assignment")
    plan_path = root / "research_infra_patch_plan.yaml"
    report_path = root / "research_infra_patch_plan.md"
    queue_path = root / "research_infra_recovery_queue.yaml"
    audit_path = root / "research_infra_recovery_audit.yaml"
    grid_dir = options.lab_ops_runtime_root / lab_run_id / "generated_grids" / "director" / "ceo_recovery" / ceo_run_id
    runtime_queue_path = _lab_runtime_queue_path(options, lab_run_id)
    input_artifacts = {
        "evidence_mart": str(mart_path or ""),
        "belief_graph": str(belief_path or ""),
        "lane_assignment": str(lane_assignment_path or ""),
    }
    missing_inputs = [
        name
        for name, path in (
            ("evidence_mart", mart_path),
            ("belief_graph", belief_path),
            ("lane_assignment", lane_assignment_path),
        )
        if path is None or not Path(path).exists()
    ]
    lane_plan: dict[str, Any] = {}
    audit: dict[str, Any] = {}
    runtime_added = 0
    if missing_inputs:
        status = "blocked_missing_recovery_inputs"
        next_action = "broaden_hypothesis_source"
        guardrail = "CEO recovery cannot generate lane-recovery items without director mart, belief graph, and lane assignment inputs."
        atomic_write_yaml(
            queue_path,
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [],
                "production_effect": "none",
            },
        )
        audit = {
            "model": "riskflow_lab_director_audit_v0",
            "passed": False,
            "errors": [f"missing {item}" for item in missing_inputs],
            "production_effect": "none",
        }
        atomic_write_yaml(audit_path, audit)
    else:
        mart = load_yaml_file(Path(mart_path))
        belief_graph = load_yaml_file(Path(belief_path))
        lane_assignment = load_yaml_file(Path(lane_assignment_path))
        lane_plan = design_lane_recovery_experiments(
            mart,
            belief_graph,
            lane_assignment,
            output_queue_path=queue_path,
            generated_grid_dir=grid_dir,
            max_new_hypotheses=options.max_new_hypotheses,
            source_root=options.source_root,
            existing_hypothesis_ids=_existing_lab_hypothesis_ids(options, lab_run_id),
        )
        audit = audit_director_plan(lane_plan, source_root=options.source_root)
        atomic_write_yaml(queue_path, lane_plan.get("generated_queue", {}))
        atomic_write_yaml(audit_path, audit)
        if audit.get("passed"):
            runtime_added = append_queue_to_runtime(runtime_queue_path, lane_plan.get("generated_queue", {}))
        if not audit.get("passed"):
            status = "blocked_recovery_audit_failed"
            next_action = "broaden_hypothesis_source"
        elif runtime_added > 0:
            status = "recovery_queue_applied"
            next_action = "continue_governed_research"
        elif int(lane_plan.get("generated_count", 0) or 0) > 0:
            status = "recovery_queue_already_present"
            next_action = "continue_governed_research"
        else:
            status = "recovery_no_supported_specs"
            next_action = "broaden_hypothesis_source"
        guardrail = "This action can add governed recovery queue items, but it cannot change production formulas, rankings, states, or alerts."
    plan = {
        "model": CEO_RESEARCH_INFRA_PATCH_PLAN_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "input_artifacts": input_artifacts,
        "missing_inputs": missing_inputs,
        "generated_count": int(lane_plan.get("generated_count", 0) or 0),
        "runtime_added": runtime_added,
        "audit_passed": audit.get("passed") if audit else False,
        "lane_recovery_plan": lane_plan,
        "recovery_audit": audit,
        "next_action": next_action,
        "guardrail": guardrail,
        "product_language_allowed": False,
        "production_effect": "none",
    }
    atomic_write_yaml(plan_path, plan)
    atomic_write_text(report_path, render_ceo_research_infra_patch_report(plan))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "patch_research_infra",
        "action_taken": "research_infra_patch_plan",
        "command_executed": "riskflow ceo patch-research-infra",
        "status": status,
        "meaningful_progress": status in {"recovery_queue_applied", "recovery_queue_already_present"},
        "inputs": input_artifacts,
        "outputs": {"plan": plan_path, "report": report_path, "queue": queue_path, "audit": audit_path},
        "next_allowed_actions": [next_action],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"plan": plan_path, "report": report_path, "queue": queue_path, "audit": audit_path})
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "plan": plan, "paths": paths}


def render_ceo_hypothesis_source_broadening_report(plan: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Hypothesis Source Broadening Plan",
        "",
        f"Generated: {plan.get('generated_at')}",
        f"Status: {plan.get('status')}",
        f"Compiled hypotheses: {plan.get('compiled_count')}",
        f"Runtime queue additions: {plan.get('runtime_added')}",
        f"Next action: {plan.get('next_action')}",
        f"Product language allowed: {plan.get('product_language_allowed')}",
        "",
        "## Outputs",
        "",
    ]
    outputs = plan.get("output_artifacts", {}) or {}
    if outputs:
        lines.extend(f"- {key}: {value}" for key, value in outputs.items())
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(plan.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_broaden_hypothesis_source(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo broaden-hypothesis-source requires --apply")
    _require_ceo_action_context(
        options,
        action="broaden_hypothesis_source",
        aliases={"broaden-hypothesis-source"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    queue_path = root / "hypothesis_source_broadening_queue.yaml"
    report_path = root / "hypothesis_source_broadening_plan.md"
    plan_path = root / "hypothesis_source_broadening_plan.yaml"
    grid_dir = options.lab_ops_runtime_root / lab_run_id / "generated_grids" / "obsidian" / ceo_run_id
    runtime_queue_path = _lab_runtime_queue_path(options, lab_run_id)
    notes = load_obsidian_notes(options.source_root / "obsidian")
    graph = build_knowledge_graph(notes)
    compiled = compile_setup_journey_queue(
        graph,
        output_queue=queue_path,
        generated_grid_dir=grid_dir,
        include_research_grammar=True,
        research_grammar_dir=options.source_root / "research" / "grammar",
        max_research_families=options.max_new_hypotheses,
    )
    compiled_queue = compiled["queue"]
    runtime_added = append_queue_to_runtime(runtime_queue_path, compiled_queue)
    compiled_count = len(compiled_queue.get("queue", []) or [])
    if runtime_added > 0:
        status = "broadening_queue_applied"
        next_action = "continue_governed_research"
    elif compiled_count > 0:
        status = "broadening_queue_already_present"
        next_action = "continue_governed_research"
    else:
        status = "no_broadening_sources"
        next_action = "stop"
    plan = {
        "model": CEO_HYPOTHESIS_SOURCE_BROADENING_PLAN_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "obsidian_node_count": len(notes),
        "compiled_count": compiled_count,
        "runtime_added": runtime_added,
        "next_action": next_action,
        "output_artifacts": {
            "queue": str(compiled["queue_path"]),
            "generated_grid_dir": str(compiled["grid_dir"]),
            "runtime_queue": str(runtime_queue_path),
        },
        "guardrail": "This action broadens research sources into shadow research queue items only; it does not validate or promote product behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
    }
    atomic_write_yaml(plan_path, plan)
    atomic_write_text(report_path, render_ceo_hypothesis_source_broadening_report(plan))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "broaden_hypothesis_source",
        "action_taken": "hypothesis_source_broadening_plan",
        "command_executed": "riskflow ceo broaden-hypothesis-source",
        "status": status,
        "meaningful_progress": runtime_added > 0,
        "inputs": {"obsidian": options.source_root / "obsidian", "research_grammar": options.source_root / "research" / "grammar"},
        "outputs": {"plan": plan_path, "report": report_path, "queue": compiled["queue_path"], "generated_grid_dir": compiled["grid_dir"]},
        "next_allowed_actions": [next_action],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"plan": plan_path, "report": report_path, "queue": Path(compiled["queue_path"]), "generated_grid_dir": Path(compiled["grid_dir"])})
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "plan": plan, "paths": paths}


def run_ceo_champion_challenger(options: CeoOpsOptions, *, top_n: int | None = None) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo champion-challenger requires --apply")
    _require_ceo_action_context(
        options,
        action="run_champion_challenger",
        aliases={"champion-challenger"},
    )
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
    governance = _load_latest_governance(options, lab_run_id)
    action_plan = attach_metric_sources_to_action_plan(action_plan, governance, options, lab_run_id)
    atomic_write_yaml(action_plan_path, action_plan)
    results = build_champion_challenger_results(action_plan, top_n=top_n)
    results_path = root / "champion_challenger_results.yaml"
    report_path = root / "champion_challenger_results.md"
    visual_queue = build_champion_challenger_visual_review_queue(results)
    visual_queue_path = root / "champion_challenger_visual_review_queue.yaml"
    visual_queue_report_path = root / "champion_challenger_visual_review_queue.md"
    atomic_write_yaml(results_path, results)
    atomic_write_text(report_path, render_champion_challenger_report(results))
    atomic_write_yaml(visual_queue_path, visual_queue)
    atomic_write_text(visual_queue_report_path, render_champion_challenger_visual_review_queue(visual_queue))
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
    else:
        stale_gap_path = root / "capability_gap.yaml"
        if stale_gap_path.exists():
            stale_gap_path.unlink()
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
            "visual_review_queue": visual_queue_path,
            "visual_review_queue_report": visual_queue_report_path,
            "capability_gap": capability_gap_path,
        },
        "next_allowed_actions": [results.get("next_action", "broaden_hypothesis_source")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update(
        {
            "action_plan": action_plan_path,
            "results": results_path,
            "report": report_path,
            "visual_review_queue": visual_queue_path,
            "visual_review_queue_report": visual_queue_report_path,
        }
    )
    if capability_gap_path:
        paths["capability_gap"] = capability_gap_path
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "action_result": action_result,
        "results": results,
        "visual_review_queue": visual_queue,
        "paths": paths,
    }


def run_ceo_fresh_control_validation(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo fresh-control-validation requires --apply")
    _require_ceo_action_context(
        options,
        action="run_fresh_or_control_validation_for_promising_shadow_challengers",
        aliases={"fresh-control-validation"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    results_path = root / "champion_challenger_results.yaml"
    report_path = root / "fresh_control_validation_plan.md"
    plan_path = root / "fresh_control_validation_plan.yaml"
    champion_results = _load_yaml_if_exists(results_path)
    if not champion_results:
        plan = {
            "model": CEO_FRESH_CONTROL_VALIDATION_PLAN_MODEL,
            "generated_at": utc_now_iso(),
            "status": "blocked_missing_champion_challenger_results",
            "candidate_count": 0,
            "missing_source_count": 0,
            "fresh_required_count": 0,
            "missing_source_ids": [],
            "fresh_required_ids": [],
            "work_items": [],
            "next_action": "run_champion_challenger",
            "guardrail": "Run champion/challenger before fresh/control validation planning.",
            "production_effect": "none",
        }
    else:
        plan = build_fresh_control_validation_plan(champion_results)
    atomic_write_yaml(plan_path, plan)
    atomic_write_text(report_path, render_fresh_control_validation_report(plan))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "run_fresh_or_control_validation_for_promising_shadow_challengers",
        "action_taken": "fresh_control_validation_plan",
        "command_executed": "riskflow ceo fresh-control-validation",
        "status": plan.get("status"),
        "meaningful_progress": bool(plan.get("candidate_count")),
        "inputs": {"champion_challenger_results": results_path},
        "outputs": {"plan": plan_path, "report": report_path},
        "next_allowed_actions": [plan.get("next_action", "broaden_hypothesis_source")],
        "production_effect": "none",
    }
    paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    paths.update({"plan": plan_path, "report": report_path})
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "action_result": action_result,
        "plan": plan,
        "paths": paths,
    }


def _effective_operator_status(
    *,
    action_board: dict[str, Any],
    operator_brief: dict[str, Any],
    decision_quality: dict[str, Any],
) -> dict[str, Any]:
    action_board_status = str(action_board.get("status", ""))
    operator_brief_status = str(operator_brief.get("status", ""))
    runtime_authority = str(decision_quality.get("runtime_authority_status", ""))
    primary = action_board.get("primary_action", {}) or {}
    primary_can_execute = primary.get("can_execute_now") is True
    runtime_blocked = decision_quality.get("runtime_blocked") is True
    manual_gate_active = (
        action_board_status == "manual_gate_required"
        or operator_brief_status == "waiting_on_manual_gate"
        or runtime_authority == "manual_gate_required"
    )
    effective_runtime_action = str(
        decision_quality.get("effective_runtime_action")
        or ((action_board.get("primary_action", {}) or {}).get("action_id"))
        or ""
    )
    runtime_block_reason = str(decision_quality.get("runtime_block_reason") or "")
    if manual_gate_active:
        status = "manual_gate_required"
        runtime_blocked = True
        if not runtime_block_reason:
            runtime_block_reason = f"manual_gate_required:{effective_runtime_action or 'unknown_action'}"
    elif action_board_status == "bounded_action_available" and primary_can_execute:
        status = "bounded_action_available"
        runtime_blocked = False
    elif action_board_status in {"diagnostic_refresh_recommended", "implementation_repair_required", "no_action_available"}:
        status = action_board_status
        runtime_blocked = True
        if not runtime_block_reason:
            runtime_block_reason = f"{action_board_status}:{effective_runtime_action or 'unknown_action'}"
    elif runtime_blocked:
        status = "runtime_blocked"
    else:
        status = "unknown_or_diagnostic"
    return {
        "effective_operator_status": status,
        "manual_gate_active": manual_gate_active,
        "runtime_blocked": runtime_blocked,
        "runtime_block_reason": runtime_block_reason,
        "effective_runtime_action": effective_runtime_action,
        "runtime_authority": runtime_authority,
        "action_board_status": action_board_status,
        "operator_brief_status": operator_brief_status,
    }


def _ceo_reused_artifact_payload(
    result: dict[str, Any] | None,
    key: str,
    *,
    ceo_run_id: str,
    lab_run_id: str,
) -> dict[str, Any] | None:
    if not result:
        return None
    payload = result.get(key)
    if not isinstance(payload, dict):
        return None
    if str(payload.get("run_id", "")) != ceo_run_id:
        return None
    if str(payload.get("lab_run_id", "")) != lab_run_id:
        return None
    return payload


def run_ceo_status(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    status = build_company_status(options, ceo_run_id, lab_run_id)
    blocker_stack = _load_yaml_if_exists(root / "blocker_stack.yaml")
    incident_register = _load_yaml_if_exists(root / "operating_incident_register.yaml")
    dispatch_receipt = _load_yaml_if_exists(root / "dispatch_receipt.yaml")
    resumption_brief = _load_yaml_if_exists(root / "resumption_brief.yaml")
    repair_plan = _load_yaml_if_exists(root / "repair_plan.yaml")
    repair_apply = _load_yaml_if_exists(root / "repair_apply.yaml")
    action_board = _load_yaml_if_exists(root / "action_board.yaml")
    operator_brief = _load_yaml_if_exists(root / "operator_brief.yaml")
    decision_quality = _load_yaml_if_exists(root / "decision_quality.yaml")
    operator_step = _load_yaml_if_exists(root / "operator_step.yaml")
    replay = _load_yaml_if_exists(root / "ceo_replay.yaml")
    eval_suite = _load_yaml_if_exists(root / "ceo_eval_suite.yaml")
    artifact_coherence = _load_yaml_if_exists(root / "artifact_coherence.yaml")
    trace_grade = _load_yaml_if_exists(root / "trace_grade.yaml")
    approval_queue = _load_yaml_if_exists(root / "approval_queue.yaml")
    approval_status = _load_yaml_if_exists(root / "approval_status.yaml")
    role_queue = _load_yaml_if_exists(root / "role_task_queue.yaml")
    role_result_validation = _load_yaml_if_exists(root / "role_result_validation.yaml")
    action_board_primary = action_board.get("primary_action", {}) or {}
    eval_readiness = eval_suite.get("nine_nine_readiness", {}) or {}
    artifact_coherence_issues = artifact_coherence.get("issues", []) or []
    artifact_coherence_top_issue = artifact_coherence_issues[0] if artifact_coherence_issues else {}
    approval_top_pending_item = (approval_queue.get("pending_items", []) or [{}])[0]
    effective_operator = _effective_operator_status(
        action_board=action_board,
        operator_brief=operator_brief,
        decision_quality=decision_quality,
    )
    live_stop_requested = status.get("stop_requested") is True
    live_stop_handoff_command = f"PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id {ceo_run_id}"
    if live_stop_requested:
        effective_operator = {
            **effective_operator,
            "effective_operator_status": "manual_gate_required",
            "manual_gate_active": True,
            "runtime_blocked": True,
            "runtime_block_reason": "manual_gate_required:blocker:stop_requested",
            "effective_runtime_action": "blocker:stop_requested",
            "runtime_authority": "manual_gate_required",
        }
    resumption_next_command = str(resumption_brief.get("next_command", ""))
    if live_stop_requested:
        resumption_next_command = live_stop_handoff_command
        default_handoff_command = live_stop_handoff_command
        default_handoff_reason = "live_stop_requested"
        resumption_status = "blocked_stop_requested"
    else:
        default_handoff_command = resumption_next_command or f"PYTHONPATH=src python3 -m riskflow ceo resumption-brief --run-id {ceo_run_id}"
        default_handoff_reason = "resumption_brief" if resumption_next_command else "missing_resumption_brief"
        resumption_status = resumption_brief.get("resume_status", "missing_resumption_brief")
    status["operating_artifacts"] = {
        "live_stop_requested": live_stop_requested,
        "runtime_authority_override": "stop_requested" if live_stop_requested else "",
        "blocker_stack_status": blocker_stack.get("status", "missing_blocker_stack"),
        "top_blocker": blocker_stack.get("top_blocker", ""),
        "blocker_next_command": live_stop_handoff_command if live_stop_requested else blocker_stack.get("next_command", ""),
        "incident_register_status": incident_register.get("status", "missing_incident_register"),
        "operating_incident_count": int(incident_register.get("incident_count", 0) or 0),
        "dispatch_receipt_status": dispatch_receipt.get("status", "missing_dispatch_receipt"),
        "dispatch_safe_to_dispatch": False if live_stop_requested else dispatch_receipt.get("safe_to_dispatch", ""),
        "trace_grade_status": trace_grade.get("verdict", "missing_trace_grade"),
        "trace_grade_score": trace_grade.get("score", ""),
        "trace_grade_recommended_next_action": trace_grade.get("recommended_next_action", ""),
        "trace_grade_issues": trace_grade.get("issues", []),
        "trace_grade_manual_data_import_required": _trace_grade_manual_data_import_required(trace_grade),
        "replay_status": replay.get("status", "missing_replay"),
        "replay_issue_count": len(replay.get("issues", []) or []),
        "replay_dispatch_receipt_status": replay.get("dispatch_receipt_status", ""),
        "operator_step_status": replay.get("operator_step_status", operator_step.get("status", "missing_operator_step")),
        "operator_step_count": replay.get("operator_step_count", ""),
        "eval_suite_status": eval_suite.get("status", "missing_eval_suite"),
        "eval_suite_score": eval_suite.get("score", ""),
        "nine_nine_readiness": eval_readiness.get("status", ""),
        "nine_nine_blocking_case_count": len(eval_readiness.get("blocking_case_ids", []) or []),
        "nine_nine_advisory_case_count": len(eval_readiness.get("advisory_case_ids", []) or []),
        "artifact_coherence_status": artifact_coherence.get("status", "missing_artifact_coherence"),
        "artifact_coherence_issue_count": artifact_coherence.get("issue_count", ""),
        "artifact_coherence_top_issue_artifact": artifact_coherence_top_issue.get("artifact", ""),
        "artifact_coherence_top_issue_types": artifact_coherence_top_issue.get("issues", []),
        "artifact_coherence_top_issue_severity": artifact_coherence_top_issue.get(
            "severity",
            "unknown" if artifact_coherence_top_issue else "",
        ),
        "effective_operator_status": effective_operator["effective_operator_status"],
        "manual_gate_active": effective_operator["manual_gate_active"],
        "effective_operator_runtime_blocked": effective_operator["runtime_blocked"],
        "effective_operator_runtime_block_reason": effective_operator["runtime_block_reason"],
        "resumption_status": resumption_status,
        "resumption_next_command": resumption_next_command,
        "default_handoff_command": default_handoff_command,
        "default_handoff_reason": default_handoff_reason,
        "repair_plan_status": repair_plan.get("status", "missing_repair_plan"),
        "runnable_repair_count": int(repair_plan.get("runnable_repair_count", repair_plan.get("autonomous_repair_count", 0)) or 0),
        "diagnostic_refresh_count": int(repair_plan.get("diagnostic_refresh_count", 0) or 0),
        "top_repair": repair_plan.get("top_repair", ""),
        "top_repair_kind": repair_plan.get("top_repair_kind", ""),
        "repair_next_command": repair_plan.get("next_command", ""),
        "repair_apply_status": repair_apply.get("status", "missing_repair_apply"),
        "repair_apply_key": repair_apply.get("repair_key", ""),
        "repair_apply_executed": repair_apply.get("action_executed", ""),
        "repair_apply_closed": repair_apply.get("repair_closed", ""),
        "approval_queue_status": approval_queue.get("status", "missing_approval_queue"),
        "approval_pending_count": approval_queue.get("pending_count", approval_status.get("pending_count", "")),
        "approval_top_pending_id": approval_queue.get("top_pending_approval_id", ""),
        "approval_top_pending_kind": approval_top_pending_item.get("kind", ""),
        "approval_top_pending_reason": approval_top_pending_item.get("reason", ""),
        "approval_top_pending_source": approval_top_pending_item.get("source_artifact", ""),
        "approval_top_pending_required_user_decision": approval_top_pending_item.get("required_user_decision", ""),
        "approval_top_pending_authority": approval_top_pending_item.get("approval_authority", approval_top_pending_item.get("authority", "")),
        "approval_top_pending_fingerprint": approval_top_pending_item.get("approval_item_fingerprint", ""),
        "approval_record_command": approval_queue.get("top_pending_approval_record_command", ""),
        "approval_apply_command": approval_queue.get("top_pending_approval_apply_command", ""),
        "approval_status": approval_status.get("status", "missing_approval_status"),
        "action_board_status": "manual_gate_required" if live_stop_requested else action_board.get("status", "missing_action_board"),
        "action_board_primary_action": "blocker:stop_requested" if live_stop_requested else action_board_primary.get("action_id", ""),
        "action_board_primary_kind": "manual_gate" if live_stop_requested else action_board_primary.get("command_kind", ""),
        "action_board_command": live_stop_handoff_command if live_stop_requested else action_board_primary.get("command", ""),
        "decision_quality_status": decision_quality.get("status", "missing_decision_quality"),
        "decision_quality_effective_runtime_action": (
            "blocker:stop_requested" if live_stop_requested else decision_quality.get("effective_runtime_action", "")
        ),
        "decision_quality_effective_runtime_command_kind": (
            "manual_gate" if live_stop_requested else decision_quality.get("effective_runtime_command_kind", "")
        ),
        "decision_quality_effective_runtime_can_execute_now": (
            False if live_stop_requested else decision_quality.get("effective_runtime_can_execute_now", "")
        ),
        "decision_quality_runtime_blocked": True if live_stop_requested else decision_quality.get("runtime_blocked", ""),
        "decision_quality_runtime_block_reason": (
            "manual_gate_required:blocker:stop_requested"
            if live_stop_requested
            else decision_quality.get("runtime_block_reason", "")
        ),
        "decision_quality_selected_action": decision_quality.get("selected_action", ""),
        "decision_quality_selected_strategic_route_advisory": decision_quality.get("selected_strategic_route_advisory", ""),
        "decision_quality_confidence": decision_quality.get("confidence", ""),
        "decision_quality_runtime_authority": "manual_gate_required" if live_stop_requested else decision_quality.get("runtime_authority_status", ""),
        "decision_quality_executable_next_action": "blocker:stop_requested" if live_stop_requested else decision_quality.get("executable_next_action", ""),
        "decision_quality_executable_command_kind": "manual_gate" if live_stop_requested else decision_quality.get("executable_next_command_kind", ""),
        "decision_quality_runtime_authorized_strategic_route": decision_quality.get("runtime_authorized_strategic_route", ""),
        "decision_quality_runtime_authorized_route_source": decision_quality.get("runtime_authorized_route_source", ""),
        "decision_quality_executable_can_execute_now": False if live_stop_requested else decision_quality.get("executable_can_execute_now", ""),
        "decision_quality_selected_action_is_executable_now": (
            False if live_stop_requested else decision_quality.get("selected_action_is_executable_now", "")
        ),
        "decision_quality_selected_action_blocked_by": (
            "manual_gate_required:blocker:stop_requested"
            if live_stop_requested
            else decision_quality.get("selected_action_blocked_by", "")
        ),
        "operator_brief_status": "waiting_on_manual_gate" if live_stop_requested else operator_brief.get("status", "missing_operator_brief"),
        "operator_brief_summary": (
            "CEO mode is stopped at a manual gate. It should not take another autonomous action."
            if live_stop_requested
            else operator_brief.get("plain_english_summary", "")
        ),
        "operator_brief_next_action": live_stop_handoff_command if live_stop_requested else operator_brief.get("recommended_next_action", ""),
        "role_queue_status": role_queue.get("status", "missing_role_task_queue"),
        "role_pending_task_count": role_queue.get("pending_task_count", ""),
        "role_pending_manual_task_count": role_queue.get("pending_manual_task_count", ""),
        "role_pending_autonomous_task_count": role_queue.get("pending_autonomous_task_count", ""),
        "role_completed_task_count": role_queue.get("completed_task_count", ""),
        "role_blocked_task_count": role_queue.get("blocked_task_count", ""),
        "role_top_pending_task_id": role_queue.get("top_pending_task_id", ""),
        "role_top_pending_role_id": role_queue.get("top_pending_role_id", ""),
        "role_top_pending_packet_path": role_queue.get("top_pending_packet_path", ""),
        "role_top_pending_result_resolution_mode": role_queue.get("top_pending_result_resolution_mode", ""),
        "role_top_pending_requires_manual_gate": role_queue.get("top_pending_requires_manual_gate", ""),
        "role_top_pending_closure_command": role_queue.get("top_pending_closure_command", ""),
        "role_top_autonomous_pending_task_id": role_queue.get("top_autonomous_pending_task_id", ""),
        "role_top_autonomous_pending_role_id": role_queue.get("top_autonomous_pending_role_id", ""),
        "role_top_autonomous_pending_packet_path": role_queue.get("top_autonomous_pending_packet_path", ""),
        "role_top_autonomous_next_result_command": role_queue.get("top_autonomous_next_role_result_command", ""),
        "role_top_blocked_task_id": role_queue.get("top_blocked_task_id", ""),
        "role_top_blocked_role_id": role_queue.get("top_blocked_role_id", ""),
        "role_top_blocked_packet_path": role_queue.get("top_blocked_packet_path", ""),
        "role_top_blocked_result_resolution_mode": role_queue.get("top_blocked_result_resolution_mode", ""),
        "role_top_blocked_validation_status": role_queue.get("top_blocked_validation_status", ""),
        "role_top_blocked_closure_command": _ceo_role_queue_top_blocked_closure_command(
            ceo_run_id=ceo_run_id,
            role_queue=role_queue,
        ),
        "role_top_blocked_review_status": role_queue.get("top_blocked_review_status", ""),
        "role_top_blocked_result_path": role_queue.get("top_blocked_result_path", ""),
        "role_top_blocked_next_action": role_queue.get("top_blocked_next_action", ""),
        "role_top_blocked_finding": role_queue.get("top_blocked_finding", ""),
        "role_next_result_command": role_queue.get("next_role_result_command", ""),
        "role_result_validation_status": role_result_validation.get("status", "missing_role_result_validation"),
        "role_result_validation_task": role_result_validation.get("task_id", ""),
        "role_result_validation_issues": role_result_validation.get("issues", []),
        "production_effect": "none",
    }
    if root.exists():
        atomic_write_yaml(root / "company_status.yaml", status)
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "company_status": status}


def _trace_grade_manual_data_import_required(trace_grade: dict[str, Any]) -> bool | str:
    if not trace_grade:
        return ""
    criteria = trace_grade.get("criteria", {}) or {}
    if "manual_data_import_required" in criteria:
        return bool(criteria.get("manual_data_import_required"))
    issues = {str(item) for item in trace_grade.get("issues", []) or []}
    if "manual_data_import_required" in issues:
        return True
    return False


def build_ceo_flight_dashboard(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    company_status: dict[str, Any],
    heartbeat_status: dict[str, Any],
    trace_grade: dict[str, Any],
    action_result: dict[str, Any],
    outcome_card: dict[str, Any],
    action_contract: dict[str, Any],
    self_audit: dict[str, Any],
    product_delta: dict[str, Any],
) -> dict[str, Any]:
    next_allowed_actions = [str(item) for item in action_result.get("next_allowed_actions", []) or []]
    stop_requested = bool(heartbeat_status.get("stop_requested"))
    true_blocker = bool(heartbeat_status.get("true_blocker") or company_status.get("true_blocker"))
    production_gate = bool(heartbeat_status.get("production_promotion_required"))
    self_audit_intervention = bool(self_audit.get("intervention_required"))
    trace_fail = str(trace_grade.get("verdict", "")) == "fail"
    safe_to_continue = not any([stop_requested, true_blocker, production_gate, self_audit_intervention, trace_fail])
    blockers: list[str] = []
    if stop_requested:
        blockers.append("stop_requested")
    if true_blocker:
        blockers.append("true_blocker")
    if production_gate:
        blockers.append("production_promotion_gate")
    if self_audit_intervention:
        blockers.append("self_audit_intervention_required")
    if trace_fail:
        blockers.append("trace_grade_failed")
    if not next_allowed_actions and action_result:
        blockers.append("no_next_allowed_action")
    return {
        "model": CEO_FLIGHT_DASHBOARD_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "safe_to_continue": safe_to_continue,
        "safe_to_continue_scope": CEO_FLIGHT_SAFETY_SCOPE,
        "dispatch_authority": "not_granted_by_flight_dashboard",
        "runtime_authority_note": CEO_RUNTIME_AUTHORITY_NOTE,
        "blockers": blockers,
        "next_recommended_action": heartbeat_status.get("next_recommended_action"),
        "last_decision": action_result.get("decision") or heartbeat_status.get("last_decision"),
        "last_action": action_result.get("action_taken"),
        "last_status": action_result.get("status"),
        "next_allowed_actions": next_allowed_actions,
        "lab_status": {
            "status": company_status.get("lab_status", {}).get("status"),
            "stop_reason": company_status.get("lab_status", {}).get("stop_reason"),
            "completed_epochs": company_status.get("lab_status", {}).get("completed_epochs", 0),
            "completed_blocks": company_status.get("lab_status", {}).get("completed_blocks", 0),
        },
        "trace_grade": {
            "score": trace_grade.get("score"),
            "verdict": trace_grade.get("verdict"),
            "recommended_next_action": trace_grade.get("recommended_next_action"),
            "issues": trace_grade.get("issues", []),
            "manual_data_import_required": _trace_grade_manual_data_import_required(trace_grade),
            "manual_next_actions": trace_grade.get("manual_next_actions", []),
            "bounded_executor_next_actions": trace_grade.get("bounded_executor_next_actions", []),
            "product_evidence_status": trace_grade.get("product_evidence_status"),
            "product_language_allowed": trace_grade.get("product_language_allowed"),
        },
        "product_delta": {
            "candidate_count": product_delta.get("candidate_count", 0),
            "chart_facing_value_status": product_delta.get("chart_facing_value_status"),
            "product_evidence_status": product_delta.get("product_evidence_status"),
            "promotion_ceiling": product_delta.get("promotion_ceiling"),
            "product_language_allowed": product_delta.get("product_language_allowed"),
        },
        "outcome_card": {
            "progress_class": outcome_card.get("progress_class"),
            "failure_avoidance_status": (outcome_card.get("failure_avoidance", {}) or {}).get("status"),
            "memory_delta_required": outcome_card.get("memory_delta_required"),
            "product_evidence_level": outcome_card.get("product_evidence_level"),
            "next_product_gate": outcome_card.get("next_product_gate"),
        },
        "action_contract": {
            "decision": action_contract.get("decision"),
            "allowed_command": action_contract.get("allowed_command"),
            "allowed_scope": action_contract.get("allowed_scope"),
        },
        "self_audit": {
            "intervention_required": self_audit_intervention,
            "intervention": self_audit.get("intervention"),
            "recent_no_progress_count": self_audit.get("recent_no_progress_count", 0),
        },
        "production_effect": "none",
    }


def render_ceo_flight_dashboard(dashboard: dict[str, Any]) -> str:
    trace = dashboard.get("trace_grade", {}) or {}
    product = dashboard.get("product_delta", {}) or {}
    outcome = dashboard.get("outcome_card", {}) or {}
    contract = dashboard.get("action_contract", {}) or {}
    self_audit = dashboard.get("self_audit", {}) or {}
    lab = dashboard.get("lab_status", {}) or {}
    blockers = dashboard.get("blockers", []) or []
    lines = [
        "# Riskflow CEO Flight Dashboard",
        "",
        f"Generated: {dashboard.get('generated_at')}",
        f"Run: {dashboard.get('run_id')}",
        f"Lab run: {dashboard.get('lab_run_id')}",
        "",
        "## Continue Decision",
        "",
        f"- Safe to continue: {dashboard.get('safe_to_continue')}",
        f"- Safety scope: {dashboard.get('safe_to_continue_scope') or CEO_FLIGHT_SAFETY_SCOPE}",
        f"- Dispatch authority: {dashboard.get('dispatch_authority') or 'not_granted_by_flight_dashboard'}",
        f"- Runtime authority note: {dashboard.get('runtime_authority_note') or CEO_RUNTIME_AUTHORITY_NOTE}",
        f"- Blockers: {', '.join(blockers) if blockers else 'none'}",
        f"- Next recommended action: {dashboard.get('next_recommended_action')}",
        "",
        "## Last Action",
        "",
        f"- Decision: {dashboard.get('last_decision')}",
        f"- Action: {dashboard.get('last_action')}",
        f"- Status: {dashboard.get('last_status')}",
        f"- Next allowed actions: {dashboard.get('next_allowed_actions') or []}",
        "",
        "## Trace",
        "",
        f"- Verdict: {trace.get('verdict')}",
        f"- Score: {trace.get('score')}",
        f"- Recommended next action: {trace.get('recommended_next_action')}",
        f"- Manual data import required: {trace.get('manual_data_import_required')}",
        f"- Issues: {trace.get('issues') or []}",
        f"- Manual gates: {trace.get('manual_next_actions') or []}",
        f"- Bounded executors: {trace.get('bounded_executor_next_actions') or []}",
        "",
        "## Product Evidence",
        "",
        f"- Candidate count: {product.get('candidate_count')}",
        f"- Status: {product.get('chart_facing_value_status')}",
        f"- Evidence status: {product.get('product_evidence_status')}",
        f"- Promotion ceiling: {product.get('promotion_ceiling')}",
        f"- Product language allowed: {product.get('product_language_allowed')}",
        "",
        "## Outcome Card",
        "",
        f"- Progress class: {outcome.get('progress_class')}",
        f"- Failure avoidance: {outcome.get('failure_avoidance_status')}",
        f"- Memory delta required: {outcome.get('memory_delta_required')}",
        f"- Product evidence level: {outcome.get('product_evidence_level')}",
        f"- Next product gate: {outcome.get('next_product_gate')}",
        "",
        "## Contract And Self-Audit",
        "",
        f"- Contract decision: {contract.get('decision')}",
        f"- Allowed command: {contract.get('allowed_command') or 'none'}",
        f"- Allowed scope: {contract.get('allowed_scope')}",
        f"- Self-audit intervention required: {self_audit.get('intervention_required')}",
        f"- Recent no-progress count: {self_audit.get('recent_no_progress_count')}",
        "",
        "## Lab",
        "",
        f"- Status: {lab.get('status')}",
        f"- Stop reason: {lab.get('stop_reason') or 'none'}",
        f"- Completed epochs: {lab.get('completed_epochs')}",
        f"- Completed blocks: {lab.get('completed_blocks')}",
        "",
        "## Guardrail",
        "",
        "This dashboard summarizes CEO process state. It is not product validation.",
        "Production effect: none.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_flight_dashboard(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    company_status = run_ceo_status(options)["company_status"]
    heartbeat_status = run_ceo_heartbeat_status(options)["status"]
    trace_grade = run_ceo_trace_grade(options)["grade"]
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    action_result = _load_yaml_if_exists(root / "binding_action_result.yaml")
    outcome_card = _load_yaml_if_exists(root / "action_outcome_card.yaml")
    action_contract = _load_yaml_if_exists(root / "action_contract.yaml")
    self_audit = _load_yaml_if_exists(root / "ceo_self_audit.yaml")
    dashboard = build_ceo_flight_dashboard(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        company_status=company_status,
        heartbeat_status=heartbeat_status,
        trace_grade=trace_grade,
        action_result=action_result,
        outcome_card=outcome_card,
        action_contract=action_contract,
        self_audit=self_audit,
        product_delta=product_delta,
    )
    path = root / "ceo_flight_dashboard.yaml"
    report_path = root / "ceo_flight_dashboard.md"
    atomic_write_yaml(path, dashboard)
    atomic_write_text(report_path, render_ceo_flight_dashboard(dashboard))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "dashboard": dashboard,
        "paths": {"dashboard": path, "dashboard_report": report_path},
    }


def _portfolio_item(portfolio: dict[str, dict[str, Any]], belief_id: str) -> dict[str, Any]:
    key = belief_id or "unknown_candidate"
    item = portfolio.setdefault(
        key,
        {
            "belief_id": key,
            "product_role": "",
            "champion": "core_signal_v0",
            "challenger": "",
            "product_delta_status": "",
            "champion_challenger_decision": "",
            "visual_review_status": "",
            "fresh_control_route": "",
            "fresh_data_status": "",
            "frozen_spec_status": "",
            "evidence_gate": "shadow_candidate",
            "next_required_evidence": "run_champion_challenger",
            "production_effect": "none",
        },
    )
    return item


def _set_if_present(item: dict[str, Any], key: str, value: Any) -> None:
    if value not in (None, ""):
        item[key] = value


def build_ceo_candidate_portfolio(
    product_delta: dict[str, Any],
    champion_results: dict[str, Any],
    visual_queue: dict[str, Any],
    fresh_control_plan: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
    frozen_plan: dict[str, Any],
    fresh_withheld_contract: dict[str, Any],
    fresh_withheld_execution: dict[str, Any],
) -> list[dict[str, Any]]:
    portfolio: dict[str, dict[str, Any]] = {}
    for candidate in product_delta.get("candidates", []) or []:
        item = _portfolio_item(portfolio, str(candidate.get("belief_id", "")))
        _set_if_present(item, "product_role", candidate.get("product_role"))
        _set_if_present(item, "champion", candidate.get("champion"))
        _set_if_present(item, "challenger", candidate.get("challenger"))
        item["product_delta_status"] = candidate.get("comparison_status", "needs_champion_challenger")
    for result in champion_results.get("results", []) or []:
        item = _portfolio_item(portfolio, str(result.get("belief_id", "")))
        _set_if_present(item, "product_role", result.get("product_role"))
        _set_if_present(item, "champion", result.get("champion"))
        _set_if_present(item, "challenger", result.get("challenger"))
        item["champion_challenger_decision"] = result.get("decision", "")
        item["metric_checklist"] = result.get("product_metric_checklist", {})
        item["evidence_gate"] = "champion_challenger_complete"
        item["next_required_evidence"] = "run_fresh_control_validation"
    for review_item in visual_queue.get("items", []) or []:
        item = _portfolio_item(portfolio, str(review_item.get("belief_id", "")))
        _set_if_present(item, "product_role", review_item.get("product_role"))
        _set_if_present(item, "champion", review_item.get("champion"))
        _set_if_present(item, "challenger", review_item.get("challenger"))
        item["visual_review_status"] = review_item.get("review_status", "")
        item["visual_review_focus"] = review_item.get("review_focus", "")
    for work_item in fresh_control_plan.get("work_items", []) or []:
        item = _portfolio_item(portfolio, str(work_item.get("belief_id", "")))
        _set_if_present(item, "product_role", work_item.get("product_role"))
        _set_if_present(item, "champion", work_item.get("champion"))
        _set_if_present(item, "challenger", work_item.get("challenger"))
        item["fresh_control_route"] = work_item.get("validation_route", "")
        item["evidence_gate"] = "fresh_control_planned"
        item["next_required_evidence"] = "run_fresh_data_preflight"
    preflight_status = fresh_data_preflight.get("overall_status", "")
    if preflight_status:
        for item in portfolio.values():
            item["fresh_data_status"] = preflight_status
            if not fresh_data_preflight.get("safe_to_run_fresh_validation"):
                item["evidence_gate"] = "data_gate_blocked"
                item["next_required_evidence"] = "import_or_curate_fresh_ohlcv_data"
    for spec in frozen_plan.get("validation_specs", []) or []:
        item = _portfolio_item(portfolio, str(spec.get("belief_id", "")))
        _set_if_present(item, "product_role", spec.get("product_role"))
        _set_if_present(item, "champion", spec.get("champion"))
        _set_if_present(item, "challenger", spec.get("challenger"))
        item["frozen_spec_status"] = spec.get("status", "")
        item["evidence_gate"] = "frozen_spec_ready" if spec.get("status") == "ready_for_execution" else "frozen_spec_blocked"
        item["next_required_evidence"] = "run_frozen_validation_executor"
    if fresh_withheld_contract.get("status") == "fresh_withheld_validation_contract_ready":
        for item in portfolio.values():
            item["fresh_withheld_contract_status"] = fresh_withheld_contract.get("status")
            item["evidence_gate"] = "fresh_withheld_contract_ready"
            item["next_required_evidence"] = "run_fresh_withheld_validation_executor"
    if fresh_withheld_execution.get("validation_completed"):
        for item in portfolio.values():
            item["fresh_withheld_execution_status"] = fresh_withheld_execution.get("status")
            item["evidence_gate"] = "fresh_withheld_execution_complete"
            item["next_required_evidence"] = "review_shadow_validation_results_and_predeclare_passing_thresholds"
    return sorted(portfolio.values(), key=lambda item: (str(item.get("evidence_gate", "")), str(item.get("belief_id", ""))))


def build_ceo_capability_backlog(
    *,
    capability_gap: dict[str, Any],
    trace_grade: dict[str, Any],
    visual_queue: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
    frozen_plan: dict[str, Any],
    fresh_withheld_contract: dict[str, Any],
    fresh_withheld_execution: dict[str, Any],
) -> list[dict[str, Any]]:
    backlog: list[dict[str, Any]] = []
    if capability_gap:
        backlog.append(
            {
                "kind": "capability_gap",
                "priority": 1,
                "capability": capability_gap.get("missing_capability", "unknown"),
                "reason": capability_gap.get("reason", ""),
                "acceptance_criteria": capability_gap.get("acceptance_criteria", []),
                "production_effect": "none",
            }
        )
    for action in trace_grade.get("unsupported_next_actions", []) or []:
        backlog.append(
            {
                "kind": "unsupported_next_action",
                "priority": 2,
                "capability": f"{action}_executor",
                "reason": "trace grade found an unsupported next action",
                "acceptance_criteria": ["add dispatcher branch", "write binding action result", "add tests"],
                "production_effect": "none",
            }
        )
    if (visual_queue.get("status") or "") == "blocked_missing_metric_sources":
        backlog.append(
            {
                "kind": "visual_review_source_gap",
                "priority": 3,
                "capability": "visual_review_metric_source_resolver",
                "reason": "visual review queue cannot be used because metric sources are missing",
                "acceptance_criteria": ["attach source records", "preserve evidence paths", "keep production_effect none"],
                "production_effect": "none",
            }
        )
    if fresh_data_preflight and not fresh_data_preflight.get("safe_to_run_fresh_validation"):
        backlog.append(
            {
                "kind": "manual_data_gate",
                "priority": 4,
                "capability": "fresh_ohlcv_import_or_curation",
                "reason": "local data is not ready for fresh/control validation",
                "acceptance_criteria": ["import or curate CSVs", "rerun fresh-data-preflight", "do not change formulas"],
                "production_effect": "none",
            }
        )
    frozen_execution_status = str(frozen_plan.get("execution_status", ""))
    frozen_validation_result = str(frozen_plan.get("validation_result", ""))
    if fresh_withheld_contract.get("status") == "fresh_withheld_validation_contract_ready":
        backlog.append(
            {
                "kind": "fresh_withheld_snapshot_manifest_gap",
                "priority": 4,
                "capability": "fresh_withheld_snapshot_manifest",
                "reason": "fresh/withheld validation contract is ready, but executor requires an explicit snapshot manifest",
                "acceptance_criteria": [
                    "create fresh_withheld_snapshot_manifest.yaml",
                    "prove snapshot_type is fresh or withheld",
                    "prove snapshot does not overlap source evidence",
                    "rerun fresh-withheld-validation-executor",
                ],
                "production_effect": "none",
            }
        )
    if frozen_plan.get("status") == "frozen_validation_specs_ready" and not frozen_execution_status:
        backlog.append(
            {
                "kind": "executor_gap",
                "priority": 5,
                "capability": "frozen_validation_executor",
                "reason": "frozen candidate specs exist, but execution remains scaffold-only",
                "acceptance_criteria": ["consume frozen specs", "run declared metrics/controls", "write validation result"],
                "production_effect": "none",
            }
        )
    elif frozen_execution_status.startswith("source_replay") or frozen_validation_result.startswith("source_replay"):
        backlog.append(
            {
                "kind": "fresh_validation_executor_gap",
                "priority": 5,
                "capability": "fresh_or_withheld_validation_executor",
                "reason": "source replay exists, but promotion still requires fresh or withheld validation",
                "acceptance_criteria": [
                    "consume frozen execution adapters",
                    "rerun candidate shape on fresh or withheld data",
                    "write promotion-eligible validation result only if controls pass",
                ],
                "production_effect": "none",
            }
        )
    return sorted(backlog, key=lambda item: int(item.get("priority", 99)))


def build_ceo_operating_dashboard(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    flight_dashboard: dict[str, Any],
    product_delta: dict[str, Any],
    champion_results: dict[str, Any],
    visual_queue: dict[str, Any],
    fresh_control_plan: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
    frozen_plan: dict[str, Any],
    fresh_withheld_contract: dict[str, Any],
    fresh_withheld_execution: dict[str, Any],
    capability_gap: dict[str, Any],
    trace_grade: dict[str, Any],
    outcome_card: dict[str, Any],
    risk_register: dict[str, Any],
    knowledge_graph_delta: dict[str, Any],
    promotion_proposal: dict[str, Any],
    evidence_debt_register: dict[str, Any],
    approval_queue: dict[str, Any] | None = None,
    executive_kpis: dict[str, Any] | None = None,
    role_queue: dict[str, Any] | None = None,
) -> dict[str, Any]:
    approval_queue = approval_queue or {}
    executive_kpis = executive_kpis or {}
    role_queue = role_queue or {}
    candidate_portfolio = build_ceo_candidate_portfolio(
        product_delta,
        champion_results,
        visual_queue,
        fresh_control_plan,
        fresh_data_preflight,
        frozen_plan,
        fresh_withheld_contract,
        fresh_withheld_execution,
    )
    capability_backlog = build_ceo_capability_backlog(
        capability_gap=capability_gap,
        trace_grade=trace_grade,
        visual_queue=visual_queue,
        fresh_data_preflight=fresh_data_preflight,
        frozen_plan=frozen_plan,
        fresh_withheld_contract=fresh_withheld_contract,
        fresh_withheld_execution=fresh_withheld_execution,
    )
    loop_meltdown = trace_grade.get("loop_meltdown", {}) or {}
    risks = list(risk_register.get("risks", []) or [])
    if loop_meltdown.get("strategy_change_required"):
        risks.append(
            {
                "risk": "loop_meltdown",
                "severity": loop_meltdown.get("severity", "warn"),
                "mitigation": loop_meltdown.get("recommended_intervention"),
            }
        )
    if fresh_data_preflight and not fresh_data_preflight.get("safe_to_run_fresh_validation"):
        risks.append(
            {
                "risk": "fresh_data_not_ready",
                "severity": "high",
                "mitigation": "import_or_curate_fresh_ohlcv_data before fresh/control validation",
            }
        )
    return {
        "model": CEO_OPERATING_DASHBOARD_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "safe_to_continue": flight_dashboard.get("safe_to_continue"),
        "safe_to_continue_scope": flight_dashboard.get("safe_to_continue_scope") or CEO_FLIGHT_SAFETY_SCOPE,
        "dispatch_authority": "not_granted_by_operating_dashboard",
        "runtime_authority_note": flight_dashboard.get("runtime_authority_note") or CEO_RUNTIME_AUTHORITY_NOTE,
        "next_recommended_action": trace_grade.get("recommended_next_action")
        or flight_dashboard.get("next_recommended_action"),
        "candidate_portfolio_count": len(candidate_portfolio),
        "candidate_portfolio": candidate_portfolio,
        "capability_backlog_count": len(capability_backlog),
        "capability_backlog": capability_backlog,
        "data_gate": {
            "overall_status": fresh_data_preflight.get("overall_status", ""),
            "safe_to_run_fresh_validation": fresh_data_preflight.get("safe_to_run_fresh_validation"),
            "next_action": fresh_data_preflight.get("next_action", ""),
        },
        "validation_gate": {
            "fresh_withheld_contract_status": fresh_withheld_contract.get("status", ""),
            "fresh_withheld_execution_status": fresh_withheld_execution.get("status", ""),
            "fresh_withheld_validation_completed": fresh_withheld_execution.get("validation_completed"),
            "fresh_withheld_validation_result": fresh_withheld_execution.get("validation_result", ""),
        },
        "memory_portfolio": {
            "memory_delta_required": outcome_card.get("memory_delta_required"),
            "knowledge_graph_delta_status": knowledge_graph_delta.get("status", ""),
            "knowledge_graph_delta": knowledge_graph_delta,
        },
        "product_governance": {
            "promotion_proposal_status": promotion_proposal.get("status", ""),
            "approval_required": promotion_proposal.get("approval_required"),
            "pending_approval_count": approval_queue.get("pending_count", 0),
            "missing_evidence": promotion_proposal.get("missing_evidence", []),
            "evidence_debt_status": evidence_debt_register.get("status", ""),
            "evidence_debt_count": evidence_debt_register.get("debt_count", 0),
            "next_evidence_debt_action": evidence_debt_register.get("next_action", ""),
            "product_language_allowed": promotion_proposal.get("product_language_allowed", False),
        },
        "executive_kpis": executive_kpis.get("kpis", {}),
        "role_orchestration": {
            "status": role_queue.get("status", ""),
            "task_count": role_queue.get("task_count", 0),
            "pending_task_count": role_queue.get("pending_task_count", 0),
            "pending_manual_task_count": role_queue.get("pending_manual_task_count", 0),
            "pending_autonomous_task_count": role_queue.get("pending_autonomous_task_count", 0),
            "completed_task_count": role_queue.get("completed_task_count", 0),
            "blocked_task_count": role_queue.get("blocked_task_count", 0),
            "top_pending_task_id": role_queue.get("top_pending_task_id", ""),
            "top_blocked_task_id": role_queue.get("top_blocked_task_id", ""),
            "top_blocked_role_id": role_queue.get("top_blocked_role_id", ""),
            "top_blocked_review_status": role_queue.get("top_blocked_review_status", ""),
            "top_blocked_result_path": role_queue.get("top_blocked_result_path", ""),
            "top_blocked_next_action": role_queue.get("top_blocked_next_action", ""),
            "top_blocked_finding": role_queue.get("top_blocked_finding", ""),
            "next_action": role_queue.get("next_action", ""),
        },
        "risk_portfolio": risks,
        "trace": {
            "score": trace_grade.get("score"),
            "verdict": trace_grade.get("verdict"),
            "recommended_next_action": trace_grade.get("recommended_next_action", ""),
            "manual_data_import_required": _trace_grade_manual_data_import_required(trace_grade),
            "issues": trace_grade.get("issues", []),
            "loop_meltdown": loop_meltdown,
        },
        "guardrail": "This dashboard allocates CEO attention across portfolios. It does not validate or promote product behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_ceo_operating_dashboard(dashboard: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Operating Dashboard",
        "",
        f"Generated: {dashboard.get('generated_at')}",
        f"Run: {dashboard.get('run_id')}",
        f"Lab run: {dashboard.get('lab_run_id')}",
        f"Safe to continue: {dashboard.get('safe_to_continue')}",
        f"Safety scope: {dashboard.get('safe_to_continue_scope') or CEO_FLIGHT_SAFETY_SCOPE}",
        f"Dispatch authority: {dashboard.get('dispatch_authority') or 'not_granted_by_operating_dashboard'}",
        f"Runtime authority note: {dashboard.get('runtime_authority_note') or CEO_RUNTIME_AUTHORITY_NOTE}",
        f"Next recommended action: {dashboard.get('next_recommended_action')}",
        "",
        "## Candidate Portfolio",
        "",
    ]
    for item in dashboard.get("candidate_portfolio", []) or []:
        lines.append(
            "- "
            f"{item.get('belief_id')} role={item.get('product_role') or 'unknown'} "
            f"gate={item.get('evidence_gate')} next={item.get('next_required_evidence')}"
        )
    if not dashboard.get("candidate_portfolio"):
        lines.append("- none")
    lines.extend(["", "## Capability Backlog", ""])
    for item in dashboard.get("capability_backlog", []) or []:
        lines.append(
            "- "
            f"p{item.get('priority')} {item.get('kind')} capability={item.get('capability')} "
            f"reason={item.get('reason')}"
        )
    if not dashboard.get("capability_backlog"):
        lines.append("- none")
    data_gate = dashboard.get("data_gate", {}) or {}
    validation_gate = dashboard.get("validation_gate", {}) or {}
    memory = dashboard.get("memory_portfolio", {}) or {}
    product_governance = dashboard.get("product_governance", {}) or {}
    executive_kpis = dashboard.get("executive_kpis", {}) or {}
    role_orchestration = dashboard.get("role_orchestration", {}) or {}
    trace = dashboard.get("trace", {}) or {}
    lines.extend(
        [
            "",
            "## Data Gate",
            "",
            f"- Overall status: {data_gate.get('overall_status') or 'none'}",
            f"- Safe for fresh validation: {data_gate.get('safe_to_run_fresh_validation')}",
            f"- Next action: {data_gate.get('next_action') or 'none'}",
            "",
            "## Validation Gate",
            "",
            f"- Fresh/withheld contract: {validation_gate.get('fresh_withheld_contract_status') or 'none'}",
            f"- Fresh/withheld execution: {validation_gate.get('fresh_withheld_execution_status') or 'none'}",
            f"- Fresh/withheld completed: {validation_gate.get('fresh_withheld_validation_completed')}",
            f"- Fresh/withheld result: {validation_gate.get('fresh_withheld_validation_result') or 'none'}",
            "",
            "## Memory And Trace",
            "",
            f"- Memory delta required: {memory.get('memory_delta_required')}",
            f"- Knowledge graph delta status: {memory.get('knowledge_graph_delta_status') or 'none'}",
            f"- Trace verdict: {trace.get('verdict')}",
            f"- Trace score: {trace.get('score') if trace.get('score') != '' else 'n/a'}",
            f"- Trace recommended next action: {trace.get('recommended_next_action') or 'none'}",
            f"- Trace manual data import required: {trace.get('manual_data_import_required') if trace.get('manual_data_import_required') != '' else 'n/a'}",
            f"- Trace issues: {trace.get('issues') or []}",
            "",
            "## Product Governance",
            "",
            f"- Promotion proposal status: {product_governance.get('promotion_proposal_status') or 'none'}",
            f"- Approval required: {product_governance.get('approval_required')}",
            f"- Pending approvals: {product_governance.get('pending_approval_count', 0)}",
            f"- Missing evidence: {product_governance.get('missing_evidence') or []}",
            f"- Evidence debt: {product_governance.get('evidence_debt_status') or 'none'} "
            f"({product_governance.get('evidence_debt_count', 0)} items)",
            f"- Next evidence debt action: {product_governance.get('next_evidence_debt_action') or 'none'}",
            f"- Product language allowed: {product_governance.get('product_language_allowed')}",
            "",
            "## Executive KPIs",
            "",
            f"- Open approvals: {executive_kpis.get('open_approval_count', 0)}",
            f"- Evidence debt: {executive_kpis.get('evidence_debt_count', 0)}",
            f"- Capability backlog: {executive_kpis.get('capability_backlog_count', 0)}",
            f"- Validation threshold status: {executive_kpis.get('validation_threshold_status') or 'none'}",
            "",
            "## Role Orchestration",
            "",
            f"- Status: {role_orchestration.get('status') or 'none'}",
            f"- Tasks: {role_orchestration.get('task_count', 0)}",
            f"- Pending: {role_orchestration.get('pending_task_count', 0)}",
            f"- Pending manual: {role_orchestration.get('pending_manual_task_count', 0)}",
            f"- Pending autonomous: {role_orchestration.get('pending_autonomous_task_count', 0)}",
            f"- Completed: {role_orchestration.get('completed_task_count', 0)}",
            f"- Blocked: {role_orchestration.get('blocked_task_count', 0)}",
            f"- Top pending task: {role_orchestration.get('top_pending_task_id') or 'none'}",
            f"- Top blocked task: {role_orchestration.get('top_blocked_task_id') or 'none'}",
            f"- Top blocked role: {role_orchestration.get('top_blocked_role_id') or 'none'}",
            f"- Top blocked review: {role_orchestration.get('top_blocked_review_status') or 'none'}",
            f"- Top blocked result path: {role_orchestration.get('top_blocked_result_path') or 'none'}",
            f"- Top blocked next action: {role_orchestration.get('top_blocked_next_action') or 'none'}",
            f"- Top blocked finding: {role_orchestration.get('top_blocked_finding') or 'none'}",
            f"- Next action: {role_orchestration.get('next_action') or 'none'}",
            "",
            "## Risks",
            "",
        ]
    )
    for risk in dashboard.get("risk_portfolio", []) or []:
        lines.append(f"- {risk.get('risk')}: {risk.get('severity')} - {risk.get('mitigation')}")
    if not dashboard.get("risk_portfolio"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(dashboard.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_operating_dashboard(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    flight = run_ceo_flight_dashboard(options)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    champion_results = _load_yaml_if_exists(root / "champion_challenger_results.yaml")
    visual_queue = _load_yaml_if_exists(root / "champion_challenger_visual_review_queue.yaml")
    fresh_control_plan = _load_yaml_if_exists(root / "fresh_control_validation_plan.yaml")
    fresh_data_preflight = _load_yaml_if_exists(root / "fresh_data_preflight.yaml")
    frozen_plan = _load_yaml_if_exists(root / "frozen_candidate_validation_plan.yaml")
    fresh_withheld_contract = _load_yaml_if_exists(root / "fresh_withheld_validation_contract.yaml")
    fresh_withheld_execution = _load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml")
    capability_gap = _load_yaml_if_exists(root / "capability_gap.yaml")
    trace_grade = _load_yaml_if_exists(root / "trace_grade.yaml")
    outcome_card = _load_yaml_if_exists(root / "action_outcome_card.yaml")
    risk_register = _load_yaml_if_exists(root / "risk_register.yaml")
    knowledge_graph_delta = _load_yaml_if_exists(root / "knowledge_graph_delta.yaml")
    promotion_proposal = _load_yaml_if_exists(root / "promotion_proposal.yaml")
    evidence_debt_register = _load_yaml_if_exists(root / "evidence_debt_register.yaml")
    approval_queue = _load_yaml_if_exists(root / "approval_queue.yaml")
    executive_kpis = _load_yaml_if_exists(root / "executive_kpis.yaml")
    role_queue = _load_yaml_if_exists(root / "role_task_queue.yaml")
    dashboard = build_ceo_operating_dashboard(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        flight_dashboard=flight["dashboard"],
        product_delta=product_delta,
        champion_results=champion_results,
        visual_queue=visual_queue,
        fresh_control_plan=fresh_control_plan,
        fresh_data_preflight=fresh_data_preflight,
        frozen_plan=frozen_plan,
        fresh_withheld_contract=fresh_withheld_contract,
        fresh_withheld_execution=fresh_withheld_execution,
        capability_gap=capability_gap,
        trace_grade=trace_grade,
        outcome_card=outcome_card,
        risk_register=risk_register,
        knowledge_graph_delta=knowledge_graph_delta,
        promotion_proposal=promotion_proposal,
        evidence_debt_register=evidence_debt_register,
        approval_queue=approval_queue,
        executive_kpis=executive_kpis,
        role_queue=role_queue,
    )
    path = root / "ceo_operating_dashboard.yaml"
    report_path = root / "ceo_operating_dashboard.md"
    atomic_write_yaml(path, dashboard)
    atomic_write_text(report_path, render_ceo_operating_dashboard(dashboard))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "dashboard": dashboard,
        "paths": {"dashboard": path, "dashboard_report": report_path},
    }


def build_ceo_promotion_proposal(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    frozen_plan: dict[str, Any],
    fresh_withheld_execution: dict[str, Any],
    champion_results: dict[str, Any],
    visual_queue: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
    trace_grade: dict[str, Any],
    specialist_review_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    frozen_specs = list(frozen_plan.get("validation_specs", []) or [])
    execution_completed = bool(fresh_withheld_execution.get("validation_completed"))
    execution_result = str(fresh_withheld_execution.get("validation_result", ""))
    threshold_status = str((fresh_withheld_execution.get("threshold_results", {}) or {}).get("status", ""))
    validation_completed = execution_completed
    validation_result = execution_result or "not_run"
    validation_passed = (
        execution_completed
        and threshold_status == "passed"
        and execution_result == "fresh_withheld_validation_passed_shadow_only_not_promotion_eligible"
    )
    ready_specs = [spec for spec in frozen_specs if spec.get("status") == "ready_for_execution"]
    missing_evidence: list[str] = []
    if not frozen_specs:
        missing_evidence.append("frozen_candidate_validation_plan")
    if not validation_completed:
        missing_evidence.append("completed_fresh_or_frozen_validation")
    if not validation_passed:
        missing_evidence.append("passing_validation_result")
    if not visual_queue.get("items"):
        missing_evidence.append("visual_review_queue_or_labels")
    if fresh_data_preflight and not fresh_data_preflight.get("safe_to_run_fresh_validation"):
        missing_evidence.append("safe_fresh_data_preflight")
    if trace_grade.get("verdict") == "fail":
        missing_evidence.append("passing_trace_grade")
    specialist_review_gate = specialist_review_gate or {
        "status": "not_evaluated",
        "passed": False,
        "missing_roles": ["validation_referee", "product_translator_or_risk_officer"],
        "production_effect": "none",
    }
    if not specialist_review_gate.get("passed"):
        missing_evidence.append("completed_specialist_reviews")
    if missing_evidence:
        status = "blocked_missing_promotion_evidence"
    else:
        status = "ready_for_user_approval"
    candidates: list[dict[str, Any]] = []
    champion_by_id = {str(item.get("belief_id", "")): item for item in champion_results.get("results", []) or []}
    visual_by_id = {str(item.get("belief_id", "")): item for item in visual_queue.get("items", []) or []}
    for spec in frozen_specs:
        belief_id = str(spec.get("belief_id", ""))
        candidates.append(
            {
                "belief_id": belief_id,
                "product_role": spec.get("product_role"),
                "champion": spec.get("champion"),
                "challenger": spec.get("challenger"),
                "frozen_spec_status": spec.get("status"),
                "champion_challenger_decision": champion_by_id.get(belief_id, {}).get("decision", ""),
                "visual_review_status": visual_by_id.get(belief_id, {}).get("review_status", ""),
                "required_metrics": spec.get("required_metrics", []),
                "required_controls": spec.get("required_controls", []),
                "production_effect": "none",
            }
        )
    return {
        "model": CEO_PROMOTION_PROPOSAL_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "candidate_count": len(candidates),
        "ready_frozen_spec_count": len(ready_specs),
        "validation_completed": validation_completed,
        "validation_result": validation_result,
        "threshold_status": threshold_status,
        "validation_passed": validation_passed,
        "fresh_withheld_execution_status": fresh_withheld_execution.get("status", ""),
        "specialist_review_gate": specialist_review_gate,
        "missing_evidence": missing_evidence,
        "candidates": candidates,
        "approval_required": True,
        "required_user_decision": "approve_or_reject_promotion_after_review",
        "forbidden_auto_actions": [
            "change core_signal_v0",
            "change Pine defaults",
            "change production scores or rankings",
            "change production states or alerts",
        ],
        "next_action": "wait_for_user_approval" if status == "ready_for_user_approval" else "complete_missing_promotion_evidence",
        "guardrail": "This proposal can summarize evidence for review, but it cannot apply product changes.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_ceo_promotion_proposal(proposal: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Promotion Proposal",
        "",
        f"Generated: {proposal.get('generated_at')}",
        f"Run: {proposal.get('run_id')}",
        f"Lab run: {proposal.get('lab_run_id')}",
        f"Status: {proposal.get('status')}",
        f"Approval required: {proposal.get('approval_required')}",
        f"Next action: {proposal.get('next_action')}",
        f"Specialist review gate: {(proposal.get('specialist_review_gate', {}) or {}).get('status')}",
        "",
        "## Missing Evidence",
        "",
    ]
    missing = proposal.get("missing_evidence", []) or []
    if missing:
        lines.extend(f"- {item}" for item in missing)
    else:
        lines.append("- none")
    lines.extend(["", "## Candidates", ""])
    for item in proposal.get("candidates", []) or []:
        lines.append(
            "- "
            f"{item.get('belief_id')} role={item.get('product_role')} "
            f"frozen={item.get('frozen_spec_status')} visual={item.get('visual_review_status')}"
        )
    if not proposal.get("candidates"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Forbidden Auto Actions",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in proposal.get("forbidden_auto_actions", []) or [])
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(proposal.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _resolve_specialist_review_path(result_path: str, *, source_root: Path | None, run_root: Path | None) -> Path | None:
    if not result_path:
        return None
    raw_path = Path(result_path)
    candidates = [raw_path] if raw_path.is_absolute() else []
    if source_root is not None and not raw_path.is_absolute():
        candidates.append(source_root / raw_path)
    if run_root is not None and not raw_path.is_absolute():
        candidates.append(run_root / raw_path)
    candidates.append(raw_path)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else None


def _specialist_review_acceptance(
    task: dict[str, Any],
    *,
    source_root: Path | None,
    run_root: Path | None,
) -> dict[str, Any]:
    role_id = str(task.get("role_id", ""))
    task_id = str(task.get("task_id", ""))
    result_path = str(task.get("result_path", ""))
    resolved_path = _resolve_specialist_review_path(result_path, source_root=source_root, run_root=run_root)
    if source_root is None and run_root is None:
        return {
            "role_id": role_id,
            "task_id": task_id,
            "status": "review_context_missing",
            "reason": "completed role task cannot be accepted without filesystem review context",
            "result_path": result_path,
            "production_effect": "none",
        }
    if resolved_path is None or not resolved_path.exists():
        return {
            "role_id": role_id,
            "task_id": task_id,
            "status": "missing_review_artifact",
            "reason": "completed role task has no readable result_path artifact",
            "result_path": result_path,
            "production_effect": "none",
        }
    review = _load_yaml_if_exists(resolved_path)
    if not review:
        return {
            "role_id": role_id,
            "task_id": task_id,
            "status": "unreadable_review_artifact",
            "reason": "result_path did not contain a YAML review payload",
            "result_path": str(resolved_path),
            "production_effect": "none",
        }
    review_role = str(review.get("role_id", "") or "")
    review_task = str(review.get("task_id", "") or "")
    review_status = str(review.get("review_status", review.get("status", ""))).lower()
    review_decision = str(review.get("decision", review.get("recommendation", ""))).lower()
    approving_values = {"pass", "passed", "approve", "approved", "accept", "accepted", "no_blocker", "no_blockers"}
    issues: list[str] = []
    if review_role and review_role != role_id:
        issues.append("role_id_mismatch")
    if review_task and review_task != task_id:
        issues.append("task_id_mismatch")
    if str(review.get("production_effect", "none")) not in {"", "none"}:
        issues.append("non_none_production_effect")
    if review.get("product_language_allowed") is True:
        issues.append("product_language_allowed_true")
    if review_status not in approving_values and review_decision not in approving_values:
        issues.append("review_not_approving")
    return {
        "role_id": role_id,
        "task_id": task_id,
        "status": "accepted" if not issues else "rejected",
        "issues": issues,
        "review_status": review_status,
        "review_decision": review_decision,
        "result_path": str(resolved_path),
        "production_effect": "none",
    }


def build_promotion_specialist_review_gate(
    role_queue: dict[str, Any],
    *,
    source_root: Path | None = None,
    run_root: Path | None = None,
) -> dict[str, Any]:
    completed_tasks = [
        task for task in role_queue.get("tasks", []) or [] if str(task.get("status", "")) == "complete"
    ]
    review_results = [
        _specialist_review_acceptance(task, source_root=source_root, run_root=run_root)
        for task in completed_tasks
    ]
    accepted_roles = {
        str(result.get("role_id", ""))
        for result in review_results
        if str(result.get("status", "")) == "accepted"
    }
    required_any = {"product_translator", "risk_officer"}
    has_validation_referee = "validation_referee" in accepted_roles
    has_product_or_risk_review = bool(accepted_roles & required_any)
    missing: list[str] = []
    if not has_validation_referee:
        missing.append("validation_referee")
    if not has_product_or_risk_review:
        missing.append("product_translator_or_risk_officer")
    rejected_reviews = [result for result in review_results if str(result.get("status", "")) != "accepted"]
    status = "passed" if not missing and not rejected_reviews else "missing_specialist_reviews" if missing else "failed_specialist_reviews"
    return {
        "status": status,
        "passed": not missing and not rejected_reviews,
        "required": ["validation_referee", "product_translator_or_risk_officer"],
        "completed_roles": sorted({str(task.get("role_id", "")) for task in completed_tasks}),
        "accepted_roles": sorted(accepted_roles),
        "missing_roles": missing,
        "review_results": review_results,
        "rejected_review_count": len(rejected_reviews),
        "source_artifact": "role_task_queue.yaml",
        "production_effect": "none",
    }


def run_ceo_promotion_proposal(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="run_promotion_proposal",
        aliases={"promotion-proposal"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    specialist_review_gate = build_promotion_specialist_review_gate(
        _load_yaml_if_exists(root / "role_task_queue.yaml"),
        source_root=options.source_root,
        run_root=root,
    )
    proposal = build_ceo_promotion_proposal(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        frozen_plan=_load_yaml_if_exists(root / "frozen_candidate_validation_plan.yaml"),
        fresh_withheld_execution=_load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml"),
        champion_results=_load_yaml_if_exists(root / "champion_challenger_results.yaml"),
        visual_queue=_load_yaml_if_exists(root / "champion_challenger_visual_review_queue.yaml"),
        fresh_data_preflight=_load_yaml_if_exists(root / "fresh_data_preflight.yaml"),
        trace_grade=_load_yaml_if_exists(root / "trace_grade.yaml"),
        specialist_review_gate=specialist_review_gate,
    )
    path = root / "promotion_proposal.yaml"
    report_path = root / "promotion_proposal.md"
    atomic_write_yaml(path, proposal)
    atomic_write_text(report_path, render_ceo_promotion_proposal(proposal))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "proposal": proposal,
        "paths": {"proposal": path, "proposal_report": report_path},
    }


def _debt_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_") or "unknown"


def _append_evidence_debt(
    debts: list[dict[str, Any]],
    seen: set[tuple[str, str]],
    *,
    candidate_id: str,
    product_role: str,
    debt_kind: str,
    priority: int,
    blocker_type: str,
    evidence_required: str | list[str],
    retire_action: str,
    source_artifact: str,
    status: str = "open",
) -> None:
    candidate_key = candidate_id or "global"
    key = (candidate_key, debt_kind)
    if key in seen:
        return
    seen.add(key)
    debts.append(
        {
            "debt_id": f"{_debt_slug(candidate_key)}__{_debt_slug(debt_kind)}",
            "candidate_id": candidate_id or None,
            "product_role": product_role or "global",
            "debt_kind": debt_kind,
            "priority": priority,
            "blocker_type": blocker_type,
            "evidence_required": evidence_required,
            "owner_command": retire_action,
            "retire_action": retire_action,
            "blocking_artifact": source_artifact,
            "source_artifact": source_artifact,
            "source_paths": [source_artifact],
            "promotion_ceiling": "shadow_candidate_until_debt_retired",
            "status": status,
            "blocks_promotion": True,
            "blocks_product_language": True,
            "production_effect": "none",
        }
    )


def _promotion_missing_debt(missing: str) -> tuple[int, str, str, str]:
    mapping = {
        "frozen_candidate_validation_plan": (
            3,
            "missing_validation_plan",
            "riskflow ceo frozen-candidate-validation",
            "frozen_candidate_validation_plan.yaml",
        ),
        "completed_fresh_or_frozen_validation": (
            1,
            "missing_completed_validation",
            "build_or_run_frozen_validation_executor",
            "frozen_candidate_validation_plan.yaml",
        ),
        "passing_validation_result": (
            1,
            "missing_passing_validation_result",
            "build_or_run_frozen_validation_executor",
            "frozen_candidate_validation_plan.yaml",
        ),
        "visual_review_queue_or_labels": (
            4,
            "missing_visual_review",
            "complete_champion_challenger_visual_review",
            "champion_challenger_visual_review_queue.yaml",
        ),
        "safe_fresh_data_preflight": (
            2,
            "fresh_data_gate_blocked",
            "riskflow ceo fresh-data-preflight",
            "fresh_data_preflight.yaml",
        ),
        "passing_trace_grade": (
            2,
            "trace_grade_failed",
            "riskflow ceo trace-grade",
            "trace_grade.yaml",
        ),
    }
    return mapping.get(
        missing,
        (
            6,
            "missing_promotion_evidence",
            "complete_missing_promotion_evidence",
            "promotion_proposal.yaml",
        ),
    )


def build_ceo_evidence_debt_register(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    candidate_portfolio: list[dict[str, Any]],
    champion_results: dict[str, Any],
    visual_queue: dict[str, Any],
    fresh_data_preflight: dict[str, Any],
    frozen_plan: dict[str, Any],
    fresh_withheld_execution: dict[str, Any],
    promotion_proposal: dict[str, Any],
    trace_grade: dict[str, Any],
) -> dict[str, Any]:
    debts: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    execution_completed = bool(fresh_withheld_execution.get("validation_completed"))
    execution_result = str(fresh_withheld_execution.get("validation_result", ""))
    threshold_status = str((fresh_withheld_execution.get("threshold_results", {}) or {}).get("status", ""))
    validation_completed = execution_completed
    validation_result = execution_result or "not_run"
    validation_passed = (
        execution_completed
        and threshold_status == "passed"
        and execution_result == "fresh_withheld_validation_passed_shadow_only_not_promotion_eligible"
    )
    safe_fresh_data = fresh_data_preflight.get("safe_to_run_fresh_validation")
    if safe_fresh_data is None:
        safe_fresh_data = not bool(fresh_data_preflight)

    champion_by_id = {str(item.get("belief_id", "")): item for item in champion_results.get("results", []) or []}
    visual_by_id = {str(item.get("belief_id", "")): item for item in visual_queue.get("items", []) or []}
    frozen_by_id = {str(item.get("belief_id", "")): item for item in frozen_plan.get("validation_specs", []) or []}

    for item in candidate_portfolio:
        candidate_id = str(item.get("belief_id", "") or "")
        if not candidate_id:
            continue
        product_role = str(item.get("product_role", "") or "")
        champion = champion_by_id.get(candidate_id, {})
        checklist = item.get("metric_checklist", {}) or champion.get("product_metric_checklist", {}) or {}
        missing_metrics = list(checklist.get("missing", []) or [])
        if not item.get("champion_challenger_decision"):
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="champion_challenger_comparison",
                priority=2,
                blocker_type="missing_shadow_comparison",
                evidence_required="compare candidate against core_signal_v0 before further product translation",
                retire_action="riskflow ceo champion-challenger",
                source_artifact="champion_challenger_results.yaml",
            )
        if missing_metrics:
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="missing_product_metric_checklist",
                priority=2,
                blocker_type="missing_metric_evidence",
                evidence_required=missing_metrics,
                retire_action="riskflow ceo champion-challenger",
                source_artifact="champion_challenger_results.yaml",
            )
        visual_status = str(item.get("visual_review_status") or visual_by_id.get(candidate_id, {}).get("review_status", ""))
        if not visual_status or visual_status.startswith("blocked"):
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="visual_review_evidence",
                priority=4,
                blocker_type="missing_visual_review",
                evidence_required="visual readability, product-role match, false-positive shape, and promotion-blocker labels",
                retire_action="complete_champion_challenger_visual_review",
                source_artifact="champion_challenger_visual_review_queue.yaml",
            )
        if not item.get("fresh_control_route"):
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="fresh_control_validation_plan",
                priority=3,
                blocker_type="missing_validation_plan",
                evidence_required="predeclared fresh/control route, tests, controls, and source snapshot",
                retire_action="riskflow ceo fresh-control-validation",
                source_artifact="fresh_control_validation_plan.yaml",
            )
        if fresh_data_preflight and not safe_fresh_data:
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="fresh_data_readiness",
                priority=1,
                blocker_type="fresh_data_gate_blocked",
                evidence_required="fresh enough OHLCV coverage across required local timeframes and active universe members",
                retire_action=str(fresh_data_preflight.get("next_action") or "import_or_curate_fresh_ohlcv_data"),
                source_artifact="fresh_data_preflight.yaml",
            )
        frozen_spec = frozen_by_id.get(candidate_id, {})
        frozen_status = str(item.get("frozen_spec_status") or frozen_spec.get("status", ""))
        if not frozen_status:
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="frozen_validation_spec",
                priority=3,
                blocker_type="missing_frozen_spec",
                evidence_required="frozen challenger shape, metrics, controls, eligible timeframes, and no-tuning contract",
                retire_action="riskflow ceo frozen-candidate-validation",
                source_artifact="frozen_candidate_validation_plan.yaml",
            )
        elif frozen_status.startswith("blocked"):
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="frozen_validation_spec_blocked",
                priority=2,
                blocker_type=frozen_status,
                evidence_required="repair blocked frozen validation spec inputs before execution",
                retire_action=str(frozen_plan.get("next_action") or "riskflow ceo frozen-candidate-validation"),
                source_artifact="frozen_candidate_validation_plan.yaml",
            )
        elif not validation_completed:
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="fresh_or_frozen_validation_execution",
                priority=1,
                blocker_type="missing_completed_validation",
                evidence_required="execute frozen validation specs with declared metrics and controls",
                retire_action="build_or_run_frozen_validation_executor",
                source_artifact="frozen_candidate_validation_plan.yaml",
            )
        elif not validation_passed:
            blocker_type = (
                "fresh_withheld_thresholds_failed"
                if str(fresh_withheld_execution.get("status", "")) == "fresh_withheld_validation_failed_thresholds"
                else "shadow_validation_not_promotion_eligible"
                if execution_completed
                else "validation_not_passing"
            )
            retire_action = (
                "review_fresh_withheld_threshold_failures_or_archive_candidate"
                if blocker_type == "fresh_withheld_thresholds_failed"
                else "review_shadow_validation_results_and_predeclare_passing_thresholds"
                if execution_completed
                else "revise_or_archive_shadow_candidate"
            )
            source_artifact = (
                "fresh_withheld_validation_execution_result.yaml"
                if execution_completed
                else "frozen_candidate_validation_plan.yaml"
            )
            _append_evidence_debt(
                debts,
                seen,
                candidate_id=candidate_id,
                product_role=product_role,
                debt_kind="passing_validation_result",
                priority=1,
                blocker_type=blocker_type,
                evidence_required="passing fresh/control validation result",
                retire_action=retire_action,
                source_artifact=source_artifact,
            )

    for missing in promotion_proposal.get("missing_evidence", []) or []:
        priority, blocker_type, retire_action, source_artifact = _promotion_missing_debt(str(missing))
        if (
            str(missing) == "passing_validation_result"
            and str(frozen_plan.get("validation_result", "")).startswith("source_replay")
        ):
            retire_action = "run_frozen_validation_rerun"
            blocker_type = "fresh_or_withheld_validation_required"
        if (
            str(missing) == "passing_validation_result"
            and str(fresh_withheld_execution.get("status", "")) == "fresh_withheld_validation_failed_thresholds"
        ):
            retire_action = "review_fresh_withheld_threshold_failures_or_archive_candidate"
            blocker_type = "fresh_withheld_thresholds_failed"
            source_artifact = "fresh_withheld_validation_execution_result.yaml"
        elif (
            str(missing) == "passing_validation_result"
            and str(fresh_withheld_execution.get("validation_result", "")).startswith("fresh_withheld")
        ):
            retire_action = "review_shadow_validation_results_and_predeclare_passing_thresholds"
            blocker_type = "shadow_validation_not_promotion_eligible"
            source_artifact = "fresh_withheld_validation_execution_result.yaml"
        _append_evidence_debt(
            debts,
            seen,
            candidate_id="",
            product_role="global",
            debt_kind=f"promotion_missing_{missing}",
            priority=priority,
            blocker_type=blocker_type,
            evidence_required=str(missing),
            retire_action=retire_action,
            source_artifact=source_artifact,
        )

    if trace_grade.get("verdict") == "fail":
        _append_evidence_debt(
            debts,
            seen,
            candidate_id="",
            product_role="global",
            debt_kind="trace_grade_failure",
            priority=1,
            blocker_type="trace_grade_failed",
            evidence_required=trace_grade.get("issues", []) or "passing CEO trace grade",
            retire_action="riskflow ceo trace-grade",
            source_artifact="trace_grade.yaml",
        )

    debts = sorted(debts, key=lambda debt: (int(debt.get("priority", 99)), str(debt.get("candidate_id") or ""), str(debt.get("debt_kind", ""))))
    candidate_debt_count = len([debt for debt in debts if debt.get("candidate_id")])
    global_debt_count = len(debts) - candidate_debt_count
    if debts:
        status = "open_evidence_debt"
    elif promotion_proposal.get("status") == "ready_for_user_approval":
        status = "clear_for_user_review"
    elif candidate_portfolio:
        status = "candidate_portfolio_present_no_open_debt"
    else:
        status = "no_candidates"
    return {
        "model": CEO_EVIDENCE_DEBT_REGISTER_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "debt_count": len(debts),
        "candidate_debt_count": candidate_debt_count,
        "global_debt_count": global_debt_count,
        "debts": debts,
        "next_action": debts[0]["retire_action"] if debts else "wait_for_user_approval",
        "promotion_status": promotion_proposal.get("status", ""),
        "guardrail": "This register tracks missing product evidence only. It does not validate, promote, or change production behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_ceo_evidence_debt_register(register: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Evidence Debt Register",
        "",
        f"Generated: {register.get('generated_at')}",
        f"Run: {register.get('run_id')}",
        f"Lab run: {register.get('lab_run_id')}",
        f"Status: {register.get('status')}",
        f"Debts: {register.get('debt_count')}",
        f"Next action: {register.get('next_action')}",
        f"Promotion status: {register.get('promotion_status')}",
        "",
        "## Open Debts",
        "",
    ]
    for debt in register.get("debts", []) or []:
        lines.append(
            "- "
            f"p{debt.get('priority')} {debt.get('debt_id')} "
            f"candidate={debt.get('candidate_id') or 'global'} "
            f"kind={debt.get('debt_kind')} retire={debt.get('retire_action')}"
        )
    if not register.get("debts"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(register.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_evidence_debt_register(options: CeoOpsOptions) -> dict[str, Any]:
    _require_ceo_action_context(
        options,
        action="run_evidence_debt_register",
        aliases={"evidence-debt-register"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context=options.ceo_context if options.ceo_context in CEO_DIAGNOSTIC_CONTEXTS else "diagnostic_refresh")
    if not (root / "trace_grade.yaml").exists():
        run_ceo_trace_grade(options)
    if not (root / "promotion_proposal.yaml").exists():
        run_ceo_promotion_proposal(diagnostic_options)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    champion_results = _load_yaml_if_exists(root / "champion_challenger_results.yaml")
    visual_queue = _load_yaml_if_exists(root / "champion_challenger_visual_review_queue.yaml")
    fresh_control_plan = _load_yaml_if_exists(root / "fresh_control_validation_plan.yaml")
    fresh_data_preflight = _load_yaml_if_exists(root / "fresh_data_preflight.yaml")
    frozen_plan = _load_yaml_if_exists(root / "frozen_candidate_validation_plan.yaml")
    fresh_withheld_contract = _load_yaml_if_exists(root / "fresh_withheld_validation_contract.yaml")
    fresh_withheld_execution = _load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml")
    candidate_portfolio = build_ceo_candidate_portfolio(
        product_delta,
        champion_results,
        visual_queue,
        fresh_control_plan,
        fresh_data_preflight,
        frozen_plan,
        fresh_withheld_contract,
        fresh_withheld_execution,
    )
    register = build_ceo_evidence_debt_register(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        candidate_portfolio=candidate_portfolio,
        champion_results=champion_results,
        visual_queue=visual_queue,
        fresh_data_preflight=fresh_data_preflight,
        frozen_plan=frozen_plan,
        fresh_withheld_execution=_load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml"),
        promotion_proposal=_load_yaml_if_exists(root / "promotion_proposal.yaml"),
        trace_grade=_load_yaml_if_exists(root / "trace_grade.yaml"),
    )
    path = root / "evidence_debt_register.yaml"
    report_path = root / "evidence_debt_register.md"
    atomic_write_yaml(path, register)
    atomic_write_text(report_path, render_ceo_evidence_debt_register(register))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "register": register,
        "paths": {"register": path, "register_report": report_path},
    }


def _approval_decision_ledger_path(root: Path) -> Path:
    return root / "approval_decision_ledger.jsonl"


def _load_approval_decisions(root: Path) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    ledger_path = _approval_decision_ledger_path(root)
    if not ledger_path.exists():
        return decisions
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            approval_id = str(item.get("approval_id", ""))
            if approval_id:
                decisions[approval_id] = item
    return decisions


def _approval_item_fingerprint(item: dict[str, Any]) -> str:
    payload = {
        "approval_id": item.get("approval_id", ""),
        "kind": item.get("kind", ""),
        "source_artifact": item.get("source_artifact", ""),
        "required_user_decision": item.get("required_user_decision", ""),
        "reason": item.get("reason", ""),
        "forbidden_auto_actions": item.get("forbidden_auto_actions", []),
    }
    return hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()


def _pending_approval_by_id(queue: dict[str, Any], approval_id: str) -> dict[str, Any]:
    for item in queue.get("pending_items", []) or []:
        if str(item.get("approval_id", "")) == approval_id:
            return item
    return {}


def _approval_item_by_id(queue: dict[str, Any], approval_id: str) -> dict[str, Any]:
    for item in queue.get("items", []) or []:
        if str(item.get("approval_id", "")) == approval_id:
            return item
    return {}


def build_ceo_approval_queue(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    promotion_proposal: dict[str, Any],
    stop_requested: bool,
    decisions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    decisions = decisions or {}
    items: list[dict[str, Any]] = []
    if promotion_proposal.get("status") == "ready_for_user_approval":
        items.append(
            {
                "approval_id": "promotion_proposal",
                "kind": "product_promotion",
                "authority": "red",
                "status": "pending",
                "reason": "promotion proposal is ready for user review but cannot be applied autonomously",
                "source_artifact": "promotion_proposal.yaml",
                "required_user_decision": "approve_or_reject_promotion_after_review",
                "forbidden_auto_actions": promotion_proposal.get("forbidden_auto_actions", []),
                "production_effect": "none",
            }
        )
    if stop_requested:
        items.append(
            {
                "approval_id": "clear_stop_request",
                "kind": "resume_stopped_run",
                "authority": "red",
                "status": "pending",
                "reason": "stopped CEO/lab runtime cannot be resumed or cleared without explicit user approval",
                "source_artifact": "stop_request.yaml",
                "required_user_decision": "approve_or_reject_resume_or_clear_stop",
                "forbidden_auto_actions": ["clear stop files", "resume stopped runtime", "mutate stopped runtime queues"],
                "production_effect": "none",
            }
        )
    for item in items:
        approval_id = str(item.get("approval_id", ""))
        item["approval_record_command"] = _ceo_approval_record_command(ceo_run_id=ceo_run_id, approval_id=approval_id)
        item["approval_apply_command"] = _ceo_approval_apply_command(ceo_run_id=ceo_run_id, approval_id=approval_id)
        item["approval_closure_steps"] = [
            "User decides approved or rejected.",
            "Record the user-confirmed decision with approval-record.",
            "If approved and an apply executor exists, run approval-apply as a second user-confirmed step.",
        ]
        item["approval_authority"] = "user_only"
        item["approval_item_fingerprint"] = _approval_item_fingerprint(item)
        if approval_id in decisions:
            item["status"] = str(decisions[approval_id].get("decision", "recorded"))
            item["decision_recorded_at"] = decisions[approval_id].get("generated_at", "")
    pending_items = [item for item in items if item.get("status") == "pending"]
    top_pending_item = pending_items[0] if pending_items else {}
    return {
        "model": CEO_APPROVAL_QUEUE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "pending_approvals" if pending_items else "no_pending_approvals",
        "pending_count": len(pending_items),
        "item_count": len(items),
        "items": items,
        "pending_items": pending_items,
        "top_pending_approval_id": top_pending_item.get("approval_id", ""),
        "top_pending_approval_record_command": top_pending_item.get("approval_record_command", ""),
        "top_pending_approval_apply_command": top_pending_item.get("approval_apply_command", ""),
        "next_action": "wait_for_user_approval" if pending_items else CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION,
        "guardrail": "This queue records red-authority decisions for user review. It never applies product or runtime changes.",
        "product_language_allowed": False,
        "production_effect": "none",
    }


def render_ceo_approval_queue(queue: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Approval Queue",
        "",
        f"Generated: {queue.get('generated_at')}",
        f"Run: {queue.get('run_id')}",
        f"Lab run: {queue.get('lab_run_id')}",
        f"Status: {queue.get('status')}",
        f"Pending approvals: {queue.get('pending_count')}",
        f"Top pending approval: {queue.get('top_pending_approval_id') or 'none'}",
        f"Record command: `{queue.get('top_pending_approval_record_command') or ''}`",
        f"Apply command: `{queue.get('top_pending_approval_apply_command') or ''}`",
        f"Next action: {queue.get('next_action')}",
        "",
        "## Items",
        "",
    ]
    for item in queue.get("items", []) or []:
        lines.extend(
            [
                f"- {item.get('approval_id')}",
                f"  - kind: {item.get('kind')}",
                f"  - authority: {item.get('authority')}",
                f"  - approval authority: {item.get('approval_authority')}",
                f"  - status: {item.get('status')}",
                f"  - reason: {item.get('reason')}",
                f"  - source: {item.get('source_artifact')}",
                f"  - required user decision: {item.get('required_user_decision')}",
                f"  - fingerprint: {item.get('approval_item_fingerprint')}",
                f"  - record command: `{item.get('approval_record_command')}`",
                f"  - apply command: `{item.get('approval_apply_command')}`",
                f"  - forbidden auto actions: {item.get('forbidden_auto_actions') or []}",
                f"  - closure steps: {' | '.join(str(step) for step in item.get('approval_closure_steps', []) or [])}",
            ]
        )
    if not queue.get("items"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(queue.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_approval_queue(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "promotion_proposal.yaml").exists():
        run_ceo_promotion_proposal(_with_ceo_context(options, context="diagnostic_refresh"))
    queue = build_ceo_approval_queue(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        promotion_proposal=_load_yaml_if_exists(root / "promotion_proposal.yaml"),
        stop_requested=is_stop_requested(options, ceo_run_id, lab_run_id),
        decisions=_load_approval_decisions(root),
    )
    status = {
        "model": CEO_APPROVAL_STATUS_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": queue.get("status"),
        "pending_count": queue.get("pending_count"),
        "pending_approval_ids": [item.get("approval_id") for item in queue.get("pending_items", []) or []],
        "top_pending_approval_id": queue.get("top_pending_approval_id", ""),
        "top_pending_approval_record_command": queue.get("top_pending_approval_record_command", ""),
        "top_pending_approval_apply_command": queue.get("top_pending_approval_apply_command", ""),
        "next_action": queue.get("next_action"),
        "production_effect": "none",
    }
    queue_path = root / "approval_queue.yaml"
    queue_report_path = root / "approval_queue.md"
    status_path = root / "approval_status.yaml"
    atomic_write_yaml(queue_path, queue)
    atomic_write_text(queue_report_path, render_ceo_approval_queue(queue))
    atomic_write_yaml(status_path, status)
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "queue": queue,
        "status": status,
        "paths": {"queue": queue_path, "queue_report": queue_report_path, "approval_status": status_path},
    }


def run_ceo_approval_record(
    options: CeoOpsOptions,
    *,
    approval_id: str,
    decision: str,
    user_confirmed: bool,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approved", "rejected"}:
        raise ValueError("approval decision must be approved or rejected")
    if not user_confirmed:
        raise ValueError("approval-record requires --user-confirmed")
    queue_before = run_ceo_approval_queue(options)["queue"]
    pending_item = _pending_approval_by_id(queue_before, approval_id)
    if not pending_item:
        raise ValueError(f"approval-record approval_id is not currently pending: {approval_id}")
    entry = {
        "model": CEO_APPROVAL_DECISION_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "approval_id": approval_id,
        "decision": normalized_decision,
        "user_confirmed": True,
        "approval_kind": pending_item.get("kind", ""),
        "source_artifact": pending_item.get("source_artifact", ""),
        "approval_item_fingerprint": pending_item.get("approval_item_fingerprint", ""),
        "production_effect": "none",
    }
    ledger_path = _approval_decision_ledger_path(root)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_json_safe(entry), sort_keys=True) + "\n")
    queue_result = run_ceo_approval_queue(options)
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": entry,
        "queue": queue_result["queue"],
        "paths": {
            "approval_decision_ledger": ledger_path,
            "approval_queue": queue_result["paths"]["queue"],
            "approval_status": queue_result["paths"]["approval_status"],
        },
    }


def render_ceo_approval_apply(result: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Approval Apply",
        "",
        f"Generated: {result.get('generated_at')}",
        f"Run: {result.get('run_id')}",
        f"Lab run: {result.get('lab_run_id')}",
        f"Approval id: {result.get('approval_id')}",
        f"Decision: {result.get('recorded_decision')}",
        f"Approval kind: {result.get('approval_kind')}",
        f"Source artifact: {result.get('source_artifact')}",
        f"Approval item current: {result.get('approval_item_current')}",
        f"Status: {result.get('status')}",
        f"Action taken: {result.get('action_taken')}",
        f"Production effect: {result.get('production_effect')}",
        "",
        "## Audit",
        "",
    ]
    audit = result.get("audit", []) or []
    lines.extend(f"- {item}" for item in audit) if audit else lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_approval_apply(
    options: CeoOpsOptions,
    *,
    approval_id: str,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("approval-apply requires --apply")
    if not user_confirmed:
        raise ValueError("approval-apply requires --user-confirmed")
    _require_ceo_action_context(
        options,
        action="approval_apply",
        aliases={"approval-apply"},
    )
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    decisions = _load_approval_decisions(root)
    recorded = decisions.get(approval_id, {})
    recorded_decision = str(recorded.get("decision", ""))
    queue_before = run_ceo_approval_queue(options)["queue"]
    current_item = _approval_item_by_id(queue_before, approval_id)
    recorded_fingerprint = str(recorded.get("approval_item_fingerprint", ""))
    current_fingerprint = str(current_item.get("approval_item_fingerprint", ""))
    audit: list[str] = []
    action_taken = "none"
    status = "blocked_missing_recorded_approval"
    if not recorded:
        audit.append("No approval decision ledger row exists for this approval id.")
    elif not current_item:
        status = "blocked_approval_not_currently_pending"
        audit.append("Recorded approval does not match a currently pending approval queue item.")
    elif not recorded_fingerprint or recorded_fingerprint != current_fingerprint:
        status = "blocked_stale_approval_record"
        audit.append("Recorded approval fingerprint does not match the current approval queue item.")
    elif recorded_decision != "approved":
        status = "closed_without_apply"
        action_taken = "recorded_rejection_honored"
        audit.append("Recorded decision is not approved; no runtime or product change was applied.")
    elif approval_id == "promotion_proposal":
        status = "promotion_approval_closed_shadow_only"
        action_taken = "promotion_approval_closure_recorded"
        audit.extend(
            [
                "Promotion approval closure was recorded for handoff.",
                "No production formula, score, ranking, state, alert, Pine, or TradingView default was changed.",
                "A separate explicit implementation task is still required for any production mutation.",
            ]
        )
    elif approval_id == "clear_stop_request":
        removed: list[str] = []
        for path in (ceo_stop_path(options, ceo_run_id), lab_stop_path(options, lab_run_id)):
            if path.exists():
                path.unlink()
                removed.append(str(path))
        status = "clear_stop_request_applied"
        action_taken = "cleared_recorded_stop_files"
        audit.append(f"Removed stop files: {removed or 'none present'}")
    else:
        status = "blocked_unsupported_approval_apply"
        audit.append("This approval id has no bounded apply executor.")
    result = {
        "model": CEO_APPROVAL_APPLY_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "approval_id": approval_id,
        "recorded_decision": recorded_decision,
        "approval_kind": recorded.get("approval_kind", ""),
        "source_artifact": recorded.get("source_artifact", ""),
        "recorded_approval_item_fingerprint": recorded_fingerprint,
        "current_approval_item_fingerprint": current_fingerprint,
        "approval_item_current": bool(current_item),
        "status": status,
        "action_taken": action_taken,
        "audit": audit,
        "guardrail": "approval-record is ledger-only; approval-apply is the explicit second step and remains non-mutating for promotion proposals.",
        "production_effect": "none",
    }
    path = root / f"approval_apply_{_debt_slug(approval_id)}.yaml"
    report_path = root / f"approval_apply_{_debt_slug(approval_id)}.md"
    atomic_write_yaml(path, result)
    atomic_write_text(report_path, render_ceo_approval_apply(result))
    action_result = {
        "model": CEO_ACTION_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "decision": "approval_apply",
        "action_taken": action_taken,
        "command_executed": "riskflow ceo approval-apply",
        "status": status,
        "meaningful_progress": status in {"promotion_approval_closed_shadow_only", "clear_stop_request_applied", "closed_without_apply"},
        "outputs": {"approval_apply": path, "approval_apply_report": report_path},
        "next_allowed_actions": [CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION],
        "production_effect": "none",
    }
    binding_paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "approval_apply": result,
        "action_result": action_result,
        "paths": {
            "approval_apply": path,
            "approval_apply_report": report_path,
            **binding_paths,
        },
    }


def build_ceo_executive_kpis(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    approval_queue: dict[str, Any],
    evidence_debt_register: dict[str, Any],
    candidate_portfolio: list[dict[str, Any]],
    capability_backlog: list[dict[str, Any]],
    trace_grade: dict[str, Any],
    fresh_withheld_execution: dict[str, Any],
    promotion_proposal: dict[str, Any],
    blocker_stack: dict[str, Any] | None = None,
    incident_register: dict[str, Any] | None = None,
    repair_plan: dict[str, Any] | None = None,
    role_queue: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blocker_stack = blocker_stack or {}
    incident_register = incident_register or {}
    repair_plan = repair_plan or {}
    role_queue = role_queue or {}
    validation_gate = {
        "execution_status": fresh_withheld_execution.get("status", ""),
        "validation_completed": bool(fresh_withheld_execution.get("validation_completed")),
        "validation_result": fresh_withheld_execution.get("validation_result", ""),
        "threshold_status": (fresh_withheld_execution.get("threshold_results", {}) or {}).get("status", ""),
    }
    loop_meltdown = trace_grade.get("loop_meltdown", {}) or {}
    trace_verdict = str(trace_grade.get("verdict", ""))
    trace_recommended_next_action = str(trace_grade.get("recommended_next_action", ""))
    trace_manual_data_import_required = _trace_grade_manual_data_import_required(trace_grade)
    role_pending_count = int(role_queue.get("pending_task_count", 0) or 0)
    role_pending_manual_count = int(role_queue.get("pending_manual_task_count", 0) or 0)
    role_pending_autonomous_count = int(role_queue.get("pending_autonomous_task_count", 0) or 0)
    role_blocked_count = int(role_queue.get("blocked_task_count", 0) or 0)
    role_completed_count = int(role_queue.get("completed_task_count", 0) or 0)
    role_top_blocked_finding = str(role_queue.get("top_blocked_finding", "") or "").replace("\n", " ").strip()
    if len(role_top_blocked_finding) > 180:
        role_top_blocked_finding = f"{role_top_blocked_finding[:177]}..."
    role_readiness_attention_required = bool(
        role_pending_count
        or role_blocked_count
        or str(role_queue.get("status", "")) in {"pending_role_tasks", "blocked_role_tasks"}
    )
    role_next_action = ""
    if role_pending_manual_count:
        role_next_action = str(role_queue.get("top_pending_closure_command", "") or "wait_for_user_approval_or_record_manual_gate_blocked")
    elif role_pending_autonomous_count:
        role_next_action = str(role_queue.get("next_role_result_command", "") or "record_next_autonomous_specialist_result")
    elif role_blocked_count:
        role_next_action = str(
            role_queue.get("top_blocked_next_action", "")
            or role_queue.get("top_blocked_closure_command", "")
            or "review_blocked_role_tasks_or_complete_missing_evidence"
        )
    kpis = {
        "open_approval_count": int(approval_queue.get("pending_count", 0) or 0),
        "evidence_debt_count": int(evidence_debt_register.get("debt_count", 0) or 0),
        "candidate_count": len(candidate_portfolio),
        "capability_backlog_count": len(capability_backlog),
        "trace_score": trace_grade.get("score"),
        "trace_verdict": trace_verdict,
        "trace_recommended_next_action": trace_recommended_next_action,
        "trace_issues": trace_grade.get("issues", []),
        "trace_manual_data_import_required": trace_manual_data_import_required,
        "no_progress_fingerprint_repeats": loop_meltdown.get("fingerprint_repeat_count", 0),
        "manual_gate_repeat_count": loop_meltdown.get("manual_gate_repeat_count", 0),
        "validation_threshold_status": validation_gate["threshold_status"],
        "promotion_status": promotion_proposal.get("status", ""),
        "top_blocker": blocker_stack.get("top_blocker", ""),
        "operating_incident_count": int(incident_register.get("incident_count", 0) or 0),
        "repair_plan_status": repair_plan.get("status", ""),
        "top_repair": repair_plan.get("top_repair", ""),
        "top_repair_kind": repair_plan.get("top_repair_kind", ""),
        "repair_next_command": repair_plan.get("next_command", ""),
        "role_queue_status": role_queue.get("status", ""),
        "role_pending_count": role_pending_count,
        "role_pending_manual_count": role_pending_manual_count,
        "role_pending_autonomous_count": role_pending_autonomous_count,
        "role_completed_count": role_completed_count,
        "role_blocked_count": role_blocked_count,
        "role_top_pending_task": role_queue.get("top_pending_task_id", ""),
        "role_top_blocked_task": role_queue.get("top_blocked_task_id", ""),
        "role_top_blocked_role": role_queue.get("top_blocked_role_id", ""),
        "role_top_blocked_review_status": role_queue.get("top_blocked_review_status", ""),
        "role_top_blocked_next_action": role_queue.get("top_blocked_next_action", ""),
        "role_top_blocked_finding": role_top_blocked_finding,
        "role_next_action": role_next_action,
        "product_language_allowed": False,
    }
    repair_attention_required = bool(kpis["top_repair"]) or kpis["repair_plan_status"] in {"manual_gate_first", "repair_plan_ready"}
    trace_attention_required = trace_verdict in {"fail", "warn"} or trace_manual_data_import_required is True
    status = (
        "attention_required"
        if (
            kpis["open_approval_count"]
            or kpis["evidence_debt_count"]
            or kpis["operating_incident_count"]
            or repair_attention_required
            or trace_attention_required
            or role_readiness_attention_required
        )
        else "operating_clear"
    )
    if kpis["open_approval_count"]:
        next_action = "wait_for_user_approval"
    elif repair_attention_required and kpis["repair_next_command"]:
        next_action = kpis["repair_next_command"]
    elif trace_attention_required:
        next_action = trace_recommended_next_action or "run_ceo_trace_grade"
    elif role_readiness_attention_required:
        next_action = role_next_action or "review_role_queue"
    elif kpis["evidence_debt_count"]:
        next_action = evidence_debt_register.get("next_action")
    else:
        next_action = CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION
    return {
        "model": CEO_EXECUTIVE_KPIS_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "kpis": kpis,
        "validation_gate": validation_gate,
        "next_action": next_action,
        "next_action_scope": "executive_health_diagnostic_only",
        "dispatch_authority": "not_granted_by_executive_kpis",
        "runtime_authority_note": CEO_RUNTIME_AUTHORITY_NOTE,
        "guardrail": "Executive KPIs score operating-system health only. They do not validate, promote, or authorize runtime dispatch.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_executive_kpis(kpis: dict[str, Any]) -> str:
    values = kpis.get("kpis", {}) or {}
    lines = [
        "# Riskflow CEO Executive KPIs",
        "",
        f"Generated: {kpis.get('generated_at')}",
        f"Run: {kpis.get('run_id')}",
        f"Lab run: {kpis.get('lab_run_id')}",
        f"Status: {kpis.get('status')}",
        f"Attention next action: {kpis.get('next_action')}",
        f"Next action scope: {kpis.get('next_action_scope') or 'executive_health_diagnostic_only'}",
        f"Dispatch authority: {kpis.get('dispatch_authority') or 'not_granted_by_executive_kpis'}",
        f"Runtime authority note: {kpis.get('runtime_authority_note') or CEO_RUNTIME_AUTHORITY_NOTE}",
        "",
        "## KPIs",
        "",
    ]
    for key, value in values.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(kpis.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_executive_kpis(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    if not (root / "approval_queue.yaml").exists():
        run_ceo_approval_queue(diagnostic_options)
    if not (root / "evidence_debt_register.yaml").exists():
        run_ceo_evidence_debt_register(diagnostic_options)
    if not (root / "trace_grade.yaml").exists():
        run_ceo_trace_grade(options)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    champion_results = _load_yaml_if_exists(root / "champion_challenger_results.yaml")
    visual_queue = _load_yaml_if_exists(root / "champion_challenger_visual_review_queue.yaml")
    fresh_control_plan = _load_yaml_if_exists(root / "fresh_control_validation_plan.yaml")
    fresh_data_preflight = _load_yaml_if_exists(root / "fresh_data_preflight.yaml")
    frozen_plan = _load_yaml_if_exists(root / "frozen_candidate_validation_plan.yaml")
    fresh_withheld_contract = _load_yaml_if_exists(root / "fresh_withheld_validation_contract.yaml")
    fresh_withheld_execution = _load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml")
    trace_grade = _load_yaml_if_exists(root / "trace_grade.yaml")
    candidate_portfolio = build_ceo_candidate_portfolio(
        product_delta,
        champion_results,
        visual_queue,
        fresh_control_plan,
        fresh_data_preflight,
        frozen_plan,
        fresh_withheld_contract,
        fresh_withheld_execution,
    )
    capability_backlog = build_ceo_capability_backlog(
        capability_gap=_load_yaml_if_exists(root / "capability_gap.yaml"),
        trace_grade=trace_grade,
        visual_queue=visual_queue,
        fresh_data_preflight=fresh_data_preflight,
        frozen_plan=frozen_plan,
        fresh_withheld_contract=fresh_withheld_contract,
        fresh_withheld_execution=fresh_withheld_execution,
    )
    artifact = build_ceo_executive_kpis(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        approval_queue=_load_yaml_if_exists(root / "approval_queue.yaml"),
        evidence_debt_register=_load_yaml_if_exists(root / "evidence_debt_register.yaml"),
        candidate_portfolio=candidate_portfolio,
        capability_backlog=capability_backlog,
        trace_grade=trace_grade,
        fresh_withheld_execution=fresh_withheld_execution,
        promotion_proposal=_load_yaml_if_exists(root / "promotion_proposal.yaml"),
        blocker_stack=_load_yaml_if_exists(root / "blocker_stack.yaml"),
        incident_register=_load_yaml_if_exists(root / "operating_incident_register.yaml"),
        repair_plan=_load_yaml_if_exists(root / "repair_plan.yaml"),
        role_queue=_load_yaml_if_exists(root / "role_task_queue.yaml"),
    )
    path = root / "executive_kpis.yaml"
    report_path = root / "executive_kpis.md"
    atomic_write_yaml(path, artifact)
    atomic_write_text(report_path, render_ceo_executive_kpis(artifact))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "kpis": artifact,
        "paths": {"executive_kpis": path, "executive_kpis_report": report_path},
    }


def build_ceo_heartbeat_plan(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    interval_minutes: int,
    max_hours: float,
) -> dict[str, Any]:
    return {
        "model": CEO_HEARTBEAT_PLAN_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "interval_minutes": interval_minutes,
        "max_hours": max_hours,
        "status": "planned",
        "tick_command": f"PYTHONPATH=src python3 -m riskflow ceo heartbeat-tick --run-id {ceo_run_id} --apply",
        "stop_command": f"PYTHONPATH=src python3 -m riskflow ceo stop --run-id {ceo_run_id} --reason user_requested",
        "guardrail": "Heartbeat persistence records bounded ticks. It does not sleep, daemonize, or bypass approval gates.",
        "production_effect": "none",
    }


def render_ceo_heartbeat_plan(plan: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Riskflow CEO Heartbeat Plan",
            "",
            f"Generated: {plan.get('generated_at')}",
            f"Run: {plan.get('run_id')}",
            f"Lab run: {plan.get('lab_run_id')}",
            f"Interval minutes: {plan.get('interval_minutes')}",
            f"Max hours: {plan.get('max_hours')}",
            f"Tick command: {plan.get('tick_command')}",
            f"Stop command: {plan.get('stop_command')}",
            "",
            "## Guardrail",
            "",
            str(plan.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    ).rstrip() + "\n"


def run_ceo_heartbeat_plan(
    options: CeoOpsOptions,
    *,
    interval_minutes: int = 15,
    max_hours: float = 8.0,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    plan = build_ceo_heartbeat_plan(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        interval_minutes=interval_minutes,
        max_hours=max_hours,
    )
    path = root / "heartbeat_plan.yaml"
    report_path = root / "heartbeat_plan.md"
    atomic_write_yaml(path, plan)
    atomic_write_text(report_path, render_ceo_heartbeat_plan(plan))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "plan": plan,
        "paths": {"heartbeat_plan": path, "heartbeat_plan_report": report_path},
    }


def _heartbeat_journal_path(root: Path) -> Path:
    return root / "heartbeat_journal.jsonl"


def _append_heartbeat_journal(root: Path, entry: dict[str, Any]) -> Path:
    path = _heartbeat_journal_path(root)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_json_safe(entry), sort_keys=True) + "\n")
    return path


def _parse_utc_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_iso_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fresh_snapshot_temporal_blockers(
    *,
    snapshot_type: str,
    source_evidence_cutoff: str,
    snapshot_cutoff: str,
    active_assets: list[dict[str, Any]],
) -> list[str]:
    if snapshot_type != "fresh":
        return []
    blockers: list[str] = []
    source_date = _parse_iso_date(source_evidence_cutoff)
    snapshot_date = _parse_iso_date(snapshot_cutoff)
    if source_evidence_cutoff and source_date is None:
        blockers.append("invalid_source_evidence_cutoff")
    if snapshot_cutoff and snapshot_date is None:
        blockers.append("invalid_snapshot_cutoff")
    if source_date is not None and snapshot_date is not None and snapshot_date <= source_date:
        blockers.append("snapshot_cutoff_not_after_source_evidence_cutoff")
    latest_dates = [
        parsed
        for parsed in (_parse_iso_date(asset.get("latest_date", "")) for asset in active_assets or [])
        if parsed is not None
    ]
    if active_assets and not latest_dates:
        blockers.append("missing_active_asset_latest_dates")
    elif snapshot_date is not None and latest_dates and max(latest_dates) < snapshot_date:
        blockers.append("active_assets_older_than_snapshot_cutoff")
    return blockers


def build_heartbeat_plan_budget_status(plan: dict[str, Any]) -> dict[str, Any]:
    started_at = _parse_utc_datetime(plan.get("generated_at"))
    max_hours = None
    try:
        max_hours = float(plan.get("max_hours"))
    except (TypeError, ValueError):
        max_hours = None
    now = datetime.now(timezone.utc)
    elapsed_hours = ((now - started_at).total_seconds() / 3600.0) if started_at else 0.0
    budget_elapsed = bool(started_at and max_hours is not None and elapsed_hours >= max_hours)
    return {
        "status": "time_budget_elapsed" if budget_elapsed else "within_time_budget",
        "plan_present": bool(plan),
        "started_at": plan.get("generated_at", ""),
        "max_hours": max_hours,
        "elapsed_hours": round(elapsed_hours, 4),
        "budget_elapsed": budget_elapsed,
        "production_effect": "none",
    }


def run_ceo_heartbeat_tick(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo heartbeat-tick requires --apply")
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    heartbeat_result = run_ceo_heartbeat_status(options)
    trace_result = run_ceo_trace_grade(options)
    flight_result = run_ceo_flight_dashboard(options)
    operating_result = run_ceo_operating_dashboard(options)
    approval_result = run_ceo_approval_queue(options)
    kpi_result = run_ceo_executive_kpis(options)
    role_result = run_ceo_role_queue(options)
    allocator_result = run_ceo_portfolio_allocator(options)
    preflight_result = run_ceo_preflight_gate(options, enforce_memory_delta=True)
    heartbeat_plan = _load_yaml_if_exists(root / "heartbeat_plan.yaml")
    budget_status = build_heartbeat_plan_budget_status(heartbeat_plan)
    blockers: list[str] = []
    heartbeat_status = heartbeat_result["status"]
    trace_grade = trace_result["grade"]
    flight_dashboard = flight_result["dashboard"]
    flight_dashboard_blockers = {str(item) for item in flight_dashboard.get("blockers", []) or [] if item}
    approval_queue = approval_result["queue"]
    if heartbeat_status.get("stop_requested"):
        blockers.append("stop_requested")
    if heartbeat_status.get("true_blocker"):
        blockers.append("true_blocker")
    if trace_grade.get("verdict") == "fail":
        blockers.append("trace_grade_failed")
    if flight_dashboard.get("safe_to_continue") is False:
        blockers.append("flight_dashboard_not_safe")
    if int(approval_queue.get("pending_count", 0) or 0) > 0:
        blockers.append("pending_user_approval")
    if budget_status.get("budget_elapsed"):
        blockers.append("heartbeat_plan_time_budget_elapsed")
    if preflight_result["preflight_gate"].get("safe_to_execute") is False:
        for item in preflight_result["preflight_gate"].get("blockers", []) or []:
            blocker = str(item.get("blocker", ""))
            if blocker and blocker not in blockers:
                blockers.append(blocker)
    pre_action_warnings: list[str] = []
    trace_only_blockers = set(blockers)
    trace_repairable_blockers = (
        trace_only_blockers == {"trace_grade_failed"}
        or (
            trace_only_blockers == {"trace_grade_failed", "flight_dashboard_not_safe"}
            and flight_dashboard_blockers <= {"trace_grade_failed"}
        )
    )
    if trace_repairable_blockers:
        # Let execute-next decide whether the next bound action is a trace repair.
        pre_action_warnings.extend(sorted(trace_only_blockers))
        blockers = []
    action_result: dict[str, Any] = {}
    if blockers:
        tick_status = "blocked_before_action"
        action_status = "not_run"
    else:
        execute_result = run_ceo_execute_next(options)
        action_result = execute_result.get("action_result", {})
        action_status = str(action_result.get("status", ""))
        tick_status = "blocked_by_execute_next" if action_status == "blocked" else "executed_one_action"
        if tick_status == "blocked_by_execute_next":
            blockers = [
                str(item.get("blocker", ""))
                for item in action_result.get("preflight_blockers", []) or []
                if item.get("blocker")
            ]
    entry = {
        "model": CEO_HEARTBEAT_TICK_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": tick_status,
        "blockers": blockers,
        "pre_action_warnings": pre_action_warnings,
        "heartbeat_plan_budget": budget_status,
        "portfolio_selected_lane": (allocator_result.get("allocator", {}).get("selected_lane", {}) or {}).get("lane_id", ""),
        "portfolio_next_action": (allocator_result.get("allocator", {}).get("selected_lane", {}) or {}).get("next_action", ""),
        "action_status": action_status,
        "action_decision": action_result.get("decision", ""),
        "next_action": (
            "wait_for_user_approval"
            if "pending_user_approval" in blockers
            else "stop_time_budget_elapsed"
            if "heartbeat_plan_time_budget_elapsed" in blockers
            else heartbeat_status.get("next_recommended_action") or kpi_result["kpis"].get("next_action")
        ),
        "artifact_paths": {
            "heartbeat_status": heartbeat_result["paths"]["heartbeat_status"],
            "trace_grade": trace_result["paths"]["trace_grade"],
            "flight_dashboard": flight_result["paths"]["dashboard"],
            "operating_dashboard": operating_result["paths"]["dashboard"],
            "approval_queue": approval_result["paths"]["queue"],
            "executive_kpis": kpi_result["paths"]["executive_kpis"],
            "role_task_queue": role_result["paths"]["role_task_queue"],
            "portfolio_allocator": allocator_result["paths"]["portfolio_allocator"],
            "preflight_gate": preflight_result["paths"]["preflight_gate"],
            "heartbeat_plan": root / "heartbeat_plan.yaml",
        },
        "production_effect": "none",
    }
    journal_path = _append_heartbeat_journal(root, entry)
    state_path = root / "heartbeat_state.yaml"
    atomic_write_yaml(state_path, _json_safe(entry))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "tick": entry,
        "action_result": action_result,
        "paths": {"heartbeat_journal": journal_path, "heartbeat_state": state_path},
    }


def run_ceo_heartbeat_journal(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    journal_path = _heartbeat_journal_path(root)
    entries: list[dict[str, Any]] = []
    if journal_path.exists():
        with journal_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    entries.append(item)
    report_path = root / "heartbeat_journal.md"
    lines = [
        "# Riskflow CEO Heartbeat Journal",
        "",
        f"Run: {ceo_run_id}",
        f"Lab run: {lab_run_id}",
        f"Ticks: {len(entries)}",
        "",
        "## Ticks",
        "",
    ]
    for item in entries:
        lines.append(
            "- "
            f"{item.get('generated_at')} status={item.get('status')} "
            f"action={item.get('action_decision') or 'none'} "
            f"lane={item.get('portfolio_selected_lane') or 'none'} "
            f"blockers={item.get('blockers') or []}"
        )
    if not entries:
        lines.append("- none")
    atomic_write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "entries": entries,
        "paths": {"heartbeat_journal": journal_path, "heartbeat_journal_report": report_path},
    }


def build_ceo_role_registry(*, ceo_run_id: str, lab_run_id: str) -> dict[str, Any]:
    roles = [
        {
            "role_id": "research_director",
            "mission": "turn open research lanes into bounded, non-duplicative experiments",
        },
        {
            "role_id": "validation_referee",
            "mission": "challenge evidence quality, thresholds, lineage, and promotion readiness",
        },
        {
            "role_id": "product_translator",
            "mission": "translate validated evidence into chart-facing product roles without overclaiming",
        },
        {
            "role_id": "risk_officer",
            "mission": "enforce approval, production-change, stop-file, and no-progress guardrails",
        },
        {
            "role_id": "memory_editor",
            "mission": "curate durable Obsidian notes with exact artifact refs and no-proof language",
        },
        {
            "role_id": "data_steward",
            "mission": "audit data freshness, active assets, source boundaries, and snapshot authority",
        },
    ]
    return {
        "model": CEO_ROLE_REGISTRY_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "roles": roles,
        "production_effect": "none",
    }


def _role_for_debt(debt: dict[str, Any]) -> str:
    blocker = str(debt.get("blocker_type", ""))
    kind = str(debt.get("debt_kind", ""))
    if "data" in blocker or "snapshot" in blocker or "fresh_data" in kind:
        return "data_steward"
    if "visual" in blocker or "product" in blocker or "metric" in blocker:
        return "product_translator"
    if "trace" in blocker or "approval" in blocker:
        return "risk_officer"
    if "validation" in blocker or "validation" in kind or "threshold" in blocker:
        return "validation_referee"
    return "research_director"


def _ceo_role_result_resolution_mode(task: dict[str, Any]) -> str:
    if (
        str(task.get("owner_command", "")) == "wait_for_user_approval"
        or str(task.get("source_type", "")) == "approval"
    ):
        return "manual_gate_blocked_record"
    return "specialist_result_required"


def _ceo_role_result_command(*, ceo_run_id: str, task: dict[str, Any]) -> str:
    task_id = str(task.get("task_id", ""))
    if not task_id:
        return ""
    command = (
        "PYTHONPATH=src python3 -m riskflow ceo role-result "
        f"--run-id {ceo_run_id} --task-id {task_id} "
    )
    if _ceo_role_result_resolution_mode(task) == "manual_gate_blocked_record":
        return command + "--status blocked"
    return command + "--status complete --result-path <path-to-specialist-result.yaml>"


def _ceo_role_closure_command(*, ceo_run_id: str, task: dict[str, Any]) -> str:
    if _ceo_role_result_resolution_mode(task) == "manual_gate_blocked_record":
        return f"PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id {ceo_run_id}"
    return _ceo_role_result_command(ceo_run_id=ceo_run_id, task=task)


def _ceo_role_summary_closure_command(
    *,
    ceo_run_id: str,
    task_id: str,
    result_resolution_mode: str,
) -> str:
    if not task_id:
        return ""
    if result_resolution_mode == "manual_gate_blocked_record":
        approval_id = task_id.removeprefix("approval_")
        return _ceo_approval_record_command(ceo_run_id=ceo_run_id, approval_id=approval_id)
    return _ceo_role_result_command(
        ceo_run_id=ceo_run_id,
        task={"task_id": task_id, "result_resolution_mode": result_resolution_mode},
    )


def _ceo_role_queue_top_blocked_closure_command(*, ceo_run_id: str, role_queue: dict[str, Any]) -> str:
    existing = str(role_queue.get("top_blocked_closure_command", ""))
    if existing:
        return existing
    return _ceo_role_summary_closure_command(
        ceo_run_id=ceo_run_id,
        task_id=str(role_queue.get("top_blocked_task_id", "")),
        result_resolution_mode=str(role_queue.get("top_blocked_result_resolution_mode", "")),
    )


def _ceo_role_blocked_review_status(task: dict[str, Any]) -> str:
    if str(task.get("status", "")) != "blocked":
        return ""
    if str(task.get("result_resolution_mode", "")) == "manual_gate_blocked_record":
        return "manual_gate_blocked_record"
    if str(task.get("validation_status", "")) == "accepted":
        return "accepted_blocked_result"
    if str(task.get("validation_status", "")) == "provenance_drift":
        return "result_provenance_drift"
    if str(task.get("validation_status", "")) == "rejected":
        return "rejected_result"
    return "needs_specialist_result"


def _ceo_role_blocked_next_action(task: dict[str, Any]) -> str:
    review_status = _ceo_role_blocked_review_status(task)
    if review_status == "accepted_blocked_result":
        return (
            str(task.get("result_recommended_next_action", "")).strip()
            or str(task.get("owner_command", "")).strip()
            or "review_blocked_specialist_result_and_collect_required_evidence"
        )
    if review_status == "manual_gate_blocked_record":
        return str(task.get("closure_command", "")).strip() or "wait_for_user_approval"
    if review_status in {"result_provenance_drift", "rejected_result", "needs_specialist_result"}:
        return str(task.get("closure_command", "")).strip()
    return ""


def build_ceo_role_task_queue(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    evidence_debt_register: dict[str, Any],
    approval_queue: dict[str, Any],
    capability_backlog: dict[str, Any],
    role_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:

    tasks: list[dict[str, Any]] = []
    for debt in evidence_debt_register.get("debts", []) or []:
        debt_id = str(debt.get("debt_id") or _debt_slug(str(debt.get("candidate_id", "")), str(debt.get("debt_kind", ""))))
        tasks.append(
            {
                "task_id": f"debt_{debt_id}",
                "role_id": _role_for_debt(debt),
                "source_artifact": debt.get("blocking_artifact", ""),
                "source_type": "evidence_debt",
                "priority": debt.get("priority", 5),
                "summary": debt.get("evidence_required", ""),
                "owner_command": debt.get("owner_command") or debt.get("retire_action", ""),
                "status": "pending",
                "production_effect": "none",
            }
        )
    for item in approval_queue.get("pending_items", []) or []:
        approval_id = str(item.get("approval_id", ""))
        tasks.append(
            {
                "task_id": f"approval_{approval_id}",
                "approval_id": approval_id,
                "approval_record_command": item.get("approval_record_command")
                or _ceo_approval_record_command(ceo_run_id=ceo_run_id, approval_id=approval_id),
                "approval_apply_command": item.get("approval_apply_command")
                or _ceo_approval_apply_command(ceo_run_id=ceo_run_id, approval_id=approval_id),
                "role_id": "risk_officer",
                "source_artifact": item.get("source_artifact", ""),
                "source_type": "approval",
                "priority": 0,
                "summary": item.get("reason", ""),
                "owner_command": "wait_for_user_approval",
                "status": "pending",
                "production_effect": "none",
            }
        )
    for item in capability_backlog.get("items", []) or []:
        tasks.append(
            {
                "task_id": f"capability_{_debt_slug(str(item.get('kind', '')) + '_' + str(item.get('capability', '')))}",
                "role_id": "research_director",
                "source_artifact": "capability_backlog.yaml",
                "source_type": "capability_backlog",
                "priority": item.get("priority", 5),
                "summary": item.get("reason", ""),
                "owner_command": item.get("capability", ""),
                "status": "pending",
                "production_effect": "none",
            }
        )
    role_results = role_results or {}
    for task in tasks:
        task["result_resolution_mode"] = _ceo_role_result_resolution_mode(task)
        task["next_role_result_command"] = _ceo_role_result_command(ceo_run_id=ceo_run_id, task=task)
        task["requires_manual_gate"] = task["result_resolution_mode"] == "manual_gate_blocked_record"
        task["approval_authority"] = "user_only" if task["requires_manual_gate"] else "none"
        task["can_complete_with_specialist_artifact"] = not task["requires_manual_gate"]
        task["manual_gate_reason"] = str(task.get("summary", "")) if task["requires_manual_gate"] else ""
        task["closure_command"] = _ceo_role_closure_command(ceo_run_id=ceo_run_id, task=task)
        if task["requires_manual_gate"] and task.get("approval_record_command"):
            task["closure_command"] = task.get("approval_record_command", "")
        task_result = role_results.get(str(task.get("task_id", "")))
        if task_result:
            task["status"] = str(task_result.get("status", "recorded"))
            task["result_path"] = task_result.get("result_path", "")
            task["resolved_result_path"] = task_result.get("resolved_result_path", "")
            task["result_sha256"] = task_result.get("result_sha256", "")
            task["current_result_sha256"] = task_result.get("current_result_sha256", "")
            task["result_provenance_status"] = task_result.get("result_provenance_status", "")
            task["recorded_status"] = task_result.get("recorded_status", "")
            task["recorded_validation_status"] = task_result.get("recorded_validation_status", "")
            task["result_recorded_at"] = task_result.get("generated_at", "")
            task["validation_status"] = task_result.get("validation_status", "")
            task["validation_issues"] = task_result.get("validation_issues", [])
            task["result_finding"] = task_result.get("result_finding", "")
            task["result_recommended_next_action"] = task_result.get("result_recommended_next_action", "")
    tasks = sorted(tasks, key=lambda item: (int(item.get("priority", 99)), str(item.get("role_id", "")), str(item.get("task_id", ""))))
    pending_tasks = [task for task in tasks if str(task.get("status")) == "pending"]
    completed_tasks = [task for task in tasks if str(task.get("status")) == "complete"]
    blocked_tasks = [task for task in tasks if str(task.get("status")) == "blocked"]
    manual_pending_tasks = [
        task
        for task in pending_tasks
        if str(task.get("owner_command", "")) == "wait_for_user_approval"
        or str(task.get("source_type", "")) == "approval"
    ]
    autonomous_pending_tasks = [task for task in pending_tasks if task not in manual_pending_tasks]
    top_pending_task = pending_tasks[0] if pending_tasks else {}
    top_pending_task_id = str(top_pending_task.get("task_id", ""))
    top_pending_packet_path = (
        f"reports/ceo_runs/{ceo_run_id}/role_dispatch_packets/{_debt_slug(top_pending_task_id)}.md"
        if top_pending_task_id
        else ""
    )
    top_autonomous_task = autonomous_pending_tasks[0] if autonomous_pending_tasks else {}
    top_autonomous_task_id = str(top_autonomous_task.get("task_id", ""))
    top_autonomous_packet_path = (
        f"reports/ceo_runs/{ceo_run_id}/role_dispatch_packets/{_debt_slug(top_autonomous_task_id)}.md"
        if top_autonomous_task_id
        else ""
    )
    specialist_blocked_tasks = [
        task
        for task in blocked_tasks
        if str(task.get("result_resolution_mode", "")) != "manual_gate_blocked_record"
    ]
    top_blocked_task = (specialist_blocked_tasks or blocked_tasks or [{}])[0]
    top_blocked_task_id = str(top_blocked_task.get("task_id", ""))
    top_blocked_packet_path = (
        f"reports/ceo_runs/{ceo_run_id}/role_dispatch_packets/{_debt_slug(top_blocked_task_id)}.md"
        if top_blocked_task_id
        else ""
    )
    top_blocked_review_status = _ceo_role_blocked_review_status(top_blocked_task)
    top_blocked_next_action = _ceo_role_blocked_next_action(top_blocked_task)
    if pending_tasks and not autonomous_pending_tasks and manual_pending_tasks:
        next_action = "wait_for_user_approval_or_record_manual_gate_blocked"
    elif pending_tasks:
        next_action = "assign_top_role_task"
    elif blocked_tasks:
        next_action = "review_blocked_role_tasks"
    else:
        next_action = CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION
    return {
        "model": CEO_ROLE_TASK_QUEUE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "pending_role_tasks" if pending_tasks else "blocked_role_tasks" if blocked_tasks else "empty",
        "task_count": len(tasks),
        "pending_task_count": len(pending_tasks),
        "pending_manual_task_count": len(manual_pending_tasks),
        "pending_autonomous_task_count": len(autonomous_pending_tasks),
        "completed_task_count": len(completed_tasks),
        "blocked_task_count": len(blocked_tasks),
        "top_pending_task": top_pending_task,
        "top_pending_task_id": top_pending_task_id,
        "top_pending_role_id": top_pending_task.get("role_id", ""),
        "top_pending_owner_command": top_pending_task.get("owner_command", ""),
        "top_pending_packet_path": top_pending_packet_path,
        "top_pending_result_resolution_mode": top_pending_task.get("result_resolution_mode", ""),
        "top_pending_requires_manual_gate": top_pending_task.get("requires_manual_gate", ""),
        "top_pending_closure_command": top_pending_task.get("closure_command", ""),
        "top_autonomous_pending_task": top_autonomous_task,
        "top_autonomous_pending_task_id": top_autonomous_task_id,
        "top_autonomous_pending_role_id": top_autonomous_task.get("role_id", ""),
        "top_autonomous_pending_packet_path": top_autonomous_packet_path,
        "top_autonomous_pending_result_resolution_mode": top_autonomous_task.get("result_resolution_mode", ""),
        "top_autonomous_next_role_result_command": _ceo_role_result_command(ceo_run_id=ceo_run_id, task=top_autonomous_task),
        "top_blocked_task": top_blocked_task,
        "top_blocked_task_id": top_blocked_task_id,
        "top_blocked_role_id": top_blocked_task.get("role_id", ""),
        "top_blocked_packet_path": top_blocked_packet_path,
        "top_blocked_result_resolution_mode": top_blocked_task.get("result_resolution_mode", ""),
        "top_blocked_validation_status": top_blocked_task.get("validation_status", ""),
        "top_blocked_closure_command": top_blocked_task.get("closure_command", ""),
        "top_blocked_review_status": top_blocked_review_status,
        "top_blocked_result_path": top_blocked_task.get("resolved_result_path") or top_blocked_task.get("result_path", ""),
        "top_blocked_finding": top_blocked_task.get("result_finding", ""),
        "top_blocked_next_action": top_blocked_next_action,
        "next_role_dispatch_command": (
            f"PYTHONPATH=src python3 -m riskflow ceo role-dispatch --run-id {ceo_run_id}"
            if pending_tasks
            else ""
        ),
        "next_role_result_command": _ceo_role_result_command(ceo_run_id=ceo_run_id, task=top_pending_task),
        "tasks": tasks,
        "next_action": next_action,
        "guardrail": "Role tasks coordinate specialist review. They do not validate statistics or apply production changes.",
        "production_effect": "none",
    }


def render_ceo_role_task_queue(queue: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Role Task Queue",
        "",
        f"Generated: {queue.get('generated_at')}",
        f"Run: {queue.get('run_id')}",
        f"Lab run: {queue.get('lab_run_id')}",
        f"Status: {queue.get('status')}",
        f"Tasks: {queue.get('task_count')}",
        f"Pending: {queue.get('pending_task_count', 0)}",
        f"Pending manual: {queue.get('pending_manual_task_count', 0)}",
        f"Pending autonomous: {queue.get('pending_autonomous_task_count', 0)}",
        f"Completed: {queue.get('completed_task_count', 0)}",
        f"Blocked: {queue.get('blocked_task_count', 0)}",
        f"Top pending: {queue.get('top_pending_task_id') or 'none'}",
        f"Top pending role: {queue.get('top_pending_role_id') or 'none'}",
        f"Top pending owner command: {queue.get('top_pending_owner_command') or 'none'}",
        f"Top pending packet: {queue.get('top_pending_packet_path') or 'none'}",
        f"Top pending result mode: {queue.get('top_pending_result_resolution_mode') or 'none'}",
        f"Top pending requires manual gate: {queue.get('top_pending_requires_manual_gate')}",
        f"Top pending closure command: `{queue.get('top_pending_closure_command') or ''}`",
        f"Top autonomous pending: {queue.get('top_autonomous_pending_task_id') or 'none'}",
        f"Top autonomous role: {queue.get('top_autonomous_pending_role_id') or 'none'}",
        f"Top autonomous packet: {queue.get('top_autonomous_pending_packet_path') or 'none'}",
        f"Top autonomous result mode: {queue.get('top_autonomous_pending_result_resolution_mode') or 'none'}",
        f"Top autonomous role result command: `{queue.get('top_autonomous_next_role_result_command') or ''}`",
        f"Top blocked: {queue.get('top_blocked_task_id') or 'none'}",
        f"Top blocked role: {queue.get('top_blocked_role_id') or 'none'}",
        f"Top blocked packet: {queue.get('top_blocked_packet_path') or 'none'}",
        f"Top blocked result mode: {queue.get('top_blocked_result_resolution_mode') or 'none'}",
        f"Top blocked validation: {queue.get('top_blocked_validation_status') or 'none'}",
        f"Top blocked closure command: `{queue.get('top_blocked_closure_command') or ''}`",
        f"Top blocked review status: {queue.get('top_blocked_review_status') or 'none'}",
        f"Top blocked result path: {queue.get('top_blocked_result_path') or 'none'}",
        f"Top blocked next action: {queue.get('top_blocked_next_action') or 'none'}",
        f"Top blocked finding: {queue.get('top_blocked_finding') or 'none'}",
        f"Next role dispatch command: `{queue.get('next_role_dispatch_command') or ''}`",
        f"Next role result command: `{queue.get('next_role_result_command') or ''}`",
        f"Next action: {queue.get('next_action')}",
        "",
        "## Tasks",
        "",
    ]
    for task in queue.get("tasks", []) or []:
        lines.append(
            "- "
            f"p{task.get('priority')} {task.get('task_id')} "
            f"role={task.get('role_id')} source={task.get('source_type')} "
            f"status={task.get('status')}"
        )
    if not queue.get("tasks"):
        lines.append("- none")
    lines.extend(["", "## Guardrail", "", str(queue.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def _load_role_task_results(root: Path, *, source_root: Path | None = None) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for item in _read_jsonl_entries(root / "role_task_ledger.jsonl"):
        task_id = str(item.get("task_id", ""))
        if task_id:
            result_path = str(item.get("result_path", ""))
            resolved_path = _resolve_specialist_review_path(result_path, source_root=source_root, run_root=root)
            if resolved_path is not None and resolved_path.exists():
                result_payload = _load_yaml_if_exists(resolved_path)
                if result_payload:
                    item["result_finding"] = str(result_payload.get("finding", ""))
                    item["result_recommended_next_action"] = str(result_payload.get("recommended_next_action", ""))
            if (
                str(item.get("status", "")) == "complete"
                and str(item.get("validation_status", "")) == "accepted"
            ):
                issues = [str(issue) for issue in item.get("validation_issues", []) or []]
                expected_sha = str(item.get("result_sha256", ""))
                current_sha = _file_sha256(resolved_path) if resolved_path is not None and resolved_path.exists() else ""
                item["resolved_result_path"] = str(resolved_path or "")
                item["current_result_sha256"] = current_sha
                item["result_provenance_status"] = "pass"
                if resolved_path is None or not resolved_path.exists():
                    issues.append("result_artifact_missing_after_acceptance")
                elif not expected_sha:
                    issues.append("missing_result_sha256")
                elif current_sha != expected_sha:
                    issues.append("result_artifact_sha_mismatch")
                if issues != [str(issue) for issue in item.get("validation_issues", []) or []]:
                    item["recorded_status"] = item.get("status", "")
                    item["recorded_validation_status"] = item.get("validation_status", "")
                    item["status"] = "blocked"
                    item["validation_status"] = "provenance_drift"
                    item["validation_issues"] = issues
                    item["result_provenance_status"] = "drift"
            results[task_id] = item
    return results


def run_ceo_role_queue(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    if not (root / "evidence_debt_register.yaml").exists():
        run_ceo_evidence_debt_register(diagnostic_options)
    if not (root / "approval_queue.yaml").exists():
        run_ceo_approval_queue(diagnostic_options)
    if not (root / "capability_backlog.yaml").exists():
        run_ceo_capability_backlog(options)
    registry = build_ceo_role_registry(ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
    queue = build_ceo_role_task_queue(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        evidence_debt_register=_load_yaml_if_exists(root / "evidence_debt_register.yaml"),
        approval_queue=_load_yaml_if_exists(root / "approval_queue.yaml"),
        capability_backlog=_load_yaml_if_exists(root / "capability_backlog.yaml"),
        role_results=_load_role_task_results(root, source_root=options.source_root),
    )
    registry_path = root / "role_registry.yaml"
    queue_path = root / "role_task_queue.yaml"
    queue_report_path = root / "role_task_queue.md"
    status_path = root / "role_orchestration_status.yaml"
    atomic_write_yaml(registry_path, registry)
    atomic_write_yaml(queue_path, queue)
    atomic_write_text(queue_report_path, render_ceo_role_task_queue(queue))
    atomic_write_yaml(
        status_path,
        {
            "model": CEO_ROLE_TASK_QUEUE_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "status": queue.get("status"),
            "task_count": queue.get("task_count"),
            "pending_task_count": queue.get("pending_task_count"),
            "completed_task_count": queue.get("completed_task_count"),
            "blocked_task_count": queue.get("blocked_task_count"),
            "next_action": queue.get("next_action"),
            "production_effect": "none",
        },
    )
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "registry": registry,
        "queue": queue,
        "paths": {
            "role_registry": registry_path,
            "role_task_queue": queue_path,
            "role_task_queue_report": queue_report_path,
            "role_orchestration_status": status_path,
        },
    }


def _load_role_merge_receipts(root: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in sorted((root / "role_merge_receipts").glob("*.yaml")):
        payload = _load_yaml_if_exists(path)
        if payload:
            payload["_receipt_path"] = str(path)
            receipts.append(payload)
    single = _load_yaml_if_exists(root / "role_merge_receipt.yaml")
    if single:
        single["_receipt_path"] = str(root / "role_merge_receipt.yaml")
        receipts.append(single)
    return receipts


def build_ceo_org_progress_score(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    role_queue: dict[str, Any],
    role_task_ledger_entries: list[dict[str, Any]],
    role_merge_receipts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    role_merge_receipts = role_merge_receipts or []
    completed_entries = [entry for entry in role_task_ledger_entries if str(entry.get("status", "")) == "complete"]
    blocked_entries = [entry for entry in role_task_ledger_entries if str(entry.get("status", "")) == "blocked"]
    accepted_completed_entries = [
        entry
        for entry in completed_entries
        if str(entry.get("validation_status", "")) == "accepted"
    ]
    accepted_blocked_entries = [
        entry
        for entry in blocked_entries
        if str(entry.get("validation_status", "")) in {"accepted", "blocked_without_artifact"}
    ]
    merge_receipt_count = len(role_merge_receipts)
    pending_count = int(role_queue.get("pending_task_count", 0) or 0)
    blocked_count = int(role_queue.get("blocked_task_count", 0) or 0)
    completed_count = int(role_queue.get("completed_task_count", 0) or 0)
    completed_without_merge_count = max(0, len(accepted_completed_entries) - merge_receipt_count)
    decision_delta_refs = [
        str(entry.get("decision_delta", "") or entry.get("result_recommended_next_action", "") or entry.get("recommended_next_action", ""))
        for entry in accepted_completed_entries + accepted_blocked_entries
    ]
    decision_delta_count = len([item for item in decision_delta_refs if item.strip()])
    flags: list[str] = []
    if pending_count:
        flags.append("pending_role_work")
    if blocked_count:
        flags.append("blocked_role_work")
    if completed_without_merge_count:
        flags.append("accepted_completion_without_merge_receipt")
    if completed_count and decision_delta_count == 0:
        flags.append("completed_work_without_decision_delta")
    if int(role_queue.get("pending_manual_task_count", 0) or 0):
        flags.append("manual_gate_pending")
    score = 100
    score -= min(35, pending_count * 4)
    score -= min(35, blocked_count * 3)
    score -= min(20, completed_without_merge_count * 5)
    score -= 10 if completed_count and decision_delta_count == 0 else 0
    score = max(0, score)
    if pending_count or blocked_count:
        status = "org_work_open"
    elif completed_without_merge_count:
        status = "progress_unmerged"
    elif completed_count:
        status = "decision_progress_recorded"
    else:
        status = "no_role_work_visible"
    if pending_count:
        next_action = role_queue.get("next_role_dispatch_command") or "run_ceo_role_dispatch"
    elif blocked_count:
        next_action = role_queue.get("top_blocked_next_action") or "review_blocked_role_tasks"
    elif completed_without_merge_count:
        next_action = "design_role_merge_receipt_gate"
    else:
        next_action = CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION
    return {
        "model": CEO_ORG_PROGRESS_SCORE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "org_progress_score": score,
        "task_count": role_queue.get("task_count", 0),
        "pending_task_count": pending_count,
        "blocked_task_count": blocked_count,
        "completed_task_count": completed_count,
        "ledger_entry_count": len(role_task_ledger_entries),
        "accepted_completed_count": len(accepted_completed_entries),
        "accepted_blocked_count": len(accepted_blocked_entries),
        "merge_receipt_count": merge_receipt_count,
        "completed_without_merge_count": completed_without_merge_count,
        "decision_delta_count": decision_delta_count,
        "fake_progress_flags": flags,
        "top_blocked_task_id": role_queue.get("top_blocked_task_id", ""),
        "top_blocked_role_id": role_queue.get("top_blocked_role_id", ""),
        "top_blocked_next_action": role_queue.get("top_blocked_next_action", ""),
        "top_blocked_finding": role_queue.get("top_blocked_finding", ""),
        "next_action": next_action,
        "action_scope": "org_progress_diagnostic_only",
        "dispatch_authority": "not_granted_by_org_progress_score",
        "guardrail": (
            "Org progress score measures whether specialist work changes decisions. "
            "It does not merge work, approve gates, validate candidates, or change production behavior."
        ),
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_org_progress_score(scorecard: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Org Progress Score",
        "",
        f"Generated: {scorecard.get('generated_at')}",
        f"Run: {scorecard.get('run_id')}",
        f"Lab run: {scorecard.get('lab_run_id')}",
        f"Status: {scorecard.get('status')}",
        f"Org progress score: {scorecard.get('org_progress_score')}",
        f"Action scope: {scorecard.get('action_scope')}",
        f"Dispatch authority: {scorecard.get('dispatch_authority')}",
        f"Next action: {scorecard.get('next_action')}",
        "",
        "## Counters",
        "",
        f"- Tasks: {scorecard.get('task_count')}",
        f"- Pending: {scorecard.get('pending_task_count')}",
        f"- Blocked: {scorecard.get('blocked_task_count')}",
        f"- Completed: {scorecard.get('completed_task_count')}",
        f"- Ledger entries: {scorecard.get('ledger_entry_count')}",
        f"- Accepted completed: {scorecard.get('accepted_completed_count')}",
        f"- Accepted blocked: {scorecard.get('accepted_blocked_count')}",
        f"- Merge receipts: {scorecard.get('merge_receipt_count')}",
        f"- Completed without merge: {scorecard.get('completed_without_merge_count')}",
        f"- Decision deltas: {scorecard.get('decision_delta_count')}",
        "",
        "## Fake Progress Flags",
        "",
    ]
    flags = scorecard.get("fake_progress_flags", []) or []
    lines.extend(f"- {item}" for item in flags) if flags else lines.append("- none")
    lines.extend(
        [
            "",
            "## Top Blocked Work",
            "",
            f"- Task: {scorecard.get('top_blocked_task_id') or 'none'}",
            f"- Role: {scorecard.get('top_blocked_role_id') or 'none'}",
            f"- Next: {scorecard.get('top_blocked_next_action') or 'none'}",
            f"- Finding: {scorecard.get('top_blocked_finding') or 'none'}",
            "",
            str(scorecard.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_org_progress_score(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    role_result = run_ceo_role_queue(_with_ceo_context(options, context="diagnostic_refresh"))
    scorecard = build_ceo_org_progress_score(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        role_queue=role_result["queue"],
        role_task_ledger_entries=_read_jsonl_entries(root / "role_task_ledger.jsonl"),
        role_merge_receipts=_load_role_merge_receipts(root),
    )
    path = root / "org_progress_score.yaml"
    report_path = root / "org_progress_score.md"
    atomic_write_yaml(path, scorecard)
    atomic_write_text(report_path, render_ceo_org_progress_score(scorecard))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "org_progress_score": scorecard,
        "paths": {
            "org_progress_score": path,
            "org_progress_score_report": report_path,
            "role_task_queue": role_result["paths"]["role_task_queue"],
        },
    }


def _role_dispatch_question(role_id: str, task: dict[str, Any]) -> str:
    summary = str(task.get("summary", "")).strip() or "Review the assigned CEO operating task."
    if role_id == "validation_referee":
        return f"Assess whether the evidence requirement is actually satisfied or still blocks promotion: {summary}"
    if role_id == "product_translator":
        return f"Translate the evidence into a chart-facing product role without adding product claims: {summary}"
    if role_id == "risk_officer":
        return f"Identify the approval, stop, or production-authority constraint and whether it can be closed without user approval: {summary}"
    if role_id == "memory_editor":
        return f"Decide whether this finding needs durable Obsidian memory with exact artifact refs: {summary}"
    if role_id == "data_steward":
        return f"Audit the data or snapshot authority needed for this task: {summary}"
    return f"Turn this task into the next bounded research-infra action or blocker: {summary}"


def render_ceo_role_dispatch_packet(packet: dict[str, Any]) -> str:
    task = packet.get("task", {}) or {}
    result_resolution_mode = str(packet.get("result_resolution_mode", ""))
    next_role_result_command = str(packet.get("next_role_result_command", ""))
    lines = [
        "# Riskflow CEO Role Dispatch Packet",
        "",
        f"Generated: {packet.get('generated_at')}",
        f"Run: {packet.get('run_id')}",
        f"Lab run: {packet.get('lab_run_id')}",
        f"Task: {packet.get('task_id')}",
        f"Role: {packet.get('role_id')}",
        f"Priority: {task.get('priority')}",
        "",
        "## Question",
        "",
        str(packet.get("question", "")),
        "",
        "## Source Artifacts",
        "",
    ]
    for artifact in packet.get("source_artifacts", []) or []:
        lines.append(f"- {artifact}")
    lines.extend(
        [
            "",
            "## Authority",
            "",
            "- This packet is review-only.",
            "- Do not change production formulas, Pine defaults, scores, rankings, states, alerts, or product language.",
            "- Do not approve manual gates.",
            f"- Approval authority: {packet.get('approval_authority', 'none')}.",
            (
                "- If this is still awaiting user approval, record it as blocked; do not fabricate a specialist approval artifact."
                if result_resolution_mode == "manual_gate_blocked_record"
                else "- Return a structured result artifact path that `ceo role-result` can record."
            ),
            "",
            "## Result Recording",
            "",
            f"Resolution mode: {result_resolution_mode or 'unknown'}",
            f"Requires manual gate: {packet.get('requires_manual_gate')}",
            f"Closure command: `{packet.get('closure_command') or ''}`",
            f"Next role result command: `{next_role_result_command}`",
            "",
            "## Expected Result Schema",
            "",
            "```yaml",
            "model: riskflow_ceo_specialist_result_v0",
            f"task_id: {packet.get('task_id')}",
            f"role_id: {packet.get('role_id')}",
            "status: complete|blocked",
            "finding: <plain English finding>",
            "evidence_refs:",
            "  - <exact YAML/CSV/MD path>",
            "recommended_next_action: <bounded command or manual gate>",
            "product_language_allowed: false",
            "production_effect: none",
            "promotion_authority: none",
            "```",
            "",
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_ceo_role_dispatch(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    role_queue: dict[str, Any],
    packet_dir: Path,
) -> dict[str, Any]:
    packet_dir.mkdir(parents=True, exist_ok=True)
    packets: list[dict[str, Any]] = []
    top_pending_task_id = str(role_queue.get("top_pending_task_id", ""))
    top_autonomous_task_id = str(role_queue.get("top_autonomous_pending_task_id", ""))
    top_packet: dict[str, Any] = {}
    top_autonomous_packet: dict[str, Any] = {}
    for task in role_queue.get("tasks", []) or []:
        if str(task.get("status", "")) != "pending":
            continue
        task_id = str(task.get("task_id", "unknown_task"))
        role_id = str(task.get("role_id", "research_director"))
        packet_path = packet_dir / f"{_debt_slug(task_id)}.md"
        packet = {
            "model": CEO_ROLE_DISPATCH_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "task_id": task_id,
            "role_id": role_id,
            "question": _role_dispatch_question(role_id, task),
            "task": task,
            "result_resolution_mode": _ceo_role_result_resolution_mode(task),
            "next_role_result_command": _ceo_role_result_command(ceo_run_id=ceo_run_id, task=task),
            "requires_manual_gate": bool(task.get("requires_manual_gate")),
            "approval_id": task.get("approval_id", ""),
            "approval_authority": task.get("approval_authority", "none"),
            "manual_gate_reason": task.get("manual_gate_reason", ""),
            "can_complete_with_specialist_artifact": task.get("can_complete_with_specialist_artifact", True),
            "closure_command": task.get("closure_command", ""),
            "source_artifacts": [
                "role_task_queue.yaml",
                str(task.get("source_artifact", "")),
                str(task.get("owner_command", "")),
            ],
            "packet_path": str(packet_path),
            "allowed_authority": "review_only",
            "product_language_allowed": False,
            "production_effect": "none",
            "promotion_authority": "none",
        }
        atomic_write_text(packet_path, render_ceo_role_dispatch_packet(packet))
        packets.append(packet)
        if task_id == top_pending_task_id:
            top_packet = packet
        if task_id == top_autonomous_task_id:
            top_autonomous_packet = packet
    return {
        "model": CEO_ROLE_DISPATCH_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "packets_written" if packets else "no_pending_role_tasks",
        "packet_count": len(packets),
        "packet_dir": str(packet_dir),
        "top_task_id": top_packet.get("task_id", ""),
        "top_role_id": top_packet.get("role_id", ""),
        "top_packet_path": top_packet.get("packet_path", ""),
        "top_result_resolution_mode": top_packet.get("result_resolution_mode", ""),
        "top_requires_manual_gate": top_packet.get("requires_manual_gate", ""),
        "top_closure_command": top_packet.get("closure_command", ""),
        "top_autonomous_task_id": top_autonomous_packet.get("task_id", ""),
        "top_autonomous_role_id": top_autonomous_packet.get("role_id", ""),
        "top_autonomous_packet_path": top_autonomous_packet.get("packet_path", ""),
        "top_autonomous_result_resolution_mode": top_autonomous_packet.get("result_resolution_mode", ""),
        "top_autonomous_next_role_result_command": str(top_autonomous_packet.get("next_role_result_command", "")),
        "next_role_result_command": str(top_packet.get("next_role_result_command", "")),
        "packets": packets,
        "guardrail": "Role dispatch packets are review-only prompts for specialist work. They do not approve gates or mutate product behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_role_dispatch(dispatch: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Role Dispatch",
        "",
        f"Generated: {dispatch.get('generated_at')}",
        f"Run: {dispatch.get('run_id')}",
        f"Lab run: {dispatch.get('lab_run_id')}",
        f"Status: {dispatch.get('status')}",
        f"Packets: {dispatch.get('packet_count')}",
        f"Packet dir: {dispatch.get('packet_dir')}",
        f"Top task: {dispatch.get('top_task_id') or 'none'}",
        f"Top role: {dispatch.get('top_role_id') or 'none'}",
        f"Top packet: {dispatch.get('top_packet_path') or 'none'}",
        f"Top result mode: {dispatch.get('top_result_resolution_mode') or 'none'}",
        f"Top requires manual gate: {dispatch.get('top_requires_manual_gate')}",
        f"Top closure command: `{dispatch.get('top_closure_command') or ''}`",
        f"Top autonomous task: {dispatch.get('top_autonomous_task_id') or 'none'}",
        f"Top autonomous role: {dispatch.get('top_autonomous_role_id') or 'none'}",
        f"Top autonomous packet: {dispatch.get('top_autonomous_packet_path') or 'none'}",
        f"Top autonomous result mode: {dispatch.get('top_autonomous_result_resolution_mode') or 'none'}",
        f"Top autonomous role result command: `{dispatch.get('top_autonomous_next_role_result_command') or ''}`",
        f"Next role result command: `{dispatch.get('next_role_result_command') or ''}`",
        "",
        "## Packets",
        "",
    ]
    for packet in dispatch.get("packets", []) or []:
        lines.append(
            "- "
            f"{packet.get('task_id')} role={packet.get('role_id')} "
            f"path={packet.get('packet_path')}"
        )
    if not dispatch.get("packets"):
        lines.append("- none")
    lines.extend(["", str(dispatch.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_role_dispatch(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    role_result = run_ceo_role_queue(_with_ceo_context(options, context="diagnostic_refresh"))
    packet_dir = root / "role_dispatch_packets"
    dispatch = build_ceo_role_dispatch(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        role_queue=role_result["queue"],
        packet_dir=packet_dir,
    )
    path = root / "role_dispatch.yaml"
    report_path = root / "role_dispatch.md"
    atomic_write_yaml(path, dispatch)
    atomic_write_text(report_path, render_ceo_role_dispatch(dispatch))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "role_dispatch": dispatch,
        "paths": {
            "role_dispatch": path,
            "role_dispatch_report": report_path,
            "role_task_queue": role_result["paths"]["role_task_queue"],
            "packet_dir": packet_dir,
        },
    }


def _find_role_task(queue: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    for task in queue.get("tasks", []) or []:
        if str(task.get("task_id", "")) == task_id:
            return task
    return None


def validate_ceo_specialist_result(
    *,
    task: dict[str, Any],
    status: str,
    result_path: str,
    source_root: Path | None,
    run_root: Path | None,
) -> dict[str, Any]:
    task_id = str(task.get("task_id", ""))
    role_id = str(task.get("role_id", ""))
    normalized_status = status.strip().lower()
    issues: list[str] = []
    result_resolution_mode = _ceo_role_result_resolution_mode(task)
    requires_manual_gate = result_resolution_mode == "manual_gate_blocked_record"
    if requires_manual_gate and normalized_status == "complete":
        issues.append("manual_gate_cannot_complete_as_specialist_result")
    resolved_path = _resolve_specialist_review_path(result_path, source_root=source_root, run_root=run_root)
    result_payload: dict[str, Any] = {}
    result_sha256 = ""
    result_artifact_exists = False

    if not result_path:
        if normalized_status == "blocked":
            return {
                "status": "blocked_without_artifact",
                "valid": True,
                "issues": [],
                "task_id": task_id,
                "role_id": role_id,
                "result_path": "",
                "result_resolution_mode": result_resolution_mode,
                "requires_manual_gate": requires_manual_gate,
                "can_complete_with_specialist_artifact": not requires_manual_gate,
                "resolved_result_path": "",
                "result_sha256": "",
                "result_artifact_exists": False,
                "production_effect": "none",
            }
        issues.append("missing_result_path")
    elif resolved_path is None or not resolved_path.exists():
        issues.append("missing_result_artifact")
    else:
        result_payload = _load_yaml_if_exists(resolved_path)
        result_sha256 = _file_sha256(resolved_path)
        result_artifact_exists = True
        if not result_payload:
            issues.append("unreadable_result_artifact")

    if result_payload:
        if str(result_payload.get("model", "")) != "riskflow_ceo_specialist_result_v0":
            issues.append("wrong_model")
        if str(result_payload.get("task_id", "")) != task_id:
            issues.append("task_id_mismatch")
        if str(result_payload.get("role_id", "")) != role_id:
            issues.append("role_id_mismatch")
        if str(result_payload.get("status", "")).strip().lower() != normalized_status:
            issues.append("status_mismatch")
        if str(result_payload.get("production_effect", "none")) not in {"", "none"}:
            issues.append("non_none_production_effect")
        if result_payload.get("product_language_allowed") is not False:
            issues.append("product_language_not_explicitly_false")
        if str(result_payload.get("promotion_authority", "none")) not in {"", "none"}:
            issues.append("promotion_authority_not_none")
        if normalized_status == "complete":
            evidence_refs = result_payload.get("evidence_refs", [])
            if not isinstance(evidence_refs, list) or not any(str(ref).strip() for ref in evidence_refs):
                issues.append("missing_evidence_refs")
            if not str(result_payload.get("finding", "")).strip():
                issues.append("missing_finding")
            if not str(result_payload.get("recommended_next_action", "")).strip():
                issues.append("missing_recommended_next_action")

    valid = not issues
    return {
        "status": "accepted" if valid else "rejected",
        "valid": valid,
        "issues": issues,
        "task_id": task_id,
        "role_id": role_id,
        "result_path": str(resolved_path or result_path),
        "result_resolution_mode": result_resolution_mode,
        "requires_manual_gate": requires_manual_gate,
        "can_complete_with_specialist_artifact": not requires_manual_gate,
        "result_status": str(result_payload.get("status", "")) if result_payload else "",
        "result_model": str(result_payload.get("model", "")) if result_payload else "",
        "result_finding": str(result_payload.get("finding", "")) if result_payload else "",
        "result_recommended_next_action": str(result_payload.get("recommended_next_action", "")) if result_payload else "",
        "resolved_result_path": str(resolved_path or ""),
        "result_sha256": result_sha256,
        "result_artifact_exists": result_artifact_exists,
        "production_effect": "none",
    }


def run_ceo_role_result(
    options: CeoOpsOptions,
    *,
    task_id: str,
    status: str,
    result_path: str = "",
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    normalized_status = status.strip().lower()
    if normalized_status not in {"complete", "blocked"}:
        raise ValueError("role-result status must be complete or blocked")
    queue_before = run_ceo_role_queue(_with_ceo_context(options, context="diagnostic_refresh"))["queue"]
    task = _find_role_task(queue_before, task_id)
    if task is None:
        validation = {
            "model": CEO_ROLE_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "task_id": task_id,
            "status": "rejected",
            "valid": False,
            "issues": ["unknown_task_id"],
            "production_effect": "none",
        }
        validation_path = root / "role_result_validation.yaml"
        atomic_write_yaml(validation_path, validation)
        raise ValueError(f"role-result task_id is not pending or known: {task_id}")
    if str(task.get("status", "")) != "pending":
        validation = {
            "model": CEO_ROLE_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "task_id": task_id,
            "status": "rejected",
            "valid": False,
            "issues": ["task_not_pending"],
            "current_task_status": task.get("status", ""),
            "production_effect": "none",
        }
        validation_path = root / "role_result_validation.yaml"
        atomic_write_yaml(validation_path, validation)
        raise ValueError(f"role-result task is not pending: {task_id}")
    validation = validate_ceo_specialist_result(
        task=task,
        status=normalized_status,
        result_path=result_path,
        source_root=options.source_root,
        run_root=root,
    )
    validation = {
        "model": CEO_ROLE_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        **validation,
    }
    validation_path = root / "role_result_validation.yaml"
    atomic_write_yaml(validation_path, validation)
    if not validation.get("valid"):
        issues = ", ".join(validation.get("issues", []) or ["invalid_result"])
        raise ValueError(f"role-result validation failed for {task_id}: {issues}")
    entry = {
        "model": CEO_ROLE_RESULT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "task_id": task_id,
        "status": normalized_status,
        "result_path": result_path,
        "resolved_result_path": validation.get("resolved_result_path", ""),
        "result_sha256": validation.get("result_sha256", ""),
        "result_artifact_exists": validation.get("result_artifact_exists", False),
        "result_provenance_status": "pass" if normalized_status == "complete" else "not_required",
        "validation_status": validation.get("status"),
        "validation_issues": validation.get("issues", []),
        "result_finding": validation.get("result_finding", ""),
        "result_recommended_next_action": validation.get("result_recommended_next_action", ""),
        "result_resolution_mode": validation.get("result_resolution_mode", _ceo_role_result_resolution_mode(task)),
        "requires_manual_gate": validation.get("requires_manual_gate", False),
        "can_complete_with_specialist_artifact": validation.get("can_complete_with_specialist_artifact", True),
        "production_effect": "none",
    }
    ledger_path = root / "role_task_ledger.jsonl"
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_json_safe(entry), sort_keys=True) + "\n")
    queue_result = run_ceo_role_queue(options)
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "result": entry,
        "queue": queue_result["queue"],
        "paths": {
            "role_task_ledger": ledger_path,
            "role_task_queue": queue_result["paths"]["role_task_queue"],
            "role_orchestration_status": queue_result["paths"]["role_orchestration_status"],
            "role_result_validation": validation_path,
        },
    }


def build_ceo_capability_backlog_artifact(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    backlog: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "model": CEO_CAPABILITY_BACKLOG_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "open_items" if backlog else "empty",
        "backlog_count": len(backlog),
        "items": backlog,
        "next_action": "work_top_capability_item" if backlog else CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION,
        "guardrail": "Capability backlog items are research-infrastructure work only. They do not change production formulas.",
        "production_effect": "none",
    }


def render_ceo_capability_backlog(backlog: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Capability Backlog",
        "",
        f"Generated: {backlog.get('generated_at')}",
        f"Run: {backlog.get('run_id')}",
        f"Lab run: {backlog.get('lab_run_id')}",
        f"Status: {backlog.get('status')}",
        f"Items: {backlog.get('backlog_count')}",
        f"Next action: {backlog.get('next_action')}",
        "",
        "## Items",
        "",
    ]
    for item in backlog.get("items", []) or []:
        lines.append(
            "- "
            f"p{item.get('priority')} {item.get('kind')} "
            f"capability={item.get('capability')} reason={item.get('reason')}"
        )
    if not backlog.get("items"):
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            str(backlog.get("guardrail")),
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_capability_backlog(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "trace_grade.yaml").exists():
        run_ceo_trace_grade(options)
    backlog_items = build_ceo_capability_backlog(
        capability_gap=_load_yaml_if_exists(root / "capability_gap.yaml"),
        trace_grade=_load_yaml_if_exists(root / "trace_grade.yaml"),
        visual_queue=_load_yaml_if_exists(root / "champion_challenger_visual_review_queue.yaml"),
        fresh_data_preflight=_load_yaml_if_exists(root / "fresh_data_preflight.yaml"),
        frozen_plan=_load_yaml_if_exists(root / "frozen_candidate_validation_plan.yaml"),
        fresh_withheld_contract=_load_yaml_if_exists(root / "fresh_withheld_validation_contract.yaml"),
        fresh_withheld_execution=_load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml"),
    )
    backlog = build_ceo_capability_backlog_artifact(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        backlog=backlog_items,
    )
    path = root / "capability_backlog.yaml"
    report_path = root / "capability_backlog.md"
    atomic_write_yaml(path, backlog)
    atomic_write_text(report_path, render_ceo_capability_backlog(backlog))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "backlog": backlog,
        "paths": {"backlog": path, "backlog_report": report_path},
    }


def _legal_decisions_from_next_actions(next_actions: list[Any]) -> set[str]:
    normalized = {
        "broaden_hypothesis_source" if str(item) == "broaden_product_candidate_source" else str(item)
        for item in next_actions
        if str(item).strip()
    }
    legal: set[str] = set()
    for item in normalized:
        if item in {
            "run_champion_challenger",
            "run_fresh_or_control_validation_for_promising_shadow_challengers",
            "continue_governed_research",
            "patch_research_infra",
            "broaden_hypothesis_source",
            "request_fresh_data",
            "run_frozen_candidate_validation",
            "run_frozen_validation_executor",
            "run_frozen_validation_rerun",
            "run_fresh_withheld_validation_contract",
            "repair_fresh_withheld_contract_inputs",
            "run_fresh_withheld_snapshot_manifest",
            "run_fresh_withheld_validation_executor",
            "import_or_curate_fresh_ohlcv_data",
            "resolve_ceo_self_audit_intervention",
            "stop",
        }:
            legal.add("run_frozen_candidate_validation" if item == "repair_fresh_withheld_contract_inputs" else item)
        elif item in {
            "wait_for_user_approval",
            "clear_stop_request_after_user_approval",
            "write_promotion_proposal_and_wait_for_user_approval",
        }:
            legal.add("approval_apply")
        elif item.startswith("build_"):
            legal.add("patch_research_infra")
    return legal


CEO_LEGACY_TRANSITION_ALIASES: dict[str, set[str]] = {
    "run_fresh_or_control_validation_for_promising_shadow_challengers": {
        "run_fresh_withheld_validation_contract",
    },
}


def _has_current_transition_evidence(action: dict[str, Any]) -> bool:
    return bool(action.get("dispatch_receipt", {}) or action.get("transition_policy_version"))


def _is_legacy_transition_gap(
    *,
    previous: dict[str, Any],
    current: dict[str, Any],
    legal: set[str],
    observed: str,
) -> bool:
    if not legal or observed in legal:
        return False
    if _has_current_transition_evidence(previous) or _has_current_transition_evidence(current):
        return False
    if str(previous.get("production_effect", "")) not in {"", "none"}:
        return False
    if str(current.get("production_effect", "")) not in {"", "none"}:
        return False
    if (
        observed == str(previous.get("decision", ""))
        and str(current.get("action_taken", "")) == str(previous.get("action_taken", ""))
    ):
        return True
    for previous_next_action in previous.get("next_allowed_actions", []) or []:
        allowed_aliases = CEO_LEGACY_TRANSITION_ALIASES.get(str(previous_next_action), set())
        if observed in allowed_aliases:
            return True
    return False


def _build_ceo_state_transition_checks(action_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for index, previous in enumerate(action_entries[:-1]):
        current = action_entries[index + 1]
        legal = _legal_decisions_from_next_actions(previous.get("next_allowed_actions", []) or [])
        observed = str(current.get("decision", ""))
        legacy_policy_gap = _is_legacy_transition_gap(
            previous=previous,
            current=current,
            legal=legal,
            observed=observed,
        )
        if not legal:
            status = "not_evaluable"
            reason = "previous action did not declare next_allowed_actions"
        elif observed in legal:
            status = "pass"
            reason = "observed decision is allowed by previous action"
        elif legacy_policy_gap:
            status = "legacy_policy_gap"
            reason = "legacy action lacks immutable dispatch or policy evidence and matches known old transition policy; preserve as drift, not current unsafe transition"
        else:
            status = "fail"
            reason = "observed decision is not allowed by previous action"
        checks.append(
            {
                "index": index,
                "previous_decision": previous.get("decision", ""),
                "previous_status": previous.get("status", ""),
                "previous_next_allowed_actions": previous.get("next_allowed_actions", []) or [],
                "legal_next_decisions": sorted(legal),
                "observed_next_decision": observed,
                "status": status,
                "reason": reason,
                "legacy_policy_gap": legacy_policy_gap,
                "production_effect": "none",
            }
        )
    return checks


def _build_dispatch_receipt_checks(
    *,
    action_entries: list[dict[str, Any]],
    root: Path,
    ceo_run_id: str,
    lab_run_id: str,
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for index, action in enumerate(action_entries, start=1):
        failures: list[str] = []
        ref = action.get("dispatch_receipt", {}) or {}
        receipt_path = _resolve_report_ref_path(root, ref.get("path", ""))
        if not ref:
            if _has_current_transition_evidence(action):
                checks.append(
                    {
                        "action_index": index,
                        "decision": action.get("decision", ""),
                        "action_taken": action.get("action_taken", ""),
                        "status": "fail",
                        "receipt_path": "",
                        "failures": ["missing_action_dispatch_receipt_ref"],
                        "production_effect": "none",
                    }
                )
                continue
            checks.append(
                {
                    "action_index": index,
                    "decision": action.get("decision", ""),
                    "action_taken": action.get("action_taken", ""),
                    "status": "not_required",
                    "receipt_path": "",
                    "failures": [],
                    "production_effect": "none",
                }
            )
            continue
        elif not receipt_path.exists():
            failures.append("action_dispatch_receipt_missing")
        else:
            receipt = _load_yaml_if_exists(receipt_path)
            if str(ref.get("sha256", "")) != _file_sha256(receipt_path):
                failures.append("action_dispatch_receipt_hash_mismatch")
            if receipt.get("model") != CEO_DISPATCH_RECEIPT_MODEL:
                failures.append("action_dispatch_receipt_model_mismatch")
            if str(receipt.get("run_id", "")) != ceo_run_id:
                failures.append("action_dispatch_receipt_run_mismatch")
            if str(receipt.get("lab_run_id", "")) != lab_run_id:
                failures.append("action_dispatch_receipt_lab_run_mismatch")
            if str(receipt.get("decision", "")) != str(action.get("decision", "")):
                failures.append("action_dispatch_receipt_decision_mismatch")
            if receipt_path.name == "dispatch_receipt.yaml" or receipt_path.parent.name != "dispatch_receipts":
                failures.append("action_dispatch_receipt_not_immutable_snapshot")
        checks.append(
            {
                "action_index": index,
                "decision": action.get("decision", ""),
                "action_taken": action.get("action_taken", ""),
                "status": "pass" if not failures else "fail",
                "receipt_path": str(receipt_path) if str(ref.get("path", "")) else "",
                "failures": failures,
                "production_effect": "none",
            }
        )
    return checks


def _build_repair_apply_checks(*, repair_apply_entries: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for index, entry in enumerate(repair_apply_entries, start=1):
        failures: list[str] = []
        paths = entry.get("paths", {}) or {}
        for label in ["before_repair_plan_snapshot", "after_repair_plan_snapshot"]:
            snapshot_ref = str(paths.get(label, ""))
            snapshot_path = _resolve_report_ref_path(root, snapshot_ref)
            expected_sha = str(entry.get(f"{label}_sha256", ""))
            if not snapshot_ref:
                failures.append(f"missing_{label}_ref")
            elif not snapshot_path.exists():
                failures.append(f"missing_{label}")
            elif snapshot_path.parent.name != "repair_apply_plans":
                failures.append(f"{label}_not_immutable_snapshot")
            elif expected_sha != _file_sha256(snapshot_path):
                failures.append(f"{label}_hash_mismatch")
        if str(entry.get("production_effect", "")) not in {"", "none"}:
            failures.append("repair_apply_non_none_production_effect")
        if entry.get("product_language_allowed") not in {False, None, ""}:
            failures.append("repair_apply_product_language_allowed")
        if str(entry.get("promotion_authority", "")) not in {"", "none"}:
            failures.append("repair_apply_promotion_authority_not_none")
        missing_snapshot_refs = {
            "missing_before_repair_plan_snapshot_ref",
            "missing_after_repair_plan_snapshot_ref",
        }
        legacy_no_action_snapshot_gap = (
            set(failures) == missing_snapshot_refs
            and entry.get("action_attempted") is False
            and entry.get("action_executed") is False
            and str(entry.get("status", "")).startswith("blocked_")
            and str(entry.get("production_effect", "")) in {"", "none"}
        )
        status = "legacy_snapshot_gap" if legacy_no_action_snapshot_gap else ("pass" if not failures else "fail")
        checks.append(
            {
                "repair_apply_index": index,
                "status": status,
                "repair_apply_status": entry.get("status", ""),
                "repair_key": entry.get("repair_key", ""),
                "before_repair_plan_snapshot": str(paths.get("before_repair_plan_snapshot", "")),
                "after_repair_plan_snapshot": str(paths.get("after_repair_plan_snapshot", "")),
                "legacy_snapshot_gap": legacy_no_action_snapshot_gap,
                "failures": failures,
                "production_effect": "none",
            }
        )
    return checks


def _build_operator_step_checks(*, operator_step_entries: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for index, entry in enumerate(operator_step_entries, start=1):
        failures: list[str] = []
        paths = entry.get("paths", {}) or {}
        for label in ["before_action_board_snapshot", "after_action_board_snapshot"]:
            snapshot_path = _resolve_report_ref_path(root, paths.get(label, ""))
            expected_sha = str(entry.get(f"{label}_sha256", ""))
            if not str(paths.get(label, "")):
                failures.append(f"missing_{label}_ref")
            elif not snapshot_path.exists():
                failures.append(f"missing_{label}")
            elif expected_sha != _file_sha256(snapshot_path):
                failures.append(f"{label}_hash_mismatch")
        binding_action_ref = str(paths.get("binding_action_result", ""))
        binding_action_path = _resolve_report_ref_path(root, binding_action_ref)
        expected_binding_sha = str(entry.get("binding_action_result_sha256", ""))
        if entry.get("action_executed") is True:
            if not binding_action_ref:
                failures.append("missing_operator_step_binding_action_result_ref")
            elif not binding_action_path.exists():
                failures.append("missing_operator_step_binding_action_result")
            elif expected_binding_sha != _file_sha256(binding_action_path):
                failures.append("operator_step_binding_action_result_hash_mismatch")
        if str(entry.get("production_effect", "")) not in {"", "none"}:
            failures.append("operator_step_non_none_production_effect")
        if entry.get("product_language_allowed") not in {False, None, ""}:
            failures.append("operator_step_product_language_allowed")
        if str(entry.get("promotion_authority", "")) not in {"", "none"}:
            failures.append("operator_step_promotion_authority_not_none")
        checks.append(
            {
                "operator_step_index": index,
                "status": "pass" if not failures else "fail",
                "operator_step_status": entry.get("status", ""),
                "before_action_board_snapshot": str(paths.get("before_action_board_snapshot", "")),
                "after_action_board_snapshot": str(paths.get("after_action_board_snapshot", "")),
                "binding_action_result": binding_action_ref,
                "failures": failures,
                "production_effect": "none",
            }
        )
    return checks


def build_ceo_replay(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    root: Path,
) -> dict[str, Any]:
    action_entries = _read_jsonl_entries(root / "ceo_action_ledger.jsonl")
    heartbeat_entries = _read_jsonl_entries(root / "heartbeat_journal.jsonl")
    approval_entries = _read_jsonl_entries(root / "approval_decision_ledger.jsonl")
    role_entries = _read_jsonl_entries(root / "role_task_ledger.jsonl")
    repair_apply_entries = _read_jsonl_entries(root / "repair_apply_ledger.jsonl")
    operator_step_entries = _read_jsonl_entries(root / "operator_step_ledger.jsonl")
    latest_binding_action = _load_yaml_if_exists(root / "binding_action_result.yaml")
    used_binding_fallback = False
    if not action_entries and latest_binding_action:
        action_entries = [latest_binding_action]
        used_binding_fallback = True
    key_artifacts = {
        "ceo_action_ledger": root / "ceo_action_ledger.jsonl",
        "heartbeat_journal": root / "heartbeat_journal.jsonl",
        "approval_decision_ledger": root / "approval_decision_ledger.jsonl",
        "role_task_ledger": root / "role_task_ledger.jsonl",
        "repair_apply_ledger": root / "repair_apply_ledger.jsonl",
        "operator_step_ledger": root / "operator_step_ledger.jsonl",
        "heartbeat_status": root / "heartbeat_status.yaml",
        "trace_grade": root / "trace_grade.yaml",
        "guardrail_audit": root / "guardrail_audit.yaml",
        "preflight_gate": root / "preflight_gate.yaml",
        "dispatch_receipt": root / "dispatch_receipt.yaml",
        "action_contract": root / "action_contract.yaml",
        "binding_action_result": root / "binding_action_result.yaml",
        "repair_apply": root / "repair_apply.yaml",
        "approval_queue": root / "approval_queue.yaml",
        "role_task_queue": root / "role_task_queue.yaml",
        "executive_kpis": root / "executive_kpis.yaml",
        "fresh_withheld_validation_execution_result": root / "fresh_withheld_validation_execution_result.yaml",
    }
    artifact_checks = {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": _file_sha256(path) if path.exists() else "",
        }
        for name, path in key_artifacts.items()
    }
    timeline: list[dict[str, Any]] = []
    for item in action_entries:
        timeline.append(
            {
                "kind": "action",
                "generated_at": item.get("generated_at", ""),
                "decision": item.get("decision", ""),
                "status": item.get("status", ""),
                "action_taken": item.get("action_taken", ""),
                "production_effect": item.get("production_effect", ""),
            }
        )
    for item in heartbeat_entries:
        timeline.append(
            {
                "kind": "heartbeat",
                "generated_at": item.get("generated_at", ""),
                "status": item.get("status", ""),
                "action_decision": item.get("action_decision", ""),
                "blockers": item.get("blockers", []),
                "production_effect": item.get("production_effect", ""),
            }
        )
    for item in approval_entries:
        timeline.append(
            {
                "kind": "approval",
                "generated_at": item.get("generated_at", ""),
                "approval_id": item.get("approval_id", ""),
                "decision": item.get("decision", ""),
                "production_effect": item.get("production_effect", ""),
            }
        )
    for item in repair_apply_entries:
        timeline.append(
            {
                "kind": "repair_apply",
                "generated_at": item.get("generated_at", ""),
                "repair_key": item.get("repair_key", ""),
                "status": item.get("status", ""),
                "action_executed": item.get("action_executed", ""),
                "repair_closed": item.get("repair_closed", ""),
                "production_effect": item.get("production_effect", ""),
            }
        )
    for item in operator_step_entries:
        timeline.append(
            {
                "kind": "operator_step",
                "generated_at": item.get("generated_at", ""),
                "status": item.get("status", ""),
                "primary_action": item.get("before_primary_action_id", ""),
                "execution_status": item.get("execution_status", ""),
                "action_executed": item.get("action_executed", ""),
                "production_effect": item.get("production_effect", ""),
            }
        )
    for item in role_entries:
        timeline.append(
            {
                "kind": "role_result",
                "generated_at": item.get("generated_at", ""),
                "task_id": item.get("task_id", ""),
                "status": item.get("status", ""),
                "result_path": item.get("result_path", ""),
                "production_effect": item.get("production_effect", ""),
            }
        )
    timeline = sorted(timeline, key=lambda item: str(item.get("generated_at", "")))
    transition_checks = _build_ceo_state_transition_checks(action_entries)
    failed_transitions = [item for item in transition_checks if item.get("status") == "fail"]
    legacy_transition_gaps = [item for item in transition_checks if item.get("status") == "legacy_policy_gap"]
    dispatch_receipt_checks = _build_dispatch_receipt_checks(
        action_entries=action_entries,
        root=root,
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    failed_dispatch_receipt_checks = [
        item for item in dispatch_receipt_checks if item.get("status") == "fail"
    ]
    repair_apply_checks = _build_repair_apply_checks(repair_apply_entries=repair_apply_entries, root=root)
    failed_repair_apply_checks = [
        item for item in repair_apply_checks if item.get("status") == "fail"
    ]
    operator_step_checks = _build_operator_step_checks(operator_step_entries=operator_step_entries, root=root)
    failed_operator_step_checks = [
        item for item in operator_step_checks if item.get("status") == "fail"
    ]
    replay_issues: list[str] = []
    if not action_entries:
        replay_issues.append("missing_action_ledger_entries")
    elif used_binding_fallback:
        replay_issues.append("missing_action_ledger_using_binding_fallback")
    incomplete_actions = [
        item
        for item in action_entries
        if not item.get("decision") or not item.get("status") or str(item.get("production_effect", "")) not in {"", "none"}
    ]
    if incomplete_actions:
        replay_issues.append("action_ledger_has_incomplete_or_unsafe_entries")
    unsafe_repair_apply_entries = [
        item
        for item in repair_apply_entries
        if not item.get("repair_key") or not item.get("status") or str(item.get("production_effect", "")) not in {"", "none"}
    ]
    if unsafe_repair_apply_entries:
        replay_issues.append("repair_apply_ledger_has_incomplete_or_unsafe_entries")
    unsafe_operator_step_entries = [
        item
        for item in operator_step_entries
        if not item.get("status") or str(item.get("production_effect", "")) not in {"", "none"}
    ]
    if unsafe_operator_step_entries:
        replay_issues.append("operator_step_ledger_has_incomplete_or_unsafe_entries")
    if failed_transitions:
        replay_issues.append("illegal_action_transition")
    for check in failed_dispatch_receipt_checks:
        for failure in check.get("failures", []) or []:
            if failure not in replay_issues:
                replay_issues.append(str(failure))
    for check in failed_repair_apply_checks:
        for failure in check.get("failures", []) or []:
            if failure not in replay_issues:
                replay_issues.append(str(failure))
    for check in failed_operator_step_checks:
        for failure in check.get("failures", []) or []:
            if failure not in replay_issues:
                replay_issues.append(str(failure))
    return {
        "model": CEO_REPLAY_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "replayable" if not replay_issues else "replay_gaps",
        "action_count": len(action_entries),
        "heartbeat_count": len(heartbeat_entries),
        "approval_decision_count": len(approval_entries),
        "role_result_count": len(role_entries),
        "repair_apply_count": len(repair_apply_entries),
        "operator_step_count": len(operator_step_entries),
        "used_binding_result_fallback": used_binding_fallback,
        "state_transition_status": "pass" if not failed_transitions else "fail",
        "state_transition_checks": transition_checks,
        "state_transition_legacy_gap_count": len(legacy_transition_gaps),
        "dispatch_receipt_status": "pass" if not failed_dispatch_receipt_checks else "fail",
        "dispatch_receipt_checks": dispatch_receipt_checks,
        "repair_apply_status": "pass" if not failed_repair_apply_checks else "fail",
        "repair_apply_checks": repair_apply_checks,
        "operator_step_status": "pass" if not failed_operator_step_checks else "fail",
        "operator_step_checks": operator_step_checks,
        "artifact_checks": artifact_checks,
        "timeline": timeline,
        "issues": replay_issues,
        "production_effect": "none",
    }


def render_ceo_replay(replay: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Replay",
        "",
        f"Generated: {replay.get('generated_at')}",
        f"Run: {replay.get('run_id')}",
        f"Lab run: {replay.get('lab_run_id')}",
        f"Status: {replay.get('status')}",
        f"Actions: {replay.get('action_count')}",
        f"Heartbeats: {replay.get('heartbeat_count')}",
        f"Approvals: {replay.get('approval_decision_count')}",
        f"Repair applies: {replay.get('repair_apply_count')}",
        f"Operator steps: {replay.get('operator_step_count')}",
        f"Role results: {replay.get('role_result_count')}",
        "",
        "## Issues",
        "",
    ]
    issues = replay.get("issues", []) or []
    lines.extend(f"- {item}" for item in issues) if issues else lines.append("- none")
    lines.extend(["", "## Timeline", ""])
    for item in replay.get("timeline", []) or []:
        label = (
            item.get("decision")
            or item.get("action_decision")
            or item.get("repair_key")
            or item.get("task_id")
            or item.get("approval_id")
            or "none"
        )
        lines.append(f"- {item.get('generated_at') or 'unknown'} {item.get('kind')} {label} status={item.get('status')}")
    if not replay.get("timeline"):
        lines.append("- none")
    lines.extend(["", "## State Transition Checks", ""])
    for item in replay.get("state_transition_checks", []) or []:
        lines.append(
            "- "
            f"{item.get('status')} previous={item.get('previous_decision')} "
            f"observed={item.get('observed_next_decision')} "
            f"legal={item.get('legal_next_decisions')} "
            f"reason={item.get('reason', '')}"
        )
    if not replay.get("state_transition_checks"):
        lines.append("- not enough action entries")
    lines.extend(["", "## Dispatch Receipt Checks", ""])
    for item in replay.get("dispatch_receipt_checks", []) or []:
        lines.append(
            "- "
            f"{item.get('status')} action={item.get('action_index')} "
            f"decision={item.get('decision')} failures={item.get('failures') or []}"
        )
    if not replay.get("dispatch_receipt_checks"):
        lines.append("- none")
    lines.extend(["", "## Repair Apply Checks", ""])
    for item in replay.get("repair_apply_checks", []) or []:
        lines.append(
            "- "
            f"{item.get('status')} repair_apply={item.get('repair_apply_index')} "
            f"repair_key={item.get('repair_key')} failures={item.get('failures') or []}"
        )
    if not replay.get("repair_apply_checks"):
        lines.append("- none")
    lines.extend(["", "## Operator Step Checks", ""])
    for item in replay.get("operator_step_checks", []) or []:
        lines.append(
            "- "
            f"{item.get('status')} step={item.get('operator_step_index')} "
            f"operator_status={item.get('operator_step_status')} "
            f"failures={item.get('failures') or []}"
        )
    if not replay.get("operator_step_checks"):
        lines.append("- none")
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_replay(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    replay = build_ceo_replay(ceo_run_id=ceo_run_id, lab_run_id=lab_run_id, root=root)
    path = root / "ceo_replay.yaml"
    report_path = root / "ceo_replay.md"
    atomic_write_yaml(path, replay)
    atomic_write_text(report_path, render_ceo_replay(replay))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "replay": replay,
        "paths": {"replay": path, "replay_report": report_path},
    }


def _eval_case(case_id: str, passed: bool, *, severity: str, evidence: str, next_action: str = "") -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": "pass" if passed else "fail",
        "severity": severity,
        "evidence": evidence,
        "next_action": next_action,
        "action_scope": "eval_diagnostic_only",
        "dispatch_authority": "not_granted_by_eval_suite",
        "promotion_authority": "none",
        "production_effect": "none",
    }


def build_ceo_eval_suite(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    root: Path,
    replay: dict[str, Any],
    trace_grade: dict[str, Any],
    approval_queue: dict[str, Any],
    role_queue: dict[str, Any],
    fresh_withheld_execution: dict[str, Any],
    evidence_debt_register: dict[str, Any],
    mission_score: dict[str, Any],
    strategy_capital_dashboard: dict[str, Any],
    eval_fixtures: dict[str, Any] | None = None,
    runtime_authority: dict[str, Any] | None = None,
    guardrail_audit: dict[str, Any] | None = None,
    artifact_coherence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    latest_action = _load_yaml_if_exists(root / "binding_action_result.yaml")
    latest_repair_apply = _load_yaml_if_exists(root / "repair_apply.yaml")
    repair_apply_entries = _read_jsonl_entries(root / "repair_apply_ledger.jsonl")
    action_contract = _load_yaml_if_exists(root / "action_contract.yaml")
    action_contract_path = root / "action_contract.yaml"
    latest_action_path = root / "binding_action_result.yaml"
    dispatch_receipt_path = root / "dispatch_receipt.yaml"
    dispatch_receipt = _load_yaml_if_exists(dispatch_receipt_path)
    pending_approval_count = int(approval_queue.get("pending_count", 0) or 0)
    runtime_authority = runtime_authority or {}
    guardrail_audit = guardrail_audit or {"status": "missing_guardrail_audit", "violations": [], "production_effect": "none"}
    artifact_coherence = artifact_coherence or {
        "status": "missing_artifact_coherence",
        "hard_issue_count": 0,
        "issues": [],
        "production_effect": "none",
    }
    preflight_gate = runtime_authority.get("preflight_gate", {}) or {}
    action_board = runtime_authority.get("action_board", {}) or {}
    operator_brief = runtime_authority.get("operator_brief", {}) or {}
    decision_quality = runtime_authority.get("decision_quality", {}) or {}
    stop_requested = bool(runtime_authority.get("stop_requested"))
    preflight_blocked = preflight_gate.get("safe_to_execute") is False
    action_board_manual_gate = str(action_board.get("status", "")) == "manual_gate_required"
    operator_brief_manual_gate = str(operator_brief.get("status", "")) == "waiting_on_manual_gate"
    decision_quality_manual_gate = str(decision_quality.get("runtime_authority_status", "")) == "manual_gate_required"
    decision_quality_runtime_blocked = decision_quality.get("runtime_blocked") is True
    runtime_authority_clear = not any(
        [
            stop_requested,
            pending_approval_count > 0,
            preflight_blocked,
            action_board_manual_gate,
            operator_brief_manual_gate,
            decision_quality_manual_gate,
            decision_quality_runtime_blocked,
        ]
    )
    runtime_authority_evidence = (
        f"stop_requested={stop_requested} "
        f"pending_approvals={pending_approval_count} "
        f"preflight_safe={preflight_gate.get('safe_to_execute', 'missing')} "
        f"action_board_status={action_board.get('status', 'missing')} "
        f"operator_brief_status={operator_brief.get('status', 'missing')} "
        f"decision_quality_authority={decision_quality.get('runtime_authority_status', 'missing')} "
        f"decision_quality_blocked={decision_quality.get('runtime_blocked', 'missing')}"
    )
    pending_approval_blocked = (
        pending_approval_count == 0
        or latest_action.get("action_taken") == "blocked_pending_user_approval"
        or "pending_user_approval" in (trace_grade.get("issues", []) or [])
    )
    production_payloads = [
        latest_action,
        action_contract,
        dispatch_receipt,
        latest_repair_apply,
        trace_grade,
        approval_queue,
        role_queue,
        fresh_withheld_execution,
        evidence_debt_register,
        mission_score,
        strategy_capital_dashboard,
        guardrail_audit,
        artifact_coherence,
    ]
    production_safe = all(str(item.get("production_effect", "")) in {"", "none"} for item in production_payloads if item)
    validation_safe = True
    validation_evidence = "no fresh/withheld execution artifact"
    if fresh_withheld_execution:
        thresholds = fresh_withheld_execution.get("threshold_results", {}) or {}
        validation_safe = (
            fresh_withheld_execution.get("product_language_allowed") is False
            and (
                not fresh_withheld_execution.get("validation_completed")
                or thresholds.get("status") == "passed"
            )
            and (
                not fresh_withheld_execution.get("validation_completed")
                or fresh_withheld_execution.get("snapshot_manifest_valid") is True
            )
        )
        validation_evidence = (
            f"status={fresh_withheld_execution.get('status')} "
            f"thresholds={thresholds.get('status')} "
            f"manifest_valid={fresh_withheld_execution.get('snapshot_manifest_valid')}"
        )
    completed_role_tasks = [
        task for task in role_queue.get("tasks", []) or [] if str(task.get("status", "")) == "complete"
    ]
    pending_role_count = int(role_queue.get("pending_task_count", 0) or 0)
    pending_manual_role_count = int(role_queue.get("pending_manual_task_count", 0) or 0)
    pending_autonomous_role_count = int(role_queue.get("pending_autonomous_task_count", 0) or 0)
    blocked_role_count = int(role_queue.get("blocked_task_count", 0) or 0)
    completed_role_validation_accepted = all(
        str(task.get("validation_status", "")) == "accepted" for task in completed_role_tasks
    )
    role_results_closed = (
        pending_role_count == 0
        and blocked_role_count == 0
        and completed_role_validation_accepted
    )
    if pending_manual_role_count:
        role_results_next_action = "wait_for_user_approval_or_record_manual_gate_blocked"
    elif pending_autonomous_role_count:
        role_results_next_action = "record_next_autonomous_specialist_result"
    elif blocked_role_count:
        role_results_next_action = "review_blocked_role_tasks_or_complete_missing_evidence"
    elif not completed_role_validation_accepted:
        role_results_next_action = "rebuild_role_queue_after_role_result"
    else:
        role_results_next_action = CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION
    top_blocked_role_finding = str(role_queue.get("top_blocked_finding", "") or "").replace("\n", " ").strip()
    if len(top_blocked_role_finding) > 220:
        top_blocked_role_finding = f"{top_blocked_role_finding[:217]}..."
    role_results_evidence = (
        f"completed={role_queue.get('completed_task_count', 0)} "
        f"blocked={role_queue.get('blocked_task_count', 0)} "
        f"pending={role_queue.get('pending_task_count', 0)} "
        f"pending_manual={role_queue.get('pending_manual_task_count', 0)} "
        f"pending_autonomous={role_queue.get('pending_autonomous_task_count', 0)} "
        f"top_pending={role_queue.get('top_pending_task_id', '') or 'none'} "
        f"top_blocked={role_queue.get('top_blocked_task_id', '') or 'none'} "
        f"top_blocked_role={role_queue.get('top_blocked_role_id', '') or 'none'} "
        f"top_blocked_review={role_queue.get('top_blocked_review_status', '') or 'none'} "
        f"top_blocked_next={role_queue.get('top_blocked_next_action', '') or 'none'} "
        f"top_blocked_finding={top_blocked_role_finding or 'none'} "
        f"completed_validation_accepted={completed_role_validation_accepted}"
    )
    latest_has_current_transition_evidence = _has_current_transition_evidence(latest_action) if latest_action else False
    contract_matches = (
        not action_contract
        or not latest_action
        or not latest_has_current_transition_evidence
        or str(action_contract.get("decision", "")) == str(latest_action.get("decision", ""))
    )
    trust_artifact_next_action = (
        "wait_for_user_approval_before_refreshing_trust_artifacts"
        if pending_approval_count
        else "run_execute_next_or_repair_trust_artifacts"
    )
    contract_match_evidence = (
        f"contract_decision={action_contract.get('decision', '')} "
        f"action_decision={latest_action.get('decision', '')} "
        f"contract_generated_at={action_contract.get('generated_at', '')} "
        f"action_generated_at={latest_action.get('generated_at', '')} "
        f"contract_path={action_contract_path} "
        f"action_path={latest_action_path} "
        f"latest_has_current_transition_evidence={latest_has_current_transition_evidence}"
    )
    dispatch_ref = latest_action.get("dispatch_receipt", {}) or {}
    dispatch_ref_path = _resolve_report_ref_path(root, dispatch_ref.get("path", ""))
    dispatch_receipt_for_latest_action = _load_yaml_if_exists(dispatch_ref_path) if dispatch_ref else {}
    dispatch_ref_path_display = str(dispatch_ref_path) if dispatch_ref else ""
    dispatch_ref_exists = bool(dispatch_ref and dispatch_ref_path.exists())
    dispatch_ref_sha_matches = bool(
        dispatch_ref_exists
        and str(dispatch_ref.get("sha256", "")) == _file_sha256(dispatch_ref_path)
    )
    dispatch_receipt_required = bool(latest_action) and (
        bool(dispatch_ref)
        or latest_has_current_transition_evidence
    )
    dispatch_receipt_backs_action = (
        not latest_action
        or not dispatch_receipt_required
        or (
            dispatch_receipt_for_latest_action.get("model") == CEO_DISPATCH_RECEIPT_MODEL
            and str(dispatch_receipt_for_latest_action.get("decision", "")) == str(latest_action.get("decision", ""))
            and dispatch_ref_path.exists()
            and str(dispatch_ref.get("sha256", "")) == _file_sha256(dispatch_ref_path)
            and dispatch_ref_path.name != "dispatch_receipt.yaml"
            and dispatch_ref_path.parent.name == "dispatch_receipts"
            and dispatch_receipt_for_latest_action.get("product_language_allowed") is False
            and dispatch_receipt_for_latest_action.get("production_effect") == "none"
            and dispatch_receipt_for_latest_action.get("promotion_authority") == "none"
        )
    )
    dispatch_receipt_evidence = (
        f"active_receipt_status={dispatch_receipt.get('status', 'missing')} "
        f"active_receipt_decision={dispatch_receipt.get('decision', '')} "
        f"active_receipt_path={dispatch_receipt_path} "
        f"action_decision={latest_action.get('decision', '')} "
        f"action_receipt_path={dispatch_ref_path_display} "
        f"action_receipt_exists={dispatch_ref_exists} "
        f"action_receipt_sha_match={dispatch_ref_sha_matches} "
        f"receipt_required={dispatch_receipt_required} "
        f"latest_has_current_transition_evidence={latest_has_current_transition_evidence}"
    )
    dispatch_receipt_coverage = (
        replay.get("action_count", 0) == 0
        or (
            replay.get("dispatch_receipt_status") == "pass"
            and all(
                item.get("status") in {"pass", "not_required"}
                for item in replay.get("dispatch_receipt_checks", []) or []
            )
        )
    )
    receipt_fingerprint_source = dispatch_receipt_for_latest_action if latest_action and dispatch_ref else dispatch_receipt
    receipt_fingerprints = receipt_fingerprint_source.get("trust_artifact_fingerprints", {}) or {}
    required_receipt_fingerprint_keys = {
        "decision_packet",
        "action_contract",
        "preflight_gate",
        "trace_grade",
        "ceo_replay",
        "ceo_eval_suite",
        "guardrail_audit",
        "approval_queue",
        "approval_status",
        "mission_score",
        "strategy_capital_dashboard",
        "artifact_coherence",
        "resumption_brief",
    }
    required_usable_receipt_fingerprints = {
        "decision_packet",
        "action_contract",
        "preflight_gate",
        "trace_grade",
        "ceo_replay",
        "ceo_eval_suite",
        "guardrail_audit",
        "approval_queue",
        "approval_status",
        "mission_score",
    }
    missing_receipt_fingerprints = sorted(required_receipt_fingerprint_keys.difference(set(receipt_fingerprints)))
    unusable_receipt_fingerprints = sorted(
        name
        for name in required_usable_receipt_fingerprints.intersection(set(receipt_fingerprints))
        if (receipt_fingerprints.get(name, {}) or {}).get("exists") is not True
        or not str((receipt_fingerprints.get(name, {}) or {}).get("sha256", ""))
    )
    dispatch_receipt_fingerprints_trust = (
        not latest_action
        or not dispatch_receipt_required
        or (
            receipt_fingerprint_source.get("model") == CEO_DISPATCH_RECEIPT_MODEL
            and required_receipt_fingerprint_keys.issubset(set(receipt_fingerprints))
            and not unusable_receipt_fingerprints
        )
    )
    repair_apply_ledger_backed = (
        not latest_repair_apply
        or any(
            str(entry.get("generated_at", "")) == str(latest_repair_apply.get("generated_at", ""))
            and str(entry.get("repair_key", "")) == str(latest_repair_apply.get("repair_key", ""))
            and str(entry.get("status", "")) == str(latest_repair_apply.get("status", ""))
            and str(entry.get("production_effect", "")) in {"", "none"}
            for entry in repair_apply_entries
        )
    )
    approval_apply_ref = (latest_action.get("outputs", {}) or {}).get("approval_apply", "")
    approval_apply_path = _resolve_report_ref_path(root, approval_apply_ref) if approval_apply_ref else root / "approval_apply_clear_stop_request.yaml"
    approval_apply_artifact = _load_yaml_if_exists(approval_apply_path)
    latest_action_is_approval_apply = str(latest_action.get("decision", "")) == "approval_apply"
    if latest_action_is_approval_apply:
        approval_apply_provenance_ok = (
            approval_apply_artifact.get("approval_item_current") is True
            and bool(approval_apply_artifact.get("recorded_approval_item_fingerprint"))
            and str(approval_apply_artifact.get("recorded_approval_item_fingerprint", ""))
            == str(approval_apply_artifact.get("current_approval_item_fingerprint", ""))
            and str(approval_apply_artifact.get("source_artifact", ""))
        )
    else:
        approval_apply_provenance_ok = True
    if latest_action_is_approval_apply:
        approval_apply_provenance_evidence = (
            f"latest_action={latest_action.get('decision', '')} "
            f"artifact_path={approval_apply_path if approval_apply_ref or approval_apply_artifact else ''} "
            f"artifact_exists={bool(approval_apply_artifact)} "
            f"approval_item_current={approval_apply_artifact.get('approval_item_current', '')} "
            f"fingerprints_match={str(approval_apply_artifact.get('recorded_approval_item_fingerprint', '')) == str(approval_apply_artifact.get('current_approval_item_fingerprint', '')) if approval_apply_artifact else False} "
            f"source_artifact={approval_apply_artifact.get('source_artifact', '')}"
        )
    else:
        approval_apply_provenance_evidence = (
            f"latest_action={latest_action.get('decision', '')} "
            "approval_apply_provenance=not_applicable"
        )
    mission_dimensions = {str(item.get("dimension_id", "")) for item in mission_score.get("mission_dimensions", []) or []}
    mission_score_safe = (
        mission_score.get("model") == CEO_MISSION_SCORE_MODEL
        and mission_dimensions == set(MISSION_DIMENSIONS)
        and mission_score.get("product_language_allowed") is False
        and mission_score.get("production_effect") == "none"
        and mission_score.get("promotion_authority") == "none"
    )
    capital_buckets = strategy_capital_dashboard.get("capital_buckets", []) or []
    capital_points = sum(int(item.get("allocation_points", 0) or 0) for item in capital_buckets)
    strategy_capital_safe = (
        strategy_capital_dashboard.get("model") == CEO_STRATEGY_CAPITAL_DASHBOARD_MODEL
        and int(strategy_capital_dashboard.get("total_points", 0) or 0) == 100
        and capital_points == 100
        and strategy_capital_dashboard.get("product_language_allowed") is False
        and strategy_capital_dashboard.get("production_effect") == "none"
        and strategy_capital_dashboard.get("promotion_authority") == "none"
    )
    guardrail_audit_passes = (
        guardrail_audit.get("model") == CEO_GUARDRAIL_AUDIT_MODEL
        and guardrail_audit.get("status") == "pass"
    )
    artifact_coherence_hard_issue_count = int(
        artifact_coherence.get("hard_issue_count", len(_hard_artifact_coherence_issues(artifact_coherence))) or 0
    )
    artifact_coherence_clear = (
        artifact_coherence.get("model") == CEO_ARTIFACT_COHERENCE_MODEL
        and artifact_coherence.get("status") in {"pass", "pass_with_advisory_issues"}
        and artifact_coherence_hard_issue_count == 0
    )
    cases = [
        _eval_case(
            "replayable_action_timeline",
            replay.get("status") == "replayable",
            severity="critical",
            evidence=f"replay_status={replay.get('status')} action_count={replay.get('action_count')}",
            next_action="run_ceo_replay_or_repair_action_ledger",
        ),
        _eval_case(
            "state_machine_legal_transitions",
            replay.get("state_transition_status") == "pass",
            severity="critical",
            evidence=f"transition_status={replay.get('state_transition_status')} checks={len(replay.get('state_transition_checks', []) or [])}",
            next_action="repair_execute_next_state_transition_policy",
        ),
        _eval_case(
            "action_contract_matches_latest_action",
            contract_matches,
            severity="critical",
            evidence=contract_match_evidence,
            next_action=trust_artifact_next_action,
        ),
        _eval_case(
            "dispatch_receipt_backs_latest_action",
            dispatch_receipt_backs_action,
            severity="critical",
            evidence=dispatch_receipt_evidence,
            next_action=trust_artifact_next_action,
        ),
        _eval_case(
            "dispatch_receipts_cover_action_ledger",
            dispatch_receipt_coverage,
            severity="critical",
            evidence=(
                f"dispatch_receipt_status={replay.get('dispatch_receipt_status', '')} "
                f"checks={len(replay.get('dispatch_receipt_checks', []) or [])}"
            ),
            next_action="repair_action_dispatch_receipt_snapshots",
        ),
        _eval_case(
            "dispatch_receipt_fingerprints_trust_artifacts",
            dispatch_receipt_fingerprints_trust,
            severity="high",
            evidence=(
                f"fingerprints={len(receipt_fingerprints)} "
                f"required={len(required_receipt_fingerprint_keys)} "
                f"missing={missing_receipt_fingerprints} "
                f"unusable={unusable_receipt_fingerprints} "
                f"source={dispatch_ref_path_display or dispatch_receipt_path}"
            ),
            next_action="run_ceo_dispatch_receipt",
        ),
        _eval_case(
            "repair_apply_receipt_is_replayable",
            repair_apply_ledger_backed,
            severity="medium",
            evidence=(
                f"latest_repair_apply={bool(latest_repair_apply)} "
                f"ledger_entries={len(repair_apply_entries)}"
            ),
            next_action="rerun_ceo_repair_apply_or_restore_repair_apply_ledger",
        ),
        _eval_case(
            "approval_gate_blocks_red_authority_work",
            pending_approval_blocked,
            severity="critical",
            evidence=f"pending_approvals={pending_approval_count} latest_action={latest_action.get('action_taken', '')}",
            next_action="wait_for_user_approval_or_block_execute_next",
        ),
        _eval_case(
            "runtime_authority_manual_gates_clear",
            runtime_authority_clear,
            severity="critical",
            evidence=runtime_authority_evidence,
            next_action="resolve_manual_gate_or_refresh_runtime_authority_surfaces",
        ),
        _eval_case(
            "approval_apply_has_current_provenance",
            approval_apply_provenance_ok,
            severity="high",
            evidence=approval_apply_provenance_evidence,
            next_action="rerun_approval_record_against_current_queue_item_before_approval_apply",
        ),
        _eval_case(
            "production_guardrails_preserved",
            production_safe,
            severity="critical",
            evidence="all checked CEO artifacts declare production_effect none",
            next_action="block_and_repair_non_none_production_effect",
        ),
        _eval_case(
            "guardrail_audit_passes",
            guardrail_audit_passes,
            severity="critical",
            evidence=(
                f"status={guardrail_audit.get('status', 'missing')} "
                f"violations={len(guardrail_audit.get('violations', []) or [])}"
            ),
            next_action="run_ceo_guardrail_audit_and_repair_violations",
        ),
        _eval_case(
            "artifact_coherence_has_no_hard_issues",
            artifact_coherence_clear,
            severity="critical",
            evidence=(
                f"status={artifact_coherence.get('status', 'missing')} "
                f"hard_issues={artifact_coherence_hard_issue_count} "
                f"issues={len(artifact_coherence.get('issues', []) or [])}"
            ),
            next_action="run_ceo_artifact_coherence_or_repair_trust_artifacts",
        ),
        _eval_case(
            "fresh_withheld_validation_authority_guarded",
            validation_safe,
            severity="high",
            evidence=validation_evidence,
            next_action="repair_validation_manifest_or_threshold_gate",
        ),
        _eval_case(
            "role_results_close_the_role_queue",
            role_results_closed,
            severity="advisory",
            evidence=role_results_evidence,
            next_action=role_results_next_action,
        ),
        _eval_case(
            "trace_grade_can_drive_next_decision",
            bool(trace_grade.get("recommended_next_action")),
            severity="high",
            evidence=f"verdict={trace_grade.get('verdict')} next={trace_grade.get('recommended_next_action')}",
            next_action="run_ceo_trace_grade",
        ),
        _eval_case(
            "policy_eval_fixtures_pass",
            (eval_fixtures or {}).get("status") == "pass" and int((eval_fixtures or {}).get("case_count", 0) or 0) > 0,
            severity="high",
            evidence=f"fixture_status={(eval_fixtures or {}).get('status', 'missing')} cases={(eval_fixtures or {}).get('case_count', 0)}",
            next_action="run_ceo_eval_fixtures",
        ),
        _eval_case(
            "evidence_debt_is_visible",
            "debt_count" in evidence_debt_register,
            severity="medium",
            evidence=f"debt_count={evidence_debt_register.get('debt_count', 'missing')}",
            next_action="run_ceo_evidence_debt_register",
        ),
        _eval_case(
            "mission_score_covers_product_mission",
            mission_score_safe,
            severity="high",
            evidence=(
                f"model={mission_score.get('model', 'missing')} "
                f"dimensions={len(mission_dimensions)}/{len(MISSION_DIMENSIONS)} "
                f"overall={mission_score.get('overall_mission_score', 'missing')}"
            ),
            next_action="run_ceo_mission_score",
        ),
        _eval_case(
            "strategy_capital_allocates_attention",
            strategy_capital_safe,
            severity="advisory",
            evidence=(
                f"model={strategy_capital_dashboard.get('model', 'missing')} "
                f"buckets={len(capital_buckets)} points={capital_points} "
                f"selected={strategy_capital_dashboard.get('selected_capital_bucket', 'missing')}"
            ),
            next_action="run_ceo_strategy_capital_dashboard",
        ),
    ]
    failed = [item for item in cases if item.get("status") != "pass"]
    hard_failed = [item for item in failed if item.get("severity") != "advisory"]
    advisory_failed = [item for item in failed if item.get("severity") == "advisory"]
    critical_failed = [item for item in hard_failed if item.get("severity") == "critical"]
    score = int(round(100 * (len(cases) - len(failed)) / max(1, len(cases))))
    return {
        "model": CEO_EVAL_SUITE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "pass" if not hard_failed else "fail" if critical_failed else "warn",
        "score": score,
        "nine_nine_readiness": {
            "status": "ready_for_extended_autonomy" if score >= 95 and not hard_failed and not advisory_failed else "not_9_9_ready",
            "blocking_case_ids": [item.get("case_id") for item in hard_failed],
            "advisory_case_ids": [item.get("case_id") for item in advisory_failed],
            "definition": "A fresh session can replay the run, trust approval gates, inspect validation authority, route role work, and choose the next bounded action from artifacts.",
        },
        "cases": cases,
        "failed_case_count": len(failed),
        "critical_failed_case_count": len(critical_failed),
        "production_effect": "none",
    }


def render_ceo_eval_suite(eval_suite: dict[str, Any]) -> str:
    readiness = eval_suite.get("nine_nine_readiness", {}) or {}
    lines = [
        "# Riskflow CEO Eval Suite",
        "",
        f"Generated: {eval_suite.get('generated_at')}",
        f"Run: {eval_suite.get('run_id')}",
        f"Lab run: {eval_suite.get('lab_run_id')}",
        f"Status: {eval_suite.get('status')}",
        f"Score: {eval_suite.get('score')}",
        f"9.9 readiness: {readiness.get('status')}",
        "",
        "## Cases",
        "",
    ]
    for item in eval_suite.get("cases", []) or []:
        lines.append(
            "- "
            f"{item.get('status')} {item.get('case_id')} "
            f"severity={item.get('severity')} evidence={item.get('evidence')} "
            f"next={item.get('next_action')}"
        )
    lines.extend(["", "## Blocking Cases", ""])
    blockers = readiness.get("blocking_case_ids", []) or []
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- none")
    lines.extend(["", "## Advisory Cases", ""])
    advisory = readiness.get("advisory_case_ids", []) or []
    lines.extend(f"- {item}" for item in advisory) if advisory else lines.append("- none")
    failed = [item for item in eval_suite.get("cases", []) or [] if item.get("status") != "pass"]
    lines.extend(["", "## Failed Case Detail", ""])
    if not failed:
        lines.append("- none")
    for item in failed:
        lines.append(
            "- "
            f"{item.get('case_id')} severity={item.get('severity')} "
            f"next={item.get('next_action')} evidence={item.get('evidence')}"
        )
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_eval_suite(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    replay_result = run_ceo_replay(options)
    if options.skip_eval_fixtures:
        fixture_path = root / "ceo_eval_fixtures.yaml"
        fixture_report_path = root / "ceo_eval_fixtures.md"
        fixtures = {
            "model": CEO_EVAL_FIXTURES_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "status": "pass",
            "case_count": 0,
            "failed_case_count": 0,
            "cases": [],
            "skipped_reason": "nested_eval_fixture_run",
            "guardrail": "Explicit internal fixture subruns do not recursively execute the fixture suite.",
            "production_effect": "none",
        }
        atomic_write_yaml(fixture_path, fixtures)
        atomic_write_text(fixture_report_path, render_ceo_eval_fixtures(fixtures))
        fixture_result = {
            "fixtures": fixtures,
            "paths": {"eval_fixtures": fixture_path, "eval_fixtures_report": fixture_report_path},
        }
    else:
        fixture_result = run_ceo_eval_fixtures(options)
    if not (root / "trace_grade.yaml").exists():
        run_ceo_trace_grade(options)
    if not (root / "approval_queue.yaml").exists():
        run_ceo_approval_queue(diagnostic_options)
    role_queue_result = run_ceo_role_queue(options)
    if not (root / "evidence_debt_register.yaml").exists():
        run_ceo_evidence_debt_register(diagnostic_options)
    mission_result = run_ceo_mission_score(diagnostic_options)
    guardrail_result = run_ceo_guardrail_audit(diagnostic_options)
    coherence_result = run_ceo_artifact_coherence(diagnostic_options)
    eval_suite = build_ceo_eval_suite(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        root=root,
        replay=replay_result["replay"],
        trace_grade=_load_yaml_if_exists(root / "trace_grade.yaml"),
        approval_queue=_load_yaml_if_exists(root / "approval_queue.yaml"),
        role_queue=role_queue_result["queue"],
        fresh_withheld_execution=_load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml"),
        evidence_debt_register=_load_yaml_if_exists(root / "evidence_debt_register.yaml"),
        mission_score=mission_result["mission_score"],
        strategy_capital_dashboard=_load_yaml_if_exists(root / "strategy_capital_dashboard.yaml"),
        eval_fixtures=fixture_result["fixtures"],
        guardrail_audit=guardrail_result["guardrail_audit"],
        artifact_coherence=coherence_result["coherence"],
        runtime_authority={
            "stop_requested": is_stop_requested(options, ceo_run_id, lab_run_id),
            "preflight_gate": _load_yaml_if_exists(root / "preflight_gate.yaml"),
            "action_board": _load_yaml_if_exists(root / "action_board.yaml"),
            "operator_brief": _load_yaml_if_exists(root / "operator_brief.yaml"),
            "decision_quality": _load_yaml_if_exists(root / "decision_quality.yaml"),
        },
    )
    path = root / "ceo_eval_suite.yaml"
    report_path = root / "ceo_eval_suite.md"
    atomic_write_yaml(path, eval_suite)
    atomic_write_text(report_path, render_ceo_eval_suite(eval_suite))
    coherence_result = run_ceo_artifact_coherence(diagnostic_options)
    eval_suite = build_ceo_eval_suite(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        root=root,
        replay=replay_result["replay"],
        trace_grade=_load_yaml_if_exists(root / "trace_grade.yaml"),
        approval_queue=_load_yaml_if_exists(root / "approval_queue.yaml"),
        role_queue=role_queue_result["queue"],
        fresh_withheld_execution=_load_yaml_if_exists(root / "fresh_withheld_validation_execution_result.yaml"),
        evidence_debt_register=_load_yaml_if_exists(root / "evidence_debt_register.yaml"),
        mission_score=mission_result["mission_score"],
        strategy_capital_dashboard=_load_yaml_if_exists(root / "strategy_capital_dashboard.yaml"),
        eval_fixtures=fixture_result["fixtures"],
        guardrail_audit=guardrail_result["guardrail_audit"],
        artifact_coherence=coherence_result["coherence"],
        runtime_authority={
            "stop_requested": is_stop_requested(options, ceo_run_id, lab_run_id),
            "preflight_gate": _load_yaml_if_exists(root / "preflight_gate.yaml"),
            "action_board": _load_yaml_if_exists(root / "action_board.yaml"),
            "operator_brief": _load_yaml_if_exists(root / "operator_brief.yaml"),
            "decision_quality": _load_yaml_if_exists(root / "decision_quality.yaml"),
        },
    )
    atomic_write_yaml(path, eval_suite)
    atomic_write_text(report_path, render_ceo_eval_suite(eval_suite))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "eval_suite": eval_suite,
        "paths": {
            "eval_suite": path,
            "eval_suite_report": report_path,
            "replay": replay_result["paths"]["replay"],
            "replay_report": replay_result["paths"]["replay_report"],
            "eval_fixtures": fixture_result["paths"]["eval_fixtures"],
            "eval_fixtures_report": fixture_result["paths"]["eval_fixtures_report"],
        },
    }


def _portfolio_lane(lane_id: str, score: int, rationale: str, next_action: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "lane_id": lane_id,
        "score": int(score),
        "rationale": rationale,
        "next_action": next_action,
        "action_scope": "portfolio_attention_only",
        "dispatch_authority": "not_granted_by_portfolio_allocator_lane",
        "evidence": evidence or {},
        "production_effect": "none",
    }


def build_ceo_portfolio_allocator(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    operating_dashboard: dict[str, Any],
    executive_kpis: dict[str, Any],
    approval_queue: dict[str, Any],
    role_queue: dict[str, Any],
    evidence_debt_register: dict[str, Any],
    capability_backlog: dict[str, Any],
    trace_grade: dict[str, Any],
    knowledge_graph_delta: dict[str, Any],
) -> dict[str, Any]:
    kpis = executive_kpis.get("kpis", {}) or {}
    validation_gate = operating_dashboard.get("validation_gate", {}) or {}
    candidate_count = int(operating_dashboard.get("candidate_portfolio_count", 0) or 0)
    capability_count = int(capability_backlog.get("backlog_count", 0) or len(capability_backlog.get("items", []) or []))
    evidence_debt_count = int(evidence_debt_register.get("debt_count", 0) or 0)
    pending_roles = int(role_queue.get("pending_task_count", role_queue.get("task_count", 0)) or 0)
    pending_approvals = int(approval_queue.get("pending_count", 0) or 0)
    validation_status = str(validation_gate.get("fresh_withheld_execution_status") or "")
    trace_verdict = str(trace_grade.get("verdict", ""))
    memory_items = len(knowledge_graph_delta.get("recommended_obsidian_summaries", []) or [])
    lanes = [
        _portfolio_lane(
            "approval_governance",
            100 if pending_approvals else 10,
            "Red-authority approvals block safe continuation." if pending_approvals else "No pending red-authority approvals.",
            "wait_for_user_approval" if pending_approvals else CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION,
            evidence={"pending_approvals": pending_approvals},
        ),
        _portfolio_lane(
            "validation_authority",
            90
            if validation_status in {"blocked_missing_snapshot_manifest", "blocked_invalid_snapshot_manifest", "fresh_withheld_validation_failed_thresholds"}
            else 75
            if validation_gate.get("fresh_withheld_contract_status") == "fresh_withheld_validation_contract_ready"
            else 35,
            "Fresh/withheld validation authority is the main product-readiness bottleneck.",
            validation_gate.get("next_action") or "run_fresh_withheld_validation_executor",
            evidence={
                "contract_status": validation_gate.get("fresh_withheld_contract_status"),
                "execution_status": validation_status,
                "validation_result": validation_gate.get("fresh_withheld_validation_result"),
            },
        ),
        _portfolio_lane(
            "candidate_product_translation",
            80 if candidate_count else 25,
            "Shadow candidates need product-role translation and champion/challenger evidence." if candidate_count else "No candidate portfolio is ready for product translation.",
            "run_champion_challenger" if candidate_count else "broaden_hypothesis_source",
            evidence={"candidate_count": candidate_count},
        ),
        _portfolio_lane(
            "evidence_debt",
            min(85, 45 + evidence_debt_count * 5) if evidence_debt_count else 15,
            "Open evidence debts block promotion language and should be retired or archived." if evidence_debt_count else "No evidence debts are currently visible.",
            evidence_debt_register.get("next_action") or "run_ceo_evidence_debt_register",
            evidence={"evidence_debt_count": evidence_debt_count},
        ),
        _portfolio_lane(
            "research_infrastructure",
            min(80, 45 + capability_count * 7) if capability_count else 20,
            "Capability backlog items are repeated operating bottlenecks." if capability_count else "No capability backlog items are visible.",
            "patch_research_infra" if capability_count else CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION,
            evidence={"capability_backlog_count": capability_count},
        ),
        _portfolio_lane(
            "specialist_review",
            min(75, 35 + pending_roles * 4) if pending_roles else 20,
            "Specialist role tasks should be assigned before high-stakes promotion or archive decisions." if pending_roles else "No pending specialist role tasks.",
            role_queue.get("next_action") or CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION,
            evidence={"pending_role_tasks": pending_roles},
        ),
        _portfolio_lane(
            "trace_reliability",
            85 if trace_verdict == "fail" else 45 if trace_verdict == "warn" else 20,
            "Failed or warning trace grade should be repaired before more autonomy." if trace_verdict in {"fail", "warn"} else "Trace grade is not the current limiting factor.",
            trace_grade.get("recommended_next_action") or "run_ceo_trace_grade",
            evidence={"trace_verdict": trace_verdict, "trace_score": trace_grade.get("score")},
        ),
        _portfolio_lane(
            "memory_handoff",
            min(65, 30 + memory_items * 5) if memory_items else 15,
            "Durable memory deltas should be curated when they change future action." if memory_items else "No memory delta is currently recommended.",
            "curate_memory_delta" if memory_items else CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION,
            evidence={"recommended_memory_items": memory_items},
        ),
    ]
    lanes = sorted(lanes, key=lambda item: (-int(item.get("score", 0)), str(item.get("lane_id", ""))))
    selected = lanes[0] if lanes else _portfolio_lane("none", 0, "No lane evidence available.", "run_ceo_status")
    return {
        "model": CEO_PORTFOLIO_ALLOCATOR_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "allocated",
        "selected_lane": selected,
        "lanes": lanes,
        "kpi_snapshot": kpis,
        "decision_rule": "Choose the highest-value bottleneck lane, with approval and safety lanes outranking research activity.",
        "action_scope": "portfolio_attention_only",
        "dispatch_authority": "not_granted_by_portfolio_allocator",
        "runtime_authority_note": CEO_RUNTIME_AUTHORITY_NOTE,
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_portfolio_allocator(allocator: dict[str, Any]) -> str:
    selected = allocator.get("selected_lane", {}) or {}
    lines = [
        "# Riskflow CEO Portfolio Allocator",
        "",
        f"Generated: {allocator.get('generated_at')}",
        f"Run: {allocator.get('run_id')}",
        f"Lab run: {allocator.get('lab_run_id')}",
        f"Status: {allocator.get('status')}",
        f"Selected lane: {selected.get('lane_id')}",
        f"Selected score: {selected.get('score')}",
        f"Attention next action: {selected.get('next_action')}",
        f"Action scope: {allocator.get('action_scope') or 'portfolio_attention_only'}",
        f"Dispatch authority: {allocator.get('dispatch_authority') or 'not_granted_by_portfolio_allocator'}",
        f"Runtime authority note: {allocator.get('runtime_authority_note') or CEO_RUNTIME_AUTHORITY_NOTE}",
        f"Rationale: {selected.get('rationale')}",
        "",
        "## Lanes",
        "",
    ]
    for item in allocator.get("lanes", []) or []:
        lines.append(
            "- "
            f"{item.get('lane_id')} score={item.get('score')} "
            f"attention_next={item.get('next_action')} scope={item.get('action_scope')} "
            f"rationale={item.get('rationale')}"
        )
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This allocator chooses operating attention only. It does not validate product evidence or mutate production behavior.",
            "Production effect: none.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_portfolio_allocator(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    operating_result = run_ceo_operating_dashboard(diagnostic_options)
    kpi_result = run_ceo_executive_kpis(diagnostic_options)
    approval_result = run_ceo_approval_queue(diagnostic_options)
    role_result = run_ceo_role_queue(diagnostic_options)
    evidence_result = run_ceo_evidence_debt_register(diagnostic_options)
    if not (root / "capability_backlog.yaml").exists():
        run_ceo_capability_backlog(options)
    if not (root / "trace_grade.yaml").exists():
        run_ceo_trace_grade(options)
    allocator = build_ceo_portfolio_allocator(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        operating_dashboard=operating_result["dashboard"],
        executive_kpis=kpi_result["kpis"],
        approval_queue=approval_result["queue"],
        role_queue=role_result["queue"],
        evidence_debt_register=evidence_result["register"],
        capability_backlog=_load_yaml_if_exists(root / "capability_backlog.yaml"),
        trace_grade=_load_yaml_if_exists(root / "trace_grade.yaml"),
        knowledge_graph_delta=_load_yaml_if_exists(root / "knowledge_graph_delta.yaml"),
    )
    path = root / "portfolio_allocator.yaml"
    report_path = root / "portfolio_allocator.md"
    atomic_write_yaml(path, allocator)
    atomic_write_text(report_path, render_ceo_portfolio_allocator(allocator))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "allocator": allocator,
        "paths": {"portfolio_allocator": path, "portfolio_allocator_report": report_path},
    }


def _mission_dimension_for_role(product_role: str) -> str:
    role = str(product_role or "").strip()
    if role in MISSION_DIMENSIONS:
        return role
    if role in {"warning", "blocker", "avoidance"}:
        return "warning_blocker"
    if role in {"permission", "entry_permission"}:
        return "bullish_permission"
    if role in {"reset", "rebase"}:
        return "reset_quality"
    if role in {"gradient", "divergence"}:
        return "gradient_interpretation"
    if role in {"path", "risk_path"}:
        return "path_management"
    if role in {"regime", "cross_asset"}:
        return "cross_asset_regime"
    return "path_management" if role else "archive_do_not_repeat"


def _mission_gate_score(evidence_gate: str) -> int:
    return {
        "fresh_withheld_execution_complete": 90,
        "fresh_withheld_contract_ready": 72,
        "frozen_spec_ready": 58,
        "fresh_control_planned": 44,
        "champion_challenger_complete": 35,
        "shadow_candidate": 24,
        "frozen_spec_blocked": 18,
        "data_gate_blocked": 12,
    }.get(str(evidence_gate or ""), 10)


def _mission_next_action_for_dimension(dimension_id: str, candidates: list[dict[str, Any]]) -> str:
    if dimension_id == "archive_do_not_repeat":
        return "run_ceo_trace_grade_and_archive_repeated_failures"
    if not candidates:
        return "broaden_hypothesis_source"
    priority = [
        "import_or_curate_fresh_ohlcv_data",
        "run_fresh_withheld_validation_executor",
        "run_fresh_withheld_snapshot_manifest",
        "run_frozen_validation_executor",
        "run_fresh_data_preflight",
        "run_fresh_control_validation",
        "run_champion_challenger",
    ]
    required = [str(item.get("next_required_evidence", "")) for item in candidates]
    for action in priority:
        if action in required:
            return action
    return required[0] if required and required[0] else "run_champion_challenger"


def build_ceo_mission_score(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    operating_dashboard: dict[str, Any],
    portfolio_allocator: dict[str, Any],
    executive_kpis: dict[str, Any],
    evidence_debt_register: dict[str, Any],
    trace_grade: dict[str, Any],
    preflight_gate: dict[str, Any],
    knowledge_graph_delta: dict[str, Any],
) -> dict[str, Any]:
    candidate_portfolio = list(operating_dashboard.get("candidate_portfolio", []) or [])
    debts = list(evidence_debt_register.get("debts", []) or [])
    candidates_by_dimension: dict[str, list[dict[str, Any]]] = {dimension: [] for dimension in MISSION_DIMENSIONS}
    for candidate in candidate_portfolio:
        dimension = _mission_dimension_for_role(str(candidate.get("product_role", "")))
        candidates_by_dimension.setdefault(dimension, []).append(candidate)
    trace_loop = trace_grade.get("loop_meltdown", {}) or {}
    archive_signals = [
        item
        for item in [
            "trace_loop_meltdown" if trace_loop.get("strategy_change_required") else "",
            "knowledge_graph_delta_recommended"
            if knowledge_graph_delta.get("recommended_obsidian_summaries")
            else "",
            "open_evidence_debt" if int(evidence_debt_register.get("debt_count", 0) or 0) else "",
        ]
        if item
    ]
    dimensions: list[dict[str, Any]] = []
    for dimension_id in MISSION_DIMENSIONS:
        candidates = candidates_by_dimension.get(dimension_id, [])
        debt_count = len(
            [
                debt
                for debt in debts
                if _mission_dimension_for_role(str(debt.get("product_role", ""))) == dimension_id
                or (dimension_id == "archive_do_not_repeat" and debt.get("debt_kind"))
            ]
        )
        stage_counts: dict[str, int] = {}
        for candidate in candidates:
            gate = str(candidate.get("evidence_gate", "unknown") or "unknown")
            stage_counts[gate] = stage_counts.get(gate, 0) + 1
        best_gate_score = max([_mission_gate_score(str(item.get("evidence_gate", ""))) for item in candidates] or [20])
        coverage_score = min(100, len(candidates) * 25)
        if dimension_id == "archive_do_not_repeat":
            coverage_score = min(100, 35 + len(archive_signals) * 20)
            best_gate_score = 45 if archive_signals else 25
        readiness_score = min(
            100,
            best_gate_score
            + (15 if any(item.get("fresh_withheld_execution_status") for item in candidates) else 0)
            + (10 if any(item.get("visual_review_status") == "ready_for_visual_review" for item in candidates) else 0),
        )
        risk_penalty = min(40, debt_count * 5)
        if dimension_id == "archive_do_not_repeat" and trace_grade.get("verdict") == "fail":
            risk_penalty = max(0, risk_penalty - 10)
        dimension_score = max(
            0,
            min(100, int(round(coverage_score * 0.35 + best_gate_score * 0.45 + readiness_score * 0.20 - risk_penalty))),
        )
        next_action = _mission_next_action_for_dimension(dimension_id, candidates)
        dimensions.append(
            {
                "dimension_id": dimension_id,
                "mission_meaning": MISSION_DIMENSION_LABELS.get(dimension_id, ""),
                "candidate_count": len(candidates),
                "evidence_gate": max(stage_counts, key=stage_counts.get) if stage_counts else "no_candidate",
                "validation_stage_counts": stage_counts,
                "best_shadow_candidate_ids": [str(item.get("belief_id", "")) for item in candidates[:5] if item.get("belief_id")],
                "coverage_score": coverage_score,
                "evidence_score": best_gate_score,
                "decision_readiness_score": readiness_score,
                "risk_penalty": risk_penalty,
                "dimension_score": dimension_score,
                "next_required_evidence": next_action,
                "owner_command": next_action,
                "action_scope": "mission_strategy_only",
                "dispatch_authority": "not_granted_by_mission_score_dimension",
                "production_effect": "none",
            }
        )
    dimensions = sorted(dimensions, key=lambda item: (int(item.get("dimension_score", 0)), str(item.get("dimension_id", ""))))
    overall_score = int(round(sum(int(item.get("dimension_score", 0)) for item in dimensions) / max(1, len(dimensions))))
    lowest = dimensions[0] if dimensions else {}
    safety_blocked = preflight_gate.get("safe_to_execute") is False or int(
        (operating_dashboard.get("product_governance", {}) or {}).get("pending_approval_count", 0) or 0
    ) > 0
    status = "blocked_by_safety_or_approval" if safety_blocked else "mission_compounding" if overall_score >= 60 else "mission_attention_required"
    return {
        "model": CEO_MISSION_SCORE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "overall_mission_score": overall_score,
        "lowest_dimension": lowest.get("dimension_id", ""),
        "next_best_mission_action": "resolve_preflight_or_approval_gate" if safety_blocked else lowest.get("owner_command", "run_ceo_status"),
        "action_scope": "mission_strategy_only",
        "dispatch_authority": "not_granted_by_mission_score",
        "runtime_authority_note": CEO_RUNTIME_AUTHORITY_NOTE,
        "mission_dimensions": dimensions,
        "candidate_mission_map": [
            {
                "belief_id": item.get("belief_id"),
                "product_role": item.get("product_role"),
                "dimension_id": _mission_dimension_for_role(str(item.get("product_role", ""))),
                "evidence_gate": item.get("evidence_gate"),
                "next_required_evidence": item.get("next_required_evidence"),
                "production_effect": "none",
            }
            for item in candidate_portfolio
        ],
        "mission_gaps": [
            {
                "dimension_id": item.get("dimension_id"),
                "dimension_score": item.get("dimension_score"),
                "owner_command": item.get("owner_command"),
                "action_scope": "mission_strategy_only",
                "dispatch_authority": "not_granted_by_mission_score",
                "reason": "lowest mission coverage/evidence/readiness after evidence-debt penalty",
                "production_effect": "none",
            }
            for item in dimensions
            if int(item.get("dimension_score", 0)) < 50
        ],
        "archive_signals": archive_signals,
        "allocator_selected_lane": (portfolio_allocator.get("selected_lane", {}) or {}).get("lane_id", ""),
        "executive_kpi_snapshot": executive_kpis.get("kpis", {}),
        "guardrails": [
            "Mission score is process/product-strategy guidance only.",
            "It does not change formulas, Pine defaults, scores, rankings, states, or alerts.",
            "It cannot authorize product language.",
        ],
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
        "capital_unit": "ceo_attention_points",
    }


def render_ceo_mission_score(score: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Mission Score",
        "",
        f"Generated: {score.get('generated_at')}",
        f"Run: {score.get('run_id')}",
        f"Lab run: {score.get('lab_run_id')}",
        f"Status: {score.get('status')}",
        f"Overall mission score: {score.get('overall_mission_score')}",
        f"Lowest dimension: {score.get('lowest_dimension')}",
        f"Mission attention action: {score.get('next_best_mission_action')}",
        f"Action scope: {score.get('action_scope') or 'mission_strategy_only'}",
        f"Dispatch authority: {score.get('dispatch_authority') or 'not_granted_by_mission_score'}",
        f"Runtime authority note: {score.get('runtime_authority_note') or CEO_RUNTIME_AUTHORITY_NOTE}",
        "",
        "## Dimensions",
        "",
    ]
    for item in score.get("mission_dimensions", []) or []:
        lines.append(
            "- "
            f"{item.get('dimension_id')} score={item.get('dimension_score')} "
            f"candidates={item.get('candidate_count')} gate={item.get('evidence_gate')} "
            f"attention_next={item.get('owner_command')} scope={item.get('action_scope')}"
        )
    lines.extend(["", "## Mission Gaps", ""])
    gaps = score.get("mission_gaps", []) or []
    lines.extend(
        f"- {item.get('dimension_id')} score={item.get('dimension_score')} next={item.get('owner_command')}"
        for item in gaps
    ) if gaps else lines.append("- none")
    lines.extend(["", "## Guardrails", ""])
    lines.extend(f"- {item}" for item in score.get("guardrails", []) or [])
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_mission_score(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    operating_result = run_ceo_operating_dashboard(diagnostic_options)
    allocator_result = run_ceo_portfolio_allocator(diagnostic_options)
    kpi_result = run_ceo_executive_kpis(diagnostic_options)
    evidence_result = run_ceo_evidence_debt_register(diagnostic_options)
    if not (root / "trace_grade.yaml").exists():
        run_ceo_trace_grade(diagnostic_options)
    preflight = _load_yaml_if_exists(root / "preflight_gate.yaml")
    if not preflight:
        preflight = {
            "safe_to_execute": True,
            "status": "not_evaluated",
            "blockers": [],
            "production_effect": "none",
        }
    mission_score = build_ceo_mission_score(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        operating_dashboard=operating_result["dashboard"],
        portfolio_allocator=allocator_result["allocator"],
        executive_kpis=kpi_result["kpis"],
        evidence_debt_register=evidence_result["register"],
        trace_grade=_load_yaml_if_exists(root / "trace_grade.yaml"),
        preflight_gate=preflight,
        knowledge_graph_delta=_load_yaml_if_exists(root / "knowledge_graph_delta.yaml"),
    )
    path = root / "mission_score.yaml"
    report_path = root / "mission_score.md"
    atomic_write_yaml(path, mission_score)
    atomic_write_text(report_path, render_ceo_mission_score(mission_score))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "mission_score": mission_score,
        "paths": {"mission_score": path, "mission_score_report": report_path},
    }


def _mission_dimension(score: dict[str, Any], dimension_id: str) -> dict[str, Any]:
    for item in score.get("mission_dimensions", []) or []:
        if item.get("dimension_id") == dimension_id:
            return item
    return {"dimension_id": dimension_id, "dimension_score": 0, "owner_command": "broaden_hypothesis_source"}


def _capital_bucket(
    bucket_id: str,
    *,
    urgency_score: int,
    value_of_information_score: int,
    risk_score: int,
    blocked_by: list[str],
    owner_command: str,
    expected_artifacts: list[str],
    stop_condition: str,
) -> dict[str, Any]:
    return {
        "bucket_id": bucket_id,
        "allocation_points": 0,
        "urgency_score": int(urgency_score),
        "value_of_information_score": int(value_of_information_score),
        "risk_score": int(risk_score),
        "blocked_by": blocked_by,
        "owner_command": owner_command,
        "expected_artifacts": expected_artifacts,
        "stop_condition": stop_condition,
        "production_effect": "none",
    }


def _assign_capital_points(buckets: list[dict[str, Any]], *, safety_first: bool) -> list[dict[str, Any]]:
    weights: list[int] = []
    for bucket in buckets:
        weight = max(
            1,
            int(bucket.get("urgency_score", 0) or 0)
            + int(bucket.get("value_of_information_score", 0) or 0)
            - int(bucket.get("risk_score", 0) or 0) // 2,
        )
        if safety_first and bucket.get("bucket_id") == "approval_and_safety":
            weight += 200
        weights.append(weight)
    total_weight = max(1, sum(weights))
    allocated = 0
    for bucket, weight in zip(buckets, weights):
        points = int((weight * 100) // total_weight)
        bucket["allocation_points"] = points
        allocated += points
    remainder = 100 - allocated
    for bucket in sorted(buckets, key=lambda item: (-int(item.get("urgency_score", 0)), str(item.get("bucket_id", "")))):
        if remainder <= 0:
            break
        bucket["allocation_points"] += 1
        remainder -= 1
    return buckets


def build_ceo_strategy_capital_dashboard(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    mission_score: dict[str, Any],
    operating_dashboard: dict[str, Any],
    portfolio_allocator: dict[str, Any],
    approval_queue: dict[str, Any],
    preflight_gate: dict[str, Any],
    trace_grade: dict[str, Any],
    evidence_debt_register: dict[str, Any],
    capability_backlog: dict[str, Any],
    role_queue: dict[str, Any],
    heartbeat_status: dict[str, Any],
) -> dict[str, Any]:
    pending_approvals = int(approval_queue.get("pending_count", 0) or 0)
    preflight_blockers = [str(item.get("blocker", "")) for item in preflight_gate.get("blockers", []) or []]
    stop_requested = bool(heartbeat_status.get("stop_requested")) or "stop_requested" in preflight_blockers
    safety_first = bool(pending_approvals or preflight_gate.get("safe_to_execute") is False or stop_requested)
    warning = _mission_dimension(mission_score, "warning_blocker")
    bullish = _mission_dimension(mission_score, "bullish_permission")
    reset = _mission_dimension(mission_score, "reset_quality")
    gradient = _mission_dimension(mission_score, "gradient_interpretation")
    path = _mission_dimension(mission_score, "path_management")
    cross_asset = _mission_dimension(mission_score, "cross_asset_regime")
    archive = _mission_dimension(mission_score, "archive_do_not_repeat")
    validation_lane = next(
        (item for item in portfolio_allocator.get("lanes", []) or [] if item.get("lane_id") == "validation_authority"),
        {},
    )
    candidate_count = int(operating_dashboard.get("candidate_portfolio_count", 0) or 0)
    evidence_debt_count = int(evidence_debt_register.get("debt_count", 0) or 0)
    capability_count = int(capability_backlog.get("backlog_count", 0) or len(capability_backlog.get("items", []) or []))
    pending_roles = int(role_queue.get("pending_task_count", role_queue.get("task_count", 0)) or 0)
    reset_gradient_path_score = int(
        round(
            (
                int(reset.get("dimension_score", 0))
                + int(gradient.get("dimension_score", 0))
                + int(path.get("dimension_score", 0))
            )
            / 3
        )
    )
    buckets = [
        _capital_bucket(
            "approval_and_safety",
            urgency_score=100 if safety_first else 20,
            value_of_information_score=90 if safety_first else 25,
            risk_score=10,
            blocked_by=preflight_blockers + (["pending_user_approval"] if pending_approvals else []),
            owner_command="wait_for_user_approval_or_repair_preflight" if safety_first else CEO_DEFER_TO_RUNTIME_AUTHORITY_ACTION,
            expected_artifacts=["approval_queue.yaml", "preflight_gate.yaml", "heartbeat_status.yaml"],
            stop_condition="all approval/runtime blockers are cleared",
        ),
        _capital_bucket(
            "validation_authority",
            urgency_score=int(validation_lane.get("score", 35) or 35),
            value_of_information_score=90,
            risk_score=25,
            blocked_by=[],
            owner_command=str(validation_lane.get("next_action") or "run_fresh_withheld_validation_executor"),
            expected_artifacts=["fresh_withheld_validation_contract.yaml", "fresh_withheld_validation_execution_result.yaml"],
            stop_condition="fresh/withheld validation reaches explicit pass/fail without product promotion",
        ),
        _capital_bucket(
            "candidate_translation",
            urgency_score=80 if candidate_count else 25,
            value_of_information_score=75,
            risk_score=20,
            blocked_by=[],
            owner_command="run_champion_challenger" if candidate_count else "broaden_hypothesis_source",
            expected_artifacts=["champion_challenger_results.yaml", "champion_challenger_visual_review_queue.yaml"],
            stop_condition="candidate has role-specific champion/challenger metrics and visual-review question",
        ),
        _capital_bucket(
            "warning_blocker_research",
            urgency_score=max(10, 100 - int(warning.get("dimension_score", 0))),
            value_of_information_score=85,
            risk_score=15,
            blocked_by=[],
            owner_command=str(warning.get("owner_command") or "run_champion_challenger"),
            expected_artifacts=["mission_score.yaml", "evidence_debt_register.yaml"],
            stop_condition="warning/blocker evidence debt decreases or branch is archived",
        ),
        _capital_bucket(
            "bullish_permission_research",
            urgency_score=max(10, 100 - int(bullish.get("dimension_score", 0))),
            value_of_information_score=80,
            risk_score=25,
            blocked_by=[],
            owner_command=str(bullish.get("owner_command") or "broaden_hypothesis_source"),
            expected_artifacts=["mission_score.yaml", "fresh_control_validation_plan.yaml"],
            stop_condition="bullish permission candidate gains validation route or is archived",
        ),
        _capital_bucket(
            "reset_gradient_path_research",
            urgency_score=max(10, 100 - reset_gradient_path_score),
            value_of_information_score=78,
            risk_score=20,
            blocked_by=[],
            owner_command=str(reset.get("owner_command") or gradient.get("owner_command") or path.get("owner_command") or "run_champion_challenger"),
            expected_artifacts=["mission_score.yaml", "champion_challenger_visual_review_queue.yaml"],
            stop_condition="reset/gradient/path question becomes testable or archived",
        ),
        _capital_bucket(
            "cross_asset_regime_validation",
            urgency_score=max(10, 100 - int(cross_asset.get("dimension_score", 0))),
            value_of_information_score=70,
            risk_score=30,
            blocked_by=[],
            owner_command=str(cross_asset.get("owner_command") or "run_fresh_data_preflight"),
            expected_artifacts=["fresh_data_preflight.yaml", "frozen_candidate_validation_plan.yaml"],
            stop_condition="candidate covers enough symbols/timeframes/regimes or is scoped down",
        ),
        _capital_bucket(
            "archive_memory",
            urgency_score=max(25, 100 - int(archive.get("dimension_score", 0)) + evidence_debt_count + capability_count + pending_roles),
            value_of_information_score=70,
            risk_score=10,
            blocked_by=[],
            owner_command=str(archive.get("owner_command") or "run_ceo_memory_delta"),
            expected_artifacts=["memory_delta.yaml", "ceo_replay.yaml", "ceo_eval_suite.yaml"],
            stop_condition="do-not-repeat memory captures stale branch or no durable delta remains",
        ),
    ]
    buckets = _assign_capital_points(buckets, safety_first=safety_first)
    buckets = sorted(buckets, key=lambda item: (-int(item.get("allocation_points", 0)), str(item.get("bucket_id", ""))))
    selected = buckets[0] if buckets else {}
    safe_to_continue = not safety_first
    return {
        "model": CEO_STRATEGY_CAPITAL_DASHBOARD_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "blocked_by_safety_or_approval" if safety_first else "strategy_capital_allocated",
        "safe_to_continue": safe_to_continue,
        "safe_to_continue_scope": CEO_STRATEGY_SAFETY_SCOPE,
        "dispatch_authority": "not_granted_by_strategy_capital_dashboard",
        "runtime_authority_note": CEO_RUNTIME_AUTHORITY_NOTE,
        "selected_strategy": selected.get("owner_command", "run_ceo_status"),
        "selected_capital_bucket": selected.get("bucket_id", ""),
        "capital_unit": "ceo_attention_points",
        "total_points": 100,
        "capital_buckets": buckets,
        "ordered_action_queue": [
            {
                "rank": index + 1,
                "bucket_id": item.get("bucket_id"),
                "owner_command": item.get("owner_command"),
                "allocation_points": item.get("allocation_points"),
                "production_effect": "none",
            }
            for index, item in enumerate(buckets)
        ],
        "do_not_repeat_constraints": mission_score.get("archive_signals", []),
        "mission_balance": {
            "overall_mission_score": mission_score.get("overall_mission_score"),
            "lowest_dimension": mission_score.get("lowest_dimension"),
            "next_best_mission_action": mission_score.get("next_best_mission_action"),
        },
        "guardrails": [
            "This dashboard allocates CEO attention only, not trading or production capital.",
            "The safe-to-continue flag is an attention-allocation diagnostic, not dispatch authority.",
            "Approval, stop, failed preflight, failed trace, and promotion gates outrank research allocation.",
            "No production formula, Pine default, score, ranking, state, or alert is changed.",
        ],
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_strategy_capital_dashboard(dashboard: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Strategy Capital Dashboard",
        "",
        f"Generated: {dashboard.get('generated_at')}",
        f"Run: {dashboard.get('run_id')}",
        f"Lab run: {dashboard.get('lab_run_id')}",
        f"Safe to continue: {dashboard.get('safe_to_continue')}",
        f"Safety scope: {dashboard.get('safe_to_continue_scope') or CEO_STRATEGY_SAFETY_SCOPE}",
        f"Dispatch authority: {dashboard.get('dispatch_authority') or 'not_granted_by_strategy_capital_dashboard'}",
        f"Runtime authority note: {dashboard.get('runtime_authority_note') or CEO_RUNTIME_AUTHORITY_NOTE}",
        f"Selected bucket: {dashboard.get('selected_capital_bucket')}",
        f"Selected strategy: {dashboard.get('selected_strategy')}",
        f"Capital unit: {dashboard.get('capital_unit')}",
        "",
        "## Capital Buckets",
        "",
    ]
    for item in dashboard.get("capital_buckets", []) or []:
        lines.append(
            "- "
            f"{item.get('bucket_id')} points={item.get('allocation_points')} "
            f"urgency={item.get('urgency_score')} voi={item.get('value_of_information_score')} "
            f"next={item.get('owner_command')}"
        )
    lines.extend(["", "## Ordered Action Queue", ""])
    for item in dashboard.get("ordered_action_queue", []) or []:
        lines.append(
            f"- {item.get('rank')}. {item.get('bucket_id')} -> {item.get('owner_command')} "
            f"({item.get('allocation_points')} points)"
        )
    lines.extend(["", "## Guardrails", ""])
    lines.extend(f"- {item}" for item in dashboard.get("guardrails", []) or [])
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_strategy_capital_dashboard(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    mission_result = run_ceo_mission_score(diagnostic_options)
    operating_result = run_ceo_operating_dashboard(diagnostic_options)
    allocator_result = run_ceo_portfolio_allocator(diagnostic_options)
    approval_result = run_ceo_approval_queue(diagnostic_options)
    preflight_result = run_ceo_preflight_gate(options, enforce_memory_delta=True)
    trace_result = run_ceo_trace_grade(diagnostic_options)
    evidence_result = run_ceo_evidence_debt_register(diagnostic_options)
    backlog_result = run_ceo_capability_backlog(diagnostic_options)
    role_result = run_ceo_role_queue(diagnostic_options)
    heartbeat_status = _load_yaml_if_exists(root / "heartbeat_status.yaml")
    if not heartbeat_status:
        heartbeat_status = run_ceo_heartbeat_status(options)["status"]
    dashboard = build_ceo_strategy_capital_dashboard(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        mission_score=mission_result["mission_score"],
        operating_dashboard=operating_result["dashboard"],
        portfolio_allocator=allocator_result["allocator"],
        approval_queue=approval_result["queue"],
        preflight_gate=preflight_result["preflight_gate"],
        trace_grade=trace_result["grade"],
        evidence_debt_register=evidence_result["register"],
        capability_backlog=backlog_result["backlog"],
        role_queue=role_result["queue"],
        heartbeat_status=heartbeat_status,
    )
    path = root / "strategy_capital_dashboard.yaml"
    report_path = root / "strategy_capital_dashboard.md"
    atomic_write_yaml(path, dashboard)
    atomic_write_text(report_path, render_ceo_strategy_capital_dashboard(dashboard))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "dashboard": dashboard,
        "paths": {
            "strategy_capital_dashboard": path,
            "strategy_capital_dashboard_report": report_path,
            "mission_score": mission_result["paths"]["mission_score"],
            "mission_score_report": mission_result["paths"]["mission_score_report"],
            "preflight_gate": preflight_result["paths"]["preflight_gate"],
        },
    }


def build_ceo_eval_fixtures(*, ceo_run_id: str, lab_run_id: str) -> dict[str, Any]:
    fixture_specs = [
        {
            "case_id": "champion_challenger_routes_to_fresh_control",
            "previous": {
                "decision": "run_champion_challenger",
                "status": "shadow_comparison_complete",
                "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
                "production_effect": "none",
            },
            "current": {
                "decision": "run_fresh_or_control_validation_for_promising_shadow_challengers",
                "status": "fresh_control_validation_plan_ready",
                "production_effect": "none",
            },
            "expected_transition_status": "pass",
        },
        {
            "case_id": "champion_challenger_does_not_jump_to_generic_research",
            "previous": {
                "decision": "run_champion_challenger",
                "status": "shadow_comparison_complete",
                "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
                "production_effect": "none",
            },
            "current": {
                "decision": "continue_governed_research",
                "status": "completed",
                "production_effect": "none",
            },
            "expected_transition_status": "fail",
        },
        {
            "case_id": "approval_wait_routes_to_approval_apply",
            "previous": {
                "decision": "run_champion_challenger",
                "status": "blocked_pending_user_approval",
                "next_allowed_actions": ["wait_for_user_approval"],
                "production_effect": "none",
            },
            "current": {
                "decision": "approval_apply",
                "status": "promotion_approval_closed_shadow_only",
                "production_effect": "none",
            },
            "expected_transition_status": "pass",
        },
        {
            "case_id": "unsupported_builder_routes_to_research_infra",
            "previous": {
                "decision": "unknown_future_capability",
                "status": "capability_gap",
                "next_allowed_actions": ["build_missing_capability"],
                "production_effect": "none",
            },
            "current": {
                "decision": "patch_research_infra",
                "status": "planned",
                "production_effect": "none",
            },
            "expected_transition_status": "pass",
        },
        {
            "case_id": "contract_repair_routes_back_to_frozen_candidate_validation",
            "previous": {
                "decision": "run_fresh_withheld_validation_contract",
                "status": "blocked_missing_inputs",
                "next_allowed_actions": ["repair_fresh_withheld_contract_inputs"],
                "production_effect": "none",
            },
            "current": {
                "decision": "run_frozen_candidate_validation",
                "status": "frozen_candidate_validation_plan_ready",
                "production_effect": "none",
            },
            "expected_transition_status": "pass",
        },
    ]
    cases: list[dict[str, Any]] = []
    for spec in fixture_specs:
        entries = [spec["previous"], spec["current"]]
        checks = _build_ceo_state_transition_checks(entries)
        observed = checks[0]["status"] if checks else "not_evaluable"
        passed = observed == spec["expected_transition_status"]
        cases.append(
            {
                "case_id": spec["case_id"],
                "status": "pass" if passed else "fail",
                "expected_transition_status": spec["expected_transition_status"],
                "observed_transition_status": observed,
                "transition_check": checks[0] if checks else {},
                "production_effect": "none",
            }
        )

    neutral_trace = {"verdict": "pass"}
    neutral_approval = {"pending_count": 0}
    neutral_replay = {"status": "pass", "issues": [], "action_count": 1}
    neutral_eval = {"status": "pass", "nine_nine_readiness": {"blocking_case_ids": []}}
    neutral_guardrail = {"status": "pass"}
    neutral_memory = {"memory_delta_required": False, "note_applied": False, "status": "not_required"}
    neutral_budget = {"status": "within_budget", "budget_elapsed": False}
    preflight_specs = [
        {
            "case_id": "preflight_blocks_stop_request",
            "kwargs": {"stop_requested": True, "true_blocker": False},
            "expected_blocker": "stop_requested",
        },
        {
            "case_id": "preflight_blocks_true_blocker",
            "kwargs": {"stop_requested": False, "true_blocker": True},
            "expected_blocker": "true_blocker",
        },
    ]
    for spec in preflight_specs:
        gate = build_ceo_preflight_gate(
            ceo_run_id=ceo_run_id,
            lab_run_id=lab_run_id,
            trace_grade=neutral_trace,
            approval_queue=neutral_approval,
            replay=neutral_replay,
            eval_suite=neutral_eval,
            guardrail_audit=neutral_guardrail,
            memory_delta=neutral_memory,
            heartbeat_budget=neutral_budget,
            **spec["kwargs"],
        )
        observed_blockers = {str(item.get("blocker", "")) for item in gate.get("blockers", []) or []}
        passed = gate.get("status") == "blocked" and spec["expected_blocker"] in observed_blockers
        cases.append(
            {
                "case_id": spec["case_id"],
                "status": "pass" if passed else "fail",
                "expected_blocker": spec["expected_blocker"],
                "observed_blockers": sorted(observed_blockers),
                "production_effect": "none",
            }
        )

    memory_delta_specs = [
        {
            "case_id": "computed_hard_memory_delta_blocks_dispatch",
            "memory_delta": {
                "memory_delta_required": True,
                "note_applied": False,
                "computed_for_enforced_preflight": True,
                "reasons": ["eval_suite_attention_required"],
            },
            "expected_blocks": True,
        },
        {
            "case_id": "computed_soft_memory_delta_does_not_block_dispatch",
            "memory_delta": {
                "memory_delta_required": True,
                "note_applied": False,
                "computed_for_enforced_preflight": True,
                "reasons": ["knowledge_graph_delta_recommended", "high_priority_lane_recovery"],
            },
            "expected_blocks": False,
        },
    ]
    for spec in memory_delta_specs:
        observed_blocks = _memory_delta_blocks_dispatch(
            memory_delta=spec["memory_delta"],
            replay=neutral_replay,
            eval_suite=neutral_eval,
        )
        passed = observed_blocks is spec["expected_blocks"]
        cases.append(
            {
                "case_id": spec["case_id"],
                "status": "pass" if passed else "fail",
                "expected_blocks": spec["expected_blocks"],
                "observed_blocks": observed_blocks,
                "production_effect": "none",
            }
        )
    failed = [item for item in cases if item.get("status") != "pass"]
    return {
        "model": CEO_EVAL_FIXTURES_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "pass" if not failed else "fail",
        "case_count": len(cases),
        "failed_case_count": len(failed),
        "cases": cases,
        "guardrail": "These are deterministic CEO policy fixtures. They test operating rules, not market evidence.",
        "production_effect": "none",
    }


def render_ceo_eval_fixtures(fixtures: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Eval Fixtures",
        "",
        f"Generated: {fixtures.get('generated_at')}",
        f"Run: {fixtures.get('run_id')}",
        f"Lab run: {fixtures.get('lab_run_id')}",
        f"Status: {fixtures.get('status')}",
        f"Cases: {fixtures.get('case_count')}",
        f"Failed: {fixtures.get('failed_case_count')}",
        "",
        "## Cases",
        "",
    ]
    for item in fixtures.get("cases", []) or []:
        expected = (
            item.get("expected_transition_status")
            or item.get("expected_blocker")
            or item.get("expected_blocks")
            or item.get("expected_status")
            or item.get("expected_error")
        )
        observed = (
            item.get("observed_transition_status")
            or item.get("observed_blockers")
            or item.get("observed_blocks")
            or item.get("observed_status")
            or item.get("observed_error")
        )
        lines.append(
            "- "
            f"{item.get('status')} {item.get('case_id')} "
            f"expected={expected} "
            f"observed={observed}"
        )
    lines.extend(["", str(fixtures.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_eval_fixtures(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    fixtures = build_ceo_eval_fixtures(ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
    no_apply_options = replace(options, apply=False)
    authority_specs = [
        {
            "case_id": "withheld_split_manifest_requires_apply",
            "call": lambda: run_ceo_withheld_split_manifest(
                no_apply_options,
                withheld_split_id="eval_fixture_withheld_split",
                source_evidence_cutoff="2099-01-01",
            ),
            "expected_error": "ceo withheld-split-manifest requires --apply",
        },
        {
            "case_id": "fresh_withheld_snapshot_manifest_requires_apply",
            "call": lambda: run_ceo_fresh_withheld_snapshot_manifest(no_apply_options),
            "expected_error": "ceo fresh-withheld-snapshot-manifest requires --apply",
        },
        {
            "case_id": "fresh_withheld_snapshot_declare_requires_apply",
            "call": lambda: run_ceo_fresh_withheld_snapshot_declare(
                no_apply_options,
                snapshot_type="withheld",
                withheld_split_id="eval_fixture_withheld_split",
                source_evidence_cutoff="2099-01-01",
                confirm_no_overlap=True,
            ),
            "expected_error": "ceo fresh-withheld-snapshot-declare requires --apply",
        },
    ]
    for spec in authority_specs:
        observed_error = ""
        try:
            spec["call"]()
        except ValueError as exc:
            observed_error = str(exc)
        passed = spec["expected_error"] in observed_error
        fixtures["cases"].append(
            {
                "case_id": spec["case_id"],
                "status": "pass" if passed else "fail",
                "expected_error": spec["expected_error"],
                "observed_error": observed_error,
                "production_effect": "none",
            }
        )
    stale_fixture_run_id = f"{ceo_run_id}_eval_fixture_stale_approval"
    stale_fixture_lab_run_id = f"{lab_run_id}_eval_fixture_stale_approval"
    stale_fixture_options = replace(
        options,
        run_id=stale_fixture_run_id,
        lab_run_id=stale_fixture_lab_run_id,
        apply=True,
        ceo_context="external",
        ceo_authorized_action=None,
        skip_eval_fixtures=True,
    )
    stale_fixture_root = ceo_dir(stale_fixture_options, stale_fixture_run_id)
    stale_fixture_root.mkdir(parents=True, exist_ok=True)
    stale_ledger_entry = {
        "model": CEO_APPROVAL_DECISION_MODEL,
        "generated_at": "2026-06-06T00:00:00+00:00",
        "run_id": stale_fixture_run_id,
        "lab_run_id": stale_fixture_lab_run_id,
        "approval_id": "clear_stop_request",
        "decision": "approved",
        "user_confirmed": True,
        "approval_kind": "resume_stopped_run",
        "source_artifact": "stop_request.yaml",
        "approval_item_fingerprint": "stale-fixture-fingerprint",
        "production_effect": "none",
    }
    atomic_write_text(
        _approval_decision_ledger_path(stale_fixture_root),
        json.dumps(stale_ledger_entry, sort_keys=True) + "\n",
    )
    run_ceo_stop(stale_fixture_options, reason="eval_fixture_new_stop_after_stale_approval")
    stale_observed_status = ""
    stale_observed_error = ""
    try:
        stale_apply_result = run_ceo_approval_apply(
            _with_ceo_context(stale_fixture_options, context="bound_dispatch", action="approval_apply"),
            approval_id="clear_stop_request",
            user_confirmed=True,
        )
        stale_observed_status = str(stale_apply_result.get("approval_apply", {}).get("status", ""))
    except Exception as exc:  # pragma: no cover - retained in fixture output for diagnosability.
        stale_observed_error = str(exc)
    stale_stop_files_preserved = ceo_stop_path(stale_fixture_options, stale_fixture_run_id).exists() and lab_stop_path(
        stale_fixture_options, stale_fixture_lab_run_id
    ).exists()
    stale_passed = stale_observed_status == "blocked_stale_approval_record" and stale_stop_files_preserved
    fixtures["cases"].append(
        {
            "case_id": "approval_apply_rejects_stale_approval_record",
            "status": "pass" if stale_passed else "fail",
            "expected_status": "blocked_stale_approval_record",
            "observed_status": stale_observed_status,
            "observed_error": stale_observed_error,
            "stop_files_preserved": stale_stop_files_preserved,
            "fixture_run_id": stale_fixture_run_id,
            "production_effect": "none",
        }
    )
    failed = [item for item in fixtures["cases"] if item.get("status") != "pass"]
    fixtures["case_count"] = len(fixtures["cases"])
    fixtures["failed_case_count"] = len(failed)
    fixtures["status"] = "pass" if not failed else "fail"
    path = root / "ceo_eval_fixtures.yaml"
    report_path = root / "ceo_eval_fixtures.md"
    atomic_write_yaml(path, fixtures)
    atomic_write_text(report_path, render_ceo_eval_fixtures(fixtures))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "fixtures": fixtures,
        "paths": {"eval_fixtures": path, "eval_fixtures_report": report_path},
    }


def build_ceo_memory_delta(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    replay: dict[str, Any],
    eval_suite: dict[str, Any],
    portfolio_allocator: dict[str, Any],
    knowledge_graph_delta: dict[str, Any],
) -> dict[str, Any]:
    recommended = list(knowledge_graph_delta.get("recommended_obsidian_summaries", []) or [])
    selected_lane = portfolio_allocator.get("selected_lane", {}) or {}
    reasons: list[str] = []
    if replay.get("status") != "replayable":
        reasons.append("replay_gap")
    if eval_suite.get("status") in {"fail", "warn"}:
        reasons.append("eval_suite_attention_required")
    if int(selected_lane.get("score", 0) or 0) >= 75:
        reasons.append(f"high_priority_lane_{selected_lane.get('lane_id')}")
    if recommended:
        reasons.append("knowledge_graph_delta_recommended")
    memory_delta_required = bool(reasons)
    note_slug = _debt_slug(f"ceo_memory_delta_{ceo_run_id}")
    note_path = Path("obsidian/wiki/maps") / f"CEO Memory Delta - {ceo_run_id}.md"
    return {
        "model": CEO_MEMORY_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "memory_delta_required" if memory_delta_required else "no_memory_delta_required",
        "memory_delta_required": memory_delta_required,
        "reasons": reasons,
        "selected_lane": selected_lane,
        "recommended_obsidian_summaries": recommended[:20],
        "target_note": str(note_path),
        "note_applied": False,
        "applied_note_path": "",
        "applied_note_sha256": "",
        "note_slug": note_slug,
        "artifact_refs": {
            "ceo_replay": f"reports/ceo_runs/{ceo_run_id}/ceo_replay.yaml",
            "ceo_eval_suite": f"reports/ceo_runs/{ceo_run_id}/ceo_eval_suite.yaml",
            "portfolio_allocator": f"reports/ceo_runs/{ceo_run_id}/portfolio_allocator.yaml",
            "knowledge_graph_delta": f"reports/ceo_runs/{ceo_run_id}/knowledge_graph_delta.yaml",
        },
        "guardrail": "Memory deltas are curated routing memory only; they are not validation proof or production approval.",
        "production_effect": "none",
    }


def render_ceo_memory_delta(delta: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Memory Delta",
        "",
        f"Generated: {delta.get('generated_at')}",
        f"Run: {delta.get('run_id')}",
        f"Lab run: {delta.get('lab_run_id')}",
        f"Status: {delta.get('status')}",
        f"Memory delta required: {delta.get('memory_delta_required')}",
        f"Target note: {delta.get('target_note')}",
        f"Note applied: {delta.get('note_applied')}",
        f"Applied note sha256: {delta.get('applied_note_sha256') or 'none'}",
        "",
        "## Reasons",
        "",
    ]
    reasons = delta.get("reasons", []) or []
    lines.extend(f"- {item}" for item in reasons) if reasons else lines.append("- none")
    lines.extend(["", "## Artifact Refs", ""])
    for key, value in (delta.get("artifact_refs", {}) or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", str(delta.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_ceo_memory_delta_note(delta: dict[str, Any]) -> str:
    run_id = str(delta.get("run_id", ""))
    updated_at = utc_now_iso()[:10]
    selected_lane = delta.get("selected_lane", {}) or {}
    refs = delta.get("artifact_refs", {}) or {}
    lines = [
        "---",
        "rf_type: map",
        f"map_id: {delta.get('note_slug')}",
        "status: active",
        f"updated_at: {updated_at}",
        "production_effect: none",
        "linked_concepts:",
        "  - CEO Eval Suite",
        "  - CEO Replay",
        "  - CEO Portfolio Allocator",
        "  - CEO State Machine",
        "  - True CEO Autonomy",
        "---",
        "",
        f"# CEO Memory Delta - {run_id}",
        "",
        "This note is curated routing memory for a CEO run. It is not product proof.",
        "",
        "## Run State",
        "",
        f"- Run: `{run_id}`",
        f"- Lab run: `{delta.get('lab_run_id')}`",
        f"- Memory delta required: `{delta.get('memory_delta_required')}`",
        f"- Selected lane: `{selected_lane.get('lane_id', '')}`",
        f"- Selected next action: `{selected_lane.get('next_action', '')}`",
        "",
        "## Why This Matters",
        "",
    ]
    reasons = delta.get("reasons", []) or []
    lines.extend(f"- {item}" for item in reasons) if reasons else lines.append("- No durable memory delta was required.")
    lines.extend(["", "## Artifact Refs", ""])
    for key, value in refs.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Reopen Conditions",
            "",
            "- Run `ceo replay`, `ceo eval-suite`, and `ceo portfolio-allocator` before continuing this run.",
            "- Do not treat this note as runtime authority if generated CEO artifacts disagree.",
            "- Do not mutate production behavior from this note.",
            "",
            "Related:",
            "",
            "- [[CEO Eval Suite]]",
            "- [[CEO Replay]]",
            "- [[CEO Portfolio Allocator]]",
            "- [[CEO State Machine]]",
            "- [[True CEO Autonomy]]",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_memory_delta(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    replay_result = run_ceo_replay(options)
    eval_result = run_ceo_eval_suite(options)
    allocator_result = run_ceo_portfolio_allocator(options)
    delta = build_ceo_memory_delta(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        replay=replay_result["replay"],
        eval_suite=eval_result["eval_suite"],
        portfolio_allocator=allocator_result["allocator"],
        knowledge_graph_delta=_load_yaml_if_exists(root / "knowledge_graph_delta.yaml"),
    )
    path = root / "memory_delta.yaml"
    report_path = root / "memory_delta.md"
    atomic_write_yaml(path, delta)
    atomic_write_text(report_path, render_ceo_memory_delta(delta))
    paths: dict[str, Path] = {"memory_delta": path, "memory_delta_report": report_path}
    if options.apply and delta.get("memory_delta_required"):
        note_path = options.source_root / str(delta.get("target_note"))
        note_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(note_path, render_ceo_memory_delta_note(delta))
        delta = {
            **delta,
            "note_applied": True,
            "applied_note_path": str(note_path),
            "applied_note_sha256": _file_sha256(note_path),
        }
        atomic_write_yaml(path, delta)
        atomic_write_text(report_path, render_ceo_memory_delta(delta))
        paths["memory_delta_note"] = note_path
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "memory_delta": delta,
        "paths": paths,
    }


def _guardrail_audit_payload_refs(payload: Any, *, path: str = "$") -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_path = f"{path}.{key}"
            if key in {"production_effect", "product_language_allowed", "promotion_authority"}:
                refs.append({"path": key_path, "field": str(key), "value": value})
            refs.extend(_guardrail_audit_payload_refs(value, path=key_path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            refs.extend(_guardrail_audit_payload_refs(value, path=f"{path}[{index}]"))
    return refs


def _load_jsonl_guardrail_payloads(path: Path) -> list[tuple[str, Any]]:
    payloads: list[tuple[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return payloads
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payloads.append((f"{path.name}:{index}", json.loads(stripped)))
        except json.JSONDecodeError:
            payloads.append((f"{path.name}:{index}", {"json_parse_error": True}))
    return payloads


def _guardrail_audit_violation(
    *, artifact: str, violation: str, observed: Any, key_path: str, field: str
) -> dict[str, Any]:
    return {
        "artifact": artifact,
        "violation": violation,
        "observed": observed,
        "path": key_path,
        "field": field,
        "production_effect": "none",
    }


def build_ceo_guardrail_audit(*, ceo_run_id: str, lab_run_id: str, root: Path) -> dict[str, Any]:
    scanned: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    candidate_paths = sorted([*root.rglob("*.yaml"), *root.rglob("*.jsonl")])
    for path in candidate_paths:
        if path.name == "guardrail_audit.yaml":
            continue
        artifact = str(path.relative_to(root))
        payload_refs: list[dict[str, Any]] = []
        if path.suffix == ".jsonl":
            loaded_payloads = _load_jsonl_guardrail_payloads(path)
            for source, payload in loaded_payloads:
                payload_refs.extend(_guardrail_audit_payload_refs(payload, path=f"${source}"))
        else:
            payload = _load_yaml_if_exists(path)
            if payload:
                payload_refs = _guardrail_audit_payload_refs(payload)
        if not payload_refs:
            continue
        production_effect_refs = [item for item in payload_refs if item["field"] == "production_effect"]
        product_language_refs = [item for item in payload_refs if item["field"] == "product_language_allowed"]
        promotion_authority_refs = [item for item in payload_refs if item["field"] == "promotion_authority"]
        item = {
            "artifact": artifact,
            "production_effect": (
                str(production_effect_refs[0]["value"]) if production_effect_refs else "missing"
            ),
            "product_language_allowed": (
                product_language_refs[0]["value"] if product_language_refs else None
            ),
            "promotion_authority": (
                str(promotion_authority_refs[0]["value"]) if promotion_authority_refs else None
            ),
            "guardrail_ref_count": len(payload_refs),
        }
        scanned.append(item)
        for ref in production_effect_refs:
            production_effect = str(ref["value"])
            if production_effect not in {"", "none"}:
                violations.append(
                    _guardrail_audit_violation(
                        artifact=artifact,
                        violation="non_none_production_effect",
                        observed=production_effect,
                        key_path=str(ref["path"]),
                        field="production_effect",
                    )
                )
        for ref in product_language_refs:
            if ref["value"] is True:
                violations.append(
                    _guardrail_audit_violation(
                        artifact=artifact,
                        violation="product_language_allowed_true",
                        observed=ref["value"],
                        key_path=str(ref["path"]),
                        field="product_language_allowed",
                    )
                )
        for ref in promotion_authority_refs:
            promotion_authority = str(ref["value"])
            if promotion_authority not in {"", "none", "user_only"}:
                violations.append(
                    _guardrail_audit_violation(
                        artifact=artifact,
                        violation="non_user_promotion_authority",
                        observed=promotion_authority,
                        key_path=str(ref["path"]),
                        field="promotion_authority",
                    )
                )
    return {
        "model": CEO_GUARDRAIL_AUDIT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "pass" if not violations else "fail",
        "scanned_artifact_count": len(scanned),
        "violation_count": len(violations),
        "scanned_artifacts": scanned,
        "violations": violations,
        "guardrail": "CEO artifacts must not claim production mutation or product-language permission without explicit approval.",
        "production_effect": "none",
    }


def render_ceo_guardrail_audit(audit: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Guardrail Audit",
        "",
        f"Generated: {audit.get('generated_at')}",
        f"Run: {audit.get('run_id')}",
        f"Lab run: {audit.get('lab_run_id')}",
        f"Status: {audit.get('status')}",
        f"Scanned artifacts: {audit.get('scanned_artifact_count')}",
        f"Violations: {audit.get('violation_count')}",
        "",
        "## Violations",
        "",
    ]
    for item in audit.get("violations", []) or []:
        lines.append(
            f"- {item.get('artifact')}: {item.get('violation')} "
            f"path={item.get('path') or '$'} observed={item.get('observed')}"
        )
    if not audit.get("violations"):
        lines.append("- none")
    lines.extend(["", str(audit.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_guardrail_audit(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    audit = build_ceo_guardrail_audit(ceo_run_id=ceo_run_id, lab_run_id=lab_run_id, root=root)
    path = root / "guardrail_audit.yaml"
    report_path = root / "guardrail_audit.md"
    atomic_write_yaml(path, audit)
    atomic_write_text(report_path, render_ceo_guardrail_audit(audit))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "guardrail_audit": audit,
        "paths": {"guardrail_audit": path, "guardrail_audit_report": report_path},
    }


def _preflight_blocker(blocker: str, *, source: str, category: str, severity: str = "blocker") -> dict[str, str]:
    return {"blocker": blocker, "source": source, "category": category, "severity": severity}


def build_ceo_preflight_gate(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    stop_requested: bool,
    true_blocker: bool,
    trace_grade: dict[str, Any],
    approval_queue: dict[str, Any],
    replay: dict[str, Any],
    eval_suite: dict[str, Any],
    guardrail_audit: dict[str, Any],
    memory_delta: dict[str, Any],
    heartbeat_budget: dict[str, Any],
    artifact_coherence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    artifact_coherence = artifact_coherence or {}
    replay_issues = {str(item) for item in replay.get("issues", []) or []}
    bootstrap_no_prior_action = (
        int(replay.get("action_count", 0) or 0) == 0
        and replay_issues == {"missing_action_ledger_entries"}
        and not (replay.get("artifact_checks", {}) or {}).get("binding_action_result", {}).get("exists")
    )
    eval_blocking_cases = {
        str(item)
        for item in (eval_suite.get("nine_nine_readiness", {}) or {}).get("blocking_case_ids", []) or []
    }
    bootstrap_eval_only = bootstrap_no_prior_action and eval_blocking_cases <= {
        "replayable_action_timeline",
        "policy_eval_fixtures_pass",
    }
    bootstrap_artifact_coherence_only = (
        bootstrap_no_prior_action
        and artifact_coherence.get("status") == "fail"
        and {
            str(item.get("artifact", ""))
            for item in artifact_coherence.get("issues", []) or []
            if set(str(issue) for issue in item.get("issues", []) or []) - {"missing_artifact"}
        }
        == set()
    )
    if stop_requested:
        blockers.append(_preflight_blocker("stop_requested", source="stop.request", category="runtime_authority"))
    if true_blocker:
        blockers.append(_preflight_blocker("true_blocker", source="company_status", category="runtime_authority"))
    if trace_grade.get("verdict") == "fail":
        blockers.append(_preflight_blocker("trace_grade_failed", source="trace_grade.yaml", category="trace_reliability"))
    if int(approval_queue.get("pending_count", 0) or 0) > 0:
        blockers.append(_preflight_blocker("pending_user_approval", source="approval_queue.yaml", category="approval_authority"))
    if replay.get("status") == "replay_gaps" and not bootstrap_no_prior_action:
        blockers.append(_preflight_blocker("replay_gaps", source="ceo_replay.yaml", category="replay_integrity"))
    if eval_suite.get("status") == "fail" and not bootstrap_eval_only:
        blockers.append(_preflight_blocker("eval_suite_failed", source="ceo_eval_suite.yaml", category="eval_readiness"))
    if guardrail_audit.get("status") == "fail":
        blockers.append(_preflight_blocker("guardrail_audit_failed", source="guardrail_audit.yaml", category="product_guardrail"))
    artifact_coherence_hard_issues = _hard_artifact_coherence_issues(artifact_coherence)
    if artifact_coherence.get("status") == "fail" and artifact_coherence_hard_issues and not bootstrap_artifact_coherence_only:
        blockers.append(_preflight_blocker("artifact_coherence_failed", source="artifact_coherence.yaml", category="artifact_coherence"))
    if _memory_delta_blocks_dispatch(memory_delta=memory_delta, replay=replay, eval_suite=eval_suite):
        blockers.append(_preflight_blocker("memory_delta_unresolved", source="memory_delta.yaml", category="memory_handoff"))
    if heartbeat_budget.get("budget_elapsed"):
        blockers.append(
            _preflight_blocker(
                "heartbeat_plan_time_budget_elapsed",
                source="heartbeat_plan.yaml",
                category="heartbeat_budget",
            )
        )
    blocker_categories = sorted({str(item.get("category", "")) for item in blockers if item.get("category")})
    return {
        "model": CEO_PREFLIGHT_GATE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "blocked" if blockers else "pass",
        "safe_to_execute": not blockers,
        "blockers": blockers,
        "blocker_categories": blocker_categories,
        "source_status": {
            "trace_verdict": trace_grade.get("verdict", ""),
            "trace_score": trace_grade.get("score", ""),
            "trace_recommended_next_action": trace_grade.get("recommended_next_action", ""),
            "trace_issues": trace_grade.get("issues", []),
            "trace_manual_data_import_required": _trace_grade_manual_data_import_required(trace_grade),
            "pending_approvals": approval_queue.get("pending_count", 0),
            "replay_status": replay.get("status", ""),
            "eval_suite_status": eval_suite.get("status", ""),
            "guardrail_audit_status": guardrail_audit.get("status", ""),
            "artifact_coherence_status": artifact_coherence.get("status", ""),
            "artifact_coherence_hard_issue_count": len(artifact_coherence_hard_issues),
            "memory_delta_status": memory_delta.get("status", ""),
            "heartbeat_budget_status": heartbeat_budget.get("status", ""),
            "stop_requested": stop_requested,
            "true_blocker": true_blocker,
            "bootstrap_no_prior_action": bootstrap_no_prior_action,
            "bootstrap_artifact_coherence_only": bootstrap_artifact_coherence_only,
        },
        "guardrail": "Preflight gate blocks CEO dispatch when generated safety artifacts indicate unresolved risk.",
        "production_effect": "none",
    }


def _hard_artifact_coherence_issues(artifact_coherence: dict[str, Any]) -> list[dict[str, Any]]:
    latest_has_current_evidence = artifact_coherence.get("latest_action_has_current_transition_evidence") is True
    if not latest_has_current_evidence and not str(artifact_coherence.get("latest_action_generated_at", "")):
        return []
    hard: list[dict[str, Any]] = []
    for item in artifact_coherence.get("issues", []) or []:
        artifact = str(item.get("artifact", ""))
        issue_names = {str(issue) for issue in item.get("issues", []) or []}
        if not issue_names:
            continue
        if artifact in {"latest_decision_packet", "strategy_capital_dashboard"} and issue_names <= {"missing_artifact"}:
            continue
        if artifact == "preflight_gate" and issue_names <= {"missing_artifact", "stale_before_latest_action"}:
            continue
        if artifact in {
            "approval_queue",
            "approval_status",
            "role_task_queue",
            "role_dispatch",
            "role_result_validation",
            "repair_apply",
            "action_board",
            "decision_quality",
            "operator_brief",
        } and issue_names <= {
            "missing_artifact",
            "missing_generated_at",
            "stale_before_latest_action",
        }:
            continue
        if artifact == "handoff_semantics" and issue_names.isdisjoint(CEO_HARD_HANDOFF_SEMANTIC_ISSUES):
            continue
        if not latest_has_current_evidence and artifact in {"action_contract", "dispatch_receipt"} and issue_names <= {
            "missing_artifact",
            "missing_action_contract",
            "action_contract_decision_mismatch",
            "missing_action_dispatch_receipt_ref",
        }:
            continue
        if issue_names == {"dispatch_receipt_trust_fingerprint_drift"}:
            mismatches = (item.get("evidence", {}) or {}).get("trust_fingerprint_mismatches", []) or []
            mismatch_artifacts = {str(mismatch.get("artifact", "")) for mismatch in mismatches}
            mutable_diagnostics = {
                "trace_grade",
                "ceo_replay",
                "ceo_eval_suite",
                "guardrail_audit",
                "mission_score",
                "artifact_coherence",
                "approval_queue",
                "approval_status",
                "role_task_queue",
                "role_dispatch",
                "role_result_validation",
                "repair_apply",
                "action_board",
                "decision_quality",
                "operator_brief",
            }
            if mismatch_artifacts and mismatch_artifacts <= mutable_diagnostics:
                continue
        hard.append(item)
    return hard


def _memory_delta_blocks_dispatch(
    *,
    memory_delta: dict[str, Any],
    replay: dict[str, Any],
    eval_suite: dict[str, Any],
) -> bool:
    if not memory_delta.get("memory_delta_required") or memory_delta.get("note_applied"):
        return False
    reasons = {str(item) for item in memory_delta.get("reasons", []) or []}
    if not memory_delta.get("computed_for_enforced_preflight"):
        return True
    hard_reasons = {
        reason
        for reason in reasons
        if not reason.startswith("high_priority_lane_") and reason != "knowledge_graph_delta_recommended"
    }
    replay_issues = {str(item) for item in replay.get("issues", []) or []}
    bootstrap_no_prior_action = (
        int(replay.get("action_count", 0) or 0) == 0
        and replay_issues == {"missing_action_ledger_entries"}
        and not (replay.get("artifact_checks", {}) or {}).get("binding_action_result", {}).get("exists")
    )
    if bootstrap_no_prior_action:
        hard_reasons.discard("replay_gap")
        eval_blocking_cases = {
            str(item)
            for item in (eval_suite.get("nine_nine_readiness", {}) or {}).get("blocking_case_ids", []) or []
        }
        if eval_blocking_cases <= {"replayable_action_timeline", "policy_eval_fixtures_pass"}:
            hard_reasons.discard("eval_suite_attention_required")
    return bool(hard_reasons)


def render_ceo_preflight_gate(gate: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Preflight Gate",
        "",
        f"Generated: {gate.get('generated_at')}",
        f"Run: {gate.get('run_id')}",
        f"Lab run: {gate.get('lab_run_id')}",
        f"Status: {gate.get('status')}",
        f"Safe to execute: {gate.get('safe_to_execute')}",
        "",
        "## Blockers",
        "",
    ]
    for item in gate.get("blockers", []) or []:
        lines.append(
            "- "
            f"{item.get('blocker')} category={item.get('category')} "
            f"severity={item.get('severity')} source={item.get('source')}"
        )
    if not gate.get("blockers"):
        lines.append("- none")
    source_status = gate.get("source_status", {}) or {}
    lines.extend(
        [
            "",
            "## Source Status",
            "",
            f"- Trace verdict: {source_status.get('trace_verdict') or 'none'}",
            f"- Trace score: {source_status.get('trace_score') if source_status.get('trace_score') != '' else 'n/a'}",
            f"- Trace recommended next action: {source_status.get('trace_recommended_next_action') or 'none'}",
            f"- Trace manual data import required: {source_status.get('trace_manual_data_import_required') if source_status.get('trace_manual_data_import_required') != '' else 'n/a'}",
            f"- Trace issues: {source_status.get('trace_issues') or []}",
        ]
    )
    lines.extend(["", str(gate.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_preflight_gate(options: CeoOpsOptions, *, enforce_memory_delta: bool = False) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    preflight_options = _with_ceo_context(options, context="preflight_refresh")
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    trace_result = run_ceo_trace_grade(preflight_options)
    approval_result = run_ceo_approval_queue(preflight_options)
    replay_result = run_ceo_replay(preflight_options)
    eval_result = run_ceo_eval_suite(preflight_options)
    guardrail_result = run_ceo_guardrail_audit(preflight_options)
    coherence_result = run_ceo_artifact_coherence(preflight_options)
    memory_delta = _load_yaml_if_exists(root / "memory_delta.yaml")
    if not memory_delta:
        if enforce_memory_delta:
            memory_delta_result = run_ceo_memory_delta(replace(preflight_options, apply=False))
            memory_delta = {**memory_delta_result["memory_delta"], "computed_for_enforced_preflight": True}
        else:
            memory_delta = {
                "model": CEO_MEMORY_DELTA_MODEL,
                "status": "not_evaluated",
                "memory_delta_required": False,
                "note_applied": False,
                "production_effect": "none",
            }
    elif not enforce_memory_delta:
        memory_delta = {**memory_delta, "memory_delta_required": False}
    heartbeat_budget = build_heartbeat_plan_budget_status(_load_yaml_if_exists(root / "heartbeat_plan.yaml"))
    gate = build_ceo_preflight_gate(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        stop_requested=is_stop_requested(options, ceo_run_id, lab_run_id),
        true_blocker=bool(company_status.get("true_blocker")),
        trace_grade=trace_result["grade"],
        approval_queue=approval_result["queue"],
        replay=replay_result["replay"],
        eval_suite=eval_result["eval_suite"],
        guardrail_audit=guardrail_result["guardrail_audit"],
        memory_delta=memory_delta,
        heartbeat_budget=heartbeat_budget,
        artifact_coherence=coherence_result["coherence"],
    )
    path = root / "preflight_gate.yaml"
    report_path = root / "preflight_gate.md"
    atomic_write_yaml(path, gate)
    atomic_write_text(report_path, render_ceo_preflight_gate(gate))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "preflight_gate": gate,
        "paths": {"preflight_gate": path, "preflight_gate_report": report_path},
    }


def _brief_artifact_status(name: str, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact": name,
        "path": str(path),
        "exists": path.exists(),
        "model": payload.get("model", ""),
        "status": payload.get("status", payload.get("verdict", "")),
        "production_effect": payload.get("production_effect", "none" if payload else ""),
    }


def _artifact_coherence_item(
    name: str,
    path: Path,
    payload: dict[str, Any],
    *,
    ceo_run_id: str,
    lab_run_id: str,
    latest_action_at: datetime | None,
    require_generated_after_action: bool,
) -> dict[str, Any]:
    exists = path.exists()
    generated_at = _parse_utc_datetime(payload.get("generated_at")) if payload else None
    issues: list[str] = []
    if not exists:
        issues.append("missing_artifact")
    if payload:
        if payload.get("run_id") and str(payload.get("run_id")) != ceo_run_id:
            issues.append("run_id_mismatch")
        if payload.get("lab_run_id") and str(payload.get("lab_run_id")) != lab_run_id:
            issues.append("lab_run_id_mismatch")
    if exists and require_generated_after_action and latest_action_at:
        if generated_at is None:
            issues.append("missing_generated_at")
        elif generated_at < latest_action_at:
            issues.append("stale_before_latest_action")
    return {
        "artifact": name,
        "path": str(path),
        "exists": exists,
        "sha256": _file_sha256(path) if exists else "",
        "model": payload.get("model", ""),
        "status": payload.get("status", payload.get("verdict", "")),
        "generated_at": payload.get("generated_at", ""),
        "issues": issues,
        "production_effect": payload.get("production_effect", "none" if payload else ""),
    }


def _handoff_semantic_coherence_issues(
    *,
    action_board: dict[str, Any],
    decision_quality: dict[str, Any],
    operator_brief: dict[str, Any],
    stop_requested: bool = False,
) -> dict[str, Any] | None:
    issues: list[str] = []
    evidence: dict[str, Any] = {}
    primary = action_board.get("primary_action", {}) or {}
    situation = operator_brief.get("current_situation", {}) or {}
    board_status = str(action_board.get("status", ""))
    primary_action = str(primary.get("action_id", ""))
    primary_kind = str(primary.get("command_kind", ""))
    decision_effective_action = str(decision_quality.get("effective_runtime_action", ""))
    decision_effective_kind = str(decision_quality.get("effective_runtime_command_kind", ""))
    operator_status = str(operator_brief.get("status", ""))
    if stop_requested:
        stale_safe_signals: list[str] = []
        if board_status == "bounded_action_available":
            stale_safe_signals.append("action_board_bounded_action_available")
        if primary.get("can_execute_now") is True:
            stale_safe_signals.append("action_board_primary_executable")
        if decision_quality.get("effective_runtime_can_execute_now") is True:
            stale_safe_signals.append("decision_quality_effective_runtime_executable")
        if decision_quality.get("selected_action_is_executable_now") is True:
            stale_safe_signals.append("decision_quality_selected_action_executable")
        if operator_status == "ready_for_one_operator_step":
            stale_safe_signals.append("operator_brief_ready_for_one_operator_step")
        if stale_safe_signals:
            issues.append("live_stop_runtime_authority_mismatch")
            evidence["live_stop_stale_safe_signals"] = stale_safe_signals
    if action_board and decision_quality:
        if primary_action and decision_effective_action and primary_action != decision_effective_action:
            issues.append("decision_quality_effective_action_mismatch")
        if primary_kind and decision_effective_kind and primary_kind != decision_effective_kind:
            issues.append("decision_quality_effective_kind_mismatch")
    if action_board and operator_brief:
        if situation.get("action_board_status") and str(situation.get("action_board_status")) != board_status:
            issues.append("operator_brief_action_board_status_mismatch")
        if situation.get("primary_action") and str(situation.get("primary_action")) != primary_action:
            issues.append("operator_brief_primary_action_mismatch")
    if board_status == "manual_gate_required":
        if primary.get("can_execute_now") is True:
            issues.append("manual_gate_primary_marked_executable")
        runnable_under_gate = [
            str(item.get("action_id", ""))
            for item in action_board.get("runnable_repairs", []) or []
            if item.get("can_execute_now") is True
        ]
        if runnable_under_gate:
            issues.append("manual_gate_has_runnable_actions")
            evidence["runnable_under_manual_gate"] = runnable_under_gate
        if primary.get("requires_manual_gate") is not True:
            issues.append("manual_gate_primary_not_marked_manual")
        if decision_quality:
            if decision_quality.get("effective_runtime_can_execute_now") is True:
                issues.append("manual_gate_decision_quality_effective_runtime_executable")
            if decision_quality.get("selected_action_is_executable_now") is True:
                issues.append("manual_gate_decision_quality_selected_action_executable")
            if decision_quality.get("runtime_blocked") is not True:
                issues.append("manual_gate_decision_quality_not_runtime_blocked")
            block_reason = str(decision_quality.get("runtime_block_reason", ""))
            if block_reason and not block_reason.startswith("manual_gate_required:"):
                issues.append("manual_gate_decision_quality_block_reason_mismatch")
        if operator_brief and operator_status != "waiting_on_manual_gate":
            issues.append("manual_gate_operator_brief_status_mismatch")
    elif board_status == "bounded_action_available":
        if primary.get("can_execute_now") is not True:
            issues.append("bounded_action_primary_not_executable")
        if decision_quality:
            if decision_quality.get("effective_runtime_can_execute_now") is not True:
                issues.append("bounded_action_decision_quality_not_executable")
            if decision_effective_action and primary_action and decision_effective_action != primary_action:
                issues.append("bounded_action_effective_runtime_mismatch")
        if operator_brief and operator_status != "ready_for_one_operator_step":
            issues.append("bounded_action_operator_brief_status_mismatch")
    if not issues:
        return None
    evidence.update(
        {
            "action_board_status": board_status,
            "action_board_primary_action": primary_action,
            "action_board_primary_kind": primary_kind,
            "decision_effective_runtime_action": decision_effective_action,
            "decision_effective_runtime_kind": decision_effective_kind,
            "decision_runtime_blocked": decision_quality.get("runtime_blocked", ""),
            "decision_selected_action_executable": decision_quality.get("selected_action_is_executable_now", ""),
            "operator_brief_status": operator_status,
            "operator_brief_action_board_status": situation.get("action_board_status", ""),
            "operator_brief_primary_action": situation.get("primary_action", ""),
            "stop_requested": stop_requested,
        }
    )
    return {
        "artifact": "handoff_semantics",
        "issues": sorted(set(issues)),
        "path": "",
        "evidence": evidence,
    }


def build_ceo_artifact_coherence(*, ceo_run_id: str, lab_run_id: str, root: Path) -> dict[str, Any]:
    ledger_entries = _read_jsonl_entries(root / "ceo_action_ledger.jsonl")
    binding_action = _load_yaml_if_exists(root / "binding_action_result.yaml")
    latest_action = binding_action or (ledger_entries[-1] if ledger_entries else {})
    latest_action_at = _parse_utc_datetime(latest_action.get("generated_at")) if latest_action else None
    action_contract_path = root / "action_contract.yaml"
    action_contract = _load_yaml_if_exists(action_contract_path)
    dispatch_receipt_path = root / "dispatch_receipt.yaml"
    dispatch_receipt = _load_yaml_if_exists(dispatch_receipt_path)
    artifact_specs = [
        ("latest_decision_packet", root / "executive_decision_packet.md", {"status": "exists" if (root / "executive_decision_packet.md").exists() else "missing"}, False),
        ("action_contract", action_contract_path, action_contract, False),
        ("dispatch_receipt", dispatch_receipt_path, dispatch_receipt, False),
        ("preflight_gate", root / "preflight_gate.yaml", _load_yaml_if_exists(root / "preflight_gate.yaml"), True),
        ("ceo_replay", root / "ceo_replay.yaml", _load_yaml_if_exists(root / "ceo_replay.yaml"), True),
        ("ceo_eval_suite", root / "ceo_eval_suite.yaml", _load_yaml_if_exists(root / "ceo_eval_suite.yaml"), True),
        ("mission_score", root / "mission_score.yaml", _load_yaml_if_exists(root / "mission_score.yaml"), True),
        (
            "strategy_capital_dashboard",
            root / "strategy_capital_dashboard.yaml",
            _load_yaml_if_exists(root / "strategy_capital_dashboard.yaml"),
            True,
        ),
        ("approval_queue", root / "approval_queue.yaml", _load_yaml_if_exists(root / "approval_queue.yaml"), True),
        ("approval_status", root / "approval_status.yaml", _load_yaml_if_exists(root / "approval_status.yaml"), True),
        ("role_task_queue", root / "role_task_queue.yaml", _load_yaml_if_exists(root / "role_task_queue.yaml"), True),
        ("role_dispatch", root / "role_dispatch.yaml", _load_yaml_if_exists(root / "role_dispatch.yaml"), True),
        (
            "role_result_validation",
            root / "role_result_validation.yaml",
            _load_yaml_if_exists(root / "role_result_validation.yaml"),
            True,
        ),
        ("repair_apply", root / "repair_apply.yaml", _load_yaml_if_exists(root / "repair_apply.yaml"), True),
        ("action_board", root / "action_board.yaml", _load_yaml_if_exists(root / "action_board.yaml"), True),
        ("decision_quality", root / "decision_quality.yaml", _load_yaml_if_exists(root / "decision_quality.yaml"), True),
        ("operator_brief", root / "operator_brief.yaml", _load_yaml_if_exists(root / "operator_brief.yaml"), True),
    ]
    artifacts = [
        _artifact_coherence_item(
            name,
            path,
            payload,
            ceo_run_id=ceo_run_id,
            lab_run_id=lab_run_id,
            latest_action_at=latest_action_at,
            require_generated_after_action=require_generated_after_action,
        )
        for name, path, payload, require_generated_after_action in artifact_specs
    ]
    issues = [
        {
            "artifact": item.get("artifact"),
            "issues": item.get("issues"),
            "path": item.get("path"),
        }
        for item in artifacts
        if item.get("issues")
    ]
    if latest_action:
        latest_decision = str(latest_action.get("decision", ""))
        semantic_action_contract_issues: list[str] = []
        if not action_contract:
            semantic_action_contract_issues.append("missing_action_contract")
        elif latest_decision and str(action_contract.get("decision", "")) != latest_decision:
            semantic_action_contract_issues.append("action_contract_decision_mismatch")
        if semantic_action_contract_issues:
            issues.append(
                {
                    "artifact": "action_contract",
                    "issues": semantic_action_contract_issues,
                    "path": str(action_contract_path),
                    "evidence": {
                        "contract_decision": action_contract.get("decision", ""),
                        "latest_action_decision": latest_decision,
                    },
                }
            )

        dispatch_ref = latest_action.get("dispatch_receipt", {}) or {}
        dispatch_ref_path = _resolve_report_ref_path(root, dispatch_ref.get("path", ""))
        dispatch_ref_exists = bool(dispatch_ref and dispatch_ref_path.exists())
        dispatch_ref_payload = _load_yaml_if_exists(dispatch_ref_path) if dispatch_ref_exists else {}
        semantic_dispatch_issues: list[str] = []
        if not dispatch_ref:
            semantic_dispatch_issues.append("missing_action_dispatch_receipt_ref")
        elif not dispatch_ref_exists:
            semantic_dispatch_issues.append("missing_action_dispatch_receipt_snapshot")
        else:
            trust_fingerprint_mismatches: list[dict[str, Any]] = []
            if str(dispatch_ref.get("sha256", "")) != _file_sha256(dispatch_ref_path):
                semantic_dispatch_issues.append("action_dispatch_receipt_sha_mismatch")
            if str(dispatch_ref_payload.get("decision", "")) != latest_decision:
                semantic_dispatch_issues.append("dispatch_receipt_decision_mismatch")
            if dispatch_ref_path.name == "dispatch_receipt.yaml" or dispatch_ref_path.parent.name != "dispatch_receipts":
                semantic_dispatch_issues.append("dispatch_receipt_not_immutable_snapshot")
            if dispatch_ref_payload.get("product_language_allowed") is not False:
                semantic_dispatch_issues.append("dispatch_receipt_product_language_not_false")
            if dispatch_ref_payload.get("production_effect") != "none":
                semantic_dispatch_issues.append("dispatch_receipt_non_none_production_effect")
            for fingerprint_name, fingerprint in (dispatch_ref_payload.get("trust_artifact_fingerprints", {}) or {}).items():
                if not isinstance(fingerprint, dict) or fingerprint.get("exists") is not True:
                    continue
                fingerprint_path = _resolve_report_ref_path(root, fingerprint.get("path", ""))
                actual_exists = fingerprint_path.exists()
                expected_sha = str(fingerprint.get("sha256", ""))
                actual_sha = _file_sha256(fingerprint_path) if actual_exists else ""
                if not actual_exists:
                    trust_fingerprint_mismatches.append(
                        {
                            "artifact": str(fingerprint_name),
                            "reason": "fingerprinted_artifact_missing",
                            "path": str(fingerprint_path),
                            "expected_sha256": expected_sha,
                            "actual_sha256": "",
                        }
                    )
                elif not expected_sha:
                    trust_fingerprint_mismatches.append(
                        {
                            "artifact": str(fingerprint_name),
                            "reason": "fingerprint_missing_expected_sha256",
                            "path": str(fingerprint_path),
                            "expected_sha256": expected_sha,
                            "actual_sha256": actual_sha,
                        }
                    )
                elif expected_sha != actual_sha:
                    trust_fingerprint_mismatches.append(
                        {
                            "artifact": str(fingerprint_name),
                            "reason": "fingerprinted_artifact_sha_mismatch",
                            "path": str(fingerprint_path),
                            "expected_sha256": expected_sha,
                            "actual_sha256": actual_sha,
                        }
                    )
            if trust_fingerprint_mismatches:
                semantic_dispatch_issues.append("dispatch_receipt_trust_fingerprint_drift")
        if semantic_dispatch_issues:
            issues.append(
                {
                    "artifact": "dispatch_receipt",
                    "issues": semantic_dispatch_issues,
                    "path": str(dispatch_ref_path) if dispatch_ref else "",
                    "evidence": {
                        "active_receipt_path": str(dispatch_receipt_path),
                        "latest_action_decision": latest_decision,
                        "receipt_decision": dispatch_ref_payload.get("decision", ""),
                        "trust_fingerprint_mismatches": trust_fingerprint_mismatches if dispatch_ref_exists else [],
                    },
                }
            )
    handoff_semantic_issue = _handoff_semantic_coherence_issues(
        action_board=_load_yaml_if_exists(root / "action_board.yaml"),
        decision_quality=_load_yaml_if_exists(root / "decision_quality.yaml"),
        operator_brief=_load_yaml_if_exists(root / "operator_brief.yaml"),
        stop_requested=(root / "stop.request").exists(),
    )
    if handoff_semantic_issue:
        issues.append(handoff_semantic_issue)
    coherence = {
        "model": CEO_ARTIFACT_COHERENCE_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "pass",
        "latest_action_generated_at": latest_action.get("generated_at", ""),
        "latest_action_sha256": _file_sha256(root / "binding_action_result.yaml") if (root / "binding_action_result.yaml").exists() else "",
        "latest_action_has_current_transition_evidence": _has_current_transition_evidence(latest_action) if latest_action else False,
        "artifact_count": len(artifacts),
        "issue_count": len(issues),
        "artifacts": artifacts,
        "issues": issues,
        "guardrail": (
            "Artifact coherence checks freshness, lineage, and handoff semantic agreement; it does not "
            "evaluate market evidence or authorize action."
        ),
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }
    hard_issues = _hard_artifact_coherence_issues(coherence)
    hard_issue_ids = {id(item) for item in hard_issues}
    for item in issues:
        item["severity"] = "hard" if id(item) in hard_issue_ids else "advisory"
    coherence["hard_issue_count"] = len(hard_issues)
    coherence["advisory_issue_count"] = max(0, len(issues) - len(hard_issues))
    coherence["hard_issues"] = hard_issues
    coherence["status"] = "fail" if hard_issues else ("pass_with_advisory_issues" if issues else "pass")
    return coherence


def render_ceo_artifact_coherence(coherence: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Artifact Coherence",
        "",
        f"Generated: {coherence.get('generated_at')}",
        f"Run: {coherence.get('run_id')}",
        f"Lab run: {coherence.get('lab_run_id')}",
        f"Status: {coherence.get('status')}",
        f"Latest action generated at: {coherence.get('latest_action_generated_at') or 'none'}",
        f"Hard issues: {coherence.get('hard_issue_count', 0)}",
        f"Advisory issues: {coherence.get('advisory_issue_count', 0)}",
        "",
        "## Artifacts",
        "",
    ]
    for item in coherence.get("artifacts", []) or []:
        lines.append(
            "- "
            f"{item.get('artifact')}: exists={item.get('exists')} "
            f"generated_at={item.get('generated_at') or 'missing'} "
            f"issues={item.get('issues') or []}"
        )
    lines.extend(["", "## Issues", ""])
    issues = coherence.get("issues", []) or []
    if issues:
        for item in issues:
            evidence = item.get("evidence", {}) or {}
            evidence_text = f" evidence={evidence}" if evidence else ""
            lines.append(
                f"- {item.get('artifact')}: severity={item.get('severity', 'unknown')} "
                f"issues={item.get('issues')} path={item.get('path')}{evidence_text}"
            )
    else:
        lines.append("- none")
    lines.extend(["", str(coherence.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_artifact_coherence(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    coherence = build_ceo_artifact_coherence(ceo_run_id=ceo_run_id, lab_run_id=lab_run_id, root=root)
    path = root / "artifact_coherence.yaml"
    report_path = root / "artifact_coherence.md"
    atomic_write_yaml(path, coherence)
    atomic_write_text(report_path, render_ceo_artifact_coherence(coherence))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "coherence": coherence,
        "paths": {"artifact_coherence": path, "artifact_coherence_report": report_path},
    }


def _resumption_authorized_route(root: Path, strategy_capital_dashboard: dict[str, Any]) -> tuple[str, str]:
    action_contract = _load_yaml_if_exists(root / "action_contract.yaml")
    contract_decision = str(action_contract.get("decision", ""))
    if contract_decision:
        return contract_decision, "action_contract"
    strategy = str(strategy_capital_dashboard.get("selected_strategy", ""))
    if strategy and strategy != "run_ceo_status":
        return strategy, "strategy_capital_dashboard"
    return "", "unavailable"


def build_ceo_resumption_brief(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    root: Path,
    stop_requested: bool,
    preflight_gate: dict[str, Any],
    replay: dict[str, Any],
    eval_suite: dict[str, Any],
    mission_score: dict[str, Any],
    strategy_capital_dashboard: dict[str, Any],
    artifact_coherence: dict[str, Any],
    latest_packet: Path,
) -> dict[str, Any]:
    blockers = [str(item.get("blocker", "")) for item in preflight_gate.get("blockers", []) or [] if item.get("blocker")]
    preflight_source_status = preflight_gate.get("source_status", {}) or {}
    readiness = eval_suite.get("nine_nine_readiness", {}) or {}
    advisory = [str(item) for item in readiness.get("advisory_case_ids", []) or []]
    authorized_route, authorized_route_source = _resumption_authorized_route(root, strategy_capital_dashboard)
    if stop_requested:
        resume_status = "blocked_stop_requested"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id {ceo_run_id}"
        rationale = "A stop request is runtime authority. Do not resume without explicit user approval and clear-stop flow."
    elif preflight_gate.get("safe_to_execute") is False:
        resume_status = "blocked_preflight"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo preflight-gate --run-id {ceo_run_id} --enforce-memory-delta"
        rationale = "Preflight reports unresolved blockers; repair or obtain approval before executing another bound action."
    elif eval_suite.get("status") == "fail":
        resume_status = "blocked_eval_suite"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo eval-suite --run-id {ceo_run_id}"
        rationale = "Eval-suite hard failures make the run unsafe to resume until repaired."
    elif not latest_packet.exists():
        resume_status = "diagnostic_missing_decision_packet"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo review --run-id {ceo_run_id}"
        rationale = "No latest decision packet exists, so execute-next has no fresh decision basis."
    elif artifact_coherence.get("status") == "fail" or int(artifact_coherence.get("hard_issue_count", 0) or 0) > 0:
        resume_status = "diagnostic_stale_artifacts"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id {ceo_run_id}"
        rationale = "Trust artifacts are missing, stale, or mismatched; refresh diagnostics before executing."
    elif advisory:
        resume_status = "diagnostic_advisory_before_extended_autonomy"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo strategy-capital-dashboard --run-id {ceo_run_id}"
        rationale = "One bound action may be safe, but advisory readiness gaps should be closed before claiming extended autonomy."
    else:
        resume_status = "safe_for_one_bound_action"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id {ceo_run_id} --apply"
        rationale = "Preflight is clean and no hard eval blocker is visible; run at most one bound action, then re-audit."
    artifact_status = [
        _brief_artifact_status("latest_decision_packet", latest_packet, {"status": "exists" if latest_packet.exists() else "missing"}),
        _brief_artifact_status("preflight_gate", root / "preflight_gate.yaml", preflight_gate),
        _brief_artifact_status("ceo_replay", root / "ceo_replay.yaml", replay),
        _brief_artifact_status("ceo_eval_suite", root / "ceo_eval_suite.yaml", eval_suite),
        _brief_artifact_status("artifact_coherence", root / "artifact_coherence.yaml", artifact_coherence),
        _brief_artifact_status("mission_score", root / "mission_score.yaml", mission_score),
        _brief_artifact_status("strategy_capital_dashboard", root / "strategy_capital_dashboard.yaml", strategy_capital_dashboard),
    ]
    return {
        "model": CEO_RESUMPTION_BRIEF_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "resume_status": resume_status,
        "next_command": next_command,
        "rationale": rationale,
        "authorized_strategic_route": authorized_route if resume_status == "safe_for_one_bound_action" else "",
        "authorized_route_source": authorized_route_source if resume_status == "safe_for_one_bound_action" else "",
        "stop_requested": stop_requested,
        "preflight_status": preflight_gate.get("status", ""),
        "preflight_blockers": blockers,
        "trace_grade_status": preflight_source_status.get("trace_verdict", ""),
        "trace_grade_score": preflight_source_status.get("trace_score", ""),
        "trace_grade_recommended_next_action": preflight_source_status.get("trace_recommended_next_action", ""),
        "trace_grade_issues": preflight_source_status.get("trace_issues", []),
        "trace_grade_manual_data_import_required": preflight_source_status.get(
            "trace_manual_data_import_required",
            "",
        ),
        "eval_suite_status": eval_suite.get("status", ""),
        "artifact_coherence_status": artifact_coherence.get("status", ""),
        "artifact_coherence_hard_issue_count": artifact_coherence.get("hard_issue_count", ""),
        "artifact_coherence_issues": artifact_coherence.get("issues", []),
        "nine_nine_readiness": readiness.get("status", ""),
        "advisory_readiness_gaps": advisory,
        "mission_score": mission_score.get("overall_mission_score", ""),
        "lowest_mission_dimension": mission_score.get("lowest_dimension", ""),
        "strategy_capital_bucket": strategy_capital_dashboard.get("selected_capital_bucket", ""),
        "strategy_capital_action": strategy_capital_dashboard.get("selected_strategy", ""),
        "artifact_status": artifact_status,
        "guardrails": [
            "This brief is diagnostic only.",
            "Run at most one bound action after a safe brief, then regenerate preflight and the brief.",
            "It cannot authorize product language, promotion, formula changes, Pine/default changes, scores, rankings, states, or alerts.",
        ],
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_resumption_brief(brief: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Resumption Brief",
        "",
        f"Generated: {brief.get('generated_at')}",
        f"Run: {brief.get('run_id')}",
        f"Lab run: {brief.get('lab_run_id')}",
        f"Resume status: {brief.get('resume_status')}",
        f"Next command: `{brief.get('next_command')}`",
        f"Rationale: {brief.get('rationale')}",
        f"Authorized strategic route: {brief.get('authorized_strategic_route') or 'none'}",
        f"Authorized route source: {brief.get('authorized_route_source') or 'none'}",
        "",
        "## Trust Snapshot",
        "",
        f"- Stop requested: {brief.get('stop_requested')}",
        f"- Preflight status: {brief.get('preflight_status')}",
        f"- Preflight blockers: {brief.get('preflight_blockers') or []}",
        f"- Trace grade: {brief.get('trace_grade_status') or 'none'}",
        f"- Trace score: {brief.get('trace_grade_score') if brief.get('trace_grade_score') != '' else 'n/a'}",
        f"- Trace recommended next action: {brief.get('trace_grade_recommended_next_action') or 'none'}",
        f"- Trace manual data import required: {brief.get('trace_grade_manual_data_import_required') if brief.get('trace_grade_manual_data_import_required') != '' else 'n/a'}",
        f"- Trace issues: {brief.get('trace_grade_issues') or []}",
        f"- Eval suite status: {brief.get('eval_suite_status')}",
        f"- Artifact coherence status: {brief.get('artifact_coherence_status')}",
        f"- Artifact coherence issues: {brief.get('artifact_coherence_issues') or []}",
        f"- 9.9 readiness: {brief.get('nine_nine_readiness')}",
        f"- Advisory readiness gaps: {brief.get('advisory_readiness_gaps') or []}",
        f"- Mission score: {brief.get('mission_score')}",
        f"- Lowest mission dimension: {brief.get('lowest_mission_dimension')}",
        f"- Strategy capital bucket: {brief.get('strategy_capital_bucket')}",
        f"- Strategy capital action: {brief.get('strategy_capital_action')}",
        "",
        "## Artifact Trust Table",
        "",
    ]
    for item in brief.get("artifact_status", []) or []:
        lines.append(
            "- "
            f"{item.get('artifact')}: exists={item.get('exists')} "
            f"status={item.get('status')} path={item.get('path')}"
        )
    lines.extend(["", "## Guardrails", ""])
    lines.extend(f"- {item}" for item in brief.get("guardrails", []) or [])
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_resumption_brief(
    options: CeoOpsOptions,
    *,
    preflight_result: dict[str, Any] | None = None,
    coherence_result: dict[str, Any] | None = None,
    mission_result: dict[str, Any] | None = None,
    strategy_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    mission_result = mission_result or (
        None if (root / "mission_score.yaml").exists() else run_ceo_mission_score(diagnostic_options)
    )
    strategy_result = strategy_result or (
        None
        if (root / "strategy_capital_dashboard.yaml").exists()
        else run_ceo_strategy_capital_dashboard(diagnostic_options)
    )
    preflight_result = preflight_result or run_ceo_preflight_gate(diagnostic_options, enforce_memory_delta=True)
    coherence_result = coherence_result or run_ceo_artifact_coherence(diagnostic_options)
    latest_packet = root / "executive_decision_packet.md"
    brief = build_ceo_resumption_brief(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        root=root,
        stop_requested=is_stop_requested(options, ceo_run_id, lab_run_id),
        preflight_gate=preflight_result["preflight_gate"],
        replay=_load_yaml_if_exists(root / "ceo_replay.yaml"),
        eval_suite=_load_yaml_if_exists(root / "ceo_eval_suite.yaml"),
        mission_score=_load_yaml_if_exists(root / "mission_score.yaml"),
        strategy_capital_dashboard=_load_yaml_if_exists(root / "strategy_capital_dashboard.yaml"),
        artifact_coherence=coherence_result["coherence"],
        latest_packet=latest_packet,
    )
    path = root / "resumption_brief.yaml"
    report_path = root / "resumption_brief.md"
    atomic_write_yaml(path, brief)
    atomic_write_text(report_path, render_ceo_resumption_brief(brief))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "brief": brief,
        "paths": {
            "resumption_brief": path,
            "resumption_brief_report": report_path,
            "preflight_gate": preflight_result["paths"]["preflight_gate"],
            "preflight_gate_report": preflight_result["paths"]["preflight_gate_report"],
            "artifact_coherence": coherence_result["paths"]["artifact_coherence"],
            "artifact_coherence_report": coherence_result["paths"]["artifact_coherence_report"],
        },
    }


def run_ceo_dispatch_receipt(options: CeoOpsOptions) -> dict[str, Any]:
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
    last_action = _load_yaml_if_exists(root / "binding_action_result.yaml")
    decision = _decision_from_previous_next_action(last_action, decision)

    preflight_result = run_ceo_preflight_gate(options, enforce_memory_delta=True)
    preflight_gate = preflight_result["preflight_gate"]
    approval_result = run_ceo_approval_queue(options)
    approval_queue = approval_result["queue"]
    stop_requested = is_stop_requested(options, ceo_run_id, lab_run_id)
    blockers = [
        str(item.get("blocker", ""))
        for item in preflight_gate.get("blockers", []) or []
        if item.get("blocker")
    ]
    safe_to_dispatch = (
        not stop_requested
        and not company_status.get("true_blocker")
        and not company_status.get("governance", {}).get("product_change_allowed")
        and preflight_gate.get("safe_to_execute") is True
        and int(approval_queue.get("pending_count", 0) or 0) == 0
    )
    if stop_requested:
        reason = "stop.request exists"
    elif company_status.get("true_blocker"):
        reason = "company status reports true blocker"
    elif company_status.get("governance", {}).get("product_change_allowed"):
        reason = "validation governance indicates product_change_allowed"
    elif blockers:
        reason = "ceo preflight gate blocked bound dispatch"
    elif int(approval_queue.get("pending_count", 0) or 0) > 0:
        reason = "approval_queue has pending red-authority items"
    else:
        reason = "diagnostic receipt found current gates safe for one bound dispatch"
    receipt_paths = _write_ceo_dispatch_receipt(
        options,
        ceo_run_id,
        lab_run_id,
        decision,
        preflight_gate=preflight_gate,
        approval_queue=approval_queue,
        safe_to_dispatch=safe_to_dispatch,
        reason=reason,
        dispatch_mode="diagnostic_only",
    )
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "receipt": _load_yaml_if_exists(receipt_paths["dispatch_receipt_snapshot"]),
        "paths": {
            **receipt_paths,
            "preflight_gate": preflight_result["paths"]["preflight_gate"],
            "preflight_gate_report": preflight_result["paths"]["preflight_gate_report"],
            "approval_queue": approval_result["paths"]["queue"],
            "approval_queue_report": approval_result["paths"]["queue_report"],
        },
    }


def _latest_tree_mtime(path: Path) -> float:
    if not path.exists():
        return 0.0
    latest = path.stat().st_mtime
    for child in path.rglob("*"):
        try:
            latest = max(latest, child.stat().st_mtime)
        except OSError:
            continue
    return latest


def _mtime_iso(timestamp: float) -> str:
    if timestamp <= 0:
        return ""
    return datetime.fromtimestamp(timestamp, timezone.utc).replace(microsecond=0).isoformat()


def _run_index_status(
    *,
    stop_requested: bool,
    resume_status: str,
    preflight_status: str,
    pending_approval_count: int = 0,
    dispatch_safe_to_dispatch: Any = "",
    dispatch_status: str = "",
    artifact_coherence_status: str = "",
    replay_status: str = "",
    eval_suite_status: str = "",
    trace_grade_status: str = "",
    trace_manual_data_import_required: bool | str = "",
    effective_operator_status: str = "",
    manual_gate_active: bool = False,
    runtime_blocked: bool = False,
) -> str:
    if stop_requested:
        return "stopped"
    if pending_approval_count > 0:
        return "blocked"
    if manual_gate_active or runtime_blocked or effective_operator_status in {"manual_gate_required", "runtime_blocked"}:
        return "blocked"
    if dispatch_safe_to_dispatch is False or dispatch_status == "dispatch_blocked":
        return "blocked"
    if artifact_coherence_status == "fail":
        return "blocked"
    if replay_status == "replay_gaps" or eval_suite_status == "fail":
        return "blocked"
    if trace_grade_status == "fail" or trace_manual_data_import_required is True:
        return "blocked"
    if resume_status.startswith("blocked_") or preflight_status == "blocked":
        return "blocked"
    if resume_status == "safe_for_one_bound_action":
        return "actionable"
    if resume_status.startswith("diagnostic_"):
        return "diagnostic"
    return "needs_resumption_brief"


def build_ceo_run_index(options: CeoOpsOptions, *, limit: int = 25) -> dict[str, Any]:
    root = options.report_root
    rows: list[dict[str, Any]] = []
    if root.exists():
        run_dirs = [item for item in root.iterdir() if item.is_dir()]
    else:
        run_dirs = []
    for run_dir in run_dirs:
        run_id = run_dir.name
        heartbeat = _load_yaml_if_exists(run_dir / "heartbeat_status.yaml")
        resumption = _load_yaml_if_exists(run_dir / "resumption_brief.yaml")
        preflight = _load_yaml_if_exists(run_dir / "preflight_gate.yaml")
        dispatch_receipt = _load_yaml_if_exists(run_dir / "dispatch_receipt.yaml")
        blocker_stack = _load_yaml_if_exists(run_dir / "blocker_stack.yaml")
        incident_register = _load_yaml_if_exists(run_dir / "operating_incident_register.yaml")
        repair_plan = _load_yaml_if_exists(run_dir / "repair_plan.yaml")
        repair_apply = _load_yaml_if_exists(run_dir / "repair_apply.yaml")
        action_board = _load_yaml_if_exists(run_dir / "action_board.yaml")
        operator_brief = _load_yaml_if_exists(run_dir / "operator_brief.yaml")
        decision_quality = _load_yaml_if_exists(run_dir / "decision_quality.yaml")
        replay = _load_yaml_if_exists(run_dir / "ceo_replay.yaml")
        artifact_coherence = _load_yaml_if_exists(run_dir / "artifact_coherence.yaml")
        trace_grade = _load_yaml_if_exists(run_dir / "trace_grade.yaml")
        eval_suite = _load_yaml_if_exists(run_dir / "ceo_eval_suite.yaml")
        approval_queue = _load_yaml_if_exists(run_dir / "approval_queue.yaml")
        approval_status = _load_yaml_if_exists(run_dir / "approval_status.yaml")
        role_queue = _load_yaml_if_exists(run_dir / "role_task_queue.yaml")
        role_result_validation = _load_yaml_if_exists(run_dir / "role_result_validation.yaml")
        mission = _load_yaml_if_exists(run_dir / "mission_score.yaml")
        strategy = _load_yaml_if_exists(run_dir / "strategy_capital_dashboard.yaml")
        lab_run_id = str(
            resumption.get("lab_run_id")
            or heartbeat.get("lab_run_id")
            or preflight.get("lab_run_id")
            or f"{run_id}_lab"
        )
        stop_requested = (run_dir / "stop.request").exists() or (options.lab_ops_runtime_root / lab_run_id / "stop.request").exists()
        resume_status = str(resumption.get("resume_status") or "")
        preflight_status = str(preflight.get("status") or "")
        pending_approval_count = int(approval_queue.get("pending_count", approval_status.get("pending_count", 0)) or 0)
        approval_top_pending_item = (approval_queue.get("pending_items", []) or [{}])[0]
        latest_mtime = _latest_tree_mtime(run_dir)
        artifact_coherence_top_issue = (artifact_coherence.get("issues", []) or [{}])[0] if artifact_coherence.get("issues") else {}
        effective_operator = _effective_operator_status(
            action_board=action_board,
            operator_brief=operator_brief,
            decision_quality=decision_quality,
        )
        live_stop_handoff_command = f"PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id {run_id}"
        if stop_requested:
            resume_status = "blocked_stop_requested"
            effective_operator = {
                **effective_operator,
                "effective_operator_status": "manual_gate_required",
                "manual_gate_active": True,
                "runtime_blocked": True,
                "runtime_block_reason": "manual_gate_required:blocker:stop_requested",
                "effective_runtime_action": "blocker:stop_requested",
                "runtime_authority": "manual_gate_required",
            }
        rows.append(
            {
                "run_id": run_id,
                "lab_run_id": lab_run_id,
                "status": _run_index_status(
                    stop_requested=stop_requested,
                    resume_status=resume_status,
                    preflight_status=preflight_status,
                    pending_approval_count=pending_approval_count,
                    dispatch_safe_to_dispatch=False if stop_requested else dispatch_receipt.get("safe_to_dispatch", ""),
                    dispatch_status="dispatch_blocked" if stop_requested else str(dispatch_receipt.get("status", "")),
                    artifact_coherence_status=str(artifact_coherence.get("status", "")),
                    replay_status=str(replay.get("status", "")),
                    eval_suite_status=str(eval_suite.get("status", "")),
                    trace_grade_status=str(trace_grade.get("verdict", "")),
                    trace_manual_data_import_required=_trace_grade_manual_data_import_required(trace_grade),
                    effective_operator_status=str(effective_operator.get("effective_operator_status", "")),
                    manual_gate_active=effective_operator.get("manual_gate_active") is True,
                    runtime_blocked=effective_operator.get("runtime_blocked") is True,
                ),
                "resume_status": resume_status or "missing_resumption_brief",
                "preflight_status": preflight_status or "missing_preflight",
                "preflight_blockers": [
                    str(item.get("blocker", ""))
                    for item in preflight.get("blockers", []) or []
                    if item.get("blocker")
                ],
                "dispatch_receipt_status": "dispatch_blocked" if stop_requested else dispatch_receipt.get("status", "missing_dispatch_receipt"),
                "dispatch_safe_to_dispatch": False if stop_requested else dispatch_receipt.get("safe_to_dispatch", ""),
                "dispatch_reason": (
                    "live stop request/manual gate overrides reused safe artifacts"
                    if stop_requested
                    else dispatch_receipt.get("reason", "")
                ),
                "trace_grade_status": trace_grade.get("verdict", "missing_trace_grade"),
                "trace_grade_score": trace_grade.get("score", ""),
                "trace_grade_recommended_next_action": trace_grade.get("recommended_next_action", ""),
                "trace_grade_issues": trace_grade.get("issues", []),
                "trace_grade_manual_data_import_required": _trace_grade_manual_data_import_required(trace_grade),
                "top_blocker": blocker_stack.get("top_blocker", ""),
                "incident_count": incident_register.get("incident_count", ""),
                "repair_plan_status": repair_plan.get("status", "missing_repair_plan"),
                "top_repair": repair_plan.get("top_repair", ""),
                "top_repair_kind": repair_plan.get("top_repair_kind", ""),
                "repair_next_command": repair_plan.get("next_command", ""),
                "repair_apply_status": repair_apply.get("status", "missing_repair_apply"),
                "repair_apply_key": repair_apply.get("repair_key", ""),
                "repair_apply_executed": repair_apply.get("action_executed", ""),
                "repair_apply_closed": repair_apply.get("repair_closed", ""),
                "effective_operator_status": effective_operator.get("effective_operator_status", ""),
                "manual_gate_active": effective_operator.get("manual_gate_active", ""),
                "effective_operator_runtime_block_reason": effective_operator.get("runtime_block_reason", ""),
                "action_board_status": "manual_gate_required" if stop_requested else action_board.get("status", "missing_action_board"),
                "operator_brief_status": "waiting_on_manual_gate" if stop_requested else operator_brief.get("status", "missing_operator_brief"),
                "operator_brief_summary": (
                    "CEO mode is stopped at a manual gate. It should not take another autonomous action."
                    if stop_requested
                    else operator_brief.get("plain_english_summary", "")
                ),
                "operator_brief_next_action": live_stop_handoff_command if stop_requested else operator_brief.get("recommended_next_action", ""),
                "decision_quality_status": decision_quality.get("status", "missing_decision_quality"),
                "decision_quality_effective_runtime_action": (
                    "blocker:stop_requested" if stop_requested else decision_quality.get("effective_runtime_action", "")
                ),
                "decision_quality_effective_runtime_command_kind": (
                    "manual_gate" if stop_requested else decision_quality.get("effective_runtime_command_kind", "")
                ),
                "decision_quality_effective_runtime_can_execute_now": (
                    False if stop_requested else decision_quality.get("effective_runtime_can_execute_now", "")
                ),
                "decision_quality_runtime_blocked": True if stop_requested else decision_quality.get("runtime_blocked", ""),
                "decision_quality_runtime_block_reason": (
                    "manual_gate_required:blocker:stop_requested"
                    if stop_requested
                    else decision_quality.get("runtime_block_reason", "")
                ),
                "decision_quality_selected_action": decision_quality.get("selected_action", ""),
                "decision_quality_selected_strategic_route_advisory": decision_quality.get("selected_strategic_route_advisory", ""),
                "decision_quality_confidence": decision_quality.get("confidence", ""),
                "decision_quality_runtime_authority": (
                    "manual_gate_required" if stop_requested else decision_quality.get("runtime_authority_status", "")
                ),
                "decision_quality_executable_next_action": (
                    "blocker:stop_requested" if stop_requested else decision_quality.get("executable_next_action", "")
                ),
                "decision_quality_executable_command_kind": (
                    "manual_gate" if stop_requested else decision_quality.get("executable_next_command_kind", "")
                ),
                "decision_quality_runtime_authorized_strategic_route": decision_quality.get("runtime_authorized_strategic_route", ""),
                "decision_quality_executable_can_execute_now": False if stop_requested else decision_quality.get("executable_can_execute_now", ""),
                "decision_quality_selected_action_is_executable_now": (
                    False if stop_requested else decision_quality.get("selected_action_is_executable_now", "")
                ),
                "decision_quality_selected_action_blocked_by": (
                    "manual_gate_required:blocker:stop_requested"
                    if stop_requested
                    else decision_quality.get("selected_action_blocked_by", "")
                ),
                "replay_status": replay.get("status", "missing_replay"),
                "replay_issue_count": len(replay.get("issues", []) or []),
                "operator_step_status": replay.get("operator_step_status", "missing_operator_step"),
                "operator_step_count": replay.get("operator_step_count", ""),
                "eval_suite_status": eval_suite.get("status", "missing_eval_suite"),
                "eval_suite_score": eval_suite.get("score", ""),
                "nine_nine_readiness": (eval_suite.get("nine_nine_readiness", {}) or {}).get("status", ""),
                "nine_nine_blocking_case_count": len(
                    ((eval_suite.get("nine_nine_readiness", {}) or {}).get("blocking_case_ids", []) or [])
                ),
                "artifact_coherence_status": artifact_coherence.get("status", "missing_artifact_coherence"),
                "artifact_coherence_issue_count": artifact_coherence.get("issue_count", ""),
                "artifact_coherence_top_issue": artifact_coherence_top_issue.get("artifact", ""),
                "artifact_coherence_top_issue_types": artifact_coherence_top_issue.get("issues", []),
                "artifact_coherence_top_issue_severity": artifact_coherence_top_issue.get(
                    "severity",
                    "unknown" if artifact_coherence_top_issue else "",
                ),
                "approval_queue_status": approval_queue.get("status", approval_status.get("status", "missing_approval_queue")),
                "approval_pending_count": approval_queue.get("pending_count", approval_status.get("pending_count", "")),
                "approval_top_pending_id": approval_queue.get("top_pending_approval_id", ""),
                "approval_top_pending_kind": approval_top_pending_item.get("kind", ""),
                "approval_top_pending_reason": approval_top_pending_item.get("reason", ""),
                "approval_top_pending_source": approval_top_pending_item.get("source_artifact", ""),
                "approval_top_pending_required_user_decision": approval_top_pending_item.get("required_user_decision", ""),
                "approval_top_pending_authority": approval_top_pending_item.get("approval_authority", approval_top_pending_item.get("authority", "")),
                "approval_top_pending_fingerprint": approval_top_pending_item.get("approval_item_fingerprint", ""),
                "approval_record_command": approval_queue.get("top_pending_approval_record_command", ""),
                "approval_apply_command": approval_queue.get("top_pending_approval_apply_command", ""),
                "role_queue_status": role_queue.get("status", "missing_role_task_queue"),
                "role_pending_task_count": role_queue.get("pending_task_count", ""),
                "role_pending_manual_task_count": role_queue.get("pending_manual_task_count", ""),
                "role_pending_autonomous_task_count": role_queue.get("pending_autonomous_task_count", ""),
                "role_blocked_task_count": role_queue.get("blocked_task_count", ""),
                "role_completed_task_count": role_queue.get("completed_task_count", ""),
                "role_top_pending_task_id": role_queue.get("top_pending_task_id", ""),
                "role_top_pending_role_id": role_queue.get("top_pending_role_id", ""),
                "role_top_pending_owner_command": role_queue.get("top_pending_owner_command", ""),
                "role_top_pending_result_resolution_mode": role_queue.get("top_pending_result_resolution_mode", ""),
                "role_top_pending_requires_manual_gate": role_queue.get("top_pending_requires_manual_gate", ""),
                "role_top_pending_closure_command": role_queue.get("top_pending_closure_command", ""),
                "role_top_autonomous_pending_task_id": role_queue.get("top_autonomous_pending_task_id", ""),
                "role_top_autonomous_pending_role_id": role_queue.get("top_autonomous_pending_role_id", ""),
                "role_top_autonomous_pending_packet_path": role_queue.get("top_autonomous_pending_packet_path", ""),
                "role_top_autonomous_next_result_command": role_queue.get("top_autonomous_next_role_result_command", ""),
                "role_top_blocked_task_id": role_queue.get("top_blocked_task_id", ""),
                "role_top_blocked_role_id": role_queue.get("top_blocked_role_id", ""),
                "role_top_blocked_packet_path": role_queue.get("top_blocked_packet_path", ""),
                "role_top_blocked_result_resolution_mode": role_queue.get("top_blocked_result_resolution_mode", ""),
                "role_top_blocked_validation_status": role_queue.get("top_blocked_validation_status", ""),
                "role_top_blocked_closure_command": _ceo_role_queue_top_blocked_closure_command(
                    ceo_run_id=run_id,
                    role_queue=role_queue,
                ),
                "role_top_blocked_review_status": role_queue.get("top_blocked_review_status", ""),
                "role_top_blocked_result_path": role_queue.get("top_blocked_result_path", ""),
                "role_top_blocked_next_action": role_queue.get("top_blocked_next_action", ""),
                "role_top_blocked_finding": role_queue.get("top_blocked_finding", ""),
                "role_result_validation_status": role_result_validation.get("status", "missing_role_result_validation"),
                "role_result_validation_task": role_result_validation.get("task_id", ""),
                "role_result_validation_issues": role_result_validation.get("issues", []),
                "stop_requested": stop_requested,
                "latest_decision_packet_exists": (run_dir / "executive_decision_packet.md").exists(),
                "heartbeat_continue_recommended": heartbeat.get("continue_recommended", ""),
                "last_decision": heartbeat.get("last_decision", ""),
                "mission_score": mission.get("overall_mission_score", ""),
                "lowest_mission_dimension": mission.get("lowest_dimension", ""),
                "strategy_capital_bucket": strategy.get("selected_capital_bucket", ""),
                "next_command": (
                    live_stop_handoff_command
                    if stop_requested
                    else resumption.get(
                        "next_command",
                        f"PYTHONPATH=src python3 -m riskflow ceo resumption-brief --run-id {run_id}",
                    )
                ),
                "last_modified": _mtime_iso(latest_mtime),
                "production_effect": "none",
            }
        )
    rows = sorted(rows, key=lambda item: str(item.get("last_modified", "")), reverse=True)[: max(1, int(limit))]
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "model": CEO_RUN_INDEX_MODEL,
        "generated_at": utc_now_iso(),
        "status": "no_runs_found" if not rows else "runs_indexed",
        "run_count": len(rows),
        "status_counts": status_counts,
        "runs": rows,
        "guardrail": "Run index is diagnostic only. Generate a resumption brief before executing any run action.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_run_index(index: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Run Index",
        "",
        f"Generated: {index.get('generated_at')}",
        f"Status: {index.get('status')}",
        f"Run count: {index.get('run_count')}",
        "",
        "## Runs",
        "",
    ]
    for row in index.get("runs", []) or []:
        dispatch_safe = row.get("dispatch_safe_to_dispatch")
        if dispatch_safe in {"", None}:
            dispatch_safe = "n/a"
        incident_count = row.get("incident_count")
        if incident_count in {"", None}:
            incident_count = "n/a"
        repair_status = row.get("repair_plan_status") or "missing_repair_plan"
        lines.append(
            "- "
            f"{row.get('run_id')} status={row.get('status')} "
            f"resume={row.get('resume_status')} preflight={row.get('preflight_status')} "
            f"dispatch={row.get('dispatch_receipt_status')} safe={dispatch_safe} "
            f"trace={row.get('trace_grade_status') or 'missing_trace_grade'} "
            f"trace_score={row.get('trace_grade_score') if row.get('trace_grade_score') != '' else 'n/a'} "
            f"trace_next={row.get('trace_grade_recommended_next_action') or 'none'} "
            f"manual_data_import_required={row.get('trace_grade_manual_data_import_required') if row.get('trace_grade_manual_data_import_required') != '' else 'n/a'} "
            f"top={row.get('top_blocker') or 'none'} incidents={incident_count} "
            f"repair={repair_status} top_repair={row.get('top_repair') or 'none'} "
            f"repair_kind={row.get('top_repair_kind') or 'none'} "
            f"repair_apply={row.get('repair_apply_status') or 'missing_repair_apply'} "
            f"repair_closed={row.get('repair_apply_closed') if row.get('repair_apply_closed') != '' else 'n/a'} "
            f"effective_operator={row.get('effective_operator_status') or 'unknown_or_diagnostic'} "
            f"manual_gate_active={row.get('manual_gate_active') if row.get('manual_gate_active') != '' else 'n/a'} "
            f"brief={row.get('operator_brief_status') or 'missing_operator_brief'} "
            f"effective_runtime={row.get('decision_quality_effective_runtime_action') or 'none'} "
            f"runtime_blocked={row.get('decision_quality_runtime_blocked') if row.get('decision_quality_runtime_blocked') != '' else 'n/a'} "
            f"decision={row.get('decision_quality_selected_action') or 'none'} "
            f"decision_advisory={row.get('decision_quality_selected_strategic_route_advisory') or 'none'} "
            f"decision_authority={row.get('decision_quality_runtime_authority') or 'missing_decision_quality'} "
            f"decision_exec={row.get('decision_quality_executable_next_action') or 'none'} "
            f"decision_can_execute={row.get('decision_quality_executable_can_execute_now') if row.get('decision_quality_executable_can_execute_now') != '' else 'n/a'} "
            f"decision_blocked_by={row.get('decision_quality_selected_action_blocked_by') or 'none'} "
            f"replay={row.get('replay_status') or 'missing_replay'} "
            f"replay_issues={row.get('replay_issue_count')} "
            f"operator_step={row.get('operator_step_status') or 'missing_operator_step'} "
            f"operator_steps={row.get('operator_step_count') if row.get('operator_step_count') != '' else 'n/a'} "
            f"eval={row.get('eval_suite_status') or 'missing_eval_suite'} "
            f"eval_score={row.get('eval_suite_score') if row.get('eval_suite_score') != '' else 'n/a'} "
            f"readiness={row.get('nine_nine_readiness') or 'missing_readiness'} "
            f"readiness_blockers={row.get('nine_nine_blocking_case_count')} "
            f"coherence={row.get('artifact_coherence_status') or 'missing_artifact_coherence'} "
            f"coherence_issues={row.get('artifact_coherence_issue_count') if row.get('artifact_coherence_issue_count') != '' else 'n/a'} "
            f"approval={row.get('approval_queue_status') or 'missing_approval_queue'} "
            f"approval_pending={row.get('approval_pending_count') if row.get('approval_pending_count') != '' else 'n/a'} "
            f"role_queue={row.get('role_queue_status') or 'missing_role_task_queue'} "
            f"role_pending={row.get('role_pending_task_count') if row.get('role_pending_task_count') != '' else 'n/a'} "
            f"role_completed={row.get('role_completed_task_count') if row.get('role_completed_task_count') != '' else 'n/a'} "
            f"role_blocked={row.get('role_blocked_task_count') if row.get('role_blocked_task_count') != '' else 'n/a'} "
            f"role_validation={row.get('role_result_validation_status') or 'missing_role_result_validation'} "
            f"resumption_next=`{row.get('next_command')}` "
            f"repair_next=`{row.get('repair_next_command') or ''}`"
        )
        if row.get("operator_brief_summary"):
            lines.append(f"  - operator_summary={row.get('operator_brief_summary')}")
        if row.get("decision_quality_runtime_authorized_strategic_route"):
            lines.append(
                "  - "
                f"decision_runtime_route={row.get('decision_quality_runtime_authorized_strategic_route')}"
            )
        if row.get("trace_grade_issues"):
            lines.append(f"  - trace_issues={row.get('trace_grade_issues')}")
        if row.get("repair_apply_key"):
            lines.append(f"  - repair_apply_key={row.get('repair_apply_key')}")
        if row.get("artifact_coherence_top_issue"):
            lines.append(
                "  - "
                f"artifact_coherence_top_issue={row.get('artifact_coherence_top_issue')} "
                f"severity={row.get('artifact_coherence_top_issue_severity') or 'unknown'} "
                f"types={row.get('artifact_coherence_top_issue_types') or []}"
            )
        if row.get("approval_top_pending_id"):
            lines.append(
                "  - "
                f"top_approval={row.get('approval_top_pending_id')} "
                f"kind={row.get('approval_top_pending_kind') or 'none'} "
                f"authority={row.get('approval_top_pending_authority') or 'none'} "
                f"reason={row.get('approval_top_pending_reason') or 'none'} "
                f"source={row.get('approval_top_pending_source') or 'none'} "
                f"fingerprint={row.get('approval_top_pending_fingerprint') or 'none'} "
                f"record=`{row.get('approval_record_command') or ''}` "
                f"apply=`{row.get('approval_apply_command') or ''}`"
            )
        if row.get("role_result_validation_issues"):
            lines.append(f"  - role_validation_issues={row.get('role_result_validation_issues')}")
        if row.get("role_top_pending_task_id"):
            lines.append(
                "  - "
                f"top_role_task={row.get('role_top_pending_task_id')} "
                f"role={row.get('role_top_pending_role_id')} "
                f"manual={row.get('role_pending_manual_task_count') if row.get('role_pending_manual_task_count') != '' else 'n/a'} "
                f"autonomous={row.get('role_pending_autonomous_task_count') if row.get('role_pending_autonomous_task_count') != '' else 'n/a'} "
                f"owner={row.get('role_top_pending_owner_command')}"
            )
        if row.get("role_top_blocked_task_id"):
            lines.append(
                "  - "
                f"top_blocked_role_task={row.get('role_top_blocked_task_id')} "
                f"role={row.get('role_top_blocked_role_id')} "
                f"mode={row.get('role_top_blocked_result_resolution_mode') or 'none'} "
                f"validation={row.get('role_top_blocked_validation_status') or 'none'} "
                f"closure={row.get('role_top_blocked_closure_command') or 'none'}"
            )
            lines.append(
                "  - "
                f"top_blocked_role_review={row.get('role_top_blocked_review_status') or 'none'} "
                f"next={row.get('role_top_blocked_next_action') or 'none'} "
                f"result={row.get('role_top_blocked_result_path') or 'none'}"
            )
            if row.get("role_top_blocked_finding"):
                lines.append(f"  - top_blocked_role_finding={row.get('role_top_blocked_finding')}")
    if not index.get("runs"):
        lines.append("- none")
    lines.extend(["", str(index.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_run_index(options: CeoOpsOptions, *, limit: int = 25) -> dict[str, Any]:
    root = options.report_root
    root.mkdir(parents=True, exist_ok=True)
    index = build_ceo_run_index(options, limit=limit)
    path = root / "run_index.yaml"
    report_path = root / "run_index.md"
    atomic_write_yaml(path, index)
    atomic_write_text(report_path, render_ceo_run_index(index))
    return {"run_index": index, "paths": {"run_index": path, "run_index_report": report_path}}


def _append_blocker(blockers: list[dict[str, Any]], *, blocker: str, authority: str, evidence: str, next_action: str) -> None:
    if blocker in {str(item.get("blocker", "")) for item in blockers}:
        return
    blockers.append(
        {
            "rank": len(blockers) + 1,
            "blocker": blocker,
            "authority": authority,
            "evidence": evidence,
            "next_action": next_action,
            "production_effect": "none",
        }
    )


def build_ceo_blocker_stack(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    stop_requested: bool,
    preflight_gate: dict[str, Any],
    dispatch_receipt: dict[str, Any],
    resumption_brief: dict[str, Any],
    replay: dict[str, Any],
    eval_suite: dict[str, Any],
    approval_queue: dict[str, Any],
    memory_delta: dict[str, Any],
    evidence_debt_register: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    if stop_requested or resumption_brief.get("resume_status") == "blocked_stop_requested":
        _append_blocker(
            blockers,
            blocker="stop_requested",
            authority="user_or_runtime_stop",
            evidence=str(resumption_brief.get("resume_status") or "stop.request exists"),
            next_action="run approval-queue and wait for explicit clear-stop approval",
        )
    pending_approvals = int(approval_queue.get("pending_count", 0) or 0)
    if pending_approvals > 0:
        _append_blocker(
            blockers,
            blocker="pending_user_approval",
            authority="red_authority",
            evidence=f"pending_approvals={pending_approvals}",
            next_action="wait for approval-record and approval-apply with user confirmation",
        )
    for item in preflight_gate.get("blockers", []) or []:
        blocker = str(item.get("blocker", ""))
        if blocker and blocker not in {entry["blocker"] for entry in blockers}:
            _append_blocker(
                blockers,
                blocker=blocker,
                authority=str(item.get("category", "preflight_gate")),
                evidence=str(item.get("evidence", preflight_gate.get("status", ""))),
                next_action=str(item.get("next_action", "repair_preflight_blockers")),
            )
    if dispatch_receipt.get("status") == "dispatch_blocked" and "dispatch_blocked" not in {entry["blocker"] for entry in blockers}:
        _append_blocker(
            blockers,
            blocker="dispatch_blocked",
            authority="dispatch_receipt",
            evidence=str(dispatch_receipt.get("reason", "")),
            next_action="repair dispatch blockers before execute-next",
        )
    if replay.get("status") != "replayable":
        _append_blocker(
            blockers,
            blocker="replay_gaps",
            authority="replayability",
            evidence=f"issues={replay.get('issues') or []}",
            next_action="repair action ledger, state transitions, or dispatch receipt references",
        )
    readiness = eval_suite.get("nine_nine_readiness", {}) or {}
    for case_id in readiness.get("blocking_case_ids", []) or []:
        _append_blocker(
            blockers,
            blocker=f"eval_blocking_case:{case_id}",
            authority="eval_suite",
            evidence=f"score={eval_suite.get('score')} status={eval_suite.get('status')}",
            next_action="repair failing eval-suite case before extended autonomy",
        )
    if memory_delta.get("memory_delta_required") and not memory_delta.get("note_applied"):
        _append_blocker(
            blockers,
            blocker="memory_delta_unresolved",
            authority="handoff_memory",
            evidence=f"reasons={memory_delta.get('reasons') or []}",
            next_action="run memory-delta --apply if the delta should become durable memory",
        )
    debt_count = int(evidence_debt_register.get("debt_count", 0) or 0)
    if debt_count:
        _append_blocker(
            blockers,
            blocker="evidence_debt_open",
            authority="product_evidence",
            evidence=f"debt_count={debt_count}",
            next_action=str(evidence_debt_register.get("next_action", "work evidence debt register")),
        )
    if stop_requested:
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id {ceo_run_id}"
    else:
        next_command = resumption_brief.get("next_command") or f"PYTHONPATH=src python3 -m riskflow ceo resumption-brief --run-id {ceo_run_id}"
    return {
        "model": CEO_BLOCKER_STACK_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "blocked" if blockers else "clear_for_one_bound_action",
        "blocker_count": len(blockers),
        "top_blocker": blockers[0]["blocker"] if blockers else "",
        "top_blocker_evidence": blockers[0]["evidence"] if blockers else "",
        "blockers": blockers,
        "next_command": next_command,
        "guardrail": "Blocker stack orders CEO operating blockers. It does not clear blockers, approve promotions, or change production behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_blocker_stack(stack: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Blocker Stack",
        "",
        f"Generated: {stack.get('generated_at')}",
        f"Run: {stack.get('run_id')}",
        f"Lab run: {stack.get('lab_run_id')}",
        f"Status: {stack.get('status')}",
        f"Top blocker: {stack.get('top_blocker') or 'none'}",
        f"Top blocker evidence: {stack.get('top_blocker_evidence') or 'none'}",
        f"Next command: `{stack.get('next_command')}`",
        "",
        "## Ordered Blockers",
        "",
    ]
    for item in stack.get("blockers", []) or []:
        lines.append(
            "- "
            f"{item.get('rank')}. {item.get('blocker')} "
            f"authority={item.get('authority')} "
            f"evidence={item.get('evidence')} "
            f"next={item.get('next_action')}"
        )
    if not stack.get("blockers"):
        lines.append("- none")
    lines.extend(["", str(stack.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_blocker_stack(
    options: CeoOpsOptions,
    *,
    resumption_result: dict[str, Any] | None = None,
    dispatch_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    reused_resumption_brief = _ceo_reused_artifact_payload(
        resumption_result,
        "brief",
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    reused_dispatch_receipt = _ceo_reused_artifact_payload(
        dispatch_result,
        "receipt",
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    resumption_result = resumption_result if reused_resumption_brief is not None else run_ceo_resumption_brief(diagnostic_options)
    dispatch_result = dispatch_result if reused_dispatch_receipt is not None else run_ceo_dispatch_receipt(diagnostic_options)
    replay = _load_yaml_if_exists(root / "ceo_replay.yaml")
    eval_suite = _load_yaml_if_exists(root / "ceo_eval_suite.yaml")
    approval_queue = _load_yaml_if_exists(root / "approval_queue.yaml")
    memory_delta = _load_yaml_if_exists(root / "memory_delta.yaml")
    evidence_debt = _load_yaml_if_exists(root / "evidence_debt_register.yaml")
    stack = build_ceo_blocker_stack(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        stop_requested=is_stop_requested(options, ceo_run_id, lab_run_id),
        preflight_gate=_load_yaml_if_exists(root / "preflight_gate.yaml"),
        dispatch_receipt=dispatch_result["receipt"],
        resumption_brief=resumption_result["brief"],
        replay=replay,
        eval_suite=eval_suite,
        approval_queue=approval_queue,
        memory_delta=memory_delta,
        evidence_debt_register=evidence_debt,
    )
    path = root / "blocker_stack.yaml"
    report_path = root / "blocker_stack.md"
    atomic_write_yaml(path, stack)
    atomic_write_text(report_path, render_ceo_blocker_stack(stack))
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "stack": stack, "paths": {"blocker_stack": path, "blocker_stack_report": report_path}}


def _incident_severity_rank(severity: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(severity, 4)


def _record_incident(
    incidents: dict[str, dict[str, Any]],
    *,
    key: str,
    severity: str,
    category: str,
    evidence: str,
    evidence_path: Path,
    owner_command: str,
    closure_condition: str,
) -> None:
    existing = incidents.get(key)
    evidence_ref = {
        "path": str(evidence_path),
        "sha256": _file_sha256(evidence_path) if evidence_path.exists() and evidence_path.is_file() else "",
        "evidence": evidence,
    }
    if existing:
        existing["occurrence_count"] = int(existing.get("occurrence_count", 1) or 1) + 1
        existing["latest_evidence"] = evidence_ref
        existing["evidence_refs"].append(evidence_ref)
        if _incident_severity_rank(severity) < _incident_severity_rank(str(existing.get("severity", ""))):
            existing["severity"] = severity
        return
    incidents[key] = {
        "incident_key": key,
        "severity": severity,
        "category": category,
        "occurrence_count": 1,
        "latest_evidence": evidence_ref,
        "evidence_refs": [evidence_ref],
        "owner_command": owner_command,
        "closure_condition": closure_condition,
        "status": "open",
        "production_effect": "none",
    }


def build_ceo_operating_incident_register(*, ceo_run_id: str, lab_run_id: str, root: Path) -> dict[str, Any]:
    incidents: dict[str, dict[str, Any]] = {}
    action_entries = _read_jsonl_entries(root / "ceo_action_ledger.jsonl")
    dispatch_receipt = _load_yaml_if_exists(root / "dispatch_receipt.yaml")
    preflight_gate = _load_yaml_if_exists(root / "preflight_gate.yaml")
    replay = _load_yaml_if_exists(root / "ceo_replay.yaml")
    eval_suite = _load_yaml_if_exists(root / "ceo_eval_suite.yaml")
    artifact_coherence = _load_yaml_if_exists(root / "artifact_coherence.yaml")
    guardrail_audit = _load_yaml_if_exists(root / "guardrail_audit.yaml")
    for action in action_entries:
        status = str(action.get("status", ""))
        action_taken = str(action.get("action_taken", ""))
        if status == "blocked" or action_taken.startswith("blocked_"):
            _record_incident(
                incidents,
                key=f"blocked_action:{action_taken or action.get('decision', 'unknown')}",
                severity="critical" if action_taken in {"blocked_pending_user_approval", "blocked_stop_requested"} else "high",
                category="blocked_dispatch",
                evidence=f"decision={action.get('decision')} action={action_taken} status={status}",
                evidence_path=root / "ceo_action_ledger.jsonl",
                owner_command="run_ceo_blocker_stack_or_repair_preflight",
                closure_condition="binding action no longer blocks or has explicit user-approved closure",
            )
    if dispatch_receipt.get("status") == "dispatch_blocked":
        _record_incident(
            incidents,
            key=f"dispatch_blocked:{dispatch_receipt.get('reason', 'unknown')}",
            severity="critical",
            category="dispatch_receipt",
            evidence=f"decision={dispatch_receipt.get('decision')} reason={dispatch_receipt.get('reason')}",
            evidence_path=root / "dispatch_receipt.yaml",
            owner_command="repair_dispatch_blockers_before_execute_next",
            closure_condition="dispatch_receipt.status is dispatch_allowed for one bound action",
        )
    for item in preflight_gate.get("blockers", []) or []:
        blocker = str(item.get("blocker", "unknown"))
        _record_incident(
            incidents,
            key=f"preflight_blocker:{blocker}",
            severity="critical" if blocker in {"stop_requested", "pending_user_approval"} else "high",
            category="preflight",
            evidence=f"category={item.get('category')} evidence={item.get('evidence', '')}",
            evidence_path=root / "preflight_gate.yaml",
            owner_command=str(item.get("next_action", "repair_preflight_blockers")),
            closure_condition=f"preflight blocker {blocker} is absent",
        )
    if replay.get("status") not in {"", "replayable"}:
        for issue in replay.get("issues", []) or ["replay_gap"]:
            _record_incident(
                incidents,
                key=f"replay_issue:{issue}",
                severity="critical" if issue in {"illegal_action_transition", "missing_action_ledger_entries"} else "high",
                category="replay",
                evidence=f"status={replay.get('status')} issue={issue}",
                evidence_path=root / "ceo_replay.yaml",
                owner_command="repair_execute_next_state_transition_policy" if issue == "illegal_action_transition" else "repair_replay_artifacts",
                closure_condition=f"ceo_replay no longer reports {issue}",
            )
    readiness = eval_suite.get("nine_nine_readiness", {}) or {}
    for case_id in readiness.get("blocking_case_ids", []) or []:
        _record_incident(
            incidents,
            key=f"eval_blocking_case:{case_id}",
            severity="critical",
            category="eval_suite",
            evidence=f"score={eval_suite.get('score')} status={eval_suite.get('status')}",
            evidence_path=root / "ceo_eval_suite.yaml",
            owner_command="repair_failing_eval_suite_case",
            closure_condition=f"eval case {case_id} passes",
        )
    if artifact_coherence.get("status") == "fail":
        for issue in artifact_coherence.get("issues", []) or [{"artifact": "unknown", "issues": ["artifact_coherence_failed"]}]:
            issue_key = ",".join(str(item) for item in issue.get("issues", []) or ["artifact_coherence_failed"])
            _record_incident(
                incidents,
                key=f"artifact_coherence:{issue.get('artifact', 'unknown')}:{issue_key}",
                severity="high",
                category="artifact_coherence",
                evidence=str(issue),
                evidence_path=root / "artifact_coherence.yaml",
                owner_command="rerun_or_repair_stale_trust_artifacts",
                closure_condition="artifact_coherence.status is pass",
            )
    if guardrail_audit.get("status") == "fail":
        for violation in guardrail_audit.get("violations", []) or [{"violation": "guardrail_audit_failed"}]:
            _record_incident(
                incidents,
                key=f"guardrail:{violation.get('violation', 'unknown')}",
                severity="critical",
                category="guardrail",
                evidence=str(violation),
                evidence_path=root / "guardrail_audit.yaml",
                owner_command="repair_non_none_production_effect_or_product_language",
                closure_condition="guardrail_audit.status is pass",
            )
    incident_list = sorted(incidents.values(), key=lambda item: (_incident_severity_rank(str(item.get("severity", ""))), str(item.get("incident_key", ""))))
    return {
        "model": CEO_OPERATING_INCIDENT_REGISTER_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": "open_incidents" if incident_list else "no_open_incidents",
        "incident_count": len(incident_list),
        "incidents": incident_list,
        "guardrail": "Operating incidents are repair memory only. They do not block, approve, validate, or change production behavior by themselves.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_operating_incident_register(register: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Operating Incident Register",
        "",
        f"Generated: {register.get('generated_at')}",
        f"Run: {register.get('run_id')}",
        f"Lab run: {register.get('lab_run_id')}",
        f"Status: {register.get('status')}",
        f"Incidents: {register.get('incident_count')}",
        "",
        "## Open Incidents",
        "",
    ]
    for item in register.get("incidents", []) or []:
        lines.append(
            "- "
            f"{item.get('severity')} {item.get('incident_key')} "
            f"count={item.get('occurrence_count')} owner=`{item.get('owner_command')}`"
        )
    if not register.get("incidents"):
        lines.append("- none")
    lines.extend(["", str(register.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_operating_incident_register(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    register = build_ceo_operating_incident_register(ceo_run_id=ceo_run_id, lab_run_id=lab_run_id, root=root)
    path = root / "operating_incident_register.yaml"
    report_path = root / "operating_incident_register.md"
    atomic_write_yaml(path, register)
    atomic_write_text(report_path, render_ceo_operating_incident_register(register))
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "register": register, "paths": {"incident_register": path, "incident_register_report": report_path}}


def _classify_repair_command(command: str, repair_key: str) -> dict[str, Any]:
    text = f"{command} {repair_key}".lower()
    manual_tokens = [
        "approval",
        "user",
        "wait",
        "clear-stop",
        "stop_requested",
        "pending_user_approval",
        "production",
        "promotion",
    ]
    diagnostic_tokens = {
        "status",
        "run-index",
        "dispatch-receipt",
        "blocker-stack",
        "incident-register",
        "repair-plan",
        "artifact-coherence",
        "resumption-brief",
        "replay",
        "eval-suite",
        "guardrail-audit",
        "preflight-gate",
    }
    is_runnable_cli = command.startswith("PYTHONPATH=src python3 -m riskflow ceo ")
    requires_manual_gate = any(token in text for token in manual_tokens)
    diagnostic_only = is_runnable_cli and any(f" ceo {token}" in command for token in diagnostic_tokens)
    needs_implementation = not is_runnable_cli and not requires_manual_gate
    if requires_manual_gate:
        command_kind = "manual_gate"
    elif diagnostic_only:
        command_kind = "diagnostic_refresh"
    elif is_runnable_cli:
        command_kind = "runnable_cli"
    else:
        command_kind = "implementation_required"
    return {
        "command_kind": command_kind,
        "is_runnable_cli": is_runnable_cli,
        "can_execute_autonomously": command_kind == "runnable_cli",
        "requires_manual_gate": requires_manual_gate,
        "needs_implementation": needs_implementation,
        "diagnostic_only": diagnostic_only,
    }


def _implementation_repair_playbook(
    *,
    repair_key: str,
    category: str,
    owner_command: str,
    closure_condition: str,
    evidence: str,
) -> dict[str, Any]:
    text = f"{repair_key} {category} {owner_command} {closure_condition}".lower()
    target_files = ["src/riskflow/ceo_ops.py", "tests/test_ceo_ops.py"]
    target_functions: list[str] = []
    test_selectors: list[str] = []
    summary = "Repair the symbolic CEO operating issue with a code or artifact-policy change."

    if "repair_apply" in text or "repair-plan snapshot" in text or "repair_plan_snapshot" in text:
        summary = "Repair repair-apply replayability so each repair attempt has immutable before/after repair-plan snapshots."
        target_functions = ["run_ceo_repair_apply", "_build_repair_apply_checks", "build_ceo_replay", "build_ceo_eval_suite"]
        test_selectors = ["repair_apply", "replay", "eval_suite"]
    elif "action_contract_decision_mismatch" in text or "missing_action_dispatch_receipt_ref" in text:
        summary = "Repair latest-action trust alignment so the action contract and immutable dispatch receipt snapshot back the binding action."
        target_functions = [
            "run_ceo_execute_next",
            "_write_ceo_action_contract",
            "_write_ceo_dispatch_receipt",
            "build_ceo_artifact_coherence",
            "build_ceo_eval_suite",
        ]
        test_selectors = ["artifact_coherence", "dispatch_receipt", "execute_next", "eval_suite"]
    elif "role_results_close_the_role_queue" in text or "role" in text:
        summary = "Repair specialist role queue closure so pending work and invalid completions cannot look closed."
        target_functions = ["build_ceo_role_task_queue", "build_ceo_eval_suite", "run_ceo_role_result"]
        test_selectors = ["role_queue", "role_result", "eval_suite"]
    elif "action_contract_matches_latest_action" in text or "dispatch_receipt_backs_latest_action" in text or "dispatch" in text:
        summary = "Repair action-contract and dispatch-receipt coherence for the latest binding action."
        target_functions = ["run_ceo_execute_next", "_write_ceo_dispatch_receipt", "build_ceo_eval_suite"]
        test_selectors = ["dispatch_receipt", "execute_next", "eval_suite"]
    elif "state_machine_legal_transitions" in text or "illegal_action_transition" in text or "replay" in text:
        summary = "Repair CEO replay state-transition policy without weakening current receipt-backed safety."
        target_functions = ["_build_ceo_state_transition_checks", "build_ceo_replay", "build_ceo_eval_suite"]
        test_selectors = ["replay", "eval_suite"]
    elif "artifact_coherence" in text or "stale" in text:
        summary = "Repair stale or mismatched CEO trust artifacts before a fresh session can rely on them."
        target_functions = ["build_ceo_artifact_coherence", "run_ceo_artifact_coherence", "build_ceo_resumption_brief"]
        test_selectors = ["artifact_coherence", "resumption_brief"]
    elif "guardrail" in text or "production_effect" in text or "product_language" in text:
        summary = "Repair CEO guardrail violations so generated artifacts cannot claim production authority."
        target_functions = ["build_ceo_guardrail_audit", "build_ceo_preflight_gate"]
        test_selectors = ["guardrail", "preflight"]
    elif "preflight" in text:
        summary = "Repair preflight blocker routing while preserving stop, approval, replay, eval, memory, and guardrail authority."
        target_functions = ["build_ceo_preflight_gate", "run_ceo_preflight_gate", "run_ceo_execute_next"]
        test_selectors = ["preflight", "execute_next"]

    return {
        "playbook_id": _debt_slug(f"{category}_{owner_command}_{repair_key}")[:96],
        "summary": summary,
        "target_files": target_files,
        "target_functions": target_functions or ["build_ceo_repair_plan", "build_ceo_operating_incident_register"],
        "test_selectors": test_selectors or ["repair_plan", "incident_register"],
        "acceptance_criteria": [
            closure_condition,
            "add or update focused tests for the named repair",
            "run the focused tests and the CEO ops suite before claiming closure",
            "preserve production_effect: none and do not change production formulas",
        ],
        "evidence": evidence,
        "non_executable_by_repair_apply": True,
        "production_effect": "none",
    }


def _append_repair_item(
    items: list[dict[str, Any]],
    seen: set[str],
    *,
    repair_key: str,
    source: str,
    severity: str,
    category: str,
    owner_command: str,
    closure_condition: str,
    evidence: str,
    exact_command: str = "",
) -> None:
    if repair_key in seen:
        return
    seen.add(repair_key)
    command = exact_command or owner_command
    command_contract = _classify_repair_command(command, repair_key)
    implementation_playbook = (
        _implementation_repair_playbook(
            repair_key=repair_key,
            category=category,
            owner_command=owner_command,
            closure_condition=closure_condition,
            evidence=evidence,
        )
        if command_contract.get("needs_implementation")
        else {}
    )
    items.append(
        {
            "rank": len(items) + 1,
            "repair_key": repair_key,
            "source": source,
            "severity": severity,
            "category": category,
            "owner_command": owner_command,
            "exact_command": exact_command,
            "recommended_command": command,
            "closure_condition": closure_condition,
            "evidence": evidence,
            **command_contract,
            "implementation_playbook": implementation_playbook,
            "production_effect": "none",
        }
    )


def _repair_apply_command(ceo_run_id: str, repair_key: str) -> str:
    return (
        "PYTHONPATH=src python3 -m riskflow ceo repair-apply "
        f"--run-id {ceo_run_id} --repair-key {repair_key} --apply"
    )


def build_ceo_repair_plan(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    blocker_stack: dict[str, Any],
    incident_register: dict[str, Any],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    stack_next_command = str(blocker_stack.get("next_command", ""))
    for blocker in blocker_stack.get("blockers", []) or []:
        blocker_id = str(blocker.get("blocker", "unknown"))
        rank = int(blocker.get("rank", 999) or 999)
        _append_repair_item(
            items,
            seen,
            repair_key=f"blocker:{blocker_id}",
            source="blocker_stack",
            severity="critical" if rank == 1 else "high",
            category=str(blocker.get("authority", "blocker")),
            owner_command=str(blocker.get("next_action", "repair_blocker_stack")),
            exact_command=stack_next_command if rank == 1 else "",
            closure_condition=f"blocker_stack no longer reports {blocker_id}",
            evidence=str(blocker.get("evidence", "")),
        )
    for incident in incident_register.get("incidents", []) or []:
        incident_key = str(incident.get("incident_key", "unknown"))
        _append_repair_item(
            items,
            seen,
            repair_key=f"incident:{incident_key}",
            source="operating_incident_register",
            severity=str(incident.get("severity", "medium")),
            category=str(incident.get("category", "incident")),
            owner_command=str(incident.get("owner_command", "repair_operating_incident")),
            closure_condition=str(incident.get("closure_condition", "incident closes")),
            evidence=str((incident.get("latest_evidence", {}) or {}).get("evidence", "")),
        )
    items = sorted(
        items,
        key=lambda item: (
            _incident_severity_rank(str(item.get("severity", ""))),
            0 if item.get("source") == "blocker_stack" else 1,
            str(item.get("repair_key", "")),
        ),
    )
    for rank, item in enumerate(items, start=1):
        item["rank"] = rank
    top = items[0] if items else {}
    manual_gate_required = any(bool(item.get("requires_manual_gate")) for item in items)
    autonomous_repair_count = sum(1 for item in items if item.get("command_kind") == "runnable_cli")
    diagnostic_refresh_count = sum(1 for item in items if item.get("command_kind") == "diagnostic_refresh")
    implementation_required = any(bool(item.get("needs_implementation")) for item in items)
    implementation_playbook_count = sum(1 for item in items if item.get("implementation_playbook"))
    if not items:
        status = "no_repairs_required"
        next_command = f"PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id {ceo_run_id} --apply"
    elif top.get("requires_manual_gate"):
        status = "manual_gate_first"
        next_command = str(top.get("recommended_command", ""))
    elif top.get("needs_implementation"):
        status = "implementation_repair_required"
        next_command = ""
    else:
        status = "repair_plan_ready"
        next_command = _repair_apply_command(ceo_run_id, str(top.get("repair_key", "")))
    return {
        "model": CEO_REPAIR_PLAN_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "repair_count": len(items),
        "autonomous_repair_count": autonomous_repair_count,
        "runnable_repair_count": autonomous_repair_count,
        "diagnostic_refresh_count": diagnostic_refresh_count,
        "implementation_required": implementation_required,
        "implementation_playbook_count": implementation_playbook_count,
        "manual_gate_required": manual_gate_required,
        "top_repair": top.get("repair_key", ""),
        "top_repair_kind": top.get("command_kind", ""),
        "next_command": next_command,
        "repair_items": items,
        "guardrail": "Repair plans order operating repairs only. They do not approve manual gates, promote candidates, or change production behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_repair_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Repair Plan",
        "",
        f"Generated: {plan.get('generated_at')}",
        f"Run: {plan.get('run_id')}",
        f"Lab run: {plan.get('lab_run_id')}",
        f"Status: {plan.get('status')}",
        f"Repairs: {plan.get('repair_count')}",
        f"Runnable repairs: {plan.get('runnable_repair_count', plan.get('autonomous_repair_count'))}",
        f"Diagnostic refreshes: {plan.get('diagnostic_refresh_count', 0)}",
        f"Implementation playbooks: {plan.get('implementation_playbook_count', 0)}",
        f"Manual gate required: {plan.get('manual_gate_required')}",
        f"Top repair: {plan.get('top_repair') or 'none'}",
        f"Top repair kind: {plan.get('top_repair_kind') or 'none'}",
        f"Next command: `{plan.get('next_command')}`",
        "",
        "## Ordered Repairs",
        "",
    ]
    for item in plan.get("repair_items", []) or []:
        playbook = item.get("implementation_playbook", {}) or {}
        lines.append(
            "- "
            f"{item.get('rank')}. {item.get('repair_key')} "
            f"severity={item.get('severity')} kind={item.get('command_kind')} "
            f"auto={item.get('can_execute_autonomously')} "
            f"owner=`{item.get('owner_command')}` close=`{item.get('closure_condition')}`"
        )
        if playbook:
            lines.append(
                "  - "
                f"playbook={playbook.get('playbook_id')} "
                f"targets={playbook.get('target_functions')} "
                f"tests={playbook.get('test_selectors')}"
            )
    if not plan.get("repair_items"):
        lines.append("- none")
    lines.extend(["", str(plan.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_repair_plan(
    options: CeoOpsOptions,
    *,
    blocker_result: dict[str, Any] | None = None,
    incident_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    blocker_result = blocker_result or run_ceo_blocker_stack(diagnostic_options)
    incident_result = incident_result or run_ceo_operating_incident_register(diagnostic_options)
    plan = build_ceo_repair_plan(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        blocker_stack=blocker_result["stack"],
        incident_register=incident_result["register"],
    )
    path = root / "repair_plan.yaml"
    report_path = root / "repair_plan.md"
    atomic_write_yaml(path, plan)
    atomic_write_text(report_path, render_ceo_repair_plan(plan))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "repair_plan": plan,
        "paths": {
            "repair_plan": path,
            "repair_plan_report": report_path,
            "blocker_stack": blocker_result["paths"]["blocker_stack"],
            "incident_register": incident_result["paths"]["incident_register"],
        },
    }


def _find_repair_item(plan: dict[str, Any], repair_key: str) -> dict[str, Any] | None:
    for item in plan.get("repair_items", []) or []:
        if str(item.get("repair_key", "")) == repair_key:
            return item
    return None


def _extract_ceo_repair_command(command: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return ""
    expected_prefix = ["PYTHONPATH=src", "python3", "-m", "riskflow", "ceo"]
    if tokens[: len(expected_prefix)] != expected_prefix or len(tokens) <= len(expected_prefix):
        return ""
    return tokens[len(expected_prefix)]


def _run_allowed_ceo_repair_command(
    *,
    command: str,
    options: CeoOpsOptions,
    command_kind: str,
) -> dict[str, Any]:
    command_name = _extract_ceo_repair_command(command)
    diagnostic_options = _with_ceo_context(options, context="repair_apply_diagnostic_refresh")
    apply_options = replace(options, apply=True)
    diagnostic_runners = {
        "status": run_ceo_status,
        "run-index": run_ceo_run_index,
        "dispatch-receipt": run_ceo_dispatch_receipt,
        "blocker-stack": run_ceo_blocker_stack,
        "incident-register": run_ceo_operating_incident_register,
        "repair-plan": run_ceo_repair_plan,
        "artifact-coherence": run_ceo_artifact_coherence,
        "resumption-brief": run_ceo_resumption_brief,
        "replay": run_ceo_replay,
        "eval-suite": run_ceo_eval_suite,
        "eval-fixtures": run_ceo_eval_fixtures,
        "guardrail-audit": run_ceo_guardrail_audit,
        "preflight-gate": run_ceo_preflight_gate,
        "action-board": run_ceo_action_board,
        "decision-quality": run_ceo_decision_quality,
        "operator-brief": run_ceo_operator_brief,
        "executive-kpis": run_ceo_executive_kpis,
        "mission-score": run_ceo_mission_score,
        "strategy-capital-dashboard": run_ceo_strategy_capital_dashboard,
    }
    runnable_runners = {
        "patch-research-infra": run_ceo_patch_research_infra,
        "broaden-hypothesis-source": run_ceo_broaden_hypothesis_source,
    }
    if command_kind == "diagnostic_refresh" and command_name in diagnostic_runners:
        result = diagnostic_runners[command_name](diagnostic_options)
        return {"command_name": command_name, "result": result}
    if command_kind == "runnable_cli" and command_name in runnable_runners:
        result = runnable_runners[command_name](
            _with_ceo_context(apply_options, context="bound_dispatch", action=command_name)
        )
        return {"command_name": command_name, "result": result}
    raise ValueError(f"repair-apply refuses unsupported CEO command: {command_name or command}")


def _repair_paths_from_result(result: dict[str, Any]) -> dict[str, str]:
    paths = result.get("paths", {}) if isinstance(result, dict) else {}
    return {str(key): str(value) for key, value in (paths or {}).items()}


def render_ceo_repair_apply(apply_result: dict[str, Any]) -> str:
    item = apply_result.get("repair_item", {}) or {}
    lines = [
        "# Riskflow CEO Repair Apply",
        "",
        f"Generated: {apply_result.get('generated_at')}",
        f"Run: {apply_result.get('run_id')}",
        f"Lab run: {apply_result.get('lab_run_id')}",
        f"Status: {apply_result.get('status')}",
        f"Repair key: {apply_result.get('repair_key')}",
        f"Command kind: {apply_result.get('command_kind') or 'n/a'}",
        f"Action attempted: {apply_result.get('action_attempted')}",
        f"Action executed: {apply_result.get('action_executed')}",
        f"Repair closed: {apply_result.get('repair_closed')}",
        f"Reason: {apply_result.get('reason')}",
        "",
        "## Repair Item",
        "",
        f"- Source: {item.get('source') or 'n/a'}",
        f"- Severity: {item.get('severity') or 'n/a'}",
        f"- Command: `{apply_result.get('recommended_command') or ''}`",
        f"- Closure: {item.get('closure_condition') or 'n/a'}",
        "",
        "## Before / After",
        "",
        f"- Before plan status: {apply_result.get('before_plan_status')}",
        f"- Before top repair: {apply_result.get('before_top_repair') or 'none'}",
        f"- After plan status: {apply_result.get('after_plan_status')}",
        f"- After top repair: {apply_result.get('after_top_repair') or 'none'}",
        f"- After repair kind: {apply_result.get('after_repair_kind') or 'cleared'}",
        "",
        "## Guardrails",
        "",
    ]
    lines.extend(f"- {item}" for item in apply_result.get("guardrails", []) or [])
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_repair_apply(options: CeoOpsOptions, *, repair_key: str) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo repair-apply requires --apply")
    if not repair_key:
        raise ValueError("ceo repair-apply requires --repair-key")
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="repair_apply")
    generated_at = utc_now_iso()
    apply_id = "".join(ch if ch.isalnum() else "_" for ch in generated_at).strip("_")
    snapshot_dir = root / "repair_apply_plans"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    before_result = run_ceo_repair_plan(diagnostic_options)
    before_plan = before_result["repair_plan"]
    before_plan_snapshot = snapshot_dir / f"{apply_id}_before_repair_plan.yaml"
    atomic_write_yaml(before_plan_snapshot, before_plan)
    repair_item = _find_repair_item(before_plan, repair_key)
    before_plan_status = str(before_plan.get("status", ""))
    before_top_repair = str(before_plan.get("top_repair", ""))
    command_kind = str((repair_item or {}).get("command_kind", ""))
    recommended_command = str((repair_item or {}).get("recommended_command", ""))
    command_result: dict[str, Any] | None = None
    action_attempted = False
    action_executed = False

    if repair_item is None:
        status = "blocked_unknown_repair"
        reason = f"Repair key {repair_key} is not present in the refreshed repair plan."
    elif repair_item.get("requires_manual_gate"):
        status = "blocked_manual_gate"
        reason = "Repair requires explicit user approval or stop-clear authority."
    elif before_plan_status != "repair_plan_ready":
        status = "blocked_repair_plan_not_ready"
        reason = (
            f"Refreshed repair plan status is {before_plan_status or 'unknown'}; "
            "repair-apply only executes when the current plan is repair_plan_ready."
        )
    elif before_top_repair and before_top_repair != repair_key:
        status = "blocked_not_top_repair"
        reason = (
            f"Repair key {repair_key} is not the refreshed top repair {before_top_repair}; "
            "repair-apply refuses lower-priority work while a higher-priority repair is open."
        )
    elif repair_item.get("needs_implementation"):
        status = "blocked_implementation_required"
        reason = "Repair is a symbolic implementation task and cannot be executed as a CEO CLI command."
    elif command_kind not in {"diagnostic_refresh", "runnable_cli"}:
        status = "blocked_unsupported_kind"
        reason = f"Repair kind {command_kind or 'unknown'} is not executable by repair-apply."
    else:
        action_attempted = True
        try:
            command_result = _run_allowed_ceo_repair_command(
                command=recommended_command,
                options=options,
                command_kind=command_kind,
            )
            action_executed = True
            status = "repair_command_executed"
            reason = f"Executed allowlisted CEO {command_kind} command {command_result.get('command_name')}."
        except ValueError as exc:
            status = "blocked_unsupported_command"
            reason = str(exc)

    after_result = run_ceo_repair_plan(diagnostic_options)
    after_plan = after_result["repair_plan"]
    after_plan_snapshot = snapshot_dir / f"{apply_id}_after_repair_plan.yaml"
    atomic_write_yaml(after_plan_snapshot, after_plan)
    after_item = _find_repair_item(after_plan, repair_key)
    after_kind = str((after_item or {}).get("command_kind", ""))
    repair_closed = action_executed and (
        after_item is None
        or after_plan.get("status") == "no_repairs_required"
    )
    if action_executed and repair_closed:
        status = "repair_closed"
        reason = f"Repair key {repair_key} cleared after the allowlisted command."
    elif action_executed and after_item is not None and bool(after_kind) and after_kind != command_kind:
        status = "repair_reclassified_not_closed"
        reason = f"Repair key {repair_key} remains open but changed kind from {command_kind} to {after_kind}."
    elif action_executed and command_kind == "diagnostic_refresh":
        status = "diagnostic_refreshed"
        reason = "Diagnostic refresh completed. The repair remains open until the refreshed repair plan clears or changes the key."

    apply_artifact = {
        "model": CEO_REPAIR_APPLY_MODEL,
        "generated_at": generated_at,
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "repair_key": repair_key,
        "command_kind": command_kind,
        "recommended_command": recommended_command,
        "reason": reason,
        "action_attempted": action_attempted,
        "action_executed": action_executed,
        "repair_closed": repair_closed,
        "repair_item": repair_item or {},
        "before_plan_status": before_plan.get("status", ""),
        "before_top_repair": before_plan.get("top_repair", ""),
        "after_plan_status": after_plan.get("status", ""),
        "after_top_repair": after_plan.get("top_repair", ""),
        "after_repair_kind": after_kind,
        "command_name": (command_result or {}).get("command_name", ""),
        "command_paths": _repair_paths_from_result((command_result or {}).get("result", {})),
        "paths": {
            "before_repair_plan": str(before_result["paths"]["repair_plan"]),
            "after_repair_plan": str(after_result["paths"]["repair_plan"]),
            "before_repair_plan_snapshot": str(before_plan_snapshot),
            "after_repair_plan_snapshot": str(after_plan_snapshot),
        },
        "before_repair_plan_snapshot_sha256": _file_sha256(before_plan_snapshot),
        "after_repair_plan_snapshot_sha256": _file_sha256(after_plan_snapshot),
        "guardrails": [
            "Repair-apply requires --apply and an exact repair key from a freshly generated repair plan.",
            "It executes only allowlisted internal CEO functions; it never shells out to YAML command text.",
            "It refuses manual gates, production approvals, stop clears, promotion authority, and symbolic implementation repairs.",
            "Diagnostic refreshes do not count as closed unless the after-plan clears or changes the repair key.",
        ],
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }
    path = root / "repair_apply.yaml"
    report_path = root / "repair_apply.md"
    ledger_path = root / "repair_apply_ledger.jsonl"
    atomic_write_yaml(path, apply_artifact)
    atomic_write_text(report_path, render_ceo_repair_apply(apply_artifact))
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_json_safe(apply_artifact), sort_keys=True) + "\n")
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "repair_apply": apply_artifact,
        "command_result": command_result or {},
        "paths": {
            "repair_apply": path,
            "repair_apply_report": report_path,
            "repair_apply_ledger": ledger_path,
            "before_repair_plan": before_result["paths"]["repair_plan"],
            "after_repair_plan": after_result["paths"]["repair_plan"],
            "before_repair_plan_snapshot": before_plan_snapshot,
            "after_repair_plan_snapshot": after_plan_snapshot,
        },
    }


def _action_board_item(
    *,
    action_id: str,
    source: str,
    command_kind: str,
    command: str,
    rationale: str,
    can_execute_now: bool,
    requires_manual_gate: bool = False,
    diagnostic_only: bool = False,
    needs_implementation: bool = False,
    closure_condition: str = "",
    authorized_strategic_route: str = "",
    authorized_route_source: str = "",
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "source": source,
        "command_kind": command_kind,
        "command": command,
        "rationale": rationale,
        "can_execute_now": can_execute_now,
        "requires_manual_gate": requires_manual_gate,
        "diagnostic_only": diagnostic_only,
        "needs_implementation": needs_implementation,
        "closure_condition": closure_condition,
        "authorized_strategic_route": authorized_strategic_route,
        "authorized_route_source": authorized_route_source,
        "production_effect": "none",
    }


def _action_board_blocked_by_runtime_authority(item: dict[str, Any], reason: str) -> dict[str, Any]:
    blocked = dict(item)
    blocked["can_execute_now"] = False
    blocked["blocked_by_runtime_authority"] = reason
    blocked["runtime_blocked"] = True
    blocked["rationale"] = (
        f"{blocked.get('rationale', '')} Runtime authority currently blocks this action: {reason}."
    ).strip()
    return blocked


def build_ceo_action_board(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    resumption_brief: dict[str, Any],
    dispatch_receipt: dict[str, Any],
    blocker_stack: dict[str, Any],
    repair_plan: dict[str, Any],
    executive_kpis: dict[str, Any],
) -> dict[str, Any]:
    manual_gates: list[dict[str, Any]] = []
    runnable_repairs: list[dict[str, Any]] = []
    diagnostic_refreshes: list[dict[str, Any]] = []
    implementation_repairs: list[dict[str, Any]] = []
    blocked_actions: list[dict[str, Any]] = []

    for item in repair_plan.get("repair_items", []) or []:
        repair_key = str(item.get("repair_key", "unknown_repair"))
        command_kind = str(item.get("command_kind", ""))
        if item.get("requires_manual_gate") or item.get("needs_implementation"):
            command = str(item.get("recommended_command", ""))
        elif command_kind in {"runnable_cli", "diagnostic_refresh"}:
            command = _repair_apply_command(ceo_run_id, repair_key)
        else:
            command = str(item.get("recommended_command", ""))
        board_item = _action_board_item(
            action_id=repair_key,
            source=str(item.get("source", "repair_plan")),
            command_kind=command_kind,
            command=command,
            rationale=str(item.get("evidence", "")) or f"Repair plan item {repair_key}",
            can_execute_now=bool(item.get("can_execute_autonomously")),
            requires_manual_gate=bool(item.get("requires_manual_gate")),
            diagnostic_only=bool(item.get("diagnostic_only")),
            needs_implementation=bool(item.get("needs_implementation")),
            closure_condition=str(item.get("closure_condition", "")),
        )
        if board_item["requires_manual_gate"]:
            manual_gates.append(board_item)
        elif board_item["needs_implementation"]:
            implementation_repairs.append(board_item)
        elif board_item["diagnostic_only"]:
            diagnostic_refreshes.append(board_item)
        elif board_item["can_execute_now"]:
            runnable_repairs.append(board_item)
        else:
            blocked_actions.append(board_item)

    resumption_command = str(resumption_brief.get("next_command", ""))
    resumption_status = str(resumption_brief.get("resume_status", ""))
    dispatch_safe = dispatch_receipt.get("safe_to_dispatch") is True
    if resumption_command:
        resumption_item = _action_board_item(
            action_id="resumption_brief_next_command",
            source="resumption_brief",
            command_kind="bounded_dispatch" if resumption_status == "safe_for_one_bound_action" else "diagnostic_refresh",
            command=resumption_command,
            rationale=str(resumption_brief.get("rationale", "")),
            can_execute_now=resumption_status == "safe_for_one_bound_action" and dispatch_safe,
            diagnostic_only=resumption_status != "safe_for_one_bound_action",
            closure_condition="regenerate resumption brief after the command completes",
            authorized_strategic_route=str(resumption_brief.get("authorized_strategic_route", "")),
            authorized_route_source=str(resumption_brief.get("authorized_route_source", "")),
        )
        if resumption_item["can_execute_now"]:
            runnable_repairs.append(resumption_item)
        elif resumption_item["diagnostic_only"]:
            diagnostic_refreshes.append(resumption_item)
        else:
            blocked_actions.append(resumption_item)

    if manual_gates and runnable_repairs:
        blocked_actions.extend(
            _action_board_blocked_by_runtime_authority(item, "manual_gate_required") for item in runnable_repairs
        )
        runnable_repairs = []

    if manual_gates:
        status = "manual_gate_required"
        autonomy_mode = "wait_for_user_or_clear_approval"
        primary_action = manual_gates[0]
    elif implementation_repairs:
        status = "implementation_repair_required"
        autonomy_mode = "code_repair_required"
        primary_action = implementation_repairs[0]
    elif runnable_repairs:
        status = "bounded_action_available"
        autonomy_mode = "one_bounded_action_then_reaudit"
        primary_action = runnable_repairs[0]
    elif diagnostic_refreshes:
        status = "diagnostic_refresh_recommended"
        autonomy_mode = "refresh_trust_artifacts"
        primary_action = diagnostic_refreshes[0]
    else:
        status = "no_action_available"
        autonomy_mode = "regenerate_action_board"
        primary_action = _action_board_item(
            action_id="regenerate_action_board",
            source="action_board",
            command_kind="diagnostic_refresh",
            command=f"PYTHONPATH=src python3 -m riskflow ceo action-board --run-id {ceo_run_id}",
            rationale="No current operating artifact produced a concrete next action.",
            can_execute_now=False,
            diagnostic_only=True,
        )

    return {
        "model": CEO_ACTION_BOARD_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "autonomy_mode": autonomy_mode,
        "primary_action": primary_action,
        "manual_gates": manual_gates,
        "runnable_repairs": runnable_repairs,
        "diagnostic_refreshes": diagnostic_refreshes,
        "implementation_repairs": implementation_repairs,
        "blocked_actions": blocked_actions,
        "counts": {
            "manual_gates": len(manual_gates),
            "runnable_repairs": len(runnable_repairs),
            "diagnostic_refreshes": len(diagnostic_refreshes),
            "implementation_repairs": len(implementation_repairs),
            "blocked_actions": len(blocked_actions),
        },
        "trust_snapshot": {
            "resumption_status": resumption_status,
            "dispatch_receipt_status": dispatch_receipt.get("status", ""),
            "dispatch_safe_to_dispatch": dispatch_safe,
            "blocker_stack_status": blocker_stack.get("status", ""),
            "top_blocker": blocker_stack.get("top_blocker", ""),
            "repair_plan_status": repair_plan.get("status", ""),
            "top_repair": repair_plan.get("top_repair", ""),
            "top_repair_kind": repair_plan.get("top_repair_kind", ""),
            "executive_kpis_status": executive_kpis.get("status", ""),
            "executive_kpis_next_action": executive_kpis.get("next_action", ""),
        },
        "prohibited_actions": [
            "Do not change core_signal_v0, Pine defaults, scores, rankings, states, or alerts from this board.",
            "Do not treat diagnostic refresh commands as completed repairs.",
            "Do not execute manual-gate actions without explicit user approval.",
            "Run at most one bounded action before regenerating the board.",
        ],
        "guardrail": "Action boards are diagnostic operating surfaces. They route attention and do not authorize production behavior changes.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_action_board(board: dict[str, Any]) -> str:
    primary = board.get("primary_action", {}) or {}
    lines = [
        "# Riskflow CEO Action Board",
        "",
        f"Generated: {board.get('generated_at')}",
        f"Run: {board.get('run_id')}",
        f"Lab run: {board.get('lab_run_id')}",
        f"Status: {board.get('status')}",
        f"Autonomy mode: {board.get('autonomy_mode')}",
        "",
        "## Primary Action",
        "",
        f"- Action: {primary.get('action_id')}",
        f"- Source: {primary.get('source')}",
        f"- Kind: {primary.get('command_kind')}",
        f"- Can execute now: {primary.get('can_execute_now')}",
        f"- Manual gate: {primary.get('requires_manual_gate')}",
        f"- Diagnostic only: {primary.get('diagnostic_only')}",
        f"- Needs implementation: {primary.get('needs_implementation')}",
        f"- Command: `{primary.get('command')}`",
        f"- Closure: {primary.get('closure_condition') or 'n/a'}",
        f"- Authorized strategic route: {primary.get('authorized_strategic_route') or 'none'}",
        f"- Authorized route source: {primary.get('authorized_route_source') or 'none'}",
        f"- Rationale: {primary.get('rationale') or 'n/a'}",
        "",
        "## Queue Counts",
        "",
    ]
    counts = board.get("counts", {}) or {}
    for key in ["manual_gates", "runnable_repairs", "diagnostic_refreshes", "implementation_repairs", "blocked_actions"]:
        lines.append(f"- {key}: {counts.get(key, 0)}")
    lines.extend(["", "## Queues", ""])
    for label, key in [
        ("Manual Gates", "manual_gates"),
        ("Runnable Repairs", "runnable_repairs"),
        ("Diagnostic Refreshes", "diagnostic_refreshes"),
        ("Implementation Repairs", "implementation_repairs"),
        ("Blocked Actions", "blocked_actions"),
    ]:
        lines.extend([f"### {label}", ""])
        items = board.get(key, []) or []
        if not items:
            lines.append("- none")
        for item in items:
            lines.append(
                "- "
                f"{item.get('action_id')} kind={item.get('command_kind')} "
                f"can_execute={item.get('can_execute_now')} command=`{item.get('command')}` "
                f"route={item.get('authorized_strategic_route') or 'none'}"
            )
        lines.append("")
    lines.extend(["## Trust Snapshot", ""])
    snapshot = board.get("trust_snapshot", {}) or {}
    for key in sorted(snapshot):
        lines.append(f"- {key}: {snapshot.get(key)}")
    lines.extend(["", "## Prohibited Actions", ""])
    lines.extend(f"- {item}" for item in board.get("prohibited_actions", []) or [])
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_action_board(
    options: CeoOpsOptions,
    *,
    resumption_result: dict[str, Any] | None = None,
    repair_result: dict[str, Any] | None = None,
    dispatch_result: dict[str, Any] | None = None,
    kpi_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    reused_resumption_brief = _ceo_reused_artifact_payload(
        resumption_result,
        "brief",
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    reused_repair_plan = _ceo_reused_artifact_payload(
        repair_result,
        "repair_plan",
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    reused_dispatch_receipt = _ceo_reused_artifact_payload(
        dispatch_result,
        "receipt",
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    reused_kpis = _ceo_reused_artifact_payload(
        kpi_result,
        "kpis",
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
    )
    resumption_result = resumption_result if reused_resumption_brief is not None else run_ceo_resumption_brief(diagnostic_options)
    repair_result = repair_result if reused_repair_plan is not None else run_ceo_repair_plan(diagnostic_options)
    dispatch_result = dispatch_result if reused_dispatch_receipt is not None else run_ceo_dispatch_receipt(diagnostic_options)
    kpi_result = kpi_result if reused_kpis is not None else run_ceo_executive_kpis(diagnostic_options)
    resumption_brief = dict(resumption_result["brief"])
    dispatch_receipt = dict(dispatch_result["receipt"])
    if is_stop_requested(options, ceo_run_id, lab_run_id):
        resumption_brief["resume_status"] = "blocked_stop_requested"
        resumption_brief["next_command"] = f"PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id {ceo_run_id}"
        dispatch_receipt["safe_to_dispatch"] = False
        dispatch_receipt["status"] = "dispatch_blocked"
        dispatch_receipt["reason"] = "live stop request/manual gate overrides reused safe artifacts"
    board = build_ceo_action_board(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        resumption_brief=resumption_brief,
        dispatch_receipt=dispatch_receipt,
        blocker_stack=_load_yaml_if_exists(root / "blocker_stack.yaml"),
        repair_plan=repair_result["repair_plan"],
        executive_kpis=kpi_result["kpis"],
    )
    path = root / "action_board.yaml"
    report_path = root / "action_board.md"
    atomic_write_yaml(path, board)
    atomic_write_text(report_path, render_ceo_action_board(board))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "action_board": board,
        "paths": {
            "action_board": path,
            "action_board_report": report_path,
            "resumption_brief": resumption_result["paths"]["resumption_brief"],
            "repair_plan": repair_result["paths"]["repair_plan"],
            "dispatch_receipt_snapshot": dispatch_result["paths"]["dispatch_receipt_snapshot"],
            "executive_kpis": kpi_result["paths"]["executive_kpis"],
        },
    }


def render_ceo_operator_step(step: dict[str, Any]) -> str:
    primary = step.get("primary_action", {}) or {}
    lines = [
        "# Riskflow CEO Operator Step",
        "",
        f"Generated: {step.get('generated_at')}",
        f"Run: {step.get('run_id')}",
        f"Lab run: {step.get('lab_run_id')}",
        f"Status: {step.get('status')}",
        f"Action attempted: {step.get('action_attempted')}",
        f"Action executed: {step.get('action_executed')}",
        f"Reason: {step.get('reason')}",
        "",
        "## Primary Action",
        "",
        f"- Action: {primary.get('action_id') or 'none'}",
        f"- Kind: {primary.get('command_kind') or 'none'}",
        f"- Can execute now: {primary.get('can_execute_now')}",
        f"- Command: `{primary.get('command') or ''}`",
        "",
        "## Execution",
        "",
        f"- Execution status: {step.get('execution_status') or 'n/a'}",
        f"- Execution action taken: {step.get('execution_action_taken') or 'n/a'}",
        f"- Execution decision: {step.get('execution_decision') or 'n/a'}",
        f"- Execution meaningful progress: {step.get('execution_meaningful_progress') if step.get('execution_meaningful_progress') != '' else 'n/a'}",
        "",
        "## Board Status",
        "",
        f"- Before: {step.get('before_board_status')}",
        f"- After: {step.get('after_board_status') or 'n/a'}",
        f"- After primary action: {step.get('after_primary_action') or 'n/a'}",
        f"- Before board snapshot sha256: {step.get('before_action_board_snapshot_sha256') or 'n/a'}",
        f"- After board snapshot sha256: {step.get('after_action_board_snapshot_sha256') or 'n/a'}",
        "",
        "## Guardrails",
        "",
    ]
    lines.extend(f"- {item}" for item in step.get("guardrails", []) or [])
    lines.extend(["", "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_operator_step(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo operator-step requires --apply")
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    before_result = run_ceo_action_board(diagnostic_options)
    before_board = before_result["action_board"]
    primary = before_board.get("primary_action", {}) or {}
    primary_kind = str(primary.get("command_kind", ""))
    primary_command = str(primary.get("command", ""))
    can_execute_now = primary.get("can_execute_now") is True

    execution_result: dict[str, Any] | None = None
    action_attempted = False
    action_executed = False
    if before_board.get("status") == "manual_gate_required":
        status = "blocked_manual_gate"
        reason = "The action board's primary action requires explicit user approval or stop-clear authority."
    elif before_board.get("status") == "implementation_repair_required":
        status = "blocked_implementation_required"
        reason = "The action board's primary action is a symbolic code repair, not an executable CEO command."
    elif before_board.get("status") == "diagnostic_refresh_recommended":
        status = "diagnostic_refresh_only"
        reason = "The action board recommends refreshing diagnostics; operator-step already refreshed the board and will not count that as a repair."
    elif not can_execute_now:
        status = "blocked_not_safe_to_execute"
        reason = "The action board did not mark the primary action safe to execute now."
    elif primary_kind != "bounded_dispatch" or " riskflow ceo execute-next " not in f" {primary_command} ":
        status = "blocked_unsupported_primary_action"
        reason = "Operator-step only executes internal bounded dispatch; it refuses arbitrary or unsupported commands."
    else:
        action_attempted = True
        execution_result = run_ceo_execute_next(replace(options, apply=True))
        action_result = execution_result["action_result"]
        execution_status = str(action_result.get("status", ""))
        raw_meaningful_progress = action_result.get("meaningful_progress")
        meaningful_progress = (
            bool(raw_meaningful_progress)
            if raw_meaningful_progress is not None
            else execution_status not in CEO_NO_PROGRESS_STATUSES and execution_status != "manual_gate"
        )
        if execution_status == "blocked":
            action_executed = False
            status = "bounded_action_blocked"
        elif execution_status == "manual_gate":
            action_executed = False
            status = "bounded_action_reached_manual_gate"
        elif execution_status == "capability_gap" and not meaningful_progress:
            action_executed = False
            status = "bounded_action_reached_capability_gap"
        elif not meaningful_progress:
            action_executed = False
            status = "bounded_action_no_meaningful_progress"
        elif execution_status == "capability_gap":
            action_executed = True
            status = "bounded_action_recorded_capability_gap"
        else:
            action_executed = True
            status = "bounded_action_executed"
        reason = str(action_result.get("reason") or action_result.get("status") or "bounded dispatch completed")

    after_result = run_ceo_action_board(diagnostic_options)
    after_board = after_result["action_board"]
    action_result = (execution_result or {}).get("action_result", {}) if execution_result else {}
    step_generated_at = utc_now_iso()
    snapshot_dir = root / "operator_step_boards"
    snapshot_slug = _receipt_slug(step_generated_at)
    before_board_snapshot = snapshot_dir / f"{snapshot_slug}_before_action_board.yaml"
    after_board_snapshot = snapshot_dir / f"{snapshot_slug}_after_action_board.yaml"
    atomic_write_yaml(before_board_snapshot, before_board)
    atomic_write_yaml(after_board_snapshot, after_board)
    binding_action_result_ref = (execution_result or {}).get("paths", {}).get("binding_action_result", "")
    binding_action_result_path = Path(str(binding_action_result_ref)) if binding_action_result_ref else Path()
    step = {
        "model": CEO_OPERATOR_STEP_MODEL,
        "generated_at": step_generated_at,
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "reason": reason,
        "action_attempted": action_attempted,
        "action_executed": action_executed,
        "primary_action": primary,
        "before_board_status": before_board.get("status", ""),
        "after_board_status": after_board.get("status", ""),
        "after_primary_action": (after_board.get("primary_action", {}) or {}).get("action_id", ""),
        "execution_status": action_result.get("status", ""),
        "execution_action_taken": action_result.get("action_taken", ""),
        "execution_decision": action_result.get("decision", ""),
        "execution_meaningful_progress": action_result.get("meaningful_progress", ""),
        "before_primary_action_id": primary.get("action_id", ""),
        "before_primary_command": primary_command,
        "before_action_board_snapshot_sha256": _file_sha256(before_board_snapshot),
        "after_action_board_snapshot_sha256": _file_sha256(after_board_snapshot),
        "binding_action_result_sha256": _file_sha256(binding_action_result_path),
        "paths": {
            "before_action_board": str(before_result["paths"]["action_board"]),
            "before_action_board_report": str(before_result["paths"]["action_board_report"]),
            "before_action_board_snapshot": str(before_board_snapshot),
            "after_action_board": str(after_result["paths"]["action_board"]),
            "after_action_board_report": str(after_result["paths"]["action_board_report"]),
            "after_action_board_snapshot": str(after_board_snapshot),
            "binding_action_result": str((execution_result or {}).get("paths", {}).get("binding_action_result", "")),
        },
        "guardrails": [
            "Operator-step runs at most one internal bounded dispatch.",
            "It does not execute shell commands from YAML.",
            "It does not clear manual gates, approve production changes, change product formulas, or authorize product language.",
            "Regenerate action-board after every step before deciding again.",
        ],
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }
    path = root / "operator_step.yaml"
    report_path = root / "operator_step.md"
    ledger_path = root / "operator_step_ledger.jsonl"
    atomic_write_yaml(path, step)
    atomic_write_text(report_path, render_ceo_operator_step(step))
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_json_safe(step), sort_keys=True) + "\n")
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "operator_step": step,
        "action_result": action_result,
        "paths": {
            "operator_step": path,
            "operator_step_report": report_path,
            "operator_step_ledger": ledger_path,
            "before_action_board": before_result["paths"]["action_board"],
            "before_action_board_snapshot": before_board_snapshot,
            "after_action_board": after_result["paths"]["action_board"],
            "after_action_board_snapshot": after_board_snapshot,
            **((execution_result or {}).get("paths", {}) if execution_result else {}),
        },
    }


def build_ceo_operator_brief(
    *,
    ceo_run_id: str,
    lab_run_id: str,
    company_status: dict[str, Any],
    action_board: dict[str, Any],
    decision_quality: dict[str, Any],
    operator_step: dict[str, Any],
    role_queue: dict[str, Any] | None = None,
    approval_queue: dict[str, Any] | None = None,
    trace_grade: dict[str, Any] | None = None,
) -> dict[str, Any]:
    primary = action_board.get("primary_action", {}) or {}
    role_queue = role_queue or {}
    approval_queue = approval_queue or {}
    trace_grade = trace_grade or {}
    lab_status = company_status.get("lab_status", {}) or {}
    action_board_status = str(action_board.get("status", ""))
    if action_board_status == "manual_gate_required":
        status = "waiting_on_manual_gate"
        next_action = str(primary.get("command", ""))
        plain_summary = "CEO mode is stopped at a manual gate. It should not take another autonomous action."
    elif action_board_status == "bounded_action_available":
        status = "ready_for_one_operator_step"
        next_action = f"PYTHONPATH=src python3 -m riskflow ceo operator-step --run-id {ceo_run_id} --apply"
        plain_summary = "CEO mode has one bounded action available. Run one operator-step, then re-audit."
    elif action_board_status == "implementation_repair_required":
        status = "needs_code_repair"
        next_action = str(primary.get("command", ""))
        plain_summary = "CEO mode found an implementation repair that needs code work before automation continues."
    elif action_board_status == "diagnostic_refresh_recommended":
        status = "refresh_diagnostics"
        next_action = str(primary.get("command", ""))
        plain_summary = "CEO mode should refresh diagnostics before claiming it can safely act."
    else:
        status = "no_safe_action"
        next_action = str(primary.get("command", ""))
        plain_summary = "CEO mode does not currently have a safe autonomous action."
    effective_operator = _effective_operator_status(
        action_board=action_board,
        operator_brief={"status": status},
        decision_quality=decision_quality,
    )
    refused_actions = [
        "manual approvals or stop-clear actions without explicit user confirmation",
        "production formula, Pine default, score, ranking, state, or alert changes",
        "product-language claims from process artifacts",
        "arbitrary shell execution from YAML commands",
        "more than one bounded action without regenerating trust artifacts",
    ]
    return {
        "model": CEO_OPERATOR_BRIEF_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": status,
        "plain_english_summary": plain_summary,
        "current_situation": {
            "lab_status": lab_status.get("status", ""),
            "stop_reason": lab_status.get("stop_reason", ""),
            "effective_operator_status": effective_operator.get("effective_operator_status", ""),
            "manual_gate_active": effective_operator.get("manual_gate_active", ""),
            "effective_operator_runtime_blocked": effective_operator.get("runtime_blocked", ""),
            "effective_operator_runtime_block_reason": effective_operator.get("runtime_block_reason", ""),
            "trace_grade_status": trace_grade.get("verdict", "missing_trace_grade"),
            "trace_grade_score": trace_grade.get("score", ""),
            "trace_grade_recommended_next_action": trace_grade.get("recommended_next_action", ""),
            "trace_grade_issues": trace_grade.get("issues", []),
            "trace_grade_manual_data_import_required": _trace_grade_manual_data_import_required(trace_grade),
            "action_board_status": action_board_status,
            "primary_action": primary.get("action_id", ""),
            "primary_kind": primary.get("command_kind", ""),
            "decision_quality_effective_runtime_action": decision_quality.get("effective_runtime_action", ""),
            "decision_quality_effective_runtime_command_kind": decision_quality.get("effective_runtime_command_kind", ""),
            "decision_quality_effective_runtime_can_execute_now": decision_quality.get("effective_runtime_can_execute_now", ""),
            "decision_quality_runtime_blocked": decision_quality.get("runtime_blocked", ""),
            "decision_quality_runtime_block_reason": decision_quality.get("runtime_block_reason", ""),
            "decision_quality_selected_action": decision_quality.get("selected_action", ""),
            "decision_quality_selected_strategic_route_advisory": decision_quality.get("selected_strategic_route_advisory", ""),
            "decision_quality_confidence": decision_quality.get("confidence", ""),
            "decision_quality_runtime_authority": decision_quality.get("runtime_authority_status", ""),
            "decision_quality_executable_next_action": decision_quality.get("executable_next_action", ""),
            "decision_quality_executable_command_kind": decision_quality.get("executable_next_command_kind", ""),
            "decision_quality_runtime_authorized_strategic_route": decision_quality.get("runtime_authorized_strategic_route", ""),
            "decision_quality_executable_can_execute_now": decision_quality.get("executable_can_execute_now", ""),
            "decision_quality_selected_action_is_executable_now": decision_quality.get("selected_action_is_executable_now", ""),
            "decision_quality_selected_action_blocked_by": decision_quality.get("selected_action_blocked_by", ""),
            "last_operator_step_status": operator_step.get("status", ""),
            "role_queue_status": role_queue.get("status", ""),
            "role_pending_task_count": role_queue.get("pending_task_count", ""),
            "role_pending_manual_task_count": role_queue.get("pending_manual_task_count", ""),
            "role_pending_autonomous_task_count": role_queue.get("pending_autonomous_task_count", ""),
            "role_completed_task_count": role_queue.get("completed_task_count", ""),
            "role_blocked_task_count": role_queue.get("blocked_task_count", ""),
            "role_top_pending_task_id": role_queue.get("top_pending_task_id", ""),
            "role_top_pending_role_id": role_queue.get("top_pending_role_id", ""),
            "role_top_pending_packet_path": role_queue.get("top_pending_packet_path", ""),
            "role_top_pending_result_resolution_mode": role_queue.get("top_pending_result_resolution_mode", ""),
            "role_top_pending_requires_manual_gate": role_queue.get("top_pending_requires_manual_gate", ""),
            "role_top_pending_closure_command": role_queue.get("top_pending_closure_command", ""),
            "role_top_autonomous_pending_task_id": role_queue.get("top_autonomous_pending_task_id", ""),
            "role_top_autonomous_pending_role_id": role_queue.get("top_autonomous_pending_role_id", ""),
            "role_top_autonomous_pending_packet_path": role_queue.get("top_autonomous_pending_packet_path", ""),
            "role_top_autonomous_next_result_command": role_queue.get("top_autonomous_next_role_result_command", ""),
            "role_top_blocked_task_id": role_queue.get("top_blocked_task_id", ""),
            "role_top_blocked_role_id": role_queue.get("top_blocked_role_id", ""),
            "role_top_blocked_packet_path": role_queue.get("top_blocked_packet_path", ""),
            "role_top_blocked_result_resolution_mode": role_queue.get("top_blocked_result_resolution_mode", ""),
            "role_top_blocked_validation_status": role_queue.get("top_blocked_validation_status", ""),
            "role_top_blocked_closure_command": _ceo_role_queue_top_blocked_closure_command(
                ceo_run_id=ceo_run_id,
                role_queue=role_queue,
            ),
            "role_top_blocked_review_status": role_queue.get("top_blocked_review_status", ""),
            "role_top_blocked_result_path": role_queue.get("top_blocked_result_path", ""),
            "role_top_blocked_next_action": role_queue.get("top_blocked_next_action", ""),
            "role_top_blocked_finding": role_queue.get("top_blocked_finding", ""),
            "role_next_result_command": role_queue.get("next_role_result_command", ""),
            "approval_queue_status": approval_queue.get("status", ""),
            "approval_pending_count": approval_queue.get("pending_count", ""),
            "approval_top_pending_id": approval_queue.get("top_pending_approval_id", ""),
            "approval_record_command": approval_queue.get("top_pending_approval_record_command", ""),
            "approval_apply_command": approval_queue.get("top_pending_approval_apply_command", ""),
        },
        "approval_work": {
            "status": approval_queue.get("status", "missing_approval_queue"),
            "pending_count": approval_queue.get("pending_count", ""),
            "top_pending_approval_id": approval_queue.get("top_pending_approval_id", ""),
            "approval_record_command": approval_queue.get("top_pending_approval_record_command", ""),
            "approval_apply_command": approval_queue.get("top_pending_approval_apply_command", ""),
            "authority": "user_only" if approval_queue.get("pending_count", 0) else "none",
            "readiness_effect": "pending approvals block autonomous action and require explicit user-confirmed record/apply steps",
            "production_effect": "none",
        },
        "trace_health": {
            "status": trace_grade.get("verdict", "missing_trace_grade"),
            "score": trace_grade.get("score", ""),
            "recommended_next_action": trace_grade.get("recommended_next_action", ""),
            "issues": trace_grade.get("issues", []),
            "manual_data_import_required": _trace_grade_manual_data_import_required(trace_grade),
            "readiness_effect": "failed trace grade blocks dispatch through preflight and must be resolved before autonomous action",
            "production_effect": "none",
        },
        "specialist_work": {
            "status": role_queue.get("status", "missing_role_task_queue"),
            "pending_task_count": role_queue.get("pending_task_count", ""),
            "pending_manual_task_count": role_queue.get("pending_manual_task_count", ""),
            "pending_autonomous_task_count": role_queue.get("pending_autonomous_task_count", ""),
            "completed_task_count": role_queue.get("completed_task_count", ""),
            "blocked_task_count": role_queue.get("blocked_task_count", ""),
            "top_pending_task_id": role_queue.get("top_pending_task_id", ""),
            "top_pending_role_id": role_queue.get("top_pending_role_id", ""),
            "top_pending_packet_path": role_queue.get("top_pending_packet_path", ""),
            "top_pending_result_resolution_mode": role_queue.get("top_pending_result_resolution_mode", ""),
            "top_pending_requires_manual_gate": role_queue.get("top_pending_requires_manual_gate", ""),
            "top_pending_closure_command": role_queue.get("top_pending_closure_command", ""),
            "top_autonomous_pending_task_id": role_queue.get("top_autonomous_pending_task_id", ""),
            "top_autonomous_pending_role_id": role_queue.get("top_autonomous_pending_role_id", ""),
            "top_autonomous_pending_packet_path": role_queue.get("top_autonomous_pending_packet_path", ""),
            "top_autonomous_next_role_result_command": role_queue.get("top_autonomous_next_role_result_command", ""),
            "top_blocked_task_id": role_queue.get("top_blocked_task_id", ""),
            "top_blocked_role_id": role_queue.get("top_blocked_role_id", ""),
            "top_blocked_packet_path": role_queue.get("top_blocked_packet_path", ""),
            "top_blocked_result_resolution_mode": role_queue.get("top_blocked_result_resolution_mode", ""),
            "top_blocked_validation_status": role_queue.get("top_blocked_validation_status", ""),
            "top_blocked_closure_command": _ceo_role_queue_top_blocked_closure_command(
                ceo_run_id=ceo_run_id,
                role_queue=role_queue,
            ),
            "top_blocked_review_status": role_queue.get("top_blocked_review_status", ""),
            "top_blocked_result_path": role_queue.get("top_blocked_result_path", ""),
            "top_blocked_next_action": role_queue.get("top_blocked_next_action", ""),
            "top_blocked_finding": role_queue.get("top_blocked_finding", ""),
            "next_role_dispatch_command": role_queue.get("next_role_dispatch_command", ""),
            "next_role_result_command": role_queue.get("next_role_result_command", ""),
            "readiness_effect": "pending or blocked role tasks lower 9.9 readiness but do not approve or block production behavior",
            "production_effect": "none",
        },
        "recommended_next_action": next_action,
        "why": [
            str(primary.get("rationale", "")) or "Action board selected the current primary action.",
            str(decision_quality.get("selected_rationale", "")) or "Decision quality explains the current routing.",
        ],
        "refused_actions": refused_actions,
        "evidence_refs": {
            "company_status": "company_status.yaml",
            "action_board": "action_board.yaml",
            "decision_quality": "decision_quality.yaml",
            "operator_step": "operator_step.yaml",
            "approval_queue": "approval_queue.yaml",
            "approval_status": "approval_status.yaml",
            "role_task_queue": "role_task_queue.yaml",
        },
        "guardrail": "Operator brief is a human-readable summary only. It does not approve execution or production behavior.",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }


def render_ceo_operator_brief(brief: dict[str, Any]) -> str:
    situation = brief.get("current_situation", {}) or {}
    lines = [
        "# Riskflow CEO Operator Brief",
        "",
        f"Generated: {brief.get('generated_at')}",
        f"Run: {brief.get('run_id')}",
        f"Lab run: {brief.get('lab_run_id')}",
        f"Status: {brief.get('status')}",
        "",
        "## Plain English",
        "",
        str(brief.get("plain_english_summary", "")),
        "",
        "## Current Situation",
        "",
    ]
    for key in [
        "lab_status",
        "stop_reason",
        "effective_operator_status",
        "manual_gate_active",
        "effective_operator_runtime_blocked",
        "effective_operator_runtime_block_reason",
        "trace_grade_status",
        "trace_grade_score",
        "trace_grade_recommended_next_action",
        "trace_grade_issues",
        "trace_grade_manual_data_import_required",
        "action_board_status",
        "primary_action",
        "primary_kind",
        "decision_quality_effective_runtime_action",
        "decision_quality_effective_runtime_command_kind",
        "decision_quality_effective_runtime_can_execute_now",
        "decision_quality_runtime_blocked",
        "decision_quality_runtime_block_reason",
        "decision_quality_selected_action",
        "decision_quality_selected_strategic_route_advisory",
        "decision_quality_confidence",
        "decision_quality_runtime_authority",
        "decision_quality_executable_next_action",
        "decision_quality_executable_command_kind",
        "decision_quality_runtime_authorized_strategic_route",
        "decision_quality_executable_can_execute_now",
        "decision_quality_selected_action_is_executable_now",
        "decision_quality_selected_action_blocked_by",
        "last_operator_step_status",
        "role_queue_status",
        "role_pending_task_count",
        "role_pending_manual_task_count",
        "role_pending_autonomous_task_count",
        "role_top_pending_task_id",
        "role_top_pending_role_id",
        "role_top_pending_packet_path",
        "role_top_pending_result_resolution_mode",
        "role_top_pending_requires_manual_gate",
        "role_top_pending_closure_command",
        "role_top_autonomous_pending_task_id",
        "role_top_autonomous_pending_role_id",
        "role_top_autonomous_pending_packet_path",
        "role_top_autonomous_next_result_command",
        "role_top_blocked_task_id",
        "role_top_blocked_role_id",
        "role_top_blocked_packet_path",
        "role_top_blocked_result_resolution_mode",
        "role_top_blocked_validation_status",
        "role_top_blocked_closure_command",
        "role_top_blocked_review_status",
        "role_top_blocked_result_path",
        "role_top_blocked_next_action",
        "role_top_blocked_finding",
        "role_next_result_command",
        "approval_queue_status",
        "approval_pending_count",
        "approval_top_pending_id",
        "approval_record_command",
        "approval_apply_command",
    ]:
        lines.append(f"- {key}: {situation.get(key)}")
    approval = brief.get("approval_work", {}) or {}
    lines.extend(
        [
            "",
            "## Approval Work",
            "",
            f"- Status: {approval.get('status')}",
            f"- Pending: {approval.get('pending_count')}",
            f"- Top approval: {approval.get('top_pending_approval_id') or 'none'}",
            f"- Record command: `{approval.get('approval_record_command') or ''}`",
            f"- Apply command: `{approval.get('approval_apply_command') or ''}`",
            f"- Authority: {approval.get('authority')}",
            f"- Readiness effect: {approval.get('readiness_effect')}",
        ]
    )
    trace = brief.get("trace_health", {}) or {}
    lines.extend(
        [
            "",
            "## Trace Health",
            "",
            f"- Status: {trace.get('status')}",
            f"- Score: {trace.get('score')}",
            f"- Recommended next action: {trace.get('recommended_next_action') or 'none'}",
            f"- Manual data import required: {trace.get('manual_data_import_required')}",
            f"- Issues: {trace.get('issues') or []}",
            f"- Readiness effect: {trace.get('readiness_effect')}",
        ]
    )
    specialist = brief.get("specialist_work", {}) or {}
    lines.extend(
        [
            "",
            "## Specialist Work",
            "",
            f"- Status: {specialist.get('status')}",
            f"- Pending: {specialist.get('pending_task_count')}",
            f"- Pending manual: {specialist.get('pending_manual_task_count')}",
            f"- Pending autonomous: {specialist.get('pending_autonomous_task_count')}",
            f"- Completed: {specialist.get('completed_task_count')}",
            f"- Blocked: {specialist.get('blocked_task_count')}",
            f"- Top task: {specialist.get('top_pending_task_id') or 'none'}",
            f"- Top role: {specialist.get('top_pending_role_id') or 'none'}",
            f"- Top packet: {specialist.get('top_pending_packet_path') or 'none'}",
            f"- Top result mode: {specialist.get('top_pending_result_resolution_mode') or 'none'}",
            f"- Top requires manual gate: {specialist.get('top_pending_requires_manual_gate')}",
            f"- Top closure command: `{specialist.get('top_pending_closure_command') or ''}`",
            f"- Top autonomous task: {specialist.get('top_autonomous_pending_task_id') or 'none'}",
            f"- Top autonomous role: {specialist.get('top_autonomous_pending_role_id') or 'none'}",
            f"- Top autonomous packet: {specialist.get('top_autonomous_pending_packet_path') or 'none'}",
            f"- Top autonomous result: `{specialist.get('top_autonomous_next_role_result_command') or ''}`",
            f"- Top blocked task: {specialist.get('top_blocked_task_id') or 'none'}",
            f"- Top blocked role: {specialist.get('top_blocked_role_id') or 'none'}",
            f"- Top blocked packet: {specialist.get('top_blocked_packet_path') or 'none'}",
            f"- Top blocked result mode: {specialist.get('top_blocked_result_resolution_mode') or 'none'}",
            f"- Top blocked validation: {specialist.get('top_blocked_validation_status') or 'none'}",
            f"- Top blocked closure command: `{specialist.get('top_blocked_closure_command') or ''}`",
            f"- Top blocked review status: {specialist.get('top_blocked_review_status') or 'none'}",
            f"- Top blocked result path: {specialist.get('top_blocked_result_path') or 'none'}",
            f"- Top blocked next action: {specialist.get('top_blocked_next_action') or 'none'}",
            f"- Top blocked finding: {specialist.get('top_blocked_finding') or 'none'}",
            f"- Next role dispatch: `{specialist.get('next_role_dispatch_command') or ''}`",
            f"- Next role result: `{specialist.get('next_role_result_command') or ''}`",
            f"- Readiness effect: {specialist.get('readiness_effect')}",
        ]
    )
    lines.extend(
        [
            "",
            "## Recommended Next Action",
            "",
            f"`{brief.get('recommended_next_action') or ''}`",
            "",
            "## Why",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in brief.get("why", []) or [])
    lines.extend(["", "## Refused Actions", ""])
    lines.extend(f"- {item}" for item in brief.get("refused_actions", []) or [])
    lines.extend(["", str(brief.get("guardrail")), "Production effect: none.", ""])
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_operator_brief(
    options: CeoOpsOptions,
    *,
    action_board_result: dict[str, Any] | None = None,
    decision_quality_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    status_result = run_ceo_status(diagnostic_options)
    action_board_result = action_board_result or run_ceo_action_board(diagnostic_options)
    decision_quality_result = decision_quality_result or run_ceo_decision_quality(
        diagnostic_options,
        action_board_result=action_board_result,
    )
    final_action_board = _load_yaml_if_exists(root / "action_board.yaml") or action_board_result["action_board"]
    final_decision_quality = _load_yaml_if_exists(root / "decision_quality.yaml") or decision_quality_result["decision_quality"]
    trace_grade = _load_yaml_if_exists(root / "trace_grade.yaml")
    approval_result = run_ceo_approval_queue(diagnostic_options)
    role_result = run_ceo_role_queue(diagnostic_options)
    brief = build_ceo_operator_brief(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        company_status=status_result["company_status"],
        action_board=final_action_board,
        decision_quality=final_decision_quality,
        operator_step=_load_yaml_if_exists(root / "operator_step.yaml"),
        role_queue=role_result["queue"],
        approval_queue=approval_result["queue"],
        trace_grade=trace_grade,
    )
    path = root / "operator_brief.yaml"
    report_path = root / "operator_brief.md"
    atomic_write_yaml(path, brief)
    atomic_write_text(report_path, render_ceo_operator_brief(brief))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "operator_brief": brief,
        "paths": {
            "operator_brief": path,
            "operator_brief_report": report_path,
            "action_board": action_board_result["paths"]["action_board"],
            "decision_quality": decision_quality_result["paths"]["decision_quality"],
            "approval_queue": approval_result["paths"]["queue"],
            "approval_status": approval_result["paths"]["approval_status"],
            "role_task_queue": role_result["paths"]["role_task_queue"],
        },
    }


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
    _require_ceo_action_context(
        options,
        action="continue_governed_research",
        aliases={"run-block"},
    )
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
    last_action = _load_yaml_if_exists(root / "binding_action_result.yaml")
    decision = _decision_from_previous_next_action(last_action, decision)
    decision_kind = str(decision.get("decision", "unknown"))

    if is_stop_requested(options, ceo_run_id, lab_run_id):
        contract_paths = _write_ceo_action_contract(options, ceo_run_id, lab_run_id, decision)
        receipt_paths = _write_ceo_dispatch_receipt(
            options,
            ceo_run_id,
            lab_run_id,
            decision,
            preflight_gate={"status": "not_run", "safe_to_execute": False, "blockers": [{"blocker": "stop_requested"}]},
            safe_to_dispatch=False,
            reason="stop.request exists",
            dispatch_mode="execute_next",
        )
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
            "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(contract_paths)
        paths.update(receipt_paths)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    if company_status.get("true_blocker"):
        contract_paths = _write_ceo_action_contract(options, ceo_run_id, lab_run_id, decision)
        receipt_paths = _write_ceo_dispatch_receipt(
            options,
            ceo_run_id,
            lab_run_id,
            decision,
            preflight_gate={"status": "not_run", "safe_to_execute": False, "blockers": [{"blocker": "true_blocker"}]},
            safe_to_dispatch=False,
            reason=decision.get("rationale", "true blocker"),
            dispatch_mode="execute_next",
        )
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
            "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(contract_paths)
        paths.update(receipt_paths)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    if company_status.get("governance", {}).get("product_change_allowed"):
        contract_paths = _write_ceo_action_contract(options, ceo_run_id, lab_run_id, decision)
        receipt_paths = _write_ceo_dispatch_receipt(
            options,
            ceo_run_id,
            lab_run_id,
            decision,
            preflight_gate={
                "status": "not_run",
                "safe_to_execute": False,
                "blockers": [{"blocker": "production_promotion_gate"}],
            },
            safe_to_dispatch=False,
            reason="validation governance indicates product_change_allowed",
            dispatch_mode="execute_next",
        )
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
            "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(contract_paths)
        paths.update(receipt_paths)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    preflight_result = run_ceo_preflight_gate(options, enforce_memory_delta=True)
    preflight_gate = preflight_result["preflight_gate"]
    contract_paths = _write_ceo_action_contract(options, ceo_run_id, lab_run_id, decision)

    preflight_blockers = [str(item.get("blocker", "")) for item in preflight_gate.get("blockers", []) or []]
    trace_repair_decisions = {
        "resolve_ceo_self_audit_intervention",
        "patch_research_infra",
        "broaden_hypothesis_source",
        "request_fresh_data",
    }
    preflight_allows_repair = (
        set(preflight_blockers) == {"trace_grade_failed"} and decision_kind in trace_repair_decisions
    )
    if preflight_gate.get("safe_to_execute") is False and not preflight_allows_repair:
        receipt_paths = _write_ceo_dispatch_receipt(
            options,
            ceo_run_id,
            lab_run_id,
            decision,
            preflight_gate=preflight_gate,
            safe_to_dispatch=False,
            reason="ceo preflight gate blocked bound dispatch",
            dispatch_mode="execute_next",
            preflight_allows_repair=preflight_allows_repair,
        )
        blockers = preflight_blockers
        if "pending_user_approval" in blockers:
            approval_queue = _load_yaml_if_exists(root / "approval_queue.yaml")
            action_result = {
                "model": CEO_ACTION_RESULT_MODEL,
                "generated_at": utc_now_iso(),
                "run_id": ceo_run_id,
                "lab_run_id": lab_run_id,
                "decision": decision_kind,
                "action_taken": "blocked_pending_user_approval",
                "command_executed": None,
                "status": "blocked",
                "meaningful_progress": False,
                "reason": "preflight gate found pending red-authority approval items",
                "pending_approval_ids": [
                    item.get("approval_id") for item in approval_queue.get("pending_items", []) or []
                ],
                "next_allowed_actions": ["wait_for_user_approval"],
                "preflight_blockers": preflight_gate.get("blockers", []),
                "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
                "production_effect": "none",
            }
            paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
            paths.update(contract_paths)
            paths.update(receipt_paths)
            paths.update(
                {
                    "approval_queue": root / "approval_queue.yaml",
                    "preflight_gate": preflight_result["paths"]["preflight_gate"],
                    "preflight_gate_report": preflight_result["paths"]["preflight_gate_report"],
                }
            )
            return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_preflight_gate",
            "command_executed": None,
            "status": "blocked",
            "meaningful_progress": False,
            "reason": "ceo preflight gate blocked bound dispatch",
            "preflight_blockers": preflight_gate.get("blockers", []),
            "next_allowed_actions": ["repair_preflight_blockers"],
            "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(contract_paths)
        paths.update(receipt_paths)
        paths.update(
            {
                "preflight_gate": preflight_result["paths"]["preflight_gate"],
                "preflight_gate_report": preflight_result["paths"]["preflight_gate_report"],
            }
        )
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    approval_result = run_ceo_approval_queue(options)
    approval_queue = approval_result["queue"]
    if int(approval_queue.get("pending_count", 0) or 0) > 0:
        receipt_paths = _write_ceo_dispatch_receipt(
            options,
            ceo_run_id,
            lab_run_id,
            decision,
            preflight_gate=preflight_gate,
            approval_queue=approval_queue,
            safe_to_dispatch=False,
            reason="approval_queue has pending red-authority items",
            dispatch_mode="execute_next",
            preflight_allows_repair=preflight_allows_repair,
        )
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_pending_user_approval",
            "command_executed": None,
            "status": "blocked",
            "meaningful_progress": False,
            "reason": "approval_queue has pending red-authority items",
            "pending_approval_ids": [item.get("approval_id") for item in approval_queue.get("pending_items", []) or []],
            "next_allowed_actions": ["wait_for_user_approval"],
            "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(contract_paths)
        paths.update(receipt_paths)
        paths.update({"approval_queue": approval_result["paths"]["queue"]})
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    self_audit = _load_yaml_if_exists(root / "ceo_self_audit.yaml")
    intervention_decisions = {
        "patch_research_infra",
        "broaden_hypothesis_source",
        "request_fresh_data",
        "run_frozen_candidate_validation",
        "run_frozen_validation_executor",
        "run_frozen_validation_rerun",
        "run_fresh_withheld_validation_contract",
        "run_fresh_withheld_snapshot_manifest",
        "run_fresh_withheld_validation_executor",
        "import_or_curate_fresh_ohlcv_data",
        "resolve_ceo_self_audit_intervention",
        "stop_true_blocker",
    }
    if self_audit.get("intervention_required") and decision_kind not in intervention_decisions:
        receipt_paths = _write_ceo_dispatch_receipt(
            options,
            ceo_run_id,
            lab_run_id,
            decision,
            preflight_gate=preflight_gate,
            approval_queue=approval_queue,
            safe_to_dispatch=False,
            reason=self_audit.get("intervention", "ceo self-audit requires intervention before repeating action"),
            dispatch_mode="execute_next",
            preflight_allows_repair=preflight_allows_repair,
        )
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_self_audit_intervention_required",
            "command_executed": None,
            "status": "blocked",
            "meaningful_progress": False,
            "reason": self_audit.get("intervention", "ceo self-audit requires intervention before repeating action"),
            "next_allowed_actions": [
                "resolve_ceo_self_audit_intervention",
                "patch_research_infra",
                "broaden_hypothesis_source",
                "request_fresh_data",
                "stop",
            ],
            "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(contract_paths)
        paths.update(receipt_paths)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    if decision_kind == "import_or_curate_fresh_ohlcv_data":
        receipt_paths = _write_ceo_dispatch_receipt(
            options,
            ceo_run_id,
            lab_run_id,
            decision,
            preflight_gate=preflight_gate,
            approval_queue=approval_queue,
            safe_to_dispatch=False,
            reason="manual OHLCV import or curation is required before fresh validation",
            dispatch_mode="execute_next",
            preflight_allows_repair=preflight_allows_repair,
        )
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "blocked_manual_data_import_required",
            "command_executed": None,
            "status": "manual_gate",
            "meaningful_progress": False,
            "reason": "local OHLCV data is not ready; manual import or curation is required before fresh validation",
            "next_allowed_actions": ["request_fresh_data"],
            "dispatch_receipt": _dispatch_receipt_reference(receipt_paths["dispatch_receipt_snapshot"]),
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(contract_paths)
        paths.update(receipt_paths)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    receipt_paths = _write_ceo_dispatch_receipt(
        options,
        ceo_run_id,
        lab_run_id,
        decision,
        preflight_gate=preflight_gate,
        approval_queue=approval_queue,
        safe_to_dispatch=True,
        reason="preflight, approval, and self-audit gates allowed one bound dispatch",
        dispatch_mode="execute_next",
        preflight_allows_repair=preflight_allows_repair,
    )
    dispatch_metadata_paths = {**contract_paths, **receipt_paths}
    dispatch_options = _with_ceo_context(options, context="bound_dispatch", action=decision_kind)

    if decision_kind == "resolve_ceo_self_audit_intervention":
        next_action = "patch_research_infra"
        if company_status.get("lab_status", {}).get("stop_reason") == "request_fresh_data":
            next_action = "request_fresh_data"
        elif not product_delta.get("candidate_count") and not company_status.get("governance", {}).get("open_lanes"):
            next_action = "broaden_hypothesis_source"
        action_result = {
            "model": CEO_ACTION_RESULT_MODEL,
            "generated_at": utc_now_iso(),
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "decision": decision_kind,
            "action_taken": "self_audit_intervention_routed",
            "command_executed": None,
            "status": "intervention_routed",
            "meaningful_progress": True,
            "reason": self_audit.get("intervention", "ceo self-audit required intervention routing"),
            "next_allowed_actions": [next_action],
            "production_effect": "none",
        }
        paths = _write_binding_action_result(options, ceo_run_id, lab_run_id, action_result)
        paths.update(dispatch_metadata_paths)
        return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "action_result": action_result, "paths": paths}

    if decision_kind == "run_fresh_or_control_validation_for_promising_shadow_challengers":
        result = run_ceo_fresh_control_validation(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "run_champion_challenger":
        last_next_actions = [str(item) for item in last_action.get("next_allowed_actions", []) or []]
        if "run_fresh_or_control_validation_for_promising_shadow_challengers" in last_next_actions:
            result = run_ceo_fresh_control_validation(
                _with_ceo_context(
                    options,
                    context="bound_dispatch",
                    action="run_fresh_or_control_validation_for_promising_shadow_challengers",
                )
            )
            result["paths"].update(dispatch_metadata_paths)
            return result
        result = run_ceo_champion_challenger(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "patch_research_infra":
        result = run_ceo_patch_research_infra(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "broaden_hypothesis_source":
        result = run_ceo_broaden_hypothesis_source(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "run_frozen_candidate_validation":
        result = run_ceo_frozen_candidate_validation(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "run_frozen_validation_executor":
        result = run_ceo_frozen_validation_executor(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "run_frozen_validation_rerun":
        result = run_ceo_frozen_validation_rerun(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "run_fresh_withheld_validation_contract":
        result = run_ceo_fresh_withheld_validation_contract(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "run_fresh_withheld_snapshot_manifest":
        result = run_ceo_fresh_withheld_snapshot_manifest(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "run_fresh_withheld_validation_executor":
        result = run_ceo_fresh_withheld_validation_executor(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

    if decision_kind == "continue_governed_research":
        block = run_ceo_run_block(dispatch_options)
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
        paths.update(dispatch_metadata_paths)
        return {
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "action_result": action_result,
            "block": block,
            "paths": paths,
        }

    if decision_kind == "request_fresh_data":
        result = run_ceo_fresh_data_preflight(dispatch_options)
        result["paths"].update(dispatch_metadata_paths)
        return result

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
    paths.update(dispatch_metadata_paths)
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
    diagnostic_options = _with_ceo_context(options, context="diagnostic_refresh")
    trace_result = run_ceo_trace_grade(diagnostic_options)
    flight_result = run_ceo_flight_dashboard(diagnostic_options)
    contract_result = run_ceo_fresh_withheld_validation_contract(diagnostic_options)
    promotion_result = run_ceo_promotion_proposal(diagnostic_options)
    evidence_debt_result = run_ceo_evidence_debt_register(diagnostic_options)
    approval_result = run_ceo_approval_queue(diagnostic_options)
    kpi_result = run_ceo_executive_kpis(diagnostic_options)
    role_result = run_ceo_role_queue(diagnostic_options)
    role_dispatch_result = run_ceo_role_dispatch(diagnostic_options)
    org_progress_result = run_ceo_org_progress_score(diagnostic_options)
    operating_result = run_ceo_operating_dashboard(diagnostic_options)
    backlog_result = run_ceo_capability_backlog(diagnostic_options)
    mission_result = run_ceo_mission_score(diagnostic_options)
    strategy_result = run_ceo_strategy_capital_dashboard(diagnostic_options)
    replay_result = run_ceo_replay(diagnostic_options)
    eval_result = run_ceo_eval_suite(diagnostic_options)
    guardrail_result = run_ceo_guardrail_audit(diagnostic_options)
    preflight_result = run_ceo_preflight_gate(diagnostic_options, enforce_memory_delta=True)
    dispatch_result = run_ceo_dispatch_receipt(diagnostic_options)
    coherence_result = run_ceo_artifact_coherence(diagnostic_options)
    resumption_result = run_ceo_resumption_brief(
        diagnostic_options,
        preflight_result=preflight_result,
        coherence_result=coherence_result,
        mission_result=mission_result,
        strategy_result=strategy_result,
    )
    blocker_stack_result = run_ceo_blocker_stack(
        diagnostic_options,
        resumption_result=resumption_result,
        dispatch_result=dispatch_result,
    )
    incident_result = run_ceo_operating_incident_register(diagnostic_options)
    repair_result = run_ceo_repair_plan(
        diagnostic_options,
        blocker_result=blocker_stack_result,
        incident_result=incident_result,
    )
    action_board_result = run_ceo_action_board(
        diagnostic_options,
        resumption_result=resumption_result,
        repair_result=repair_result,
        dispatch_result=dispatch_result,
        kpi_result=kpi_result,
    )
    decision_quality_result = run_ceo_decision_quality(diagnostic_options, action_board_result=action_board_result)
    operator_brief_result = run_ceo_operator_brief(
        diagnostic_options,
        action_board_result=action_board_result,
        decision_quality_result=decision_quality_result,
    )
    coherence_result = run_ceo_artifact_coherence(diagnostic_options)
    final_decision_quality = _load_yaml_if_exists(root / "decision_quality.yaml") or decision_quality_result["decision_quality"]
    final_action_board = _load_yaml_if_exists(root / "action_board.yaml") or action_board_result["action_board"]
    final_operator_brief = _load_yaml_if_exists(root / "operator_brief.yaml") or operator_brief_result["operator_brief"]
    final_artifact_coherence = _load_yaml_if_exists(root / "artifact_coherence.yaml") or coherence_result["coherence"]
    final_artifact_coherence_issues = final_artifact_coherence.get("issues", []) or []
    final_artifact_coherence_top_issue = final_artifact_coherence_issues[0] if final_artifact_coherence_issues else {}
    final_effective_operator = _effective_operator_status(
        action_board=final_action_board,
        operator_brief=final_operator_brief,
        decision_quality=final_decision_quality,
    )
    repair_apply = _load_yaml_if_exists(root / "repair_apply.yaml")
    repair_apply_report = root / "repair_apply.md"
    role_result_validation = _load_yaml_if_exists(root / "role_result_validation.yaml")
    role_queue = role_result["queue"]
    approval_top_pending_item = (approval_result["queue"].get("pending_items", []) or [{}])[0]
    packet_path = latest_packet
    readiness = eval_result["eval_suite"].get("nine_nine_readiness", {}) or {}
    preflight_blockers = [
        str(item.get("blocker", ""))
        for item in preflight_result["preflight_gate"].get("blockers", []) or []
        if item.get("blocker")
    ]
    portfolio_allocator = _load_yaml_if_exists(root / "portfolio_allocator.yaml")
    portfolio_allocator_report = root / "portfolio_allocator.md"
    portfolio_selected = portfolio_allocator.get("selected_lane", {}) or {}
    final_flight_dashboard = flight_result["dashboard"]
    final_mission_score = mission_result["mission_score"]
    final_strategy_dashboard = strategy_result["dashboard"]
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
        f"- Trace grade: {trace_result['paths']['trace_grade_report']}",
        f"- Flight dashboard: {flight_result['paths']['dashboard_report']}",
        f"- Operating dashboard: {operating_result['paths']['dashboard_report']}",
        f"- Portfolio allocator: {portfolio_allocator_report}" if portfolio_allocator_report.exists() else "- Portfolio allocator: missing",
        f"- Mission score: {mission_result['paths']['mission_score_report']}",
        f"- Strategy capital dashboard: {strategy_result['paths']['strategy_capital_dashboard_report']}",
        f"- Decision quality: {decision_quality_result['paths']['decision_quality_report']}",
        f"- Replay: {replay_result['paths']['replay_report']}",
        f"- Eval suite: {eval_result['paths']['eval_suite_report']}",
        f"- Guardrail audit: {guardrail_result['paths']['guardrail_audit_report']}",
        f"- Preflight gate: {preflight_result['paths']['preflight_gate_report']}",
        f"- Dispatch receipt: {dispatch_result['paths']['dispatch_receipt_report']}",
        f"- Blocker stack: {blocker_stack_result['paths']['blocker_stack_report']}",
        f"- Operating incident register: {incident_result['paths']['incident_register_report']}",
        f"- Repair plan: {repair_result['paths']['repair_plan_report']}",
        f"- Repair apply: {repair_apply_report}" if repair_apply_report.exists() else "- Repair apply: missing",
        f"- Action board: {action_board_result['paths']['action_board_report']}",
        f"- Operator brief: {operator_brief_result['paths']['operator_brief_report']}",
        f"- Artifact coherence: {coherence_result['paths']['artifact_coherence_report']}",
        f"- Resumption brief: {resumption_result['paths']['resumption_brief_report']}",
        f"- Approval queue: {approval_result['paths']['queue_report']}",
        f"- Executive KPIs: {kpi_result['paths']['executive_kpis_report']}",
        f"- Role task queue: {role_result['paths']['role_task_queue_report']}",
        f"- Role result validation: {root / 'role_result_validation.yaml'}" if role_result_validation else "- Role result validation: missing",
        f"- Role dispatch: {role_dispatch_result['paths']['role_dispatch_report']}",
        f"- Org progress score: {org_progress_result['paths']['org_progress_score_report']}",
        f"- Capability backlog: {backlog_result['paths']['backlog_report']}",
        f"- Fresh/withheld validation contract: {contract_result['paths']['report']}",
        f"- Promotion proposal: {promotion_result['paths']['proposal_report']}",
        f"- Evidence debt register: {evidence_debt_result['paths']['register_report']}",
    ]
    if lab_report:
        lines.append(f"- Lab report: {lab_report}")
    lines.extend(
        [
            "",
            "## CEO Operating Snapshot",
            "",
            f"- Trace verdict: {trace_result['grade'].get('verdict')}",
            f"- Trace score: {trace_result['grade'].get('score')}",
            f"- Trace recommended next action: {trace_result['grade'].get('recommended_next_action')}",
            f"- Trace manual data import required: {_trace_grade_manual_data_import_required(trace_result['grade'])}",
            f"- Trace issues: {trace_result['grade'].get('issues') or []}",
            f"- Flight safe to continue: {final_flight_dashboard.get('safe_to_continue')}",
            f"- Flight safety scope: {final_flight_dashboard.get('safe_to_continue_scope') or CEO_FLIGHT_SAFETY_SCOPE}",
            f"- Flight dispatch authority: {final_flight_dashboard.get('dispatch_authority') or 'not_granted_by_flight_dashboard'}",
            f"- Flight runtime authority note: {final_flight_dashboard.get('runtime_authority_note') or CEO_RUNTIME_AUTHORITY_NOTE}",
            f"- Candidate portfolio: {operating_result['dashboard'].get('candidate_portfolio_count')}",
            f"- Portfolio selected lane: {portfolio_selected.get('lane_id') or 'none'}",
            f"- Portfolio attention action: {portfolio_selected.get('next_action') or 'none'}",
            f"- Portfolio action scope: {portfolio_allocator.get('action_scope') or 'portfolio_attention_only'}",
            f"- Portfolio dispatch authority: {portfolio_allocator.get('dispatch_authority') or 'not_granted_by_portfolio_allocator'}",
            f"- Mission score: {final_mission_score.get('overall_mission_score')}",
            f"- Lowest mission dimension: {final_mission_score.get('lowest_dimension')}",
            f"- Mission attention action: {final_mission_score.get('next_best_mission_action')}",
            f"- Mission action scope: {final_mission_score.get('action_scope') or 'mission_strategy_only'}",
            f"- Mission dispatch authority: {final_mission_score.get('dispatch_authority') or 'not_granted_by_mission_score'}",
            f"- Strategy capital bucket: {final_strategy_dashboard.get('selected_capital_bucket')}",
            f"- Strategy capital action: {final_strategy_dashboard.get('selected_strategy')}",
            f"- Strategy capital safety scope: {final_strategy_dashboard.get('safe_to_continue_scope') or CEO_STRATEGY_SAFETY_SCOPE}",
            f"- Strategy capital dispatch authority: {final_strategy_dashboard.get('dispatch_authority') or 'not_granted_by_strategy_capital_dashboard'}",
            f"- Runtime authority source: ceo status, approval queue, action board, resumption brief, preflight gate, and dispatch receipt",
            f"- Decision quality effective runtime action: {final_decision_quality.get('effective_runtime_action') or 'none'}",
            f"- Decision quality effective runtime command kind: {final_decision_quality.get('effective_runtime_command_kind') or 'none'}",
            f"- Decision quality effective runtime can execute now: {final_decision_quality.get('effective_runtime_can_execute_now')}",
            f"- Decision quality runtime blocked: {final_decision_quality.get('runtime_blocked')}",
            f"- Decision quality runtime block reason: {final_decision_quality.get('runtime_block_reason') or 'none'}",
            f"- Decision quality selected action: {final_decision_quality.get('selected_action')}",
            f"- Decision quality selected strategic route advisory: {final_decision_quality.get('selected_strategic_route_advisory') or 'none'}",
            f"- Decision quality confidence: {final_decision_quality.get('confidence')}",
            f"- Decision quality runner-up: {final_decision_quality.get('runner_up_action') or 'none'}",
            f"- Decision quality runtime authority: {final_decision_quality.get('runtime_authority_status')}",
            f"- Decision quality executable next action: {final_decision_quality.get('executable_next_action') or 'none'}",
            f"- Decision quality executable command kind: {final_decision_quality.get('executable_next_command_kind') or 'none'}",
            f"- Decision quality runtime authorized strategic route: {final_decision_quality.get('runtime_authorized_strategic_route') or 'none'}",
            f"- Decision quality can execute now: {final_decision_quality.get('executable_can_execute_now')}",
            f"- Decision quality selected action executable now: {final_decision_quality.get('selected_action_is_executable_now')}",
            f"- Decision quality selected action blocked by: {final_decision_quality.get('selected_action_blocked_by') or 'none'}",
            f"- Replay status: {replay_result['replay'].get('status')}",
            f"- Eval suite status: {eval_result['eval_suite'].get('status')}",
            f"- Eval suite score: {eval_result['eval_suite'].get('score')}",
            f"- 9.9 readiness: {readiness.get('status')}",
            f"- Advisory readiness gaps: {readiness.get('advisory_case_ids') or []}",
            f"- Guardrail audit status: {guardrail_result['guardrail_audit'].get('status')}",
            f"- Preflight status: {preflight_result['preflight_gate'].get('status')}",
            f"- Preflight blockers: {preflight_blockers or []}",
            f"- Dispatch receipt status: {dispatch_result['receipt'].get('status')}",
            f"- Dispatch safe to dispatch: {dispatch_result['receipt'].get('safe_to_dispatch')}",
            f"- Blocker stack status: {blocker_stack_result['stack'].get('status')}",
            f"- Top blocker: {blocker_stack_result['stack'].get('top_blocker') or 'none'}",
            f"- Operating incidents: {incident_result['register'].get('incident_count')}",
            f"- Repair plan status: {repair_result['repair_plan'].get('status')}",
            f"- Runnable repairs: {repair_result['repair_plan'].get('runnable_repair_count', repair_result['repair_plan'].get('autonomous_repair_count'))}",
            f"- Diagnostic refreshes: {repair_result['repair_plan'].get('diagnostic_refresh_count', 0)}",
            f"- Top repair: {repair_result['repair_plan'].get('top_repair') or 'none'}",
            f"- Top repair kind: {repair_result['repair_plan'].get('top_repair_kind') or 'none'}",
            f"- Repair next command: {repair_result['repair_plan'].get('next_command')}",
            f"- Repair apply status: {repair_apply.get('status', 'missing_repair_apply')}",
            f"- Repair apply key: {repair_apply.get('repair_key', '') or 'none'}",
            f"- Repair apply executed: {repair_apply.get('action_executed', '')}",
            f"- Repair apply closed: {repair_apply.get('repair_closed', '')}",
            f"- Effective operator status: {final_effective_operator.get('effective_operator_status')}",
            f"- Manual gate active: {final_effective_operator.get('manual_gate_active')}",
            f"- Effective operator runtime blocked: {final_effective_operator.get('runtime_blocked')}",
            f"- Effective operator runtime block reason: {final_effective_operator.get('runtime_block_reason') or 'none'}",
            f"- Action board status: {final_action_board.get('status')}",
            f"- Action board primary action: {(final_action_board.get('primary_action', {}) or {}).get('action_id') or 'none'}",
            f"- Action board primary kind: {(final_action_board.get('primary_action', {}) or {}).get('command_kind') or 'none'}",
            f"- Action board command: {(final_action_board.get('primary_action', {}) or {}).get('command') or 'none'}",
            f"- Operator brief status: {final_operator_brief.get('status')}",
            f"- Operator brief summary: {final_operator_brief.get('plain_english_summary')}",
            f"- Artifact coherence status: {final_artifact_coherence.get('status')}",
            f"- Artifact coherence top issue: {final_artifact_coherence_top_issue.get('artifact') or 'none'}",
            f"- Artifact coherence top issue severity: {final_artifact_coherence_top_issue.get('severity', 'unknown') if final_artifact_coherence_top_issue else 'none'}",
            f"- Artifact coherence top issue types: {final_artifact_coherence_top_issue.get('issues', []) if final_artifact_coherence_top_issue else []}",
            f"- Artifact coherence issues: {final_artifact_coherence.get('issues') or []}",
            f"- Resumption status: {resumption_result['brief'].get('resume_status')}",
            f"- Resumption next command: {resumption_result['brief'].get('next_command')}",
            f"- Pending approvals: {approval_result['queue'].get('pending_count')}",
            f"- Approval top pending id: {approval_result['queue'].get('top_pending_approval_id') or 'none'}",
            f"- Approval top pending kind: {approval_top_pending_item.get('kind') or 'none'}",
            f"- Approval top pending reason: {approval_top_pending_item.get('reason') or 'none'}",
            f"- Approval top pending source: {approval_top_pending_item.get('source_artifact') or 'none'}",
            f"- Approval top pending required user decision: {approval_top_pending_item.get('required_user_decision') or 'none'}",
            f"- Approval top pending authority: {approval_top_pending_item.get('approval_authority', approval_top_pending_item.get('authority', '')) or 'none'}",
            f"- Approval top pending fingerprint: {approval_top_pending_item.get('approval_item_fingerprint') or 'none'}",
            f"- Executive KPI status: {kpi_result['kpis'].get('status')}",
            f"- Role queue status: {role_queue.get('status')}",
            f"- Role tasks: {role_queue.get('task_count')}",
            f"- Role pending: {role_queue.get('pending_task_count')}",
            f"- Role pending manual: {role_queue.get('pending_manual_task_count')}",
            f"- Role pending autonomous: {role_queue.get('pending_autonomous_task_count')}",
            f"- Role completed: {role_queue.get('completed_task_count')}",
            f"- Role blocked: {role_queue.get('blocked_task_count')}",
            f"- Role top pending task: {role_queue.get('top_pending_task_id') or 'none'}",
            f"- Role top pending role: {role_queue.get('top_pending_role_id') or 'none'}",
            f"- Role top pending packet: {role_queue.get('top_pending_packet_path') or 'none'}",
            f"- Role top pending result mode: {role_queue.get('top_pending_result_resolution_mode') or 'none'}",
            f"- Role top pending closure command: {role_queue.get('top_pending_closure_command') or 'none'}",
            f"- Role top autonomous pending task: {role_queue.get('top_autonomous_pending_task_id') or 'none'}",
            f"- Role top autonomous result command: {role_queue.get('top_autonomous_next_role_result_command') or 'none'}",
            f"- Role top blocked task: {role_queue.get('top_blocked_task_id') or 'none'}",
            f"- Role top blocked role: {role_queue.get('top_blocked_role_id') or 'none'}",
            f"- Role top blocked packet: {role_queue.get('top_blocked_packet_path') or 'none'}",
            f"- Role top blocked result mode: {role_queue.get('top_blocked_result_resolution_mode') or 'none'}",
            f"- Role top blocked validation: {role_queue.get('top_blocked_validation_status') or 'none'}",
            f"- Role top blocked closure command: {_ceo_role_queue_top_blocked_closure_command(ceo_run_id=ceo_run_id, role_queue=role_queue) or 'none'}",
            f"- Role top blocked review status: {role_queue.get('top_blocked_review_status') or 'none'}",
            f"- Role top blocked result path: {role_queue.get('top_blocked_result_path') or 'none'}",
            f"- Role top blocked next action: {role_queue.get('top_blocked_next_action') or 'none'}",
            f"- Role top blocked finding: {role_queue.get('top_blocked_finding') or 'none'}",
            f"- Role result validation status: {role_result_validation.get('status', 'missing_role_result_validation')}",
            f"- Role result validation issues: {role_result_validation.get('issues', []) if role_result_validation else []}",
            f"- Role dispatch packets: {role_dispatch_result['role_dispatch'].get('packet_count')}",
            f"- Org progress status: {org_progress_result['org_progress_score'].get('status')}",
            f"- Org progress score: {org_progress_result['org_progress_score'].get('org_progress_score')}",
            f"- Org fake-progress flags: {org_progress_result['org_progress_score'].get('fake_progress_flags') or []}",
            f"- Org completed without merge: {org_progress_result['org_progress_score'].get('completed_without_merge_count')}",
            f"- Org decision deltas: {org_progress_result['org_progress_score'].get('decision_delta_count')}",
            f"- Capability backlog items: {backlog_result['backlog'].get('backlog_count')}",
            f"- Fresh/withheld contract status: {contract_result['contract'].get('status')}",
            f"- Promotion proposal status: {promotion_result['proposal'].get('status')}",
            f"- Evidence debt: {evidence_debt_result['register'].get('status')} "
            f"({evidence_debt_result['register'].get('debt_count')} items)",
            f"- Next evidence debt action: {evidence_debt_result['register'].get('next_action')}",
            "",
            packet_path.read_text(encoding="utf-8") if packet_path.exists() else "",
        ]
    )
    report_path = root / "final_ceo_report.md"
    atomic_write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "paths": {
            "report": report_path,
            "trace_grade_report": trace_result["paths"]["trace_grade_report"],
            "flight_dashboard_report": flight_result["paths"]["dashboard_report"],
            "operating_dashboard_report": operating_result["paths"]["dashboard_report"],
            "mission_score_report": mission_result["paths"]["mission_score_report"],
            "strategy_capital_dashboard_report": strategy_result["paths"]["strategy_capital_dashboard_report"],
            "decision_quality_report": decision_quality_result["paths"]["decision_quality_report"],
            "replay_report": replay_result["paths"]["replay_report"],
            "eval_suite_report": eval_result["paths"]["eval_suite_report"],
            "guardrail_audit_report": guardrail_result["paths"]["guardrail_audit_report"],
            "preflight_gate_report": preflight_result["paths"]["preflight_gate_report"],
            "dispatch_receipt_report": dispatch_result["paths"]["dispatch_receipt_report"],
            "blocker_stack_report": blocker_stack_result["paths"]["blocker_stack_report"],
            "incident_register_report": incident_result["paths"]["incident_register_report"],
            "repair_plan_report": repair_result["paths"]["repair_plan_report"],
            **({"repair_apply_report": repair_apply_report} if repair_apply_report.exists() else {}),
            "action_board_report": action_board_result["paths"]["action_board_report"],
            "operator_brief_report": operator_brief_result["paths"]["operator_brief_report"],
            "artifact_coherence_report": coherence_result["paths"]["artifact_coherence_report"],
            "resumption_brief_report": resumption_result["paths"]["resumption_brief_report"],
            "approval_queue_report": approval_result["paths"]["queue_report"],
            "executive_kpis_report": kpi_result["paths"]["executive_kpis_report"],
            "role_task_queue_report": role_result["paths"]["role_task_queue_report"],
            **({"role_result_validation": root / "role_result_validation.yaml"} if role_result_validation else {}),
            "role_dispatch_report": role_dispatch_result["paths"]["role_dispatch_report"],
            "org_progress_score_report": org_progress_result["paths"]["org_progress_score_report"],
            "capability_backlog_report": backlog_result["paths"]["backlog_report"],
            "fresh_withheld_validation_contract_report": contract_result["paths"]["report"],
            "promotion_proposal_report": promotion_result["paths"]["proposal_report"],
            "evidence_debt_register_report": evidence_debt_result["paths"]["register_report"],
            **review["paths"],
        },
    }


def render_ceo_trace_grade_report(grade: dict[str, Any]) -> str:
    lines = [
        "# Riskflow CEO Trace Grade",
        "",
        f"Run: {grade.get('run_id')}",
        f"Lab run: {grade.get('lab_run_id')}",
        f"Generated: {grade.get('generated_at')}",
        "",
        "## Grade",
        "",
        f"- Score: {grade.get('score')}",
        f"- Verdict: {grade.get('verdict')}",
        f"- Latest decision: {grade.get('latest_decision')}",
        f"- Latest action: {grade.get('latest_action')}",
        f"- Latest status: {grade.get('latest_status')}",
        f"- Recommended next action: {grade.get('recommended_next_action')}",
        f"- Manual data import required: {_trace_grade_manual_data_import_required(grade)}",
        f"- Trace scope: {grade.get('trace_scope')}",
        f"- Product evidence status: {grade.get('product_evidence_status')}",
        f"- Product language allowed: {grade.get('product_language_allowed')}",
        f"- Production effect: {grade.get('production_effect')}",
        "",
        "## Issues",
        "",
    ]
    issues = grade.get("issues", []) or []
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- none")
    lines.extend(["", "## Criteria", ""])
    criteria = grade.get("criteria", {}) or {}
    for key in sorted(criteria):
        lines.append(f"- {key}: {criteria[key]}")
    failure = grade.get("failure_avoidance", {}) or {}
    prior = failure.get("prior_failure", {}) or {}
    lines.extend(
        [
            "",
            "## Failure Avoidance",
            "",
            f"- Status: {failure.get('status')}",
            f"- Repeated prior failure: {failure.get('repeated_prior_failure')}",
            f"- Current is failure: {failure.get('current_is_failure')}",
            f"- Prior failure: {prior or 'none'}",
            "",
            "## Loop Meltdown",
            "",
        ]
    )
    meltdown = grade.get("loop_meltdown", {}) or {}
    lines.extend(
        [
            f"- Severity: {meltdown.get('severity')}",
            f"- Strategy change required: {meltdown.get('strategy_change_required')}",
            f"- Decision repeats: {meltdown.get('decision_repeat_count')}",
            f"- Fingerprint repeats: {meltdown.get('fingerprint_repeat_count')}",
            f"- No-progress count: {meltdown.get('no_progress_count')}",
            f"- Manual gate count: {meltdown.get('manual_gate_count')}",
            f"- Capability builder count: {meltdown.get('capability_builder_count')}",
            f"- Recommended intervention: {meltdown.get('recommended_intervention')}",
            "",
            "## Evidence Provenance",
            "",
        ]
    )
    provenance = grade.get("evidence_provenance", {}) or {}
    lines.extend(
        [
            f"- Command: {provenance.get('command_executed') or 'none'}",
            f"- Inputs: {provenance.get('input_artifacts') or {}}",
            f"- Outputs: {provenance.get('output_artifacts') or {}}",
        ]
    )
    unsupported = grade.get("unsupported_next_actions", []) or []
    if unsupported:
        lines.extend(["", "## Unsupported Next Actions", ""])
        lines.extend(f"- {item}" for item in unsupported)
    manual = grade.get("manual_next_actions", []) or []
    bounded = grade.get("bounded_executor_next_actions", []) or []
    capability = grade.get("capability_builder_next_actions", []) or []
    if manual or bounded or capability:
        lines.extend(["", "## Next Action Route Types", ""])
        lines.append(f"- Bounded executors: {bounded or 'none'}")
        lines.append(f"- Manual gates: {manual or 'none'}")
        lines.append(f"- Capability builders: {capability or 'none'}")
    return "\n".join(lines).rstrip() + "\n"


def run_ceo_trace_grade(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    action_result = _load_yaml_if_exists(root / "binding_action_result.yaml")
    self_audit = _load_yaml_if_exists(root / "ceo_self_audit.yaml")
    heartbeat_status = _load_yaml_if_exists(root / "heartbeat_status.yaml")
    company_status = _load_yaml_if_exists(root / "company_status.yaml")
    if not heartbeat_status:
        heartbeat_status = run_ceo_heartbeat_status(options)["status"]
    if not company_status:
        company_status = build_company_status(options, ceo_run_id, lab_run_id)
        root.mkdir(parents=True, exist_ok=True)
        atomic_write_yaml(root / "company_status.yaml", company_status)
    grade = build_ceo_trace_grade(
        ceo_run_id=ceo_run_id,
        lab_run_id=lab_run_id,
        root=root,
        ledger_entries=_read_action_ledger(options, ceo_run_id),
        action_result=action_result,
        self_audit=self_audit,
        heartbeat_status=heartbeat_status,
        company_status=company_status,
    )
    grade_path = root / "trace_grade.yaml"
    report_path = root / "trace_grade.md"
    atomic_write_yaml(grade_path, grade)
    atomic_write_text(report_path, render_ceo_trace_grade_report(grade))
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "grade": grade,
        "paths": {"trace_grade": grade_path, "trace_grade_report": report_path},
    }


def run_ceo_heartbeat_status(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    path = ceo_heartbeat_status_path(options, ceo_run_id)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    block_number = max(0, _next_block_number(options, ceo_run_id) - 1)
    payload = build_heartbeat_status(
        options,
        ceo_run_id,
        lab_run_id,
        block_number=block_number,
        company_status=company_status,
        decision=decision,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_yaml(path, payload)
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "status": payload,
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
