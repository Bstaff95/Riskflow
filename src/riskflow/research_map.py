from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .lab_director import utc_now_iso
from .lab_loop import atomic_write_yaml, load_yaml_file


RESEARCH_MAP_MODEL = "riskflow_research_map_v0"
DEFAULT_RESEARCH_MAP_PATH = Path("research/riskflow_map/research_map.yaml")
DEFAULT_RESEARCH_MAP_REPORT_ROOT = Path("reports/riskflow_map")


def _assignment_for(belief_id: str, lane_assignment: dict[str, Any] | None) -> dict[str, Any]:
    if not lane_assignment:
        return {}
    for item in lane_assignment.get("assignments", []) or []:
        if str(item.get("belief_id", "")) == belief_id:
            return item
    return {}


def _validation_for(belief_id: str, validation_governance: dict[str, Any] | None) -> dict[str, Any]:
    if not validation_governance:
        return {}
    for item in validation_governance.get("decisions", []) or []:
        if str(item.get("belief_id", "")) == belief_id:
            return item
    return {}


def _blocker_for(belief_id: str, blocker_audit: dict[str, Any] | None) -> dict[str, Any]:
    if not blocker_audit:
        return {}
    for item in blocker_audit.get("items", []) or []:
        if str(item.get("belief_id") or item.get("blocker_id")) == belief_id:
            return item
    return {}


def _node_status(belief: dict[str, Any], validation: dict[str, Any]) -> str:
    if belief.get("status") in {"archived", "rejected"} or belief.get("evidence_level") == "rejected":
        return "archived"
    gate = str(validation.get("current_gate", ""))
    if gate == "G4_validated":
        return "validated_candidate"
    if belief.get("evidence_level") == "L3_attributed":
        return "attributed"
    if belief.get("evidence_level") == "L2_discovered":
        return "discovery_survivor"
    if belief.get("evidence_level") == "L1_seen":
        return "encoded"
    return "idea"


