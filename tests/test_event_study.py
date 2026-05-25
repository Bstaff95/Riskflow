import numpy as np
import pandas as pd
import pytest

from riskflow.event_registry import get_event_spec
from riskflow.event_study import EVENT_NAMES, RECORD_COLUMNS, summary_columns, run_event_study, summarize_event_records
from riskflow.research_outcomes import (
    apply_event_cooldown,
    event_cluster_id,
    forward_max_drawdown,
    forward_relative_return,
    forward_return,
)


def test_event_study_produces_required_columns():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    target = pd.Series(100.0 * np.cumprod(np.full(60, 1.01)), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(np.full(60, 1.005)), index=dates)
    final_signal = pd.Series(np.linspace(-2.0, 2.5, 60), index=dates)
    relative_component = pd.Series(np.linspace(-1.5, 1.5, 60), index=dates)
    frame = pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "final_signal": final_signal,
            "viscosity": 0.0,
            "relative_component": relative_component,
            "compression_score": 75.0,
            "compression_duration": range(60),
            "setup_readiness_score": final_signal.rank(pct=True) * 100.0,
            "relative_accumulation_score": relative_component.rank(pct=True) * 100.0,
            "extension_risk_score": 0.0,
            "state": "Weak",
        },
        index=dates,
    )
    frame.loc[dates[50:], "extension_risk_score"] = 80.0
    frame.loc[dates[35], "state"] = "Emerging Leader"
    frame.loc[dates[45], "state"] = "Confirmed Leader"

    summary, records = run_event_study({"AAA": frame}, cooldown_bars=0, min_sample_size=1)

    assert list(summary.columns) == summary_columns()
    assert list(records.columns) == RECORD_COLUMNS
    assert set(summary["event"]) == set(EVENT_NAMES)
    assert not records.empty
    assert "setup_readiness_score_crosses_threshold" in set(records["event"])
    assert {"event_id", "event_family", "classification", "notes"}.issubset(summary.columns)
    assert {"entry_lag_bars", "entry_date", "cooldown_bars", "event_cluster_id"}.issubset(records.columns)


def test_shared_forward_outcomes_handle_entry_lag_and_relative_return():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    target = pd.Series([100.0, 110.0, 121.0, 133.1, 146.41], index=dates)
    benchmark = pd.Series([100.0, 105.0, 110.25, 115.7625, 121.550625], index=dates)

    no_lag = forward_return(target, horizon=2, entry_lag_bars=0)
    with_lag = forward_return(target, horizon=2, entry_lag_bars=1)
    relative = forward_relative_return(target, benchmark, horizon=2, entry_lag_bars=1)

    assert round(no_lag.iloc[0], 6) == 0.21
    assert round(with_lag.iloc[0], 6) == 0.21
    assert round(relative.iloc[0], 6) == round((1.21 / 1.1025) - 1.0, 6)


def test_drawdown_starts_after_entry_not_signal_bar():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    close = pd.Series([100.0, 50.0, 120.0, 90.0, 130.0], index=dates)

    drawdown = forward_max_drawdown(close, horizon=2, entry_lag_bars=1)

    assert drawdown.iloc[0] == 0.0
    assert drawdown.iloc[1] == -0.25


def test_cooldown_suppresses_repeated_events_and_cluster_id_is_deterministic():
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    mask = pd.Series([True, True, False, True, False, True], index=dates)

    cooled = apply_event_cooldown(mask, cooldown_bars=2)

    assert cooled.tolist() == [True, False, False, True, False, False]
    assert event_cluster_id(dates[0]) == "2024-01"


def test_event_registry_covers_base_events_and_rejects_unknown_ids():
    for event_name in EVENT_NAMES:
        assert get_event_spec(event_name).event_id == event_name
    with pytest.raises(KeyError):
        get_event_spec("not_a_real_event")


def test_event_summary_classifies_inconclusive_useful_watchlist_and_fragile():
    records = []
    dates = pd.date_range("2024-01-01", periods=24, freq="40D")
    for idx, date in enumerate(dates[:6]):
        records.append(
            {
                "symbol": f"U{idx}",
                "date": date,
                "event": "signal_crosses_above_zero",
                "event_cluster_id": f"2024-{idx + 1:02d}",
                "forward_relative_return_3": 0.01,
                "forward_relative_return_7": 0.01,
                "forward_relative_return_14": 0.02,
                "forward_relative_return_30": 0.03,
                "max_drawdown_14": -0.02,
                "max_drawdown_30": -0.03,
            }
        )
    for idx, date in enumerate(dates[6:12]):
        records.append(
            {
                "symbol": f"W{idx}",
                "date": date,
                "event": "final_signal_reclaims_minus_1_5",
                "event_cluster_id": f"2025-{idx + 1:02d}",
                "forward_relative_return_3": 0.0,
                "forward_relative_return_7": 0.0,
                "forward_relative_return_14": 0.01,
                "forward_relative_return_30": -0.01,
                "max_drawdown_14": -0.02,
                "max_drawdown_30": -0.03,
            }
        )
    for idx, date in enumerate(dates[12:18]):
        records.append(
            {
                "symbol": f"F{idx}",
                "date": date,
                "event": "signal_crosses_below_viscosity",
                "event_cluster_id": f"2026-{idx + 1:02d}",
                "forward_relative_return_3": -0.01,
                "forward_relative_return_7": -0.01,
                "forward_relative_return_14": -0.02,
                "forward_relative_return_30": -0.03,
                "max_drawdown_14": -0.10,
                "max_drawdown_30": -0.20,
            }
        )
    for idx, date in enumerate(dates[18:24]):
        records.append(
            {
                "symbol": "ONE",
                "date": date,
                "event": "relative_component_crosses_above_zero",
                "event_cluster_id": f"2027-{idx + 1:02d}",
                "forward_relative_return_3": 0.01,
                "forward_relative_return_7": 0.01,
                "forward_relative_return_14": 0.02,
                "forward_relative_return_30": 0.03,
                "max_drawdown_14": -0.02,
                "max_drawdown_30": -0.03,
            }
        )

    summary = summarize_event_records(pd.DataFrame(records), min_sample_size=5)
    classes = dict(zip(summary["event"], summary["classification"]))

    assert classes["compression_80_relative_rising"] == "inconclusive"
    assert classes["signal_crosses_above_zero"] == "useful"
    assert classes["final_signal_reclaims_minus_1_5"] == "watchlist"
    assert classes["signal_crosses_below_viscosity"] == "useful"
    assert classes["relative_component_crosses_above_zero"] == "fragile"
    concentrated = summary[summary["event"] == "relative_component_crosses_above_zero"].iloc[0]
    assert concentrated["max_symbol_event_share"] == 1.0
