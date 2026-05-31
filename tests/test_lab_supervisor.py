from __future__ import annotations

import json
from pathlib import Path

import yaml

from riskflow.lab_loop import BULLISH_POSITIVE_OBJECTIVE
from riskflow.lab_supervisor import SupervisorOptions, supervise_latest_epoch


def _write_supervisor_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0001"
    epoch_dir.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_epoch_branch_decisions_v0",
                "epoch": "epoch_0001",
                "decisions": [
                    {
                        "concept_id": "positive_parent",
                        "decision": "promote",
                        "latest_loop": 5,
                        "reason": "strict survivor",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    state_path = tmp_path / "lab_state.json"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "last_completed_loop": 5,
                "completed_hypothesis_ids": ["positive_parent"],
                "loop_history": [
                    {
                        "loop_number": idx,
                        "hypothesis_id": f"warning_{idx}",
                        "root_hypothesis_id": f"warning_{idx}",
                        "track": "warning",
                        "decision": "promote",
                        "survivor_count": 1,
                        "useful_count": 1,
                        "errors": 0,
                    }
                    for idx in range(1, 5)
                ],
                "last_epoch": {
                    "epoch": "epoch_0001",
                    "epoch_dir": str(epoch_dir),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": "warning_next",
                        "track": "warning",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 1,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "warning",
                    },
                    {
                        "id": "positive_parent_validation_lag2_l0005",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 10,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "positive validation",
                        "research_gate_stage": "validation",
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_concept_scoreboard_v0",
                "concepts": {
                    "positive_parent": {
                        "track": "bullish_setup",
                        "current_promotion_level": "L3_strict_survivor",
                        "strict_survivors": 1,
                        "event_clusters": 16,
                        "best_timeframe": "1d",
                        "best_median_relative_return": 0.06,
                        "validation_status": "time_split_supported",
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return state_path, queue_path, scoreboard_path, epoch_dir


def test_supervisor_boosts_bullish_validation_gate(tmp_path: Path) -> None:
    state_path, queue_path, scoreboard_path, epoch_dir = _write_supervisor_fixture(tmp_path)

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            apply=True,
            epoch_size=5,
        )
    )

    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    positive = next(item for item in queue["queue"] if item["id"] == "positive_parent_validation_lag2_l0005")
    assert positive["priority"] == 0
    assert positive["supervisor_next_epoch_slot"] == 1
    assert result["actions"]
    assert (epoch_dir / "supervisor_decisions.yaml").exists()
    assert (epoch_dir / "supervisor_summary.md").exists()
    assert (tmp_path / "evidence_ledger.yaml").exists()


def test_supervisor_dry_run_does_not_mutate_queue(tmp_path: Path) -> None:
    state_path, queue_path, scoreboard_path, _epoch_dir = _write_supervisor_fixture(tmp_path)
    before = queue_path.read_text(encoding="utf-8")
    state_before = state_path.read_text(encoding="utf-8")
    ledger_path = tmp_path / "evidence_ledger.yaml"

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=ledger_path,
            apply=False,
            epoch_size=5,
        )
    )

    assert queue_path.read_text(encoding="utf-8") == before
    assert state_path.read_text(encoding="utf-8") == state_before
    assert not ledger_path.exists()
    assert result["actions"] == []
    assert result["decision"]["next_epoch_slots"]


def test_supervisor_reseeds_when_runnable_queue_is_empty(tmp_path: Path) -> None:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0002"
    loop_dir = tmp_path / "reports" / "session_test" / "loop_0006"
    epoch_dir.mkdir(parents=True)
    loop_dir.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_epoch_branch_decisions_v0",
                "epoch": "epoch_0002",
                "decisions": [
                    {
                        "concept_id": "useful_parent_validation_lag2_l0006",
                        "decision": "refine",
                        "latest_loop": 6,
                        "reason": "useful evidence",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest_path = epoch_dir / "epoch_manifest.json"
    manifest_path.write_text(
        json.dumps({"loop_start": 6, "loop_end": 6}),
        encoding="utf-8",
    )
    loop_dir.joinpath("ranked.csv").write_text(
        "\n".join(
            [
                "variant_id,family_id,timeframe,direction,detector,classification,params",
                'variant_1,family_1,1d,positive,compression_warning_bullish_setup,useful,"{""lookback"":20,""min_signal"":1.5}"',
            ]
        ),
        encoding="utf-8",
    )
    loop_dir.joinpath("strict_referee.csv").write_text("variant_id,strict_survivor\n", encoding="utf-8")
    state_path = tmp_path / "lab_state.json"
    parent_id = "useful_parent_validation_lag2_l0006"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "status": "completed_no_runnable_hypotheses",
                "last_completed_loop": 6,
                "completed_hypothesis_ids": [parent_id],
                "loop_history": [
                    {
                        "loop_number": 6,
                        "hypothesis_id": parent_id,
                        "track": "bullish_setup",
                        "generation": 1,
                        "decision": "refine",
                        "survivor_count": 0,
                        "useful_count": 1,
                        "report_dir": str(loop_dir),
                    }
                ],
                "last_epoch": {
                    "epoch": "epoch_0002",
                    "epoch_dir": str(epoch_dir),
                    "manifest": str(manifest_path),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": parent_id,
                        "track": "bullish_setup",
                        "status": "tested",
                        "promotion_level": "L2_discovered",
                        "priority": 1,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "parent",
                        "generation": 1,
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(yaml.safe_dump({"model": "scoreboard", "concepts": {}}), encoding="utf-8")

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            generated_grid_dir=tmp_path / "generated_grids",
            apply=True,
            epoch_size=5,
        )
    )

    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    reseeded = [item for item in queue["queue"] if item.get("created_from") == "meta_supervisor_reseed"]
    assert len(reseeded) == 1
    assert reseeded[0]["priority"] == 0
    assert reseeded[0]["root_id"] == "useful_parent"
    assert reseeded[0]["lineage_fingerprint"]
    assert reseeded[0]["reseed_source_signature"]
    assert Path(reseeded[0]["source"]).exists()
    assert result["decision"]["next_epoch_slots"][0]["hypothesis_id"] == reseeded[0]["id"]
    assert any(action.startswith("reseeded ") for action in result["actions"])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["status"] == "completed"


def test_bullish_objective_reseeds_bullish_near_miss_before_warning(tmp_path: Path) -> None:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0003"
    bullish_loop = tmp_path / "reports" / "session_test" / "loop_0010"
    warning_loop = tmp_path / "reports" / "session_test" / "loop_0011"
    epoch_dir.mkdir(parents=True)
    bullish_loop.mkdir(parents=True)
    warning_loop.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_epoch_branch_decisions_v0",
                "epoch": "epoch_0003",
                "decisions": [
                    {"concept_id": "bullish_parent", "decision": "refine", "latest_loop": 10},
                    {"concept_id": "warning_parent", "decision": "promote", "latest_loop": 11},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest_path = epoch_dir / "epoch_manifest.json"
    manifest_path.write_text(json.dumps({"loop_start": 10, "loop_end": 11}), encoding="utf-8")
    bullish_loop.joinpath("ranked.csv").write_text(
        "\n".join(
            [
                "variant_id,family_id,timeframe,direction,detector,classification,params",
                'bullish_v1,bullish_family,4h,positive,compression_warning_bullish_setup,useful,"{""lookback"":20,""min_compression"":55.0,""trigger"":""viscosity_reclaim""}"',
            ]
        ),
        encoding="utf-8",
    )
    bullish_loop.joinpath("strict_referee.csv").write_text("variant_id,strict_survivor\n", encoding="utf-8")
    bullish_loop.joinpath("bullish_evidence.yaml").write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_bullish_evidence_v0",
                "hypothesis_id": "bullish_parent",
                "track": "bullish_setup",
                "claim_type": "bullish_entry",
                "passes_path_gate": True,
                "passes_bullish_contract": False,
                "positive_useful_rows": 28,
                "terminal_median_relative_return": 0.04,
                "hit_rate": 0.45,
                "mfe_mae_ratio": 2.1,
                "unique_event_clusters": 4,
                "failure_reason": "positive rows exist but did not pass strict referee",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    warning_loop.joinpath("ranked.csv").write_text(
        "\n".join(
            [
                "variant_id,family_id,timeframe,direction,detector,classification,params",
                'warning_v1,warning_family,1d,negative,lower_high_rollover,useful,"{""lookback"":20,""recent_window"":5}"',
            ]
        ),
        encoding="utf-8",
    )
    warning_loop.joinpath("strict_referee.csv").write_text(
        "variant_id,strict_survivor\nwarning_v1,True\n",
        encoding="utf-8",
    )
    state_path = tmp_path / "lab_state.json"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "status": "completed_no_runnable_hypotheses",
                "last_completed_loop": 11,
                "completed_hypothesis_ids": ["bullish_parent", "warning_parent"],
                "loop_history": [
                    {
                        "loop_number": 10,
                        "hypothesis_id": "bullish_parent",
                        "track": "bullish_setup",
                        "decision": "refine",
                        "survivor_count": 0,
                        "useful_count": 28,
                        "report_dir": str(bullish_loop),
                    },
                    {
                        "loop_number": 11,
                        "hypothesis_id": "warning_parent",
                        "track": "warning",
                        "decision": "promote",
                        "survivor_count": 12,
                        "useful_count": 12,
                        "report_dir": str(warning_loop),
                    },
                ],
                "last_epoch": {
                    "epoch": "epoch_0003",
                    "epoch_dir": str(epoch_dir),
                    "manifest": str(manifest_path),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": "bullish_parent",
                        "track": "bullish_setup",
                        "status": "tested",
                        "promotion_level": "L2_discovered",
                        "priority": 1,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "bullish parent",
                        "claim_type": "bullish_entry",
                    },
                    {
                        "id": "warning_parent",
                        "track": "warning",
                        "status": "tested",
                        "promotion_level": "L3_strict_survivor",
                        "priority": 2,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "warning parent",
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(yaml.safe_dump({"model": "scoreboard", "concepts": {}}), encoding="utf-8")

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            generated_grid_dir=tmp_path / "generated_grids",
            apply=True,
            epoch_size=5,
            objective=BULLISH_POSITIVE_OBJECTIVE,
            max_reseed_per_epoch=3,
        )
    )

    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    reseeded = [item for item in queue["queue"] if item.get("created_from") == "meta_supervisor_reseed"]
    bullish_reseeded = [item for item in reseeded if item.get("track") == "bullish_setup"]
    assert bullish_reseeded
    assert bullish_reseeded[0]["claim_type"] == "bullish_entry"
    assert result["decision"]["next_epoch_slots"][0]["hypothesis_id"] == bullish_reseeded[0]["id"]


def test_bullish_objective_portfolio_prefers_distinct_new_setup_classes(tmp_path: Path) -> None:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0004"
    epoch_dir.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump({"model": "riskflow_lab_loop_epoch_branch_decisions_v0", "epoch": "epoch_0004", "decisions": []}),
        encoding="utf-8",
    )
    state_path = tmp_path / "lab_state.json"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "last_completed_loop": 15,
                "completed_hypothesis_ids": [],
                "loop_history": [],
                "last_epoch": {
                    "epoch": "epoch_0004",
                    "epoch_dir": str(epoch_dir),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    source = "research/grammar/rule_search_grid_v2_candidate.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": "flush_a",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 1,
                        "source": source,
                        "hypothesis": "flush a",
                        "claim_type": "bullish_entry",
                        "setup_class": "flush_reclaim",
                        "discovery_mode": "new_family",
                        "measurable_primitives": ["flush", "reclaim"],
                    },
                    {
                        "id": "flush_b",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 2,
                        "source": source,
                        "hypothesis": "flush b",
                        "claim_type": "bullish_entry",
                        "setup_class": "flush_reclaim",
                        "discovery_mode": "new_family",
                        "measurable_primitives": ["flush", "reclaim"],
                    },
                    {
                        "id": "zero_a",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 3,
                        "source": source,
                        "hypothesis": "zero a",
                        "claim_type": "bullish_entry",
                        "setup_class": "zero_reclaim",
                        "discovery_mode": "new_family",
                        "measurable_primitives": ["zero", "acceptance"],
                    },
                    {
                        "id": "compression_a",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 4,
                        "source": source,
                        "hypothesis": "compression a",
                        "claim_type": "bullish_entry",
                        "setup_class": "compression_reclaim",
                        "discovery_mode": "new_family",
                        "measurable_primitives": ["compression", "reclaim"],
                    },
                    {
                        "id": "control_a",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 5,
                        "source": source,
                        "hypothesis": "control a",
                        "claim_type": "control",
                        "setup_class": "flush_reclaim",
                        "research_gate_stage": "attribution",
                        "measurable_primitives": ["flush", "control"],
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(yaml.safe_dump({"model": "scoreboard", "concepts": {}}), encoding="utf-8")

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            apply=False,
            epoch_size=5,
            objective=BULLISH_POSITIVE_OBJECTIVE,
        )
    )

    slot_ids = [slot["hypothesis_id"] for slot in result["decision"]["next_epoch_slots"]]
    assert {"flush_a", "zero_a", "compression_a", "control_a"}.issubset(set(slot_ids))
    assert "flush_b" not in slot_ids[:4]


