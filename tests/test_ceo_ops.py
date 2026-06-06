from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml

import riskflow.ceo_ops as ceo_ops
import riskflow.cli as cli
from riskflow.ceo_ops import (
    CeoOpsOptions,
    attach_metric_sources_to_action_plan,
    build_champion_challenger_action_plan,
    build_champion_challenger_results,
    build_champion_challenger_visual_review_queue,
    build_ceo_promotion_proposal,
    build_product_delta_scoreboard,
    run_ceo_action_board,
    run_ceo_artifact_coherence,
    run_ceo_approval_apply,
    run_ceo_approval_queue,
    run_ceo_approval_record,
    run_ceo_blocker_stack,
    run_ceo_broaden_hypothesis_source,
    run_ceo_capability_backlog,
    run_ceo_champion_challenger,
    run_ceo_decision_quality,
    run_ceo_dispatch_receipt,
    run_ceo_evidence_debt_register,
    run_ceo_execute_next,
    run_ceo_executive_kpis,
    run_ceo_eval_suite,
    run_ceo_eval_fixtures,
    run_ceo_fresh_withheld_validation_contract,
    run_ceo_fresh_withheld_snapshot_declare,
    run_ceo_fresh_withheld_snapshot_manifest,
    run_ceo_fresh_withheld_validation_executor,
    run_ceo_withheld_split_manifest,
    run_ceo_fresh_control_validation,
    run_ceo_fresh_data_preflight,
    run_ceo_flight_dashboard,
    run_ceo_frozen_candidate_validation,
    run_ceo_frozen_validation_executor,
    run_ceo_frozen_validation_rerun,
    run_ceo_guardrail_audit,
    run_ceo_heartbeat_journal,
    run_ceo_heartbeat_plan,
    run_ceo_heartbeat_status,
    run_ceo_heartbeat_tick,
    run_ceo_memory_delta,
    run_ceo_mission_score,
    run_ceo_operating_dashboard,
    run_ceo_operating_incident_register,
    run_ceo_operator_brief,
    run_ceo_operator_step,
    run_ceo_patch_research_infra,
    run_ceo_plan,
    run_ceo_portfolio_allocator,
    run_ceo_preflight_gate,
    run_ceo_promotion_proposal,
    run_ceo_repair_plan,
    run_ceo_report,
    run_ceo_replay,
    run_ceo_resumption_brief,
    run_ceo_review,
    run_ceo_role_dispatch,
    run_ceo_role_queue,
    run_ceo_role_result,
    run_ceo_run_block,
    run_ceo_run_index,
    run_ceo_status,
    run_ceo_strategy_capital_dashboard,
    run_ceo_stop,
    run_ceo_trace_grade,
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
        source_root=tmp_path,
        block_epochs=2,
        epoch_size=5,
        apply=apply,
    )


def _authorized(options: CeoOpsOptions, action: str) -> CeoOpsOptions:
    return replace(options, ceo_context="bound_dispatch", ceo_authorized_action=action)


