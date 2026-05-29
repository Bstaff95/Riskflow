from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from riskflow.lab_loop import (
    LabLoopOptions,
    acquire_lock,
    build_refinement_grid,
    decide_loop_outcome,
    load_lab_queue,
    release_lock,
    run_lab_loop,
    select_next_hypothesis,
    validate_lab_queue,
)


def _queue() -> dict:
    return {
        "model": "riskflow_lab_loop_hypothesis_queue_v0",
        "queue": [
            {
                "id": "warning_a",
                "track": "warning",
                "status": "tested_needs_fresh_data",
                "promotion_level": "L2_discovered",
                "priority": 2,
                "source": "research/grammar/rule_search_grid_v19_relative_failed_breakout_current_candidates.yaml",
                "hypothesis": "warning test",
                "measurable_primitives": ["relative_failed_breakout_warning"],
                "expected_outcome": "negative_forward_relative_return",
            },
            {
                "id": "bullish_a",
                "track": "bullish_setup",
                "status": "new",
                "promotion_level": "L0_registered",
                "priority": 1,
                "hypothesis": "bullish journey test",
                "measurable_primitives": ["viscosity_reclaim"],
                "expected_outcome": "positive_trade_path",
            },
        ],
    }


def test_validate_lab_queue_accepts_seed_shape() -> None:
    errors = validate_lab_queue(_queue())

    assert errors == []


def test_load_lab_queue_rejects_duplicate_ids(tmp_path: Path) -> None:
    queue = _queue()
    queue["queue"][1]["id"] = "warning_a"
    path = tmp_path / "queue.yaml"
    path.write_text(yaml.safe_dump(queue), encoding="utf-8")

    try:
        load_lab_queue(path)
    except ValueError as exc:
        assert "duplicates warning_a" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected duplicate id failure")


def test_select_next_hypothesis_prefers_executable_and_skips_terminal() -> None:
    queue = _queue()
    selected = select_next_hypothesis(queue, {"last_completed_loop": 0})

    assert selected is not None
    assert selected["id"] == "warning_a"

    queue["queue"][0]["status"] = "archived"
    selected = select_next_hypothesis(queue, {"last_completed_loop": 0})

    assert selected is not None
    assert selected["id"] == "bullish_a"


def test_decide_loop_outcome_promotes_strict_survivors() -> None:
    ranked = pd.DataFrame(
        {
            "variant_id": ["v1"],
            "classification": ["useful"],
        }
    )
    strict = pd.DataFrame(
        {
            "variant_id": ["v1"],
            "strict_survivor": [True],
        }
    )

    decision = decide_loop_outcome(ranked, strict)

    assert decision["decision"] == "promote"
    assert decision["promotion_level"] == "L3_strict_survivor"


def test_decide_loop_outcome_refines_useful_non_strict() -> None:
    ranked = pd.DataFrame(
        {
            "variant_id": ["v1"],
            "classification": ["watchlist"],
        }
    )

    decision = decide_loop_outcome(ranked, pd.DataFrame())

    assert decision["decision"] == "refine"
    assert decision["promotion_level"] == "L2_discovered"


def test_build_refinement_grid_mutates_numeric_params() -> None:
    row = pd.Series(
        {
            "variant_id": "v1",
            "family_id": "relative_failed_breakout",
            "direction": "negative",
            "detector": "relative_failed_breakout_warning",
            "params": json.dumps(
                {
                    "timeframe": "1d",
                    "lookback": 20,
                    "require_viscosity_loss": True,
                    "min_gradient": 0.0,
                    "trigger": "viscosity_loss",
                }
            ),
        }
    )

    grid = build_refinement_grid(row, family_suffix="loop_0001")
    params = grid["families"][0]["parameter_grid"]

    assert grid["families"][0]["family_id"] == "relative_failed_breakout_loop_0001"
    assert params["lookback"] == [15, 20, 25]
    assert params["require_viscosity_loss"] == [True]
    assert params["trigger"] == ["viscosity_loss"]
    assert "timeframe" not in params


def test_run_lab_loop_dry_run_writes_state_and_status(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.yaml"
    runtime_queue = tmp_path / "runtime_queue.yaml"
    state_path = tmp_path / "lab_state.json"
    report_root = tmp_path / "reports"
    queue_path.write_text(yaml.safe_dump(_queue()), encoding="utf-8")

    state = run_lab_loop(
        LabLoopOptions(
            queue_path=queue_path,
            runtime_queue_path=runtime_queue,
            state_path=state_path,
            lock_path=tmp_path / "lab_loop.lock",
            report_root=report_root,
            max_loops=1,
            dry_run=True,
        )
    )

    assert state["status"] == "completed"
    assert state["last_completed_loop"] == 1
    assert state_path.exists()
    assert runtime_queue.exists()
    assert (report_root / "latest_status.md").exists()


def test_lab_loop_lock_rejects_duplicate_runner(tmp_path: Path) -> None:
    lock_path = tmp_path / "lab_loop.lock"
    token = acquire_lock(lock_path)
    try:
        try:
            acquire_lock(lock_path)
        except RuntimeError as exc:
            assert "lock already exists" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("expected duplicate lock failure")
    finally:
        release_lock(lock_path, token)

    assert not lock_path.exists()