def test_bullish_objective_cools_weak_family_after_repeated_non_contract_attempts(tmp_path: Path) -> None:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0005"
    epoch_dir.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_epoch_branch_decisions_v0",
                "epoch": "epoch_0005",
                "decisions": [{"concept_id": "weak_parent", "decision": "refine", "reason": "near miss"}],
            }
        ),
        encoding="utf-8",
    )
    history = []
    for loop_number in range(20, 23):
        loop_dir = tmp_path / "reports" / "session_test" / f"loop_{loop_number:04d}"
        loop_dir.mkdir(parents=True)
        loop_dir.joinpath("bullish_evidence.yaml").write_text(
            yaml.safe_dump(
                {
                    "hypothesis_id": "weak_parent",
                    "track": "bullish_setup",
                    "passes_path_gate": True,
                    "passes_bullish_contract": False,
                    "positive_useful_rows": 3,
                    "failure_reason": "positive rows exist but did not pass strict referee",
                }
            ),
            encoding="utf-8",
        )
        history.append(
            {
                "loop_number": loop_number,
                "hypothesis_id": "weak_parent",
                "root_hypothesis_id": "weak_parent",
                "track": "bullish_setup",
                "decision": "refine",
                "survivor_count": 0,
                "useful_count": 3,
                "report_dir": str(loop_dir),
            }
        )
    state_path = tmp_path / "lab_state.json"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "last_completed_loop": 22,
                "completed_hypothesis_ids": ["weak_parent"],
                "loop_history": history,
                "last_epoch": {
                    "epoch": "epoch_0005",
                    "epoch_dir": str(epoch_dir),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": "weak_parent_child",
                        "root_id": "weak_parent",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 1,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "weak child",
                        "claim_type": "bullish_entry",
                        "setup_class": "weak_class",
                    },
                    {
                        "id": "fresh_parent",
                        "track": "bullish_setup",
                        "status": "new",
                        "promotion_level": "L1_encoded",
                        "priority": 10,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "fresh",
                        "claim_type": "bullish_entry",
                        "setup_class": "fresh_class",
                        "discovery_mode": "new_family",
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(yaml.safe_dump({"model": "scoreboard", "concepts": {}}), encoding="utf-8")

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            apply=True,
            epoch_size=5,
            objective=BULLISH_POSITIVE_OBJECTIVE,
            weak_family_attempt_limit=3,
            weak_family_cooldown_loops=25,
        )
    )

    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    weak_child = next(item for item in queue["queue"] if item["id"] == "weak_parent_child")
    slot_ids = [slot["hypothesis_id"] for slot in result["decision"]["next_epoch_slots"]]
    assert "weak_parent_child" not in slot_ids
    assert "fresh_parent" in slot_ids
    assert weak_child["evidence_budget_status"] == "cooldown_weak_family"
    assert weak_child["cooldown_until_loop"] == 47


