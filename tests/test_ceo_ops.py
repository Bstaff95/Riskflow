from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from riskflow.ceo_ops import (
    CeoOpsOptions,
    build_product_delta_scoreboard,
    run_ceo_plan,
    run_ceo_review,
    run_ceo_run_block,
)


def _options(tmp_path: Path, *, run_id: str = "ceo_test", lab_run_id: str = "ceo_test_lab", apply: bool = False) -> CeoOpsOptions:
    queue = tmp_path / "research" / "seed_queue.yaml"
    queue.parent.mkdir(parents=True, exist_ok=True)
    queue.write_text(yaml.safe_dump({"model": "riskflow_lab_loop_hypothesis_queue_v0", "queue": []}), encoding="utf-8")
    return CeoOpsOptions(
        run_id=run_id,
        lab_run_id=lab_run_id,
        queue_path=queue,
        report_root=tmp_path / "reports" / "ceo_runs",
        lab_ops_report_root=tmp_path / "reports" / "lab_ops",
        lab_ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        block_epochs=2,
        epoch_size=5,
        apply=apply,
    )


def _write_lab_artifacts(tmp_path: Path, lab_run_id: str = "ceo_test_lab", *, with_candidate: bool = True) -> None:
    root = tmp_path / "reports" / "lab_ops" / lab_run_id
    governance = root / "governance" / "block_0001"
    governance.mkdir(parents=True, exist_ok=True)
    (root / "latest_status.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_ops_latest_status_v0",
                "run_id": lab_run_id,
                "status": "stopped",
                "stop_reason": "request_fresh_data",
                "completed_epochs": 2,
                "completed_blocks": 1,
                "last_completed_loop": 10,
                "latest_process_score": 67,
                "latest_intervention": "request_fresh_data",
                "governance": {"open_lanes": ["warning_blocker"], "all_lanes_blocked": False},
            }
        ),
        encoding="utf-8",
    )
    (root / "run_manifest.yaml").write_text(
        yaml.safe_dump({"status": "stopped", "completed_epochs": 2, "completed_blocks": 1, "objective": "bullish-positive"}),
        encoding="utf-8",
    )
    assignments = [
        {
            "belief_id": "lower_high_rollover_warning_4h",
            "lane": "warning_blocker",
            "next_action": "validate_blocker_cost",
            "blocked": False,
            "evidence_level": "L3_attributed",
            "confidence_score": 72,
        }
    ] if with_candidate else []
    (governance / "lane_assignment.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_research_lane_assignment_v0",
                "open_lanes": ["warning_blocker"] if with_candidate else [],
                "all_lanes_blocked": False,
                "lane_counts": {"warning_blocker": 1} if with_candidate else {},
                "assignments": assignments,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    decisions = [
        {
            "belief_id": "lower_high_rollover_warning_4h",
            "lane": "warning_blocker",
            "current_gate": "G4_validated",
            "decision": "hold_for_validation",
            "evidence_level": "L3_attributed",
            "production_effect": "none",
        }
    ] if with_candidate else []
    (governance / "validation_decision.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_validation_governance_v0",
                "decision_counts": {"hold_for_validation": 1} if with_candidate else {},
                "gate_counts": {"G4_validated": 1} if with_candidate else {},
                "product_change_allowed": False,
                "decisions": decisions,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (governance / "research_map.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_research_map_v0",
                "nodes": [{"id": "lower_high_rollover_warning_4h", "status": "validated_candidate"}] if with_candidate else [],
                "edges": [],
                "views": {
                    "validation_debt": ["lower_high_rollover_warning_4h"] if with_candidate else [],
                    "product_ready_candidates": ["lower_high_rollover_warning_4h"] if with_candidate else [],
                    "saturated_families": [],
                    "top_open_questions": [],
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (governance / "blocker_audit.yaml").write_text(yaml.safe_dump({"items": [], "decision_counts": {}}), encoding="utf-8")


def test_ceo_plan_writes_manifest_and_plan(tmp_path: Path) -> None:
    options = _options(tmp_path)

    result = run_ceo_plan(options)

    assert result["run_id"] == "ceo_test"
    assert result["paths"]["manifest"].exists()
    assert result["paths"]["plan"].exists()
    assert result["plan"]["production_effect"] == "none"


def test_ceo_run_block_requires_apply(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=False)

    with pytest.raises(ValueError, match="requires --apply"):
        run_ceo_run_block(options)


def test_product_delta_extracts_shadow_candidates() -> None:
    scoreboard = build_product_delta_scoreboard(
        {
            "lane_assignment": {
                "assignments": [
                    {
                        "belief_id": "reset_quality_candidate",
                        "lane": "reset_quality",
                        "evidence_level": "L3_attributed",
                        "confidence_score": 70,
                    }
                ]
            },
            "validation_governance": {
                "decisions": [
                    {
                        "belief_id": "reset_quality_candidate",
                        "current_gate": "G4_validated",
                        "decision": "hold_for_validation",
                    }
                ]
            },
        }
    )

    assert scoreboard["candidate_count"] == 1
    assert scoreboard["candidates"][0]["champion"] == "core_signal_v0"
    assert scoreboard["candidates"][0]["comparison_status"] == "needs_champion_challenger"
    assert scoreboard["production_effect"] == "none"


def test_ceo_review_writes_decision_packet_for_product_candidate(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=True)

    result = run_ceo_review(options)

    assert result["decision"]["decision"] == "run_champion_challenger"
    assert result["paths"]["latest_decision_packet"].exists()
    assert result["paths"]["product_delta"].exists()
    packet = result["paths"]["latest_decision_packet"].read_text(encoding="utf-8")
    assert "Riskflow CEO Decision Packet" in packet
    assert "Chart-facing value: candidate_pipeline" in packet


def test_ceo_review_flags_fake_progress_without_product_delta(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=False)

    result = run_ceo_review(options)

    risk_register = yaml.safe_load(result["paths"]["risk_register"].read_text(encoding="utf-8"))
    assert any(item["risk"] == "fake_progress" for item in risk_register["risks"])
    assert result["product_delta"]["chart_facing_value_status"] == "no_product_delta_yet"
