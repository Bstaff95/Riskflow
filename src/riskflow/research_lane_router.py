from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .lab_director import utc_now_iso
from .lab_loop import atomic_write_yaml, load_yaml_file
from .meta_research import classify_product_categories


LANE_ASSIGNMENT_MODEL = "riskflow_research_lane_assignment_v0"

RESEARCH_LANES = {
    "bullish_permission",
    "warning_blocker",
    "invalidation",
    "reset_quality",
    "gradient_interpretation",
    "path_management",
    "cross_asset_regime",
    "archive",
}


def _text_for_belief(belief: dict[str, Any]) -> str:
    values = [
        belief.get("claim_id", ""),
        belief.get("plain_english_claim", ""),
        belief.get("claim_kind", ""),
        belief.get("setup_class", ""),
        " ".join(str(item) for item in belief.get("suspected_drivers", []) or []),
        " ".join(str(item) for item in belief.get("known_failure_modes", []) or []),
    ]
    return " ".join(str(value) for value in values).lower()


def _blocker_decision_for(belief_id: str, blocker_audit: dict[str, Any] | None) -> str:
    if not blocker_audit:
        return ""
    for item in blocker_audit.get("items", []) or []:
        if str(item.get("belief_id") or item.get("blocker_id")) == belief_id:
            return str(item.get("audit_decision", ""))
    return ""


def choose_lane(belief: dict[str, Any], blocker_audit: dict[str, Any] | None = None) -> str:
    belief_id = str(belief.get("claim_id", ""))
    text = _text_for_belief(belief)
    categories = set(classify_product_categories(belief))
    blocker_decision = _blocker_decision_for(belief_id, blocker_audit)
    status = str(belief.get("status", ""))
    level = str(belief.get("evidence_level", ""))

    if status in {"archived", "rejected"} or level == "rejected":
        if blocker_decision in {"valid_blocker", "permission_filter_only", "needs_more_controls"}:
            return "warning_blocker"
        return "archive"
    if blocker_decision in {"valid_blocker", "permission_filter_only", "needs_more_controls"}:
        return "warning_blocker"
    if "invalidation" in text or "failed reclaim" in text or "reject" in text:
        return "invalidation"
    if "gradient_interpretation" in categories or any(token in text for token in ("gradient", "color", "acceleration", "curvature")):
        return "gradient_interpretation"
    if "reset_quality" in categories:
        return "reset_quality"
    if "path_management" in categories or any(token in text for token in ("entry", "lag", "cooldown", "mfe", "mae", "drawdown")):
        return "path_management"
    if "cross_asset_usefulness" in categories:
        return "cross_asset_regime"
    if "permission" in categories:
        return "bullish_permission"
    if "blocker" in categories:
        return "warning_blocker"
    return "bullish_permission"


def _next_action_for_lane(lane: str, belief: dict[str, Any], blocker_decision: str) -> str:
    level = str(belief.get("evidence_level", ""))
    if lane == "archive":
        return "record_do_not_repeat"
    if lane == "warning_blocker":
        if blocker_decision == "valid_blocker":
            return "validate_blocker_cost"
        return "run_blocker_controls"
    if lane == "gradient_interpretation":
        if level in {"L3_attributed", "L4_validated"}:
            return "run_incremental_gradient_controls"
        return "hold_for_attribution"
    if lane == "reset_quality":
        return "decompose_reset_driver" if level == "L2_discovered" else "validate_reset_rule"
    if lane == "path_management":
        return "test_lag_cooldown_mfe_mae"
    if lane == "invalidation":
        return "test_invalidation_timing"
    if lane == "cross_asset_regime":
        return "test_symbol_cluster_timeframe_transfer"
    if level == "L3_attributed":
        return "validate_frozen_permission_rule"
    if level == "L2_discovered":
        return "decompose_permission_drivers"
    return "broaden_or_archive"


def _lane_blocked(lane: str, belief: dict[str, Any], next_action: str) -> bool:
    if lane == "archive":
        return True
    if next_action in {"hold_for_attribution"}:
        return False
    if str(belief.get("evidence_level", "")) == "rejected":
        return True
    return False


def build_lane_assignment(
    belief_graph: dict[str, Any],
    *,
    blocker_audit: dict[str, Any] | None = None,
    meta_scorecard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assignments: list[dict[str, Any]] = []
    for belief in belief_graph.get("beliefs", []) or []:
        belief_id = str(belief.get("claim_id", ""))
        blocker_decision = _blocker_decision_for(belief_id, blocker_audit)
        lane = choose_lane(belief, blocker_audit)
        next_action = _next_action_for_lane(lane, belief, blocker_decision)
        assignments.append(
            {
                "belief_id": belief_id,
                "lane": lane,
                "next_action": next_action,
                "blocked": _lane_blocked(lane, belief, next_action),
                "evidence_level": belief.get("evidence_level"),
                "confidence_score": belief.get("confidence_score"),
                "blocker_audit_decision": blocker_decision,
                "product_categories": classify_product_categories(belief),
                "stop_condition": _stop_condition_for_lane(lane, next_action),
            }
        )

    counts = Counter(str(item["lane"]) for item in assignments)
    open_lanes = sorted({item["lane"] for item in assignments if not item["blocked"] and item["lane"] != "archive"})
    return {
        "model": LANE_ASSIGNMENT_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": belief_graph.get("session_id", "ad_hoc"),
        "assignment_count": len(assignments),
        "lane_counts": dict(sorted(counts.items())),
        "open_lanes": open_lanes,
        "all_lanes_blocked": not open_lanes and bool(assignments),
        "meta_process_score": (meta_scorecard or {}).get("overall_process_score"),
        "assignments": assignments,
        "production_effect": "none",
    }


def _stop_condition_for_lane(lane: str, next_action: str) -> str:
    if lane == "archive":
        return "archived_or_rejected"
    if next_action == "run_blocker_controls":
        return "blocked_until_blocker_controls_exist"
    if next_action == "hold_for_attribution":
        return "blocked_until_attribution_evidence_exists"
    return "continue_until_validation_or_archive"


def has_open_research_lanes(assignment: dict[str, Any]) -> bool:
    return bool(assignment.get("open_lanes"))


def write_lane_assignment(assignment: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "lane_assignment.yaml"
    atomic_write_yaml(path, assignment)
    return path


def run_lane_assignment(
    *,
    belief_graph_path: Path,
    output_dir: Path,
    blocker_audit_path: Path | None = None,
    meta_scorecard_path: Path | None = None,
) -> dict[str, Any]:
    belief_graph = load_yaml_file(belief_graph_path)
    blocker_audit = load_yaml_file(blocker_audit_path) if blocker_audit_path and blocker_audit_path.exists() else None
    meta_scorecard = load_yaml_file(meta_scorecard_path) if meta_scorecard_path and meta_scorecard_path.exists() else None
    assignment = build_lane_assignment(belief_graph, blocker_audit=blocker_audit, meta_scorecard=meta_scorecard)
    path = write_lane_assignment(assignment, output_dir)
    return {"assignment": assignment, "paths": {"assignment": path}}
