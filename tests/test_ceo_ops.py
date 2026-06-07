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
    run_ceo_org_progress_score,
    run_ceo_operating_dashboard,
    run_ceo_operating_incident_register,
    run_ceo_operator_brief,
    run_ceo_operator_step,
    run_ceo_patch_research_infra,
    run_ceo_plan,
    run_ceo_portfolio_allocator,
    run_ceo_preflight_gate,
    run_ceo_promotion_proposal,
    run_ceo_repair_apply,
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
    action_contract = {
        "model": "riskflow_ceo_action_contract_v0",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "run_id": run_id,
        "lab_run_id": lab_run_id,
        "decision": enriched.get("decision", ""),
        "allowed_command": "test_fixture",
        "allowed_scope": "test fixture action contract",
        "input_artifacts": [],
        "expected_artifacts": ["binding_action_result.yaml"],
        "stop_conditions": [],
        "forbidden_changes": [],
        "production_effect": "none",
    }
    (root / "action_contract.yaml").write_text(yaml.safe_dump(action_contract), encoding="utf-8")
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
            name: {
                "path": str(root / f"{name}.yaml"),
                "exists": (root / f"{name}.yaml").exists(),
                "sha256": _sha256(root / f"{name}.yaml") if (root / f"{name}.yaml").exists() else "",
            }
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
    (root / "memory_delta.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_memory_delta_v0",
                "generated_at": "2026-06-06T00:00:00+00:00",
                "run_id": run_id,
                "lab_run_id": lab_run_id,
                "status": "no_memory_delta_required",
                "memory_delta_required": False,
                "note_applied": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )


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