def test_bullish_objective_does_not_reseed_generation_one_near_miss_without_contract(tmp_path: Path) -> None:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0006"
    loop_dir = tmp_path / "reports" / "session_test" / "loop_0030"
    epoch_dir.mkdir(parents=True)
    loop_dir.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_epoch_branch_decisions_v0",
                "epoch": "epoch_0006",
                "decisions": [{"concept_id": "weak_parent", "decision": "refine", "reason": "near miss"}],
            }
        ),
        encoding="utf-8",
    )
    manifest_path = epoch_dir / "epoch_manifest.json"
    manifest_path.write_text(json.dumps({"loop_start": 30, "loop_end": 30}), encoding="utf-8")
    loop_dir.joinpath("ranked.csv").write_text(
        "\n".join(
            [
                "variant_id,family_id,timeframe,direction,detector,classification,params",
                'v1,family,4h,positive,failed_weakness_reclaim,useful,"{""lookback"":20}"',
            ]
        ),
        encoding="utf-8",
    )
    loop_dir.joinpath("strict_referee.csv").write_text("variant_id,strict_survivor\n", encoding="utf-8")
    loop_dir.joinpath("bullish_evidence.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": "weak_parent_child",
                "track": "bullish_setup",
                "passes_path_gate": True,
                "passes_bullish_contract": False,
                "positive_useful_rows": 8,
                "failure_reason": "positive rows exist but did not pass strict referee",
            }
        ),
        encoding="utf-8",
    )
    state_path = tmp_path / "lab_state.json"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "status": "completed_no_runnable_hypotheses",
                "last_completed_loop": 30,
                "completed_hypothesis_ids": ["weak_parent_child"],
                "loop_history": [
                    {
                        "loop_number": 30,
                        "hypothesis_id": "weak_parent_child",
                        "root_hypothesis_id": "weak_parent",
                        "track": "bullish_setup",
                        "generation": 1,
                        "decision": "refine",
                        "survivor_count": 0,
                        "useful_count": 8,
                        "report_dir": str(loop_dir),
                    }
                ],
                "last_epoch": {
                    "epoch": "epoch_0006",
                    "epoch_dir": str(epoch_dir),
                    "manifest": str(manifest_path),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": "weak_parent_child",
                        "track": "bullish_setup",
                        "status": "tested",
                        "promotion_level": "L2_discovered",
                        "priority": 1,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "weak child",
                        "generation": 1,
                        "claim_type": "bullish_entry",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(yaml.safe_dump({"model": "scoreboard", "concepts": {}}), encoding="utf-8")

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            generated_grid_dir=tmp_path / "generated_grids",
            apply=True,
            epoch_size=5,
            objective=BULLISH_POSITIVE_OBJECTIVE,
        )
    )

    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    assert [item for item in queue["queue"] if item.get("created_from") == "meta_supervisor_reseed"] == []
    assert result["decision"]["next_epoch_slots"] == []


