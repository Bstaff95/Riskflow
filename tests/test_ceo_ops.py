from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import riskflow.ceo_ops as ceo_ops
from riskflow.ceo_ops import (
    CeoOpsOptions,
    build_product_delta_scoreboard,
    run_ceo_heartbeat_status,
    run_ceo_plan,
    run_ceo_review,
    run_ceo_run_block,
    run_ceo_stop,
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


def _write_lab_artifacts(
    tmp_path: Path,
    lab_run_id: str = "ceo_test_lab",
    *,
    with_candidate: bool = True,
    stop_reason: str = "request_fresh_data",
    product_change_allowed: bool = False,
) -> None:
    root = tmp_path / "reports" / "lab_ops" / lab_run_id
    governance = root / "governance" / "block_0001"
    governance.mkdir(parents=True, exist_ok=True)
    (root / "latest_status.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_ops_latest_status_v0",
                "run_id": lab_run_id,
                "status": "stopped",
                "stop_reason": stop_reason,
                "completed_epochs": 2,
                "completed_blocks": 1,
                "last_completed_loop": 10,
                "latest_process_score": 67,
                "latest_intervention": stop_reason,
                "governance": {"open_lanes": ["warning_blocker"] if with_candidate else [], "all_lanes_blocked": False},
            }
        ),
        encoding="utf-8",
    )
    (root / "run_manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "status": "stopped",
                "stop_reason": stop_reason,
                "completed_epochs": 2,
                "completed_blocks": 1,
                "objective": "bullish-positive",
            }
        ),
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
                "product_change_allowed": product_change_allowed,
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
    heartbeat = yaml.safe_load(result["paths"]["heartbeat_status"].read_text(encoding="utf-8"))
    assert heartbeat["last_block_number"] == 1
    assert heartbeat["last_decision"] == "run_champion_challenger"
    assert heartbeat["continue_recommended"] is True


def test_ceo_review_flags_fake_progress_without_product_delta(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=False)

    result = run_ceo_review(options)

    risk_register = yaml.safe_load(result["paths"]["risk_register"].read_text(encoding="utf-8"))
    assert any(item["risk"] == "fake_progress" for item in risk_register["risks"])
    assert result["product_delta"]["chart_facing_value_status"] == "no_product_delta_yet"


def test_repeated_ceo_run_block_reuses_state_and_keeps_prior_packets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    options = _options(tmp_path, apply=True)
    calls = []

    def fake_run_lab_ops_run(lab_options):
        calls.append(lab_options)
        _write_lab_artifacts(tmp_path, with_candidate=True)
        return {"run_id": lab_options.run_id, "status": "completed", "stop_reason": "", "completed_epochs": 2, "completed_blocks": 1}

    monkeypatch.setattr(ceo_ops, "run_lab_ops_run", fake_run_lab_ops_run)

    first = run_ceo_run_block(options)
    runtime_root = options.lab_ops_runtime_root / "ceo_test_lab"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "lab_state.json").write_text("{}", encoding="utf-8")
    second = run_ceo_run_block(options)

    root = options.report_root / "ceo_test"
    assert first["review"]["block_number"] == 1
    assert second["review"]["block_number"] == 2
    assert (root / "executive_decision_packet_0001.md").exists()
    assert (root / "executive_decision_packet_0002.md").exists()
    assert calls[0].resume is False
    assert calls[1].resume is True


def test_ceo_heartbeat_status_is_read_only(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    packets_before = sorted(root.glob("executive_decision_packet_*.md"))

    status = run_ceo_heartbeat_status(options)

    packets_after = sorted(root.glob("executive_decision_packet_*.md"))
    assert status["from_file"] is True
    assert status["status"]["last_decision"] == "run_champion_challenger"
    assert packets_after == packets_before


def test_ceo_stop_writes_ceo_and_lab_stop_requests(tmp_path: Path) -> None:
    options = _options(tmp_path)

    result = run_ceo_stop(options, reason="flight_landed")

    assert result["paths"]["ceo_stop"].read_text(encoding="utf-8").strip() == "flight_landed"
    assert result["paths"]["lab_stop"].read_text(encoding="utf-8").strip() == "flight_landed"
    assert result["heartbeat_status"]["stop_requested"] is True
    assert result["heartbeat_status"]["continue_recommended"] is False


def test_ceo_stop_blocks_next_run_block(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    run_ceo_stop(options, reason="user_requested")

    with pytest.raises(RuntimeError, match="ceo stop requested"):
        run_ceo_run_block(options)


def test_true_blocker_prevents_heartbeat_continuation(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=True, stop_reason="director_audit_failed")

    result = run_ceo_review(options)

    heartbeat = yaml.safe_load(result["paths"]["heartbeat_status"].read_text(encoding="utf-8"))
    assert result["decision"]["decision"] == "stop_true_blocker"
    assert heartbeat["true_blocker"] is True
    assert heartbeat["continue_recommended"] is False


def test_product_promotion_requirement_prevents_heartbeat_continuation(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=True, product_change_allowed=True)

    result = run_ceo_review(options)

    heartbeat = yaml.safe_load(result["paths"]["heartbeat_status"].read_text(encoding="utf-8"))
    assert heartbeat["production_promotion_required"] is True
    assert heartbeat["continue_recommended"] is False


def test_fake_progress_recommends_repair_or_broaden_not_blind_continuation(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=False, stop_reason="no_runnable_and_no_valid_director_plan")

    result = run_ceo_review(options)

    assert result["decision"]["decision"] in {"patch_research_infra", "broaden_hypothesis_source", "request_fresh_data"}
    assert result["decision"]["decision"] != "continue_governed_research"