def test_ceo_cli_artifact_coherence_advisory_status_exits_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    artifact_path = root / "artifact_coherence.yaml"
    report_path = root / "artifact_coherence.md"
    artifact_path.write_text("status: pass_with_advisory_issues\n", encoding="utf-8")
    report_path.write_text("# advisory\n", encoding="utf-8")

    def fake_artifact_coherence(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "coherence": {
                "status": "pass_with_advisory_issues",
                "issue_count": 2,
                "hard_issue_count": 0,
                "advisory_issue_count": 2,
                "production_effect": "none",
            },
            "paths": {"artifact_coherence": artifact_path, "artifact_coherence_report": report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_artifact_coherence", fake_artifact_coherence)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="artifact-coherence",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            apply=False,
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
        trace_grade={
            "verdict": "pass",
            "score": 91,
            "recommended_next_action": "continue_with_one_bound_ceo_action",
            "issues": [],
            "criteria": {"manual_data_import_required": False},
        },
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
        trace_grade={
            "verdict": "pass",
            "score": 91,
            "recommended_next_action": "continue_with_one_bound_ceo_action",
            "issues": [],
            "criteria": {"manual_data_import_required": False},
        },
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


def test_ceo_promotion_proposal_does_not_treat_complete_review_closure_as_approval(tmp_path: Path) -> None:
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
                "model": "riskflow_ceo_specialist_result_v0",
                "role_id": "product_translator",
                "task_id": "product_task",
                "status": "complete",
                "finding": "Visual-review evidence is missing, so product language is not allowed.",
                "evidence_refs": ["champion_challenger_visual_review_queue.yaml"],
                "recommended_next_action": "complete_champion_challenger_visual_review",
                "product_language_allowed": False,
                "production_effect": "none",
                "promotion_authority": "none",
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
    gate = proposal["specialist_review_gate"]
    product_result = next(item for item in gate["review_results"] if item["role_id"] == "product_translator")
    assert proposal["status"] == "blocked_missing_promotion_evidence"
    assert "completed_specialist_reviews" in proposal["missing_evidence"]
    assert gate["status"] == "missing_specialist_reviews"
    assert gate["missing_roles"] == ["product_translator_or_risk_officer"]
    assert product_result["status"] == "rejected"
    assert "review_not_approving" in product_result["issues"]


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
        trace_grade={
            "verdict": "pass",
            "score": 91,
            "recommended_next_action": "continue_with_one_bound_ceo_action",
            "issues": [],
            "criteria": {"manual_data_import_required": False},
        },
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
    assert queue["top_pending_approval_id"] == "promotion_proposal"
    assert queue["top_pending_approval_record_command"].endswith(
        "approval-record --run-id ceo_test --approval-id promotion_proposal --decision <approved|rejected> --user-confirmed"
    )
    assert queue["top_pending_approval_apply_command"].endswith(
        "approval-apply --run-id ceo_test --approval-id promotion_proposal --user-confirmed --apply"
    )
    assert queue["pending_items"][0]["approval_authority"] == "user_only"
    assert queue["product_language_allowed"] is False
    assert queue["production_effect"] == "none"
    assert result["paths"]["queue"].exists()
    assert result["paths"]["queue_report"].exists()
    assert result["paths"]["approval_status"].exists()
    report = result["paths"]["queue_report"].read_text(encoding="utf-8")
    assert "approval authority: user_only" in report
    assert "reason: promotion proposal is ready for user review" in report
    assert "required user decision: approve_or_reject_promotion_after_review" in report
    assert "fingerprint:" in report
    assert "apply command: `PYTHONPATH=src python3 -m riskflow ceo approval-apply --run-id ceo_test --approval-id promotion_proposal --user-confirmed --apply`" in report
    assert "closure steps: User decides approved or rejected." in report


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
    assert ledger_entry["source_artifact"] == "promotion_proposal.yaml"
    assert ledger_entry["approval_item_fingerprint"]


def test_ceo_approval_record_rejects_unknown_or_not_pending_approval_id(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "promotion_proposal.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_promotion_proposal_v0",
                "status": "blocked_missing_evidence",
                "approval_required": False,
                "product_language_allowed": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not currently pending"):
        run_ceo_approval_record(
            options,
            approval_id="promotion_proposal",
            decision="approved",
            user_confirmed=True,
        )

    assert not (root / "approval_decision_ledger.jsonl").exists()


def test_ceo_approval_apply_requires_recorded_approval_and_stays_shadow_only(tmp_path: Path) -> None:
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
    assert approval_apply["approval_item_current"] is True
    assert approval_apply["recorded_approval_item_fingerprint"] == approval_apply["current_approval_item_fingerprint"]
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


def test_ceo_approval_apply_rejects_stale_clear_stop_approval_recorded_before_stop_request(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    ledger_path = root / "approval_decision_ledger.jsonl"
    stale_entry = {
        "model": "riskflow_ceo_approval_decision_v0",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "run_id": "ceo_test",
        "lab_run_id": "ceo_test_lab",
        "approval_id": "clear_stop_request",
        "decision": "approved",
        "user_confirmed": True,
        "approval_kind": "resume_stopped_run",
        "source_artifact": "stop_request.yaml",
        "approval_item_fingerprint": "stale-fingerprint",
        "production_effect": "none",
    }
    ledger_path.write_text(json.dumps(stale_entry, sort_keys=True) + "\n", encoding="utf-8")
    run_ceo_stop(options, reason="new_stop_after_stale_approval")

    result = run_ceo_approval_apply(
        _authorized(options, "approval_apply"),
        approval_id="clear_stop_request",
        user_confirmed=True,
    )

    approval_apply = result["approval_apply"]
    assert approval_apply["status"] == "blocked_stale_approval_record"
    assert approval_apply["approval_item_current"] is True
    assert approval_apply["recorded_approval_item_fingerprint"] == "stale-fingerprint"
    assert approval_apply["current_approval_item_fingerprint"] != "stale-fingerprint"
    assert ceo_ops.ceo_stop_path(options, "ceo_test").exists()
    assert ceo_ops.lab_stop_path(options, "ceo_test_lab").exists()


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
                "recommended_next_action": "continue_with_one_bound_ceo_action",
                "issues": [],
                "criteria": {"manual_data_import_required": False},
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
    (root / "repair_apply.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_repair_apply_v0",
                "status": "blocked_manual_gate",
                "repair_key": "blocker:pending_user_approval",
                "action_executed": False,
                "repair_closed": False,
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
                        "approval_id": "clear_stop_request",
                        "kind": "resume_stopped_run",
                        "reason": "stop request awaits user approval",
                        "source_artifact": "stop.request",
                        "required_user_decision": "approve_or_reject_resume_or_clear_stop",
                        "approval_authority": "user_only",
                        "approval_item_fingerprint": "stop-fingerprint",
                    }
                ],
                "top_pending_approval_id": "clear_stop_request",
                "top_pending_approval_record_command": "PYTHONPATH=src python3 -m riskflow ceo approval-record --run-id ceo_test --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed",
                "top_pending_approval_apply_command": "PYTHONPATH=src python3 -m riskflow ceo approval-apply --run-id ceo_test --approval-id clear_stop_request --user-confirmed --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_status.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_status_v0",
                "status": "pending_approvals",
                "pending_count": 1,
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
    (root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "status": "decision_quality_written",
                "selected_action": "run_frozen_candidate_validation",
                "confidence": "low",
                "runtime_authority_status": "manual_gate_required",
                "executable_next_action": "blocker:pending_user_approval",
                "executable_next_command_kind": "manual_gate",
                "runtime_authorized_strategic_route": "",
                "executable_can_execute_now": False,
                "selected_action_is_executable_now": False,
                "selected_action_blocked_by": "manual_gate_required:blocker:pending_user_approval",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "role_result_validation.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_result_v0",
                "status": "rejected",
                "task_id": "debt_candidate_a",
                "issues": ["missing_result_path"],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "role_task_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_task_queue_v0",
                "status": "pending_role_tasks",
                "pending_task_count": 4,
                "pending_manual_task_count": 1,
                "pending_autonomous_task_count": 3,
                "completed_task_count": 8,
                "blocked_task_count": 2,
                "top_pending_task_id": "approval_clear_stop_request",
                "top_pending_role_id": "risk_officer",
                "top_pending_packet_path": "reports/ceo_runs/ceo_test/role_dispatch_packets/approval_clear_stop_request.md",
                "top_pending_result_resolution_mode": "manual_gate_blocked_record",
                "top_pending_requires_manual_gate": True,
                "top_pending_closure_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
                "top_blocked_role_id": "product_translator",
                "top_blocked_packet_path": "reports/ceo_runs/ceo_test/role_dispatch_packets/debt_candidate_a_visual_review_evidence.md",
                "top_blocked_result_resolution_mode": "specialist_result_required",
                "top_blocked_validation_status": "accepted",
                "top_blocked_closure_command": "PYTHONPATH=src python3 -m riskflow ceo role-result --run-id ceo_test --task-id debt_candidate_a_visual_review_evidence --status complete --result-path <path-to-specialist-result.yaml>",
                "top_blocked_review_status": "accepted_blocked_result",
                "top_blocked_result_path": "reports/ceo_runs/ceo_test/specialist_results/debt_candidate_a_visual_review_evidence.yaml",
                "top_blocked_next_action": "complete_champion_challenger_visual_review",
                "top_blocked_finding": "Visual review evidence is missing.",
                "next_role_result_command": "PYTHONPATH=src python3 -m riskflow ceo role-result --run-id ceo_test --task-id approval_clear_stop_request --status blocked",
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
    assert kpis["kpis"]["trace_recommended_next_action"] == "continue_with_one_bound_ceo_action"
    assert kpis["kpis"]["trace_issues"] == []
    assert kpis["kpis"]["trace_manual_data_import_required"] is False
    assert kpis["kpis"]["top_blocker"] == "pending_user_approval"
    assert kpis["kpis"]["operating_incident_count"] == 4
    assert kpis["kpis"]["repair_plan_status"] == "manual_gate_first"
    assert kpis["kpis"]["top_repair"] == "blocker:pending_user_approval"
    assert kpis["kpis"]["top_repair_kind"] == "manual_gate"
    assert kpis["kpis"]["repair_next_command"].endswith("approval-queue --run-id ceo_test")
    assert kpis["kpis"]["role_queue_status"] == "pending_role_tasks"
    assert kpis["kpis"]["role_pending_count"] == 4
    assert kpis["kpis"]["role_pending_manual_count"] == 1
    assert kpis["kpis"]["role_pending_autonomous_count"] == 3
    assert kpis["kpis"]["role_completed_count"] == 8
    assert kpis["kpis"]["role_blocked_count"] == 2
    assert kpis["kpis"]["role_top_pending_task"] == "approval_clear_stop_request"
    assert kpis["kpis"]["role_top_blocked_task"] == "debt_candidate_a_visual_review_evidence"
    assert kpis["kpis"]["role_top_blocked_role"] == "product_translator"
    assert kpis["kpis"]["role_top_blocked_review_status"] == "accepted_blocked_result"
    assert kpis["kpis"]["role_top_blocked_next_action"] == "complete_champion_challenger_visual_review"
    assert kpis["kpis"]["role_top_blocked_finding"] == "Visual review evidence is missing."
    assert kpis["kpis"]["role_next_action"].endswith("approval-queue --run-id ceo_test")
    assert kpis["next_action_scope"] == "executive_health_diagnostic_only"
    assert kpis["dispatch_authority"] == "not_granted_by_executive_kpis"
    assert "ceo status" in kpis["runtime_authority_note"]
    assert kpis["product_language_allowed"] is False
    assert kpis["production_effect"] == "none"
    assert kpis["promotion_authority"] == "none"
    assert result["paths"]["executive_kpis"].exists()
    assert result["paths"]["executive_kpis_report"].exists()
    report = result["paths"]["executive_kpis_report"].read_text(encoding="utf-8")
    assert "Attention next action:" in report
    assert "Next action scope: executive_health_diagnostic_only" in report
    assert "Dispatch authority: not_granted_by_executive_kpis" in report
    assert "trace_recommended_next_action: continue_with_one_bound_ceo_action" in report
    assert "trace_manual_data_import_required: False" in report
    assert "role_top_blocked_review_status: accepted_blocked_result" in report
    assert "role_top_blocked_finding: Visual review evidence is missing." in report


def test_ceo_executive_kpis_trace_failure_requires_attention_without_other_blockers() -> None:
    kpis = ceo_ops.build_ceo_executive_kpis(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        approval_queue={"pending_count": 0, "production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        candidate_portfolio=[],
        capability_backlog=[],
        trace_grade={
            "verdict": "fail",
            "score": 55,
            "recommended_next_action": "stop_for_manual_data_import",
            "issues": ["manual_data_import_required"],
            "production_effect": "none",
        },
        fresh_withheld_execution={"production_effect": "none"},
        promotion_proposal={"status": "", "production_effect": "none"},
        blocker_stack={"top_blocker": "", "production_effect": "none"},
        incident_register={"incident_count": 0, "production_effect": "none"},
        repair_plan={"status": "", "top_repair": "", "next_command": "", "production_effect": "none"},
    )

    assert kpis["status"] == "attention_required"
    assert kpis["next_action"] == "stop_for_manual_data_import"
    assert kpis["kpis"]["trace_manual_data_import_required"] is True


def test_ceo_executive_kpis_role_queue_requires_attention_without_other_blockers() -> None:
    kpis = ceo_ops.build_ceo_executive_kpis(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        approval_queue={"pending_count": 0, "production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        candidate_portfolio=[],
        capability_backlog=[],
        trace_grade={
            "verdict": "pass",
            "score": 94,
            "recommended_next_action": "continue_with_one_bound_ceo_action",
            "issues": [],
            "criteria": {"manual_data_import_required": False},
            "production_effect": "none",
        },
        fresh_withheld_execution={"production_effect": "none"},
        promotion_proposal={"status": "", "production_effect": "none"},
        blocker_stack={"top_blocker": "", "production_effect": "none"},
        incident_register={"incident_count": 0, "production_effect": "none"},
        repair_plan={"status": "", "top_repair": "", "next_command": "", "production_effect": "none"},
        role_queue={
            "status": "blocked_role_tasks",
            "pending_task_count": 0,
            "pending_manual_task_count": 0,
            "pending_autonomous_task_count": 0,
            "completed_task_count": 9,
            "blocked_task_count": 1,
            "top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
            "top_blocked_role_id": "product_translator",
            "top_blocked_review_status": "accepted_blocked_result",
            "top_blocked_next_action": "complete_champion_challenger_visual_review",
            "top_blocked_finding": "Visual review evidence is missing.",
            "production_effect": "none",
        },
    )

    assert kpis["status"] == "attention_required"
    assert kpis["next_action"] == "complete_champion_challenger_visual_review"
    assert kpis["kpis"]["role_queue_status"] == "blocked_role_tasks"
    assert kpis["kpis"]["role_blocked_count"] == 1
    assert kpis["kpis"]["role_top_blocked_review_status"] == "accepted_blocked_result"
    assert kpis["kpis"]["role_top_blocked_finding"] == "Visual review evidence is missing."


def test_ceo_status_surfaces_existing_operating_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "status": "decision_quality_written",
                "selected_action": "run_frozen_candidate_validation",
                "confidence": "low",
                "runtime_authority_status": "manual_gate_required",
                "executable_next_action": "blocker:pending_user_approval",
                "executable_next_command_kind": "manual_gate",
                "runtime_authorized_strategic_route": "",
                "executable_can_execute_now": False,
                "selected_action_is_executable_now": False,
                "selected_action_blocked_by": "manual_gate_required:blocker:pending_user_approval",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
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
    (root / "trace_grade.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_trace_grade_v0",
                "verdict": "fail",
                "score": 42,
                "recommended_next_action": "stop_for_manual_data_import",
                "issues": ["manual_data_import_required"],
                "criteria": {"manual_data_import_required": True},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_replay.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_replay_v0",
                "status": "replay_gaps",
                "issues": ["missing_action_ledger_entries"],
                "dispatch_receipt_status": "fail",
                "operator_step_status": "fail",
                "operator_step_count": 2,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_eval_suite.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_eval_suite_v0",
                "status": "fail",
                "score": 71,
                "nine_nine_readiness": {
                    "status": "blocked_before_extended_autonomy",
                    "blocking_case_ids": ["replayable_action_timeline", "operator_step_replayable"],
                    "advisory_case_ids": ["strategy_capital_allocates_attention"],
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "artifact_coherence.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_artifact_coherence_v0",
                "status": "fail",
                "issue_count": 1,
                "issues": [{"artifact": "dispatch_receipt", "issues": ["missing_action_dispatch_receipt_ref"]}],
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
    (root / "repair_apply.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_repair_apply_v0",
                "status": "blocked_manual_gate",
                "repair_key": "blocker:pending_user_approval",
                "action_executed": False,
                "repair_closed": False,
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
                        "approval_id": "clear_stop_request",
                        "kind": "resume_stopped_run",
                        "reason": "stop request awaits user approval",
                        "source_artifact": "stop.request",
                        "required_user_decision": "approve_or_reject_resume_or_clear_stop",
                        "approval_authority": "user_only",
                        "approval_item_fingerprint": "stop-fingerprint",
                    }
                ],
                "top_pending_approval_id": "clear_stop_request",
                "top_pending_approval_record_command": "PYTHONPATH=src python3 -m riskflow ceo approval-record --run-id ceo_test --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed",
                "top_pending_approval_apply_command": "PYTHONPATH=src python3 -m riskflow ceo approval-apply --run-id ceo_test --approval-id clear_stop_request --user-confirmed --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_status.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_status_v0",
                "status": "pending_approvals",
                "pending_count": 1,
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
    (root / "role_result_validation.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_result_v0",
                "status": "rejected",
                "task_id": "debt_candidate_a",
                "issues": ["missing_result_path"],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "role_task_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_task_queue_v0",
                "status": "pending_role_tasks",
                "pending_task_count": 4,
                "pending_manual_task_count": 1,
                "pending_autonomous_task_count": 3,
                "completed_task_count": 8,
                "blocked_task_count": 2,
                "top_pending_task_id": "approval_clear_stop_request",
                "top_pending_role_id": "risk_officer",
                "top_pending_packet_path": "reports/ceo_runs/ceo_test/role_dispatch_packets/approval_clear_stop_request.md",
                "top_pending_result_resolution_mode": "manual_gate_blocked_record",
                "top_pending_requires_manual_gate": True,
                "top_pending_closure_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
                "top_blocked_role_id": "product_translator",
                "top_blocked_packet_path": "reports/ceo_runs/ceo_test/role_dispatch_packets/debt_candidate_a_visual_review_evidence.md",
                "top_blocked_result_resolution_mode": "specialist_result_required",
                "top_blocked_validation_status": "accepted",
                "top_blocked_closure_command": "PYTHONPATH=src python3 -m riskflow ceo role-result --run-id ceo_test --task-id debt_candidate_a_visual_review_evidence --status complete --result-path <path-to-specialist-result.yaml>",
                "top_blocked_review_status": "accepted_blocked_result",
                "top_blocked_result_path": "reports/ceo_runs/ceo_test/specialist_results/debt_candidate_a_visual_review_evidence.yaml",
                "top_blocked_next_action": "complete_champion_challenger_visual_review",
                "top_blocked_finding": "Visual review evidence is missing.",
                "next_role_result_command": "PYTHONPATH=src python3 -m riskflow ceo role-result --run-id ceo_test --task-id approval_clear_stop_request --status blocked",
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
    assert operating["trace_grade_status"] == "fail"
    assert operating["trace_grade_score"] == 42
    assert operating["trace_grade_recommended_next_action"] == "stop_for_manual_data_import"
    assert operating["trace_grade_issues"] == ["manual_data_import_required"]
    assert operating["trace_grade_manual_data_import_required"] is True
    assert operating["replay_status"] == "replay_gaps"
    assert operating["replay_issue_count"] == 1
    assert operating["replay_dispatch_receipt_status"] == "fail"
    assert operating["operator_step_status"] == "fail"
    assert operating["operator_step_count"] == 2
    assert operating["eval_suite_status"] == "fail"
    assert operating["eval_suite_score"] == 71
    assert operating["nine_nine_readiness"] == "blocked_before_extended_autonomy"
    assert operating["nine_nine_blocking_case_count"] == 2
    assert operating["nine_nine_advisory_case_count"] == 1
    assert operating["artifact_coherence_status"] == "fail"
    assert operating["artifact_coherence_issue_count"] == 1
    assert operating["artifact_coherence_top_issue_artifact"] == "dispatch_receipt"
    assert operating["artifact_coherence_top_issue_types"] == ["missing_action_dispatch_receipt_ref"]
    assert operating["artifact_coherence_top_issue_severity"] == "unknown"
    assert operating["effective_operator_status"] == "manual_gate_required"
    assert operating["manual_gate_active"] is True
    assert operating["effective_operator_runtime_blocked"] is True
    assert operating["effective_operator_runtime_block_reason"] == "manual_gate_required:blocker:pending_user_approval"
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
    assert operating["repair_apply_status"] == "blocked_manual_gate"
    assert operating["repair_apply_key"] == "blocker:pending_user_approval"
    assert operating["repair_apply_executed"] is False
    assert operating["repair_apply_closed"] is False
    assert operating["approval_queue_status"] == "pending_approvals"
    assert operating["approval_pending_count"] == 1
    assert operating["approval_top_pending_id"] == "clear_stop_request"
    assert operating["approval_top_pending_kind"] == "resume_stopped_run"
    assert operating["approval_top_pending_reason"] == "stop request awaits user approval"
    assert operating["approval_top_pending_source"] == "stop.request"
    assert operating["approval_top_pending_required_user_decision"] == "approve_or_reject_resume_or_clear_stop"
    assert operating["approval_top_pending_authority"] == "user_only"
    assert operating["approval_top_pending_fingerprint"] == "stop-fingerprint"
    assert operating["approval_record_command"].endswith(
        "approval-record --run-id ceo_test --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed"
    )
    assert operating["approval_apply_command"].endswith(
        "approval-apply --run-id ceo_test --approval-id clear_stop_request --user-confirmed --apply"
    )
    assert operating["approval_status"] == "pending_approvals"
    assert operating["action_board_status"] == "manual_gate_required"
    assert operating["action_board_primary_action"] == "blocker:pending_user_approval"
    assert operating["action_board_primary_kind"] == "manual_gate"
    assert operating["action_board_command"].endswith("approval-queue --run-id ceo_test")
    assert operating["decision_quality_status"] == "decision_quality_written"
    assert operating["decision_quality_selected_action"] == "run_frozen_candidate_validation"
    assert operating["decision_quality_confidence"] == "low"
    assert operating["decision_quality_runtime_authority"] == "manual_gate_required"
    assert operating["decision_quality_executable_next_action"] == "blocker:pending_user_approval"
    assert operating["decision_quality_executable_command_kind"] == "manual_gate"
    assert operating["decision_quality_runtime_authorized_strategic_route"] == ""
    assert operating["decision_quality_executable_can_execute_now"] is False
    assert operating["decision_quality_selected_action_is_executable_now"] is False
    assert operating["decision_quality_selected_action_blocked_by"] == "manual_gate_required:blocker:pending_user_approval"
    assert operating["operator_brief_status"] == "waiting_on_manual_gate"
    assert operating["operator_brief_summary"] == "CEO mode is stopped at a manual gate."
    assert operating["operator_brief_next_action"].endswith("approval-queue --run-id ceo_test")
    assert operating["role_queue_status"] == "pending_role_tasks"
    assert operating["role_pending_task_count"] == 4
    assert operating["role_pending_manual_task_count"] == 1
    assert operating["role_pending_autonomous_task_count"] == 3
    assert operating["role_completed_task_count"] == 8
    assert operating["role_blocked_task_count"] == 2
    assert operating["role_top_pending_task_id"] == "approval_clear_stop_request"
    assert operating["role_top_pending_role_id"] == "risk_officer"
    assert operating["role_top_pending_packet_path"].endswith("approval_clear_stop_request.md")
    assert operating["role_top_pending_result_resolution_mode"] == "manual_gate_blocked_record"
    assert operating["role_top_pending_requires_manual_gate"] is True
    assert operating["role_top_pending_closure_command"].endswith("approval-queue --run-id ceo_test")
    assert operating["role_top_blocked_task_id"] == "debt_candidate_a_visual_review_evidence"
    assert operating["role_top_blocked_role_id"] == "product_translator"
    assert operating["role_top_blocked_packet_path"].endswith("debt_candidate_a_visual_review_evidence.md")
    assert operating["role_top_blocked_result_resolution_mode"] == "specialist_result_required"
    assert operating["role_top_blocked_validation_status"] == "accepted"
    assert operating["role_top_blocked_closure_command"].endswith(
        "role-result --run-id ceo_test --task-id debt_candidate_a_visual_review_evidence "
        "--status complete --result-path <path-to-specialist-result.yaml>"
    )
    assert operating["role_top_blocked_review_status"] == "accepted_blocked_result"
    assert operating["role_top_blocked_result_path"].endswith("debt_candidate_a_visual_review_evidence.yaml")
    assert operating["role_top_blocked_next_action"] == "complete_champion_challenger_visual_review"
    assert operating["role_top_blocked_finding"] == "Visual review evidence is missing."
    assert "--task-id approval_clear_stop_request" in operating["role_next_result_command"]
    assert "--status blocked" in operating["role_next_result_command"]
    assert operating["role_result_validation_status"] == "rejected"
    assert operating["role_result_validation_task"] == "debt_candidate_a"
    assert operating["role_result_validation_issues"] == ["missing_result_path"]
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
    assert operating["decision_quality_status"] == "missing_decision_quality"
    assert operating["operator_brief_status"] == "missing_operator_brief"
    assert operating["replay_status"] == "missing_replay"
    assert operating["operator_step_status"] == "missing_operator_step"
    assert operating["eval_suite_status"] == "missing_eval_suite"
    assert operating["artifact_coherence_status"] == "missing_artifact_coherence"
    assert operating["repair_apply_status"] == "missing_repair_apply"
    assert operating["role_result_validation_status"] == "missing_role_result_validation"


def test_ceo_status_live_stop_overrides_stale_safe_operating_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    ceo_ops.ceo_stop_path(options, "ceo_test").write_text("user_requested\n", encoding="utf-8")
    (root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_dispatch_receipt_v0",
                "status": "dispatch_allowed",
                "safe_to_dispatch": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --objective bullish-positive --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "status": "bounded_action_available",
                "primary_action": {
                    "action_id": "resumption_brief_next_command",
                    "command_kind": "bounded_dispatch",
                    "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --objective bullish-positive --apply",
                    "can_execute_now": True,
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
                "status": "ready_for_bounded_action",
                "recommended_next_action": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --objective bullish-positive --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "status": "decision_quality_written",
                "runtime_authority_status": "bounded_action_available",
                "effective_runtime_action": "resumption_brief_next_command",
                "effective_runtime_can_execute_now": True,
                "runtime_blocked": False,
                "selected_action": "run_champion_challenger",
                "selected_action_is_executable_now": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_status(options)

    operating = result["company_status"]["operating_artifacts"]
    assert result["company_status"]["stop_requested"] is True
    assert operating["live_stop_requested"] is True
    assert operating["runtime_authority_override"] == "stop_requested"
    assert operating["dispatch_safe_to_dispatch"] is False
    assert operating["effective_operator_status"] == "manual_gate_required"
    assert operating["manual_gate_active"] is True
    assert operating["effective_operator_runtime_blocked"] is True
    assert operating["effective_operator_runtime_block_reason"] == "manual_gate_required:blocker:stop_requested"
    assert operating["resumption_status"] == "blocked_stop_requested"
    assert operating["resumption_next_command"].endswith("approval-queue --run-id ceo_test")
    assert operating["default_handoff_command"].endswith("approval-queue --run-id ceo_test")
    assert "execute-next" not in operating["default_handoff_command"]
    assert operating["default_handoff_reason"] == "live_stop_requested"
    assert operating["action_board_status"] == "manual_gate_required"
    assert operating["action_board_primary_action"] == "blocker:stop_requested"
    assert operating["action_board_primary_kind"] == "manual_gate"
    assert operating["action_board_command"].endswith("approval-queue --run-id ceo_test")
    assert operating["decision_quality_effective_runtime_action"] == "blocker:stop_requested"
    assert operating["decision_quality_effective_runtime_command_kind"] == "manual_gate"
    assert operating["decision_quality_effective_runtime_can_execute_now"] is False
    assert operating["decision_quality_runtime_blocked"] is True
    assert operating["decision_quality_runtime_block_reason"] == "manual_gate_required:blocker:stop_requested"
    assert operating["decision_quality_runtime_authority"] == "manual_gate_required"
    assert operating["decision_quality_executable_next_action"] == "blocker:stop_requested"
    assert operating["decision_quality_executable_command_kind"] == "manual_gate"
    assert operating["decision_quality_executable_can_execute_now"] is False
    assert operating["decision_quality_selected_action_is_executable_now"] is False
    assert operating["decision_quality_selected_action_blocked_by"] == "manual_gate_required:blocker:stop_requested"
    assert operating["operator_brief_status"] == "waiting_on_manual_gate"
    assert operating["operator_brief_next_action"].endswith("approval-queue --run-id ceo_test")


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
    assert queue["pending_task_count"] == 3
    assert queue["pending_manual_task_count"] == 1
    assert queue["pending_autonomous_task_count"] == 2
    assert queue["top_pending_task_id"] == "approval_promotion_proposal"
    assert queue["top_pending_role_id"] == "risk_officer"
    assert queue["top_pending_owner_command"] == "wait_for_user_approval"
    assert queue["top_pending_packet_path"].endswith("role_dispatch_packets/approval_promotion_proposal.md")
    assert queue["next_role_dispatch_command"].endswith("ceo role-dispatch --run-id ceo_test")
    assert queue["top_pending_result_resolution_mode"] == "manual_gate_blocked_record"
    assert queue["top_pending_requires_manual_gate"] is True
    assert queue["top_pending_closure_command"].endswith(
        "approval-record --run-id ceo_test --approval-id promotion_proposal --decision <approved|rejected> --user-confirmed"
    )
    assert queue["top_autonomous_pending_task_id"] == "debt_candidate_a_passing_validation_result"
    assert queue["top_autonomous_pending_role_id"] == "validation_referee"
    assert queue["top_autonomous_pending_packet_path"].endswith("role_dispatch_packets/debt_candidate_a_passing_validation_result.md")
    assert "--task-id debt_candidate_a_passing_validation_result" in queue["top_autonomous_next_role_result_command"]
    assert "--status complete" in queue["top_autonomous_next_role_result_command"]
    assert "--task-id approval_promotion_proposal" in queue["next_role_result_command"]
    assert "--status blocked" in queue["next_role_result_command"]
    assert "--result-path" not in queue["next_role_result_command"]
    assert queue["production_effect"] == "none"
    assert result["paths"]["role_registry"].exists()
    assert result["paths"]["role_task_queue"].exists()
    assert result["paths"]["role_task_queue_report"].exists()


def test_ceo_org_progress_score_flags_open_and_unmerged_role_work() -> None:
    scorecard = ceo_ops.build_ceo_org_progress_score(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        role_queue={
            "task_count": 3,
            "pending_task_count": 1,
            "blocked_task_count": 1,
            "completed_task_count": 1,
            "pending_manual_task_count": 0,
            "top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
            "top_blocked_role_id": "product_translator",
            "top_blocked_next_action": "complete_visual_review",
            "top_blocked_finding": "visual evidence missing",
        },
        role_task_ledger_entries=[
            {
                "task_id": "debt_candidate_b_validation",
                "status": "complete",
                "validation_status": "accepted",
                "result_recommended_next_action": "run_fresh_withheld_validation_executor",
                "production_effect": "none",
            }
        ],
        role_merge_receipts=[],
    )

    assert scorecard["model"] == "riskflow_ceo_org_progress_score_v0"
    assert scorecard["status"] == "org_work_open"
    assert scorecard["org_progress_score"] < 100
    assert scorecard["completed_without_merge_count"] == 1
    assert "pending_role_work" in scorecard["fake_progress_flags"]
    assert "blocked_role_work" in scorecard["fake_progress_flags"]
    assert "accepted_completion_without_merge_receipt" in scorecard["fake_progress_flags"]
    assert scorecard["action_scope"] == "org_progress_diagnostic_only"
    assert scorecard["dispatch_authority"] == "not_granted_by_org_progress_score"
    assert scorecard["production_effect"] == "none"


def test_ceo_org_progress_score_writes_artifacts(tmp_path: Path) -> None:
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
                        "debt_id": "candidate_a_visual_review_evidence",
                        "candidate_id": "candidate_a",
                        "debt_kind": "visual_review_evidence",
                        "blocker_type": "visual_review_missing",
                        "priority": 1,
                        "evidence_required": "visual review evidence",
                        "owner_command": "complete_visual_review",
                        "blocking_artifact": "champion_challenger_visual_review_queue.yaml",
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_approval_queue_v0", "pending_count": 0, "pending_items": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "capability_backlog.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_capability_backlog_v0", "items": [], "production_effect": "none"}),
        encoding="utf-8",
    )

    result = run_ceo_org_progress_score(options)

    scorecard = result["org_progress_score"]
    assert scorecard["status"] == "org_work_open"
    assert scorecard["pending_task_count"] == 1
    assert scorecard["action_scope"] == "org_progress_diagnostic_only"
    assert scorecard["dispatch_authority"] == "not_granted_by_org_progress_score"
    assert result["paths"]["org_progress_score"].exists()
    assert result["paths"]["org_progress_score_report"].exists()
    report = result["paths"]["org_progress_score_report"].read_text(encoding="utf-8")
    assert "Org progress score" in report
    assert "Dispatch authority: not_granted_by_org_progress_score" in report


def test_ceo_role_queue_routes_manual_only_pending_to_user_approval(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_evidence_debt_register_v0", "debts": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_queue_v0",
                "pending_count": 1,
                "pending_items": [
                    {
                        "approval_id": "clear_stop_request",
                        "reason": "stop.request exists",
                        "source_artifact": "stop.request",
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

    queue = run_ceo_role_queue(options)["queue"]

    assert queue["pending_task_count"] == 1
    assert queue["pending_manual_task_count"] == 1
    assert queue["pending_autonomous_task_count"] == 0
    assert queue["top_pending_task_id"] == "approval_clear_stop_request"
    assert queue["top_autonomous_pending_task_id"] == ""
    assert queue["next_action"] == "wait_for_user_approval_or_record_manual_gate_blocked"


def test_ceo_role_queue_top_blocked_prefers_specialist_work_over_recorded_manual_gate() -> None:
    queue = ceo_ops.build_ceo_role_task_queue(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        evidence_debt_register={
            "model": "riskflow_ceo_evidence_debt_register_v0",
            "status": "open_evidence_debt",
            "debt_count": 1,
            "debts": [
                {
                    "debt_id": "candidate_a_visual_review_evidence",
                    "candidate_id": "candidate_a",
                    "debt_kind": "visual_review_evidence",
                    "blocker_type": "missing_visual_review",
                    "priority": 1,
                    "evidence_required": "chart review",
                    "owner_command": "collect_visual_review_evidence",
                    "blocking_artifact": "champion_challenger_visual_review_queue.yaml",
                }
            ],
            "production_effect": "none",
        },
        approval_queue={
            "model": "riskflow_ceo_approval_queue_v0",
            "pending_count": 1,
            "pending_items": [
                {
                    "approval_id": "clear_stop_request",
                    "reason": "stop.request exists",
                    "source_artifact": "stop.request",
                }
            ],
            "production_effect": "none",
        },
        capability_backlog={"model": "riskflow_ceo_capability_backlog_v0", "items": [], "production_effect": "none"},
        role_results={
            "approval_clear_stop_request": {
                "status": "blocked",
                "validation_status": "blocked_without_artifact",
                "result_resolution_mode": "manual_gate_blocked_record",
                "production_effect": "none",
            },
            "debt_candidate_a_visual_review_evidence": {
                "status": "blocked",
                "validation_status": "accepted",
                "result_resolution_mode": "specialist_result_required",
                "result_finding": "Chart evidence is still missing.",
                "result_recommended_next_action": "collect_visual_review_evidence",
                "production_effect": "none",
            },
        },
    )

    assert queue["blocked_task_count"] == 2
    assert queue["top_blocked_task_id"] == "debt_candidate_a_visual_review_evidence"
    assert queue["top_blocked_result_resolution_mode"] == "specialist_result_required"
    assert queue["top_blocked_validation_status"] == "accepted"
    assert queue["top_blocked_closure_command"].endswith(
        "role-result --run-id ceo_test --task-id debt_candidate_a_visual_review_evidence "
        "--status complete --result-path <path-to-specialist-result.yaml>"
    )
    assert queue["top_blocked_review_status"] == "accepted_blocked_result"
    assert queue["top_blocked_finding"] == "Chart evidence is still missing."
    assert queue["top_blocked_next_action"] == "collect_visual_review_evidence"


def test_ceo_role_result_appends_ledger(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    review_path = tmp_path / "reports" / "review.yaml"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_specialist_result_v0",
                "task_id": "debt_candidate_a_passing_validation_result",
                "role_id": "validation_referee",
                "status": "complete",
                "finding": "Threshold evidence still needs review.",
                "evidence_refs": ["fresh_withheld_validation_execution_result.yaml"],
                "recommended_next_action": "review_fresh_withheld_threshold_failures_or_archive_candidate",
                "product_language_allowed": False,
                "production_effect": "none",
                "promotion_authority": "none",
            }
        ),
        encoding="utf-8",
    )
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
        result_path="reports/review.yaml",
    )

    assert result["result"]["status"] == "complete"
    assert result["result"]["validation_status"] == "accepted"
    assert result["result"]["production_effect"] == "none"
    lines = result["paths"]["role_task_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["task_id"] == "debt_candidate_a_passing_validation_result"
    assert entry["result_path"] == "reports/review.yaml"
    assert entry["resolved_result_path"].endswith("reports/review.yaml")
    assert len(entry["result_sha256"]) == 64
    assert entry["result_artifact_exists"] is True
    assert entry["result_provenance_status"] == "pass"
    assert entry["validation_status"] == "accepted"
    assert result["queue"]["completed_task_count"] == 1
    assert result["queue"]["pending_task_count"] == 0
    assert result["queue"]["tasks"][0]["status"] == "complete"
    assert result["queue"]["tasks"][0]["result_provenance_status"] == "pass"
    assert result["queue"]["tasks"][0]["current_result_sha256"] == entry["result_sha256"]
    assert result["paths"]["role_task_queue"].exists()
    assert result["paths"]["role_result_validation"].exists()


def test_ceo_role_result_blocked_specialist_finding_surfaces_in_queue(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    review_path = tmp_path / "reports" / "blocked_review.yaml"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_specialist_result_v0",
                "task_id": "debt_candidate_a_visual_review_evidence",
                "role_id": "product_translator",
                "status": "blocked",
                "finding": "Visual-review queue is missing chart labels.",
                "evidence_refs": ["champion_challenger_visual_review_queue.yaml"],
                "recommended_next_action": "complete_champion_challenger_visual_review",
                "product_language_allowed": False,
                "production_effect": "none",
                "promotion_authority": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
                "status": "open_evidence_debt",
                "debt_count": 1,
                "debts": [
                    {
                        "debt_id": "candidate_a_visual_review_evidence",
                        "candidate_id": "candidate_a",
                        "debt_kind": "visual_review_evidence",
                        "blocker_type": "missing_visual_review",
                        "priority": 1,
                        "evidence_required": "chart review",
                        "owner_command": "collect_visual_review_evidence",
                        "blocking_artifact": "champion_challenger_visual_review_queue.yaml",
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
        task_id="debt_candidate_a_visual_review_evidence",
        status="blocked",
        result_path="reports/blocked_review.yaml",
    )

    queue = result["queue"]
    assert result["result"]["status"] == "blocked"
    assert result["result"]["validation_status"] == "accepted"
    assert result["result"]["result_finding"] == "Visual-review queue is missing chart labels."
    assert queue["blocked_task_count"] == 1
    assert queue["top_blocked_review_status"] == "accepted_blocked_result"
    assert queue["top_blocked_result_path"].endswith("reports/blocked_review.yaml")
    assert queue["top_blocked_finding"] == "Visual-review queue is missing chart labels."
    assert queue["top_blocked_next_action"] == "complete_champion_challenger_visual_review"
    report = queue["top_blocked_task"]
    assert report["result_recommended_next_action"] == "complete_champion_challenger_visual_review"


def test_ceo_role_queue_blocks_result_provenance_drift(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    review_path = tmp_path / "reports" / "review.yaml"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_payload = {
        "model": "riskflow_ceo_specialist_result_v0",
        "task_id": "debt_candidate_a_passing_validation_result",
        "role_id": "validation_referee",
        "status": "complete",
        "finding": "Threshold evidence still needs review.",
        "evidence_refs": ["fresh_withheld_validation_execution_result.yaml"],
        "recommended_next_action": "review_fresh_withheld_threshold_failures_or_archive_candidate",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }
    review_path.write_text(yaml.safe_dump(review_payload), encoding="utf-8")
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

    run_ceo_role_result(
        options,
        task_id="debt_candidate_a_passing_validation_result",
        status="complete",
        result_path="reports/review.yaml",
    )
    review_payload["finding"] = "Changed after acceptance."
    review_path.write_text(yaml.safe_dump(review_payload), encoding="utf-8")

    result = run_ceo_role_queue(options)
    queue = result["queue"]

    assert queue["completed_task_count"] == 0
    assert queue["blocked_task_count"] == 1
    assert queue["status"] == "blocked_role_tasks"
    assert queue["top_blocked_task_id"] == "debt_candidate_a_passing_validation_result"
    assert queue["top_blocked_role_id"] == "validation_referee"
    assert queue["top_blocked_packet_path"].endswith(
        "role_dispatch_packets/debt_candidate_a_passing_validation_result.md"
    )
    assert queue["top_blocked_result_resolution_mode"] == "specialist_result_required"
    assert queue["top_blocked_validation_status"] == "provenance_drift"
    assert queue["top_blocked_closure_command"].endswith(
        "role-result --run-id ceo_test --task-id debt_candidate_a_passing_validation_result "
        "--status complete --result-path <path-to-specialist-result.yaml>"
    )
    report = result["paths"]["role_task_queue_report"].read_text(encoding="utf-8")
    assert "Top blocked: debt_candidate_a_passing_validation_result" in report
    assert "Top blocked role: validation_referee" in report
    assert "Top blocked validation: provenance_drift" in report
    assert "Top blocked closure command" in report
    task = queue["tasks"][0]
    assert task["status"] == "blocked"
    assert task["recorded_status"] == "complete"
    assert task["validation_status"] == "provenance_drift"
    assert task["result_provenance_status"] == "drift"
    assert "result_artifact_sha_mismatch" in task["validation_issues"]
    stale_queue = {**queue, "completed_task_count": 1, "blocked_task_count": 0, "pending_task_count": 0}
    (root / "role_task_queue.yaml").write_text(yaml.safe_dump(stale_queue), encoding="utf-8")

    eval_result = run_ceo_eval_suite(options)
    role_case = {item["case_id"]: item for item in eval_result["eval_suite"]["cases"]}["role_results_close_the_role_queue"]
    refreshed_queue = yaml.safe_load((root / "role_task_queue.yaml").read_text(encoding="utf-8"))

    assert role_case["status"] == "fail"
    assert refreshed_queue["completed_task_count"] == 0
    assert refreshed_queue["blocked_task_count"] == 1
    assert refreshed_queue["tasks"][0]["validation_status"] == "provenance_drift"


def test_ceo_role_result_rejects_complete_without_result_path(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
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

    with pytest.raises(ValueError, match="missing_result_path"):
        run_ceo_role_result(
            options,
            task_id="debt_candidate_a_passing_validation_result",
            status="complete",
            result_path="",
        )

    assert not (root / "role_task_ledger.jsonl").exists()
    validation = yaml.safe_load((root / "role_result_validation.yaml").read_text(encoding="utf-8"))
    assert validation["status"] == "rejected"
    assert "missing_result_path" in validation["issues"]


def test_ceo_role_result_rejects_mismatched_role_and_product_language(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    review_path = tmp_path / "reports" / "unsafe_review.yaml"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_specialist_result_v0",
                "task_id": "debt_candidate_a_passing_validation_result",
                "role_id": "product_translator",
                "status": "complete",
                "finding": "Use this product claim.",
                "evidence_refs": ["fresh_withheld_validation_execution_result.yaml"],
                "recommended_next_action": "promote_candidate",
                "product_language_allowed": True,
                "production_effect": "none",
                "promotion_authority": "approved",
            }
        ),
        encoding="utf-8",
    )
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
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

    with pytest.raises(ValueError, match="role_id_mismatch"):
        run_ceo_role_result(
            options,
            task_id="debt_candidate_a_passing_validation_result",
            status="complete",
            result_path="reports/unsafe_review.yaml",
        )

    validation = yaml.safe_load((root / "role_result_validation.yaml").read_text(encoding="utf-8"))
    assert "role_id_mismatch" in validation["issues"]
    assert "product_language_not_explicitly_false" in validation["issues"]
    assert "promotion_authority_not_none" in validation["issues"]
    assert not (root / "role_task_ledger.jsonl").exists()


def test_ceo_role_result_rejects_manual_gate_completion_artifact(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    review_path = tmp_path / "reports" / "manual_gate_review.yaml"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_specialist_result_v0",
                "task_id": "approval_clear_stop_request",
                "role_id": "risk_officer",
                "status": "complete",
                "finding": "Pretend the approval is complete.",
                "evidence_refs": ["approval_queue.yaml"],
                "recommended_next_action": "continue_without_user_approval",
                "product_language_allowed": False,
                "production_effect": "none",
                "promotion_authority": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_evidence_debt_register_v0", "debts": [], "production_effect": "none"}),
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
                        "approval_id": "clear_stop_request",
                        "reason": "stop request awaits user approval",
                        "source_artifact": "approval_queue.yaml",
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

    with pytest.raises(ValueError, match="manual_gate_cannot_complete_as_specialist_result"):
        run_ceo_role_result(
            options,
            task_id="approval_clear_stop_request",
            status="complete",
            result_path="reports/manual_gate_review.yaml",
        )

    validation = yaml.safe_load((root / "role_result_validation.yaml").read_text(encoding="utf-8"))
    assert validation["status"] == "rejected"
    assert validation["result_resolution_mode"] == "manual_gate_blocked_record"
    assert validation["requires_manual_gate"] is True
    assert validation["can_complete_with_specialist_artifact"] is False
    assert "manual_gate_cannot_complete_as_specialist_result" in validation["issues"]
    assert not (root / "role_task_ledger.jsonl").exists()


def test_ceo_role_result_records_manual_gate_as_blocked_without_artifact(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_evidence_debt_register_v0", "debts": [], "production_effect": "none"}),
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
                        "approval_id": "clear_stop_request",
                        "reason": "stop request awaits user approval",
                        "source_artifact": "approval_queue.yaml",
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

    result = run_ceo_role_result(
        options,
        task_id="approval_clear_stop_request",
        status="blocked",
    )

    assert result["result"]["status"] == "blocked"
    assert result["result"]["validation_status"] == "blocked_without_artifact"
    assert result["result"]["result_resolution_mode"] == "manual_gate_blocked_record"
    assert result["result"]["requires_manual_gate"] is True
    assert result["queue"]["pending_task_count"] == 0
    assert result["queue"]["blocked_task_count"] == 1
    assert result["queue"]["tasks"][0]["status"] == "blocked"
    validation = yaml.safe_load((root / "role_result_validation.yaml").read_text(encoding="utf-8"))
    assert validation["status"] == "blocked_without_artifact"
    lines = result["paths"]["role_task_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["task_id"] == "approval_clear_stop_request"
    assert entry["requires_manual_gate"] is True


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
    assert dispatch["top_task_id"] == "debt_candidate_a_passing_validation_result"
    assert dispatch["top_role_id"] == "validation_referee"
    assert dispatch["top_packet_path"].endswith("role_dispatch_packets/debt_candidate_a_passing_validation_result.md")
    assert dispatch["top_result_resolution_mode"] == "specialist_result_required"
    assert dispatch["top_requires_manual_gate"] is False
    assert "--task-id debt_candidate_a_passing_validation_result" in dispatch["next_role_result_command"]
    assert "--status complete" in dispatch["next_role_result_command"]
    assert "--result-path" in dispatch["next_role_result_command"]
    packet = dispatch["packets"][0]
    assert packet["role_id"] == "validation_referee"
    assert packet["result_resolution_mode"] == "specialist_result_required"
    assert packet["can_complete_with_specialist_artifact"] is True
    assert packet["allowed_authority"] == "review_only"
    assert packet["product_language_allowed"] is False
    assert packet["production_effect"] == "none"
    packet_path = Path(packet["packet_path"])
    assert packet_path.exists()
    packet_text = packet_path.read_text(encoding="utf-8")
    assert "Expected Result Schema" in packet_text
    assert "product_language_allowed: false" in packet_text
    assert "production_effect: none" in packet_text
    assert "promotion_authority: none" in packet_text
    assert "Do not approve manual gates" in packet_text
    assert result["paths"]["role_dispatch"].exists()
    assert result["paths"]["role_dispatch_report"].exists()


def test_ceo_role_dispatch_manual_gate_uses_blocked_result_command(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_evidence_debt_register_v0", "debts": [], "production_effect": "none"}),
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
                        "approval_id": "clear_stop_request",
                        "reason": "stop request needs user approval before continuing",
                        "source_artifact": "approval_queue.yaml",
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

    result = run_ceo_role_dispatch(options)

    dispatch = result["role_dispatch"]
    assert dispatch["top_task_id"] == "approval_clear_stop_request"
    assert dispatch["top_role_id"] == "risk_officer"
    assert dispatch["top_result_resolution_mode"] == "manual_gate_blocked_record"
    assert dispatch["top_requires_manual_gate"] is True
    assert dispatch["top_autonomous_task_id"] == ""
    assert dispatch["top_closure_command"].endswith(
        "approval-record --run-id ceo_test --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed"
    )
    assert dispatch["next_role_result_command"].endswith(
        "role-result --run-id ceo_test --task-id approval_clear_stop_request --status blocked"
    )
    assert "--result-path" not in dispatch["next_role_result_command"]
    packet = dispatch["packets"][0]
    assert packet["requires_manual_gate"] is True
    assert packet["approval_authority"] == "user_only"
    assert packet["can_complete_with_specialist_artifact"] is False
    packet_text = Path(packet["packet_path"]).read_text(encoding="utf-8")
    assert "record it as blocked" in packet_text
    assert "Approval authority: user_only" in packet_text


def test_ceo_role_dispatch_surfaces_top_autonomous_packet_behind_manual_gate(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "evidence_debt_register.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_evidence_debt_register_v0",
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
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_queue_v0",
                "status": "pending_approvals",
                "pending_count": 1,
                "pending_items": [
                    {
                        "approval_id": "clear_stop_request",
                        "reason": "stop request needs user approval before continuing",
                        "source_artifact": "approval_queue.yaml",
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

    result = run_ceo_role_dispatch(options)

    dispatch = result["role_dispatch"]
    assert dispatch["top_task_id"] == "approval_clear_stop_request"
    assert dispatch["top_autonomous_task_id"] == "debt_candidate_a_passing_validation_result"
    assert dispatch["top_autonomous_role_id"] == "validation_referee"
    assert dispatch["top_autonomous_packet_path"].endswith("role_dispatch_packets/debt_candidate_a_passing_validation_result.md")
    assert dispatch["top_autonomous_result_resolution_mode"] == "specialist_result_required"
    assert "--task-id debt_candidate_a_passing_validation_result" in dispatch["top_autonomous_next_role_result_command"]
    assert "--status complete" in dispatch["top_autonomous_next_role_result_command"]


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
    assert dispatch["top_task_id"] == ""
    assert dispatch["next_role_result_command"] == ""
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


def test_ceo_replay_includes_repair_apply_ledger(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    snapshot_dir = root / "repair_apply_plans"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    before_snapshot = snapshot_dir / "repair_apply_before.yaml"
    after_snapshot = snapshot_dir / "repair_apply_after.yaml"
    before_snapshot.write_text(yaml.safe_dump({"status": "repairs_pending", "production_effect": "none"}), encoding="utf-8")
    after_snapshot.write_text(yaml.safe_dump({"status": "no_repairs_required", "production_effect": "none"}), encoding="utf-8")
    (root / "repair_apply_ledger.jsonl").write_text(
        json.dumps(
            {
                "model": "riskflow_ceo_repair_apply_v0",
                "generated_at": "2026-06-06T00:00:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "repair_closed",
                "repair_key": "blocker:stale_artifacts",
                "action_executed": True,
                "repair_closed": True,
                "paths": {
                    "before_repair_plan_snapshot": str(before_snapshot),
                    "after_repair_plan_snapshot": str(after_snapshot),
                },
                "before_repair_plan_snapshot_sha256": _sha256(before_snapshot),
                "after_repair_plan_snapshot_sha256": _sha256(after_snapshot),
                "production_effect": "none",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    replay = ceo_ops.build_ceo_replay(ceo_run_id="ceo_test", lab_run_id="ceo_test_lab", root=root)

    assert replay["repair_apply_count"] == 1
    assert replay["artifact_checks"]["repair_apply_ledger"]["exists"] is True
    assert replay["timeline"][0]["kind"] == "repair_apply"
    assert replay["timeline"][0]["repair_key"] == "blocker:stale_artifacts"
    assert replay["repair_apply_status"] == "pass"
    assert replay["repair_apply_checks"][0]["status"] == "pass"
    assert "repair_apply_ledger_has_incomplete_or_unsafe_entries" not in replay["issues"]


def test_ceo_replay_fails_repair_apply_with_missing_plan_snapshot(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    missing_before = root / "repair_apply_plans" / "missing_before.yaml"
    missing_after = root / "repair_apply_plans" / "missing_after.yaml"
    (root / "repair_apply_ledger.jsonl").write_text(
        json.dumps(
            {
                "model": "riskflow_ceo_repair_apply_v0",
                "generated_at": "2026-06-06T00:00:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "repair_closed",
                "repair_key": "blocker:stale_artifacts",
                "action_executed": True,
                "repair_closed": True,
                "paths": {
                    "before_repair_plan_snapshot": str(missing_before),
                    "after_repair_plan_snapshot": str(missing_after),
                },
                "before_repair_plan_snapshot_sha256": "missing",
                "after_repair_plan_snapshot_sha256": "missing",
                "production_effect": "none",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    replay = ceo_ops.build_ceo_replay(ceo_run_id="ceo_test", lab_run_id="ceo_test_lab", root=root)

    assert replay["repair_apply_count"] == 1
    assert replay["repair_apply_status"] == "fail"
    assert replay["repair_apply_checks"][0]["status"] == "fail"
    assert "missing_before_repair_plan_snapshot" in replay["repair_apply_checks"][0]["failures"]
    assert "missing_before_repair_plan_snapshot" in replay["issues"]


def test_ceo_replay_treats_legacy_no_action_repair_apply_snapshot_gap_as_advisory(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "repair_apply_ledger.jsonl").write_text(
        json.dumps(
            {
                "model": "riskflow_ceo_repair_apply_v0",
                "generated_at": "2026-06-06T00:00:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "blocked_manual_gate",
                "repair_key": "blocker:stop_requested",
                "action_attempted": False,
                "action_executed": False,
                "repair_closed": False,
                "paths": {
                    "before_repair_plan": str(root / "repair_plan.yaml"),
                    "after_repair_plan": str(root / "repair_plan.yaml"),
                },
                "production_effect": "none",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    replay = ceo_ops.build_ceo_replay(ceo_run_id="ceo_test", lab_run_id="ceo_test_lab", root=root)

    assert replay["repair_apply_status"] == "pass"
    assert replay["repair_apply_checks"][0]["status"] == "legacy_snapshot_gap"
    assert replay["repair_apply_checks"][0]["legacy_snapshot_gap"] is True
    assert "missing_before_repair_plan_snapshot_ref" not in replay["issues"]
    assert "missing_after_repair_plan_snapshot_ref" not in replay["issues"]


def test_ceo_replay_fails_operator_step_with_missing_board_snapshot(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    present_snapshot = root / "operator_step_boards" / "present_after.yaml"
    present_snapshot.parent.mkdir(parents=True, exist_ok=True)
    present_snapshot.write_text(yaml.safe_dump({"model": "riskflow_ceo_action_board_v0"}), encoding="utf-8")
    missing_snapshot = root / "operator_step_boards" / "missing_before.yaml"
    (root / "operator_step_ledger.jsonl").write_text(
        json.dumps(
            {
                "model": "riskflow_ceo_operator_step_v0",
                "generated_at": "2026-06-06T00:00:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "blocked_manual_gate",
                "action_attempted": False,
                "action_executed": False,
                "before_action_board_snapshot_sha256": "missing-sha",
                "after_action_board_snapshot_sha256": _sha256(present_snapshot),
                "paths": {
                    "before_action_board_snapshot": str(missing_snapshot),
                    "after_action_board_snapshot": str(present_snapshot),
                },
                "production_effect": "none",
                "product_language_allowed": False,
                "promotion_authority": "none",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    replay = ceo_ops.build_ceo_replay(ceo_run_id="ceo_test", lab_run_id="ceo_test_lab", root=root)

    assert replay["operator_step_count"] == 1
    assert replay["operator_step_status"] == "fail"
    assert replay["operator_step_checks"][0]["status"] == "fail"
    assert "missing_before_action_board_snapshot" in replay["operator_step_checks"][0]["failures"]
    assert "missing_before_action_board_snapshot" in replay["issues"]


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


def test_ceo_replay_fails_current_policy_action_without_dispatch_receipt_ref(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    action = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "decision": "run_champion_challenger",
        "action_taken": "champion_challenger",
        "status": "shadow_comparison_complete",
        "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
        "transition_policy_version": "riskflow_ceo_transition_policy_v1",
        "production_effect": "none",
    }
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(action), encoding="utf-8")
    (root / "ceo_action_ledger.jsonl").write_text(json.dumps(action, sort_keys=True) + "\n", encoding="utf-8")

    replay_result = run_ceo_replay(options)
    eval_result = run_ceo_eval_suite(options)

    replay = replay_result["replay"]
    cases = {item["case_id"]: item for item in eval_result["eval_suite"]["cases"]}
    assert replay["status"] == "replay_gaps"
    assert replay["dispatch_receipt_status"] == "fail"
    assert replay["dispatch_receipt_checks"][0]["status"] == "fail"
    assert "missing_action_dispatch_receipt_ref" in replay["dispatch_receipt_checks"][0]["failures"]
    assert "missing_action_dispatch_receipt_ref" in replay["issues"]
    assert cases["dispatch_receipt_backs_latest_action"]["status"] == "fail"
    assert cases["dispatch_receipts_cover_action_ledger"]["status"] == "fail"
    assert "dispatch_receipt_backs_latest_action" in eval_result["eval_suite"]["nine_nine_readiness"]["blocking_case_ids"]


def test_ceo_binding_action_writer_creates_receipt_for_guarded_direct_action(tmp_path: Path) -> None:
    options = replace(_options(tmp_path, apply=True), ceo_context="guarded_direct", ceo_authorized_action="champion-challenger")
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_preflight_gate_v0", "status": "pass", "safe_to_execute": True, "blockers": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_approval_queue_v0", "status": "no_pending_approvals", "pending_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )
    action = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "run_id": "ceo_test",
        "lab_run_id": "ceo_test_lab",
        "decision": "run_champion_challenger",
        "action_taken": "champion_challenger",
        "status": "shadow_comparison_complete",
        "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
        "production_effect": "none",
    }

    paths = ceo_ops._write_binding_action_result(options, "ceo_test", "ceo_test_lab", action)

    receipt_ref = action["dispatch_receipt"]
    receipt_path = Path(receipt_ref["path"])
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    assert paths["dispatch_receipt_snapshot"] == receipt_path
    assert receipt_path.parent.name == "dispatch_receipts"
    assert receipt_ref["sha256"] == _sha256(receipt_path)
    assert receipt["decision"] == "run_champion_challenger"
    assert receipt["dispatch_mode"] == "guarded_direct"


def test_ceo_binding_action_writer_refuses_receiptless_bound_action_without_preflight(tmp_path: Path) -> None:
    options = replace(_options(tmp_path, apply=True), ceo_context="bound_dispatch", ceo_authorized_action="patch-research-infra")
    action = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "decision": "patch_research_infra",
        "action_taken": "research_infra_patch_plan",
        "status": "planned",
        "production_effect": "none",
    }

    with pytest.raises(ValueError, match="passing preflight gate"):
        ceo_ops._write_binding_action_result(options, "ceo_test", "ceo_test_lab", action)


def test_ceo_binding_action_writer_does_not_reuse_blocked_receipt_for_allowed_action(tmp_path: Path) -> None:
    options = replace(_options(tmp_path, apply=True), ceo_context="bound_dispatch", ceo_authorized_action="patch-research-infra")
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_preflight_gate_v0", "status": "pass", "safe_to_execute": True, "blockers": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_approval_queue_v0", "status": "no_pending_approvals", "pending_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )
    blocked_snapshot = root / "dispatch_receipts" / "blocked_patch.yaml"
    blocked_snapshot.parent.mkdir(parents=True, exist_ok=True)
    blocked_receipt = {
        "model": "riskflow_ceo_dispatch_receipt_v0",
        "generated_at": "2026-06-06T00:00:00+00:00",
        "run_id": "ceo_test",
        "lab_run_id": "ceo_test_lab",
        "decision": "patch_research_infra",
        "dispatch_mode": "bound_dispatch",
        "status": "dispatch_blocked",
        "safe_to_dispatch": False,
        "snapshot_path": str(blocked_snapshot),
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
    }
    blocked_snapshot.write_text(yaml.safe_dump(blocked_receipt), encoding="utf-8")
    (root / "dispatch_receipt.yaml").write_text(yaml.safe_dump(blocked_receipt), encoding="utf-8")
    action = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-06T00:01:00+00:00",
        "run_id": "ceo_test",
        "lab_run_id": "ceo_test_lab",
        "decision": "patch_research_infra",
        "action_taken": "research_infra_patch_plan",
        "status": "planned",
        "production_effect": "none",
    }

    paths = ceo_ops._write_binding_action_result(options, "ceo_test", "ceo_test_lab", action)

    assert Path(action["dispatch_receipt"]["path"]) != blocked_snapshot
    receipt = yaml.safe_load(paths["dispatch_receipt_snapshot"].read_text(encoding="utf-8"))
    assert receipt["status"] == "dispatch_allowed"
    assert receipt["safe_to_dispatch"] is True


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


def test_ceo_replay_classifies_legacy_repeated_action_without_weakening_guarded_actions(tmp_path: Path) -> None:
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
            "decision": "run_champion_challenger",
            "action_taken": "champion_challenger",
            "status": "shadow_comparison_complete",
            "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
            "production_effect": "none",
        },
    ]
    (root / "ceo_action_ledger.jsonl").write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in entries) + "\n",
        encoding="utf-8",
    )

    result = run_ceo_replay(options)

    replay = result["replay"]
    assert replay["status"] == "replayable"
    assert replay["state_transition_status"] == "pass"
    assert replay["state_transition_legacy_gap_count"] == 1
    assert replay["state_transition_checks"][0]["status"] == "legacy_policy_gap"
    assert replay["state_transition_checks"][0]["legacy_policy_gap"] is True
    assert "illegal_action_transition" not in replay["issues"]


def test_ceo_replay_still_fails_guarded_repeated_action_with_dispatch_snapshots(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    snapshot_dir = root / "dispatch_receipts"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for index in [1, 2]:
        receipt = {
            "model": "riskflow_ceo_dispatch_receipt_v0",
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "decision": "run_champion_challenger",
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
                "decision": "run_champion_challenger",
                "action_taken": "champion_challenger",
                "status": "shadow_comparison_complete",
                "next_allowed_actions": ["run_fresh_or_control_validation_for_promising_shadow_challengers"],
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
    assert replay["status"] == "replay_gaps"
    assert replay["state_transition_status"] == "fail"
    assert replay["state_transition_legacy_gap_count"] == 0
    assert replay["state_transition_checks"][0]["status"] == "fail"
    assert "illegal_action_transition" in replay["issues"]


def test_ceo_replay_classifies_legacy_fresh_validation_alias_without_weakening_current_policy(tmp_path: Path) -> None:
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
            "decision": "run_fresh_withheld_validation_contract",
            "action_taken": "fresh_withheld_validation_contract",
            "status": "blocked_missing_inputs",
            "next_allowed_actions": ["repair_fresh_withheld_contract_inputs"],
            "production_effect": "none",
        },
    ]
    (root / "ceo_action_ledger.jsonl").write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in entries) + "\n",
        encoding="utf-8",
    )

    result = run_ceo_replay(options)

    replay = result["replay"]
    assert replay["status"] == "replayable"
    assert replay["state_transition_status"] == "pass"
    assert replay["state_transition_legacy_gap_count"] == 1
    assert replay["state_transition_checks"][0]["status"] == "legacy_policy_gap"
    assert "illegal_action_transition" not in replay["issues"]


def test_ceo_replay_fails_current_fresh_validation_alias_with_dispatch_snapshot(tmp_path: Path) -> None:
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
            "run_fresh_withheld_validation_contract",
            "fresh_withheld_validation_contract",
            "blocked_missing_inputs",
            ["repair_fresh_withheld_contract_inputs"],
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
    assert replay["status"] == "replay_gaps"
    assert replay["state_transition_status"] == "fail"
    assert replay["state_transition_legacy_gap_count"] == 0
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
    assert cases["approval_apply_has_current_provenance"]["status"] == "pass"
    assert "approval_apply_provenance=not_applicable" in cases["approval_apply_has_current_provenance"]["evidence"]
    assert cases["production_guardrails_preserved"]["status"] == "pass"
    assert cases["guardrail_audit_passes"]["status"] == "pass"
    assert cases["artifact_coherence_has_no_hard_issues"]["status"] == "pass"
    assert cases["policy_eval_fixtures_pass"]["status"] == "pass"
    assert cases["runtime_authority_manual_gates_clear"]["status"] == "pass"
    assert all(item["action_scope"] == "eval_diagnostic_only" for item in suite["cases"])
    assert all(item["dispatch_authority"] == "not_granted_by_eval_suite" for item in suite["cases"])
    assert all(item["promotion_authority"] == "none" for item in suite["cases"])
    assert all(item["production_effect"] == "none" for item in suite["cases"])
    assert suite["production_effect"] == "none"
    fixtures = yaml.safe_load(result["paths"]["eval_fixtures"].read_text(encoding="utf-8"))
    assert fixtures["case_count"] > 0
    assert "skipped_reason" not in fixtures
    assert result["paths"]["eval_suite"].exists()
    assert result["paths"]["eval_suite_report"].exists()
    assert result["paths"]["eval_fixtures"].exists()


def test_ceo_eval_suite_fails_guardrail_audit_violation(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "state_transition_status": "pass", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
        guardrail_audit={
            "model": "riskflow_ceo_guardrail_audit_v0",
            "status": "fail",
            "violations": [{"artifact": "unsafe.yaml", "violation": "product_language_allowed"}],
            "production_effect": "none",
        },
        artifact_coherence={"model": "riskflow_ceo_artifact_coherence_v0", "status": "pass", "hard_issue_count": 0, "issues": []},
    )

    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["guardrail_audit_passes"]["status"] == "fail"
    assert cases["guardrail_audit_passes"]["severity"] == "critical"
    assert "violations=1" in cases["guardrail_audit_passes"]["evidence"]
    assert suite["status"] == "fail"
    assert "guardrail_audit_passes" in suite["nine_nine_readiness"]["blocking_case_ids"]


def test_ceo_eval_suite_fails_hard_artifact_coherence_issue(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "state_transition_status": "pass", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
        guardrail_audit={"model": "riskflow_ceo_guardrail_audit_v0", "status": "pass", "violations": [], "production_effect": "none"},
        artifact_coherence={
            "model": "riskflow_ceo_artifact_coherence_v0",
            "status": "fail",
            "hard_issue_count": 1,
            "issues": [{"artifact": "dispatch_receipt", "issues": ["receipt_fingerprint_drift"]}],
            "production_effect": "none",
        },
    )

    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["artifact_coherence_has_no_hard_issues"]["status"] == "fail"
    assert cases["artifact_coherence_has_no_hard_issues"]["severity"] == "critical"
    assert "hard_issues=1" in cases["artifact_coherence_has_no_hard_issues"]["evidence"]
    assert suite["status"] == "fail"
    assert "artifact_coherence_has_no_hard_issues" in suite["nine_nine_readiness"]["blocking_case_ids"]


def test_ceo_eval_suite_missing_guardrail_and_coherence_are_not_green(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "state_transition_status": "pass", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["guardrail_audit_passes"]["status"] == "fail"
    assert "status=missing_guardrail_audit" in cases["guardrail_audit_passes"]["evidence"]
    assert cases["artifact_coherence_has_no_hard_issues"]["status"] == "fail"
    assert "status=missing_artifact_coherence" in cases["artifact_coherence_has_no_hard_issues"]["evidence"]
    assert suite["status"] == "fail"


def test_ceo_eval_suite_does_not_skip_fixtures_from_run_id_substring(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(
        tmp_path,
        run_id="ordinary_eval_fixture_named_run",
        lab_run_id="ordinary_eval_fixture_named_run_lab",
        apply=True,
    )
    calls: list[str] = []

    def fake_eval_fixtures(passed_options: CeoOpsOptions) -> dict[str, object]:
        ceo_run_id = ceo_ops.resolve_ceo_run_id(passed_options)
        lab_run_id = ceo_ops.resolve_lab_run_id(passed_options, ceo_run_id)
        root = ceo_ops.ceo_dir(passed_options, ceo_run_id)
        root.mkdir(parents=True, exist_ok=True)
        fixture_path = root / "ceo_eval_fixtures.yaml"
        fixture_report_path = root / "ceo_eval_fixtures.md"
        fixtures = {
            "model": ceo_ops.CEO_EVAL_FIXTURES_MODEL,
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "status": "pass",
            "case_count": 1,
            "failed_case_count": 0,
            "cases": [{"case_id": "sentinel_fixture_ran", "status": "pass"}],
            "production_effect": "none",
        }
        fixture_path.write_text(yaml.safe_dump(fixtures), encoding="utf-8")
        fixture_report_path.write_text("# fixtures\n", encoding="utf-8")
        calls.append(ceo_run_id)
        return {
            "run_id": ceo_run_id,
            "lab_run_id": lab_run_id,
            "fixtures": fixtures,
            "paths": {"eval_fixtures": fixture_path, "eval_fixtures_report": fixture_report_path},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_eval_fixtures", fake_eval_fixtures)

    result = run_ceo_eval_suite(options)

    assert calls == ["ordinary_eval_fixture_named_run"]
    cases = {item["case_id"]: item for item in result["eval_suite"]["cases"]}
    assert cases["policy_eval_fixtures_pass"]["status"] == "pass"
    fixtures = yaml.safe_load(result["paths"]["eval_fixtures"].read_text(encoding="utf-8"))
    assert fixtures["case_count"] == 1
    assert "skipped_reason" not in fixtures


def test_ceo_eval_suite_blocks_9_9_readiness_on_live_stop_even_with_stale_safe_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)
    root = options.report_root / "ceo_test"
    ceo_stop_path = ceo_ops.ceo_stop_path(options, "ceo_test")
    ceo_stop_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_stop_request_v0",
                "run_id": "ceo_test",
                "reason": "user_requested",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_queue_v0",
                "status": "no_pending_approvals",
                "pending_count": 0,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "status": "bounded_action_available",
                "primary_action": {"action_id": "resumption_brief_next_command", "can_execute_now": True},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_eval_suite(options)

    suite = result["eval_suite"]
    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["runtime_authority_manual_gates_clear"]["status"] == "fail"
    assert cases["runtime_authority_manual_gates_clear"]["severity"] == "critical"
    assert "stop_requested=True" in cases["runtime_authority_manual_gates_clear"]["evidence"]
    assert suite["status"] == "fail"
    assert suite["nine_nine_readiness"]["status"] == "not_9_9_ready"
    assert "runtime_authority_manual_gates_clear" in suite["nine_nine_readiness"]["blocking_case_ids"]


def test_ceo_eval_suite_explicit_internal_option_skips_nested_fixtures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = replace(_options(tmp_path, apply=True), skip_eval_fixtures=True)

    def fail_if_eval_fixtures_run(_: CeoOpsOptions) -> dict[str, object]:
        raise AssertionError("internal skip should not call run_ceo_eval_fixtures")

    monkeypatch.setattr(ceo_ops, "run_ceo_eval_fixtures", fail_if_eval_fixtures_run)

    result = run_ceo_eval_suite(options)

    fixtures = yaml.safe_load(result["paths"]["eval_fixtures"].read_text(encoding="utf-8"))
    assert fixtures["status"] == "pass"
    assert fixtures["case_count"] == 0
    assert fixtures["skipped_reason"] == "nested_eval_fixture_run"
    assert "Explicit internal fixture subruns" in fixtures["guardrail"]
    cases = {item["case_id"]: item for item in result["eval_suite"]["cases"]}
    assert cases["policy_eval_fixtures_pass"]["status"] == "fail"
    assert "cases=0" in cases["policy_eval_fixtures_pass"]["evidence"]
    assert result["eval_suite"]["nine_nine_readiness"]["status"] == "not_9_9_ready"


def test_ceo_eval_suite_does_not_require_current_receipt_for_legacy_latest_action(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "generated_at": "2026-06-06T00:01:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "decision": "run_fresh_withheld_validation_contract",
                "status": "blocked_missing_inputs",
                "action_taken": "fresh_withheld_validation_contract",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_contract_v0",
                "generated_at": "2026-06-06T00:02:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "decision": "run_frozen_candidate_validation",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_dispatch_receipt_v0",
                "generated_at": "2026-06-06T00:03:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "decision": "run_frozen_candidate_validation",
                "status": "dispatch_blocked",
                "trust_artifact_fingerprints": {},
                "product_language_allowed": False,
                "production_effect": "none",
                "promotion_authority": "none",
            }
        ),
        encoding="utf-8",
    )

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={
            "status": "replayable",
            "action_count": 1,
            "state_transition_status": "pass",
            "dispatch_receipt_status": "pass",
            "dispatch_receipt_checks": [{"status": "not_required"}],
            "production_effect": "none",
        },
        trace_grade={"verdict": "pass", "recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={
            "model": ceo_ops.CEO_MISSION_SCORE_MODEL,
            "mission_dimensions": [{"dimension_id": item} for item in ceo_ops.MISSION_DIMENSIONS],
            "product_language_allowed": False,
            "production_effect": "none",
            "promotion_authority": "none",
        },
        strategy_capital_dashboard={
            "model": ceo_ops.CEO_STRATEGY_CAPITAL_DASHBOARD_MODEL,
            "total_points": 100,
            "capital_buckets": [{"allocation_points": 100}],
            "product_language_allowed": False,
            "production_effect": "none",
            "promotion_authority": "none",
        },
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["action_contract_matches_latest_action"]["status"] == "pass"
    assert cases["dispatch_receipt_backs_latest_action"]["status"] == "pass"
    assert cases["dispatch_receipt_fingerprints_trust_artifacts"]["status"] == "pass"
    assert "latest_has_current_transition_evidence=False" in cases["action_contract_matches_latest_action"]["evidence"]
    assert "receipt_required=False" in cases["dispatch_receipt_backs_latest_action"]["evidence"]
    report = ceo_ops.render_ceo_eval_suite(suite)
    assert "## Failed Case Detail" in report
    assert "next=" in report


def test_ceo_eval_suite_checks_action_receipt_snapshot_fingerprints_not_alias(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    snapshot_path = root / "dispatch_receipts" / "action_snapshot.yaml"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "model": "riskflow_ceo_dispatch_receipt_v0",
        "run_id": "ceo_test",
        "lab_run_id": "ceo_test_lab",
        "decision": "run_champion_challenger",
        "status": "dispatch_allowed",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
        "trust_artifact_fingerprints": {},
    }
    snapshot_path.write_text(yaml.safe_dump(snapshot), encoding="utf-8")
    required_fingerprints = {
        name: {"path": str(root / f"{name}.yaml"), "exists": True, "sha256": f"{name}-sha"}
        for name in [
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
            "artifact_coherence",
            "resumption_brief",
        ]
    }
    alias = {**snapshot, "trust_artifact_fingerprints": required_fingerprints}
    (root / "dispatch_receipt.yaml").write_text(yaml.safe_dump(alias), encoding="utf-8")
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "generated_at": "2026-06-06T00:01:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "decision": "run_champion_challenger",
                "status": "shadow_comparison_complete",
                "action_taken": "champion_challenger",
                "dispatch_receipt": {"path": str(snapshot_path), "sha256": _sha256(snapshot_path)},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
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

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 1, "dispatch_receipt_status": "pass", "dispatch_receipt_checks": [{"status": "pass"}]},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    case = {item["case_id"]: item for item in suite["cases"]}["dispatch_receipt_fingerprints_trust_artifacts"]
    assert case["status"] == "fail"
    assert "fingerprints=0" in case["evidence"]
    assert "artifact_coherence" in case["evidence"]
    assert "resumption_brief" in case["evidence"]
    assert str(snapshot_path) in case["evidence"]


def test_ceo_eval_suite_fails_action_receipt_snapshot_with_unusable_required_fingerprint(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    snapshot_path = root / "dispatch_receipts" / "action_snapshot.yaml"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    required_names = [
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
        "artifact_coherence",
        "resumption_brief",
    ]
    healthy_fingerprints = {
        name: {"path": str(root / f"{name}.yaml"), "exists": True, "sha256": f"{name}-sha"}
        for name in required_names
    }
    snapshot_fingerprints = dict(healthy_fingerprints)
    snapshot_fingerprints["action_contract"] = {
        "path": str(root / "action_contract.yaml"),
        "exists": False,
        "sha256": "",
    }
    snapshot = {
        "model": "riskflow_ceo_dispatch_receipt_v0",
        "run_id": "ceo_test",
        "lab_run_id": "ceo_test_lab",
        "decision": "run_champion_challenger",
        "status": "dispatch_allowed",
        "product_language_allowed": False,
        "production_effect": "none",
        "promotion_authority": "none",
        "trust_artifact_fingerprints": snapshot_fingerprints,
    }
    snapshot_path.write_text(yaml.safe_dump(snapshot), encoding="utf-8")
    alias = {**snapshot, "trust_artifact_fingerprints": healthy_fingerprints}
    (root / "dispatch_receipt.yaml").write_text(yaml.safe_dump(alias), encoding="utf-8")
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "generated_at": "2026-06-06T00:01:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "decision": "run_champion_challenger",
                "status": "shadow_comparison_complete",
                "action_taken": "champion_challenger",
                "dispatch_receipt": {"path": str(snapshot_path), "sha256": _sha256(snapshot_path)},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
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

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 1, "dispatch_receipt_status": "pass", "dispatch_receipt_checks": [{"status": "pass"}]},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    case = {item["case_id"]: item for item in suite["cases"]}["dispatch_receipt_fingerprints_trust_artifacts"]
    assert case["status"] == "fail"
    assert "fingerprints=14" in case["evidence"]
    assert "unusable=['action_contract']" in case["evidence"]
    assert str(snapshot_path) in case["evidence"]


def test_ceo_eval_suite_requires_accepted_role_result_validation(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "role_task_ledger.jsonl").write_text(
        json.dumps(
            {
                "model": "riskflow_ceo_role_result_v0",
                "task_id": "debt_candidate_a",
                "status": "complete",
                "result_path": "review.yaml",
                "production_effect": "none",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={
            "completed_task_count": 1,
            "blocked_task_count": 0,
            "pending_task_count": 0,
            "tasks": [{"task_id": "debt_candidate_a", "status": "complete", "production_effect": "none"}],
            "production_effect": "none",
        },
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["role_results_close_the_role_queue"]["status"] == "fail"
    assert "completed_validation_accepted=False" in cases["role_results_close_the_role_queue"]["evidence"]


def test_ceo_eval_suite_flags_approval_apply_without_current_provenance(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "decision": "approval_apply",
                "action_taken": "cleared_recorded_stop_files",
                "status": "clear_stop_request_applied",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "approval_apply_clear_stop_request.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_apply_v0",
                "approval_id": "clear_stop_request",
                "status": "clear_stop_request_applied",
                "approval_item_current": False,
                "recorded_approval_item_fingerprint": "old",
                "current_approval_item_fingerprint": "",
                "source_artifact": "",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    case = {item["case_id"]: item for item in suite["cases"]}["approval_apply_has_current_provenance"]
    assert case["status"] == "fail"
    assert case["severity"] == "high"
    assert "approval_item_current=False" in case["evidence"]
    assert "fingerprints_match=False" in case["evidence"]


def test_ceo_eval_suite_accepts_approval_apply_current_provenance_path(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    approval_apply_path = root / "approval_apply_promotion_proposal.yaml"
    (root / "binding_action_result.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_binding_action_result_v0",
                "decision": "approval_apply",
                "action_taken": "promotion_approval_closure_recorded",
                "status": "promotion_approval_closed_shadow_only",
                "outputs": {"approval_apply": str(approval_apply_path)},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    approval_apply_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_apply_v0",
                "approval_id": "promotion_proposal",
                "status": "promotion_approval_closed_shadow_only",
                "approval_item_current": True,
                "recorded_approval_item_fingerprint": "matching-fingerprint",
                "current_approval_item_fingerprint": "matching-fingerprint",
                "source_artifact": "promotion_proposal.yaml",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    case = {item["case_id"]: item for item in suite["cases"]}["approval_apply_has_current_provenance"]
    assert case["status"] == "pass"
    assert "artifact_path=" in case["evidence"]
    assert "source_artifact=promotion_proposal.yaml" in case["evidence"]


def test_ceo_eval_suite_fails_pending_role_tasks_without_ledger(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={
            "completed_task_count": 0,
            "blocked_task_count": 0,
            "pending_task_count": 1,
            "pending_manual_task_count": 0,
            "pending_autonomous_task_count": 1,
            "top_pending_task_id": "debt_candidate_a",
            "tasks": [
                {
                    "task_id": "debt_candidate_a",
                    "status": "pending",
                    "role_id": "validation_referee",
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    cases = {item["case_id"]: item for item in suite["cases"]}
    role_case = cases["role_results_close_the_role_queue"]
    assert role_case["status"] == "fail"
    assert role_case["severity"] == "advisory"
    assert "pending=1" in role_case["evidence"]
    assert "pending_autonomous=1" in role_case["evidence"]
    assert "top_pending=debt_candidate_a" in role_case["evidence"]
    assert role_case["next_action"] == "record_next_autonomous_specialist_result"


def test_ceo_eval_suite_fails_blocked_role_tasks(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={
            "completed_task_count": 0,
            "blocked_task_count": 1,
            "pending_task_count": 0,
            "pending_manual_task_count": 0,
            "pending_autonomous_task_count": 0,
            "top_pending_task_id": "",
            "top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
            "top_blocked_role_id": "validation_referee",
            "top_blocked_review_status": "accepted_blocked_result",
            "top_blocked_next_action": "complete_champion_challenger_visual_review",
            "top_blocked_finding": "Visual-review queue is missing chart labels.",
            "tasks": [
                {
                    "task_id": "debt_candidate_a_visual_review_evidence",
                    "status": "blocked",
                    "role_id": "validation_referee",
                    "result_resolution_mode": "specialist_result_required",
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    role_case = {item["case_id"]: item for item in suite["cases"]}["role_results_close_the_role_queue"]
    assert role_case["status"] == "fail"
    assert role_case["severity"] == "advisory"
    assert "blocked=1" in role_case["evidence"]
    assert "top_blocked=debt_candidate_a_visual_review_evidence" in role_case["evidence"]
    assert "top_blocked_role=validation_referee" in role_case["evidence"]
    assert "top_blocked_review=accepted_blocked_result" in role_case["evidence"]
    assert "top_blocked_next=complete_champion_challenger_visual_review" in role_case["evidence"]
    assert "top_blocked_finding=Visual-review queue is missing chart labels." in role_case["evidence"]
    assert role_case["next_action"] == "review_blocked_role_tasks_or_complete_missing_evidence"


def test_ceo_eval_suite_routes_manual_pending_role_tasks_to_user_approval(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 1, "production_effect": "none"},
        role_queue={
            "completed_task_count": 0,
            "blocked_task_count": 0,
            "pending_task_count": 1,
            "pending_manual_task_count": 1,
            "pending_autonomous_task_count": 0,
            "top_pending_task_id": "approval_clear_stop_request",
            "tasks": [
                {
                    "task_id": "approval_clear_stop_request",
                    "status": "pending",
                    "role_id": "risk_officer",
                    "result_resolution_mode": "manual_gate_blocked_record",
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    role_case = {item["case_id"]: item for item in suite["cases"]}["role_results_close_the_role_queue"]
    assert role_case["status"] == "fail"
    assert "pending_manual=1" in role_case["evidence"]
    assert role_case["next_action"] == "wait_for_user_approval_or_record_manual_gate_blocked"


def test_ceo_eval_suite_requires_repair_apply_ledger_for_latest_receipt(tmp_path: Path) -> None:
    root = tmp_path / "reports" / "ceo_runs" / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "repair_apply.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_repair_apply_v0",
                "generated_at": "2026-06-06T00:00:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "repair_closed",
                "repair_key": "blocker:stale_artifacts",
                "action_executed": True,
                "repair_closed": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    suite = ceo_ops.build_ceo_eval_suite(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        root=root,
        replay={"status": "replayable", "action_count": 0, "dispatch_receipt_status": "pass"},
        trace_grade={"recommended_next_action": "continue", "production_effect": "none"},
        approval_queue={"pending_count": 0, "production_effect": "none"},
        role_queue={"completed_task_count": 0, "blocked_task_count": 0, "pending_task_count": 0, "tasks": [], "production_effect": "none"},
        fresh_withheld_execution={"production_effect": "none"},
        evidence_debt_register={"debt_count": 0, "production_effect": "none"},
        mission_score={"overall_mission_score": 80, "lowest_dimension": "reset_quality", "production_effect": "none"},
        strategy_capital_dashboard={"selected_capital_bucket": "validation_authority", "production_effect": "none"},
        eval_fixtures={"status": "pass", "case_count": 1, "production_effect": "none"},
    )

    cases = {item["case_id"]: item for item in suite["cases"]}
    assert cases["repair_apply_receipt_is_replayable"]["status"] == "fail"
    assert "latest_repair_apply=True" in cases["repair_apply_receipt_is_replayable"]["evidence"]
    assert "ledger_entries=0" in cases["repair_apply_receipt_is_replayable"]["evidence"]


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
    assert "action_receipt_exists=False" in cases["dispatch_receipt_backs_latest_action"]["evidence"]
    assert "action_receipt_sha_match=False" in cases["dispatch_receipt_backs_latest_action"]["evidence"]
    assert "action_receipt_path=" in cases["dispatch_receipt_backs_latest_action"]["evidence"]
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
    assert "role_results_close_the_role_queue" in missing_strategy["nine_nine_readiness"]["advisory_case_ids"]

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
    assert allocator["selected_lane"]["action_scope"] == "portfolio_attention_only"
    assert allocator["selected_lane"]["dispatch_authority"] == "not_granted_by_portfolio_allocator_lane"
    assert allocator["action_scope"] == "portfolio_attention_only"
    assert allocator["dispatch_authority"] == "not_granted_by_portfolio_allocator"
    assert allocator["runtime_authority_note"] == ceo_ops.CEO_RUNTIME_AUTHORITY_NOTE
    assert allocator["product_language_allowed"] is False
    assert allocator["production_effect"] == "none"
    assert allocator["promotion_authority"] == "none"
    assert result["paths"]["portfolio_allocator"].exists()
    assert result["paths"]["portfolio_allocator_report"].exists()
    report = result["paths"]["portfolio_allocator_report"].read_text(encoding="utf-8")
    assert "Attention next action: wait_for_user_approval" in report
    assert "Action scope: portfolio_attention_only" in report
    assert "Dispatch authority: not_granted_by_portfolio_allocator" in report


def test_ceo_portfolio_allocator_empty_lanes_defer_to_runtime_authority() -> None:
    allocator = ceo_ops.build_ceo_portfolio_allocator(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        operating_dashboard={
            "candidate_portfolio_count": 0,
            "validation_gate": {"next_action": ""},
        },
        executive_kpis={"kpis": {}},
        approval_queue={"pending_count": 0},
        role_queue={"pending_task_count": 0, "next_action": ""},
        evidence_debt_register={"debt_count": 0, "next_action": ""},
        capability_backlog={"backlog_count": 0, "items": []},
        trace_grade={"verdict": "pass", "recommended_next_action": ""},
        knowledge_graph_delta={"recommended_obsidian_summaries": []},
    )

    fallback_lanes = {
        lane["lane_id"]: lane["next_action"]
        for lane in allocator["lanes"]
        if lane["lane_id"] in {"approval_governance", "research_infrastructure", "specialist_review", "memory_handoff"}
    }
    assert set(fallback_lanes.values()) == {"defer_to_runtime_authority_surface"}
    assert all(action != "continue_with_bound_action_dispatch" for action in fallback_lanes.values())
    assert all(lane["action_scope"] == "portfolio_attention_only" for lane in allocator["lanes"])
    assert allocator["dispatch_authority"] == "not_granted_by_portfolio_allocator"
    assert allocator["production_effect"] == "none"


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
    assert score["action_scope"] == "mission_strategy_only"
    assert score["dispatch_authority"] == "not_granted_by_mission_score"
    assert score["runtime_authority_note"] == ceo_ops.CEO_RUNTIME_AUTHORITY_NOTE
    assert all(item["action_scope"] == "mission_strategy_only" for item in dimensions.values())
    assert all(item["dispatch_authority"] == "not_granted_by_mission_score_dimension" for item in dimensions.values())
    assert result["paths"]["mission_score"].exists()
    assert result["paths"]["mission_score_report"].exists()
    report = result["paths"]["mission_score_report"].read_text(encoding="utf-8")
    assert "Mission attention action:" in report
    assert "Action scope: mission_strategy_only" in report
    assert "Dispatch authority: not_granted_by_mission_score" in report


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
    assert dimensions["warning_blocker"]["action_scope"] == "mission_strategy_only"
    assert dimensions["warning_blocker"]["dispatch_authority"] == "not_granted_by_mission_score_dimension"
    assert score["action_scope"] == "mission_strategy_only"
    assert score["dispatch_authority"] == "not_granted_by_mission_score"
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
    assert dashboard["safe_to_continue_scope"] == "strategy_attention_only_not_dispatch_authority"
    assert dashboard["dispatch_authority"] == "not_granted_by_strategy_capital_dashboard"
    assert dashboard["selected_capital_bucket"] == "approval_and_safety"
    assert dashboard["selected_strategy"] == "wait_for_user_approval_or_repair_preflight"
    assert dashboard["capital_buckets"][0]["bucket_id"] == "approval_and_safety"
    assert "pending_user_approval" in dashboard["capital_buckets"][0]["blocked_by"]


def test_ceo_strategy_capital_points_sum_to_100() -> None:
    dashboard = ceo_ops.build_ceo_strategy_capital_dashboard(**_strategy_dashboard_inputs())

    assert dashboard["status"] == "strategy_capital_allocated"
    assert dashboard["safe_to_continue"] is True
    assert dashboard["safe_to_continue_scope"] == "strategy_attention_only_not_dispatch_authority"
    assert dashboard["dispatch_authority"] == "not_granted_by_strategy_capital_dashboard"
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
    assert dashboard["safe_to_continue_scope"] == "strategy_attention_only_not_dispatch_authority"
    assert dashboard["dispatch_authority"] == "not_granted_by_strategy_capital_dashboard"
    assert sum(int(item["allocation_points"]) for item in dashboard["capital_buckets"]) == 100
    report = result["paths"]["strategy_capital_dashboard_report"].read_text(encoding="utf-8")
    assert "Safety scope: strategy_attention_only_not_dispatch_authority" in report
    assert "Dispatch authority: not_granted_by_strategy_capital_dashboard" in report
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
    assert brief["trace_grade_status"] in {"pass", "warn", "fail"}
    assert "trace_grade_recommended_next_action" in brief
    assert "trace_grade_manual_data_import_required" in brief
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
    report = result["paths"]["resumption_brief_report"].read_text(encoding="utf-8")
    assert "Trace grade:" in report
    assert "Trace recommended next action:" in report
    assert "Trace manual data import required:" in report
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
    assert brief["authorized_strategic_route"] == "run_fresh_withheld_validation_executor"
    assert brief["authorized_route_source"] == "strategy_capital_dashboard"
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
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_contract_v0",
                "generated_at": "2026-06-06T00:01:30+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "decision": "run_champion_challenger",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "executive_decision_packet.md").write_text("# packet\n", encoding="utf-8")
    for name in [
        "preflight_gate.yaml",
        "ceo_replay.yaml",
        "ceo_eval_suite.yaml",
        "mission_score.yaml",
        "strategy_capital_dashboard.yaml",
        "approval_queue.yaml",
        "approval_status.yaml",
        "role_task_queue.yaml",
        "role_dispatch.yaml",
        "role_result_validation.yaml",
        "repair_apply.yaml",
        "action_board.yaml",
        "decision_quality.yaml",
        "operator_brief.yaml",
    ]:
        _write_coherence_artifact(root, name)
    action = yaml.safe_load((root / "binding_action_result.yaml").read_text(encoding="utf-8"))
    receipt_path = Path(action["dispatch_receipt"]["path"])
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    for fingerprint_name, artifact_name in {
        "action_contract": "action_contract.yaml",
        "preflight_gate": "preflight_gate.yaml",
        "ceo_replay": "ceo_replay.yaml",
        "ceo_eval_suite": "ceo_eval_suite.yaml",
        "mission_score": "mission_score.yaml",
        "strategy_capital_dashboard": "strategy_capital_dashboard.yaml",
        "approval_queue": "approval_queue.yaml",
        "approval_status": "approval_status.yaml",
        "role_task_queue": "role_task_queue.yaml",
        "role_dispatch": "role_dispatch.yaml",
        "role_result_validation": "role_result_validation.yaml",
        "repair_apply": "repair_apply.yaml",
        "action_board": "action_board.yaml",
        "decision_quality": "decision_quality.yaml",
        "operator_brief": "operator_brief.yaml",
    }.items():
        artifact_path = root / artifact_name
        receipt["trust_artifact_fingerprints"][fingerprint_name] = {
            "path": str(artifact_path),
            "exists": artifact_path.exists(),
            "sha256": _sha256(artifact_path) if artifact_path.exists() else "",
        }
    receipt_path.write_text(yaml.safe_dump(receipt), encoding="utf-8")
    action["dispatch_receipt"]["sha256"] = _sha256(receipt_path)
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(action), encoding="utf-8")
    (root / "ceo_action_ledger.jsonl").write_text(json.dumps(action, sort_keys=True) + "\n", encoding="utf-8")


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


def test_ceo_artifact_coherence_keeps_stale_decision_quality_advisory(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    _write_coherence_artifact(root, "decision_quality.yaml", generated_at="2026-06-06T00:00:30+00:00")

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    issues = {item["artifact"]: item["issues"] for item in coherence["issues"]}
    assert coherence["status"] == "pass_with_advisory_issues"
    assert coherence["hard_issue_count"] == 0
    assert "stale_before_latest_action" in issues["decision_quality"]


def test_ceo_artifact_coherence_keeps_approval_role_freshness_advisory(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    _write_coherence_artifact(root, "approval_queue.yaml", generated_at="2026-06-06T00:00:30+00:00")
    _write_coherence_artifact(root, "role_task_queue.yaml", generated_at="2026-06-06T00:00:30+00:00")
    _write_coherence_artifact(root, "role_result_validation.yaml", generated_at="2026-06-06T00:00:30+00:00")
    (root / "role_dispatch.yaml").unlink()

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    issues = {item["artifact"]: item for item in coherence["issues"]}
    assert coherence["status"] == "pass_with_advisory_issues"
    assert coherence["hard_issue_count"] == 0
    assert "stale_before_latest_action" in issues["approval_queue"]["issues"]
    assert "stale_before_latest_action" in issues["role_task_queue"]["issues"]
    assert "stale_before_latest_action" in issues["role_result_validation"]["issues"]
    assert issues["role_dispatch"]["issues"] == ["missing_artifact"]
    assert all(item["severity"] == "advisory" for item in issues.values())


def test_ceo_artifact_coherence_flags_manual_gate_handoff_semantic_mismatch(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    (root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "manual_gate_required",
                "primary_action": {
                    "action_id": "blocker:stop_requested",
                    "command_kind": "manual_gate",
                    "can_execute_now": True,
                    "requires_manual_gate": True,
                },
                "runnable_repairs": [
                    {"action_id": "resumption_brief_next_command", "can_execute_now": True},
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "decision_quality_written",
                "effective_runtime_action": "blocker:stop_requested",
                "effective_runtime_command_kind": "manual_gate",
                "effective_runtime_can_execute_now": True,
                "runtime_blocked": False,
                "runtime_block_reason": "",
                "selected_action_is_executable_now": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "ready_for_one_operator_step",
                "current_situation": {
                    "action_board_status": "manual_gate_required",
                    "primary_action": "blocker:stop_requested",
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    semantic = next(item for item in coherence["issues"] if item["artifact"] == "handoff_semantics")
    assert coherence["status"] == "fail"
    assert coherence["hard_issue_count"] == 1
    assert semantic["severity"] == "hard"
    assert "manual_gate_primary_marked_executable" in semantic["issues"]
    assert "manual_gate_has_runnable_actions" in semantic["issues"]
    assert "manual_gate_decision_quality_selected_action_executable" in semantic["issues"]
    assert "manual_gate_operator_brief_status_mismatch" in semantic["issues"]
    report = result["paths"]["artifact_coherence_report"].read_text(encoding="utf-8")
    assert "handoff_semantics" in report
    assert "action_board_status" in report


def test_ceo_artifact_coherence_flags_bounded_action_handoff_semantic_mismatch(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    (root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "bounded_action_available",
                "primary_action": {
                    "action_id": "resumption_brief_next_command",
                    "command_kind": "bounded_dispatch",
                    "can_execute_now": True,
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "decision_quality_written",
                "effective_runtime_action": "blocker:stop_requested",
                "effective_runtime_command_kind": "manual_gate",
                "effective_runtime_can_execute_now": False,
                "runtime_blocked": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "waiting_on_manual_gate",
                "current_situation": {
                    "action_board_status": "bounded_action_available",
                    "primary_action": "resumption_brief_next_command",
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    semantic = next(item for item in coherence["issues"] if item["artifact"] == "handoff_semantics")
    assert coherence["status"] == "pass_with_advisory_issues"
    assert coherence["hard_issue_count"] == 0
    assert semantic["severity"] == "advisory"
    assert "decision_quality_effective_action_mismatch" in semantic["issues"]
    assert "bounded_action_decision_quality_not_executable" in semantic["issues"]
    assert "bounded_action_operator_brief_status_mismatch" in semantic["issues"]


def test_ceo_artifact_coherence_flags_live_stop_stale_safe_handoff(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    ceo_ops.ceo_stop_path(options, "ceo_test").write_text("user_requested\n", encoding="utf-8")
    (root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "bounded_action_available",
                "primary_action": {
                    "action_id": "resumption_brief_next_command",
                    "command_kind": "bounded_dispatch",
                    "can_execute_now": True,
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "decision_quality_written",
                "effective_runtime_action": "resumption_brief_next_command",
                "effective_runtime_command_kind": "bounded_dispatch",
                "effective_runtime_can_execute_now": True,
                "runtime_blocked": False,
                "selected_action_is_executable_now": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "ready_for_one_operator_step",
                "current_situation": {
                    "action_board_status": "bounded_action_available",
                    "primary_action": "resumption_brief_next_command",
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    semantic = next(item for item in coherence["issues"] if item["artifact"] == "handoff_semantics")
    assert coherence["status"] == "fail"
    assert coherence["hard_issue_count"] == 1
    assert semantic["severity"] == "hard"
    assert "live_stop_runtime_authority_mismatch" in semantic["issues"]
    assert "action_board_bounded_action_available" in semantic["evidence"]["live_stop_stale_safe_signals"]
    assert "decision_quality_effective_runtime_executable" in semantic["evidence"]["live_stop_stale_safe_signals"]
    assert semantic["evidence"]["stop_requested"] is True


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


def test_ceo_artifact_coherence_flags_action_contract_decision_mismatch(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_contract_v0",
                "generated_at": "2026-06-06T00:05:00+00:00",
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "decision": "run_frozen_candidate_validation",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    issues = {item["artifact"]: item["issues"] for item in coherence["issues"]}
    assert coherence["status"] == "fail"
    assert coherence["hard_issue_count"] == 2
    assert "action_contract_decision_mismatch" in issues["action_contract"]


def test_ceo_artifact_coherence_keeps_legacy_no_receipt_action_advisory(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    action = yaml.safe_load((root / "binding_action_result.yaml").read_text(encoding="utf-8"))
    action.pop("dispatch_receipt", None)
    action.pop("transition_policy_version", None)
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(action), encoding="utf-8")
    (root / "ceo_action_ledger.jsonl").write_text(json.dumps(action, sort_keys=True) + "\n", encoding="utf-8")
    contract = yaml.safe_load((root / "action_contract.yaml").read_text(encoding="utf-8"))
    contract["decision"] = "run_frozen_candidate_validation"
    (root / "action_contract.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    issues = {item["artifact"]: item["issues"] for item in coherence["issues"]}
    assert coherence["status"] == "pass_with_advisory_issues"
    assert coherence["hard_issue_count"] == 0
    assert coherence["advisory_issue_count"] == 2
    assert coherence["latest_action_has_current_transition_evidence"] is False
    assert "action_contract_decision_mismatch" in issues["action_contract"]
    assert "missing_action_dispatch_receipt_ref" in issues["dispatch_receipt"]


def test_ceo_artifact_coherence_flags_missing_action_receipt_snapshot(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    action = yaml.safe_load((root / "binding_action_result.yaml").read_text(encoding="utf-8"))
    missing_receipt = root / "dispatch_receipts" / "missing_receipt.yaml"
    action["dispatch_receipt"] = {"path": str(missing_receipt), "sha256": "missing"}
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(action), encoding="utf-8")

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    issues = {item["artifact"]: item["issues"] for item in coherence["issues"]}
    assert coherence["status"] == "fail"
    assert "missing_action_dispatch_receipt_snapshot" in issues["dispatch_receipt"]


def test_ceo_artifact_coherence_flags_receipt_fingerprint_drift(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    _write_clean_coherence_inputs(root)
    action = yaml.safe_load((root / "binding_action_result.yaml").read_text(encoding="utf-8"))
    receipt_path = Path(action["dispatch_receipt"]["path"])
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    preflight_path = root / "preflight_gate.yaml"
    receipt["trust_artifact_fingerprints"]["preflight_gate"] = {
        "path": str(preflight_path),
        "exists": True,
        "sha256": _sha256(preflight_path),
    }
    receipt_path.write_text(yaml.safe_dump(receipt), encoding="utf-8")
    action["dispatch_receipt"]["sha256"] = _sha256(receipt_path)
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(action), encoding="utf-8")
    _write_coherence_artifact(root, "preflight_gate.yaml", generated_at="2026-06-06T00:06:00+00:00")

    result = run_ceo_artifact_coherence(options)

    coherence = result["coherence"]
    dispatch_issue = next(item for item in coherence["issues"] if item["artifact"] == "dispatch_receipt")
    mismatches = dispatch_issue["evidence"]["trust_fingerprint_mismatches"]
    assert coherence["status"] == "fail"
    assert "dispatch_receipt_trust_fingerprint_drift" in dispatch_issue["issues"]
    assert mismatches[0]["artifact"] == "preflight_gate"
    assert mismatches[0]["reason"] == "fingerprinted_artifact_sha_mismatch"


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


def test_ceo_resumption_brief_allows_advisory_artifact_coherence_issues(tmp_path: Path) -> None:
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
            "status": "pass_with_advisory_issues",
            "hard_issue_count": 0,
            "advisory_issue_count": 2,
            "issues": [
                {"artifact": "action_contract", "issues": ["action_contract_decision_mismatch"]},
                {"artifact": "dispatch_receipt", "issues": ["missing_action_dispatch_receipt_ref"]},
            ],
            "production_effect": "none",
        },
        latest_packet=latest_packet,
    )

    assert brief["resume_status"] == "safe_for_one_bound_action"
    assert "execute-next" in brief["next_command"]


def test_ceo_run_index_classifies_runs_and_next_commands(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    clean_root = options.report_root / "ceo_clean_actionable"
    actionable_root = options.report_root / "ceo_actionable"
    eval_blocked_root = options.report_root / "ceo_eval_blocked"
    stale_trace_root = options.report_root / "ceo_stale_trace_fail"
    stale_manual_gate_root = options.report_root / "ceo_stale_manual_gate"
    stale_stop_safe_root = options.report_root / "ceo_stale_stop_safe"
    stopped_root = options.report_root / "ceo_stopped"
    blocked_root = options.report_root / "ceo_blocked"
    for root in [
        clean_root,
        actionable_root,
        eval_blocked_root,
        stale_trace_root,
        stale_manual_gate_root,
        stale_stop_safe_root,
        stopped_root,
        blocked_root,
    ]:
        root.mkdir(parents=True, exist_ok=True)

    (clean_root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "run_id": "ceo_clean_actionable",
                "lab_run_id": "ceo_clean_actionable_lab",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo operator-step --run-id ceo_clean_actionable --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (clean_root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"status": "pass", "safe_to_execute": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (clean_root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump({"status": "dispatch_allowed", "safe_to_dispatch": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (clean_root / "artifact_coherence.yaml").write_text(
        yaml.safe_dump({"status": "pass", "issue_count": 0, "issues": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (clean_root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"status": "no_pending_approvals", "pending_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )

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
    (actionable_root / "trace_grade.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_trace_grade_v0",
                "verdict": "pass",
                "score": 93,
                "recommended_next_action": "continue_with_one_bound_ceo_action",
                "issues": [],
                "criteria": {"manual_data_import_required": False},
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
    (actionable_root / "repair_apply.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_repair_apply_v0",
                "status": "repair_closed",
                "repair_key": "blocker:stale_artifacts",
                "action_executed": True,
                "repair_closed": True,
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
    (actionable_root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "status": "bounded_action_available",
                "primary_action": {
                    "action_id": "resumption_brief_next_command",
                    "command_kind": "bounded_dispatch",
                    "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_actionable --apply",
                    "can_execute_now": True,
                    "authorized_strategic_route": "run_fresh_withheld_validation_executor",
                    "authorized_route_source": "action_contract",
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "status": "decision_quality_written",
                "selected_action": "run_fresh_withheld_validation_executor",
                "confidence": "medium",
                "runtime_authority_status": "bounded_action_available",
                "executable_next_action": "resumption_brief_next_command",
                "executable_next_command_kind": "bounded_dispatch",
                "runtime_authorized_strategic_route": "run_fresh_withheld_validation_executor",
                "executable_can_execute_now": True,
                "selected_action_is_executable_now": True,
                "selected_action_blocked_by": "",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "ceo_replay.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_replay_v0",
                "status": "replayable",
                "issues": [],
                "operator_step_status": "pass",
                "operator_step_count": 3,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "ceo_eval_suite.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_eval_suite_v0",
                "status": "pass",
                "score": 94,
                "nine_nine_readiness": {
                    "status": "ready_for_extended_autonomy",
                    "blocking_case_ids": [],
                    "advisory_case_ids": ["role_results_close_the_role_queue"],
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "artifact_coherence.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_artifact_coherence_v0",
                "status": "pass_with_advisory_issues",
                "issue_count": 1,
                "hard_issue_count": 0,
                "advisory_issue_count": 1,
                "issues": [
                    {
                        "artifact": "action_contract",
                        "issues": ["action_contract_decision_mismatch"],
                        "severity": "advisory",
                    }
                ],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "approval_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_queue_v0",
                "status": "pending_approvals",
                "pending_count": 1,
                "pending_items": [
                    {
                        "approval_id": "clear_stop_request",
                        "kind": "resume_stopped_run",
                        "reason": "stop request awaits user approval",
                        "source_artifact": "stop.request",
                        "required_user_decision": "approve_or_reject_resume_or_clear_stop",
                        "approval_authority": "user_only",
                        "approval_item_fingerprint": "actionable-stop-fingerprint",
                    }
                ],
                "top_pending_approval_id": "clear_stop_request",
                "top_pending_approval_record_command": "PYTHONPATH=src python3 -m riskflow ceo approval-record --run-id ceo_actionable --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed",
                "top_pending_approval_apply_command": "PYTHONPATH=src python3 -m riskflow ceo approval-apply --run-id ceo_actionable --approval-id clear_stop_request --user-confirmed --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "approval_status.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_approval_status_v0",
                "status": "pending_approvals",
                "pending_count": 1,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "role_result_validation.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_result_v0",
                "status": "accepted",
                "task_id": "debt_candidate_a",
                "issues": [],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (actionable_root / "role_task_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_task_queue_v0",
                "status": "pending_role_tasks",
                "pending_task_count": 2,
                "pending_manual_task_count": 1,
                "pending_autonomous_task_count": 1,
                "completed_task_count": 1,
                "blocked_task_count": 2,
                "top_pending_task_id": "approval_clear_stop_request",
                "top_pending_role_id": "risk_officer",
                "top_pending_owner_command": "wait_for_user_approval",
                "top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
                "top_blocked_role_id": "product_translator",
                "top_blocked_packet_path": "reports/ceo_runs/ceo_actionable/role_dispatch_packets/debt_candidate_a_visual_review_evidence.md",
                "top_blocked_result_resolution_mode": "specialist_result_required",
                "top_blocked_validation_status": "accepted",
                "top_blocked_review_status": "accepted_blocked_result",
                "top_blocked_result_path": "reports/ceo_runs/ceo_actionable/specialist_results/debt_candidate_a_visual_review_evidence.yaml",
                "top_blocked_next_action": "complete_champion_challenger_visual_review",
                "top_blocked_finding": "Visual review evidence is missing.",
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

    (eval_blocked_root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "run_id": "ceo_eval_blocked",
                "lab_run_id": "ceo_eval_blocked_lab",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo operator-step --run-id ceo_eval_blocked --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (eval_blocked_root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"status": "pass", "safe_to_execute": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (eval_blocked_root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump({"status": "dispatch_allowed", "safe_to_dispatch": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (eval_blocked_root / "trace_grade.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_trace_grade_v0",
                "verdict": "fail",
                "score": 55,
                "recommended_next_action": "stop_for_manual_data_import",
                "issues": ["manual_data_import_required"],
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (eval_blocked_root / "artifact_coherence.yaml").write_text(
        yaml.safe_dump({"status": "pass", "issue_count": 0, "issues": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (eval_blocked_root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"status": "no_pending_approvals", "pending_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )
    (eval_blocked_root / "ceo_replay.yaml").write_text(
        yaml.safe_dump({"status": "replay_gaps", "issues": ["missing_action_ledger_entries"], "production_effect": "none"}),
        encoding="utf-8",
    )
    (eval_blocked_root / "ceo_eval_suite.yaml").write_text(
        yaml.safe_dump({"status": "fail", "score": 40, "nine_nine_readiness": {"blocking_case_ids": ["replayable_action_timeline"]}, "production_effect": "none"}),
        encoding="utf-8",
    )

    (stale_trace_root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "run_id": "ceo_stale_trace_fail",
                "lab_run_id": "ceo_stale_trace_fail_lab",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_stale_trace_fail --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_trace_root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"status": "pass", "safe_to_execute": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_trace_root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump({"status": "dispatch_allowed", "safe_to_dispatch": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_trace_root / "trace_grade.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_trace_grade_v0",
                "verdict": "fail",
                "score": 15,
                "recommended_next_action": "import_or_curate_fresh_ohlcv_data",
                "issues": ["manual_data_import_required"],
                "criteria": {"manual_data_import_required": True},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_trace_root / "ceo_replay.yaml").write_text(
        yaml.safe_dump({"status": "replayable", "issues": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_trace_root / "ceo_eval_suite.yaml").write_text(
        yaml.safe_dump({"status": "pass", "score": 95, "nine_nine_readiness": {"blocking_case_ids": []}, "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_trace_root / "artifact_coherence.yaml").write_text(
        yaml.safe_dump({"status": "pass", "issue_count": 0, "issues": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_trace_root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"status": "no_pending_approvals", "pending_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )

    (stale_manual_gate_root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "run_id": "ceo_stale_manual_gate",
                "lab_run_id": "ceo_stale_manual_gate_lab",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_stale_manual_gate --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_manual_gate_root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"status": "pass", "safe_to_execute": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_manual_gate_root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump({"status": "dispatch_allowed", "safe_to_dispatch": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_manual_gate_root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "status": "manual_gate_required",
                "primary_action": {"action_id": "blocker:stop_requested", "command_kind": "manual_gate"},
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_manual_gate_root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "status": "waiting_on_manual_gate",
                "plain_english_summary": "CEO mode is stopped at a manual gate.",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_manual_gate_root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "runtime_authority_status": "manual_gate_required",
                "runtime_blocked": True,
                "runtime_block_reason": "manual_gate_required:blocker:stop_requested",
                "selected_action": "run_frozen_candidate_validation",
                "selected_action_is_executable_now": False,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_manual_gate_root / "artifact_coherence.yaml").write_text(
        yaml.safe_dump({"status": "pass", "issue_count": 0, "issues": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_manual_gate_root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"status": "no_pending_approvals", "pending_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )

    (stale_stop_safe_root / "stop.request").write_text("user_requested\n", encoding="utf-8")
    (stale_stop_safe_root / "resumption_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_resumption_brief_v0",
                "run_id": "ceo_stale_stop_safe",
                "lab_run_id": "ceo_stale_stop_safe_lab",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_stale_stop_safe --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_stop_safe_root / "preflight_gate.yaml").write_text(
        yaml.safe_dump({"status": "pass", "safe_to_execute": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_stop_safe_root / "dispatch_receipt.yaml").write_text(
        yaml.safe_dump({"status": "dispatch_allowed", "safe_to_dispatch": True, "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_stop_safe_root / "action_board.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_board_v0",
                "status": "bounded_action_available",
                "primary_action": {
                    "action_id": "resumption_brief_next_command",
                    "command_kind": "bounded_dispatch",
                    "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_stale_stop_safe --apply",
                    "can_execute_now": True,
                },
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_stop_safe_root / "operator_brief.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_operator_brief_v0",
                "status": "ready_for_one_operator_step",
                "plain_english_summary": "CEO mode has one bounded action available.",
                "recommended_next_action": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_stale_stop_safe --apply",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_stop_safe_root / "decision_quality.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_decision_quality_v0",
                "runtime_authority_status": "bounded_action_available",
                "effective_runtime_action": "resumption_brief_next_command",
                "effective_runtime_command_kind": "bounded_dispatch",
                "effective_runtime_can_execute_now": True,
                "runtime_blocked": False,
                "selected_action": "run_champion_challenger",
                "selected_action_is_executable_now": True,
                "executable_next_action": "resumption_brief_next_command",
                "executable_next_command_kind": "bounded_dispatch",
                "executable_can_execute_now": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (stale_stop_safe_root / "artifact_coherence.yaml").write_text(
        yaml.safe_dump({"status": "pass", "issue_count": 0, "issues": [], "production_effect": "none"}),
        encoding="utf-8",
    )
    (stale_stop_safe_root / "approval_queue.yaml").write_text(
        yaml.safe_dump({"status": "no_pending_approvals", "pending_count": 0, "production_effect": "none"}),
        encoding="utf-8",
    )

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
    assert index["status_counts"]["stopped"] == 2
    assert index["status_counts"]["blocked"] == 5
    assert rows["ceo_clean_actionable"]["status"] == "actionable"
    assert rows["ceo_actionable"]["status"] == "blocked"
    assert rows["ceo_eval_blocked"]["status"] == "blocked"
    assert rows["ceo_eval_blocked"]["replay_status"] == "replay_gaps"
    assert rows["ceo_eval_blocked"]["eval_suite_status"] == "fail"
    assert rows["ceo_eval_blocked"]["trace_grade_status"] == "fail"
    assert rows["ceo_eval_blocked"]["trace_grade_manual_data_import_required"] is True
    assert rows["ceo_stale_trace_fail"]["status"] == "blocked"
    assert rows["ceo_stale_trace_fail"]["resume_status"] == "safe_for_one_bound_action"
    assert rows["ceo_stale_trace_fail"]["preflight_status"] == "pass"
    assert rows["ceo_stale_trace_fail"]["dispatch_safe_to_dispatch"] is True
    assert rows["ceo_stale_trace_fail"]["replay_status"] == "replayable"
    assert rows["ceo_stale_trace_fail"]["eval_suite_status"] == "pass"
    assert rows["ceo_stale_trace_fail"]["trace_grade_status"] == "fail"
    assert rows["ceo_stale_trace_fail"]["trace_grade_manual_data_import_required"] is True
    assert rows["ceo_stale_manual_gate"]["status"] == "blocked"
    assert rows["ceo_stale_manual_gate"]["dispatch_receipt_status"] == "dispatch_allowed"
    assert rows["ceo_stale_manual_gate"]["dispatch_safe_to_dispatch"] is True
    assert rows["ceo_stale_manual_gate"]["effective_operator_status"] == "manual_gate_required"
    assert rows["ceo_stale_manual_gate"]["manual_gate_active"] is True
    assert rows["ceo_stale_manual_gate"]["effective_operator_runtime_block_reason"] == "manual_gate_required:blocker:stop_requested"
    assert rows["ceo_stale_manual_gate"]["action_board_status"] == "manual_gate_required"
    assert rows["ceo_stale_manual_gate"]["decision_quality_runtime_authority"] == "manual_gate_required"
    assert rows["ceo_stale_manual_gate"]["decision_quality_runtime_blocked"] is True
    assert rows["ceo_stale_stop_safe"]["status"] == "stopped"
    assert rows["ceo_stale_stop_safe"]["resume_status"] == "blocked_stop_requested"
    assert rows["ceo_stale_stop_safe"]["dispatch_receipt_status"] == "dispatch_blocked"
    assert rows["ceo_stale_stop_safe"]["dispatch_safe_to_dispatch"] is False
    assert rows["ceo_stale_stop_safe"]["dispatch_reason"] == "live stop request/manual gate overrides reused safe artifacts"
    assert rows["ceo_stale_stop_safe"]["effective_operator_status"] == "manual_gate_required"
    assert rows["ceo_stale_stop_safe"]["manual_gate_active"] is True
    assert rows["ceo_stale_stop_safe"]["effective_operator_runtime_block_reason"] == "manual_gate_required:blocker:stop_requested"
    assert rows["ceo_stale_stop_safe"]["action_board_status"] == "manual_gate_required"
    assert rows["ceo_stale_stop_safe"]["operator_brief_status"] == "waiting_on_manual_gate"
    assert rows["ceo_stale_stop_safe"]["operator_brief_next_action"].endswith("approval-queue --run-id ceo_stale_stop_safe")
    assert rows["ceo_stale_stop_safe"]["decision_quality_effective_runtime_action"] == "blocker:stop_requested"
    assert rows["ceo_stale_stop_safe"]["decision_quality_effective_runtime_command_kind"] == "manual_gate"
    assert rows["ceo_stale_stop_safe"]["decision_quality_effective_runtime_can_execute_now"] is False
    assert rows["ceo_stale_stop_safe"]["decision_quality_runtime_authority"] == "manual_gate_required"
    assert rows["ceo_stale_stop_safe"]["decision_quality_executable_next_action"] == "blocker:stop_requested"
    assert rows["ceo_stale_stop_safe"]["decision_quality_executable_command_kind"] == "manual_gate"
    assert rows["ceo_stale_stop_safe"]["decision_quality_executable_can_execute_now"] is False
    assert rows["ceo_stale_stop_safe"]["decision_quality_selected_action_is_executable_now"] is False
    assert rows["ceo_stale_stop_safe"]["decision_quality_selected_action_blocked_by"] == "manual_gate_required:blocker:stop_requested"
    assert rows["ceo_stale_stop_safe"]["next_command"].endswith("approval-queue --run-id ceo_stale_stop_safe")
    assert "execute-next" not in rows["ceo_stale_stop_safe"]["next_command"]
    assert rows["ceo_actionable"]["latest_decision_packet_exists"] is True
    assert rows["ceo_actionable"]["dispatch_receipt_status"] == "dispatch_allowed"
    assert rows["ceo_actionable"]["dispatch_safe_to_dispatch"] is True
    assert rows["ceo_actionable"]["trace_grade_status"] == "pass"
    assert rows["ceo_actionable"]["trace_grade_score"] == 93
    assert rows["ceo_actionable"]["trace_grade_recommended_next_action"] == "continue_with_one_bound_ceo_action"
    assert rows["ceo_actionable"]["trace_grade_manual_data_import_required"] is False
    assert rows["ceo_actionable"]["top_blocker"] == ""
    assert rows["ceo_actionable"]["incident_count"] == 0
    assert rows["ceo_actionable"]["repair_plan_status"] == "no_repairs_required"
    assert rows["ceo_actionable"]["top_repair"] == ""
    assert rows["ceo_actionable"]["top_repair_kind"] == ""
    assert rows["ceo_actionable"]["repair_apply_status"] == "repair_closed"
    assert rows["ceo_actionable"]["repair_apply_key"] == "blocker:stale_artifacts"
    assert rows["ceo_actionable"]["repair_apply_executed"] is True
    assert rows["ceo_actionable"]["repair_apply_closed"] is True
    assert rows["ceo_actionable"]["effective_operator_status"] == "bounded_action_available"
    assert rows["ceo_actionable"]["manual_gate_active"] is False
    assert rows["ceo_actionable"]["operator_brief_status"] == "ready_for_one_operator_step"
    assert rows["ceo_actionable"]["operator_brief_summary"] == "CEO mode has one bounded action available."
    assert rows["ceo_actionable"]["decision_quality_status"] == "decision_quality_written"
    assert rows["ceo_actionable"]["decision_quality_selected_action"] == "run_fresh_withheld_validation_executor"
    assert rows["ceo_actionable"]["decision_quality_confidence"] == "medium"
    assert rows["ceo_actionable"]["decision_quality_runtime_authority"] == "bounded_action_available"
    assert rows["ceo_actionable"]["decision_quality_executable_next_action"] == "resumption_brief_next_command"
    assert rows["ceo_actionable"]["decision_quality_executable_command_kind"] == "bounded_dispatch"
    assert rows["ceo_actionable"]["decision_quality_runtime_authorized_strategic_route"] == "run_fresh_withheld_validation_executor"
    assert rows["ceo_actionable"]["decision_quality_executable_can_execute_now"] is True
    assert rows["ceo_actionable"]["decision_quality_selected_action_is_executable_now"] is True
    assert rows["ceo_actionable"]["decision_quality_selected_action_blocked_by"] == ""
    assert rows["ceo_actionable"]["replay_status"] == "replayable"
    assert rows["ceo_actionable"]["replay_issue_count"] == 0
    assert rows["ceo_actionable"]["operator_step_status"] == "pass"
    assert rows["ceo_actionable"]["operator_step_count"] == 3
    assert rows["ceo_actionable"]["eval_suite_status"] == "pass"
    assert rows["ceo_actionable"]["eval_suite_score"] == 94
    assert rows["ceo_actionable"]["nine_nine_readiness"] == "ready_for_extended_autonomy"
    assert rows["ceo_actionable"]["nine_nine_blocking_case_count"] == 0
    assert rows["ceo_actionable"]["artifact_coherence_status"] == "pass_with_advisory_issues"
    assert rows["ceo_actionable"]["artifact_coherence_issue_count"] == 1
    assert rows["ceo_actionable"]["artifact_coherence_top_issue"] == "action_contract"
    assert rows["ceo_actionable"]["artifact_coherence_top_issue_types"] == ["action_contract_decision_mismatch"]
    assert rows["ceo_actionable"]["artifact_coherence_top_issue_severity"] == "advisory"
    assert rows["ceo_actionable"]["approval_queue_status"] == "pending_approvals"
    assert rows["ceo_actionable"]["approval_pending_count"] == 1
    assert rows["ceo_actionable"]["approval_top_pending_id"] == "clear_stop_request"
    assert rows["ceo_actionable"]["approval_top_pending_kind"] == "resume_stopped_run"
    assert rows["ceo_actionable"]["approval_top_pending_reason"] == "stop request awaits user approval"
    assert rows["ceo_actionable"]["approval_top_pending_source"] == "stop.request"
    assert rows["ceo_actionable"]["approval_top_pending_required_user_decision"] == "approve_or_reject_resume_or_clear_stop"
    assert rows["ceo_actionable"]["approval_top_pending_authority"] == "user_only"
    assert rows["ceo_actionable"]["approval_top_pending_fingerprint"] == "actionable-stop-fingerprint"
    assert rows["ceo_actionable"]["approval_record_command"].endswith(
        "approval-record --run-id ceo_actionable --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed"
    )
    assert rows["ceo_actionable"]["role_queue_status"] == "pending_role_tasks"
    assert rows["ceo_actionable"]["role_pending_task_count"] == 2
    assert rows["ceo_actionable"]["role_pending_manual_task_count"] == 1
    assert rows["ceo_actionable"]["role_pending_autonomous_task_count"] == 1
    assert rows["ceo_actionable"]["role_completed_task_count"] == 1
    assert rows["ceo_actionable"]["role_blocked_task_count"] == 2
    assert rows["ceo_actionable"]["role_top_pending_task_id"] == "approval_clear_stop_request"
    assert rows["ceo_actionable"]["role_top_pending_role_id"] == "risk_officer"
    assert rows["ceo_actionable"]["role_top_pending_owner_command"] == "wait_for_user_approval"
    assert rows["ceo_actionable"]["role_top_blocked_task_id"] == "debt_candidate_a_visual_review_evidence"
    assert rows["ceo_actionable"]["role_top_blocked_role_id"] == "product_translator"
    assert rows["ceo_actionable"]["role_top_blocked_result_resolution_mode"] == "specialist_result_required"
    assert rows["ceo_actionable"]["role_top_blocked_validation_status"] == "accepted"
    assert rows["ceo_actionable"]["role_top_blocked_closure_command"].endswith(
        "role-result --run-id ceo_actionable --task-id debt_candidate_a_visual_review_evidence "
        "--status complete --result-path <path-to-specialist-result.yaml>"
    )
    assert rows["ceo_actionable"]["role_top_blocked_review_status"] == "accepted_blocked_result"
    assert rows["ceo_actionable"]["role_top_blocked_result_path"].endswith("debt_candidate_a_visual_review_evidence.yaml")
    assert rows["ceo_actionable"]["role_top_blocked_next_action"] == "complete_champion_challenger_visual_review"
    assert rows["ceo_actionable"]["role_top_blocked_finding"] == "Visual review evidence is missing."
    assert rows["ceo_actionable"]["role_result_validation_status"] == "accepted"
    assert rows["ceo_actionable"]["role_result_validation_task"] == "debt_candidate_a"
    assert rows["ceo_actionable"]["mission_score"] == 82
    assert rows["ceo_actionable"]["strategy_capital_bucket"] == "validation_authority"
    assert rows["ceo_stopped"]["status"] == "stopped"
    assert rows["ceo_blocked"]["status"] == "blocked"
    assert rows["ceo_blocked"]["preflight_blockers"] == ["pending_user_approval"]
    assert rows["ceo_blocked"]["next_command"].endswith("ceo resumption-brief --run-id ceo_blocked")
    report = result["paths"]["run_index_report"].read_text(encoding="utf-8")
    assert "resumption_next=" in report
    assert "brief=ready_for_one_operator_step" in report
    assert "decision=run_fresh_withheld_validation_executor" in report
    assert "decision_authority=bounded_action_available" in report
    assert "decision_exec=resumption_brief_next_command" in report
    assert "decision_can_execute=True" in report
    assert "decision_blocked_by=none" in report
    assert "effective_operator=bounded_action_available" in report
    assert "manual_gate_active=False" in report
    assert "decision_runtime_route=run_fresh_withheld_validation_executor" in report
    assert "trace=pass" in report
    assert "trace_score=93" in report
    assert "trace_next=continue_with_one_bound_ceo_action" in report
    assert "manual_data_import_required=False" in report
    assert "repair_apply=repair_closed" in report
    assert "replay=replayable" in report
    assert "operator_step=pass" in report
    assert "operator_steps=3" in report
    assert "eval=pass" in report
    assert "eval_score=94" in report
    assert "readiness=ready_for_extended_autonomy" in report
    assert "readiness_blockers=0" in report
    assert "coherence=pass_with_advisory_issues" in report
    assert "coherence_issues=1" in report
    assert "artifact_coherence_top_issue=action_contract severity=advisory" in report
    assert "types=['action_contract_decision_mismatch']" in report
    assert "approval=pending_approvals" in report
    assert "top_approval=clear_stop_request" in report
    assert "kind=resume_stopped_run" in report
    assert "authority=user_only" in report
    assert "reason=stop request awaits user approval" in report
    assert "source=stop.request" in report
    assert "fingerprint=actionable-stop-fingerprint" in report
    assert "approval-record --run-id ceo_actionable --approval-id clear_stop_request" in report
    assert "repair_closed=True" in report
    assert "repair_apply_key=blocker:stale_artifacts" in report
    assert "role_queue=pending_role_tasks" in report
    assert "role_pending=2" in report
    assert "role_completed=1" in report
    assert "role_blocked=2" in report
    assert "top_role_task=approval_clear_stop_request" in report
    assert "top_blocked_role_task=debt_candidate_a_visual_review_evidence" in report
    assert "role_validation=accepted" in report
    assert "top_blocked_role_review=accepted_blocked_result" in report
    assert "top_blocked_role_finding=Visual review evidence is missing." in report
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


def test_ceo_cli_run_index_prints_latest_decision_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_index_path = tmp_path / "reports" / "ceo_runs" / "run_index.yaml"
    run_index_report_path = tmp_path / "reports" / "ceo_runs" / "run_index.md"

    def fake_run_index(_options: CeoOpsOptions, *, limit: int = 25) -> dict[str, object]:
        return {
            "run_index": {
                "model": "riskflow_ceo_run_index_v0",
                "status": "runs_indexed",
                "run_count": 1,
                "status_counts": {"stopped": 1},
                "runs": [
                    {
                        "run_id": "ceo_latest",
                        "status": "stopped",
                        "artifact_coherence_status": "pass_with_advisory_issues",
                        "artifact_coherence_top_issue": "action_contract",
                        "artifact_coherence_top_issue_severity": "advisory",
                        "effective_operator_status": "manual_gate_required",
                        "manual_gate_active": True,
                        "decision_quality_selected_action": "run_frozen_candidate_validation",
                        "decision_quality_runtime_authority": "manual_gate_required",
                        "decision_quality_executable_can_execute_now": False,
                        "decision_quality_selected_action_blocked_by": "manual_gate_required:blocker:stop_requested",
                        "role_top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
                        "role_top_blocked_role_id": "product_translator",
                        "role_top_blocked_result_resolution_mode": "specialist_result_required",
                        "role_top_blocked_validation_status": "accepted",
                        "role_top_blocked_closure_command": (
                            "PYTHONPATH=src python3 -m riskflow ceo role-result --run-id ceo_latest "
                            "--task-id debt_candidate_a_visual_review_evidence --status complete "
                            "--result-path <path-to-specialist-result.yaml>"
                        ),
                        "role_top_blocked_review_status": "accepted_blocked_result",
                        "role_top_blocked_result_path": (
                            "reports/ceo_runs/ceo_latest/specialist_results/"
                            "debt_candidate_a_visual_review_evidence.yaml"
                        ),
                        "role_top_blocked_next_action": "complete_champion_challenger_visual_review",
                        "role_top_blocked_finding": "Visual review evidence is missing.",
                        "next_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_latest",
                    }
                ],
                "production_effect": "none",
            },
            "paths": {"run_index": run_index_path, "run_index_report": run_index_report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_run_index", fake_run_index)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="run-index",
            run_id=None,
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            limit=25,
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Latest run: ceo_latest" in out
    assert "Latest artifact coherence: pass_with_advisory_issues" in out
    assert "Latest artifact coherence top issue: action_contract" in out
    assert "Latest artifact coherence top issue severity: advisory" in out
    assert "Latest effective operator status: manual_gate_required" in out
    assert "Latest manual gate active: True" in out
    assert "Latest decision: run_frozen_candidate_validation" in out
    assert "Latest decision authority: manual_gate_required" in out
    assert "Latest decision can execute: False" in out
    assert "Latest decision blocked by: manual_gate_required:blocker:stop_requested" in out
    assert "Latest top blocked role task: debt_candidate_a_visual_review_evidence" in out
    assert "Latest top blocked role: product_translator" in out
    assert "Latest top blocked role mode: specialist_result_required" in out
    assert "Latest top blocked role validation: accepted" in out
    assert "Latest top blocked role closure: PYTHONPATH=src python3 -m riskflow ceo role-result" in out
    assert "Latest top blocked role review: accepted_blocked_result" in out
    assert "Latest top blocked role result: reports/ceo_runs/ceo_latest/specialist_results/debt_candidate_a_visual_review_evidence.yaml" in out
    assert "Latest top blocked role next action: complete_champion_challenger_visual_review" in out
    assert "Latest top blocked role finding: Visual review evidence is missing." in out
    assert "Latest next command: PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_latest" in out


def test_ceo_cli_status_prints_runtime_authority_without_selected_action(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_status(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "company_status": {
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "lab_status": {},
                "stop_requested": True,
                "true_blocker": False,
                "open_lanes": [],
                "operating_artifacts": {
                    "decision_quality_status": "missing_decision_quality",
                    "decision_quality_effective_runtime_action": "blocker:stop_requested",
                    "decision_quality_effective_runtime_command_kind": "manual_gate",
                    "decision_quality_effective_runtime_can_execute_now": False,
                    "decision_quality_runtime_blocked": True,
                    "decision_quality_runtime_block_reason": "manual_gate_required:blocker:stop_requested",
                    "decision_quality_runtime_authority": "manual_gate_required",
                    "decision_quality_executable_next_action": "blocker:stop_requested",
                    "decision_quality_executable_command_kind": "manual_gate",
                    "decision_quality_executable_can_execute_now": False,
                    "decision_quality_selected_action_is_executable_now": False,
                    "decision_quality_selected_action_blocked_by": "manual_gate_required:blocker:stop_requested",
                },
            }
        }

    monkeypatch.setattr(cli, "run_ceo_status", fake_status)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="status",
            run_id="ceo_test",
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            show_lab_status=False,
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Decision quality effective runtime action: blocker:stop_requested" in out
    assert "Decision quality selected action: none" in out
    assert "Decision quality runtime authority: manual_gate_required" in out
    assert "Decision quality selected action blocked by: manual_gate_required:blocker:stop_requested" in out


def test_ceo_cli_flight_dashboard_prints_trace_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dashboard_path = tmp_path / "flight.yaml"
    dashboard_report_path = tmp_path / "flight.md"

    def fake_flight_dashboard(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "dashboard": {
                "safe_to_continue": False,
                "blockers": ["trace_grade_failed"],
                "next_recommended_action": "honor_stop_request",
                "trace_grade": {
                    "verdict": "fail",
                    "score": 15,
                    "recommended_next_action": "honor_stop_request",
                    "manual_data_import_required": False,
                    "issues": ["stop_requested"],
                },
            },
            "paths": {"dashboard": dashboard_path, "dashboard_report": dashboard_report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_flight_dashboard", fake_flight_dashboard)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="flight-dashboard",
            run_id="ceo_test",
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Trace verdict: fail" in out
    assert "Trace score: 15" in out
    assert "Trace recommended next action: honor_stop_request" in out
    assert "Trace manual data import required: False" in out
    assert "Trace issues: ['stop_requested']" in out
    assert "Safety scope: flight_dashboard_only_not_dispatch_authority" in out
    assert "Dispatch authority: not_granted_by_flight_dashboard" in out


def test_ceo_cli_operating_dashboard_prints_trace_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dashboard_path = tmp_path / "operating.yaml"
    dashboard_report_path = tmp_path / "operating.md"

    def fake_operating_dashboard(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "dashboard": {
                "candidate_portfolio_count": 2,
                "capability_backlog_count": 1,
                "next_recommended_action": "repair_trace",
                "trace": {
                    "verdict": "warn",
                    "score": 72,
                    "recommended_next_action": "repair_trace",
                    "manual_data_import_required": True,
                    "issues": ["manual_data_import_required"],
                },
            },
            "paths": {"dashboard": dashboard_path, "dashboard_report": dashboard_report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_operating_dashboard", fake_operating_dashboard)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="operating-dashboard",
            run_id="ceo_test",
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Trace verdict: warn" in out
    assert "Trace score: 72" in out
    assert "Safety scope: flight_dashboard_only_not_dispatch_authority" in out
    assert "Dispatch authority: not_granted_by_operating_dashboard" in out
    assert "Trace recommended next action: repair_trace" in out
    assert "Trace manual data import required: True" in out
    assert "Trace issues: ['manual_data_import_required']" in out


def test_ceo_cli_strategy_capital_dashboard_prints_authority_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dashboard_path = tmp_path / "strategy.yaml"
    dashboard_report_path = tmp_path / "strategy.md"

    def fake_strategy_dashboard(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "dashboard": {
                "safe_to_continue": True,
                "safe_to_continue_scope": "strategy_attention_only_not_dispatch_authority",
                "dispatch_authority": "not_granted_by_strategy_capital_dashboard",
                "runtime_authority_note": "Dispatch authority is decided by ceo status.",
                "selected_capital_bucket": "validation_authority",
                "selected_strategy": "run_fresh_withheld_validation_executor",
                "total_points": 100,
            },
            "paths": {
                "strategy_capital_dashboard": dashboard_path,
                "strategy_capital_dashboard_report": dashboard_report_path,
            },
        }

    monkeypatch.setattr(cli, "run_ceo_strategy_capital_dashboard", fake_strategy_dashboard)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="strategy-capital-dashboard",
            run_id="ceo_test",
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Safety scope: strategy_attention_only_not_dispatch_authority" in out
    assert "Dispatch authority: not_granted_by_strategy_capital_dashboard" in out
    assert "Runtime authority note: Dispatch authority is decided by ceo status." in out


def test_ceo_cli_executive_kpis_prints_authority_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    kpi_path = tmp_path / "executive_kpis.yaml"
    report_path = tmp_path / "executive_kpis.md"

    def fake_executive_kpis(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "kpis": {
                "status": "operating_clear",
                "next_action": "defer_to_runtime_authority_surface",
                "next_action_scope": "executive_health_diagnostic_only",
                "dispatch_authority": "not_granted_by_executive_kpis",
                "runtime_authority_note": "Dispatch authority is decided by ceo status.",
                "kpis": {
                    "open_approval_count": 0,
                    "evidence_debt_count": 0,
                    "trace_verdict": "pass",
                    "trace_score": 91,
                    "trace_recommended_next_action": "defer_to_runtime_authority_surface",
                    "trace_manual_data_import_required": False,
                    "trace_issues": [],
                },
            },
            "paths": {"executive_kpis": kpi_path, "executive_kpis_report": report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_executive_kpis", fake_executive_kpis)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="executive-kpis",
            run_id="ceo_test",
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Attention next action: defer_to_runtime_authority_surface" in out
    assert "Next action scope: executive_health_diagnostic_only" in out
    assert "Dispatch authority: not_granted_by_executive_kpis" in out
    assert "Runtime authority note: Dispatch authority is decided by ceo status." in out


def test_ceo_cli_portfolio_allocator_prints_authority_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    allocator_path = tmp_path / "portfolio_allocator.yaml"
    report_path = tmp_path / "portfolio_allocator.md"

    def fake_portfolio_allocator(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "allocator": {
                "selected_lane": {
                    "lane_id": "validation_authority",
                    "score": 90,
                    "next_action": "run_fresh_withheld_validation_executor",
                },
                "action_scope": "portfolio_attention_only",
                "dispatch_authority": "not_granted_by_portfolio_allocator",
                "runtime_authority_note": "Dispatch authority is decided by ceo status.",
                "production_effect": "none",
            },
            "paths": {"portfolio_allocator": allocator_path, "portfolio_allocator_report": report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_portfolio_allocator", fake_portfolio_allocator)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="portfolio-allocator",
            run_id="ceo_test",
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Attention next action: run_fresh_withheld_validation_executor" in out
    assert "Action scope: portfolio_attention_only" in out
    assert "Dispatch authority: not_granted_by_portfolio_allocator" in out
    assert "Runtime authority note: Dispatch authority is decided by ceo status." in out


def test_ceo_cli_mission_score_prints_authority_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    score_path = tmp_path / "mission_score.yaml"
    report_path = tmp_path / "mission_score.md"

    def fake_mission_score(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "mission_score": {
                "status": "mission_compounding",
                "overall_mission_score": 72,
                "lowest_dimension": "reset_quality",
                "next_best_mission_action": "run_champion_challenger",
                "action_scope": "mission_strategy_only",
                "dispatch_authority": "not_granted_by_mission_score",
                "runtime_authority_note": "Dispatch authority is decided by ceo status.",
                "production_effect": "none",
            },
            "paths": {"mission_score": score_path, "mission_score_report": report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_mission_score", fake_mission_score)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="mission-score",
            run_id="ceo_test",
            lab_run_id=None,
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        )
    )

    out = capsys.readouterr().out
    assert status == 0
    assert "Mission attention action: run_champion_challenger" in out
    assert "Action scope: mission_strategy_only" in out
    assert "Dispatch authority: not_granted_by_mission_score" in out
    assert "Runtime authority note: Dispatch authority is decided by ceo status." in out


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
    assert stack["top_blocker_evidence"] == "blocked_stop_requested"
    assert "pending_user_approval" in blocker_ids
    assert "replay_gaps" in blocker_ids
    assert "eval_blocking_case:replayable_action_timeline" in blocker_ids
    assert "memory_delta_unresolved" in blocker_ids
    assert "evidence_debt_open" in blocker_ids
    assert "approval-queue" in stack["next_command"]
    assert result["paths"]["blocker_stack"].exists()
    assert result["paths"]["blocker_stack_report"].exists()
    report = result["paths"]["blocker_stack_report"].read_text(encoding="utf-8")
    assert "Top blocker evidence: blocked_stop_requested" in report
    assert "evidence=blocked_stop_requested" in report
    assert "evidence=pending_approvals=1" in report
    assert stack["production_effect"] == "none"


def test_ceo_blocker_stack_stop_overrides_stale_resumption_next_command() -> None:
    stack = ceo_ops.build_ceo_blocker_stack(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        stop_requested=True,
        preflight_gate={},
        dispatch_receipt={"status": "dispatch_allowed", "safe_to_dispatch": True},
        resumption_brief={
            "resume_status": "safe_for_one_bound_action",
            "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
        },
        replay={"status": "replayable"},
        eval_suite={"nine_nine_readiness": {"blocking_case_ids": []}},
        approval_queue={},
        memory_delta={},
        evidence_debt_register={},
    )

    assert stack["status"] == "blocked"
    assert stack["top_blocker"] == "stop_requested"
    assert stack["top_blocker_evidence"] == "safe_for_one_bound_action"
    assert stack["next_command"] == "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test"
    assert "execute-next" not in stack["next_command"]


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
    assert all(item["implementation_playbook"]["non_executable_by_repair_apply"] is True for item in symbolic_items)
    assert plan["implementation_playbook_count"] == len(symbolic_items)
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
    assert item["implementation_playbook"]["summary"].startswith("Repair CEO replay state-transition policy")
    assert "src/riskflow/ceo_ops.py" in item["implementation_playbook"]["target_files"]
    assert "_build_ceo_state_transition_checks" in item["implementation_playbook"]["target_functions"]
    assert "replay" in item["implementation_playbook"]["test_selectors"]
    assert item["implementation_playbook"]["non_executable_by_repair_apply"] is True
    assert plan["implementation_playbook_count"] == 1
    assert plan["autonomous_repair_count"] == 0
    assert plan["runnable_repair_count"] == 0


def test_ceo_repair_plan_targets_trust_alignment_playbook_for_artifact_coherence_incidents(tmp_path: Path) -> None:
    plan = ceo_ops.build_ceo_repair_plan(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        blocker_stack={"model": "riskflow_ceo_blocker_stack_v0", "blockers": [], "production_effect": "none"},
        incident_register={
            "model": "riskflow_ceo_operating_incident_register_v0",
            "incidents": [
                {
                    "incident_key": "artifact_coherence:action_contract:action_contract_decision_mismatch",
                    "severity": "high",
                    "category": "artifact_coherence",
                    "owner_command": "rerun_or_repair_stale_trust_artifacts",
                    "closure_condition": "artifact_coherence.status is pass",
                    "latest_evidence": {"evidence": "action_contract_decision_mismatch"},
                    "production_effect": "none",
                },
                {
                    "incident_key": "artifact_coherence:dispatch_receipt:missing_action_dispatch_receipt_ref",
                    "severity": "high",
                    "category": "artifact_coherence",
                    "owner_command": "rerun_or_repair_stale_trust_artifacts",
                    "closure_condition": "artifact_coherence.status is pass",
                    "latest_evidence": {"evidence": "missing_action_dispatch_receipt_ref"},
                    "production_effect": "none",
                },
            ],
            "production_effect": "none",
        },
    )

    items = {item["repair_key"]: item for item in plan["repair_items"]}
    for key in [
        "incident:artifact_coherence:action_contract:action_contract_decision_mismatch",
        "incident:artifact_coherence:dispatch_receipt:missing_action_dispatch_receipt_ref",
    ]:
        playbook = items[key]["implementation_playbook"]
        assert items[key]["command_kind"] == "implementation_required"
        assert playbook["summary"].startswith("Repair latest-action trust alignment")
        assert "_write_ceo_action_contract" in playbook["target_functions"]
        assert "_write_ceo_dispatch_receipt" in playbook["target_functions"]
        assert "artifact_coherence" in playbook["test_selectors"]
        assert "eval_suite" in playbook["test_selectors"]


def test_ceo_repair_plan_targets_repair_apply_snapshot_playbook(tmp_path: Path) -> None:
    plan = ceo_ops.build_ceo_repair_plan(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        blocker_stack={"model": "riskflow_ceo_blocker_stack_v0", "blockers": [], "production_effect": "none"},
        incident_register={
            "model": "riskflow_ceo_operating_incident_register_v0",
            "incidents": [
                {
                    "incident_key": "replay_issue:missing_before_repair_plan_snapshot_ref",
                    "severity": "high",
                    "category": "replay",
                    "owner_command": "repair_replay_artifacts",
                    "closure_condition": "ceo_replay no longer reports missing_before_repair_plan_snapshot_ref",
                    "latest_evidence": {"evidence": "missing_before_repair_plan_snapshot_ref"},
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
    )

    item = plan["repair_items"][0]
    playbook = item["implementation_playbook"]
    assert item["command_kind"] == "implementation_required"
    assert playbook["summary"].startswith("Repair repair-apply replayability")
    assert "run_ceo_repair_apply" in playbook["target_functions"]
    assert "_build_repair_apply_checks" in playbook["target_functions"]
    assert "repair_apply" in playbook["test_selectors"]
    assert "replay" in playbook["test_selectors"]


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
    assert items["incident:replay_issue:illegal_action_transition"]["implementation_playbook"]["test_selectors"] == ["replay", "eval_suite"]
    assert plan["autonomous_repair_count"] == 0
    assert plan["runnable_repair_count"] == 0
    assert plan["diagnostic_refresh_count"] == 1
    assert "repair-apply" in plan["next_command"]
    assert "--repair-key blocker:stale_artifacts" in plan["next_command"]


def test_ceo_action_board_routes_repair_items_through_repair_apply(tmp_path: Path) -> None:
    board = ceo_ops.build_ceo_action_board(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        resumption_brief={"resume_status": "blocked_preflight", "next_command": "PYTHONPATH=src python3 -m riskflow ceo resumption-brief --run-id ceo_test"},
        dispatch_receipt={"model": "riskflow_ceo_dispatch_receipt_v0", "status": "dispatch_blocked", "safe_to_dispatch": False},
        blocker_stack={"model": "riskflow_ceo_blocker_stack_v0", "status": "blocked", "top_blocker": "stale_artifacts"},
        repair_plan={
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "repair_plan_ready",
            "top_repair": "blocker:stale_artifacts",
            "top_repair_kind": "diagnostic_refresh",
            "repair_items": [
                {
                    "repair_key": "blocker:stale_artifacts",
                    "source": "blocker_stack",
                    "command_kind": "diagnostic_refresh",
                    "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id ceo_test",
                    "evidence": "artifact stale",
                    "can_execute_autonomously": False,
                    "requires_manual_gate": False,
                    "diagnostic_only": True,
                    "needs_implementation": False,
                    "closure_condition": "artifact coherence passes",
                }
            ],
        },
        executive_kpis={"model": "riskflow_ceo_executive_kpis_v0", "status": "attention_required", "next_action": "refresh_artifact_coherence"},
    )

    assert board["status"] == "diagnostic_refresh_recommended"
    primary = board["primary_action"]
    assert primary["action_id"] == "blocker:stale_artifacts"
    assert primary["command_kind"] == "diagnostic_refresh"
    assert "repair-apply" in primary["command"]
    assert "--repair-key blocker:stale_artifacts" in primary["command"]
    assert "artifact-coherence" not in primary["command"]


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


def test_ceo_repair_apply_requires_apply(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=False)

    with pytest.raises(ValueError, match="requires --apply"):
        run_ceo_repair_apply(options, repair_key="blocker:stale_artifacts")


def test_ceo_repair_apply_refuses_manual_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    repair_plan_path = root / "repair_plan.yaml"
    repair_plan_report_path = root / "repair_plan.md"
    plan = {
        "model": "riskflow_ceo_repair_plan_v0",
        "status": "manual_gate_first",
        "top_repair": "blocker:pending_user_approval",
        "repair_items": [
            {
                "repair_key": "blocker:pending_user_approval",
                "source": "blocker_stack",
                "severity": "critical",
                "command_kind": "manual_gate",
                "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "requires_manual_gate": True,
                "needs_implementation": False,
                "closure_condition": "approval queue clears",
                "production_effect": "none",
            }
        ],
        "production_effect": "none",
    }

    def fake_repair_plan(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "repair_plan": plan,
            "paths": {"repair_plan": repair_plan_path, "repair_plan_report": repair_plan_report_path},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_repair_plan", fake_repair_plan)

    result = run_ceo_repair_apply(options, repair_key="blocker:pending_user_approval")

    apply_result = result["repair_apply"]
    assert apply_result["model"] == "riskflow_ceo_repair_apply_v0"
    assert apply_result["status"] == "blocked_manual_gate"
    assert apply_result["action_attempted"] is False
    assert apply_result["action_executed"] is False
    assert apply_result["repair_closed"] is False
    ledger_entries = result["paths"]["repair_apply_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger_entries) == 1
    assert json.loads(ledger_entries[0])["repair_key"] == "blocker:pending_user_approval"
    assert result["paths"]["repair_apply"].exists()
    report = result["paths"]["repair_apply_report"].read_text(encoding="utf-8")
    assert "Production effect: none." in report


def test_ceo_repair_apply_blocks_lower_priority_runnable_when_manual_gate_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    repair_plan_path = root / "repair_plan.yaml"
    repair_plan_report_path = root / "repair_plan.md"
    plan = {
        "model": "riskflow_ceo_repair_plan_v0",
        "status": "manual_gate_first",
        "top_repair": "blocker:pending_user_approval",
        "repair_items": [
            {
                "repair_key": "blocker:pending_user_approval",
                "source": "blocker_stack",
                "severity": "critical",
                "command_kind": "manual_gate",
                "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "requires_manual_gate": True,
                "needs_implementation": False,
                "closure_condition": "approval queue clears",
                "production_effect": "none",
            },
            {
                "repair_key": "blocker:research_infra_patch",
                "source": "blocker_stack",
                "severity": "high",
                "command_kind": "runnable_cli",
                "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo patch-research-infra --run-id ceo_test --apply",
                "requires_manual_gate": False,
                "needs_implementation": False,
                "closure_condition": "research infra patch executed",
                "production_effect": "none",
            },
        ],
        "production_effect": "none",
    }

    def fake_repair_plan(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "repair_plan": plan,
            "paths": {"repair_plan": repair_plan_path, "repair_plan_report": repair_plan_report_path},
        }

    def fail_patch_research_infra(_: CeoOpsOptions) -> dict[str, object]:
        raise AssertionError("repair-apply must not execute lower-priority work behind a manual gate")

    monkeypatch.setattr(ceo_ops, "run_ceo_repair_plan", fake_repair_plan)
    monkeypatch.setattr(ceo_ops, "run_ceo_patch_research_infra", fail_patch_research_infra)

    result = run_ceo_repair_apply(options, repair_key="blocker:research_infra_patch")

    apply_result = result["repair_apply"]
    assert apply_result["status"] == "blocked_repair_plan_not_ready"
    assert apply_result["action_attempted"] is False
    assert apply_result["action_executed"] is False
    assert apply_result["repair_closed"] is False
    assert apply_result["before_plan_status"] == "manual_gate_first"
    assert apply_result["before_top_repair"] == "blocker:pending_user_approval"
    ledger_entries = result["paths"]["repair_apply_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger_entries) == 1
    assert json.loads(ledger_entries[0])["status"] == "blocked_repair_plan_not_ready"


def test_ceo_repair_apply_runs_diagnostic_refresh_without_false_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    repair_plan_path = root / "repair_plan.yaml"
    repair_plan_report_path = root / "repair_plan.md"
    calls: list[str] = []
    plan = {
        "model": "riskflow_ceo_repair_plan_v0",
        "status": "repair_plan_ready",
        "top_repair": "blocker:stale_artifacts",
        "repair_items": [
            {
                "repair_key": "blocker:stale_artifacts",
                "source": "blocker_stack",
                "severity": "high",
                "command_kind": "diagnostic_refresh",
                "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id ceo_test",
                "requires_manual_gate": False,
                "needs_implementation": False,
                "diagnostic_only": True,
                "closure_condition": "artifact coherence passes",
                "production_effect": "none",
            }
        ],
        "production_effect": "none",
    }

    def fake_repair_plan(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "repair_plan": plan,
            "paths": {"repair_plan": repair_plan_path, "repair_plan_report": repair_plan_report_path},
        }

    def fake_artifact_coherence(_: CeoOpsOptions) -> dict[str, object]:
        calls.append("artifact-coherence")
        path = root / "artifact_coherence.yaml"
        return {"coherence": {"status": "fail"}, "paths": {"artifact_coherence": path}}

    monkeypatch.setattr(ceo_ops, "run_ceo_repair_plan", fake_repair_plan)
    monkeypatch.setattr(ceo_ops, "run_ceo_artifact_coherence", fake_artifact_coherence)

    result = run_ceo_repair_apply(options, repair_key="blocker:stale_artifacts")

    apply_result = result["repair_apply"]
    assert calls == ["artifact-coherence"]
    assert apply_result["status"] == "diagnostic_refreshed"
    assert apply_result["action_attempted"] is True
    assert apply_result["action_executed"] is True
    assert apply_result["repair_closed"] is False
    assert apply_result["command_name"] == "artifact-coherence"


def test_ceo_repair_apply_runs_runnable_cli_with_bound_action_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    repair_plan_path = root / "repair_plan.yaml"
    repair_plan_report_path = root / "repair_plan.md"
    calls: list[tuple[bool, str, str | None]] = []
    plans = [
        {
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "repair_plan_ready",
            "top_repair": "blocker:research_infra_patch",
            "repair_items": [
                {
                    "repair_key": "blocker:research_infra_patch",
                    "source": "blocker_stack",
                    "severity": "high",
                    "command_kind": "runnable_cli",
                    "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo patch-research-infra --run-id ceo_test --apply",
                    "requires_manual_gate": False,
                    "needs_implementation": False,
                    "diagnostic_only": False,
                    "closure_condition": "research infra patch executed",
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
        {
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "no_repairs_required",
            "top_repair": "",
            "repair_items": [],
            "production_effect": "none",
        },
    ]

    def fake_repair_plan(_: CeoOpsOptions) -> dict[str, object]:
        plan = plans.pop(0) if plans else plans[-1]
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "repair_plan": plan,
            "paths": {"repair_plan": repair_plan_path, "repair_plan_report": repair_plan_report_path},
        }

    def fake_patch_research_infra(patched_options: CeoOpsOptions) -> dict[str, object]:
        calls.append((patched_options.apply, patched_options.ceo_context, patched_options.ceo_authorized_action))
        return {"paths": {"infra_delta": root / "infra_delta.yaml"}}

    monkeypatch.setattr(ceo_ops, "run_ceo_repair_plan", fake_repair_plan)
    monkeypatch.setattr(ceo_ops, "run_ceo_patch_research_infra", fake_patch_research_infra)

    result = run_ceo_repair_apply(options, repair_key="blocker:research_infra_patch")

    apply_result = result["repair_apply"]
    assert calls == [(True, "bound_dispatch", "patch-research-infra")]
    assert apply_result["status"] == "repair_closed"
    assert apply_result["action_executed"] is True
    assert apply_result["repair_closed"] is True
    assert apply_result["command_name"] == "patch-research-infra"
    assert Path(apply_result["paths"]["before_repair_plan_snapshot"]).parent.name == "repair_apply_plans"
    assert Path(apply_result["paths"]["after_repair_plan_snapshot"]).exists()
    assert apply_result["before_repair_plan_snapshot_sha256"] == _sha256(Path(apply_result["paths"]["before_repair_plan_snapshot"]))
    assert apply_result["after_repair_plan_snapshot_sha256"] == _sha256(Path(apply_result["paths"]["after_repair_plan_snapshot"]))
    ledger_entry = json.loads(result["paths"]["repair_apply_ledger"].read_text(encoding="utf-8").strip())
    assert ledger_entry["paths"]["before_repair_plan_snapshot"] == apply_result["paths"]["before_repair_plan_snapshot"]
    assert ledger_entry["before_repair_plan_snapshot_sha256"] == apply_result["before_repair_plan_snapshot_sha256"]


def test_ceo_repair_apply_marks_closed_when_after_plan_clears_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    repair_plan_path = root / "repair_plan.yaml"
    repair_plan_report_path = root / "repair_plan.md"
    plans = [
        {
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "repair_plan_ready",
            "top_repair": "blocker:stale_artifacts",
            "repair_items": [
                {
                    "repair_key": "blocker:stale_artifacts",
                    "source": "blocker_stack",
                    "severity": "high",
                    "command_kind": "diagnostic_refresh",
                    "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id ceo_test",
                    "requires_manual_gate": False,
                    "needs_implementation": False,
                    "diagnostic_only": True,
                    "closure_condition": "artifact coherence passes",
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
        {
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "no_repairs_required",
            "top_repair": "",
            "repair_items": [],
            "production_effect": "none",
        },
    ]

    def fake_repair_plan(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "repair_plan": plans.pop(0),
            "paths": {"repair_plan": repair_plan_path, "repair_plan_report": repair_plan_report_path},
        }

    def fake_artifact_coherence(_: CeoOpsOptions) -> dict[str, object]:
        path = root / "artifact_coherence.yaml"
        return {"coherence": {"status": "pass"}, "paths": {"artifact_coherence": path}}

    monkeypatch.setattr(ceo_ops, "run_ceo_repair_plan", fake_repair_plan)
    monkeypatch.setattr(ceo_ops, "run_ceo_artifact_coherence", fake_artifact_coherence)

    result = run_ceo_repair_apply(options, repair_key="blocker:stale_artifacts")

    apply_result = result["repair_apply"]
    assert apply_result["status"] == "repair_closed"
    assert apply_result["action_executed"] is True
    assert apply_result["repair_closed"] is True
    assert apply_result["after_plan_status"] == "no_repairs_required"
    ledger_entries = result["paths"]["repair_apply_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger_entries) == 1
    assert json.loads(ledger_entries[0])["status"] == "repair_closed"


@pytest.mark.parametrize("after_kind", ["manual_gate", "implementation_required"])
def test_ceo_repair_apply_does_not_close_same_key_reclassified_to_blocker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    after_kind: str,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    repair_plan_path = root / "repair_plan.yaml"
    repair_plan_report_path = root / "repair_plan.md"
    plans = [
        {
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "repair_plan_ready",
            "top_repair": "blocker:stale_artifacts",
            "repair_items": [
                {
                    "repair_key": "blocker:stale_artifacts",
                    "source": "blocker_stack",
                    "severity": "high",
                    "command_kind": "diagnostic_refresh",
                    "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id ceo_test",
                    "requires_manual_gate": False,
                    "needs_implementation": False,
                    "diagnostic_only": True,
                    "closure_condition": "artifact coherence passes",
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
        {
            "model": "riskflow_ceo_repair_plan_v0",
            "status": "manual_gate_first" if after_kind == "manual_gate" else "implementation_repair_required",
            "top_repair": "blocker:stale_artifacts",
            "repair_items": [
                {
                    "repair_key": "blocker:stale_artifacts",
                    "source": "blocker_stack",
                    "severity": "high",
                    "command_kind": after_kind,
                    "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test"
                    if after_kind == "manual_gate"
                    else "",
                    "requires_manual_gate": after_kind == "manual_gate",
                    "needs_implementation": after_kind == "implementation_required",
                    "diagnostic_only": False,
                    "closure_condition": "same key still open",
                    "production_effect": "none",
                }
            ],
            "production_effect": "none",
        },
    ]

    def fake_repair_plan(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "repair_plan": plans.pop(0),
            "paths": {"repair_plan": repair_plan_path, "repair_plan_report": repair_plan_report_path},
        }

    def fake_artifact_coherence(_: CeoOpsOptions) -> dict[str, object]:
        path = root / "artifact_coherence.yaml"
        return {"coherence": {"status": "fail"}, "paths": {"artifact_coherence": path}}

    monkeypatch.setattr(ceo_ops, "run_ceo_repair_plan", fake_repair_plan)
    monkeypatch.setattr(ceo_ops, "run_ceo_artifact_coherence", fake_artifact_coherence)

    result = run_ceo_repair_apply(options, repair_key="blocker:stale_artifacts")

    apply_result = result["repair_apply"]
    assert apply_result["status"] == "repair_reclassified_not_closed"
    assert apply_result["action_executed"] is True
    assert apply_result["repair_closed"] is False
    assert apply_result["after_repair_kind"] == after_kind
    assert after_kind in apply_result["reason"]


def test_ceo_repair_apply_blocks_unsupported_yaml_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    repair_plan_path = root / "repair_plan.yaml"
    repair_plan_report_path = root / "repair_plan.md"
    plan = {
        "model": "riskflow_ceo_repair_plan_v0",
        "status": "repair_plan_ready",
        "top_repair": "blocker:unsafe",
        "repair_items": [
            {
                "repair_key": "blocker:unsafe",
                "source": "blocker_stack",
                "severity": "high",
                "command_kind": "runnable_cli",
                "recommended_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
                "requires_manual_gate": False,
                "needs_implementation": False,
                "closure_condition": "unsafe closes",
                "production_effect": "none",
            }
        ],
        "production_effect": "none",
    }

    def fake_repair_plan(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "repair_plan": plan,
            "paths": {"repair_plan": repair_plan_path, "repair_plan_report": repair_plan_report_path},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_repair_plan", fake_repair_plan)

    result = run_ceo_repair_apply(options, repair_key="blocker:unsafe")

    apply_result = result["repair_apply"]
    assert apply_result["status"] == "blocked_unsupported_command"
    assert apply_result["action_attempted"] is True
    assert apply_result["action_executed"] is False
    assert "unsupported CEO command" in apply_result["reason"]


def test_ceo_cli_repair_apply_dispatches_with_repair_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repair_apply_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "repair_apply.yaml"
    repair_apply_report_path = tmp_path / "reports" / "ceo_runs" / "ceo_test" / "repair_apply.md"
    calls: list[tuple[bool, str]] = []

    def fake_repair_apply(options: CeoOpsOptions, *, repair_key: str) -> dict[str, object]:
        calls.append((options.apply, repair_key))
        return {
            "repair_apply": {
                "status": "diagnostic_refreshed",
                "repair_key": repair_key,
                "command_kind": "diagnostic_refresh",
                "action_attempted": True,
                "action_executed": True,
                "repair_closed": False,
                "reason": "refreshed",
            },
            "paths": {"repair_apply": repair_apply_path, "repair_apply_report": repair_apply_report_path},
        }

    monkeypatch.setattr(cli, "run_ceo_repair_apply", fake_repair_apply)

    status = cli.ceo_command(
        SimpleNamespace(
            ceo_action="repair-apply",
            run_id="ceo_test",
            lab_run_id="ceo_test_lab",
            source_root=tmp_path,
            ceo_report_root=tmp_path / "reports" / "ceo_runs",
            ops_report_root=tmp_path / "reports" / "lab_ops",
            ops_runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
            repair_key="blocker:stale_artifacts",
            apply=True,
        )
    )

    assert status == 0
    assert calls == [(True, "blocker:stale_artifacts")]


def test_ceo_action_board_prioritizes_manual_gate_over_safe_dispatch(tmp_path: Path) -> None:
    board = ceo_ops.build_ceo_action_board(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        resumption_brief={
            "resume_status": "safe_for_one_bound_action",
            "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
            "rationale": "clean gates",
            "authorized_strategic_route": "run_champion_challenger",
            "authorized_route_source": "action_contract",
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
    assert board["counts"]["runnable_repairs"] == 0
    assert board["counts"]["blocked_actions"] == 1
    blocked = board["blocked_actions"][0]
    assert blocked["action_id"] == "resumption_brief_next_command"
    assert blocked["can_execute_now"] is False
    assert blocked["blocked_by_runtime_authority"] == "manual_gate_required"
    assert blocked["runtime_blocked"] is True
    assert blocked["authorized_strategic_route"] == "run_champion_challenger"
    assert blocked["authorized_route_source"] == "action_contract"
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
        executive_kpis={"model": "riskflow_ceo_executive_kpis_v0", "status": "operating_clear", "next_action": "defer_to_runtime_authority_surface"},
    )

    assert board["status"] == "no_action_available"
    assert board["primary_action"]["action_id"] == "regenerate_action_board"
    assert board["counts"]["runnable_repairs"] == 0
    assert board["counts"]["blocked_actions"] == 1


def test_ceo_action_board_rechecks_live_stop_before_using_reused_safe_artifacts(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "stop.request").write_text("user_requested\n", encoding="utf-8")
    resumption_path = root / "resumption_brief.yaml"
    repair_path = root / "repair_plan.yaml"
    receipt_path = root / "dispatch_receipt.yaml"
    kpi_path = root / "executive_kpis.yaml"

    result = run_ceo_action_board(
        options,
        resumption_result={
            "brief": {
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "resume_status": "safe_for_one_bound_action",
                "next_command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
                "authorized_strategic_route": "run_champion_challenger",
                "authorized_route_source": "action_contract",
                "rationale": "stale safe artifact",
            },
            "paths": {"resumption_brief": resumption_path, "resumption_brief_report": root / "resumption_brief.md"},
        },
        repair_result={
            "repair_plan": {
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "no_repairs_required",
                "repair_items": [],
            },
            "paths": {"repair_plan": repair_path, "repair_plan_report": root / "repair_plan.md"},
        },
        dispatch_result={
            "receipt": {
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "dispatch_allowed",
                "safe_to_dispatch": True,
            },
            "paths": {
                "dispatch_receipt": receipt_path,
                "dispatch_receipt_report": root / "dispatch_receipt.md",
                "dispatch_receipt_snapshot": root / "dispatch_receipts" / "safe.yaml",
            },
        },
        kpi_result={
            "kpis": {
                "run_id": "ceo_test",
                "lab_run_id": "ceo_test_lab",
                "status": "operating_clear",
                "next_action": "defer_to_runtime_authority_surface",
            },
            "paths": {"executive_kpis": kpi_path, "executive_kpis_report": root / "executive_kpis.md"},
        },
    )

    board = result["action_board"]
    assert board["status"] == "diagnostic_refresh_recommended"
    assert board["primary_action"]["command_kind"] == "diagnostic_refresh"
    assert board["primary_action"]["can_execute_now"] is False
    assert board["trust_snapshot"]["resumption_status"] == "blocked_stop_requested"
    assert board["trust_snapshot"]["dispatch_safe_to_dispatch"] is False


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
        action_result = {
            "model": "riskflow_ceo_binding_action_result_v0",
            "decision": "run_champion_challenger",
            "action_taken": "champion_challenger",
            "status": "shadow_comparison_complete",
            "production_effect": "none",
        }
        binding_path.write_text(yaml.safe_dump(action_result), encoding="utf-8")
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "action_result": action_result,
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
    assert step["before_primary_action_id"] == "resumption_brief_next_command"
    assert step["before_primary_command"].endswith("execute-next --run-id ceo_test --apply")
    assert result["paths"]["before_action_board_snapshot"].exists()
    assert result["paths"]["after_action_board_snapshot"].exists()
    assert step["before_action_board_snapshot_sha256"] == _sha256(result["paths"]["before_action_board_snapshot"])
    assert step["after_action_board_snapshot_sha256"] == _sha256(result["paths"]["after_action_board_snapshot"])
    assert step["binding_action_result_sha256"] == _sha256(binding_path)
    assert result["paths"]["operator_step"].exists()
    assert result["paths"]["operator_step_ledger"].exists()
    ledger_rows = result["paths"]["operator_step_ledger"].read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger_rows) == 1
    ledger_entry = json.loads(ledger_rows[0])
    assert ledger_entry["before_action_board_snapshot_sha256"] == step["before_action_board_snapshot_sha256"]
    assert ledger_entry["after_action_board_snapshot_sha256"] == step["after_action_board_snapshot_sha256"]
    assert ledger_entry["paths"]["before_action_board_snapshot"] == str(result["paths"]["before_action_board_snapshot"])
    replay = ceo_ops.build_ceo_replay(ceo_run_id="ceo_test", lab_run_id="ceo_test_lab", root=root)
    assert replay["operator_step_count"] == 1
    assert replay["operator_step_status"] == "pass"
    assert replay["operator_step_checks"][0]["status"] == "pass"


@pytest.mark.parametrize(
    ("execution_status", "meaningful_progress", "expected_step_status"),
    [
        ("manual_gate", False, "bounded_action_reached_manual_gate"),
        ("capability_gap", False, "bounded_action_reached_capability_gap"),
        ("noop_complete", False, "bounded_action_no_meaningful_progress"),
    ],
)
def test_ceo_operator_step_distinguishes_no_progress_execution_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    execution_status: str,
    meaningful_progress: bool,
    expected_step_status: str,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    board_path = root / "action_board.yaml"
    board_report_path = root / "action_board.md"
    binding_path = root / "binding_action_result.yaml"
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
            "primary_action": {"action_id": "refresh", "command_kind": "diagnostic_refresh"},
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

    def fake_execute_next(_: CeoOpsOptions) -> dict[str, object]:
        return {
            "run_id": "ceo_test",
            "lab_run_id": "ceo_test_lab",
            "action_result": {
                "model": "riskflow_ceo_binding_action_result_v0",
                "decision": "test_decision",
                "action_taken": "test_action",
                "status": execution_status,
                "meaningful_progress": meaningful_progress,
                "production_effect": "none",
            },
            "paths": {"binding_action_result": binding_path},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_action_board", fake_action_board)
    monkeypatch.setattr(ceo_ops, "run_ceo_execute_next", fake_execute_next)

    result = run_ceo_operator_step(options)

    step = result["operator_step"]
    assert step["status"] == expected_step_status
    assert step["action_attempted"] is True
    assert step["action_executed"] is False
    assert step["execution_status"] == execution_status
    assert step["execution_meaningful_progress"] is False
    assert result["paths"]["before_action_board_snapshot"].exists()
    assert result["paths"]["after_action_board_snapshot"].exists()


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
    assert brief["current_situation"]["effective_operator_status"] == "manual_gate_required"
    assert brief["current_situation"]["manual_gate_active"] is True
    assert brief["current_situation"]["effective_operator_runtime_blocked"] is True
    assert brief["current_situation"]["effective_operator_runtime_block_reason"].startswith("manual_gate_required:")
    assert brief["current_situation"]["trace_grade_status"] in {"fail", "warn", "pass"}
    assert brief["trace_health"]["status"] == brief["current_situation"]["trace_grade_status"]
    assert "recommended_next_action" in brief["trace_health"]
    assert brief["current_situation"]["primary_kind"] == "manual_gate"
    assert brief["approval_work"]["status"] == "pending_approvals"
    assert brief["approval_work"]["pending_count"] == 1
    assert brief["approval_work"]["top_pending_approval_id"] == "clear_stop_request"
    assert brief["approval_work"]["approval_record_command"].endswith(
        "approval-record --run-id ceo_test --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed"
    )
    assert brief["approval_work"]["approval_apply_command"].endswith(
        "approval-apply --run-id ceo_test --approval-id clear_stop_request --user-confirmed --apply"
    )
    assert brief["specialist_work"]["status"] == "pending_role_tasks"
    assert brief["specialist_work"]["pending_task_count"] >= 1
    assert "completed_task_count" in brief["specialist_work"]
    assert "blocked_task_count" in brief["specialist_work"]
    assert brief["specialist_work"]["top_pending_task_id"] == "approval_clear_stop_request"
    assert brief["specialist_work"]["top_pending_role_id"] == "risk_officer"
    assert brief["specialist_work"]["top_pending_packet_path"].endswith("approval_clear_stop_request.md")
    assert brief["specialist_work"]["top_pending_result_resolution_mode"] == "manual_gate_blocked_record"
    assert brief["specialist_work"]["top_pending_requires_manual_gate"] is True
    assert brief["specialist_work"]["top_pending_closure_command"].endswith(
        "approval-record --run-id ceo_test --approval-id clear_stop_request --decision <approved|rejected> --user-confirmed"
    )
    assert brief["specialist_work"]["top_autonomous_pending_task_id"]
    assert brief["specialist_work"]["top_autonomous_pending_task_id"] != "approval_clear_stop_request"
    assert brief["specialist_work"]["top_autonomous_pending_role_id"] in {"data_steward", "research_director", "validation_referee"}
    assert "role_dispatch_packets/" in brief["specialist_work"]["top_autonomous_pending_packet_path"]
    assert "--task-id approval_clear_stop_request" in brief["specialist_work"]["next_role_result_command"]
    assert "--status blocked" in brief["specialist_work"]["next_role_result_command"]
    assert "approval" in brief["refused_actions"][0]
    assert brief["product_language_allowed"] is False
    assert brief["production_effect"] == "none"
    report = result["paths"]["operator_brief_report"].read_text(encoding="utf-8")
    assert "Plain English" in report
    assert "effective_operator_status" in report
    assert "manual_gate_active" in report
    assert "Approval Work" in report
    assert "Trace Health" in report
    assert "Manual data import required" in report
    assert "approval-record --run-id ceo_test --approval-id clear_stop_request" in report
    assert "Specialist Work" in report
    assert "Completed:" in report
    assert "Blocked:" in report
    assert "Top autonomous task" in report
    assert "approval_clear_stop_request" in report
    assert "Refused Actions" in report
    assert "Production effect: none." in report


def test_ceo_operator_brief_uses_final_refreshed_action_board(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    stale_board = {
        "model": "riskflow_ceo_action_board_v0",
        "status": "bounded_action_available",
        "primary_action": {
            "action_id": "resumption_brief_next_command",
            "command_kind": "bounded_dispatch",
            "can_execute_now": True,
            "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
        },
        "production_effect": "none",
    }
    final_board = {
        "model": "riskflow_ceo_action_board_v0",
        "status": "manual_gate_required",
        "primary_action": {
            "action_id": "blocker:stop_requested",
            "command_kind": "manual_gate",
            "can_execute_now": False,
            "requires_manual_gate": True,
            "command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
        },
        "production_effect": "none",
    }
    final_quality = {
        "model": "riskflow_ceo_decision_quality_v0",
        "status": "decision_quality_written",
        "selected_action": "run_frozen_candidate_validation",
        "selected_rationale": "manual gate outranks the strategic route",
        "effective_runtime_action": "blocker:stop_requested",
        "effective_runtime_command_kind": "manual_gate",
        "effective_runtime_can_execute_now": False,
        "runtime_blocked": True,
        "runtime_block_reason": "manual_gate_required:blocker:stop_requested",
        "runtime_authority_status": "manual_gate_required",
        "executable_next_action": "blocker:stop_requested",
        "executable_next_command_kind": "manual_gate",
        "selected_action_is_executable_now": False,
        "selected_action_blocked_by": "manual_gate_required:blocker:stop_requested",
        "production_effect": "none",
    }

    def fake_status(_options: CeoOpsOptions) -> dict[str, object]:
        return {"company_status": {"lab_status": {"status": "stopped", "stop_reason": "user_requested"}}}

    def fake_action_board(_options: CeoOpsOptions) -> dict[str, object]:
        path = root / "action_board.yaml"
        path.write_text(yaml.safe_dump(stale_board), encoding="utf-8")
        return {"action_board": stale_board, "paths": {"action_board": path, "action_board_report": root / "action_board.md"}}

    def fake_decision_quality(
        _options: CeoOpsOptions,
        *,
        action_board_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        board_path = root / "action_board.yaml"
        quality_path = root / "decision_quality.yaml"
        board_path.write_text(yaml.safe_dump(final_board), encoding="utf-8")
        quality_path.write_text(yaml.safe_dump(final_quality), encoding="utf-8")
        return {
            "decision_quality": final_quality,
            "paths": {"decision_quality": quality_path, "decision_quality_report": root / "decision_quality.md"},
        }

    def fake_approval_queue(_options: CeoOpsOptions) -> dict[str, object]:
        return {
            "queue": {"status": "pending_approvals", "pending_count": 1},
            "paths": {"queue": root / "approval_queue.yaml", "approval_status": root / "approval_status.yaml"},
        }

    def fake_role_queue(_options: CeoOpsOptions) -> dict[str, object]:
        return {"queue": {"status": "pending_role_tasks", "pending_task_count": 1}, "paths": {"role_task_queue": root / "role_task_queue.yaml"}}

    monkeypatch.setattr(ceo_ops, "run_ceo_status", fake_status)
    monkeypatch.setattr(ceo_ops, "run_ceo_action_board", fake_action_board)
    monkeypatch.setattr(ceo_ops, "run_ceo_decision_quality", fake_decision_quality)
    monkeypatch.setattr(ceo_ops, "run_ceo_approval_queue", fake_approval_queue)
    monkeypatch.setattr(ceo_ops, "run_ceo_role_queue", fake_role_queue)

    result = run_ceo_operator_brief(options)

    brief = result["operator_brief"]
    assert brief["status"] == "waiting_on_manual_gate"
    assert brief["current_situation"]["primary_action"] == "blocker:stop_requested"
    assert brief["current_situation"]["decision_quality_effective_runtime_action"] == "blocker:stop_requested"


def test_ceo_eval_fixtures_cover_transition_policy(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)

    result = run_ceo_eval_fixtures(options)

    fixtures = result["fixtures"]
    cases = {item["case_id"]: item for item in fixtures["cases"]}
    assert fixtures["status"] == "pass"
    assert cases["champion_challenger_routes_to_fresh_control"]["observed_transition_status"] == "pass"
    assert cases["champion_challenger_does_not_jump_to_generic_research"]["observed_transition_status"] == "fail"
    assert cases["approval_wait_routes_to_approval_apply"]["observed_transition_status"] == "pass"
    assert cases["approval_apply_rejects_stale_approval_record"]["observed_status"] == "blocked_stale_approval_record"
    assert cases["approval_apply_rejects_stale_approval_record"]["stop_files_preserved"] is True
    assert cases["contract_repair_routes_back_to_frozen_candidate_validation"]["observed_transition_status"] == "pass"
    assert "stop_requested" in cases["preflight_blocks_stop_request"]["observed_blockers"]
    assert "true_blocker" in cases["preflight_blocks_true_blocker"]["observed_blockers"]
    assert cases["computed_hard_memory_delta_blocks_dispatch"]["observed_blocks"] is True
    assert cases["computed_soft_memory_delta_does_not_block_dispatch"]["observed_blocks"] is False
    assert "requires --apply" in cases["withheld_split_manifest_requires_apply"]["observed_error"]
    assert "requires --apply" in cases["fresh_withheld_snapshot_manifest_requires_apply"]["observed_error"]
    assert "requires --apply" in cases["fresh_withheld_snapshot_declare_requires_apply"]["observed_error"]
    stale_fixture_run_id = cases["approval_apply_rejects_stale_approval_record"]["fixture_run_id"]
    stale_fixture_path = options.report_root / stale_fixture_run_id / "ceo_eval_fixtures.yaml"
    stale_nested_fixtures = yaml.safe_load(stale_fixture_path.read_text(encoding="utf-8"))
    assert stale_nested_fixtures["run_id"] == stale_fixture_run_id
    assert stale_nested_fixtures["skipped_reason"] == "nested_eval_fixture_run"
    assert stale_nested_fixtures["case_count"] == 0
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


def test_ceo_guardrail_audit_scans_nested_trust_snapshots(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    receipt_dir = root / "dispatch_receipts"
    board_dir = root / "operator_step_boards"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    board_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / "receipt_001.yaml").write_text(
        yaml.safe_dump({"model": "receipt", "production_effect": "changed_alerts", "product_language_allowed": False}),
        encoding="utf-8",
    )
    (board_dir / "after_board.yaml").write_text(
        yaml.safe_dump({"model": "board", "production_effect": "none", "product_language_allowed": True}),
        encoding="utf-8",
    )

    result = run_ceo_guardrail_audit(options)

    audit = result["guardrail_audit"]
    violations = {(item["artifact"], item["violation"]) for item in audit["violations"]}
    assert audit["status"] == "fail"
    assert ("dispatch_receipts/receipt_001.yaml", "non_none_production_effect") in violations
    assert ("operator_step_boards/after_board.yaml", "product_language_allowed_true") in violations
    assert any(item["artifact"] == "dispatch_receipts/receipt_001.yaml" for item in audit["scanned_artifacts"])


def test_ceo_guardrail_audit_recurses_nested_payloads_and_jsonl(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    root = options.report_root / "ceo_test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "nested_artifact.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "nested",
                "production_effect": "none",
                "snapshots": [
                    {
                        "candidate": "unsafe_translation",
                        "product_language_allowed": True,
                        "promotion_authority": "autonomous",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "action_ledger.jsonl").write_text(
        json.dumps(
            {
                "event": "unsafe_receipt",
                "payload": {"production_effect": "changed_rankings", "product_language_allowed": False},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_ceo_guardrail_audit(options)

    audit = result["guardrail_audit"]
    violations = {(item["artifact"], item["violation"], item["path"]) for item in audit["violations"]}
    assert audit["status"] == "fail"
    assert ("nested_artifact.yaml", "product_language_allowed_true", "$.snapshots[0].product_language_allowed") in violations
    assert ("nested_artifact.yaml", "non_user_promotion_authority", "$.snapshots[0].promotion_authority") in violations
    assert (
        "action_ledger.jsonl",
        "non_none_production_effect",
        "$action_ledger.jsonl:1.payload.production_effect",
    ) in violations


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
    blockers = [item["blocker"] for item in action["preflight_blockers"]]
    assert "guardrail_audit_failed" in blockers
    assert action.get("action_executed") is not True
    assert result["paths"]["preflight_gate"].exists()
    assert result["paths"]["dispatch_receipt"].exists()
    receipt = yaml.safe_load(result["paths"]["dispatch_receipt"].read_text(encoding="utf-8"))
    assert receipt["model"] == "riskflow_ceo_dispatch_receipt_v0"
    assert receipt["status"] == "dispatch_blocked"
    assert receipt["safe_to_dispatch"] is False
    assert receipt["decision"] == action["decision"]
    assert "guardrail_audit_failed" in receipt["preflight_blockers"]
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
        trace_grade={
            "verdict": "pass",
            "score": 91,
            "recommended_next_action": "continue_with_one_bound_ceo_action",
            "issues": [],
            "criteria": {"manual_data_import_required": False},
        },
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
    assert gate["source_status"]["trace_verdict"] == "pass"
    assert gate["source_status"]["trace_score"] == 91
    assert gate["source_status"]["trace_recommended_next_action"] == "continue_with_one_bound_ceo_action"
    assert gate["source_status"]["trace_issues"] == []
    assert gate["source_status"]["trace_manual_data_import_required"] is False


def test_ceo_preflight_source_status_infers_legacy_manual_data_issue() -> None:
    gate = ceo_ops.build_ceo_preflight_gate(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        stop_requested=False,
        true_blocker=False,
        trace_grade={
            "verdict": "fail",
            "score": 55,
            "recommended_next_action": "stop_for_manual_data_import",
            "issues": ["manual_data_import_required"],
        },
        approval_queue={"pending_count": 0},
        replay={"status": "replayable"},
        eval_suite={"status": "pass"},
        guardrail_audit={"status": "pass"},
        memory_delta={"status": "no_memory_delta_required", "memory_delta_required": False, "note_applied": False},
        heartbeat_budget={"status": "within_time_budget", "budget_elapsed": False},
    )

    assert gate["status"] == "blocked"
    assert gate["source_status"]["trace_manual_data_import_required"] is True
    assert gate["source_status"]["trace_recommended_next_action"] == "stop_for_manual_data_import"
    report = ceo_ops.render_ceo_preflight_gate(gate)
    assert "## Source Status" in report
    assert "Trace score: 55" in report
    assert "Trace recommended next action: stop_for_manual_data_import" in report
    assert "Trace manual data import required: True" in report
    assert "Trace issues: ['manual_data_import_required']" in report


def test_ceo_preflight_blocks_failed_artifact_coherence() -> None:
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
        artifact_coherence={
            "status": "fail",
            "latest_action_generated_at": "2026-06-06T00:00:00+00:00",
            "latest_action_has_current_transition_evidence": True,
            "issues": [{"artifact": "dispatch_receipt", "issues": ["dispatch_receipt_decision_mismatch"]}],
        },
        memory_delta={"status": "no_memory_delta_required", "memory_delta_required": False, "note_applied": False},
        heartbeat_budget={"status": "within_time_budget", "budget_elapsed": False},
    )

    blockers = [item["blocker"] for item in gate["blockers"]]
    assert gate["status"] == "blocked"
    assert gate["safe_to_execute"] is False
    assert "artifact_coherence_failed" in blockers
    assert "artifact_coherence" in gate["blocker_categories"]
    assert gate["source_status"]["artifact_coherence_status"] == "fail"


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
    (root / "memory_delta.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_memory_delta_v0",
                "status": "memory_delta_required",
                "memory_delta_required": True,
                "note_applied": True,
                "computed_for_enforced_preflight": True,
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
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


def test_ceo_single_manual_data_gate_blocks_resumption_and_action_board(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    action_result = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-05T00:00:02Z",
        "decision": "import_or_curate_fresh_ohlcv_data",
        "action_taken": "blocked_manual_data_import_required",
        "status": "manual_gate",
        "meaningful_progress": False,
        "next_allowed_actions": ["request_fresh_data"],
        "production_effect": "none",
    }
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(action_result), encoding="utf-8")
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
    (root / "ceo_action_ledger.jsonl").write_text(json.dumps(action_result, sort_keys=True) + "\n", encoding="utf-8")

    trace = run_ceo_trace_grade(options)["grade"]
    assert trace["verdict"] == "fail"
    assert trace["criteria"]["manual_data_import_required"] is True
    assert trace["recommended_next_action"] == "stop_for_manual_data_import"
    assert "manual_data_import_required" in trace["issues"]

    preflight = run_ceo_preflight_gate(options, enforce_memory_delta=True)["preflight_gate"]
    blockers = [item["blocker"] for item in preflight["blockers"]]
    assert preflight["safe_to_execute"] is False
    assert "trace_grade_failed" in blockers

    resumption = run_ceo_resumption_brief(options)["brief"]
    assert resumption["resume_status"] == "blocked_preflight"
    assert "execute-next" not in resumption["next_command"]

    action_board = run_ceo_action_board(options)["action_board"]
    assert action_board["status"] != "bounded_action_available"
    assert (action_board.get("primary_action", {}) or {}).get("can_execute_now") is not True

    decision_quality = run_ceo_decision_quality(options)["decision_quality"]
    assert decision_quality["selected_action_is_executable_now"] is False
    assert decision_quality["effective_runtime_can_execute_now"] is not True


def test_ceo_manual_data_import_next_action_blocks_before_first_manual_gate_result(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    action_result = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-05T00:00:02Z",
        "decision": "request_fresh_data",
        "action_taken": "fresh_data_preflight",
        "status": "blocked_missing_fresh_data",
        "meaningful_progress": False,
        "next_allowed_actions": ["import_or_curate_fresh_ohlcv_data"],
        "production_effect": "none",
    }
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(action_result), encoding="utf-8")
    (root / "action_contract.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_action_contract_v0",
                "decision": "request_fresh_data",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )
    (root / "ceo_action_ledger.jsonl").write_text(json.dumps(action_result, sort_keys=True) + "\n", encoding="utf-8")

    trace = run_ceo_trace_grade(options)["grade"]
    assert trace["verdict"] == "fail"
    assert trace["criteria"]["manual_data_import_required"] is True
    assert trace["manual_next_actions"] == ["import_or_curate_fresh_ohlcv_data"]
    assert trace["recommended_next_action"] == "stop_for_manual_data_import"
    assert "manual_data_import_required" in trace["issues"]

    preflight = run_ceo_preflight_gate(options, enforce_memory_delta=True)["preflight_gate"]
    blockers = [item["blocker"] for item in preflight["blockers"]]
    assert preflight["safe_to_execute"] is False
    assert "trace_grade_failed" in blockers

    resumption = run_ceo_resumption_brief(options)["brief"]
    assert resumption["resume_status"] == "blocked_preflight"
    assert "execute-next" not in resumption["next_command"]


def test_ceo_execute_next_manual_data_import_writes_blocked_receipt_even_if_preflight_is_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    root = options.report_root / "ceo_test"
    previous_action = {
        "model": "riskflow_ceo_binding_action_result_v0",
        "generated_at": "2026-06-05T00:00:02Z",
        "decision": "request_fresh_data",
        "action_taken": "fresh_data_preflight",
        "status": "blocked_missing_fresh_data",
        "meaningful_progress": False,
        "next_allowed_actions": ["import_or_curate_fresh_ohlcv_data"],
        "production_effect": "none",
    }
    (root / "binding_action_result.yaml").write_text(yaml.safe_dump(previous_action), encoding="utf-8")
    (root / "ceo_self_audit.yaml").write_text(
        yaml.safe_dump({"model": "riskflow_ceo_self_audit_v0", "production_effect": "none"}),
        encoding="utf-8",
    )

    def stale_passing_preflight(_options: CeoOpsOptions, *, enforce_memory_delta: bool = False) -> dict[str, object]:
        return {
            "preflight_gate": {
                "model": "riskflow_ceo_preflight_gate_v0",
                "status": "pass",
                "safe_to_execute": True,
                "blockers": [],
                "production_effect": "none",
            },
            "paths": {},
        }

    monkeypatch.setattr(ceo_ops, "run_ceo_preflight_gate", stale_passing_preflight)

    result = run_ceo_execute_next(options)

    assert result["action_result"]["decision"] == "import_or_curate_fresh_ohlcv_data"
    assert result["action_result"]["action_taken"] == "blocked_manual_data_import_required"
    assert result["action_result"]["status"] == "manual_gate"
    receipt = yaml.safe_load(result["paths"]["dispatch_receipt"].read_text(encoding="utf-8"))
    assert receipt["status"] == "dispatch_blocked"
    assert receipt["safe_to_dispatch"] is False
    assert receipt["reason"] == "manual OHLCV import or curation is required before fresh validation"


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
    assert "manual_data_import_required" in dashboard["trace_grade"]
    assert dashboard["safe_to_continue_scope"] == "flight_dashboard_only_not_dispatch_authority"
    assert dashboard["dispatch_authority"] == "not_granted_by_flight_dashboard"
    assert "ceo status" in dashboard["runtime_authority_note"]
    assert dashboard["product_delta"]["product_language_allowed"] is False
    assert dashboard["production_effect"] == "none"
    report = result["paths"]["dashboard_report"].read_text(encoding="utf-8")
    assert "Riskflow CEO Flight Dashboard" in report
    assert "Manual data import required" in report
    assert "Safety scope: flight_dashboard_only_not_dispatch_authority" in report
    assert "Dispatch authority: not_granted_by_flight_dashboard" in report
    assert "This dashboard summarizes CEO process state. It is not product validation." in report


def test_ceo_operating_dashboard_writes_portfolio_snapshot(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_execute_next(options)
    root = options.report_root / "ceo_test"
    (root / "role_task_queue.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_ceo_role_task_queue_v0",
                "status": "blocked_role_tasks",
                "task_count": 3,
                "pending_task_count": 0,
                "pending_manual_task_count": 0,
                "pending_autonomous_task_count": 0,
                "completed_task_count": 2,
                "blocked_task_count": 1,
                "top_blocked_task_id": "debt_candidate_a_visual_review_evidence",
                "top_blocked_role_id": "product_translator",
                "top_blocked_review_status": "accepted_blocked_result",
                "top_blocked_result_path": "reports/ceo_runs/ceo_test/specialist_results/debt_candidate_a_visual_review_evidence.yaml",
                "top_blocked_next_action": "complete_champion_challenger_visual_review",
                "top_blocked_finding": "Visual review evidence is missing.",
                "next_action": "complete_champion_challenger_visual_review",
                "production_effect": "none",
            }
        ),
        encoding="utf-8",
    )

    result = run_ceo_operating_dashboard(options)

    dashboard = result["dashboard"]
    assert dashboard["model"] == "riskflow_ceo_operating_dashboard_v0"
    assert dashboard["candidate_portfolio_count"] >= 1
    assert dashboard["capability_backlog_count"] >= 1
    assert dashboard["candidate_portfolio"][0]["production_effect"] == "none"
    assert dashboard["product_language_allowed"] is False
    assert dashboard["product_governance"]["product_language_allowed"] is False
    assert dashboard["safe_to_continue_scope"] == "flight_dashboard_only_not_dispatch_authority"
    assert dashboard["dispatch_authority"] == "not_granted_by_operating_dashboard"
    assert "recommended_next_action" in dashboard["trace"]
    assert "manual_data_import_required" in dashboard["trace"]
    assert dashboard["role_orchestration"]["status"] == "blocked_role_tasks"
    assert dashboard["role_orchestration"]["blocked_task_count"] == 1
    assert dashboard["role_orchestration"]["top_blocked_review_status"] == "accepted_blocked_result"
    assert dashboard["role_orchestration"]["top_blocked_finding"] == "Visual review evidence is missing."
    assert result["paths"]["dashboard"].exists()
    assert result["paths"]["dashboard_report"].exists()
    report = result["paths"]["dashboard_report"].read_text(encoding="utf-8")
    assert "Riskflow CEO Operating Dashboard" in report
    assert "Trace score" in report
    assert "Trace recommended next action" in report
    assert "Trace manual data import required" in report
    assert "Validation Gate" in report
    assert "Executive KPIs" in report
    assert "Role Orchestration" in report
    assert "Safety scope: flight_dashboard_only_not_dispatch_authority" in report
    assert "Dispatch authority: not_granted_by_operating_dashboard" in report
    assert "Top blocked review: accepted_blocked_result" in report
    assert "Top blocked finding: Visual review evidence is missing." in report


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


def test_ceo_capability_backlog_empty_defers_to_runtime_authority() -> None:
    backlog = ceo_ops.build_ceo_capability_backlog_artifact(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        backlog=[],
    )

    assert backlog["status"] == "empty"
    assert backlog["next_action"] == "defer_to_runtime_authority_surface"
    assert backlog["next_action"] != "continue_with_bound_action_dispatch"
    assert backlog["production_effect"] == "none"


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
    assert quality["runtime_authority_status"]
    assert quality["executable_next_action"]
    assert quality["selected_action_blocked_by"]
    assert alternatives["run_champion_challenger"]["selected"] is True
    assert alternatives["run_champion_challenger"]["evidence"]["candidate_count"] >= 1
    assert alternatives["broaden_hypothesis_source"]["why_not_selected"]
    assert quality["production_effect"] == "none"
    assert result["paths"]["decision_quality"].exists()
    report = result["paths"]["decision_quality_report"].read_text(encoding="utf-8")
    assert "Riskflow CEO Decision Quality" in report
    assert "Runtime Authority" in report
    assert "## Alternatives" in report
    assert "Production effect: none." in report


def test_ceo_decision_quality_separates_selected_route_from_manual_gate_authority(tmp_path: Path) -> None:
    options = _options(tmp_path, apply=True)
    _write_lab_artifacts(tmp_path, with_candidate=True)
    run_ceo_review(options)
    run_ceo_stop(options, reason="user_requested")

    result = run_ceo_decision_quality(options)

    quality = result["decision_quality"]
    assert quality["runtime_authority_status"] == "manual_gate_required"
    assert quality["effective_runtime_action"].startswith("blocker:")
    assert quality["effective_runtime_command_kind"] == "manual_gate"
    assert quality["effective_runtime_can_execute_now"] is False
    assert quality["runtime_blocked"] is True
    assert quality["runtime_block_reason"] == f"manual_gate_required:{quality['executable_next_action']}"
    assert quality["selected_strategic_route_advisory"] == quality["selected_action"]
    assert quality["executable_next_action"].startswith("blocker:")
    assert quality["executable_next_command_kind"] == "manual_gate"
    assert quality["executable_can_execute_now"] is False
    assert quality["selected_action_is_executable_now"] is False
    assert quality["selected_action_blocked_by"] == f"manual_gate_required:{quality['executable_next_action']}"
    assert "manual gate" in quality["selected_action_runtime_note"]
    report = result["paths"]["decision_quality_report"].read_text(encoding="utf-8")
    assert "Effective runtime action:" in report
    assert "Strategic Selection" in report
    assert f"Selected action blocked by: manual_gate_required:{quality['executable_next_action']}" in report


def test_ceo_decision_quality_treats_bounded_execute_next_wrapper_as_selected_route_authority() -> None:
    quality = ceo_ops.build_ceo_decision_quality(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        company_status={"lab_status": {"stop_reason": ""}, "governance": {"open_lanes": []}, "true_blocker": False},
        product_delta={"candidate_count": 1, "chart_facing_value_status": "shadow_product_candidate_pipeline"},
        infra_delta={"infra_delta_status": "clear"},
        decision={
            "decision": "run_champion_challenger",
            "rationale": "Candidates need base-vs-challenger evidence.",
            "production_effect": "none",
        },
        action_board={
            "status": "bounded_action_available",
            "autonomy_mode": "one_bounded_action_then_reaudit",
            "primary_action": {
                "action_id": "resumption_brief_next_command",
                "command_kind": "bounded_dispatch",
                "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
                "can_execute_now": True,
                "authorized_strategic_route": "run_champion_challenger",
                "authorized_route_source": "action_contract",
            },
        },
    )

    assert quality["runtime_authority_status"] == "bounded_action_available"
    assert quality["executable_next_action"] == "resumption_brief_next_command"
    assert quality["runtime_authorized_strategic_route"] == "run_champion_challenger"
    assert quality["effective_runtime_action"] == "resumption_brief_next_command"
    assert quality["effective_runtime_can_execute_now"] is True
    assert quality["runtime_blocked"] is False
    assert quality["selected_strategic_route_advisory"] == ""
    assert quality["selected_action_is_executable_now"] is True
    assert quality["selected_action_blocked_by"] == ""
    assert "bounded execute-next wrapper" in quality["selected_action_runtime_note"]


def test_ceo_decision_quality_does_not_self_authorize_bounded_execute_next_route() -> None:
    quality = ceo_ops.build_ceo_decision_quality(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        company_status={"lab_status": {"stop_reason": ""}, "governance": {"open_lanes": []}, "true_blocker": False},
        product_delta={"candidate_count": 1, "chart_facing_value_status": "shadow_product_candidate_pipeline"},
        infra_delta={"infra_delta_status": "clear"},
        decision={
            "decision": "run_champion_challenger",
            "rationale": "Candidates need base-vs-challenger evidence.",
            "production_effect": "none",
        },
        action_board={
            "status": "bounded_action_available",
            "autonomy_mode": "one_bounded_action_then_reaudit",
            "primary_action": {
                "action_id": "resumption_brief_next_command",
                "command_kind": "bounded_dispatch",
                "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
                "can_execute_now": True,
                "authorized_strategic_route": "run_fresh_withheld_validation_executor",
                "authorized_route_source": "action_contract",
            },
        },
    )

    assert quality["runtime_authority_status"] == "bounded_action_available"
    assert quality["runtime_authorized_strategic_route"] == "run_fresh_withheld_validation_executor"
    assert quality["selected_action_is_executable_now"] is False
    assert quality["selected_action_blocked_by"] == "different_executable_action:resumption_brief_next_command"


def test_ceo_decision_quality_rejects_malformed_bounded_wrapper_route() -> None:
    quality = ceo_ops.build_ceo_decision_quality(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        company_status={"lab_status": {"stop_reason": ""}, "governance": {"open_lanes": []}, "true_blocker": False},
        product_delta={"candidate_count": 1, "chart_facing_value_status": "shadow_product_candidate_pipeline"},
        infra_delta={"infra_delta_status": "clear"},
        decision={
            "decision": "run_champion_challenger",
            "rationale": "Candidates need base-vs-challenger evidence.",
            "production_effect": "none",
        },
        action_board={
            "status": "bounded_action_available",
            "autonomy_mode": "one_bounded_action_then_reaudit",
            "primary_action": {
                "action_id": "resumption_brief_next_command",
                "command_kind": "bounded_dispatch",
                "command": "PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id ceo_test",
                "can_execute_now": True,
                "authorized_strategic_route": "run_champion_challenger",
                "authorized_route_source": "action_contract",
            },
        },
    )

    assert quality["effective_runtime_can_execute_now"] is True
    assert quality["runtime_authorized_strategic_route"] == "run_champion_challenger"
    assert quality["selected_action_is_executable_now"] is False
    assert quality["selected_action_blocked_by"] == "different_executable_action:resumption_brief_next_command"


def test_ceo_decision_quality_manual_gate_status_overrides_stale_runnable_wrapper() -> None:
    quality = ceo_ops.build_ceo_decision_quality(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        company_status={"lab_status": {"stop_reason": ""}, "governance": {"open_lanes": []}, "true_blocker": False},
        product_delta={"candidate_count": 1, "chart_facing_value_status": "shadow_product_candidate_pipeline"},
        infra_delta={"infra_delta_status": "clear"},
        decision={
            "decision": "run_champion_challenger",
            "rationale": "Candidates need base-vs-challenger evidence.",
            "production_effect": "none",
        },
        action_board={
            "status": "manual_gate_required",
            "autonomy_mode": "manual_gate",
            "primary_action": {
                "action_id": "resumption_brief_next_command",
                "command_kind": "bounded_dispatch",
                "command": "PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id ceo_test --apply",
                "can_execute_now": True,
                "authorized_strategic_route": "run_champion_challenger",
                "authorized_route_source": "stale_action_contract",
            },
        },
    )

    assert quality["runtime_authority_status"] == "manual_gate_required"
    assert quality["effective_runtime_action"] == "resumption_brief_next_command"
    assert quality["effective_runtime_can_execute_now"] is False
    assert quality["runtime_blocked"] is True
    assert quality["runtime_block_reason"] == "manual_gate_required:resumption_brief_next_command"
    assert quality["executable_can_execute_now"] is False
    assert quality["selected_strategic_route_advisory"] == "run_champion_challenger"
    assert quality["selected_action_is_executable_now"] is False
    assert quality["selected_action_blocked_by"] == "manual_gate_required:resumption_brief_next_command"


@pytest.mark.parametrize(
    ("board_status", "primary_action", "command_kind", "primary_flags", "expected_blocker_prefix"),
    [
        (
            "diagnostic_refresh_recommended",
            "regenerate_action_board",
            "diagnostic_refresh",
            {"diagnostic_only": True},
            "diagnostic_refresh_required",
        ),
        (
            "implementation_repair_required",
            "repair:artifact_coherence_policy",
            "implementation_required",
            {"needs_implementation": True},
            "implementation_repair_required",
        ),
    ],
)
def test_ceo_decision_quality_names_non_executable_runtime_authority(
    board_status: str,
    primary_action: str,
    command_kind: str,
    primary_flags: dict[str, bool],
    expected_blocker_prefix: str,
) -> None:
    quality = ceo_ops.build_ceo_decision_quality(
        ceo_run_id="ceo_test",
        lab_run_id="ceo_test_lab",
        company_status={"lab_status": {"stop_reason": ""}, "governance": {"open_lanes": []}, "true_blocker": False},
        product_delta={"candidate_count": 1, "chart_facing_value_status": "shadow_product_candidate_pipeline"},
        infra_delta={"infra_delta_status": "clear"},
        decision={
            "decision": "run_champion_challenger",
            "rationale": "Candidates need base-vs-challenger evidence.",
            "production_effect": "none",
        },
        action_board={
            "status": board_status,
            "autonomy_mode": "test_mode",
            "primary_action": {
                "action_id": primary_action,
                "command_kind": command_kind,
                "command": "PYTHONPATH=src python3 -m riskflow ceo action-board --run-id ceo_test",
                "can_execute_now": False,
                **primary_flags,
            },
        },
    )

    assert quality["runtime_authority_status"] == board_status
    assert quality["executable_next_action"] == primary_action
    assert quality["selected_action_is_executable_now"] is False
    assert quality["selected_action_blocked_by"] == f"{expected_blocker_prefix}:{primary_action}"


def test_effective_operator_status_trusts_action_board_over_stale_executable_decision_quality() -> None:
    status = ceo_ops._effective_operator_status(
        action_board={
            "status": "diagnostic_refresh_recommended",
            "primary_action": {
                "action_id": "regenerate_action_board",
                "command_kind": "diagnostic_refresh",
                "can_execute_now": False,
            },
        },
        operator_brief={},
        decision_quality={
            "runtime_authority_status": "bounded_action_available",
            "effective_runtime_can_execute_now": True,
            "executable_can_execute_now": True,
            "runtime_blocked": False,
        },
    )

    assert status["effective_operator_status"] == "diagnostic_refresh_recommended"
    assert status["runtime_blocked"] is True
    assert status["runtime_block_reason"] == "diagnostic_refresh_recommended:regenerate_action_board"


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
    assert quality["runtime_authority_status"] == "unknown_action_board"
    assert quality["selected_action_blocked_by"] == "action_board_missing"
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
    assert result["paths"]["org_progress_score_report"].exists()
    assert result["paths"]["capability_backlog_report"].exists()
    assert result["paths"]["fresh_withheld_validation_contract_report"].exists()
    assert result["paths"]["promotion_proposal_report"].exists()
    assert result["paths"]["evidence_debt_register_report"].exists()
    report = result["paths"]["report"].read_text(encoding="utf-8")
    assert "CEO Operating Snapshot" in report
    assert "Portfolio allocator" in report
    assert "Portfolio action scope" in report
    assert "Portfolio dispatch authority" in report
    assert "Mission score" in report
    assert "Mission attention action" in report
    assert "Mission action scope" in report
    assert "Mission dispatch authority" in report
    assert "Strategy capital dashboard" in report
    assert "Strategy capital bucket" in report
    assert "Strategy capital action" in report
    assert "Strategy capital safety scope" in report
    assert "Strategy capital dispatch authority" in report
    assert "Runtime authority source" in report
    assert "Flight safety scope" in report
    assert "Flight dispatch authority" in report
    assert "Decision quality" in report
    assert "Decision quality effective runtime action" in report
    assert "Decision quality runtime blocked" in report
    assert "Decision quality selected strategic route advisory" in report
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
    assert "Repair apply" in report
    assert "Repair plan status" in report
    assert "Repair apply status" in report
    assert "Repair apply key" in report
    assert "Repair apply executed" in report
    assert "Repair apply closed" in report
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
    assert "Artifact coherence top issue" in report
    assert "Artifact coherence top issue severity" in report
    assert "Artifact coherence top issue types" in report
    assert "Effective operator status" in report
    assert "Manual gate active" in report
    assert "Effective operator runtime blocked" in report
    assert "Effective operator runtime block reason" in report
    assert "Resumption status" in report
    assert "Resumption next command" in report
    assert "Approval queue" in report
    assert "Executive KPIs" in report
    assert "Role task queue" in report
    assert "Role result validation" in report
    assert "Role result validation status" in report
    assert "Role result validation issues" in report
    assert "Role dispatch" in report
    assert "Pending approvals" in report
    assert "Approval top pending id" in report
    assert "Approval top pending kind" in report
    assert "Approval top pending reason" in report
    assert "Approval top pending source" in report
    assert "Approval top pending required user decision" in report
    assert "Approval top pending authority" in report
    assert "Approval top pending fingerprint" in report
    assert "Role queue status" in report
    assert "Role tasks" in report
    assert "Role pending" in report
    assert "Role pending manual" in report
    assert "Role pending autonomous" in report
    assert "Role completed" in report
    assert "Role blocked" in report
    assert "Role top pending task" in report
    assert "Role top pending result mode" in report
    assert "Role top pending closure command" in report
    assert "Role top autonomous pending task" in report
    assert "Role top autonomous result command" in report
    assert "Role top blocked task" in report
    assert "Role top blocked result mode" in report
    assert "Role top blocked validation" in report
    assert "Role top blocked closure command" in report
    assert "Role top blocked review status" in report
    assert "Role top blocked result path" in report
    assert "Role top blocked next action" in report
    assert "Role top blocked finding" in report
    assert "Role dispatch packets" in report
    assert "Org progress score" in report
    assert "Org fake-progress flags" in report
    assert "Org completed without merge" in report
    assert "Org decision deltas" in report
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
