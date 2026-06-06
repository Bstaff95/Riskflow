from __future__ import annotations

import json
from pathlib import Path

import yaml

from riskflow.lab_director import (
    LabDirectorOptions,
    audit_director_plan,
    build_belief_graph,
    build_evidence_mart,
    design_lane_recovery_experiments,
    design_experiments,
    run_director_plan_next,
    _safe_slug_with_hash,
)
from riskflow.lab_loop import validate_lab_queue


def _write_director_fixture(tmp_path: Path) -> LabDirectorOptions:
    session_id = "director_test"
    source_grid = tmp_path / "research" / "lab_loop" / "generated_grids" / session_id / "deep_reset.yaml"
    source_grid.parent.mkdir(parents=True)
    source_grid.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_grammar_search_v0",
                "families": [
                    {
                        "family_id": "targeted_deep_reset_regime_reclaim_entry_compression_30",
                        "direction": "positive",
                        "detector": "regime_confirmed_reclaim",
                        "description": "Deep reset plus regime reclaim.",
                        "parameter_grid": {
                            "benchmark_window": [5],
                            "max_signal": [1.0],
                            "min_benchmark_return": [0.0],
                            "min_compression": [30.0],
                            "min_recent_signal_low": [-1.5],
                            "min_relative_slope": [0.05],
                            "relative_window": [5],
                            "require_warning_absent": [True],
                            "trigger": ["viscosity_reclaim"],
                            "warning_context_window": [8],
                            "warning_lookback": [20],
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    report_root = tmp_path / "reports" / "lab_loop"
    loop_dir = report_root / "2026-05-31" / f"session_{session_id}" / "loop_0021"
    loop_dir.mkdir(parents=True)
    source_value = source_grid.relative_to(tmp_path).as_posix()
    loop_dir.joinpath("hypothesis.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "targeted_deep_reset_regime_reclaim_entry_compression_30_validation_cooldown60_l0006",
                "root_id": "targeted_deep_reset_regime_reclaim_entry_compression_30",
                "track": "bullish_setup",
                "claim_type": "control",
                "setup_class": "deep_reset_regime_reclaim_entry",
                "primary_detector": "regime_confirmed_reclaim",
                "source": source_value,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    loop_dir.joinpath("grammar_search_manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_runner_v0",
                "hypothesis_id": "targeted_deep_reset_regime_reclaim_entry_compression_30_validation_cooldown60_l0006",
                "source_grid": source_value,
                "timeframes": ["1d"],
                "record_count": 23,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    loop_dir.joinpath("bullish_evidence.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_bullish_evidence_v0",
                "contract_model": "riskflow_bullish_contract_v2",
                "objective": "bullish-positive",
                "hypothesis_id": "targeted_deep_reset_regime_reclaim_entry_compression_30_validation_cooldown60_l0006",
                "track": "bullish_setup",
                "claim_type": "control",
                "setup_class": "deep_reset_regime_reclaim_entry",
                "contract_tier": "asymmetric_candidate",
                "asymmetry_score": 4.66,
                "contract_failures": ["positive rows exist but did not pass strict referee"],
                "strict_positive_survivors": 0,
                "strict_negative_survivors": 0,
                "positive_useful_rows": 4,
                "candidate_timeframe": "1d",
                "sample_size": 23,
                "unique_symbols": 17,
                "unique_event_clusters": 16,
                "terminal_median_relative_return": 0.0463,
                "edge_vs_unconditional": 0.05,
                "edge_vs_cluster": 0.02,
                "hit_rate": 0.565,
                "median_max_drawdown": -0.18,
                "mfe_mae_ratio": 3.642,
                "validation_status": "not_time_split_supported",
                "passes_path_gate": True,
                "passes_bullish_contract": False,
                "decision": "bullish_path_watchlist",
                "decision_reason": "positive rows exist but did not pass strict referee",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    state_path = tmp_path / "research" / "lab_loop" / "lab_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"session_id": session_id, "last_completed_loop": 21}), encoding="utf-8")
    runtime_queue = tmp_path / "research" / "lab_loop" / "runtime_queue.yaml"
    runtime_queue.write_text(
        yaml.safe_dump({"model": "riskflow_lab_loop_hypothesis_queue_v0", "queue": []}, sort_keys=False),
        encoding="utf-8",
    )
    return LabDirectorOptions(
        state_path=state_path,
        runtime_queue_path=runtime_queue,
        concept_scoreboard_path=tmp_path / "research" / "lab_loop" / "concept_scoreboard.yaml",
        evidence_ledger_path=tmp_path / "research" / "lab_loop" / "evidence_ledger.yaml",
        report_root=report_root,
        director_report_root=tmp_path / "reports" / "lab_director",
        output_queue_path=tmp_path / "research" / "lab_loop" / "director_candidate_queue.yaml",
        generated_grid_dir=tmp_path / "research" / "lab_loop" / "generated_grids" / "director",
        max_new_hypotheses=12,
        source_root=tmp_path,
    )


def test_evidence_mart_normalizes_bullish_loop_artifacts(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)

    mart = build_evidence_mart(options)

    assert mart["row_count"] == 1
    row = mart["rows"][0]
    assert row["contract_tier"] == "asymmetric_candidate"
    assert row["setup_class"] == "deep_reset_regime_reclaim_entry"
    assert row["timeframe"] == "1d"
    assert row["sample_size"] == 23
    assert row["same_cluster_pass"] is True


def test_belief_graph_keeps_asymmetric_candidate_discovery_only(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)

    graph = build_belief_graph(build_evidence_mart(options))
    belief = graph["beliefs"][0]

    assert belief["claim_id"] == "deep_reset_regime_reclaim_entry_1d"
    assert belief["evidence_level"] == "L2_discovered"
    assert belief["confidence_score"] <= 60
    assert "no_strict_validated_contract" in belief["promotion_blockers"]
    assert "ablate_reset_depth" in belief["next_required_tests"]
    assert "ablate_reclaim_timing" in belief["next_required_tests"]


def test_director_plan_generates_valid_decomposition_queue(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)

    result = run_director_plan_next(options)

    assert result["audit"]["passed"] is True
    queue = result["plan"]["generated_queue"]
    assert validate_lab_queue(queue, validate_sources=True, source_root=tmp_path) == []
    stages = {item["research_stage"] for item in queue["queue"]}
    assert "causal_decomposition" in stages
    assert "validation" in stages
    questions = " ".join(item["research_question"] for item in queue["queue"])
    assert "reset depth" in questions
    assert "warning absence" in questions


def test_director_skips_seen_ids_and_emits_deeper_controls(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)
    graph = build_belief_graph(build_evidence_mart(options))
    seen = {
        "director_deep_reset_regime_reclaim_entry_1d_ablate_reset_depth",
        "director_deep_reset_regime_reclaim_entry_1d_ablate_reclaim_timing",
        "director_deep_reset_regime_reclaim_entry_1d_compression_dependency",
        "director_deep_reset_regime_reclaim_entry_1d_warning_filter_dependency",
        "director_deep_reset_regime_reclaim_entry_1d_parent_context_dependency",
        "director_deep_reset_regime_reclaim_entry_1d_validation_lag0",
        "director_deep_reset_regime_reclaim_entry_1d_validation_lag2",
        "director_deep_reset_regime_reclaim_entry_1d_validation_cooldown60",
        "director_deep_reset_regime_reclaim_entry_1d_direction_flip_counterexample",
        "director_deep_reset_regime_reclaim_entry_1d_timeframe_transfer",
    }

    plan = design_experiments(
        graph,
        output_queue_path=tmp_path / "research" / "lab_loop" / "director_candidate_queue.yaml",
        generated_grid_dir=tmp_path / "research" / "lab_loop" / "generated_grids" / "director_seen",
        max_new_hypotheses=6,
        source_root=tmp_path,
        existing_hypothesis_ids=seen,
    )

    ids = {item["id"] for item in plan["generated_queue"]["queue"]}
    assert "director_deep_reset_regime_reclaim_entry_1d_validation_lag1_frozen" in ids
    assert "director_deep_reset_regime_reclaim_entry_1d_validation_cooldown30" in ids
    assert "director_deep_reset_regime_reclaim_entry_1d_timeframe_transfer_1h" in ids
    assert ids.isdisjoint(seen)


def test_lane_recovery_generates_valid_reset_quality_queue(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)
    mart = build_evidence_mart(options)
    graph = build_belief_graph(mart)
    lane_assignment = {
        "model": "riskflow_research_lane_assignment_v0",
        "open_lanes": ["reset_quality"],
        "assignments": [
            {
                "belief_id": "deep_reset_regime_reclaim_entry_1d",
                "lane": "reset_quality",
                "blocked": False,
                "confidence_score": 60,
            }
        ],
    }

    plan = design_lane_recovery_experiments(
        mart,
        graph,
        lane_assignment,
        output_queue_path=tmp_path / "research" / "lab_loop" / "recovery_candidate_queue.yaml",
        generated_grid_dir=tmp_path / "research" / "lab_loop" / "generated_grids" / "recovery",
        max_new_hypotheses=8,
        source_root=tmp_path,
    )

    assert plan["model"] == "riskflow_lab_director_lane_recovery_plan_v0"
    assert plan["generated_count"] > 0
    queue = plan["generated_queue"]
    assert validate_lab_queue(queue, validate_sources=True, source_root=tmp_path) == []
    ids = {item["id"] for item in queue["queue"]}
    assert any(item_id.startswith("recovery_reset_quality_") for item_id in ids)
    assert {item["production_effect"] for item in queue["queue"]} == {"none"}


def test_lane_recovery_supports_extended_research_lanes(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)
    mart = build_evidence_mart(options)
    graph = build_belief_graph(mart)
    expected_tracks = {
        "cross_asset_regime": "mtf_context",
        "path_management": "bullish_setup",
        "invalidation": "warning",
        "gradient_interpretation": "gradient_translation",
    }

    for lane, expected_track in expected_tracks.items():
        lane_assignment = {
            "model": "riskflow_research_lane_assignment_v0",
            "open_lanes": [lane],
            "assignments": [
                {
                    "belief_id": "deep_reset_regime_reclaim_entry_1d",
                    "lane": lane,
                    "blocked": False,
                    "confidence_score": 60,
                }
            ],
        }
        plan = design_lane_recovery_experiments(
            mart,
            graph,
            lane_assignment,
            output_queue_path=tmp_path / f"{lane}_recovery_candidate_queue.yaml",
            generated_grid_dir=tmp_path / "research" / "lab_loop" / "generated_grids" / lane,
            max_new_hypotheses=8,
            source_root=tmp_path,
        )

        assert plan["generated_count"] > 0, lane
        assert plan["blocked_lanes"] == [], lane
        queue = plan["generated_queue"]
        assert validate_lab_queue(queue, validate_sources=True, source_root=tmp_path) == []
        assert {item["research_lane"] for item in queue["queue"]} == {lane}
        assert expected_track in {item["track"] for item in queue["queue"]}
        assert {item["production_effect"] for item in queue["queue"]} == {"none"}


def test_lane_recovery_skips_already_seen_ids(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)
    mart = build_evidence_mart(options)
    graph = build_belief_graph(mart)
    lane_assignment = {
        "open_lanes": ["warning_blocker"],
        "assignments": [
            {
                "belief_id": "deep_reset_regime_reclaim_entry_1d",
                "lane": "warning_blocker",
                "blocked": False,
                "confidence_score": 60,
            }
        ],
    }
    first = design_lane_recovery_experiments(
        mart,
        graph,
        lane_assignment,
        output_queue_path=tmp_path / "first_queue.yaml",
        generated_grid_dir=tmp_path / "first_grids",
        max_new_hypotheses=8,
        source_root=tmp_path,
    )
    seen = {item["id"] for item in first["generated_queue"]["queue"]}

    second = design_lane_recovery_experiments(
        mart,
        graph,
        lane_assignment,
        output_queue_path=tmp_path / "second_queue.yaml",
        generated_grid_dir=tmp_path / "second_grids",
        max_new_hypotheses=8,
        source_root=tmp_path,
        existing_hypothesis_ids=seen,
    )

    assert second["generated_count"] == 0
    assert second["generated_queue"]["queue"] == []
    assert all(str(item["reason"]).startswith("already_seen:") for item in second["skipped"])


def test_director_long_ids_keep_unique_hash_suffixes() -> None:
    first = _safe_slug_with_hash("director_" + "very_long_claim_" * 12 + "validation_lag0", max_length=96)
    second = _safe_slug_with_hash("director_" + "very_long_claim_" * 12 + "validation_lag2", max_length=96)

    assert len(first) <= 96
    assert len(second) <= 96
    assert first != second


def test_director_apply_can_append_audited_queue_to_runtime(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)
    options = LabDirectorOptions(**{**options.__dict__, "apply": True, "apply_to_runtime": True})

    result = run_director_plan_next(options)

    assert result["audit"]["passed"] is True
    assert result["runtime_added"] > 0
    runtime = yaml.safe_load(options.runtime_queue_path.read_text(encoding="utf-8"))
    assert len(runtime["queue"]) == result["runtime_added"]
    assert options.output_queue_path.exists()


def test_director_audit_rejects_production_effects(tmp_path: Path) -> None:
    options = _write_director_fixture(tmp_path)
    result = run_director_plan_next(options)
    plan = result["plan"]
    plan["generated_queue"]["queue"][0]["production_effect"] = "changes_gradient"

    audit = audit_director_plan(plan, source_root=tmp_path)

    assert audit["passed"] is False
    assert any("production_effect" in error for error in audit["errors"])
