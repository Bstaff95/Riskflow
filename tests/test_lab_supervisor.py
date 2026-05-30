from __future__ import annotations

import json
from pathlib import Path

import yaml

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
    assert Path(reseeded[0]["source"]).exists()
    assert result["decision"]["next_epoch_slots"][0]["hypothesis_id"] == reseeded[0]["id"]
    assert any(action.startswith("reseeded ") for action in result["actions"])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["status"] == "completed"