def _write_test_universe(path: Path, *, min_active_members: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "name": "test_universe",
                "min_active_members": min_active_members,
                "assets": [
                    {"symbol": "AAA", "name": "Asset A", "sector": "test", "subgroup": "test"},
                    {"symbol": "BBB", "name": "Asset B", "sector": "test", "subgroup": "test"},
                    {"symbol": "CCC", "name": "Asset C", "sector": "test", "subgroup": "test"},
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_ohlcv_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "date,open,high,low,close,volume",
                "2099-01-01,1,2,1,2,100",
                "2099-01-02,2,3,2,3,120",
                "2099-01-03,3,4,3,4,130",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_action_result_fixture(root: Path, payload: dict[str, object]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    enriched = {"generated_at": "2026-06-06T00:00:00+00:00", **payload}
    run_id = str(enriched.get("run_id", "ceo_test"))
    lab_run_id = str(enriched.get("lab_run_id", "ceo_test_lab"))
    trust_names = [
        "decision_packet",
        "action_contract",
        "preflight_gate",
        "trace_grade",
        "ceo_replay",
        "ceo_eval_suite",
        "guardrail_audit",
        "memory_delta",
        "approval_queue",
        "approval_status",
        "mission_score",
        "strategy_capital_dashboard",
    ]
    receipt = {
        "model": "riskflow_ceo_dispatch_receipt_v0",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "run_id": run_id,
        "lab_run_id": lab_run_id,
        "dispatch_mode": "test_fixture",
        "decision": enriched.get("decision", ""),
        "status": "dispatch_blocked" if enriched.get("status") == "blocked" else "dispatch_allowed",
        "safe_to_dispatch": enriched.get("status") != "blocked",
        "reason": "test fixture dispatch receipt",
        "trust_artifact_fingerprints": {
            name: {"path": str(root / f"{name}.yaml"), "exists": False, "sha256": ""}
            for name in trust_names
        },
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }
    receipt_path = root / "dispatch_receipt.yaml"
    snapshot_path = root / "dispatch_receipts" / "test_fixture_receipt.yaml"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    receipt["receipt_id"] = "test_fixture_receipt"
    receipt["latest_alias_path"] = str(receipt_path)
    receipt["snapshot_path"] = str(snapshot_path)
    snapshot_path.write_text(yaml.safe_dump(receipt), encoding="utf-8")
    receipt_path.write_text(yaml.safe_dump(receipt), encoding="utf-8")
    enriched["dispatch_receipt"] = {"path": str(snapshot_path), "sha256": _sha256(snapshot_path)}
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(enriched), encoding="utf-8")
    (root / "ceo_action_ledger.jsonl").write_text(json.dumps(enriched, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(path: Path) -> dict[str, object]:
    return {"path": str(path), "exists": path.exists(), "sha256": _sha256(path) if path.exists() else ""}


def _write_fresh_withheld_executor_inputs(root: Path, *, include_grid: bool = True) -> None:
    root.mkdir(parents=True, exist_ok=True)
    frozen_plan_path = root / "frozen_candidate_validation_plan.yaml"
    rerun_result_path = root / "frozen_validation_rerun_result.yaml"
    preflight_path = root / "fresh_data_preflight.yaml"
    grid_path = root / "frozen_validation_rerun_grid.yaml"
    contract_path = root / "fresh_withheld_validation_contract.yaml"
    manifest_path = root / "fresh_withheld_snapshot_manifest.yaml"
    split_manifest_path = root / "withheld_split_manifest.yaml"
    active_asset_path = root / "AAA_1d.csv"
    _write_ohlcv_csv(active_asset_path)
    frozen_plan_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "status": "frozen_validation_specs_ready",
                "validation_specs": [{"spec_id": "spec_a", "status": "ready_for_execution"}],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    rerun_result_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_validation_rerun_v0",
                "status": "adapter_rerun_completed_not_promotion_eligible",
                "record_rows": 3,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    preflight_path.write_text(
        yaml.safe_dump({"safe_to_run_fresh_validation": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    if include_grid:
        grid_path.write_text(
            yaml.safe_dump(
                {
                    "model": "riskflow_grammar_search_grid_v0",
                    "families": [
                        {
                            "family_id": "family_a",
                            "detector": "regime_confirmed_reclaim",
                            "parameter_grid": {"trigger": ["viscosity_reclaim"]},
                        }
                    ],
                    "candidate_specs": [
                        {
                            "timeframe": "1d",
                            "benchmark": "MEME_BASKET",
                            "entry_lag_bars": "1",
                            "cooldown_bars": "30",
                        }
                    ],
                    "production_effect": "none",
                }
            ),
            encoding="utf-8",
        )
    contract_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_withheld_validation_contract_v0",
                "status": "fresh_withheld_validation_contract_ready",
                "artifact_fingerprints": {
                    "frozen_plan": _fingerprint(frozen_plan_path),
                    "rerun_result": _fingerprint(rerun_result_path),
                    "fresh_data_preflight": _fingerprint(preflight_path),
                    "rerun_grid": _fingerprint(grid_path),
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    split_manifest_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_withheld_split_manifest_v0",
                "status": "withheld_split_manifest_ready",
                "withheld_split_id": "withheld_split_a",
                "source_evidence_cutoff": "2099-01-01",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_withheld_snapshot_manifest_v0",
                "status": "ready",
                "snapshot_type": "withheld",
                "withheld_split_id": "withheld_split_a",
                "withheld_split_manifest_valid": True,
                "withheld_split_manifest": _fingerprint(split_manifest_path),
                "source_evidence_cutoff": "2099-01-01",
                "overlap_with_source_evidence": False,
                "rule_shape_frozen": True,
                "active_assets": [
                    {
                        "timeframe": "1d",
                        "symbol": "AAA",
                        "path": str(active_asset_path),
                        "latest_date": "2099-01-03",
                        "row_count": 3,
                        "data_sha256": _sha256(active_asset_path),
                    }
                ],
                "artifact_fingerprints": {
                    "contract": _fingerprint(contract_path),
                    "fresh_data_preflight": _fingerprint(preflight_path),
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )


def _write_fresh_control_plan(root: Path, *, belief_id: str = "candidate_a") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "fresh_control_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_control_validation_plan_v0",
                "status": "fresh_data_required",
                "candidate_count": 1,
                "missing_source_count": 0,
                "fresh_required_count": 1,
                "work_items": [
                    {
                        "priority": 1,
                        "belief_id": belief_id,
                        "product_role": "reset_quality",
                        "champion": "core_signal_v0",
                        "challenger": f"core_signal_v0_plus_{belief_id}",
                        "validation_route": "fresh_and_control_validation",
                        "source_status": "matched",
                        "source_count": 1,
                        "metric_summary": {
                            "role_decision": "needs_fresh_or_control_validation",
                            "champion_baseline_method": "same_source_all_ranked_variants_proxy",
                        },
                        "evidence_sources": [
                            {
                                "loop_dir": "reports/lab_ops/ceo_test_lab/lab_loop/session/loop_0001",
                                "ranked": "ranked.csv",
                                "bullish_evidence": "bullish_evidence.yaml",
                                "strict_referee": "strict_referee.csv",
                            }
                        ],
                        "required_tests": ["rerun the frozen shape after fresh OHLCV import or on a withheld split"],
                        "promotion_ceiling_before_pass": "shadow_candidate",
                        "production_effect": "none",
                    }
                ],
                "next_action": "import_or_curate_fresh_ohlcv_data",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
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
    assert "ceo execute-next" in result["plan"]["next_command"]
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


def test_champion_challenger_action_plan_prioritizes_shadow_candidates() -> None:
    product_delta = {
        "champion": "core_signal_v0",
        "required_metrics": ["forward_relative_return_vs_basket", "hit_rate"],
        "candidates": [
            {
                "belief_id": "reset_candidate",
                "product_role": "reset_quality",
                "current_gate": "G2_discovered",
                "validation_decision": "hold_for_validation",
                "evidence_level": "L2_discovered",
                "confidence_score": 70,
                "champion": "core_signal_v0",
                "challenger": "core_signal_v0_plus_reset_candidate",
                "comparison_status": "needs_champion_challenger",
            },
            {
                "belief_id": "warning_candidate",
                "product_role": "warning_blocker",
                "current_gate": "G2_discovered",
                "validation_decision": "hold_for_blocker_audit",
                "evidence_level": "L2_discovered",
                "confidence_score": 60,
                "champion": "core_signal_v0",
                "challenger": "core_signal_v0_plus_warning_candidate",
                "comparison_status": "needs_champion_challenger",
            },
        ],
    }

    plan = build_champion_challenger_action_plan(product_delta)

    assert plan["status"] == "ready"
    assert plan["candidate_count"] == 2
    assert plan["work_items"][0]["belief_id"] == "warning_candidate"
    assert plan["work_items"][0]["minimum_decision"] == "compare_against_core_signal_v0_before_more_recovery_expansion"
    assert plan["production_effect"] == "none"


def test_ceo_champion_challenger_writes_gap_when_metric_sources_are_missing(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)

    result = run_ceo_champion_challenger(_authorized(options, "run_champion_challenger"))

    assert result["results"]["status"] == "blocked_missing_metric_sources"
    assert result["paths"]["results"].exists()
    assert result["paths"]["visual_review_queue"].exists()
    assert result["paths"]["capability_gap"].exists()
    assert result["paths"]["binding_action_result"].exists()
    assert result["paths"]["action_outcome_card"].exists()
    action_result = yaml.safe_load(result["paths"]["binding_action_result"].read_text(encoding="utf-8"))
    outcome_card = yaml.safe_load(result["paths"]["action_outcome_card"].read_text(encoding="utf-8"))
    assert action_result["decision"] == "run_champion_challenger"
    assert action_result["action_taken"] == "champion_challenger"
    assert action_result["production_effect"] == "none"
    assert outcome_card["production_effect"] == "none"
    assert outcome_card["memory_delta_required"] is True
    assert outcome_card["evidence_provenance"]["output_artifacts"]["results"].endswith("champion_challenger_results.yaml")
    assert outcome_card["evidence_provenance"]["output_artifacts"]["visual_review_queue"].endswith(
        "champion_challenger_visual_review_queue.yaml"
    )
    assert outcome_card["failure_avoidance"]["status"] == "not_applicable"
    assert outcome_card["product_evidence_level"] == "not_evaluated"
    assert outcome_card["product_language_allowed"] is False


def test_champion_challenger_attaches_metric_sources_from_research_map(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    lab_run_id = "ceo_test_lab"
    loop_dir = tmp_path / "reports" / "lab_ops" / lab_run_id / "lab_loop" / "2026-06-01" / "session_a" / "loop_0001"
    loop_dir.mkdir(parents=True, exist_ok=True)
    (loop_dir / "bullish_evidence.yaml").write_text(
        yaml.safe_dump({"hypothesis_id": "root_candidate_a", "contract_tier": "asymmetric_candidate"}),
        encoding="utf-8",
    )
    (loop_dir / "hypothesis.yaml").write_text("families: []\n", encoding="utf-8")
    (loop_dir / "grammar_search_ranked.csv").write_text(
        "\n".join(
            [
                "variant_id,family_id,timeframe,classification,rank_score,median_forward_relative_return_secondary,hit_rate_forward_relative_return_primary,median_max_drawdown,median_max_favorable_excursion,median_mfe_mae_ratio,sample_size,unique_symbols,unique_event_clusters",
                "variant_a,family_a,1d,useful,12.5,-0.08,0.42,-0.2,0.3,1.5,40,15,20",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    governance = {
        "research_map": {
            "nodes": [
                {
                    "id": "candidate_a",
                    "status": "discovery_survivor",
                    "setup_class": "candidate_setup",
                    "timeframes": ["1d"],
                    "root_ids": ["root_candidate_a"],
                }
            ]
        }
    }
    action_plan = {
        "champion": "core_signal_v0",
        "work_items": [
            {
                "belief_id": "candidate_a",
                "product_role": "warning_blocker",
                "champion": "core_signal_v0",
                "challenger": "core_signal_v0_plus_candidate_a",
                "required_metrics": ["forward_relative_return_vs_basket"],
            }
        ],
    }

    enriched = attach_metric_sources_to_action_plan(action_plan, governance, options, lab_run_id)

    source = enriched["work_items"][0]["metric_sources"][0]
    assert enriched["metric_source_count"] == 1
    assert source["bullish_evidence"].endswith("bullish_evidence.yaml")
    assert source["metric_summary"]["champion_baseline_method"] == "same_source_all_ranked_variants_proxy"
    assert source["metric_summary"]["avoided_downside_benefit"] == pytest.approx(0.0)
    assert source["metric_summary"]["missed_upside_cost"] == pytest.approx(0.0)
    assert enriched["production_effect"] == "none"


def test_champion_challenger_results_route_mixed_source_gaps_to_validation_plan() -> None:
    action_plan = {
        "champion": "core_signal_v0",
        "work_items": [
            {
                "belief_id": "matched_candidate",
                "product_role": "warning_blocker",
                "champion": "core_signal_v0",
                "challenger": "core_signal_v0_plus_matched_candidate",
                "metric_sources": [{"metric_summary": {"role_decision": "shadow_challenger_promising"}}],
            },
            {
                "belief_id": "missing_candidate",
                "product_role": "reset_quality",
                "champion": "core_signal_v0",
                "challenger": "core_signal_v0_plus_missing_candidate",
            },
        ],
    }

    results = build_champion_challenger_results(action_plan)

    assert results["status"] == "shadow_comparison_partial_source_gaps"
    assert results["missing_metric_source_count"] == 1
    assert results["next_action"] == "run_fresh_or_control_validation_for_promising_shadow_challengers"
    assert results["results"][0]["product_metric_checklist"]["complete"] is False
    assert "forward_relative_return_vs_basket" in results["results"][0]["product_metric_checklist"]["missing"]


def test_champion_challenger_visual_review_queue_prioritizes_ready_sources() -> None:
    results = {
        "model": "riskflow_ceo_champion_challenger_results_v0",
        "results": [
            {
                "belief_id": "warning_candidate",
                "product_role": "warning_blocker",
                "champion": "core_signal_v0",
                "challenger": "core_signal_v0_plus_warning_candidate",
                "decision": "shadow_challenger_promising_needs_fresh_validation",
                "product_metric_checklist": {"complete": True, "missing": []},
                "metric_summary": {
                    "role_delta_vs_champion_baseline": 0.12,
                    "rank_score": 10.0,
                    "event_diversity": 20.0,
                    "missed_upside_cost": 0.0,
                    "avoided_downside_benefit": 0.12,
                },
                "available_metric_sources": [
                    {
                        "loop_dir": "reports/lab_ops/run/lab_loop/session/loop_0001",
                        "ranked": "grammar_search_ranked.csv",
                        "variant_records": "grammar_search_variant_records.csv",
                        "strict_referee": "strict_referee.csv",
                        "bullish_evidence": "bullish_evidence.yaml",
                    }
                ],
            }
        ],
    }

    queue = build_champion_challenger_visual_review_queue(results)

    assert queue["status"] == "ready"
    assert queue["ready_count"] == 1
    assert queue["items"][0]["review_status"] == "ready_for_visual_review"
    assert queue["items"][0]["review_focus"] == "blocker_false_positive_and_avoided_downside_review"
    assert queue["items"][0]["production_effect"] == "none"
    assert queue["production_effect"] == "none"


def test_ceo_fresh_control_validation_writes_validation_plan(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "champion_challenger_results.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_champion_challenger_results_v0",
                "status": "shadow_comparison_complete",
                "results": [
                    {
                        "belief_id": "candidate_a",
                        "product_role": "warning_blocker",
                        "champion": "core_signal_v0",
                        "challenger": "core_signal_v0_plus_candidate_a",
                        "decision": "shadow_challenger_promising_needs_fresh_validation",
                        "available_metric_sources": [
                            {
                                "loop_dir": "reports/lab_ops/ceo_test_lab/lab_loop/session/loop_0001",
                                "ranked": "ranked.csv",
                                "bullish_evidence": "bullish_evidence.yaml",
                                "strict_referee": "strict_referee.csv",
                                "metric_summary": {
                                    "champion_baseline_method": "same_source_all_ranked_variants_proxy",
                                    "role_decision": "shadow_challenger_promising",
                                },
                            }
                        ],
                        "metric_summary": {
                            "champion_baseline_method": "same_source_all_ranked_variants_proxy",
                            "role_decision": "shadow_challenger_promising",
                        },
                    }
                ],
                "next_action": "run_fresh_or_control_validation_for_promising_shadow_challengers",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_fresh_control_validation(
        _authorized(options, "run_fresh_or_control_validation_for_promising_shadow_challengers")
    )

    assert result["plan"]["status"] == "fresh_data_required"
    assert result["plan"]["next_action"] == "import_or_curate_fresh_ohlcv_data"
    assert result["plan"]["validation_completed"] is False
    assert result["plan"]["validation_result"] == "not_run"
    assert result["plan"]["candidate_status_after_plan"] == "shadow_only"
    assert result["plan"]["product_language_allowed"] is False
    assert result["paths"]["plan"].exists()
    assert result["paths"]["report"].exists()
    assert result["paths"]["action_outcome_card"].exists()
    assert result["action_result"]["decision"] == "run_fresh_or_control_validation_for_promising_shadow_challengers"
    assert result["action_result"]["action_taken"] == "fresh_control_validation_plan"
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_fresh_data_preflight_marks_ready_local_data(tmp_path: Path) -> None:
    config_path = tmp_path / "configs" / "test_universe.yaml"
    data_dir = tmp_path / "data" / "raw"
    _write_test_universe(config_path, min_active_members=2)
    _write_ohlcv_csv(data_dir / "AAA_1d.csv")
    _write_ohlcv_csv(data_dir / "BBB_1d.csv")

    options = replace(
        _options(tmp_path, apply=True),
        config_path=config_path,
        data_dir=data_dir,
        timeframes=("1d",),
    )

    result = run_ceo_fresh_data_preflight(_authorized(options, "request_fresh_data"))

    assert result["preflight"]["overall_status"] == "partial_ready"
    assert result["preflight"]["safe_to_run_fresh_validation"] is True
    assert result["preflight"]["next_action"] == "run_frozen_candidate_validation"
    assert result["preflight"]["timeframes"][0]["active_count"] == 2
    assert result["preflight"]["timeframes"][0]["missing_count"] == 1
    assert result["paths"]["preflight"].exists()
    assert result["paths"]["report"].exists()
    assert result["action_result"]["action_taken"] == "fresh_data_preflight"
    assert result["action_result"]["next_allowed_actions"] == ["run_frozen_candidate_validation"]
    assert result["action_result"]["production_effect"] == "none"


@pytest.mark.parametrize(
    ("call", "expected_action"),
    [
        (lambda options: run_ceo_run_block(options), "continue_governed_research"),
        (lambda options: run_ceo_champion_challenger(options), "run_champion_challenger"),
        (lambda options: run_ceo_fresh_control_validation(options), "run_fresh_or_control_validation"),
        (lambda options: run_ceo_fresh_data_preflight(options), "request_fresh_data"),
        (lambda options: run_ceo_frozen_candidate_validation(options), "run_frozen_candidate_validation"),
        (lambda options: run_ceo_frozen_validation_executor(options), "run_frozen_validation_executor"),
        (lambda options: run_ceo_frozen_validation_rerun(options), "run_frozen_validation_rerun"),
        (lambda options: run_ceo_fresh_withheld_validation_contract(options), "run_fresh_withheld_validation_contract"),
        (lambda options: run_ceo_withheld_split_manifest(options, withheld_split_id="x", source_evidence_cutoff="2099-01-01"), "write_withheld_split_manifest"),
        (lambda options: run_ceo_fresh_withheld_snapshot_manifest(options), "run_fresh_withheld_snapshot_manifest"),
        (
            lambda options: run_ceo_fresh_withheld_snapshot_declare(
                options,
                snapshot_type="withheld",
                withheld_split_id="x",
                source_evidence_cutoff="2099-01-01",
                confirm_no_overlap=True,
            ),
            "declare_fresh_withheld_snapshot_authority",
        ),
        (lambda options: run_ceo_fresh_withheld_validation_executor(options), "run_fresh_withheld_validation_executor"),
        (lambda options: run_ceo_patch_research_infra(options), "patch_research_infra"),
        (lambda options: run_ceo_broaden_hypothesis_source(options), "broaden_hypothesis_source"),
        (lambda options: run_ceo_promotion_proposal(options), "run_promotion_proposal"),
        (lambda options: run_ceo_evidence_debt_register(options), "run_evidence_debt_register"),
        (
            lambda options: run_ceo_approval_apply(options, approval_id="promotion_proposal", user_confirmed=True),
            "approval_apply",
        ),
    ],
)
def test_ceo_public_action_writers_reject_plain_external_calls(
    tmp_path: Path,
    call,
    expected_action: str,
) -> None:
    options = _options(tmp_path, apply=True)

    with pytest.raises(ValueError, match=expected_action):
        call(options)


def test_ceo_diagnostic_action_context_does_not_append_action_ledger(tmp_path: Path) -> None:
    options = _authorized(_options(tmp_path, apply=True), "run_fresh_withheld_validation_contract")
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    run_ceo_fresh_withheld_validation_contract(replace(options, ceo_context="diagnostic_refresh"))

    assert (root / "fresh_withheld_validation_contract.yaml").exists()
    assert not (root / "binding_action_result.yaml").exists()
    assert not (root / "ceo_action_ledger.jsonl").exists()


@pytest.mark.parametrize(
    ("call", "expected_action"),
    [
        (lambda options: run_ceo_run_block(options), "continue_governed_research"),
        (lambda options: run_ceo_patch_research_infra(options), "patch_research_infra"),
        (lambda options: run_ceo_broaden_hypothesis_source(options), "broaden_hypothesis_source"),
        (lambda options: run_ceo_fresh_withheld_snapshot_manifest(options), "run_fresh_withheld_snapshot_manifest"),
    ],
)
def test_ceo_diagnostic_context_rejects_heavy_action_writers(
    tmp_path: Path,
    call,
    expected_action: str,
) -> None:
    options = replace(_options(tmp_path, apply=True), ceo_context="diagnostic_refresh")

    with pytest.raises(ValueError, match=expected_action):
        call(options)


def test_ceo_frozen_candidate_validation_writes_specs_after_safe_preflight(tmp_path: Path) -> None:
    config_path = tmp_path / "configs" / "test_universe.yaml"
    data_dir = tmp_path / "data" / "raw"
    _write_test_universe(config_path, min_active_members=2)
    _write_ohlcv_csv(data_dir / "AAA_1d.csv")
    _write_ohlcv_csv(data_dir / "BBB_1d.csv")
    options = replace(
        _options(tmp_path, apply=True),
        config_path=config_path,
        data_dir=data_dir,
        timeframes=("1d",),
    )
    root = options.report_root / "ceo_test"
    _write_fresh_control_plan(root)
    run_ceo_fresh_data_preflight(_authorized(options, "request_fresh_data"))

    result = run_ceo_frozen_candidate_validation(_authorized(options, "run_frozen_candidate_validation"))

    assert result["plan"]["status"] == "frozen_validation_specs_ready"
    assert result["plan"]["safe_to_execute_specs"] is True
    assert result["plan"]["ready_spec_count"] == 1
    assert result["plan"]["validation_specs"][0]["status"] == "ready_for_execution"
    assert result["plan"]["validation_specs"][0]["frozen_shape_contract"]["no_post_result_threshold_tuning"] is True
    assert result["plan"]["validation_specs"][0]["production_effect"] == "none"
    assert result["plan"]["next_action"] == "run_frozen_validation_executor"
    assert result["paths"]["plan"].exists()
    assert result["paths"]["report"].exists()
    assert result["action_result"]["action_taken"] == "frozen_candidate_validation_scaffold"
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_frozen_candidate_validation_extracts_execution_adapter(tmp_path: Path) -> None:
    config_path = tmp_path / "configs" / "test_universe.yaml"
    data_dir = tmp_path / "data" / "raw"
    _write_test_universe(config_path, min_active_members=2)
    _write_ohlcv_csv(data_dir / "AAA_1d.csv")
    _write_ohlcv_csv(data_dir / "BBB_1d.csv")
    options = replace(
        _options(tmp_path, apply=True),
        config_path=config_path,
        data_dir=data_dir,
        timeframes=("1d",),
    )
    source_dir = tmp_path / "source_artifacts"
    source_dir.mkdir(parents=True, exist_ok=True)
    variant_records = source_dir / "variant_records.csv"
    variant_records.write_text(
        "\n".join(
            [
                "variant_id,family_id,detector,direction,timeframe,benchmark,params,entry_lag_bars,cooldown_bars",
                'variant_a,family_a,regime_confirmed_reclaim,positive,1d,MEME_BASKET,"{""trigger"": ""viscosity_reclaim""}",1,30',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    root = options.report_root / "ceo_test"
    _write_fresh_control_plan(root)
    plan = yaml.safe_load((root / "fresh_control_validation_plan.yaml").read_text(encoding="utf-8"))
    plan["work_items"][0]["metric_summary"]["best_variant_id"] = "variant_a"
    plan["work_items"][0]["evidence_sources"][0]["variant_records"] = str(variant_records)
    (root / "fresh_control_validation_plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
    run_ceo_fresh_data_preflight(_authorized(options, "request_fresh_data"))

    result = run_ceo_frozen_candidate_validation(_authorized(options, "run_frozen_candidate_validation"))

    adapter = result["plan"]["validation_specs"][0]["execution_adapter"]
    assert adapter["adapter_status"] == "ready"
    assert adapter["adapter_type"] == "grammar_search_variant_replay"
    assert adapter["detector"] == "regime_confirmed_reclaim"
    assert adapter["params"]["trigger"] == "viscosity_reclaim"
    assert adapter["production_effect"] == "none"


def test_ceo_frozen_validation_executor_replays_source_artifacts_without_promotion(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    source_dir = tmp_path / "source_artifacts"
    source_dir.mkdir(parents=True, exist_ok=True)
    strict_referee = source_dir / "strict_referee.csv"
    strict_referee.write_text(
        "\n".join(
            [
                "variant_id,strict_survivor,validation_status",
                "variant_a,True,strict_survivor",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    variant_records = source_dir / "variant_records.csv"
    variant_records.write_text(
        "\n".join(
            [
                "symbol,event_cluster_id,variant_id",
                "AAA,cluster_1,variant_a",
                "BBB,cluster_2,variant_a",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    root.mkdir(parents=True, exist_ok=True)
    (root / "frozen_candidate_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "status": "frozen_validation_specs_ready",
                "validation_completed": False,
                "validation_result": "not_run",
                "validation_specs": [
                    {
                        "spec_id": "frozen_validation_candidate_a",
                        "belief_id": "candidate_a",
                        "product_role": "reset_quality",
                        "status": "ready_for_execution",
                        "metric_summary_snapshot": {"best_variant_id": "variant_a"},
                        "execution_adapter": {
                            "adapter_status": "ready",
                            "adapter_type": "grammar_search_variant_replay",
                            "variant_id": "variant_a",
                            "family_id": "family_a",
                            "detector": "regime_confirmed_reclaim",
                            "direction": "positive",
                            "timeframe": "1d",
                            "benchmark": "MEME_BASKET",
                            "params": {"trigger": "viscosity_reclaim", "relative_window": 5},
                            "entry_lag_bars": "1",
                            "cooldown_bars": "30",
                            "production_effect": "none",
                        },
                        "evidence_sources": [
                            {
                                "loop_dir": str(source_dir),
                                "strict_referee": str(strict_referee),
                                "variant_records": str(variant_records),
                            }
                        ],
                        "required_metrics": ["forward_relative_return_vs_basket"],
                        "required_controls": ["fresh_snapshot_or_withheld_split"],
                        "production_effect": "none",
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_frozen_validation_executor(_authorized(options, "run_frozen_validation_executor"))

    execution = result["execution"]
    assert execution["status"] == "source_replay_completed"
    assert execution["validation_completed"] is True
    assert execution["validation_result"] == "source_replay_only_not_promotion_eligible"
    assert execution["product_language_allowed"] is False
    assert execution["production_effect"] == "none"
    assert execution["spec_results"][0]["best_source_survivor_count"] == 1
    assert execution["fresh_execution_contract"]["adapter_ready_count"] == 1
    assert "fresh_or_withheld_ohlcv_snapshot" in execution["fresh_execution_contract"]["required_next_inputs"]
    assert execution["next_action"] == "run_frozen_validation_rerun"
    assert result["rerun_grid"]["status"] == "ready"
    assert result["rerun_grid"]["families"][0]["family_id"] == "family_a"
    assert result["rerun_grid"]["families"][0]["parameter_grid"]["trigger"] == ["viscosity_reclaim"]
    assert result["paths"]["rerun_grid"].exists()
    assert result["action_result"]["action_taken"] == "frozen_validation_source_replay"
    assert result["action_result"]["production_effect"] == "none"
    updated_plan = yaml.safe_load((root / "frozen_candidate_validation_plan.yaml").read_text(encoding="utf-8"))
    assert updated_plan["validation_completed"] is True
    assert updated_plan["validation_result"] == "source_replay_only_not_promotion_eligible"


def test_ceo_frozen_validation_rerun_blocks_without_grid(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "frozen_candidate_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "status": "frozen_validation_specs_ready",
                "validation_specs": [],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_frozen_validation_rerun(_authorized(options, "run_frozen_validation_rerun"))

    rerun = result["rerun"]
    assert rerun["status"] == "blocked_missing_rerun_grid"
    assert rerun["product_language_allowed"] is False
    assert rerun["production_effect"] == "none"
    assert result["paths"]["result"].exists()
    assert result["paths"]["report"].exists()
    assert result["action_result"]["decision"] == "run_frozen_validation_rerun"
    assert result["action_result"]["action_taken"] == "frozen_validation_adapter_rerun"
    assert result["action_result"]["production_effect"] == "none"
    updated_plan = yaml.safe_load((root / "frozen_candidate_validation_plan.yaml").read_text(encoding="utf-8"))
    assert updated_plan["validation_rerun_status"] == "blocked_missing_rerun_grid"
    assert updated_plan["product_language_allowed"] is False


def test_ceo_frozen_validation_rerun_completion_routes_to_fresh_executor_gap(tmp_path: Path) -> None:
    result = ceo_ops.build_frozen_validation_rerun_result(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        grid={"families": [{"family_id": "family_a"}], "candidate_specs": [{"spec_id": "spec_a"}]},
        warnings=[],
        output_dir=tmp_path / "rerun",
        record_rows=3,
    )

    assert result["status"] == "adapter_rerun_completed_not_promotion_eligible"
    assert result["next_action"] == "run_fresh_withheld_validation_contract"
    assert result["product_language_allowed"] is False
    assert result["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_contract_ready_after_adapter_rerun(tmp_path: Path) -> None:
    contract = ceo_ops.build_fresh_withheld_validation_contract(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        frozen_plan={
            "validation_specs": [
                {"spec_id": "spec_a", "status": "ready_for_execution", "production_effect": "none"}
            ],
            "production_effect": "none",
        },
        rerun_result={
            "status": "adapter_rerun_completed_not_promotion_eligible",
            "record_rows": 3,
            "production_effect": "none",
        },
        fresh_data_preflight={"safe_to_run_fresh_validation": True, "production_effect": "none"},
    )

    assert contract["status"] == "fresh_withheld_validation_contract_ready"
    assert contract["next_action"] == "run_fresh_withheld_validation_executor"
    assert contract["pass_fail_thresholds"]["strict_referee_required"] is True
    assert contract["product_language_allowed"] is False
    assert contract["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_contract_writes_guarded_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "frozen_candidate_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "status": "frozen_validation_specs_ready",
                "validation_specs": [
                    {"spec_id": "spec_a", "status": "ready_for_execution", "production_effect": "none"}
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "frozen_validation_rerun_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_validation_rerun_v0",
                "status": "adapter_rerun_completed_not_promotion_eligible",
                "record_rows": 3,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "fresh_data_preflight.yaml").write_text(
        yaml.safe_dump({"safe_to_run_fresh_validation": True, "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_fresh_withheld_validation_contract(
        _authorized(options, "run_fresh_withheld_validation_contract")
    )

    contract = result["contract"]
    assert contract["status"] == "fresh_withheld_validation_contract_ready"
    assert contract["next_action"] == "run_fresh_withheld_validation_executor"
    assert contract["artifact_fingerprints"]["frozen_plan"]["exists"] is True
    assert contract["artifact_fingerprints"]["frozen_plan"]["sha256"]
    assert contract["artifact_fingerprints"]["rerun_result"]["exists"] is True
    assert contract["artifact_fingerprints"]["fresh_data_preflight"]["exists"] is True
    assert result["paths"]["contract"].exists()
    assert result["paths"]["report"].exists()
    assert result["action_result"]["decision"] == "run_fresh_withheld_validation_contract"
    assert result["action_result"]["action_taken"] == "fresh_withheld_validation_contract"
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_authority_functions_require_apply(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=False)

    with pytest.raises(ValueError, match="withheld-split-manifest requires --apply"):
        run_ceo_withheld_split_manifest(
            options,
            withheld_split_id="withheld_split_a",
            source_evidence_cutoff="2099-01-01",
        )
    with pytest.raises(ValueError, match="fresh-withheld-snapshot-manifest requires --apply"):
        run_ceo_fresh_withheld_snapshot_manifest(options)
    with pytest.raises(ValueError, match="fresh-withheld-snapshot-declare requires --apply"):
        run_ceo_fresh_withheld_snapshot_declare(
            options,
            snapshot_type="withheld",
            withheld_split_id="withheld_split_a",
            source_evidence_cutoff="2099-01-01",
            confirm_no_overlap=True,
        )


def test_ceo_withheld_split_manifest_writes_guarded_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)

    result = run_ceo_withheld_split_manifest(
        _authorized(options, "write_withheld_split_manifest"),
        withheld_split_id="withheld_split_a",
        source_evidence_cutoff="2099-01-01",
        description="holdout after discovery cutoff",
    )

    manifest = result["manifest"]
    assert manifest["status"] == "withheld_split_manifest_ready"
    assert manifest["withheld_split_id"] == "withheld_split_a"
    assert manifest["source_evidence_cutoff"] == "2099-01-01"
    assert manifest["blocked_reasons"] == []
    assert manifest["product_language_allowed"] is False
    assert manifest["production_effect"] == "none"
    assert result["paths"]["manifest"].exists()
    assert result["paths"]["report"].exists()
    assert result["action_result"]["decision"] == "write_withheld_split_manifest"
    assert result["action_result"]["action_taken"] == "withheld_split_manifest"
    assert result["action_result"]["meaningful_progress"] is True
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_withheld_split_manifest_blocks_invalid_cutoff(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)

    result = run_ceo_withheld_split_manifest(
        _authorized(options, "write_withheld_split_manifest"),
        withheld_split_id="withheld_split_a",
        source_evidence_cutoff="not-a-date",
    )

    manifest = result["manifest"]
    assert manifest["status"] == "blocked_invalid_withheld_split_manifest"
    assert "invalid_source_evidence_cutoff" in manifest["blocked_reasons"]
    assert manifest["product_language_allowed"] is False
    assert manifest["production_effect"] == "none"
    assert result["action_result"]["meaningful_progress"] is False


def test_ceo_fresh_withheld_validation_executor_blocks_without_snapshot_manifest(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "fresh_withheld_validation_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_withheld_validation_contract_v0",
                "status": "fresh_withheld_validation_contract_ready",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_fresh_withheld_validation_executor(
        _authorized(options, "run_fresh_withheld_validation_executor")
    )

    execution = result["execution"]
    assert execution["status"] == "blocked_missing_snapshot_manifest"
    assert execution["validation_completed"] is False
    assert execution["validation_result"] == "not_run"
    assert "missing_snapshot_manifest" in execution["blocked_reasons"]
    assert execution["product_language_allowed"] is False
    assert execution["production_effect"] == "none"
    assert result["paths"]["result"].exists()
    assert result["paths"]["report"].exists()
    assert result["action_result"]["decision"] == "run_fresh_withheld_validation_executor"
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_fresh_withheld_snapshot_manifest_writes_manual_authority_draft(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "fresh_withheld_validation_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_withheld_validation_contract_v0",
                "status": "fresh_withheld_validation_contract_ready",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "fresh_data_preflight.yaml").write_text(
        yaml.safe_dump(
            {
                "overall_status": "partial_ready",
                "safe_to_run_fresh_validation": True,
                "timeframes": [
                    {
                        "timeframe": "1d",
                        "assets": [
                            {
                                "symbol": "AAA",
                                "status": "ready",
                                "path": "data/raw/AAA_1d.csv",
                                "latest_date": "2099-01-03",
                                "row_count": 3,
                            }
                        ],
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_fresh_withheld_snapshot_manifest(
        _authorized(options, "run_fresh_withheld_snapshot_manifest")
    )

    manifest = result["manifest"]
    assert manifest["status"] == "draft_requires_manual_snapshot_authority"
    assert manifest["snapshot_type"] == ""
    assert manifest["overlap_with_source_evidence"] is None
    assert manifest["rule_shape_frozen"] is True
    assert manifest["active_asset_count"] == 1
    assert manifest["artifact_fingerprints"]["contract"]["exists"] is True
    assert result["paths"]["manifest"].exists()
    assert result["paths"]["report"].exists()
    assert result["action_result"]["decision"] == "run_fresh_withheld_snapshot_manifest"
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_fresh_withheld_snapshot_declare_requires_no_overlap_confirmation(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)

    result = run_ceo_fresh_withheld_snapshot_declare(
        _authorized(options, "declare_fresh_withheld_snapshot_authority"),
        snapshot_type="withheld",
        withheld_split_id="split_a",
        source_evidence_cutoff="2099-01-01",
        confirm_no_overlap=False,
    )

    manifest = result["manifest"]
    assert manifest["status"] == "draft_requires_manual_snapshot_authority"
    assert "no_overlap_not_confirmed" in manifest["blocked_reasons"]
    assert manifest["overlap_with_source_evidence"] is None
    assert manifest["product_language_allowed"] is False
    assert manifest["production_effect"] == "none"


def test_ceo_fresh_withheld_snapshot_declare_marks_withheld_authority_ready(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)

    result = run_ceo_fresh_withheld_snapshot_declare(
        _authorized(options, "declare_fresh_withheld_snapshot_authority"),
        snapshot_type="withheld",
        withheld_split_id="withheld_split_a",
        source_evidence_cutoff="2099-01-01",
        confirm_no_overlap=True,
    )

    manifest = result["manifest"]
    assert manifest["status"] == "snapshot_authority_ready"
    assert manifest["snapshot_type"] == "withheld"
    assert manifest["withheld_split_id"] == "withheld_split_a"
    assert manifest["withheld_split_manifest_valid"] is True
    assert manifest["source_evidence_cutoff"] == "2099-01-01"
    assert manifest["overlap_with_source_evidence"] is False
    assert manifest["next_action"] == "run_fresh_withheld_validation_executor"
    assert result["action_result"]["status"] == "snapshot_authority_ready"
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_fresh_withheld_snapshot_declare_requires_withheld_split_manifest(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)
    (root / "withheld_split_manifest.yaml").unlink()

    result = run_ceo_fresh_withheld_snapshot_declare(
        _authorized(options, "declare_fresh_withheld_snapshot_authority"),
        snapshot_type="withheld",
        withheld_split_id="withheld_split_a",
        source_evidence_cutoff="2099-01-01",
        confirm_no_overlap=True,
    )

    manifest = result["manifest"]
    assert manifest["status"] == "draft_requires_manual_snapshot_authority"
    assert "missing_withheld_split_manifest" in manifest["blocked_reasons"]
    assert manifest["withheld_split_manifest_valid"] is False
    assert manifest["production_effect"] == "none"


def test_ceo_fresh_withheld_snapshot_declare_requires_ready_withheld_split_manifest(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)
    split_manifest_path = root / "withheld_split_manifest.yaml"
    split_manifest = yaml.safe_load(split_manifest_path.read_text(encoding="utf-8"))
    split_manifest["status"] = "blocked_invalid_withheld_split_manifest"
    split_manifest_path.write_text(yaml.safe_dump(split_manifest), encoding="utf-8")

    result = run_ceo_fresh_withheld_snapshot_declare(
        _authorized(options, "declare_fresh_withheld_snapshot_authority"),
        snapshot_type="withheld",
        withheld_split_id="withheld_split_a",
        source_evidence_cutoff="2099-01-01",
        confirm_no_overlap=True,
    )

    manifest = result["manifest"]
    assert manifest["status"] == "draft_requires_manual_snapshot_authority"
    assert "withheld_split_manifest_not_ready" in manifest["blocked_reasons"]
    assert manifest["withheld_split_manifest_valid"] is False
    assert manifest["production_effect"] == "none"


def test_ceo_fresh_withheld_snapshot_declare_blocks_stale_fresh_cutoff(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)
    manifest_path = root / "fresh_withheld_snapshot_manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["active_assets"] = [{"timeframe": "1d", "symbol": "AAA", "latest_date": "2099-01-03"}]
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    result = run_ceo_fresh_withheld_snapshot_declare(
        _authorized(options, "declare_fresh_withheld_snapshot_authority"),
        snapshot_type="fresh",
        snapshot_cutoff="2099-01-04",
        source_evidence_cutoff="2099-01-01",
        confirm_no_overlap=True,
    )

    manifest = result["manifest"]
    assert manifest["status"] == "draft_requires_manual_snapshot_authority"
    assert "active_assets_older_than_snapshot_cutoff" in manifest["blocked_reasons"]
    assert manifest["product_language_allowed"] is False
    assert manifest["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_execution_result_completes_shadow_only_after_valid_manifest(tmp_path: Path) -> None:
    result = ceo_ops.build_fresh_withheld_validation_execution_result(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        contract={"status": "fresh_withheld_validation_contract_ready", "production_effect": "none"},
        snapshot_manifest={
            "status": "ready",
            "snapshot_type": "withheld",
            "withheld_split_id": "withheld_split_a",
            "withheld_split_manifest_valid": True,
            "source_evidence_cutoff": "2099-01-01",
            "overlap_with_source_evidence": False,
            "rule_shape_frozen": True,
            "active_assets": [{"timeframe": "1d", "symbol": "AAA"}],
            "production_effect": "none",
        },
    )

    assert result["status"] == "fresh_withheld_validation_executed_shadow_only"
    assert result["snapshot_manifest_valid"] is True
    assert result["blocked_reasons"] == []
    assert result["validation_completed"] is True
    assert result["validation_result"] == "fresh_withheld_execution_shadow_only_not_promotion_eligible"
    assert result["product_language_allowed"] is False
    assert result["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_execution_result_blocks_stale_fresh_manifest() -> None:
    result = ceo_ops.build_fresh_withheld_validation_execution_result(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        contract={"status": "fresh_withheld_validation_contract_ready", "production_effect": "none"},
        snapshot_manifest={
            "status": "snapshot_authority_ready",
            "snapshot_type": "fresh",
            "snapshot_cutoff": "2099-01-04",
            "source_evidence_cutoff": "2099-01-01",
            "overlap_with_source_evidence": False,
            "rule_shape_frozen": True,
            "active_assets": [{"timeframe": "1d", "symbol": "AAA", "latest_date": "2099-01-03"}],
            "production_effect": "none",
        },
    )

    assert result["status"] == "blocked_invalid_snapshot_manifest"
    assert result["snapshot_manifest_valid"] is False
    assert "active_assets_older_than_snapshot_cutoff" in result["blocked_reasons"]
    assert result["validation_completed"] is False
    assert result["production_effect"] == "none"


def test_ceo_cli_direct_validation_executor_obeys_preflight_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: blocked\n", encoding="utf-8")
    preflight_report_path.write_text("# blocked\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {
                "status": "blocked",
                "safe_to_execute": False,
                "blockers": [{"blocker": "pending_user_approval", "source": "approval_queue.yaml"}],
            },
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fail_executor(_options):
        raise AssertionError("direct validation executor must not run through a failed preflight gate")

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_fresh_withheld_validation_executor", fail_executor)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="fresh-withheld-validation-executor",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 1


@pytest.mark.parametrize(
    ("ceo_action", "handler_name"),
    [
        ("promotion-proposal", "run_ceo_promotion_proposal"),
        ("evidence-debt-register", "run_ceo_evidence_debt_register"),
    ],
)
def test_ceo_cli_direct_evidence_authority_commands_obey_preflight_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ceo_action: str,
    handler_name: str,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: blocked\n", encoding="utf-8")
    preflight_report_path.write_text("# blocked\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {
                "status": "blocked",
                "safe_to_execute": False,
                "blockers": [{"blocker": "guardrail_audit_failed", "source": "guardrail_audit.yaml"}],
            },
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fail_handler(_options):
        raise AssertionError(f"direct {ceo_action} must not run through a failed preflight gate")

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, handler_name, fail_handler)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action=ceo_action,
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 1


def test_ceo_cli_guarded_direct_command_passes_context_after_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: pass\n", encoding="utf-8")
    preflight_report_path.write_text("# pass\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {"status": "pass", "safe_to_execute": True, "blockers": []},
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fake_register(options):
        assert options.ceo_context == "guarded_direct"
        assert options.ceo_authorized_action == "evidence-debt-register"
        return {
            "register": {"status": "open_evidence_debt", "debt_count": 0, "next_action": "none"},
            "paths": {
                "register": preflight_path.parent / "evidence_debt_register.yaml",
                "register_report": preflight_path.parent / "evidence_debt_register.md",
            },
        }

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_evidence_debt_register", fake_register)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="evidence-debt-register",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 0


def test_ceo_cli_fresh_data_preflight_passes_guarded_context_after_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: pass\n", encoding="utf-8")
    preflight_report_path.write_text("# pass\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {"status": "pass", "safe_to_execute": True, "blockers": []},
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fake_fresh_data_preflight(options):
        assert options.ceo_context == "guarded_direct"
        assert options.ceo_authorized_action == "fresh-data-preflight"
        return {
            "preflight": {
                "overall_status": "partial_ready",
                "safe_to_run_fresh_validation": True,
                "next_action": "run_frozen_candidate_validation",
            },
            "paths": {
                "preflight": preflight_path.parent / "fresh_data_preflight.yaml",
                "report": preflight_path.parent / "fresh_data_preflight.md",
            },
        }

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_fresh_data_preflight", fake_fresh_data_preflight)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="fresh-data-preflight",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 0


def test_ceo_cli_approval_apply_inspects_preflight_before_guarded_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: blocked\n", encoding="utf-8")
    preflight_report_path.write_text("# pending approval\n", encoding="utf-8")

    calls: list[str] = []

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        calls.append("preflight")
        return {
            "preflight_gate": {
                "status": "blocked",
                "safe_to_execute": False,
                "blockers": [{"blocker": "pending_user_approval", "source": "approval_queue.yaml"}],
            },
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fake_approval_apply(options, *, approval_id, user_confirmed=False):
        assert calls == ["preflight"]
        assert options.ceo_context == "guarded_direct"
        assert options.ceo_authorized_action == "approval-apply"
        assert approval_id == "promotion_proposal"
        assert user_confirmed is True
        return {
            "approval_apply": {
                "status": "promotion_approval_closed_shadow_only",
                "action_taken": "promotion_approval_closure_recorded",
            },
            "paths": {
                "approval_apply": preflight_path.parent / "approval_apply_promotion_proposal.yaml",
                "approval_apply_report": preflight_path.parent / "approval_apply_promotion_proposal.md",
            },
        }

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_approval_apply", fake_approval_apply)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="approval-apply",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            approval_id="promotion_proposal",
            user_confirmed=True,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 0


def test_ceo_cli_approval_apply_blocks_unrelated_preflight_blockers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: blocked\n", encoding="utf-8")
    preflight_report_path.write_text("# guardrail failed\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {
                "status": "blocked",
                "safe_to_execute": False,
                "blockers": [{"blocker": "guardrail_audit_failed", "source": "guardrail_audit.yaml"}],
            },
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fail_approval_apply(*_args, **_kwargs):
        raise AssertionError("approval-apply must not run through unrelated preflight blockers")

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_approval_apply", fail_approval_apply)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="approval-apply",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            approval_id="promotion_proposal",
            user_confirmed=True,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 1


def test_ceo_cli_snapshot_declare_obeys_preflight_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: blocked\n", encoding="utf-8")
    preflight_report_path.write_text("# blocked\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {
                "status": "blocked",
                "safe_to_execute": False,
                "blockers": [{"blocker": "stop_requested", "source": "stop.request"}],
            },
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fail_declare(*_args, **_kwargs):
        raise AssertionError("snapshot authority declaration must not bypass a failed preflight gate")

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_fresh_withheld_snapshot_declare", fail_declare)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="fresh-withheld-snapshot-declare",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            snapshot_type="withheld",
            snapshot_cutoff="",
            withheld_split_id="withheld_split_a",
            source_evidence_cutoff="2099-01-01",
            confirm_no_overlap=True,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 1


def test_ceo_cli_snapshot_declare_requires_apply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: pass\n", encoding="utf-8")
    preflight_report_path.write_text("# pass\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {"status": "pass", "safe_to_execute": True, "blockers": []},
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fail_declare(*_args, **_kwargs):
        raise AssertionError("snapshot authority declaration must require explicit --apply")

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_fresh_withheld_snapshot_declare", fail_declare)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="fresh-withheld-snapshot-declare",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            snapshot_type="withheld",
            snapshot_cutoff="",
            withheld_split_id="withheld_split_a",
            source_evidence_cutoff="2099-01-01",
            confirm_no_overlap=True,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=False,
        )
    )

    assert status == 1


def test_ceo_fresh_withheld_validation_execution_result_blocks_missing_withheld_split_authority() -> None:
    result = ceo_ops.build_fresh_withheld_validation_execution_result(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        contract={"status": "fresh_withheld_validation_contract_ready", "production_effect": "none"},
        snapshot_manifest={
            "status": "snapshot_authority_ready",
            "snapshot_type": "withheld",
            "withheld_split_id": "withheld_split_a",
            "withheld_split_manifest_valid": False,
            "source_evidence_cutoff": "2099-01-01",
            "overlap_with_source_evidence": False,
            "rule_shape_frozen": True,
            "active_assets": [{"timeframe": "1d", "symbol": "AAA"}],
            "production_effect": "none",
        },
    )

    assert result["status"] == "blocked_invalid_snapshot_manifest"
    assert result["snapshot_manifest_valid"] is False
    assert "missing_withheld_split_manifest_authority" in result["blocked_reasons"]
    assert result["validation_completed"] is False
    assert result["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_execution_result_blocks_weak_manifest_authority(tmp_path: Path) -> None:
    result = ceo_ops.build_fresh_withheld_validation_execution_result(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        contract={"status": "fresh_withheld_validation_contract_ready", "production_effect": "none"},
        snapshot_manifest={
            "status": "draft_requires_manual_snapshot_authority",
            "snapshot_type": "withheld",
            "overlap_with_source_evidence": False,
            "rule_shape_frozen": True,
            "production_effect": "none",
        },
    )

    assert result["status"] == "blocked_invalid_snapshot_manifest"
    assert result["snapshot_manifest_valid"] is False
    assert "snapshot_manifest_status_not_ready" in result["blocked_reasons"]
    assert "snapshot_manifest_has_no_active_assets" in result["blocked_reasons"]
    assert "missing_snapshot_authority_reference" in result["blocked_reasons"]
    assert "missing_source_evidence_boundary" in result["blocked_reasons"]
    assert result["validation_completed"] is False
    assert result["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_executor_blocks_valid_manifest_without_grid(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root, include_grid=False)

    result = run_ceo_fresh_withheld_validation_executor(
        _authorized(options, "run_fresh_withheld_validation_executor")
    )

    execution = result["execution"]
    assert execution["status"] == "blocked_missing_rerun_grid"
    assert "missing_frozen_validation_rerun_grid" in execution["blocked_reasons"]
    assert execution["validation_completed"] is False
    assert execution["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_executor_runs_frozen_grid_shadow_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)

    monkeypatch.setattr(
        ceo_ops,
        "load_analysis_frames_by_timeframe",
        lambda **_kwargs: (SimpleNamespace(benchmark=SimpleNamespace(name="MEME_BASKET")), {"1d": [object()]}, []),
    )
    monkeypatch.setattr(
        ceo_ops,
        "run_grammar_search",
        lambda *_args, **_kwargs: (
            pd.DataFrame([{"variant_id": "variant_a"}]),
            pd.DataFrame(
                [
                    {"variant_id": "variant_a", "symbol": "AAA", "event_cluster_id": "c1"},
                    {"variant_id": "variant_a", "symbol": "BBB", "event_cluster_id": "c2"},
                    {"variant_id": "variant_a", "symbol": "AAA", "event_cluster_id": "c3"},
                ]
            ),
            pd.DataFrame(
                [
                    {
                        "variant_id": "variant_a",
                        "score": 1.0,
                        "median_forward_relative_return_secondary": 0.08,
                        "entry_lag_bars": 1,
                        "cooldown_bars": 30,
                        "lag_sensitivity_status": "passed",
                        "cooldown_sensitivity_status": "passed",
                    }
                ]
            ),
            pd.DataFrame([{"family_id": "family_a"}]),
            ["variant_a"],
        ),
    )
    monkeypatch.setattr(
        ceo_ops,
        "strict_baseline_referee",
        lambda *_args, **_kwargs: pd.DataFrame(
            [{"variant_id": "variant_a", "strict_survivor": True, "matched_null_p_value": 0.01}]
        ),
    )

    result = run_ceo_fresh_withheld_validation_executor(
        _authorized(options, "run_fresh_withheld_validation_executor")
    )

    execution = result["execution"]
    assert execution["status"] == "fresh_withheld_validation_executed_shadow_only"
    assert execution["validation_completed"] is True
    assert execution["validation_result"] == "fresh_withheld_validation_passed_shadow_only_not_promotion_eligible"
    assert execution["threshold_results"]["status"] == "passed"
    assert execution["record_rows"] == 3
    assert execution["strict_referee_rows"] == 1
    assert execution["product_language_allowed"] is False
    assert execution["production_effect"] == "none"
    assert (result["paths"]["result"].parent / "fresh_withheld_validation_execution" / "records.csv").exists()


def test_ceo_fresh_withheld_validation_executor_fails_shadow_thresholds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)

    monkeypatch.setattr(
        ceo_ops,
        "load_analysis_frames_by_timeframe",
        lambda **_kwargs: (SimpleNamespace(benchmark=SimpleNamespace(name="MEME_BASKET")), {"1d": [object()]}, []),
    )
    monkeypatch.setattr(
        ceo_ops,
        "run_grammar_search",
        lambda *_args, **_kwargs: (
            pd.DataFrame([{"variant_id": "variant_a"}]),
            pd.DataFrame([{"variant_id": "variant_a", "symbol": "AAA", "event_cluster_id": "c1"}]),
            pd.DataFrame([{"variant_id": "variant_a", "score": 1.0}]),
            pd.DataFrame([{"family_id": "family_a"}]),
            ["variant_a"],
        ),
    )
    monkeypatch.setattr(
        ceo_ops,
        "strict_baseline_referee",
        lambda *_args, **_kwargs: pd.DataFrame([{"variant_id": "variant_a", "strict_survivor": False}]),
    )

    result = run_ceo_fresh_withheld_validation_executor(
        _authorized(options, "run_fresh_withheld_validation_executor")
    )

    execution = result["execution"]
    assert execution["status"] == "fresh_withheld_validation_failed_thresholds"
    assert execution["validation_completed"] is False
    assert execution["validation_result"] == "fresh_withheld_validation_failed_thresholds"
    assert execution["threshold_results"]["status"] == "failed"
    assert execution["threshold_results"]["distinct_symbols"] == 1
    assert execution["threshold_results"]["event_clusters"] == 1
    assert execution["product_language_allowed"] is False
    assert execution["production_effect"] == "none"


def test_ceo_fresh_withheld_thresholds_fail_bad_matched_null_and_directional_result() -> None:
    result = ceo_ops.build_fresh_withheld_threshold_results(
        contract={
            "pass_fail_thresholds": {
                "strict_referee_required": True,
                "matched_null_required": True,
                "matched_null_max_p_value": 0.05,
                "directional_forward_relative_return_required": True,
                "min_forward_relative_return": 0.0,
            }
        },
        records=pd.DataFrame(
            [
                {"symbol": "AAA", "event_cluster_id": "c1"},
                {"symbol": "BBB", "event_cluster_id": "c2"},
            ]
        ),
        ranked=pd.DataFrame(
            [
                {
                    "variant_id": "variant_a",
                    "median_forward_relative_return_secondary": -0.02,
                }
            ]
        ),
        strict=pd.DataFrame(
            [
                {
                    "variant_id": "variant_a",
                    "strict_survivor": True,
                    "matched_null_p_value": 0.25,
                }
            ]
        ),
    )

    checks = {item["name"]: item for item in result["checks"]}
    assert result["status"] == "failed"
    assert checks["strict_referee_survivor"]["passed"] is True
    assert checks["matched_null_evaluated"]["passed"] is False
    assert checks["directional_forward_relative_return"]["passed"] is False


def test_ceo_fresh_withheld_thresholds_fail_explicit_lag_or_cooldown_failure() -> None:
    result = ceo_ops.build_fresh_withheld_threshold_results(
        contract={
            "pass_fail_thresholds": {
                "strict_referee_required": True,
                "lag_sensitivity_required": True,
                "cooldown_sensitivity_required": True,
            }
        },
        records=pd.DataFrame(
            [
                {"symbol": "AAA", "event_cluster_id": "c1"},
                {"symbol": "BBB", "event_cluster_id": "c2"},
            ]
        ),
        ranked=pd.DataFrame(
            [
                {
                    "variant_id": "variant_a",
                    "entry_lag_bars": 1,
                    "cooldown_bars": 30,
                    "lag_sensitivity_status": "failed",
                    "cooldown_sensitivity_status": "passed",
                }
            ]
        ),
        strict=pd.DataFrame([{"variant_id": "variant_a", "strict_survivor": True}]),
    )

    checks = {item["name"]: item for item in result["checks"]}
    assert result["status"] == "failed"
    assert checks["lag_sensitivity_evaluated"]["passed"] is False
    assert checks["cooldown_sensitivity_evaluated"]["passed"] is True


def test_ceo_fresh_withheld_thresholds_fail_required_presence_only_controls() -> None:
    result = ceo_ops.build_fresh_withheld_threshold_results(
        contract={
            "pass_fail_thresholds": {
                "strict_referee_required": True,
                "matched_null_required": True,
                "lag_sensitivity_required": True,
                "cooldown_sensitivity_required": True,
            }
        },
        records=pd.DataFrame(
            [
                {"symbol": "AAA", "event_cluster_id": "c1"},
                {"symbol": "BBB", "event_cluster_id": "c2"},
            ]
        ),
        ranked=pd.DataFrame(
            [
                {
                    "variant_id": "variant_a",
                    "entry_lag_bars": 1,
                    "cooldown_bars": 30,
                }
            ]
        ),
        strict=pd.DataFrame(
            [
                {
                    "variant_id": "variant_a",
                    "strict_survivor": True,
                    "matched_null_delta": 0.1,
                }
            ]
        ),
    )

    checks = {item["name"]: item for item in result["checks"]}
    assert result["status"] == "failed"
    assert checks["matched_null_evaluated"]["observed"]["evaluated"] is True
    assert checks["matched_null_evaluated"]["passed"] is False
    assert checks["lag_sensitivity_evaluated"]["observed"]["evaluated"] is True
    assert checks["lag_sensitivity_evaluated"]["passed"] is False
    assert checks["cooldown_sensitivity_evaluated"]["observed"]["evaluated"] is True
    assert checks["cooldown_sensitivity_evaluated"]["passed"] is False


def test_ceo_fresh_withheld_validation_executor_blocks_drifted_frozen_grid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)
    (root / "frozen_validation_rerun_grid.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_grammar_search_grid_v0", "families": []}),
        encoding="utf-8",
    )

    def fail_grammar_search(*_args, **_kwargs):
        raise AssertionError("executor must not run grammar search after artifact drift")

    monkeypatch.setattr(ceo_ops, "run_grammar_search", fail_grammar_search)

    result = run_ceo_fresh_withheld_validation_executor(
        _authorized(options, "run_fresh_withheld_validation_executor")
    )

    execution = result["execution"]
    assert execution["status"] == "blocked_artifact_fingerprint_mismatch"
    assert "artifact_fingerprint_mismatch" in execution["blocked_reasons"]
    assert execution["artifact_fingerprint_mismatches"][0]["artifact"] == "rerun_grid"
    assert execution["validation_completed"] is False
    assert execution["production_effect"] == "none"


def test_ceo_fresh_withheld_validation_executor_blocks_mutated_active_asset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_fresh_withheld_executor_inputs(root)
    active_asset_path = root / "AAA_1d.csv"
    active_asset_path.write_text(
        "\n".join(
            [
                "date,open,high,low,close,volume",
                "2099-01-01,1,2,1,2,100",
                "2099-01-02,2,3,2,99,120",
                "2099-01-03,3,4,3,4,130",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_grammar_search(*_args, **_kwargs):
        raise AssertionError("executor must not run grammar search after active asset data drift")

    monkeypatch.setattr(ceo_ops, "run_grammar_search", fail_grammar_search)

    result = run_ceo_fresh_withheld_validation_executor(
        _authorized(options, "run_fresh_withheld_validation_executor")
    )

    execution = result["execution"]
    assert execution["status"] == "blocked_artifact_fingerprint_mismatch"
    assert "artifact_fingerprint_mismatch" in execution["blocked_reasons"]
    assert execution["artifact_fingerprint_mismatches"][0]["reason"] == "active_asset_fingerprint_mismatch"
    assert execution["validation_completed"] is False
    assert execution["production_effect"] == "none"


def test_ceo_promotion_proposal_blocks_without_completed_validation(tmp_path: Path) -> None:
    config_path = tmp_path / "configs" / "test_universe.yaml"
    data_dir = tmp_path / "data" / "raw"
    _write_test_universe(config_path, min_active_members=2)
    _write_ohlcv_csv(data_dir / "AAA_1d.csv")
    _write_ohlcv_csv(data_dir / "BBB_1d.csv")
    options = replace(
        _options(tmp_path, apply=True),
        config_path=config_path,
        data_dir=data_dir,
        timeframes=("1d",),
    )
    root = options.report_root / "ceo_test"
    _write_fresh_control_plan(root)
    run_ceo_fresh_data_preflight(_authorized(options, "request_fresh_data"))
    run_ceo_frozen_candidate_validation(_authorized(options, "run_frozen_candidate_validation"))

    result = run_ceo_promotion_proposal(_authorized(options, "promotion-proposal"))

    proposal = result["proposal"]
    assert proposal["status"] == "blocked_missing_promotion_evidence"
    assert proposal["approval_required"] is True
    assert "completed_fresh_or_frozen_validation" in proposal["missing_evidence"]
    assert "passing_validation_result" in proposal["missing_evidence"]
    assert proposal["product_language_allowed"] is False
    assert proposal["production_effect"] == "none"
    assert result["paths"]["proposal"].exists()
    assert result["paths"]["proposal_report"].exists()


def test_ceo_evidence_debt_register_tracks_candidate_blockers_across_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)

    result = run_ceo_evidence_debt_register(_authorized(options, "evidence-debt-register"))

    register = result["register"]
    assert result["paths"]["register"].exists()
    assert result["paths"]["register_report"].exists()
    assert register["status"] == "open_evidence_debt"
    assert register["debt_count"] > 0
    assert register["product_language_allowed"] is False
    assert register["production_effect"] == "none"
    candidate_debts = [
        debt
        for debt in register["debts"]
        if debt.get("candidate_id") == "lower_high_rollover_warning_4h"
    ]
    assert candidate_debts
    fresh_control_debt = next(
        debt for debt in candidate_debts if debt["debt_kind"] == "fresh_control_validation_plan"
    )
    assert fresh_control_debt["blocking_artifact"] == "fresh_control_validation_plan.yaml"
    assert fresh_control_debt["owner_command"] == "riskflow ceo fresh-control-validation"
    assert fresh_control_debt["blocks_promotion"] is True
    assert fresh_control_debt["production_effect"] == "none"


def test_ceo_evidence_debt_register_routes_source_replay_to_fresh_validation(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "frozen_candidate_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "status": "frozen_validation_specs_ready",
                "validation_completed": True,
                "validation_result": "source_replay_only_not_promotion_eligible",
                "execution_status": "source_replay_completed",
                "validation_specs": [],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "blocked_missing_promotion_evidence",
                "missing_evidence": ["passing_validation_result"],
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_evidence_debt_register(_authorized(options, "evidence-debt-register"))

    debt = result["register"]["debts"][0]
    assert debt["debt_kind"] == "promotion_missing_passing_validation_result"
    assert debt["owner_command"] == "run_frozen_validation_rerun"
    assert debt["blocker_type"] == "fresh_or_withheld_validation_required"
    assert debt["production_effect"] == "none"


def test_ceo_evidence_debt_register_routes_shadow_execution_to_result_review(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "frozen_candidate_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "status": "frozen_validation_specs_ready",
                "validation_completed": False,
                "validation_result": "source_replay_only_not_promotion_eligible",
                "validation_specs": [],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "fresh_withheld_validation_execution_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_withheld_validation_execution_v0",
                "status": "fresh_withheld_validation_executed_shadow_only",
                "validation_completed": True,
                "validation_result": "fresh_withheld_execution_shadow_only_not_promotion_eligible",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "blocked_missing_promotion_evidence",
                "missing_evidence": ["passing_validation_result"],
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_evidence_debt_register(_authorized(options, "evidence-debt-register"))

    debt = result["register"]["debts"][0]
    assert debt["debt_kind"] == "promotion_missing_passing_validation_result"
    assert debt["owner_command"] == "review_shadow_validation_results_and_predeclare_passing_thresholds"
    assert debt["blocker_type"] == "shadow_validation_not_promotion_eligible"
    assert debt["blocking_artifact"] == "fresh_withheld_validation_execution_result.yaml"
    assert debt["production_effect"] == "none"


def test_ceo_promotion_proposal_ready_still_requires_user_approval() -> None:
    proposal = build_ceo_promotion_proposal(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        frozen_plan={
            "validation_completed": True,
            "validation_result": "source_replay_only_not_promotion_eligible",
            "validation_specs": [
                {
                    "belief_id": "candidate_a",
                    "product_role": "reset_quality",
                    "champion": "core_signal_v0",
                    "challenger": "core_signal_v0_plus_candidate_a",
                    "status": "ready_for_execution",
                }
            ],
        },
        fresh_withheld_execution={
            "status": "fresh_withheld_validation_executed_shadow_only",
            "validation_completed": True,
            "validation_result": "fresh_withheld_validation_passed_shadow_only_not_promotion_eligible",
            "threshold_results": {"status": "passed"},
            "production_effect": "none",
        },
        champion_results={"results": [{"belief_id": "candidate_a", "decision": "shadow_challenger_promising_needs_fresh_validation"}]},
        visual_queue={"items": [{"belief_id": "candidate_a", "review_status": "ready_for_visual_review"}]},
        fresh_data_preflight={"safe_to_run_fresh_validation": True},
        trace_grade={"verdict": "pass"},
        specialist_review_gate={
            "status": "passed",
            "passed": True,
            "accepted_roles": ["product_translator", "validation_referee"],
            "production_effect": "none",
        },
    )

    assert proposal["status"] == "ready_for_user_approval"
    assert proposal["validation_passed"] is True
    assert proposal["approval_required"] is True
    assert proposal["product_language_allowed"] is False
    assert proposal["production_effect"] == "none"


def test_ceo_promotion_proposal_builder_blocks_without_specialist_gate() -> None:
    proposal = build_ceo_promotion_proposal(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        frozen_plan={
            "validation_specs": [{"belief_id": "candidate_a", "product_role": "reset_quality", "status": "ready_for_execution"}],
        },
        fresh_withheld_execution={
            "validation_completed": True,
            "validation_result": "fresh_withheld_validation_passed_shadow_only_not_promotion_eligible",
            "threshold_results": {"status": "passed"},
            "production_effect": "none",
        },
        champion_results={"results": [{"belief_id": "candidate_a", "decision": "shadow_challenger_promising_needs_fresh_validation"}]},
        visual_queue={"items": [{"belief_id": "candidate_a", "review_status": "ready_for_visual_review"}]},
        fresh_data_preflight={"safe_to_run_fresh_validation": True},
        trace_grade={"verdict": "pass"},
    )

    assert proposal["status"] == "blocked_missing_promotion_evidence"
    assert "completed_specialist_reviews" in proposal["missing_evidence"]
    assert proposal["specialist_review_gate"]["status"] == "not_evaluated"


def _write_promotion_ready_inputs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "frozen_candidate_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "validation_specs": [
                    {
                        "belief_id": "candidate_a",
                        "product_role": "warning_blocker",
                        "status": "ready_for_execution",
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "fresh_withheld_validation_execution_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_withheld_validation_execution_v0",
                "validation_completed": True,
                "validation_result": "fresh_withheld_validation_passed_shadow_only_not_promotion_eligible",
                "threshold_results": {"status": "passed"},
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "champion_challenger_results.yaml").write_text(
        yaml.safe_dump({"results": [{"belief_id": "candidate_a", "decision": "shadow_challenger_promising_needs_fresh_validation"}]}),
        encoding="utf-8",
    )
    (root / "champion_challenger_visual_review_queue.yaml").write_text(
        yaml.safe_dump({"items": [{"belief_id": "candidate_a", "review_status": "ready_for_visual_review"}]}),
        encoding="utf-8",
    )
    (root / "fresh_data_preflight.yaml").write_text(
        yaml.safe_dump({"safe_to_run_fresh_validation": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "trace_grade.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_trace_grade_v0", "verdict": "pass", "production_effect": "none"}),
        encoding="utf-8",
    )


def test_ceo_promotion_proposal_run_requires_specialist_reviews(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_promotion_ready_inputs(root)
    (root / "role_task_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_task_queue_v0",
                "tasks": [],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_promotion_proposal(_authorized(options, "promotion-proposal"))

    proposal = result["proposal"]
    assert proposal["status"] == "blocked_missing_promotion_evidence"
    assert "completed_specialist_reviews" in proposal["missing_evidence"]
    assert proposal["specialist_review_gate"]["status"] == "missing_specialist_reviews"
    assert proposal["production_effect"] == "none"


def test_ceo_promotion_proposal_requires_passing_specialist_review_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_promotion_ready_inputs(root)
    (root / "validation_review.yaml").write_text(
        yaml.safe_dump(
            {
                "role_id": "validation_referee",
                "task_id": "validation_task",
                "review_status": "blocked",
                "decision": "reject",
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "role_task_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_task_queue_v0",
                "tasks": [
                    {
                        "task_id": "validation_task",
                        "role_id": "validation_referee",
                        "status": "complete",
                        "result_path": "validation_review.yaml",
                    },
                    {
                        "task_id": "product_task",
                        "role_id": "product_translator",
                        "status": "complete",
                        "result_path": "missing_product_review.yaml",
                    },
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_promotion_proposal(_authorized(options, "promotion-proposal"))

    gate = result["proposal"]["specialist_review_gate"]
    assert result["proposal"]["status"] == "blocked_missing_promotion_evidence"
    assert "completed_specialist_reviews" in result["proposal"]["missing_evidence"]
    assert gate["passed"] is False
    assert gate["rejected_review_count"] == 2
    assert {item["status"] for item in gate["review_results"]} == {"rejected", "missing_review_artifact"}


def test_ceo_promotion_proposal_accepts_structured_specialist_reviews(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_promotion_ready_inputs(root)
    (root / "validation_review.yaml").write_text(
        yaml.safe_dump(
            {
                "role_id": "validation_referee",
                "task_id": "validation_task",
                "review_status": "passed",
                "decision": "approved",
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "product_review.yaml").write_text(
        yaml.safe_dump(
            {
                "role_id": "product_translator",
                "task_id": "product_task",
                "review_status": "passed",
                "decision": "approved",
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "role_task_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_task_queue_v0",
                "tasks": [
                    {
                        "task_id": "validation_task",
                        "role_id": "validation_referee",
                        "status": "complete",
                        "result_path": "validation_review.yaml",
                    },
                    {
                        "task_id": "product_task",
                        "role_id": "product_translator",
                        "status": "complete",
                        "result_path": "product_review.yaml",
                    },
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_promotion_proposal(_authorized(options, "promotion-proposal"))

    proposal = result["proposal"]
    assert proposal["status"] == "ready_for_user_approval"
    assert proposal["specialist_review_gate"]["status"] == "passed"
    assert proposal["specialist_review_gate"]["accepted_roles"] == ["product_translator", "validation_referee"]
    assert proposal["product_language_allowed"] is False
    assert proposal["production_effect"] == "none"


def test_ceo_promotion_proposal_reads_fresh_withheld_execution_without_promoting() -> None:
    proposal = build_ceo_promotion_proposal(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        frozen_plan={
            "validation_completed": False,
            "validation_result": "source_replay_only_not_promotion_eligible",
            "validation_specs": [
                {
                    "belief_id": "candidate_a",
                    "product_role": "reset_quality",
                    "status": "ready_for_execution",
                }
            ],
        },
        fresh_withheld_execution={
            "status": "fresh_withheld_validation_executed_shadow_only",
            "validation_completed": True,
            "validation_result": "fresh_withheld_execution_shadow_only_not_promotion_eligible",
            "production_effect": "none",
        },
        champion_results={"results": [{"belief_id": "candidate_a", "decision": "shadow_challenger_promising_needs_fresh_validation"}]},
        visual_queue={"items": [{"belief_id": "candidate_a", "review_status": "ready_for_visual_review"}]},
        fresh_data_preflight={"safe_to_run_fresh_validation": True},
        trace_grade={"verdict": "pass"},
    )

    assert proposal["validation_completed"] is True
    assert "completed_fresh_or_frozen_validation" not in proposal["missing_evidence"]
    assert "passing_validation_result" in proposal["missing_evidence"]
    assert proposal["status"] == "blocked_missing_promotion_evidence"
    assert proposal["product_language_allowed"] is False


def test_ceo_promotion_proposal_blocks_fabricated_frozen_pass_without_fresh_withheld_execution() -> None:
    proposal = build_ceo_promotion_proposal(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        frozen_plan={
            "validation_completed": True,
            "validation_result": "passed",
            "validation_specs": [
                {
                    "belief_id": "candidate_a",
                    "product_role": "reset_quality",
                    "status": "ready_for_execution",
                }
            ],
        },
        fresh_withheld_execution={},
        champion_results={"results": [{"belief_id": "candidate_a", "decision": "shadow_challenger_promising_needs_fresh_validation"}]},
        visual_queue={"items": [{"belief_id": "candidate_a", "review_status": "ready_for_visual_review"}]},
        fresh_data_preflight={"safe_to_run_fresh_validation": True},
        trace_grade={"verdict": "pass"},
    )

    assert proposal["status"] == "blocked_missing_promotion_evidence"
    assert proposal["validation_completed"] is False
    assert proposal["validation_passed"] is False
    assert "completed_fresh_or_frozen_validation" in proposal["missing_evidence"]
    assert "passing_validation_result" in proposal["missing_evidence"]
    assert proposal["production_effect"] == "none"


def test_ceo_approval_queue_tracks_ready_promotion_proposal(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "forbidden_auto_actions": ["change core_signal_v0"],
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_approval_queue(options)

    queue = result["queue"]
    assert queue["status"] == "pending_approvals"
    assert queue["pending_count"] == 1
    assert queue["pending_items"][0]["approval_id"] == "promotion_proposal"
    assert queue["pending_items"][0]["authority"] == "red"
    assert queue["product_language_allowed"] is False
    assert queue["production_effect"] == "none"
    assert result["paths"]["queue"].exists()
    assert result["paths"]["queue_report"].exists()
    assert result["paths"]["approval_status"].exists()


def test_ceo_approval_record_appends_ledger_and_updates_queue(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_approval_record(
        options,
        approval_id="promotion_proposal",
        decision="approved",
        user_confirmed=True,
    )

    assert result["decision"]["decision"] == "approved"
    assert result["decision"]["production_effect"] == "none"
    assert result["queue"]["status"] == "no_pending_approvals"
    assert result["paths"]["approval_decision_ledger"].exists()
    ledger_lines = result["paths"]["approval_decision_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger_lines) == 1
    ledger_entry = json.loads(ledger_lines[0])
    assert ledger_entry["approval_id"] == "promotion_proposal"
    assert ledger_entry["user_confirmed"] is True


def test_ceo_approval_apply_requires_recorded_approval_and_stays_shadow_only(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    run_ceo_approval_record(
        options,
        approval_id="promotion_proposal",
        decision="approved",
        user_confirmed=True,
    )

    result = run_ceo_approval_apply(
        _authorized(options, "approval_apply"),
        approval_id="promotion_proposal",
        user_confirmed=True,
    )

    approval_apply = result["approval_apply"]
    assert approval_apply["status"] == "promotion_approval_closed_shadow_only"
    assert approval_apply["action_taken"] == "promotion_approval_closure_recorded"
    assert approval_apply["production_effect"] == "none"
    assert "No production formula" in approval_apply["audit"][1]
    assert result["paths"]["approval_apply"].exists()
    assert result["paths"]["binding_action_result"].exists()
    action_result = yaml.safe_load(result["paths"]["binding_action_result"].read_text(encoding="utf-8"))
    assert action_result["decision"] == "approval_apply"
    assert action_result["production_effect"] == "none"


def test_ceo_approval_apply_clears_stop_only_after_second_explicit_apply(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    run_ceo_stop(options, reason="test_stop")
    ceo_stop = ceo_ops.ceo_stop_path(options, "ceo_test")
    lab_stop = ceo_ops.lab_stop_path(options, "ceo_test_lab")
    assert ceo_stop.exists()
    assert lab_stop.exists()
    run_ceo_approval_record(
        options,
        approval_id="clear_stop_request",
        decision="approved",
        user_confirmed=True,
    )
    assert ceo_stop.exists()
    assert lab_stop.exists()

    result = run_ceo_approval_apply(
        _authorized(options, "approval_apply"),
        approval_id="clear_stop_request",
        user_confirmed=True,
    )

    assert result["approval_apply"]["status"] == "clear_stop_request_applied"
    assert not ceo_stop.exists()
    assert not lab_stop.exists()


def test_ceo_executive_kpis_writes_operating_scoreboard(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
                "status": "open_evidence_debt",
                "debt_count": 2,
                "next_action": "retire_top_debt",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "trace_grade.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_trace_grade_v0",
                "verdict": "pass",
                "score": 92,
                "loop_meltdown": {"fingerprint_repeat_count": 0, "manual_gate_repeat_count": 0},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "blocker_stack.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_blocker_stack_v0", "top_blocker": "pending_user_approval", "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "operating_incident_register.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_operating_incident_register_v0", "incident_count": 4, "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "repair_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_repair_plan_v0",
                "status": "manual_gate_first",
                "autonomous_repair_count": 0,
                "runnable_repair_count": 0,
                "diagnostic_refresh_count": 1,
                "top_repair": "blocker:pending_user_approval",
                "top_repair_kind": "manual_gate",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "status": "manual_gate_required",
                "primary_action": {
                    "action_id": "blocker:pending_user_approval",
                    "command_kind": "manual_gate",
                    "command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "status": "waiting_on_manual_gate",
                "plain_english_summary": "CEO mode is stopped at a manual gate.",
                "recommended_next_action": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_executive_kpis(options)

    kpis = result["kpis"]
    assert kpis["status"] == "attention_required"
    assert kpis["kpis"]["open_approval_count"] == 1
    assert kpis["kpis"]["evidence_debt_count"] == 2
    assert kpis["kpis"]["trace_verdict"] == "pass"
    assert kpis["kpis"]["top_blocker"] == "pending_user_approval"
    assert kpis["kpis"]["operating_incident_count"] == 4
    assert kpis["kpis"]["repair_plan_status"] == "manual_gate_first"
    assert kpis["kpis"]["top_repair"] == "blocker:pending_user_approval"
    assert kpis["kpis"]["top_repair_kind"] == "manual_gate"
    assert kpis["kpis"]["repair_next_command"].endswith("approval-queue --run-id ceo_test")
    assert kpis["product_language_allowed"] is False
    assert kpis["production_effect"] == "none"
    assert result["paths"]["executive_kpis"].exists()
    assert result["paths"]["executive_kpis_report"].exists()


def test_ceo_status_surfaces_existing_operating_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "blocker_stack.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_blocker_stack_v0",
                "status": "blocked",
                "top_blocker": "pending_user_approval",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "operating_incident_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operating_incident_register_v0",
                "status": "open_incidents",
                "incident_count": 3,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_dispatch_receipt_v0",
                "status": "dispatch_blocked",
                "safe_to_dispatch": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "resume_status": "blocked_stop_requested",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "repair_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_repair_plan_v0",
                "status": "manual_gate_first",
                "autonomous_repair_count": 0,
                "runnable_repair_count": 0,
                "diagnostic_refresh_count": 1,
                "top_repair": "blocker:pending_user_approval",
                "top_repair_kind": "manual_gate",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "status": "manual_gate_required",
                "primary_action": {
                    "action_id": "blocker:pending_user_approval",
                    "command_kind": "manual_gate",
                    "command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "status": "waiting_on_manual_gate",
                "plain_english_summary": "CEO mode is stopped at a manual gate.",
                "recommended_next_action": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_status(options)

    operating = result["company_status"]["operating_artifacts"]
    assert operating["blocker_stack_status"] == "blocked"
    assert operating["top_blocker"] == "pending_user_approval"
    assert operating["operating_incident_count"] == 3
    assert operating["dispatch_receipt_status"] == "dispatch_blocked"
    assert operating["dispatch_safe_to_dispatch"] is False
    assert operating["resumption_status"] == "blocked_stop_requested"
    assert operating["resumption_next_command"].endswith("approval-queue --run-id ceo_test")
    assert operating["default_handoff_command"] == operating["resumption_next_command"]
    assert operating["default_handoff_reason"] == "resumption_brief"
    assert operating["repair_plan_status"] == "manual_gate_first"
    assert operating["runnable_repair_count"] == 0
    assert operating["diagnostic_refresh_count"] == 1
    assert operating["top_repair"] == "blocker:pending_user_approval"
    assert operating["top_repair_kind"] == "manual_gate"
    assert operating["repair_next_command"].endswith("approval-queue --run-id ceo_test")
    assert operating["action_board_status"] == "manual_gate_required"
    assert operating["action_board_primary_action"] == "blocker:pending_user_approval"
    assert operating["action_board_primary_kind"] == "manual_gate"
    assert operating["action_board_command"].endswith("approval-queue --run-id ceo_test")
    assert operating["operator_brief_status"] == "waiting_on_manual_gate"
    assert operating["operator_brief_summary"] == "CEO mode is stopped at a manual gate."
    assert operating["operator_brief_next_action"].endswith("approval-queue --run-id ceo_test")
    assert result["company_status"]["production_effect"] == "none"
    assert yaml.safe_load((root / "company_status.yaml").read_text(encoding="utf-8"))["operating_artifacts"] == operating


def test_ceo_status_defaults_to_resumption_brief_when_handoff_missing(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    result = run_ceo_status(options)

    operating = result["company_status"]["operating_artifacts"]
    assert operating["resumption_status"] == "missing_resumption_brief"
    assert operating["resumption_next_command"] == ""
    assert operating["default_handoff_command"] == "PYTHONPATH=src python3 -m riskflow ceo resumption-brief --run-id ceo_test"
    assert operating["default_handoff_reason"] == "missing_resumption_brief"
    assert operating["action_board_status"] == "missing_action_board"
    assert operating["operator_brief_status"] == "missing_operator_brief"


def test_ceo_heartbeat_plan_writes_persistent_tick_contract(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)

    result = run_ceo_heartbeat_plan(options, interval_minutes=10, max_hours=2.5)

    plan = result["plan"]
    assert plan["status"] == "planned"
    assert plan["interval_minutes"] == 10
    assert plan["max_hours"] == 2.5
    assert "heartbeat-tick" in plan["tick_command"]
    assert plan["production_effect"] == "none"
    assert result["paths"]["heartbeat_plan"].exists()
    assert result["paths"]["heartbeat_plan_report"].exists()


def test_ceo_heartbeat_tick_blocks_when_plan_time_budget_elapsed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    run_ceo_heartbeat_plan(options, interval_minutes=10, max_hours=0.01)
    root = options.report_root / "ceo_test"
    plan_path = root / "heartbeat_plan.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan["generated_at"] = "2000-01-01T00:00:00+00:00"
    plan_path.write_text(yaml.safe_dump(plan), encoding="utf-8")

    def fail_execute_next(_options):
        raise AssertionError("heartbeat tick must not execute after the plan budget elapsed")

    monkeypatch.setattr(ceo_ops, "run_ceo_execute_next", fail_execute_next)

    result = run_ceo_heartbeat_tick(options)

    tick = result["tick"]
    assert tick["status"] == "blocked_before_action"
    assert "heartbeat_plan_time_budget_elapsed" in tick["blockers"]
    assert tick["heartbeat_plan_budget"]["status"] == "time_budget_elapsed"
    assert tick["portfolio_selected_lane"]
    assert tick["next_action"] == "stop_time_budget_elapsed"
    assert tick["production_effect"] == "none"


def test_ceo_heartbeat_tick_blocks_pending_approval_and_journals_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    def fail_execute_next(_options):
        raise AssertionError("heartbeat tick must not execute while approval is pending")

    monkeypatch.setattr(ceo_ops, "run_ceo_execute_next", fail_execute_next)

    result = run_ceo_heartbeat_tick(options)

    tick = result["tick"]
    assert tick["status"] == "blocked_before_action"
    assert "pending_user_approval" in tick["blockers"]
    assert tick["portfolio_selected_lane"] == "approval_governance"
    assert tick["action_status"] == "not_run"
    assert tick["production_effect"] == "none"
    journal_lines = result["paths"]["heartbeat_journal"].read_text(encoding="utf-8").strip().splitlines()
    assert len(journal_lines) == 1
    rendered = run_ceo_heartbeat_journal(options)
    assert len(rendered["entries"]) == 1
    assert rendered["paths"]["heartbeat_journal_report"].exists()


def test_ceo_heartbeat_tick_delegates_trace_only_blocker_to_execute_next(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    trace_path = root / "trace_grade.yaml"
    failed_trace = {
        "model": "riskflow_ceo_trace_grade_v0",
        "verdict": "fail",
        "recommended_next_action": "patch_research_infra",
        "issues": ["synthetic_trace_failure"],
        "production_effect": "none",
    }
    trace_path.write_text(yaml.safe_dump(failed_trace), encoding="utf-8")
    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_trace_grade",
        lambda _options: {"grade": failed_trace, "paths": {"trace_grade": trace_path}},
    )

    def fake_execute_next(_options):
        return {
            "action_result": {
                "decision": "patch_research_infra",
                "action_taken": "research_infra_patch_plan",
                "status": "blocked_missing_recovery_inputs",
                "production_effect": "none",
            }
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_execute_next", fake_execute_next)

    result = run_ceo_heartbeat_tick(options)

    tick = result["tick"]
    assert tick["status"] == "executed_one_action"
    assert tick["pre_action_warnings"] == ["flight_dashboard_not_safe", "trace_grade_failed"]
    assert tick["blockers"] == []
    assert tick["action_decision"] == "patch_research_infra"
    assert tick["action_status"] == "blocked_missing_recovery_inputs"
    assert tick["production_effect"] == "none"


def test_ceo_heartbeat_tick_records_execute_next_trace_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    trace_path = root / "trace_grade.yaml"
    failed_trace = {
        "model": "riskflow_ceo_trace_grade_v0",
        "verdict": "fail",
        "recommended_next_action": "patch_research_infra",
        "issues": ["synthetic_trace_failure"],
        "production_effect": "none",
    }
    trace_path.write_text(yaml.safe_dump(failed_trace), encoding="utf-8")
    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_trace_grade",
        lambda _options: {"grade": failed_trace, "paths": {"trace_grade": trace_path}},
    )

    def fake_execute_next(_options):
        return {
            "action_result": {
                "decision": "run_fresh_withheld_validation_executor",
                "action_taken": "blocked_preflight_gate",
                "status": "blocked",
                "preflight_blockers": [{"blocker": "trace_grade_failed", "source": "trace_grade.yaml"}],
                "production_effect": "none",
            }
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_execute_next", fake_execute_next)

    result = run_ceo_heartbeat_tick(options)

    tick = result["tick"]
    assert tick["status"] == "blocked_by_execute_next"
    assert tick["pre_action_warnings"] == ["flight_dashboard_not_safe", "trace_grade_failed"]
    assert tick["blockers"] == ["trace_grade_failed"]
    assert tick["action_decision"] == "run_fresh_withheld_validation_executor"
    assert tick["action_status"] == "blocked"
    assert tick["production_effect"] == "none"


def test_ceo_role_queue_maps_debt_and_approval_to_specialist_roles(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
                "status": "open_evidence_debt",
                "debt_count": 2,
                "debts": [
                    {
                        "debt_id": "candidate_a_passing_validation_result",
                        "candidate_id": "candidate_a",
                        "debt_kind": "passing_validation_result",
                        "blocker_type": "fresh_withheld_thresholds_failed",
                        "priority": 1,
                        "evidence_required": "passing fresh/withheld thresholds",
                        "owner_command": "review_fresh_withheld_threshold_failures_or_archive_candidate",
                        "blocking_artifact": "fresh_withheld_validation_execution_result.yaml",
                    },
                    {
                        "debt_id": "candidate_b_fresh_data_readiness",
                        "candidate_id": "candidate_b",
                        "debt_kind": "fresh_data_readiness",
                        "blocker_type": "fresh_data_gate_blocked",
                        "priority": 2,
                        "evidence_required": "fresh OHLCV coverage",
                        "owner_command": "import_or_curate_fresh_ohlcv_data",
                        "blocking_artifact": "fresh_data_preflight.yaml",
                    },
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_queue_v0",
                "status": "pending_approvals",
                "pending_count": 1,
                "pending_items": [
                    {
                        "approval_id": "promotion_proposal",
                        "reason": "promotion proposal awaits approval",
                        "source_artifact": "promotion_proposal.yaml",
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "capability_backlog.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_capability_backlog_v0", "items": [], "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_role_queue(options)

    queue = result["queue"]
    roles_by_task = {task["task_id"]: task["role_id"] for task in queue["tasks"]}
    assert roles_by_task["debt_candidate_a_passing_validation_result"] == "validation_referee"
    assert roles_by_task["debt_candidate_b_fresh_data_readiness"] == "data_steward"
    assert roles_by_task["approval_promotion_proposal"] == "risk_officer"
    assert queue["production_effect"] == "none"
    assert result["paths"]["role_registry"].exists()
    assert result["paths"]["role_task_queue"].exists()
    assert result["paths"]["role_task_queue_report"].exists()


def test_ceo_role_result_appends_ledger(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
                "status": "open_evidence_debt",
                "debt_count": 1,
                "debts": [
                    {
                        "debt_id": "candidate_a_passing_validation_result",
                        "candidate_id": "candidate_a",
                        "debt_kind": "passing_validation_result",
                        "blocker_type": "fresh_withheld_thresholds_failed",
                        "priority": 1,
                        "evidence_required": "passing fresh/withheld thresholds",
                        "owner_command": "review_fresh_withheld_threshold_failures_or_archive_candidate",
                        "blocking_artifact": "fresh_withheld_validation_execution_result.yaml",
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_approval_queue_v0", "pending_count": 0, "pending_items": []}),
        encoding="utf-8",
    )
    (root / "capability_backlog.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_capability_backlog_v0", "items": [], "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_role_result(
        options,
        task_id="debt_candidate_a_passing_validation_result",
        status="complete",
        result_path="reports/review.md",
    )

    assert result["result"]["status"] == "complete"
    assert result["result"]["production_effect"] == "none"
    lines = result["paths"]["role_task_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["task_id"] == "debt_candidate_a_passing_validation_result"
    assert entry["result_path"] == "reports/review.md"
    assert result["queue"]["completed_task_count"] == 1
    assert result["queue"]["pending_task_count"] == 0
    assert result["queue"]["tasks"][0]["status"] == "complete"
    assert result["paths"]["role_task_queue"].exists()


def test_ceo_role_dispatch_writes_specialist_packets(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
                "status": "open_evidence_debt",
                "debt_count": 1,
                "debts": [
                    {
                        "debt_id": "candidate_a_passing_validation_result",
                        "candidate_id": "candidate_a",
                        "debt_kind": "passing_validation_result",
                        "blocker_type": "fresh_withheld_thresholds_failed",
                        "priority": 1,
                        "evidence_required": "passing fresh/withheld thresholds",
                        "owner_command": "review_fresh_withheld_threshold_failures_or_archive_candidate",
                        "blocking_artifact": "fresh_withheld_validation_execution_result.yaml",
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_approval_queue_v0", "pending_count": 0, "pending_items": []}),
        encoding="utf-8",
    )
    (root / "capability_backlog.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_capability_backlog_v0", "items": [], "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_role_dispatch(options)

    dispatch = result["role_dispatch"]
    assert dispatch["model"] == "riskflow_ceo_role_dispatch_v0"
    assert dispatch["status"] == "packets_written"
    assert dispatch["packet_count"] == 1
    packet = dispatch["packets"][0]
    assert packet["role_id"] == "validation_referee"
    assert packet["allowed_authority"] == "review_only"
    assert packet["product_language_allowed"] is False
    assert packet["production_effect"] == "none"
    packet_path = Path(packet["packet_path"])
    assert packet_path.exists()
    packet_text = packet_path.read_text(encoding="utf-8")
    assert "Expected Result Schema" in packet_text
    assert "production_effect: none" in packet_text
    assert "Do not approve manual gates" in packet_text
    assert result["paths"]["role_dispatch"].exists()
    assert result["paths"]["role_dispatch_report"].exists()


def test_ceo_role_dispatch_handles_empty_queue(tmp_path: Path) -> None:
    queue = {
        "model": "riskflow_ceo_role_task_queue_v0",
        "tasks": [{"task_id": "done", "role_id": "risk_officer", "status": "complete", "production_effect": "none"}],
        "production_effect": "none",
    }

    dispatch = ceo_ops.build_ceo_role_dispatch(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        role_queue=queue,
        packet_dir=tmp_path / "packets",
    )

    assert dispatch["status"] == "no_pending_role_tasks"
    assert dispatch["packet_count"] == 0
    assert dispatch["production_effect"] == "none"


def test_ceo_replay_reconstructs_action_ledger_and_key_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)

    result = run_ceo_replay(options)

    replay = result["replay"]
    assert replay["status"] == "replayable"
    assert replay["action_count"] == 1
    assert replay["artifact_checks"]["ceo_action_ledger"]["exists"] is True
    assert replay["artifact_checks"]["binding_action_result"]["exists"] is True
    assert replay["artifact_checks"]["action_contract"]["exists"] is True
    assert replay["artifact_checks"]["dispatch_receipt"]["exists"] is True
    assert replay["dispatch_receipt_status"] == "pass"
    assert replay["dispatch_receipt_checks"][0]["status"] == "pass"
    assert "preflight_gate" in replay["artifact_checks"]
    assert "guardrail_audit" in replay["artifact_checks"]
    assert replay["timeline"][0]["kind"] == "action"
    assert replay["production_effect"] == "none"
    assert result["paths"]["replay"].exists()
    assert result["paths"]["replay_report"].exists()


def test_ceo_replay_binding_fallback_is_diagnostic_not_replayable(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_champion_challenger",
            "action_taken": "champion_challenger",
            "status": "shadow_comparison_complete",
            "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
            "production_effect": "none",
        },
    )
    (root / "ceo_action_ledger.jsonl").unlink()

    result = run_ceo_replay(options)

    replay = result["replay"]
    assert replay["status"] == "replay_gaps"
    assert replay["used_binding_result_fallback"] is True
    assert "missing_action_ledger_using_binding_fallback" in replay["issues"]
    assert replay["action_count"] == 1


def test_ceo_replay_flags_illegal_state_transition(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "generated_at": "2026-06-06T00:00:00Z",
            "decision": "run_champion_challenger",
            "action_taken": "champion_challenger",
            "status": "shadow_comparison_complete",
            "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
            "production_effect": "none",
        },
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "generated_at": "2026-06-06T00:01:00Z",
            "decision": "continue_governed_research",
            "action_taken": "run_block",
            "status": "completed",
            "next_allowed_actions": [],
            "production_effect": "none",
        },
    ]
    (root / "ceo_action_ledger.jsonl").write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in entries) + "\n",
        encoding="utf-8",
    )

    result = run_ceo_replay(options)

    replay = result["replay"]
    assert replay["status"] == "replay_gaps"
    assert replay["state_transition_status"] == "fail"
    assert replay["state_transition_checks"][0]["status"] == "fail"
    assert "illegal_action_transition" in replay["issues"]


def test_ceo_replay_verifies_every_action_dispatch_receipt_snapshot(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    snapshot_dir = root / "dispatch_receipts"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    decisions = [
        (
            "run_champion_challenger",
            "champion_challenger",
            "shadow_comparison_complete",
            ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
        ),
        (
            "run_fresh_or_control_validation_for_promising_shadow_challengers",
            "fresh_control_validation_plan",
            "planned",
            [],
        ),
    ]
    for index, (decision, action_taken, status, next_allowed_actions) in enumerate(decisions, start=1):
        receipt = {
            "model": "riskflow_ceo_dispatch_receipt_v0",
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "decision": decision,
            "status": "dispatch_allowed",
            "product_language_allowed": False,
            "production_effect": "none",
            "promotion_authority": "none",
        }
        receipt_path = snapshot_dir / f"receipt_{index}.yaml"
        receipt_path.write_text(yaml.safe_dump(receipt), encoding="utf-8")
        entries.append(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "generated_at": f"2026-06-06T00:0{index}:00Z",
                "decision": decision,
                "action_taken": action_taken,
                "status": status,
                "next_allowed_actions": next_allowed_actions,
                "dispatch_receipt": {"path": str(receipt_path), "sha256": _sha256(receipt_path)},
                "production_effect": "none",
            }
        )
    (root / "ceo_action_ledger.jsonl").write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in entries) + "\n",
        encoding="utf-8",
    )

    result = run_ceo_replay(options)

    replay = result["replay"]
    assert replay["status"] == "replayable"
    assert replay["dispatch_receipt_status"] == "pass"
    assert [item["status"] for item in replay["dispatch_receipt_checks"]] == ["pass", "pass"]


def test_ceo_eval_suite_scores_replay_guardrails_and_closure(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)

    result = run_ceo_eval_suite(options)

    suite = result["eval_suite"]
    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["replayable_action_timeline"]["status"] == "pass"
    assert cases["action_contract_matches_latest_action"]["status"] == "pass"
    assert cases["dispatch_receipt_backs_latest_action"]["status"] == "pass"
    assert cases["dispatch_receipts_cover_action_ledger"]["status"] == "pass"
    assert cases["dispatch_receipt_fingerprints_trust_artifacts"]["status"] == "pass"
    assert cases["production_guardrails_preserved"]["status"] == "pass"
    assert cases["policy_eval_fixtures_pass"]["status"] == "pass"
    assert suite["production_effect"] == "none"
    assert result["paths"]["eval_suite"].exists()
    assert result["paths"]["eval_suite_report"].exists()
    assert result["paths"]["eval_fixtures"].exists()


def test_ceo_eval_suite_flags_missing_dispatch_receipt_for_latest_action(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)
    root = options.report_root / "ceo_test"
    latest_action = yaml.safe_load((root / "binding_action_result.yaml").read_text(encoding="utf-8"))
    Path(latest_action["dispatch_receipt"]["path"]).unlink()

    result = run_ceo_eval_suite(options)

    suite = result["eval_suite"]
    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["dispatch_receipt_backs_latest_action"]["status"] == "fail"
    assert cases["dispatch_receipt_backs_latest_action"]["severity"] == "critical"
    assert cases["dispatch_receipts_cover_action_ledger"]["status"] == "fail"
    assert suite["status"] == "fail"
    assert "dispatch_receipt_backs_latest_action" in suite["nine_nine_readiness"]["blocking_case_ids"]


def test_ceo_eval_suite_scores_mission_and_strategy_readiness(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)

    missing_strategy = run_ceo_eval_suite(options)["eval_suite"]
    missing_cases = {item["case_id"]: item for item in missing_strategy["cases"]}
    assert missing_cases["mission_score_covers_product_mission"]["status"] == "pass"
    assert missing_cases["strategy_capital_allocates_attention"]["status"] == "fail"
    assert missing_strategy["status"] == "pass"
    assert "strategy_capital_allocates_attention" in missing_strategy["nine_nine_readiness"]["advisory_case_ids"]

    run_ceo_strategy_capital_dashboard(options)
    ready_strategy = run_ceo_eval_suite(options)["eval_suite"]
    ready_cases = {item["case_id"]: item for item in ready_strategy["cases"]}
    assert ready_cases["mission_score_covers_product_mission"]["status"] == "pass"
    assert ready_cases["strategy_capital_allocates_attention"]["status"] == "pass"


def test_ceo_eval_suite_scores_state_machine_transition_failure(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "generated_at": "2026-06-06T00:00:00Z",
            "decision": "run_champion_challenger",
            "status": "shadow_comparison_complete",
            "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
            "production_effect": "none",
        },
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "generated_at": "2026-06-06T00:01:00Z",
            "decision": "continue_governed_research",
            "status": "completed",
            "next_allowed_actions": [],
            "production_effect": "none",
        },
    ]
    (root / "ceo_action_ledger.jsonl").write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in entries) + "\n",
        encoding="utf-8",
    )
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(entries[-1]), encoding="utf-8")
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_action_contract_v0", "decision": "continue_governed_research", "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_eval_suite(options)

    cases = {item["case_id"]: item for item in result["eval_suite"]["cases"]}
    assert cases["state_machine_legal_transitions"]["status"] == "fail"
    assert result["eval_suite"]["status"] == "fail"


def test_ceo_portfolio_allocator_prioritizes_pending_approval(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_portfolio_allocator(options)

    allocator = result["allocator"]
    assert allocator["selected_lane"]["lane_id"] == "approval_governance"
    assert allocator["selected_lane"]["next_action"] == "wait_for_user_approval"
    assert allocator["product_language_allowed"] is False
    assert allocator["production_effect"] == "none"
    assert result["paths"]["portfolio_allocator"].exists()
    assert result["paths"]["portfolio_allocator_report"].exists()


def test_ceo_mission_score_writes_all_mission_dimensions(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)

    result = run_ceo_mission_score(options)

    score = result["mission_score"]
    dimensions = {item["dimension_id"]: item for item in score["mission_dimensions"]}
    assert score["model"] == "riskflow_ceo_mission_score_v0"
    assert set(dimensions) == {
        "bullish_permission",
        "warning_blocker",
        "invalidation",
        "reset_quality",
        "gradient_interpretation",
        "path_management",
        "cross_asset_regime",
        "archive_do_not_repeat",
    }
    assert score["product_language_allowed"] is False
    assert score["production_effect"] == "none"
    assert score["promotion_authority"] == "none"
    assert result["paths"]["mission_score"].exists()
    assert result["paths"]["mission_score_report"].exists()


def test_ceo_mission_score_maps_candidates_to_product_roles() -> None:
    score = ceo_ops.build_ceo_mission_score(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        operating_dashboard={
            "candidate_portfolio": [
                {
                    "belief_id": "warning_a",
                    "product_role": "warning_blocker",
                    "evidence_gate": "champion_challenger_complete",
                    "next_required_evidence": "run_fresh_control_validation",
                    "production_effect": "none",
                },
                {
                    "belief_id": "reset_a",
                    "product_role": "reset_quality",
                    "evidence_gate": "fresh_withheld_contract_ready",
                    "next_required_evidence": "run_fresh_withheld_validation_executor",
                    "production_effect": "none",
                },
            ],
            "product_governance": {"pending_approval_count": 0},
            "production_effect": "none",
        },
        portfolio_allocator={"selected_lane": {"lane_id": "candidate_product_translation"}},
        executive_kpis={"kpis": {}},
        evidence_debt_register={"debt_count": 0, "debts": [], "production_effect": "none"},
        trace_grade={"verdict": "pass", "production_effect": "none"},
        preflight_gate={"safe_to_execute": True, "blockers": [], "production_effect": "none"},
        knowledge_graph_delta={"recommended_obsidian_summaries": [], "production_effect": "none"},
    )

    candidate_map = {item["belief_id"]: item for item in score["candidate_mission_map"]}
    dimensions = {item["dimension_id"]: item for item in score["mission_dimensions"]}
    assert candidate_map["warning_a"]["dimension_id"] == "warning_blocker"
    assert candidate_map["reset_a"]["dimension_id"] == "reset_quality"
    assert dimensions["warning_blocker"]["candidate_count"] == 1
    assert dimensions["reset_quality"]["candidate_count"] == 1
    assert score["production_effect"] == "none"


def _strategy_dashboard_inputs(*, pending_approval: bool = False, preflight_safe: bool = True) -> dict[str, object]:
    dimensions = [
        {
            "dimension_id": dimension,
            "dimension_score": 65,
            "owner_command": "run_champion_challenger",
            "production_effect": "none",
        }
        for dimension in ceo_ops.MISSION_DIMENSIONS
    ]
    dimensions[0]["dimension_score"] = 35
    dimensions[0]["owner_command"] = "run_fresh_control_validation"
    return {
        "ceo_run_id": "ceo_test",
        "lab_run_id": "ceo_test_lab",
        "mission_score": {
            "overall_mission_score": 60,
            "lowest_dimension": "bullish_permission",
            "next_best_mission_action": "run_fresh_control_validation",
            "mission_dimensions": dimensions,
            "archive_signals": ["open_evidence_debt"],
            "production_effect": "none",
        },
        "operating_dashboard": {"candidate_portfolio_count": 2, "production_effect": "none"},
        "portfolio_allocator": {
            "lanes": [{"lane_id": "validation_authority", "score": 75, "next_action": "run_fresh_withheld_validation_executor"}],
            "production_effect": "none",
        },
        "approval_queue": {"pending_count": 1 if pending_approval else 0, "production_effect": "none"},
        "preflight_gate": {
            "safe_to_execute": preflight_safe,
            "blockers": [] if preflight_safe else [{"blocker": "computed_memory_delta_required"}],
            "production_effect": "none",
        },
        "trace_grade": {"verdict": "pass", "production_effect": "none"},
        "evidence_debt_register": {"debt_count": 2, "debts": [], "production_effect": "none"},
        "capability_backlog": {"backlog_count": 1, "items": [], "production_effect": "none"},
        "role_queue": {"pending_task_count": 1, "production_effect": "none"},
        "heartbeat_status": {"stop_requested": False, "production_effect": "none"},
    }


def test_ceo_strategy_capital_dashboard_prioritizes_approval_gate() -> None:
    dashboard = ceo_ops.build_ceo_strategy_capital_dashboard(
        **_strategy_dashboard_inputs(pending_approval=True, preflight_safe=True)
    )

    assert dashboard["model"] == "riskflow_ceo_strategy_capital_dashboard_v0"
    assert dashboard["status"] == "blocked_by_safety_or_approval"
    assert dashboard["safe_to_continue"] is False
    assert dashboard["selected_capital_bucket"] == "approval_and_safety"
    assert dashboard["selected_strategy"] == "wait_for_user_approval_or_repair_preflight"
    assert dashboard["capital_buckets"][0]["bucket_id"] == "approval_and_safety"
    assert "pending_user_approval" in dashboard["capital_buckets"][0]["blocked_by"]


def test_ceo_strategy_capital_points_sum_to_100() -> None:
    dashboard = ceo_ops.build_ceo_strategy_capital_dashboard(**_strategy_dashboard_inputs())

    assert dashboard["status"] == "strategy_capital_allocated"
    assert dashboard["safe_to_continue"] is True
    assert dashboard["total_points"] == 100
    assert sum(int(item["allocation_points"]) for item in dashboard["capital_buckets"]) == 100
    assert len(dashboard["ordered_action_queue"]) == len(dashboard["capital_buckets"])
    assert all(item["production_effect"] == "none" for item in dashboard["capital_buckets"])
    assert dashboard["product_language_allowed"] is False
    assert dashboard["production_effect"] == "none"
    assert dashboard["promotion_authority"] == "none"


def test_ceo_strategy_capital_dashboard_is_diagnostic_only(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)

    result = run_ceo_strategy_capital_dashboard(options)

    dashboard = result["dashboard"]
    root = options.report_root / "ceo_test"
    assert result["paths"]["strategy_capital_dashboard"].exists()
    assert result["paths"]["strategy_capital_dashboard_report"].exists()
    assert dashboard["product_language_allowed"] is False
    assert dashboard["production_effect"] == "none"
    assert dashboard["promotion_authority"] == "none"
    assert sum(int(item["allocation_points"]) for item in dashboard["capital_buckets"]) == 100
    assert not (root / "binding_action_result.yaml").exists()
    assert not (root / "ceo_action_ledger.jsonl").exists()


def test_ceo_resumption_brief_writes_fresh_session_trust_card(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_strategy_capital_dashboard(options)

    result = run_ceo_resumption_brief(options)

    brief = result["brief"]
    root = options.report_root / "ceo_test"
    assert brief["model"] == "riskflow_ceo_resumption_brief_v0"
    assert brief["product_language_allowed"] is False
    assert brief["production_effect"] == "none"
    assert brief["promotion_authority"] == "none"
    if brief["resume_status"] == "blocked_preflight":
        assert "execute-next" not in brief["next_command"]
        assert brief["preflight_blockers"]
    else:
        assert brief["resume_status"] in {"safe_for_one_bound_action", "diagnostic_advisory_before_extended_autonomy"}
        assert "execute-next" in brief["next_command"] or "strategy-capital-dashboard" in brief["next_command"]
    artifacts = {item["artifact"]: item for item in brief["artifact_status"]}
    assert artifacts["preflight_gate"]["exists"] is True
    assert artifacts["ceo_replay"]["exists"] is True
    assert artifacts["ceo_eval_suite"]["exists"] is True
    assert artifacts["mission_score"]["exists"] is True
    assert artifacts["strategy_capital_dashboard"]["exists"] is True
    assert result["paths"]["resumption_brief"].exists()
    assert result["paths"]["resumption_brief_report"].exists()
    assert not (root / "binding_action_result.yaml").exists()
    assert not (root / "ceo_action_ledger.jsonl").exists()


def test_ceo_resumption_brief_blocks_stopped_run(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")

    result = run_ceo_resumption_brief(options)

    brief = result["brief"]
    assert brief["resume_status"] == "blocked_stop_requested"
    assert "execute-next" not in brief["next_command"]
    assert "approval-queue" in brief["next_command"]
    assert brief["stop_requested"] is True


def test_ceo_resumption_brief_blocks_failed_preflight(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "unsafe_product_claim.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_test_bad_artifact_v0",
                "product_language_allowed": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_resumption_brief(options)

    brief = result["brief"]
    assert brief["resume_status"] == "blocked_preflight"
    assert "execute-next" not in brief["next_command"]
    assert "guardrail_audit_failed" in brief["preflight_blockers"]


def test_ceo_resumption_brief_allows_one_bound_action_only_when_clean(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    latest_packet = root / "executive_decision_packet.md"
    latest_packet.write_text("# packet\n", encoding="utf-8")
    for filename in [
        "preflight_gate.yaml",
        "ceo_replay.yaml",
        "ceo_eval_suite.yaml",
        "mission_score.yaml",
        "strategy_capital_dashboard.yaml",
    ]:
        (root / filename).write_text("production_effect: none\n", encoding="utf-8")

    brief = ceo_ops.build_ceo_resumption_brief(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        stop_requested=False,
        preflight_gate={"status": "pass", "safe_to_execute": True, "blockers": [], "production_effect": "none"},
        replay={"model": "riskflow_ceo_replay_v0", "status": "replayable", "production_effect": "none"},
        eval_suite={
            "model": "riskflow_ceo_eval_suite_v0",
            "status": "pass",
            "nine_nine_readiness": {"status": "ready_for_extended_autonomy", "advisory_case_ids": []},
            "production_effect": "none",
        },
        mission_score={
            "model": "riskflow_ceo_mission_score_v0",
            "status": "mission_compounding",
            "overall_mission_score": 90,
            "lowest_dimension": "path_management",
            "production_effect": "none",
        },
        strategy_capital_dashboard={
            "model": "riskflow_ceo_strategy_capital_dashboard_v0",
            "selected_capital_bucket": "validation_authority",
            "selected_strategy": "run_fresh_withheld_validation_executor",
            "production_effect": "none",
        },
        artifact_coherence={"model": "riskflow_ceo_artifact_coherence_v0", "status": "pass", "issues": [], "production_effect": "none"},
        latest_packet=latest_packet,
    )

    assert brief["resume_status"] == "safe_for_one_bound_action"
    assert brief["next_command"] == "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply"
    assert brief["product_language_allowed"] is False
    assert brief["promotion_authority"] == "none"


def test_ceo_resumption_brief_requires_decision_packet_before_execute_next(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    latest_packet = root / "executive_decision_packet.md"
    for filename in [
        "preflight_gate.yaml",
        "ceo_replay.yaml",
        "ceo_eval_suite.yaml",
        "mission_score.yaml",
        "strategy_capital_dashboard.yaml",
    ]:
        (root / filename).write_text("production_effect: none\n", encoding="utf-8")

    brief = ceo_ops.build_ceo_resumption_brief(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        stop_requested=False,
        preflight_gate={"status": "pass", "safe_to_execute": True, "blockers": [], "production_effect": "none"},
        replay={"model": "riskflow_ceo_replay_v0", "status": "replayable", "production_effect": "none"},
        eval_suite={
            "model": "riskflow_ceo_eval_suite_v0",
            "status": "pass",
            "nine_nine_readiness": {"status": "ready_for_extended_autonomy", "advisory_case_ids": []},
            "production_effect": "none",
        },
        mission_score={"model": "riskflow_ceo_mission_score_v0", "production_effect": "none"},
        strategy_capital_dashboard={"model": "riskflow_ceo_strategy_capital_dashboard_v0", "production_effect": "none"},
        artifact_coherence={"model": "riskflow_ceo_artifact_coherence_v0", "status": "pass", "issues": [], "production_effect": "none"},
        latest_packet=latest_packet,
    )

    assert brief["resume_status"] == "diagnostic_missing_decision_packet"
    assert brief["next_command"] == "PYTHONPATH=src python3 -m riskflow ceo review --run-id ceo_test"
    assert "execute-next" not in brief["next_command"]


def _write_coherence_artifact(root: Path, name: str, *, run_id: str = "ceo_test", lab_run_id: str = "ceo_test_lab", generated_at: str = "2026-06-06T00:05:00+00:00") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(
        yaml.safe_dump(
            {
                "model": f"riskflow_{name.replace('.yaml', '')}_v0",
                "generated_at": generated_at,
                "run_id": run_id,
                "lab_run_id": lab_run_id,
                "status": "pass",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )


def _write_clean_coherence_inputs(root: Path) -> None:
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "decision": "run_champion_challenger",
            "action_taken": "champion_challenger",
            "status": "shadow_comparison_complete",
            "generated_at": "2026-06-06T00:01:00+00:00",
            "production_effect": "none",
        },
    )
    (root / "executive_decision_packet.md").write_text("# packet\n", encoding="utf-8")
    for name in [
        "preflight_gate.yaml",
        "ceo_replay.yaml",
        "ceo_eval_suite.yaml",
        "mission_score.yaml",
        "strategy_capital_dashboard.yaml",
    ]:
        _write_coherence_artifact(root, name)


def test_ceo_artifact_coherence_passes_clean_current_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    ledger_before = (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8")

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    assert coherence["model"] == "riskflow_ceo_artifact_coherence_v0"
    assert coherence["status"] == "pass"
    assert coherence["issue_count"] == 0
    assert result["paths"]["artifact_coherence"].exists()
    assert result["paths"]["artifact_coherence_report"].exists()
    assert (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8") == ledger_before


def test_ceo_artifact_coherence_flags_stale_mission_after_latest_action(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    _write_coherence_artifact(root, "mission_score.yaml", generated_at="2026-06-06T00:00:30+00:00")

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    issues = {item["artifact"]: item["issues"] for item in coherence["issues"]}
    assert coherence["status"] == "fail"
    assert "stale_before_latest_action" in issues["mission_score"]


def test_ceo_artifact_coherence_flags_run_id_mismatch(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    _write_coherence_artifact(root, "preflight_gate.yaml", run_id="other_run")

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    issues = {item["artifact"]: item["issues"] for item in coherence["issues"]}
    assert coherence["status"] == "fail"
    assert "run_id_mismatch" in issues["preflight_gate"]


def test_ceo_resumption_brief_downgrades_clean_preflight_on_failed_coherence(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    latest_packet = root / "executive_decision_packet.md"
    latest_packet.write_text("# packet\n", encoding="utf-8")

    brief = ceo_ops.build_ceo_resumption_brief(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        stop_requested=False,
        preflight_gate={"status": "pass", "safe_to_execute": True, "blockers": [], "production_effect": "none"},
        replay={"model": "riskflow_ceo_replay_v0", "status": "replayable", "production_effect": "none"},
        eval_suite={
            "model": "riskflow_ceo_eval_suite_v0",
            "status": "pass",
            "nine_nine_readiness": {"status": "ready_for_extended_autonomy", "advisory_case_ids": []},
            "production_effect": "none",
        },
        mission_score={"model": "riskflow_ceo_mission_score_v0", "production_effect": "none"},
        strategy_capital_dashboard={"model": "riskflow_ceo_strategy_capital_dashboard_v0", "production_effect": "none"},
        artifact_coherence={
            "model": "riskflow_ceo_artifact_coherence_v0",
            "status": "fail",
            "issues": [{"artifact": "mission_score", "issues": ["stale_before_latest_action"]}],
            "production_effect": "none",
        },
        latest_packet=latest_packet,
    )

    assert brief["resume_status"] == "diagnostic_stale_artifacts"
    assert "artifact-coherence" in brief["next_command"]
    assert "execute-next" not in brief["next_command"]


def test_ceo_run_index_classifies_runs_and_next_commands(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    actionable_root = options.report_root / "ceo_actionable"
    stopped_root = options.report_root / "ceo_stopped"
    blocked_root = options.report_root / "ceo_blocked"
    for root in [actionable_root, stopped_root, blocked_root]:
        root.mkdir(parents=True, exist_ok=True)

    (actionable_root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "run_id": "ceo_actionable",
                "lab_run_id": "ceo_actionable_lab",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_actionable --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"status": "pass", "safe_to_execute": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (actionable_root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_dispatch_receipt_v0",
                "status": "dispatch_allowed",
                "safe_to_dispatch": True,
                "reason": "preflight, approval, and self-audit gates allowed one bound dispatch",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "blocker_stack.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_blocker_stack_v0", "status": "clear_for_one_bound_action", "top_blocker": "", "production_effect": "none"}),
        encoding="utf-8",
    )
    (actionable_root / "operating_incident_register.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_operating_incident_register_v0", "status": "no_open_incidents", "incident_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )
    (actionable_root / "repair_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_repair_plan_v0",
                "status": "no_repairs_required",
                "top_repair": "",
                "top_repair_kind": "",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_actionable --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "status": "ready_for_one_operator_step",
                "plain_english_summary": "CEO mode has one bounded action available.",
                "recommended_next_action": "PYTHONPATH=src python3 -m riskflow ceo operator-step --run-id ceo_actionable --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "mission_score.yaml").write_text(
        yaml.safe_dump({"overall_mission_score": 82, "lowest_dimension": "reset_quality", "production_effect": "none"}),
        encoding="utf-8",
    )
    (actionable_root / "strategy_capital_dashboard.yaml").write_text(
        yaml.safe_dump({"selected_capital_bucket": "validation_authority", "production_effect": "none"}),
        encoding="utf-8",
    )
    (actionable_root / "executive_decision_packet.md").write_text("# packet\n", encoding="utf-8")

    (stopped_root / "stop.request").write_text("user_requested\n", encoding="utf-8")
    (stopped_root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "run_id": "ceo_stopped",
                "lab_run_id": "ceo_stopped_lab",
                "resume_status": "blocked_stop_requested",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_stopped",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    (blocked_root / "preflight_gate.yaml").write_text(
        yaml.safe_dump(
            {
                "status": "blocked",
                "safe_to_execute": False,
                "blockers": [{"blocker": "pending_user_approval"}],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_run_index(options)

    index = result["run_index"]
    rows = {item["run_id"]: item for item in index["runs"]}
    assert index["model"] == "riskflow_ceo_run_index_v0"
    assert index["status"] == "runs_indexed"
    assert index["status_counts"]["actionable"] == 1
    assert index["status_counts"]["stopped"] == 1
    assert index["status_counts"]["blocked"] == 1
    assert rows["ceo_actionable"]["status"] == "actionable"
    assert rows["ceo_actionable"]["latest_decision_packet_exists"] is True
    assert rows["ceo_actionable"]["dispatch_receipt_status"] == "dispatch_allowed"
    assert rows["ceo_actionable"]["dispatch_safe_to_dispatch"] is True
    assert rows["ceo_actionable"]["top_blocker"] == ""
    assert rows["ceo_actionable"]["incident_count"] == 0
    assert rows["ceo_actionable"]["repair_plan_status"] == "no_repairs_required"
    assert rows["ceo_actionable"]["top_repair"] == ""
    assert rows["ceo_actionable"]["top_repair_kind"] == ""
    assert rows["ceo_actionable"]["operator_brief_status"] == "ready_for_one_operator_step"
    assert rows["ceo_actionable"]["operator_brief_summary"] == "CEO mode has one bounded action available."
    assert rows["ceo_actionable"]["mission_score"] == 82
    assert rows["ceo_actionable"]["strategy_capital_bucket"] == "validation_authority"
    assert rows["ceo_stopped"]["status"] == "stopped"
    assert rows["ceo_blocked"]["status"] == "blocked"
    assert rows["ceo_blocked"]["preflight_blockers"] == ["pending_user_approval"]
    assert rows["ceo_blocked"]["next_command"].endswith("ceo resumption-brief --run-id ceo_blocked")
    report = result["paths"]["run_index_report"].read_text(encoding="utf-8")
    assert "resumption_next=" in report
    assert "brief=ready_for_one_operator_step" in report
    assert "operator_summary=CEO mode has one bounded action available." in report
    assert "repair_next=`PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_actionable --apply`" in report


def test_ceo_run_index_is_diagnostic_only(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    ledger_before = (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8")

    result = run_ceo_run_index(options)

    assert result["paths"]["run_index"].exists()
    assert result["paths"]["run_index_report"].exists()
    assert result["run_index"]["production_effect"] == "none"
    assert result["run_index"]["promotion_authority"] == "none"
    assert (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8") == ledger_before


def test_ceo_dispatch_receipt_command_is_diagnostic_only(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"

    result = run_ceo_dispatch_receipt(options)

    receipt = result["receipt"]
    assert receipt["model"] == "riskflow_ceo_dispatch_receipt_v0"
    assert receipt["dispatch_mode"] == "diagnostic_only"
    assert receipt["production_effect"] == "none"
    assert receipt["product_language_allowed"] is False
    assert receipt["promotion_authority"] == "none"
    assert receipt["action_contract_source"] == "decision_contract_template"
    assert result["paths"]["dispatch_receipt"].exists()
    assert result["paths"]["dispatch_receipt_report"].exists()
    assert result["paths"]["dispatch_receipt_snapshot"].exists()
    assert receipt["snapshot_path"] == str(result["paths"]["dispatch_receipt_snapshot"])
    assert Path(receipt["snapshot_path"]).parent.name == "dispatch_receipts"
    assert receipt["trust_artifact_fingerprints"]["decision_packet"]["exists"] is True
    assert receipt["trust_artifact_fingerprints"]["action_contract"]["exists"] is False
    assert not (root / "action_contract.yaml").exists()
    assert not (root / "binding_action_result.yaml").exists()
    assert not (root / "ceo_action_ledger.jsonl").exists()


def test_ceo_blocker_stack_orders_stop_approval_and_replay_gaps(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")
    root = options.report_root / "ceo_test"
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_queue_v0",
                "status": "pending_approvals",
                "pending_count": 1,
                "pending_items": [{"approval_id": "clear_stop_request"}],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_replay.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_replay_v0", "status": "replay_gaps", "issues": ["missing_action_ledger_entries"], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_eval_suite.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_eval_suite_v0",
                "status": "fail",
                "score": 50,
                "nine_nine_readiness": {"blocking_case_ids": ["replayable_action_timeline"]},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "memory_delta.yaml").write_text(
        yaml.safe_dump({"memory_delta_required": True, "note_applied": False, "reasons": ["replay_gap"], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump({"debt_count": 3, "next_action": "build_or_run_frozen_validation_executor", "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_blocker_stack(options)

    stack = result["stack"]
    blocker_ids = [item["blocker"] for item in stack["blockers"]]
    assert stack["model"] == "riskflow_ceo_blocker_stack_v0"
    assert stack["status"] == "blocked"
    assert blocker_ids[0] == "stop_requested"
    assert "pending_user_approval" in blocker_ids
    assert "replay_gaps" in blocker_ids
    assert "eval_blocking_case:replayable_action_timeline" in blocker_ids
    assert "memory_delta_unresolved" in blocker_ids
    assert "evidence_debt_open" in blocker_ids
    assert "approval-queue" in stack["next_command"]
    assert result["paths"]["blocker_stack"].exists()
    assert result["paths"]["blocker_stack_report"].exists()
    assert stack["production_effect"] == "none"


def test_ceo_blocker_stack_is_diagnostic_only(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    ledger_before = (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8")
    contract_before = (root / "action_contract.yaml").read_text(encoding="utf-8") if (root / "action_contract.yaml").exists() else ""

    result = run_ceo_blocker_stack(options)

    assert result["paths"]["blocker_stack"].exists()
    assert result["paths"]["blocker_stack_report"].exists()
    assert (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8") == ledger_before
    if contract_before:
        assert (root / "action_contract.yaml").read_text(encoding="utf-8") == contract_before


def test_ceo_incident_register_has_no_incidents_for_clean_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    for name, payload in {
        "dispatch_receipt.yaml": {"model": "riskflow_ceo_dispatch_receipt_v0", "status": "dispatch_allowed", "production_effect": "none"},
        "preflight_gate.yaml": {"model": "riskflow_ceo_preflight_gate_v0", "status": "pass", "blockers": [], "production_effect": "none"},
        "ceo_replay.yaml": {"model": "riskflow_ceo_replay_v0", "status": "replayable", "issues": [], "production_effect": "none"},
        "ceo_eval_suite.yaml": {"model": "riskflow_ceo_eval_suite_v0", "status": "pass", "nine_nine_readiness": {"blocking_case_ids": []}, "production_effect": "none"},
        "artifact_coherence.yaml": {"model": "riskflow_ceo_artifact_coherence_v0", "status": "pass", "issues": [], "production_effect": "none"},
        "guardrail_audit.yaml": {"model": "riskflow_ceo_guardrail_audit_v0", "status": "pass", "violations": [], "production_effect": "none"},
    }.items():
        (root / name).write_text(yaml.safe_dump(payload), encoding="utf-8")
    (root / "ceo_action_ledger.jsonl").write_text("", encoding="utf-8")

    result = run_ceo_operating_incident_register(options)

    register = result["register"]
    assert register["model"] == "riskflow_ceo_operating_incident_register_v0"
    assert register["status"] == "no_open_incidents"
    assert register["incident_count"] == 0
    assert result["paths"]["incident_register"].exists()
    assert result["paths"]["incident_register_report"].exists()


def test_ceo_incident_register_groups_blocked_dispatch_and_replay_failures(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    entries = [
        {"decision": "run_champion_challenger", "action_taken": "blocked_preflight_gate", "status": "blocked", "production_effect": "none"},
        {"decision": "run_champion_challenger", "action_taken": "blocked_preflight_gate", "status": "blocked", "production_effect": "none"},
    ]
    (root / "ceo_action_ledger.jsonl").write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in entries) + "\n",
        encoding="utf-8",
    )
    (root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_dispatch_receipt_v0", "status": "dispatch_blocked", "reason": "stop.request exists", "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_preflight_gate_v0", "status": "blocked", "blockers": [{"blocker": "stop_requested", "category": "stop_request"}], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_replay.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_replay_v0", "status": "replay_gaps", "issues": ["illegal_action_transition"], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_eval_suite.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_eval_suite_v0", "status": "fail", "score": 40, "nine_nine_readiness": {"blocking_case_ids": ["state_machine_legal_transitions"]}, "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_operating_incident_register(options)

    incidents = {item["incident_key"]: item for item in result["register"]["incidents"]}
    assert incidents["blocked_action:blocked_preflight_gate"]["occurrence_count"] == 2
    assert incidents["blocked_action:blocked_preflight_gate"]["severity"] == "high"
    assert incidents["preflight_blocker:stop_requested"]["severity"] == "critical"
    assert incidents["replay_issue:illegal_action_transition"]["owner_command"] == "repair_execute_next_state_transition_policy"
    assert incidents["eval_blocking_case:state_machine_legal_transitions"]["severity"] == "critical"
    assert result["register"]["status"] == "open_incidents"
    assert result["register"]["production_effect"] == "none"


def test_ceo_incident_register_is_diagnostic_only(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    ledger_before = (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8")
    contract_before = (root / "action_contract.yaml").read_text(encoding="utf-8") if (root / "action_contract.yaml").exists() else ""

    result = run_ceo_operating_incident_register(options)

    assert result["paths"]["incident_register"].exists()
    assert result["paths"]["incident_register_report"].exists()
    assert (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8") == ledger_before
    if contract_before:
        assert (root / "action_contract.yaml").read_text(encoding="utf-8") == contract_before


def test_ceo_repair_plan_orders_manual_gate_and_runnable_repairs(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")
    root = options.report_root / "ceo_test"
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_queue_v0",
                "status": "pending_approvals",
                "pending_count": 1,
                "pending_items": [{"approval_id": "clear_stop_request"}],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_replay.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_replay_v0", "status": "replay_gaps", "issues": ["illegal_action_transition"], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_eval_suite.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_eval_suite_v0",
                "status": "fail",
                "score": 40,
                "nine_nine_readiness": {"blocking_case_ids": ["state_machine_legal_transitions"]},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_repair_plan(options)

    plan = result["repair_plan"]
    repair_keys = [item["repair_key"] for item in plan["repair_items"]]
    assert plan["model"] == "riskflow_ceo_repair_plan_v0"
    assert plan["status"] == "manual_gate_first"
    assert plan["manual_gate_required"] is True
    assert plan["top_repair"] == "blocker:stop_requested"
    assert plan["top_repair_kind"] == "manual_gate"
    assert "approval-queue" in plan["next_command"]
    assert "blocker:pending_user_approval" in repair_keys
    assert any(key.startswith("incident:eval_blocking_case:") for key in repair_keys)
    symbolic_items = [item for item in plan["repair_items"] if item["command_kind"] == "implementation_required"]
    assert symbolic_items
    assert all(item["can_execute_autonomously"] is False for item in symbolic_items)
    assert plan["production_effect"] == "none"
    assert plan["runnable_repair_count"] == plan["autonomous_repair_count"]
    assert result["paths"]["repair_plan"].exists()
    assert result["paths"]["repair_plan_report"].exists()


def test_ceo_repair_plan_marks_symbolic_repairs_as_implementation_required(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    plan = ceo_ops.build_ceo_repair_plan(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        blocker_stack={"model": "riskflow_ceo_blocker_stack_v0", "blockers": [], "production_effect": "none"},
        incident_register={
            "model": "riskflow_ceo_operating_incident_register_v0",
            "incidents": [
                {
                    "incident_key": "eval_blocking_case:state_machine_legal_transitions",
                    "severity": "critical",
                    "category": "eval_suite",
                    "owner_command": "repair_failing_eval_suite_case",
                    "closure_condition": "eval case passes",
                    "latest_evidence": {"evidence": "score=40"},
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
    )

    item = plan["repair_items"][0]
    assert plan["status"] == "implementation_repair_required"
    assert plan["next_command"] == ""
    assert item["command_kind"] == "implementation_required"
    assert item["needs_implementation"] is True
    assert item["can_execute_autonomously"] is False
    assert plan["autonomous_repair_count"] == 0
    assert plan["runnable_repair_count"] == 0


def test_ceo_repair_plan_counts_only_runnable_cli_as_autonomous(tmp_path: Path) -> None:
    plan = ceo_ops.build_ceo_repair_plan(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        blocker_stack={
            "model": "riskflow_ceo_blocker_stack_v0",
            "blockers": [
                {
                    "rank": 1,
                    "blocker": "stale_artifacts",
                    "authority": "artifact_coherence",
                    "evidence": "artifact stale",
                    "next_action": "PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id ceo_test",
                    "production_effect": "none",
                }
            ],
            "next_command": "PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id ceo_test",
            "production_effect": "none",
        },
        incident_register={
            "model": "riskflow_ceo_operating_incident_register_v0",
            "incidents": [
                {
                    "incident_key": "replay_issue:illegal_action_transition",
                    "severity": "high",
                    "category": "replay",
                    "owner_command": "repair_execute_next_state_transition_policy",
                    "closure_condition": "replay passes",
                    "latest_evidence": {"evidence": "illegal transition"},
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
    )

    items = {item["repair_key"]: item for item in plan["repair_items"]}
    assert items["blocker:stale_artifacts"]["command_kind"] == "diagnostic_refresh"
    assert items["blocker:stale_artifacts"]["can_execute_autonomously"] is False
    assert items["blocker:stale_artifacts"]["diagnostic_only"] is True
    assert items["incident:replay_issue:illegal_action_transition"]["command_kind"] == "implementation_required"
    assert items["incident:replay_issue:illegal_action_transition"]["can_execute_autonomously"] is False
    assert plan["autonomous_repair_count"] == 0
    assert plan["runnable_repair_count"] == 0
    assert plan["diagnostic_refresh_count"] == 1


def test_ceo_repair_plan_is_diagnostic_only(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    ledger_before = (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8")
    contract_before = (root / "action_contract.yaml").read_text(encoding="utf-8") if (root / "action_contract.yaml").exists() else ""

    result = run_ceo_repair_plan(options)

    assert result["paths"]["repair_plan"].exists()
    assert result["paths"]["repair_plan_report"].exists()
    assert result["repair_plan"]["production_effect"] == "none"
    assert (root / "ceo_action_ledger.jsonl").read_text(encoding="utf-8") == ledger_before
    if contract_before:
        assert (root / "action_contract.yaml").read_text(encoding="utf-8") == contract_before


def test_ceo_action_board_prioritizes_manual_gate_over_safe_dispatch(tmp_path: Path) -> None:
    board = ceo_ops.build_ceo_action_board(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        resumption_brief={
            "resume_status": "safe_for_one_bound_action",
            "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
            "rationale": "clean gates",
        },
        dispatch_receipt={"model": "riskflow_ceo_dispatch_receipt_v0", "status": "dispatch_allowed", "safe_to_dispatch": True},
        blocker_stack={"model": "riskflow_ceo_blocker_stack_v0", "status": "blocked", "top_blocker": "pending_user_approval"},
        repair_plan={
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "manual_gate_first",
            "top_repair": "blocker:pending_user_approval",
            "top_repair_kind": "manual_gate",
            "repair_items": [
                {
                    "repair_key": "blocker:pending_user_approval",
                    "source": "blocker_stack",
                    "command_kind": "manual_gate",
                    "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                    "evidence": "approval required",
                    "can_execute_autonomously": False,
                    "requires_manual_gate": True,
                    "diagnostic_only": False,
                    "needs_implementation": False,
                    "closure_condition": "approval queue clears",
                }
            ],
        },
        executive_kpis={"model": "riskflow_ceo_executive_kpis_v0", "status": "attention_required", "next_action": "wait_for_user_approval"},
    )

    assert board["model"] == "riskflow_ceo_action_board_v0"
    assert board["status"] == "manual_gate_required"
    assert board["autonomy_mode"] == "wait_for_user_or_clear_approval"
    assert board["primary_action"]["action_id"] == "blocker:pending_user_approval"
    assert board["primary_action"]["requires_manual_gate"] is True
    assert board["counts"]["manual_gates"] == 1
    assert board["counts"]["runnable_repairs"] == 1
    assert board["production_effect"] == "none"


def test_ceo_action_board_requires_dispatch_safe_for_bounded_action(tmp_path: Path) -> None:
    board = ceo_ops.build_ceo_action_board(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        resumption_brief={
            "resume_status": "safe_for_one_bound_action",
            "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
            "rationale": "clean gates",
        },
        dispatch_receipt={"model": "riskflow_ceo_dispatch_receipt_v0", "status": "dispatch_blocked", "safe_to_dispatch": False},
        blocker_stack={"model": "riskflow_ceo_blocker_stack_v0", "status": "clear_for_one_bound_action"},
        repair_plan={"model": "riskflow_ceo_repair_plan_v0", "status": "no_repairs_required", "repair_items": []},
        executive_kpis={"model": "riskflow_ceo_executive_kpis_v0", "status": "operating_clear", "next_action": "continue_with_bound_action_dispatch"},
    )

    assert board["status"] == "no_action_available"
    assert board["primary_action"]["action_id"] == "regenerate_action_board"
    assert board["counts"]["runnable_repairs"] == 0
    assert board["counts"]["blocked_actions"] == 1


def test_ceo_action_board_command_writes_operator_surface(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")

    result = run_ceo_action_board(options)

    board = result["action_board"]
    assert board["status"] == "manual_gate_required"
    assert board["primary_action"]["command_kind"] == "manual_gate"
    assert board["counts"]["manual_gates"] >= 1
    assert result["paths"]["action_board"].exists()
    report = result["paths"]["action_board_report"].read_text(encoding="utf-8")
    assert "## Primary Action" in report
    assert "## Prohibited Actions" in report
    assert "Production effect: none." in report


def test_ceo_operator_step_refuses_manual_gate(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")

    result = run_ceo_operator_step(options)

    step = result["operator_step"]
    assert step["model"] == "riskflow_ceo_operator_step_v0"
    assert step["status"] == "blocked_manual_gate"
    assert step["action_attempted"] is False
    assert step["action_executed"] is False
    assert step["primary_action"]["command_kind"] == "manual_gate"
    assert result["paths"]["operator_step"].exists()
    report = result["paths"]["operator_step_report"].read_text(encoding="utf-8")
    assert "Riskflow CEO Operator Step" in report
    assert "Action executed: False" in report
    assert "Production effect: none." in report


def test_ceo_operator_step_executes_one_safe_bounded_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    board_path = root / "action_board.yaml"
    board_report_path = root / "action_board.md"
    binding_path = root / "binding_action_result.yaml"
    calls: list[bool] = []
    boards = [
        {
            "model": "riskflow_ceo_action_board_v0",
            "status": "bounded_action_available",
            "primary_action": {
                "action_id": "resumption_brief_next_command",
                "command_kind": "bounded_dispatch",
                "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
                "can_execute_now": True,
            },
            "production_effect": "none",
        },
        {
            "model": "riskflow_ceo_action_board_v0",
            "status": "diagnostic_refresh_recommended",
            "primary_action": {"action_id": "resumption_brief_next_command", "command_kind": "diagnostic_refresh"},
            "production_effect": "none",
        },
    ]

    def fake_action_board(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "action_board": boards.pop(0),
            "paths": {"action_board": board_path, "action_board_report": board_report_path},
        }

    def fake_execute_next(execute_options: CeoOpsOptions) -> dict[str, object]:
        calls.append(execute_options.apply)
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "action_result": {
                "model": "riskflow_ceo_binding_action_result_v0",
                "decision": "run_champion_challenger",
                "action_taken": "champion_challenger",
                "status": "shadow_comparison_complete",
                "production_effect": "none",
            },
            "paths": {"binding_action_result": binding_path},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_action_board", fake_action_board)
    monkeypatch.setattr(ceo_ops, "run_ceo_execute_next", fake_execute_next)

    result = run_ceo_operator_step(options)

    step = result["operator_step"]
    assert calls == [True]
    assert step["status"] == "bounded_action_executed"
    assert step["action_attempted"] is True
    assert step["action_executed"] is True
    assert step["execution_status"] == "shadow_comparison_complete"
    assert step["execution_action_taken"] == "champion_challenger"
    assert step["after_board_status"] == "diagnostic_refresh_recommended"
    assert result["paths"]["operator_step"].exists()


def test_ceo_operator_brief_writes_plain_english_manual_gate_summary(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")
    run_ceo_operator_step(options)

    result = run_ceo_operator_brief(options)

    brief = result["operator_brief"]
    assert brief["model"] == "riskflow_ceo_operator_brief_v0"
    assert brief["status"] == "waiting_on_manual_gate"
    assert "manual gate" in brief["plain_english_summary"]
    assert brief["current_situation"]["primary_kind"] == "manual_gate"
    assert "approval" in brief["refused_actions"][0]
    assert brief["product_language_allowed"] is False
    assert brief["production_effect"] == "none"
    report = result["paths"]["operator_brief_report"].read_text(encoding="utf-8")
    assert "Plain English" in report
    assert "Refused Actions" in report
    assert "Production effect: none." in report


def test_ceo_eval_fixtures_cover_transition_policy(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)

    result = run_ceo_eval_fixtures(options)

    fixtures = result["fixtures"]
    cases = {item["case_id"]: item for item in fixtures["cases"]}
    assert fixtures["status"] == "pass"
    assert cases["champion_challenger_routes_to_fresh_control"]["observed_transition_status"] == "pass"
    assert cases["champion_challenger_does_not_jump_to_generic_research"]["observed_transition_status"] == "fail"
    assert cases["approval_wait_routes_to_approval_apply"]["observed_transition_status"] == "pass"
    assert cases["contract_repair_routes_back_to_frozen_candidate_validation"]["observed_transition_status"] == "pass"
    assert "stop_requested" in cases["preflight_blocks_stop_request"]["observed_blockers"]
    assert "true_blocker" in cases["preflight_blocks_true_blocker"]["observed_blockers"]
    assert cases["computed_hard_memory_delta_blocks_dispatch"]["observed_blocks"] is True
    assert cases["computed_soft_memory_delta_does_not_block_dispatch"]["observed_blocks"] is False
    assert "requires --apply" in cases["withheld_split_manifest_requires_apply"]["observed_error"]
    assert "requires --apply" in cases["fresh_withheld_snapshot_manifest_requires_apply"]["observed_error"]
    assert "requires --apply" in cases["fresh_withheld_snapshot_declare_requires_apply"]["observed_error"]
    assert fixtures["production_effect"] == "none"
    assert result["paths"]["eval_fixtures"].exists()
    assert result["paths"]["eval_fixtures_report"].exists()


def test_ceo_guardrail_audit_flags_product_language_or_production_effect(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "bad_artifact.yaml").write_text(
        yaml.safe_dump({"model": "bad", "production_effect": "changed_core_signal", "product_language_allowed": True}),
        encoding="utf-8",
    )

    result = run_ceo_guardrail_audit(options)

    audit = result["guardrail_audit"]
    assert audit["status"] == "fail"
    assert audit["violation_count"] == 2
    assert {item["violation"] for item in audit["violations"]} == {
        "non_none_production_effect",
        "product_language_allowed_true",
    }
    assert audit["production_effect"] == "none"


def test_ceo_preflight_gate_blocks_pending_approval(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_preflight_gate(options)

    gate = result["preflight_gate"]
    blockers = [item["blocker"] for item in gate["blockers"]]
    assert gate["status"] == "blocked"
    assert "pending_user_approval" in blockers
    assert "approval_authority" in gate["blocker_categories"]
    assert next(item for item in gate["blockers"] if item["blocker"] == "pending_user_approval")["category"] == "approval_authority"
    assert gate["production_effect"] == "none"


def test_ceo_execute_next_blocks_failed_preflight_guardrail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    (root / "unsafe_product_claim.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_test_bad_artifact_v0",
                "product_language_allowed": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    def fail_champion(*_args, **_kwargs):
        raise AssertionError("execute-next must not dispatch through a failed guardrail preflight")

    monkeypatch.setattr(ceo_ops, "run_ceo_champion_challenger", fail_champion)

    result = run_ceo_execute_next(options)

    action = result["action_result"]
    assert action["action_taken"] == "blocked_preflight_gate"
    assert action["status"] == "blocked"
    assert [item["blocker"] for item in action["preflight_blockers"]] == ["guardrail_audit_failed"]
    assert result["paths"]["preflight_gate"].exists()
    assert result["paths"]["dispatch_receipt"].exists()
    receipt = yaml.safe_load(result["paths"]["dispatch_receipt"].read_text(encoding="utf-8"))
    assert receipt["model"] == "riskflow_ceo_dispatch_receipt_v0"
    assert receipt["status"] == "dispatch_blocked"
    assert receipt["safe_to_dispatch"] is False
    assert receipt["decision"] == action["decision"]
    assert receipt["preflight_blockers"] == ["guardrail_audit_failed"]
    assert receipt["trust_artifact_fingerprints"]["preflight_gate"]["exists"] is True
    assert receipt["trust_artifact_fingerprints"]["action_contract"]["sha256"]
    assert action["dispatch_receipt"]["path"] == str(result["paths"]["dispatch_receipt_snapshot"])
    assert action["dispatch_receipt"]["sha256"] == ceo_ops._file_sha256(result["paths"]["dispatch_receipt_snapshot"])


def test_ceo_execute_next_writes_immutable_dispatch_receipt_snapshot(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=False, stop_reason="governed_recovery_no_supported_specs")

    result = run_ceo_execute_next(options)

    latest_path = result["paths"]["dispatch_receipt"]
    snapshot_path = result["paths"]["dispatch_receipt_snapshot"]
    latest = yaml.safe_load(latest_path.read_text(encoding="utf-8"))
    snapshot = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))
    assert latest_path.exists()
    assert snapshot_path.exists()
    assert snapshot_path.parent.name == "dispatch_receipts"
    assert latest["receipt_id"] == snapshot["receipt_id"]
    assert latest["snapshot_path"] == str(snapshot_path)
    assert result["action_result"]["dispatch_receipt"]["path"] == str(snapshot_path)
    assert result["action_result"]["dispatch_receipt"]["sha256"] == ceo_ops._file_sha256(snapshot_path)


def test_ceo_execute_next_stop_request_overrides_preflight_blockers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")
    root = options.report_root / "ceo_test"
    (root / "unsafe_product_claim.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_test_bad_artifact_v0",
                "product_language_allowed": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    def fail_preflight(*_args, **_kwargs):
        raise AssertionError("execute-next must honor stop requests before preflight")

    monkeypatch.setattr(ceo_ops, "run_ceo_preflight_gate", fail_preflight)

    result = run_ceo_execute_next(options)

    action = result["action_result"]
    assert action["action_taken"] == "blocked_stop_requested"
    assert action["status"] == "blocked"
    assert action["next_allowed_actions"] == ["clear_stop_request_after_user_approval"]
    assert result["paths"]["action_contract"].exists()
    assert result["paths"]["dispatch_receipt"].exists()
    receipt = yaml.safe_load(result["paths"]["dispatch_receipt"].read_text(encoding="utf-8"))
    assert receipt["status"] == "dispatch_blocked"
    assert receipt["reason"] == "stop.request exists"
    assert receipt["preflight_blockers"] == ["stop_requested"]


def test_ceo_execute_next_blocks_unresolved_memory_delta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    (root / "memory_delta.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_memory_delta_v0",
                "status": "memory_delta_required",
                "memory_delta_required": True,
                "note_applied": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    def fail_champion(*_args, **_kwargs):
        raise AssertionError("execute-next must not dispatch with an unresolved memory delta")

    monkeypatch.setattr(ceo_ops, "run_ceo_champion_challenger", fail_champion)

    result = run_ceo_execute_next(options)

    action = result["action_result"]
    assert action["action_taken"] == "blocked_preflight_gate"
    assert action["status"] == "blocked"
    assert [item["blocker"] for item in action["preflight_blockers"]] == ["memory_delta_unresolved"]


def test_ceo_execute_next_computes_missing_memory_delta_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    assert not (root / "memory_delta.yaml").exists()

    trace_path = root / "trace_grade.yaml"
    pass_trace = {"verdict": "pass", "production_effect": "none"}
    trace_path.write_text(yaml.safe_dump(pass_trace), encoding="utf-8")
    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_trace_grade",
        lambda _options: {"grade": pass_trace, "paths": {"trace_grade": trace_path}},
    )
    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_replay",
        lambda _options: {
            "replay": {"status": "replayable", "action_count": 1, "production_effect": "none"},
            "paths": {},
        },
    )
    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_eval_suite",
        lambda _options: {"eval_suite": {"status": "warn", "production_effect": "none"}, "paths": {}},
    )
    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_portfolio_allocator",
        lambda _options: {
            "allocator": {
                "selected_lane": {"lane_id": "fresh_withheld_validation", "score": 90},
                "production_effect": "none",
            },
            "paths": {},
        },
    )

    def fail_champion(*_args, **_kwargs):
        raise AssertionError("execute-next must compute and block on missing memory delta before dispatch")

    monkeypatch.setattr(ceo_ops, "run_ceo_champion_challenger", fail_champion)

    result = run_ceo_execute_next(options)

    action = result["action_result"]
    assert action["action_taken"] == "blocked_preflight_gate"
    assert [item["blocker"] for item in action["preflight_blockers"]] == ["memory_delta_unresolved"]
    persisted = yaml.safe_load((root / "memory_delta.yaml").read_text(encoding="utf-8"))
    assert persisted["status"] == "memory_delta_required"
    assert persisted["memory_delta_required"] is True
    assert persisted["note_applied"] is False
    assert "eval_suite_attention_required" in persisted["reasons"]


def test_ceo_execute_next_failed_trace_blocks_validation_executor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_fresh_withheld_validation_contract",
            "action_taken": "fresh_withheld_validation_contract",
            "status": "fresh_withheld_validation_contract_ready",
            "meaningful_progress": True,
            "next_allowed_actions": ["run_fresh_withheld_validation_executor"],
            "production_effect": "none",
        },
    )
    failed_trace = {
        "model": "riskflow_ceo_trace_grade_v0",
        "verdict": "fail",
        "recommended_next_action": "patch_research_infra",
        "issues": ["synthetic_trace_failure"],
        "production_effect": "none",
    }
    trace_path = root / "trace_grade.yaml"
    trace_path.write_text(yaml.safe_dump(failed_trace), encoding="utf-8")

    def fail_executor(*_args, **_kwargs):
        raise AssertionError("validation executor must not run through a failed trace gate")

    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_trace_grade",
        lambda _options: {"grade": failed_trace, "paths": {"trace_grade": trace_path}},
    )
    monkeypatch.setattr(ceo_ops, "run_ceo_fresh_withheld_validation_executor", fail_executor)

    result = run_ceo_execute_next(options)

    action = result["action_result"]
    assert action["decision"] == "run_fresh_withheld_validation_executor"
    assert action["action_taken"] == "blocked_preflight_gate"
    assert [item["blocker"] for item in action["preflight_blockers"]] == ["trace_grade_failed"]


def test_ceo_memory_delta_writes_plan_without_obsidian_note_by_default(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=False)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(replace(options, apply=True))

    result = run_ceo_memory_delta(options)

    delta = result["memory_delta"]
    assert delta["model"] == "riskflow_ceo_memory_delta_v0"
    assert delta["memory_delta_required"] is True
    assert result["paths"]["memory_delta"].exists()
    assert result["paths"]["memory_delta_report"].exists()
    assert "memory_delta_note" not in result["paths"]
    assert delta["production_effect"] == "none"


def test_ceo_memory_delta_apply_writes_curated_obsidian_note(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_memory_delta(options)

    note_path = result["paths"]["memory_delta_note"]
    assert note_path.exists()
    note = note_path.read_text(encoding="utf-8")
    assert "CEO Memory Delta - ceo_test" in note
    assert "CEO Eval Suite" in note
    assert result["memory_delta"]["note_applied"] is True
    assert result["memory_delta"]["applied_note_sha256"]
    persisted = yaml.safe_load(result["paths"]["memory_delta"].read_text(encoding="utf-8"))
    assert persisted["note_applied"] is True
    assert persisted["applied_note_sha256"] == result["memory_delta"]["applied_note_sha256"]
    assert result["memory_delta"]["production_effect"] == "none"


def test_ceo_preflight_allows_applied_memory_delta() -> None:
    gate = ceo_ops.build_ceo_preflight_gate(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        stop_requested=False,
        true_blocker=False,
        trace_grade={"verdict": "pass"},
        approval_queue={"pending_count": 0},
        replay={"status": "replayable"},
        eval_suite={"status": "pass"},
        guardrail_audit={"status": "pass"},
        memory_delta={"status": "memory_delta_required", "memory_delta_required": True, "note_applied": True},
        heartbeat_budget={"status": "within_time_budget", "budget_elapsed": False},
    )

    assert gate["status"] == "pass"
    assert gate["safe_to_execute"] is True
    assert gate["blockers"] == []


def test_ceo_preflight_blocks_stop_request(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    run_ceo_stop(options, reason="user_requested")

    result = run_ceo_preflight_gate(options)

    gate = result["preflight_gate"]
    blockers = [item["blocker"] for item in gate["blockers"]]
    assert gate["status"] == "blocked"
    assert "stop_requested" in blockers
    assert "runtime_authority" in gate["blocker_categories"]
    assert next(item for item in gate["blockers"] if item["blocker"] == "stop_requested")["severity"] == "blocker"
    assert gate["production_effect"] == "none"


def test_ceo_cli_direct_run_block_obeys_preflight_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.yaml"
    preflight_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "preflight_gate.md"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text("status: blocked\n", encoding="utf-8")
    preflight_report_path.write_text("# blocked\n", encoding="utf-8")

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        return {
            "preflight_gate": {
                "status": "blocked",
                "safe_to_execute": False,
                "blockers": [{"blocker": "stop_requested", "source": "stop.request"}],
            },
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    def fail_run_block(_options):
        raise AssertionError("direct run-block must not run through a failed preflight gate")

    monkeypatch.setattr(cli, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(cli, "run_ceo_run_block", fail_run_block)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="run-block",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=True,
        )
    )

    assert status == 1


def test_ceo_execute_next_runs_champion_challenger_not_another_lab_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)

    def fail_run_lab_ops_run(_lab_options):
        raise AssertionError("execute-next must not run a generic lab block for champion/challenger decisions")

    monkeypatch.setattr(ceo_ops, "run_lab_ops_run", fail_run_lab_ops_run)

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_champion_challenger"
    assert result["action_result"]["action_taken"] == "champion_challenger"
    assert result["paths"]["results"].exists()
    assert result["paths"]["action_ledger"].exists()
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_champion_challenger"
    assert contract["production_effect"] == "none"


def test_ceo_execute_next_blocks_pending_user_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "ready_for_user_approval",
                "approval_required": True,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    def fail_champion(*_args, **_kwargs):
        raise AssertionError("execute-next must not act while approval is pending")

    monkeypatch.setattr(ceo_ops, "run_ceo_champion_challenger", fail_champion)

    result = run_ceo_execute_next(options)

    action = result["action_result"]
    assert action["action_taken"] == "blocked_pending_user_approval"
    assert action["status"] == "blocked"
    assert action["pending_approval_ids"] == ["promotion_proposal"]
    assert action["production_effect"] == "none"
    assert result["paths"]["approval_queue"].exists()


def test_ceo_execute_next_runs_fresh_control_validation_after_champion_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_champion_challenger",
            "action_taken": "champion_challenger",
            "status": "shadow_comparison_complete",
            "meaningful_progress": True,
            "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
            "production_effect": "none",
        },
    )
    (root / "champion_challenger_results.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_champion_challenger_results_v0",
                "status": "shadow_comparison_complete",
                "results": [
                    {
                        "belief_id": "candidate_a",
                        "product_role": "reset_quality",
                        "champion": "core_signal_v0",
                        "challenger": "core_signal_v0_plus_candidate_a",
                        "decision": "needs_fresh_or_control_validation",
                        "available_metric_sources": [
                            {
                                "loop_dir": "reports/lab_ops/ceo_test_lab/lab_loop/session/loop_0001",
                                "ranked": "ranked.csv",
                                "bullish_evidence": "bullish_evidence.yaml",
                                "strict_referee": "strict_referee.csv",
                                "metric_summary": {"role_decision": "needs_fresh_or_control_validation"},
                            }
                        ],
                        "metric_summary": {"role_decision": "needs_fresh_or_control_validation"},
                    }
                ],
                "next_action": "run_fresh_or_control_validation_for_promising_shadow_challengers",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    def fail_run_champion_challenger(_options):
        raise AssertionError("execute-next must not repeat champion/challenger after fresh/control next action")

    monkeypatch.setattr(ceo_ops, "run_ceo_champion_challenger", fail_run_champion_challenger)

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_fresh_or_control_validation_for_promising_shadow_challengers"
    assert result["action_result"]["action_taken"] == "fresh_control_validation_plan"
    assert result["paths"]["plan"].exists()
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_fresh_or_control_validation_for_promising_shadow_challengers"
    assert contract["allowed_command"] == "riskflow ceo fresh-control-validation"


def test_ceo_execute_next_routes_after_fresh_control_plan_requires_fresh_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = replace(_options(tmp_path, apply=True), data_dir=tmp_path / "data" / "raw")
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_fresh_or_control_validation_for_promising_shadow_challengers",
            "action_taken": "fresh_control_validation_plan",
            "status": "fresh_data_required",
            "meaningful_progress": True,
            "next_allowed_actions": ["import_or_curate_fresh_ohlcv_data"],
            "production_effect": "none",
        },
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )

    def fail_run_champion_challenger(_options):
        raise AssertionError("execute-next must not repeat champion/challenger after fresh data is required")

    monkeypatch.setattr(ceo_ops, "run_ceo_champion_challenger", fail_run_champion_challenger)

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "request_fresh_data"
    assert result["action_result"]["action_taken"] == "fresh_data_preflight"
    assert result["action_result"]["status"] == "not_ready"
    assert result["action_result"]["next_allowed_actions"] == ["import_or_curate_fresh_ohlcv_data"]
    assert result["preflight"]["safe_to_run_fresh_validation"] is False
    assert result["paths"]["preflight"].exists()


def test_ceo_execute_next_routes_after_safe_preflight_to_frozen_specs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "configs" / "test_universe.yaml"
    data_dir = tmp_path / "data" / "raw"
    _write_test_universe(config_path, min_active_members=2)
    _write_ohlcv_csv(data_dir / "AAA_1d.csv")
    _write_ohlcv_csv(data_dir / "BBB_1d.csv")
    options = replace(
        _options(tmp_path, apply=True),
        config_path=config_path,
        data_dir=data_dir,
        timeframes=("1d",),
    )
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_fresh_control_plan(root)
    run_ceo_fresh_data_preflight(_authorized(options, "request_fresh_data"))

    def fail_run_champion_challenger(_options):
        raise AssertionError("execute-next must not repeat champion/challenger after safe fresh data preflight")

    monkeypatch.setattr(ceo_ops, "run_ceo_champion_challenger", fail_run_champion_challenger)

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_frozen_candidate_validation"
    assert result["action_result"]["action_taken"] == "frozen_candidate_validation_scaffold"
    assert result["plan"]["status"] == "frozen_validation_specs_ready"
    assert result["paths"]["plan"].exists()
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_frozen_candidate_validation"
    assert contract["allowed_command"] == "riskflow ceo frozen-candidate-validation"


def test_ceo_execute_next_routes_after_source_replay_to_frozen_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_frozen_validation_executor",
            "action_taken": "frozen_validation_source_replay",
            "status": "source_replay_completed",
            "meaningful_progress": True,
            "next_allowed_actions": ["run_frozen_validation_rerun"],
            "production_effect": "none",
        },
    )

    def fake_run_frozen_validation_rerun(_options):
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "rerun": {"status": "blocked_missing_rerun_grid", "production_effect": "none"},
            "action_result": {
                "decision": "run_frozen_validation_rerun",
                "action_taken": "frozen_validation_adapter_rerun",
                "status": "blocked_missing_rerun_grid",
                "production_effect": "none",
            },
            "paths": {},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_frozen_validation_rerun", fake_run_frozen_validation_rerun)

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_frozen_validation_rerun"
    assert result["action_result"]["action_taken"] == "frozen_validation_adapter_rerun"
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_frozen_validation_rerun"
    assert contract["allowed_command"] == "riskflow ceo frozen-validation-rerun"


def test_ceo_execute_next_routes_after_adapter_rerun_to_fresh_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_frozen_validation_rerun",
            "action_taken": "frozen_validation_adapter_rerun",
            "status": "adapter_rerun_completed_not_promotion_eligible",
            "meaningful_progress": True,
            "next_allowed_actions": ["run_fresh_withheld_validation_contract"],
            "production_effect": "none",
        },
    )

    def fake_run_fresh_withheld_validation_contract(_options):
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "contract": {"status": "fresh_withheld_validation_contract_ready", "production_effect": "none"},
            "action_result": {
                "decision": "run_fresh_withheld_validation_contract",
                "action_taken": "fresh_withheld_validation_contract",
                "status": "fresh_withheld_validation_contract_ready",
                "production_effect": "none",
            },
            "paths": {},
        }

    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_fresh_withheld_validation_contract",
        fake_run_fresh_withheld_validation_contract,
    )

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_fresh_withheld_validation_contract"
    assert result["action_result"]["action_taken"] == "fresh_withheld_validation_contract"
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_fresh_withheld_validation_contract"
    assert contract["allowed_command"] == "riskflow ceo fresh-withheld-validation-contract"


def test_ceo_execute_next_routes_contract_input_repair_to_frozen_specs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_fresh_withheld_validation_contract",
            "action_taken": "fresh_withheld_validation_contract",
            "status": "blocked_missing_inputs",
            "meaningful_progress": False,
            "next_allowed_actions": ["repair_fresh_withheld_contract_inputs"],
            "production_effect": "none",
        },
    )

    def fake_run_frozen_candidate_validation(_options):
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "plan": {"status": "blocked_missing_inputs", "production_effect": "none"},
            "action_result": {
                "decision": "run_frozen_candidate_validation",
                "action_taken": "frozen_candidate_validation_scaffold",
                "status": "blocked_missing_inputs",
                "production_effect": "none",
            },
            "paths": {},
        }

    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_frozen_candidate_validation",
        fake_run_frozen_candidate_validation,
    )

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_frozen_candidate_validation"
    assert result["action_result"]["action_taken"] == "frozen_candidate_validation_scaffold"
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_frozen_candidate_validation"
    assert contract["allowed_command"] == "riskflow ceo frozen-candidate-validation"


def test_ceo_replay_maps_contract_input_repair_to_frozen_specs() -> None:
    checks = ceo_ops._build_ceo_state_transition_checks(
        [
            {
                "decision": "run_fresh_withheld_validation_contract",
                "status": "blocked_missing_inputs",
                "next_allowed_actions": ["repair_fresh_withheld_contract_inputs"],
                "production_effect": "none",
            },
            {
                "decision": "run_frozen_candidate_validation",
                "status": "blocked_missing_inputs",
                "next_allowed_actions": ["request_fresh_data"],
                "production_effect": "none",
            },
        ]
    )

    assert checks[0]["status"] == "pass"
    assert checks[0]["legal_next_decisions"] == ["run_frozen_candidate_validation"]


def test_ceo_execute_next_routes_after_fresh_contract_to_executor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_fresh_withheld_validation_contract",
            "action_taken": "fresh_withheld_validation_contract",
            "status": "fresh_withheld_validation_contract_ready",
            "meaningful_progress": True,
            "next_allowed_actions": ["run_fresh_withheld_validation_executor"],
            "production_effect": "none",
        },
    )

    def fake_run_fresh_withheld_validation_executor(_options):
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "execution": {"status": "blocked_missing_snapshot_manifest", "production_effect": "none"},
            "action_result": {
                "decision": "run_fresh_withheld_validation_executor",
                "action_taken": "fresh_withheld_validation_executor",
                "status": "blocked_missing_snapshot_manifest",
                "production_effect": "none",
            },
            "paths": {},
        }

    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_fresh_withheld_validation_executor",
        fake_run_fresh_withheld_validation_executor,
    )

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_fresh_withheld_validation_executor"
    assert result["action_result"]["action_taken"] == "fresh_withheld_validation_executor"
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_fresh_withheld_validation_executor"
    assert contract["allowed_command"] == "riskflow ceo fresh-withheld-validation-executor"


def test_ceo_execute_next_routes_after_missing_snapshot_to_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_fresh_withheld_validation_executor",
            "action_taken": "fresh_withheld_validation_executor",
            "status": "blocked_missing_snapshot_manifest",
            "meaningful_progress": True,
            "next_allowed_actions": ["run_fresh_withheld_snapshot_manifest"],
            "production_effect": "none",
        },
    )

    def fake_run_fresh_withheld_snapshot_manifest(_options):
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "manifest": {"status": "draft_requires_manual_snapshot_authority", "production_effect": "none"},
            "action_result": {
                "decision": "run_fresh_withheld_snapshot_manifest",
                "action_taken": "fresh_withheld_snapshot_manifest",
                "status": "draft_requires_manual_snapshot_authority",
                "production_effect": "none",
            },
            "paths": {},
        }

    def fake_preflight(_options, *, enforce_memory_delta=False):
        assert enforce_memory_delta is True
        preflight_path = root / "preflight_gate.yaml"
        preflight_report_path = root / "preflight_gate.md"
        preflight_path.write_text("status: pass\n", encoding="utf-8")
        preflight_report_path.write_text("# pass\n", encoding="utf-8")
        return {
            "preflight_gate": {"status": "pass", "safe_to_execute": True, "blockers": []},
            "paths": {"preflight_gate": preflight_path, "preflight_gate_report": preflight_report_path},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_preflight_gate", fake_preflight)
    monkeypatch.setattr(
        ceo_ops,
        "run_ceo_fresh_withheld_snapshot_manifest",
        fake_run_fresh_withheld_snapshot_manifest,
    )

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_fresh_withheld_snapshot_manifest"
    assert result["action_result"]["action_taken"] == "fresh_withheld_snapshot_manifest"
    contract = yaml.safe_load(result["paths"]["action_contract"].read_text(encoding="utf-8"))
    assert contract["decision"] == "run_fresh_withheld_snapshot_manifest"
    assert contract["allowed_command"] == "riskflow ceo fresh-withheld-snapshot-manifest"


def test_ceo_execute_next_routes_patch_research_infra_to_bounded_plan(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=False, stop_reason="governed_recovery_no_supported_specs")

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "patch_research_infra"
    assert result["action_result"]["action_taken"] == "research_infra_patch_plan"
    assert result["action_result"]["status"] == "blocked_missing_recovery_inputs"
    assert result["paths"]["plan"].exists()
    assert result["plan"]["missing_inputs"] == ["evidence_mart", "belief_graph"]
    assert result["paths"]["action_contract"].exists()
    assert result["paths"]["dispatch_receipt"].exists()
    receipt = yaml.safe_load(result["paths"]["dispatch_receipt"].read_text(encoding="utf-8"))
    assert receipt["status"] == "dispatch_allowed"
    assert receipt["safe_to_dispatch"] is True
    assert result["action_result"]["dispatch_receipt"]["path"] == str(result["paths"]["dispatch_receipt_snapshot"])
    assert result["action_result"]["dispatch_receipt"]["sha256"] == ceo_ops._file_sha256(result["paths"]["dispatch_receipt_snapshot"])
    assert result["paths"]["queue"].exists()
    assert result["paths"]["audit"].exists()


def test_ceo_execute_next_routes_broaden_hypothesis_source_to_bounded_plan(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=False, stop_reason="")

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "broaden_hypothesis_source"
    assert result["action_result"]["action_taken"] == "hypothesis_source_broadening_plan"
    assert result["action_result"]["status"] == "no_broadening_sources"
    assert result["plan"]["compiled_count"] == 0
    assert result["plan"]["product_language_allowed"] is False
    assert result["paths"]["plan"].exists()
    assert result["paths"]["queue"].exists()


def test_ceo_execute_next_blocks_when_self_audit_requires_intervention(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_self_audit_v0",
                "intervention_required": True,
                "intervention": "build_missing_capability_or_change_strategy_before_more_lab_blocks",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "run_champion_challenger"
    assert result["action_result"]["action_taken"] == "blocked_self_audit_intervention_required"
    assert result["action_result"]["status"] == "blocked"
    assert result["action_result"]["meaningful_progress"] is False
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_execute_next_resolves_self_audit_intervention_route(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_champion_challenger",
            "action_taken": "blocked_self_audit_intervention_required",
            "status": "blocked",
            "meaningful_progress": False,
            "next_allowed_actions": ["resolve_ceo_self_audit_intervention"],
            "production_effect": "none",
        },
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_self_audit_v0",
                "intervention_required": True,
                "intervention": "build_missing_capability_or_change_strategy_before_more_lab_blocks",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "resolve_ceo_self_audit_intervention"
    assert result["action_result"]["action_taken"] == "self_audit_intervention_routed"
    assert result["action_result"]["status"] == "intervention_routed"
    assert result["action_result"]["production_effect"] == "none"


def test_ceo_trace_grade_accepts_fresh_control_next_action(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "decision": "run_champion_challenger",
                "action_taken": "champion_challenger",
                "status": "shadow_comparison_complete",
                "meaningful_progress": True,
                "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_action_ledger.jsonl").write_text("", encoding="utf-8")

    result = run_ceo_trace_grade(options)

    assert result["paths"]["trace_grade"].exists()
    assert result["paths"]["trace_grade_report"].exists()
    assert result["grade"]["verdict"] == "pass"
    assert "unsupported_next_action" not in result["grade"]["issues"]
    assert result["grade"]["unsupported_next_actions"] == []
    assert result["grade"]["bounded_executor_next_actions"] == ["run_fresh_or_control_validation_for_promising_shadow_challengers"]
    assert result["grade"]["manual_next_actions"] == []
    assert result["grade"]["production_effect"] == "none"
    assert result["grade"]["trace_scope"] == "process_only"
    assert result["grade"]["product_evidence_status"] == "not_evaluated"
    assert result["grade"]["product_language_allowed"] is False


def test_ceo_trace_grade_accepts_fresh_withheld_contract_repair_action(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    _write_action_result_fixture(
        root,
        {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_fresh_withheld_validation_contract",
            "action_taken": "fresh_withheld_validation_contract",
            "status": "blocked_missing_inputs",
            "meaningful_progress": False,
            "next_allowed_actions": ["repair_fresh_withheld_contract_inputs"],
            "production_effect": "none",
        },
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_trace_grade(options)

    assert "unsupported_next_action" not in result["grade"]["issues"]
    assert result["grade"]["unsupported_next_actions"] == []
    assert result["grade"]["bounded_executor_next_actions"] == ["repair_fresh_withheld_contract_inputs"]
    assert result["grade"]["production_effect"] == "none"


def test_ceo_trace_grade_flags_repeated_prior_failure(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    current = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-05T00:00:02Z",
        "decision": "run_champion_challenger",
        "action_taken": "blocked_self_audit_intervention_required",
        "status": "blocked",
        "meaningful_progress": False,
        "next_allowed_actions": ["resolve_ceo_self_audit_intervention"],
        "production_effect": "none",
    }
    prior = {
        **current,
        "generated_at": "2026-06-05T00:00:01Z",
    }
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(current), encoding="utf-8")
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_contract_v0",
                "decision": "run_champion_challenger",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_action_ledger.jsonl").write_text(
        json.dumps(prior, sort_keys=True) + "\n" + json.dumps(current, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = run_ceo_trace_grade(options)

    assert result["grade"]["criteria"]["failure_avoidance_status"] == "repeated_prior_failure"
    assert result["grade"]["failure_avoidance"]["repeated_prior_failure"] is True
    assert "repeated_prior_failure" in result["grade"]["issues"]


def test_ceo_trace_grade_flags_manual_gate_loop_meltdown(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    current = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-05T00:00:02Z",
        "decision": "import_or_curate_fresh_ohlcv_data",
        "action_taken": "blocked_manual_data_import_required",
        "status": "manual_gate",
        "meaningful_progress": False,
        "next_allowed_actions": ["request_fresh_data"],
        "production_effect": "none",
    }
    prior = {
        **current,
        "generated_at": "2026-06-05T00:00:01Z",
    }
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(current), encoding="utf-8")
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_contract_v0",
                "decision": "import_or_curate_fresh_ohlcv_data",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_action_ledger.jsonl").write_text(
        json.dumps(prior, sort_keys=True) + "\n" + json.dumps(current, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = run_ceo_trace_grade(options)

    assert result["grade"]["loop_meltdown"]["strategy_change_required"] is True
    assert result["grade"]["loop_meltdown"]["manual_gate_count"] == 2
    assert result["grade"]["recommended_next_action"] == "stop_for_manual_data_import"
    assert "loop_meltdown_strategy_change_required" in result["grade"]["issues"]


def test_ceo_trace_grade_flags_action_contract_mismatch(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "decision": "run_champion_challenger",
                "action_taken": "champion_challenger",
                "status": "shadow_comparison_complete",
                "meaningful_progress": True,
                "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_contract_v0",
                "decision": "continue_governed_research",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_action_ledger.jsonl").write_text("", encoding="utf-8")

    result = run_ceo_trace_grade(options)

    assert result["grade"]["verdict"] == "warn"
    assert "action_contract_mismatch" in result["grade"]["issues"]
    assert result["grade"]["criteria"]["action_contract_present"] is True


def test_ceo_flight_dashboard_writes_plain_state_summary(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)

    result = run_ceo_flight_dashboard(options)

    assert result["paths"]["dashboard"].exists()
    assert result["paths"]["dashboard_report"].exists()
    dashboard = result["dashboard"]
    assert dashboard["model"] == "riskflow_ceo_flight_dashboard_v0"
    assert dashboard["last_decision"] == "run_champion_challenger"
    assert dashboard["trace_grade"]["product_language_allowed"] is False
    assert dashboard["product_delta"]["product_language_allowed"] is False
    assert dashboard["production_effect"] == "none"
    report = result["paths"]["dashboard_report"].read_text(encoding="utf-8")
    assert "Riskflow CEO Flight Dashboard" in report
    assert "This dashboard summarizes CEO process state. It is not product validation." in report


def test_ceo_operating_dashboard_writes_portfolio_snapshot(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)

    result = run_ceo_operating_dashboard(options)

    dashboard = result["dashboard"]
    assert dashboard["model"] == "riskflow_ceo_operating_dashboard_v0"
    assert dashboard["candidate_portfolio_count"] >= 1
    assert dashboard["capability_backlog_count"] >= 1
    assert dashboard["candidate_portfolio"][0]["production_effect"] == "none"
    assert dashboard["product_language_allowed"] is False
    assert dashboard["product_governance"]["product_language_allowed"] is False
    assert result["paths"]["dashboard"].exists()
    assert result["paths"]["dashboard_report"].exists()
    report = result["paths"]["dashboard_report"].read_text(encoding="utf-8")
    assert "Riskflow CEO Operating Dashboard" in report
    assert "Validation Gate" in report
    assert "Executive KPIs" in report
    assert "Role Orchestration" in report


def test_ceo_capability_backlog_writes_standalone_infra_queue(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)

    result = run_ceo_capability_backlog(options)

    backlog = result["backlog"]
    assert backlog["model"] == "riskflow_ceo_capability_backlog_v0"
    assert backlog["status"] == "open_items"
    assert backlog["backlog_count"] >= 1
    assert backlog["items"][0]["production_effect"] == "none"
    assert result["paths"]["backlog"].exists()
    assert result["paths"]["backlog_report"].exists()


def test_ceo_capability_backlog_routes_source_replay_to_fresh_executor_gap(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "frozen_candidate_validation_plan.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_frozen_candidate_validation_v0",
                "status": "frozen_validation_specs_ready",
                "execution_status": "source_replay_completed",
                "validation_result": "source_replay_only_not_promotion_eligible",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_capability_backlog(options)

    assert result["backlog"]["items"][0]["kind"] == "fresh_validation_executor_gap"
    assert result["backlog"]["items"][0]["capability"] == "fresh_or_withheld_validation_executor"
    assert result["backlog"]["items"][0]["production_effect"] == "none"


def test_ceo_capability_backlog_prioritizes_ready_fresh_contract_executor_gap(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "fresh_withheld_validation_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_fresh_withheld_validation_contract_v0",
                "status": "fresh_withheld_validation_contract_ready",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_capability_backlog(options)

    assert result["backlog"]["items"][0]["kind"] == "fresh_withheld_snapshot_manifest_gap"
    assert result["backlog"]["items"][0]["capability"] == "fresh_withheld_snapshot_manifest"
    assert "fresh_withheld_snapshot_manifest.yaml" in result["backlog"]["items"][0]["acceptance_criteria"][0]
    assert result["backlog"]["items"][0]["production_effect"] == "none"


def test_ceo_review_writes_decision_packet_for_product_candidate(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=True)

    result = run_ceo_review(options)

    assert result["decision"]["decision"] == "run_champion_challenger"
    assert result["paths"]["latest_decision_packet"].exists()
    assert result["paths"]["product_delta"].exists()
    assert result["paths"]["champion_challenger_action_plan"].exists()
    packet = result["paths"]["latest_decision_packet"].read_text(encoding="utf-8")
    assert "Riskflow CEO Decision Packet" in packet
    assert "Chart-facing value: shadow_product_candidate_pipeline" in packet
    assert "Product language allowed: False" in packet
    heartbeat = yaml.safe_load(result["paths"]["heartbeat_status"].read_text(encoding="utf-8"))
    assert heartbeat["last_block_number"] == 1
    assert heartbeat["last_decision"] == "run_champion_challenger"
    assert heartbeat["continue_recommended"] is True


def test_ceo_decision_quality_explains_selected_action_and_alternatives(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)

    result = run_ceo_decision_quality(options)

    quality = result["decision_quality"]
    alternatives = {item["action_id"]: item for item in quality["alternatives"]}
    assert quality["model"] == "riskflow_ceo_decision_quality_v0"
    assert quality["selected_action"] == "run_champion_challenger"
    assert quality["expected_artifact"] == "champion_challenger_results.yaml"
    assert quality["confidence"] in {"high", "medium", "low"}
    assert quality["runner_up_action"]
    assert alternatives["run_champion_challenger"]["selected"] is True
    assert alternatives["run_champion_challenger"]["evidence"]["candidate_count"] >= 1
    assert alternatives["broaden_hypothesis_source"]["why_not_selected"]
    assert quality["production_effect"] == "none"
    assert result["paths"]["decision_quality"].exists()
    report = result["paths"]["decision_quality_report"].read_text(encoding="utf-8")
    assert "Riskflow CEO Decision Quality" in report
    assert "## Alternatives" in report
    assert "Production effect: none." in report


def test_ceo_decision_quality_uses_previous_next_action_override(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "decision": "run_champion_challenger",
                "status": "capability_gap",
                "next_allowed_actions": ["patch_research_infra"],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_decision_quality(options)

    quality = result["decision_quality"]
    assert quality["selected_action"] == "patch_research_infra"
    assert quality["expected_artifact"] == "research_infra_patch_plan.yaml"
    assert any(item["action_id"] == "run_champion_challenger" for item in quality["alternatives"])


def test_ceo_decision_quality_includes_specialized_selected_route(tmp_path: Path) -> None:
    quality = ceo_ops.build_ceo_decision_quality(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        company_status={"lab_status": {"stop_reason": ""}, "governance": {"open_lanes": []}, "true_blocker": False},
        product_delta={"candidate_count": 1, "chart_facing_value_status": "shadow_product_candidate_pipeline"},
        infra_delta={"infra_delta_status": "clear"},
        decision={
            "decision": "run_frozen_candidate_validation",
            "rationale": "Previous validation plan requested frozen specs.",
            "production_effect": "none",
        },
    )

    selected = [item for item in quality["alternatives"] if item["selected"]]
    assert quality["selected_action"] == "run_frozen_candidate_validation"
    assert quality["expected_artifact"] == "frozen_candidate_validation_plan.yaml"
    assert selected[0]["action_id"] == "run_frozen_candidate_validation"
    assert selected[0]["expected_artifact"] == "frozen_candidate_validation_plan.yaml"


def test_ceo_report_includes_operating_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)

    result = run_ceo_report(options)

    assert result["paths"]["report"].exists()
    assert result["paths"]["trace_grade_report"].exists()
    assert result["paths"]["operating_dashboard_report"].exists()
    assert result["paths"]["mission_score_report"].exists()
    assert result["paths"]["strategy_capital_dashboard_report"].exists()
    assert result["paths"]["decision_quality_report"].exists()
    assert result["paths"]["replay_report"].exists()
    assert result["paths"]["eval_suite_report"].exists()
    assert result["paths"]["guardrail_audit_report"].exists()
    assert result["paths"]["preflight_gate_report"].exists()
    assert result["paths"]["dispatch_receipt_report"].exists()
    assert result["paths"]["blocker_stack_report"].exists()
    assert result["paths"]["incident_register_report"].exists()
    assert result["paths"]["repair_plan_report"].exists()
    assert result["paths"]["action_board_report"].exists()
    assert result["paths"]["operator_brief_report"].exists()
    assert result["paths"]["artifact_coherence_report"].exists()
    assert result["paths"]["resumption_brief_report"].exists()
    assert result["paths"]["approval_queue_report"].exists()
    assert result["paths"]["executive_kpis_report"].exists()
    assert result["paths"]["role_task_queue_report"].exists()
    assert result["paths"]["role_dispatch_report"].exists()
    assert result["paths"]["capability_backlog_report"].exists()
    assert result["paths"]["fresh_withheld_validation_contract_report"].exists()
    assert result["paths"]["promotion_proposal_report"].exists()
    assert result["paths"]["evidence_debt_register_report"].exists()
    report = result["paths"]["report"].read_text(encoding="utf-8")
    assert "CEO Operating Snapshot" in report
    assert "Mission score" in report
    assert "Strategy capital dashboard" in report
    assert "Strategy capital bucket" in report
    assert "Strategy capital action" in report
    assert "Decision quality" in report
    assert "Decision quality selected action" in report
    assert "Decision quality confidence" in report
    assert "Decision quality runner-up" in report
    assert "Replay status" in report
    assert "Eval suite status" in report
    assert "9.9 readiness" in report
    assert "Guardrail audit status" in report
    assert "Preflight status" in report
    assert "Dispatch receipt" in report
    assert "Dispatch receipt status" in report
    assert "Dispatch safe to dispatch" in report
    assert "Blocker stack" in report
    assert "Blocker stack status" in report
    assert "Top blocker" in report
    assert "Operating incident register" in report
    assert "Operating incidents" in report
    assert "Repair plan" in report
    assert "Repair plan status" in report
    assert "Runnable repairs" in report
    assert "Diagnostic refreshes" in report
    assert "Top repair" in report
    assert "Top repair kind" in report
    assert "Repair next command" in report
    assert "Action board" in report
    assert "Action board status" in report
    assert "Action board primary action" in report
    assert "Action board primary kind" in report
    assert "Action board command" in report
    assert "Operator brief" in report
    assert "Operator brief status" in report
    assert "Operator brief summary" in report
    assert "Artifact coherence status" in report
    assert "Resumption status" in report
    assert "Resumption next command" in report
    assert "Approval queue" in report
    assert "Executive KPIs" in report
    assert "Role task queue" in report
    assert "Role dispatch" in report
    assert "Pending approvals" in report
    assert "Role tasks" in report
    assert "Role dispatch packets" in report
    assert "Fresh/withheld contract status" in report
    assert "Promotion proposal status" in report
    assert "Evidence debt" in report


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

    first = run_ceo_run_block(_authorized(options, "continue_governed_research"))
    runtime_root = options.lab_ops_runtime_root / "ceo_test_lab"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "lab_state.json").write_text("{}", encoding="utf-8")
    second = run_ceo_run_block(_authorized(options, "continue_governed_research"))

    root = options.report_root / "ceo_test"
    assert first["review"]["block_number"] == 1
    assert second["review"]["block_number"] == 2
    assert (root / "executive_decision_packet_0001.md").exists()
    assert (root / "executive_decision_packet_0002.md").exists()
    assert calls[0].resume is False
    assert calls[1].resume is True


def test_ceo_heartbeat_status_writes_status_without_new_packet(tmp_path: Path) -> None:
    options = _options(tmp_path)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    (root / "heartbeat_status.yaml").unlink()
    packets_before = sorted(root.glob("executive_decision_packet_*.md"))

    status = run_ceo_heartbeat_status(options)

    packets_after = sorted(root.glob("executive_decision_packet_*.md"))
    assert status["from_file"] is False
    assert status["paths"]["heartbeat_status"].exists()
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
        run_ceo_run_block(_authorized(options, "continue_governed_research"))


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
