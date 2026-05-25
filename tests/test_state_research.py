from __future__ import annotations

import numpy as np
import pandas as pd

from riskflow.state_research import (
    RECORD_COLUMNS,
    SUMMARY_COLUMNS,
    TRANSITION_COLUMNS,
    build_state_transition_matrix,
    run_state_research,
)
from riskflow.state_registry import STATE_MODEL_V0, get_state_model_spec


def _frame(states: list[str] | None = None, periods: int = 40) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    if states is None:
        states = (
            ["Compression"] * 6
            + ["Relative Accumulation"] * 7
            + ["Emerging Leader"] * 9
            + ["Confirmed Leader"] * 8
            + ["Breakdown"] * (periods - 30)
        )
    target = pd.Series(100.0 * np.cumprod(np.full(periods, 1.01)), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(np.full(periods, 1.004)), index=dates)
    return pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "state": states[:periods],
            "state_model": STATE_MODEL_V0,
            "state_confidence": 75.0,
        },
        index=dates,
    )


def test_state_research_outputs_required_columns_and_forward_returns():
    summary, records, transition_matrix = run_state_research(
        {"AAA": _frame()},
        min_sample_size=1,
        entry_lag_bars=1,
    )

    assert list(records.columns) == RECORD_COLUMNS
    assert list(summary.columns) == SUMMARY_COLUMNS
    assert list(transition_matrix.columns) == TRANSITION_COLUMNS
    assert not records.empty
    assert records["forward_relative_return_14"].notna().any()
    assert set(summary["state"]) == set(get_state_model_spec(STATE_MODEL_V0).states)


def test_transition_matrix_includes_all_states_and_normalized_probabilities():
    summary, records, matrix = run_state_research({"AAA": _frame()}, min_sample_size=1)

    states = set(get_state_model_spec(STATE_MODEL_V0).states)
    assert set(matrix["from_state"]) == states
    assert set(matrix["to_state"]) == states
    active_sums = matrix.groupby("from_state")["transition_probability"].sum()
    assert active_sums["Compression"] == 1.0
    assert active_sums["Relative Accumulation"] == 1.0
    assert active_sums["Emerging Leader"] == 1.0
    assert active_sums["Confirmed Leader"] == 1.0
    assert active_sums["Breakdown"] == 0.0
    assert summary.loc[summary["state"] == "Compression", "most_common_next_state"].iloc[0] == "Relative Accumulation"


def test_state_duration_uses_completed_runs_not_same_state_transitions():
    states = ["Compression"] * 3 + ["Emerging Leader"] * 2 + ["Compression"] * 4
    summary, records, matrix = run_state_research(
        {"AAA": _frame(states=states, periods=len(states))},
        min_sample_size=1,
    )

    compression = summary[summary["state"] == "Compression"].iloc[0]
    assert compression["median_state_duration"] == 3.5
    compression_transitions = matrix[
        (matrix["from_state"] == "Compression") & (matrix["transition_count"] > 0)
    ]
    assert set(compression_transitions["to_state"]) == {"Emerging Leader"}


def test_state_research_small_sample_is_inconclusive_and_concentration_is_fragile():
    small_summary, _records, _matrix = run_state_research(
        {"AAA": _frame(periods=8)},
        min_sample_size=999,
    )
    assert set(small_summary["classification"]) == {"inconclusive"}

    concentrated_summary, _records, _matrix = run_state_research(
        {"AAA": _frame(periods=40)},
        min_sample_size=1,
    )
    compression_concentrated = concentrated_summary[concentrated_summary["state"] == "Compression"].iloc[0]
    assert compression_concentrated["classification"] == "fragile"
    assert compression_concentrated["max_symbol_state_share"] == 1.0

    repeated = _frame(periods=40)
    summary, _records, _matrix = run_state_research(
        {"AAA": repeated, "BBB": repeated.copy()},
        min_sample_size=1,
    )
    compression = summary[summary["state"] == "Compression"].iloc[0]
    assert compression["classification"] in {"useful", "watchlist", "fragile"}
    assert compression["max_symbol_state_share"] == 0.5


def test_state_research_empty_input_returns_valid_outputs():
    summary, records, matrix = run_state_research({})

    assert list(records.columns) == RECORD_COLUMNS
    assert list(summary.columns) == SUMMARY_COLUMNS
    assert list(matrix.columns) == TRANSITION_COLUMNS
    assert records.empty
    assert set(summary["classification"]) == {"inconclusive"}
    assert matrix["transition_count"].sum() == 0
