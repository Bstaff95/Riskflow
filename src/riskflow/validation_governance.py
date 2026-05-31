from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .lab_director import utc_now_iso
from .lab_loop import atomic_write_yaml, load_yaml_file


VALIDATION_GOVERNANCE_MODEL = "riskflow_validation_governance_v0"

GATES = (
    "G0_idea",
    "G1_measurable",
    "G2_discovered",
    "G3_attributed",
    "G4_validated",
    "G5_product_candidate",
    "G6_sidecar_ready",
    "G7_indicator_change_candidate",
)

DECISIONS = {
    "promote",
    "hold_for_validation",
    "hold_for_blocker_audit",
    "hold_for_visual_review",
    "demote",
    "archive",
    "reject_product_translation",
}


def _assignment_for(belief_id: str, lane_assignment: dict[str, Any] | None) -> dict[str, Any]:
    if not lane_assignment:
        return {}
    for item in lane_assignment.get("assignments", []) or []:
        if str(item.get("belief_id", "")) == belief_id:
            return item
    return {}


def _blocker_item_for(belief_id: str, blocker_audit: dict[str, Any] | None) -> dict[str, Any]:
    if not blocker_audit:
        return {}
    for item in blocker_audit.get("items", []) or []:
        if str(item.get("belief_id") or item.get("blocker_id")) == belief_id:
            return item
    return {}


def _base_gate(belief: dict[str, Any]) -> str:
    level = str(belief.get("evidence_level", ""))
    status = str(belief.get("status", ""))
    best = belief.get("best_trial", {}) or {}
    blockers = set(str(item) for item in belief.get("promotion_blockers", []) or [])
    if status in {"archived", "rejected"} or level == "rejected":
        return "G1_measurable"
    if level == "L1_seen":
        return "G1_measurable"
    if level == "L2_discovered":
        return "G2_discovered"
    if level == "L3_attributed":
        if best.get("contract_tier") == "strict_validated" and not blockers:
            return "G4_validated"
        return "G3_attributed"
    if level == "L4_validated":
        return "G4_validated"
    return "G0_idea"


def _gate_index(gate: str) -> int:
    try:
        return GATES.index(gate)
    except ValueError:
        return 0


def review_belief(
    belief: dict[str, Any],
    *,
    lane_assignment: dict[str, Any] | None = None,
    blocker_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    belief_id = str(belief.get("claim_id", ""))
    assignment = _assignment_for(belief_id, lane_assignment)
    blocker_item = _blocker_item_for(belief_id, blocker_audit)
    lane = str(assignment.get("lane", "archive" if belief.get("status") in {"archived", "rejected"} else "bullish_permission"))
    gate = _base_gate(belief)
    blockers: list[str] = []

    if lane == "warning_blocker" and blocker_item.get("audit_decision") != "valid_blocker":
        decision = "hold_for_blocker_audit"
        blockers.append("blocker_audit_not_valid")
    elif lane == "gradient_interpretation" and _gate_index(gate) < _gate_index("G4_validated"):
        decision = "hold_for_validation"
        blockers.append("gradient_candidate_needs_incremental_validation")
    elif lane == "gradient_interpretation":
        decision = "hold_for_visual_review"
        blockers.append("gradient_candidate_needs_visual_readability_review")
    elif belief.get("status") in {"archived", "rejected"} or str(belief.get("evidence_level", "")) == "rejected":
        decision = "archive"
    elif _gate_index(gate) < _gate_index("G4_validated"):
        decision = "hold_for_validation"
        blockers.append("fresh_or_frozen_validation_required")
    elif lane in {"archive"}:
        decision = "archive"
    else:
        decision = "hold_for_validation"
        blockers.append("product_translation_requires_explicit_user_approval")

    if decision == "hold_for_validation" and "cluster_concentrated" in set(belief.get("promotion_blockers", []) or []):
        blockers.append("cluster_concentration_must_clear")
    if decision == "promote":
        blockers.append("manual_approval_required_before_product_change")

    return {
        "belief_id": belief_id,
        "lane": lane,
        "current_gate": gate,
        "decision": decision,
        "blockers": sorted(set(blockers)),
        "evidence_level": belief.get("evidence_level"),
        "confidence_score": belief.get("confidence_score"),
        "production_effect": "none",
    }


def build_validation_governance(
    belief_graph: dict[str, Any],
    *,
    lane_assignment: dict[str, Any] | None = None,
    blocker_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decisions = [
        review_belief(belief, lane_assignment=lane_assignment, blocker_audit=blocker_audit)
        for belief in belief_graph.get("beliefs", []) or []
    ]
    decision_counts = Counter(str(item["decision"]) for item in decisions)
    gate_counts = Counter(str(item["current_gate"]) for item in decisions)
    return {
        "model": VALIDATION_GOVERNANCE_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": belief_graph.get("session_id", "ad_hoc"),
        "decision_counts": dict(sorted(decision_counts.items())),
        "gate_counts": dict(sorted(gate_counts.items())),
        "product_change_allowed": False,
        "decisions": decisions,
        "production_effect": "none",
    }


def write_validation_governance(governance: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "validation_decision.yaml"
    atomic_write_yaml(path, governance)
    return path


def run_validation_governance(
    *,
    belief_graph_path: Path,
    output_dir: Path,
    lane_assignment_path: Path | None = None,
    blocker_audit_path: Path | None = None,
) -> dict[str, Any]:
    belief_graph = load_yaml_file(belief_graph_path)
    lane_assignment = load_yaml_file(lane_assignment_path) if lane_assignment_path and lane_assignment_path.exists() else None
    blocker_audit = load_yaml_file(blocker_audit_path) if blocker_audit_path and blocker_audit_path.exists() else None
    governance = build_validation_governance(
        belief_graph,
        lane_assignment=lane_assignment,
        blocker_audit=blocker_audit,
    )
    path = write_validation_governance(governance, output_dir)
    return {"governance": governance, "paths": {"governance": path}}
