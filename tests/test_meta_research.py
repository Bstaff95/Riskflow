from __future__ import annotations

from pathlib import Path

import yaml

from riskflow.lab_director import LabDirectorOptions
from riskflow.meta_research import (
    LabMetaOptions,
    audit_process_intervention,
    build_process_scorecard,
    choose_process_intervention,
    diagnose_process_failure,
    run_lab_meta_plan,
)


def _mart(rows: list[dict]) -> dict:
    return {
        "model": "riskflow_lab_director_evidence_mart_v0",
        "generated_at": "2026-05-31T00:00:00+00:00",
        "session_id": "meta_test",
        "row_count": len(rows),
        "inputs": {"report_root": "reports/lab_loop"},
        "rows": rows,
    }


def _row(**updates: object) -> dict:
    row = {
        "trial_id": "loop_0001:hyp",
        "loop_number": 1,
        "hypothesis_id": "deep_reset_validation",
        "root_id": "deep_reset_root",
        "claim_type": "control",
        "setup_class": "deep_reset_regime_reclaim_entry",
        "timeframe": "1d",
        "discovery_stage": "discovery",
        "contract_tier": "asymmetric_candidate",
        "decision": "bullish_path_watchlist",
        "median_forward_relative_return": 0.04,
        "hit_rate": 0.56,
        "mfe_mae_ratio": 2.1,
        "sample_size": 24,
        "unique_symbols": 14,
        "event_clusters": 13,
        "time_split_pass": False,
        "source_grid_path": "research/grid.yaml",
        "source_report_dir": "reports/lab_loop/session/loop_0001",
        "bullish_evidence_path": "reports/lab_loop/session/loop_0001/bullish_evidence.yaml",
    }
    row.update(updates)
    return row


def _belief(level: str = "L2_discovered") -> dict:
    return {
        "claim_id": "deep_reset_regime_reclaim_entry_1d",
        "plain_english_claim": "deep reset reclaim may improve bullish path management on 1d.",
        "claim_kind": "permission",
        "status": "promising_unvalidated",
        "setup_class": "deep_reset_regime_reclaim_entry",
        "timeframes": ["1d"],
        "root_ids": ["deep_reset_root"],
        "evidence_level": level,
        "confidence_score": 55 if level == "L2_discovered" else 72,
        "known_failure_modes": ["no_strict_validated_contract"],
        "suspected_drivers": ["reset_depth", "reclaim_timing", "warning_filter"],
        "supporting_trials": ["loop_0001:hyp"],
        "contradicting_trials": [],
        "next_required_tests": ["ablate_reset_depth", "direction_flip_counterexample"],
        "promotion_blockers": ["no_strict_validated_contract"],
    }


def test_meta_scorecard_routes_l2_discovery_to_decomposition() -> None:
    mart = _mart([_row()])
    graph = {"model": "riskflow_lab_director_belief_graph_v0", "session_id": "meta_test", "beliefs": [_belief()]}
    plan = {"research_mode": "decompose_promising_family", "generated_queue": {"queue": [{"id": "q1"}]}}
    audit = {"passed": True}

    scorecard = build_process_scorecard(mart, graph, plan=plan, audit=audit)
    diagnosis = diagnose_process_failure(scorecard)
    intervention = choose_process_intervention(scorecard, diagnosis, graph, plan=plan)

    assert scorecard["overall_process_score"] <= 80
    assert intervention["intervention_type"] == "decompose_top_belief"
    assert "deep_reset_regime_reclaim_entry_1d" in intervention["target_belief_ids"]
    assert "reset_quality" in scorecard["top_beliefs"][0]["categories"]


def test_meta_scorecard_routes_l3_belief_to_frozen_validation() -> None:
    mart = _mart([_row(discovery_stage="causal_decomposition"), _row(trial_id="loop_0002:hyp", discovery_stage="validation")])
    graph = {"model": "riskflow_lab_director_belief_graph_v0", "session_id": "meta_test", "beliefs": [_belief("L3_attributed")]}
    plan = {"research_mode": "decompose_promising_family", "generated_queue": {"queue": [{"id": "q1"}]}}
    audit = {"passed": True}

    scorecard = build_process_scorecard(mart, graph, plan=plan, audit=audit)
    intervention = choose_process_intervention(scorecard, diagnose_process_failure(scorecard), graph, plan=plan)

    assert intervention["intervention_type"] == "validate_frozen_rule"