def build_research_map(
    mart: dict[str, Any],
    belief_graph: dict[str, Any],
    *,
    lane_assignment: dict[str, Any] | None = None,
    blocker_audit: dict[str, Any] | None = None,
    validation_governance: dict[str, Any] | None = None,
    prior_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prior_nodes = {str(node.get("id", "")): node for node in (prior_map or {}).get("nodes", []) or []}
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    do_not_repeat: set[str] = set()

    for belief in belief_graph.get("beliefs", []) or []:
        belief_id = str(belief.get("claim_id", ""))
        assignment = _assignment_for(belief_id, lane_assignment)
        validation = _validation_for(belief_id, validation_governance)
        blocker = _blocker_for(belief_id, blocker_audit)
        prior = prior_nodes.get(belief_id, {})
        node = {
            "id": belief_id,
            "type": "belief",
            "status": _node_status(belief, validation),
            "lane": assignment.get("lane", prior.get("lane", "")),
            "evidence_level": belief.get("evidence_level"),
            "confidence_score": belief.get("confidence_score"),
            "setup_class": belief.get("setup_class"),
            "timeframes": belief.get("timeframes", []),
            "root_ids": belief.get("root_ids", []),
            "next_action": assignment.get("next_action", ""),
            "validation_decision": validation.get("decision", ""),
            "blocker_decision": blocker.get("audit_decision", ""),
            "product_translation_status": belief.get("product_translation_status", "not_eligible"),
            "last_seen_session": belief_graph.get("session_id", mart.get("session_id", "ad_hoc")),
        }
        nodes.append(node)

        for trial_id in belief.get("supporting_trials", []) or []:
            edges.append({"from": str(trial_id), "to": belief_id, "type": "supports"})
        for trial_id in belief.get("contradicting_trials", []) or []:
            edges.append({"from": str(trial_id), "to": belief_id, "type": "contradicts"})
        for root_id in belief.get("root_ids", []) or []:
            edges.append({"from": str(root_id), "to": belief_id, "type": "depends_on"})
        for root_id in belief.get("do_not_repeat", []) or []:
            do_not_repeat.add(str(root_id))
            edges.append({"from": belief_id, "to": str(root_id), "type": "do_not_repeat"})
        if validation.get("decision") in {"hold_for_validation", "hold_for_blocker_audit", "hold_for_visual_review"}:
            edges.append({"from": belief_id, "to": validation["decision"], "type": "blocked_by"})
        if blocker.get("audit_decision") == "valid_blocker":
            edges.append({"from": belief_id, "to": "warning_blocker", "type": "translates_to"})

    for prior_id, prior in prior_nodes.items():
        if prior_id not in {str(node.get("id", "")) for node in nodes}:
            stale = dict(prior)
            stale["status"] = "stale"
            nodes.append(stale)

    lane_counts = Counter(str(node.get("lane", "") or "unassigned") for node in nodes)
    status_counts = Counter(str(node.get("status", "") or "unknown") for node in nodes)
    validation_debt = [
        node["id"]
        for node in nodes
        if node.get("status") in {"discovery_survivor", "attributed"}
        and node.get("validation_decision") in {"hold_for_validation", ""}
    ]
    product_candidates = [
        node["id"]
        for node in nodes
        if node.get("status") == "validated_candidate" and node.get("validation_decision") != "archive"
    ]
    saturated_families = sorted(do_not_repeat)
    open_questions = [
        {
            "belief_id": node["id"],
            "lane": node.get("lane"),
            "next_action": node.get("next_action") or "needs_director_plan",
        }
        for node in nodes
        if node.get("status") not in {"archived", "stale"} and node.get("next_action") not in {"", "record_do_not_repeat"}
    ][:20]

    return {
        "model": RESEARCH_MAP_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": belief_graph.get("session_id", mart.get("session_id", "ad_hoc")),
        "nodes": nodes,
        "edges": edges,
        "views": {
            "lane_counts": dict(sorted(lane_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "top_open_questions": open_questions,
            "saturated_families": saturated_families[:50],
            "product_ready_candidates": product_candidates,
            "validation_debt": validation_debt[:50],
            "stale_evidence_needing_fresh_data": [
                item["belief_id"]
                for item in (lane_assignment or {}).get("assignments", []) or []
                if item.get("stop_condition") in {"blocked_until_attribution_evidence_exists", "blocked_until_blocker_controls_exist"}
            ],
        },
        "production_effect": "none",
    }


def write_research_map(research_map: dict[str, Any], map_path: Path = DEFAULT_RESEARCH_MAP_PATH) -> Path:
    atomic_write_yaml(map_path, research_map)
    return map_path


def write_research_map_status(
    research_map: dict[str, Any],
    report_root: Path = DEFAULT_RESEARCH_MAP_REPORT_ROOT,
) -> Path:
    status = {
        "model": "riskflow_research_map_status_v0",
        "generated_at": utc_now_iso(),
        "session_id": research_map.get("session_id", "ad_hoc"),
        "node_count": len(research_map.get("nodes", []) or []),
        "edge_count": len(research_map.get("edges", []) or []),
        "views": research_map.get("views", {}),
        "production_effect": "none",
    }
    path = report_root / "latest_map_status.yaml"
    atomic_write_yaml(path, status)
    return path


def run_research_map_update(
    *,
    evidence_mart_path: Path,
    belief_graph_path: Path,
    map_path: Path = DEFAULT_RESEARCH_MAP_PATH,
    report_root: Path = DEFAULT_RESEARCH_MAP_REPORT_ROOT,
    lane_assignment_path: Path | None = None,
    blocker_audit_path: Path | None = None,
    validation_governance_path: Path | None = None,
) -> dict[str, Any]:
    mart = load_yaml_file(evidence_mart_path)
    belief_graph = load_yaml_file(belief_graph_path)
    lane_assignment = load_yaml_file(lane_assignment_path) if lane_assignment_path and lane_assignment_path.exists() else None
    blocker_audit = load_yaml_file(blocker_audit_path) if blocker_audit_path and blocker_audit_path.exists() else None
    validation_governance = (
        load_yaml_file(validation_governance_path) if validation_governance_path and validation_governance_path.exists() else None
    )
    prior_map = load_yaml_file(map_path) if map_path.exists() else None
    research_map = build_research_map(
        mart,
        belief_graph,
        lane_assignment=lane_assignment,
        blocker_audit=blocker_audit,
        validation_governance=validation_governance,
        prior_map=prior_map,
    )
    written_map = write_research_map(research_map, map_path)
    status_path = write_research_map_status(research_map, report_root)
    return {"research_map": research_map, "paths": {"map": written_map, "status": status_path}}