def test_supervisor_does_not_schedule_over_generation_candidate(tmp_path: Path) -> None:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0007"
    epoch_dir.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump({"model": "riskflow_lab_loop_epoch_branch_decisions_v0", "epoch": "epoch_0007", "decisions": []}),
        encoding="utf-8",
    )
    state_path = tmp_path / "lab_state.json"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "last_completed_loop": 31,
                "completed_hypothesis_ids": [],
                "loop_history": [],
                "last_epoch": {
                    "epoch": "epoch_0007",
                    "epoch_dir": str(epoch_dir),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": "warning_parent_supervisor_reseed_g003_l0030_r0030_1",
                        "track": "warning",
                        "status": "new",
                        "promotion_level": "L2_discovered",
                        "priority": 0,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "over cap warning child",
                        "generation": 3,
                        "research_gate_stage": "reseed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(yaml.safe_dump({"model": "scoreboard", "concepts": {}}), encoding="utf-8")

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            apply=False,
            epoch_size=5,
            max_generation=2,
        )
    )

    assert result["decision"]["next_epoch_slots"] == []


def test_supervisor_does_not_reseed_past_generation_cap(tmp_path: Path) -> None:
    epoch_dir = tmp_path / "reports" / "session_test" / "epochs" / "epoch_0008"
    loop_dir = tmp_path / "reports" / "session_test" / "loop_0032"
    epoch_dir.mkdir(parents=True)
    loop_dir.mkdir(parents=True)
    branch_path = epoch_dir / "branch_decisions.yaml"
    branch_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_epoch_branch_decisions_v0",
                "epoch": "epoch_0008",
                "decisions": [{"concept_id": "warning_parent", "decision": "refine", "latest_loop": 32}],
            }
        ),
        encoding="utf-8",
    )
    manifest_path = epoch_dir / "epoch_manifest.json"
    manifest_path.write_text(json.dumps({"loop_start": 32, "loop_end": 32}), encoding="utf-8")
    loop_dir.joinpath("ranked.csv").write_text(
        "\n".join(
            [
                "variant_id,family_id,timeframe,direction,detector,classification,params",
                'v1,family,4h,negative,lower_high_rollover,useful,"{""lookback"":20}"',
            ]
        ),
        encoding="utf-8",
    )
    loop_dir.joinpath("strict_referee.csv").write_text("variant_id,strict_survivor\n", encoding="utf-8")
    state_path = tmp_path / "lab_state.json"
    parent_id = "warning_parent_supervisor_reseed_g002_l0028_r0031_1"
    state_path.write_text(
        json.dumps(
            {
                "session_id": "test",
                "status": "completed_no_runnable_hypotheses",
                "last_completed_loop": 32,
                "completed_hypothesis_ids": [parent_id],
                "loop_history": [
                    {
                        "loop_number": 32,
                        "hypothesis_id": parent_id,
                        "track": "warning",
                        "generation": 2,
                        "decision": "refine",
                        "survivor_count": 0,
                        "useful_count": 36,
                        "report_dir": str(loop_dir),
                    }
                ],
                "last_epoch": {
                    "epoch": "epoch_0008",
                    "epoch_dir": str(epoch_dir),
                    "manifest": str(manifest_path),
                    "branch_decisions": str(branch_path),
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime_queue.yaml"
    queue_path.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [
                    {
                        "id": parent_id,
                        "track": "warning",
                        "status": "tested",
                        "promotion_level": "L2_discovered",
                        "priority": 1,
                        "source": "research/grammar/rule_search_grid_v2_candidate.yaml",
                        "hypothesis": "warning parent",
                        "generation": 2,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    scoreboard_path = tmp_path / "concept_scoreboard.yaml"
    scoreboard_path.write_text(yaml.safe_dump({"model": "scoreboard", "concepts": {}}), encoding="utf-8")

    result = supervise_latest_epoch(
        SupervisorOptions(
            state_path=state_path,
            runtime_queue_path=queue_path,
            concept_scoreboard_path=scoreboard_path,
            evidence_ledger_path=tmp_path / "evidence_ledger.yaml",
            generated_grid_dir=tmp_path / "generated_grids",
            apply=True,
            epoch_size=5,
            max_generation=2,
        )
    )

    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    assert [item for item in queue["queue"] if item.get("created_from") == "meta_supervisor_reseed"] == []
    assert result["decision"]["next_epoch_slots"] == []