def test_meta_scorecard_penalizes_duplicate_same_sample_research() -> None:
    rows = [
        _row(
            trial_id=f"loop_{index:04d}:hyp",
            hypothesis_id=f"hyp_{index}",
            unique_symbols=3,
            event_clusters=2,
            source_grid_path="research/same_grid.yaml",
            contract_tier="archive",
        )
        for index in range(1, 9)
    ]
    graph = {"model": "riskflow_lab_director_belief_graph_v0", "session_id": "meta_test", "beliefs": []}

    scorecard = build_process_scorecard(_mart(rows), graph, plan={"generated_queue": {"queue": []}, "stop_reason": "no_valid_director_experiments"}, audit={"passed": True})
    diagnosis = diagnose_process_failure(scorecard)

    assert scorecard["penalties"]["sample_reuse"] > 65
    assert "same_sample_overfit" in diagnosis["failure_modes"]


def test_process_intervention_audit_rejects_production_effect() -> None:
    intervention = {
        "model": "riskflow_lab_process_intervention_plan_v0",
        "intervention_type": "decompose_top_belief",
        "rationale": "test",
        "queue_requirements": ["ablate driver"],
        "policy_adjustments": [],
        "acceptance_checks": [],
        "production_effect": "changes_gradient",
        "supporting_artifacts": ["reports/example.yaml"],
    }

    audit = audit_process_intervention(intervention)

    assert audit["passed"] is False
    assert any("production_effect" in error for error in audit["errors"])


def test_lab_meta_plan_writes_artifacts_from_director_fixture(tmp_path: Path) -> None:
    source_grid = tmp_path / "research" / "grid.yaml"
    source_grid.parent.mkdir(parents=True)
    source_grid.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_grammar_search_v0",
                "families": [
                    {
                        "family_id": "deep_reset",
                        "direction": "positive",
                        "detector": "regime_confirmed_reclaim",
                        "parameter_grid": {
                            "min_recent_signal_low": [-1.5],
                            "trigger": ["viscosity_reclaim"],
                            "require_warning_absent": [True],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report_root = tmp_path / "reports" / "lab_loop"
    loop_dir = report_root / "2026-05-31" / "session_meta_test" / "loop_0001"
    loop_dir.mkdir(parents=True)
    loop_dir.joinpath("hypothesis.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "deep_reset_hyp",
                "root_id": "deep_reset",
                "setup_class": "deep_reset_regime_reclaim_entry",
                "claim_type": "control",
                "source": source_grid.relative_to(tmp_path).as_posix(),
            }
        ),
        encoding="utf-8",
    )
    loop_dir.joinpath("grammar_search_manifest.yaml").write_text(
        yaml.safe_dump({"source_grid": source_grid.relative_to(tmp_path).as_posix()}),
        encoding="utf-8",
    )
    loop_dir.joinpath("bullish_evidence.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": "deep_reset_hyp",
                "setup_class": "deep_reset_regime_reclaim_entry",
                "claim_type": "control",
                "contract_tier": "asymmetric_candidate",
                "decision": "bullish_path_watchlist",
                "candidate_timeframe": "1d",
                "sample_size": 21,
                "unique_symbols": 12,
                "unique_event_clusters": 12,
                "terminal_median_relative_return": 0.04,
                "hit_rate": 0.56,
                "mfe_mae_ratio": 2.0,
            }
        ),
        encoding="utf-8",
    )
    state_path = tmp_path / "research" / "lab_loop" / "lab_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text('{"session_id": "meta_test", "last_completed_loop": 1}', encoding="utf-8")
    runtime_queue = tmp_path / "research" / "lab_loop" / "runtime_queue.yaml"
    runtime_queue.write_text("model: riskflow_lab_loop_hypothesis_queue_v0\nqueue: []\n", encoding="utf-8")
    director_options = LabDirectorOptions(
        state_path=state_path,
        runtime_queue_path=runtime_queue,
        report_root=report_root,
        director_report_root=tmp_path / "reports" / "lab_director",
        output_queue_path=tmp_path / "research" / "lab_loop" / "director_queue.yaml",
        generated_grid_dir=tmp_path / "research" / "lab_loop" / "generated_grids" / "director",
        source_root=tmp_path,
    )

    result = run_lab_meta_plan(LabMetaOptions(director_options=director_options, meta_report_root=tmp_path / "reports" / "lab_meta"))

    assert result["audit"]["passed"] is True
    assert result["paths"]["scorecard"].exists()
    assert result["paths"]["intervention"].exists()
