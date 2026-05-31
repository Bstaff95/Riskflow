from __future__ import annotations

from pathlib import Path

import yaml

from riskflow.blocker_audit import build_blocker_audit
from riskflow.research_lane_router import build_lane_assignment, has_open_research_lanes
from riskflow.research_map import run_research_map_update
from riskflow.validation_governance import build_validation_governance


def _mart() -> dict:
    return {
        "model": "riskflow_lab_director_evidence_mart_v0",
        "session_id": "governance_test",
        "rows": [
            {
                "trial_id": "loop_0001:lower_high_warning",
                "hypothesis_id": "lower_high_warning",
                "root_id": "warning_root",
                "setup_class": "lower_high_rollover_warning",
                "claim_type": "warning_blocker",
                "discovery_stage": "counterexample",
                "contract_tier": "blocker",
                "timeframe": "4h",
                "median_forward_relative_return": -0.12,
                "median_drawdown": -0.18,
                "hit_rate": 0.35,
                "unique_symbols": 11,
                "event_clusters": 10,
            },
            {
                "trial_id": "loop_0002:warning_control",
                "hypothesis_id": "warning_control",
                "root_id": "warning_root",
                "setup_class": "lower_high_rollover_warning",
                "claim_type": "control",
                "discovery_stage": "causal_decomposition",
                "contract_tier": "archive",
                "timeframe": "4h",
                "median_forward_relative_return": -0.03,
                "median_drawdown": -0.08,
                "hit_rate": 0.42,
                "unique_symbols": 12,
                "event_clusters": 9,
            },
            {
                "trial_id": "loop_0003:deep_reset",
                "hypothesis_id": "deep_reset",
                "root_id": "bullish_root",
                "setup_class": "deep_reset_reclaim_entry",
                "claim_type": "bullish_permission",
                "discovery_stage": "discovery",
                "contract_tier": "asymmetric_candidate",
                "timeframe": "1d",
                "median_forward_relative_return": 0.09,
                "median_drawdown": -0.05,
                "hit_rate": 0.57,
                "unique_symbols": 14,
                "event_clusters": 8,
            },
        ],
    }


def _belief_graph() -> dict:
    return {
        "model": "riskflow_lab_director_belief_graph_v0",
        "session_id": "governance_test",
        "beliefs": [
            {
                "claim_id": "lower_high_rollover_warning_4h",
                "plain_english_claim": "Lower-high rollover may identify warning blocker conditions.",
                "claim_kind": "blocker",
                "status": "promising_unvalidated",
                "setup_class": "lower_high_rollover_warning",
                "timeframes": ["4h"],
                "root_ids": ["warning_root"],
                "evidence_level": "L2_discovered",
                "confidence_score": 62,
                "known_failure_modes": ["false_positive_reclaim"],
                "suspected_drivers": ["gradient_fade"],
                "supporting_trials": ["loop_0001:lower_high_warning", "loop_0002:warning_control"],
                "contradicting_trials": [],
                "best_trial": {"contract_tier": "blocker"},
                "next_required_tests": ["direction_flip_counterexample"],
                "promotion_blockers": ["no_strict_validated_contract"],
                "product_translation_status": "not_eligible",
                "do_not_repeat": [],
            },
            {
                "claim_id": "deep_reset_reclaim_entry_1d",
                "plain_english_claim": "Deep reset reclaim may improve bullish permission.",
                "claim_kind": "entry",
                "status": "promising_unvalidated",
                "setup_class": "deep_reset_reclaim_entry",
                "timeframes": ["1d"],
                "root_ids": ["bullish_root"],
                "evidence_level": "L3_attributed",
                "confidence_score": 70,
                "known_failure_modes": [],
                "suspected_drivers": ["reset_depth", "reclaim_timing"],
                "supporting_trials": ["loop_0003:deep_reset"],
                "contradicting_trials": [],
                "best_trial": {"contract_tier": "strict_validated"},
                "next_required_tests": ["fresh_split_validation"],
                "promotion_blockers": [],
                "product_translation_status": "sidecar_candidate",
                "do_not_repeat": ["stale_bullish_root"],
            },
        ],
    }


def test_blocker_audit_requires_harm_avoided_controls() -> None:
    audit = build_blocker_audit(_mart(), _belief_graph())

    item = audit["items"][0]
    assert item["blocker_id"] == "lower_high_rollover_warning_4h"
    assert item["audit_decision"] == "valid_blocker"
    assert item["harm_avoided_score"] > item["missed_upside_cost"]


def test_lane_router_keeps_open_research_lanes() -> None:
    blocker_audit = build_blocker_audit(_mart(), _belief_graph())
    assignment = build_lane_assignment(_belief_graph(), blocker_audit=blocker_audit)

    lanes = {item["belief_id"]: item["lane"] for item in assignment["assignments"]}
    assert lanes["lower_high_rollover_warning_4h"] == "warning_blocker"
    assert lanes["deep_reset_reclaim_entry_1d"] in {"reset_quality", "path_management", "bullish_permission"}
    assert has_open_research_lanes(assignment) is True


def test_validation_governance_blocks_product_changes() -> None:
    blocker_audit = build_blocker_audit(_mart(), _belief_graph())
    assignment = build_lane_assignment(_belief_graph(), blocker_audit=blocker_audit)
    governance = build_validation_governance(_belief_graph(), lane_assignment=assignment, blocker_audit=blocker_audit)

    assert governance["product_change_allowed"] is False
    decisions = {item["belief_id"]: item["decision"] for item in governance["decisions"]}
    assert decisions["lower_high_rollover_warning_4h"] == "hold_for_validation"
    assert decisions["deep_reset_reclaim_entry_1d"] == "hold_for_validation"


def test_research_map_update_writes_durable_map_and_status(tmp_path: Path) -> None:
    mart_path = tmp_path / "evidence_mart.yaml"
    graph_path = tmp_path / "belief_graph.yaml"
    mart_path.write_text(yaml.safe_dump(_mart()), encoding="utf-8")
    graph_path.write_text(yaml.safe_dump(_belief_graph()), encoding="utf-8")

    result = run_research_map_update(
        evidence_mart_path=mart_path,
        belief_graph_path=graph_path,
        map_path=tmp_path / "research_map.yaml",
        report_root=tmp_path / "reports" / "riskflow_map",
    )

    assert result["paths"]["map"].exists()
    assert result["paths"]["status"].exists()
    research_map = result["research_map"]
    assert "deep_reset_reclaim_entry_1d" in {node["id"] for node in research_map["nodes"]}
    assert "stale_bullish_root" in research_map["views"]["saturated_families"]
