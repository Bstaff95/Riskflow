import numpy as np
import pandas as pd

from riskflow.setup_research import (
    RECORD_COLUMNS,
    SETUP_EVENT_NAMES,
    SUMMARY_COLUMNS,
    run_setup_research,
)


def test_setup_research_outputs_required_columns():
    dates = pd.date_range("2024-01-01", periods=80, freq="D")
    target = pd.Series(100.0 * np.cumprod(np.full(80, 1.01)), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(np.full(80, 1.004)), index=dates)
    frame = pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "final_signal": np.linspace(-1.0, 2.0, 80),
            "viscosity": 0.0,
            "relative_component": np.linspace(-0.5, 1.5, 80),
            "compression_score_v0": np.linspace(50.0, 90.0, 80),
            "compression_score": np.linspace(50.0, 90.0, 80),
            "compression_duration": range(80),
            "setup_readiness_score": np.linspace(0.0, 100.0, 80),
            "relative_accumulation_score": np.linspace(0.0, 100.0, 80),
            "extension_risk_score": np.r_[np.zeros(60), np.linspace(0.0, 100.0, 20)],
            "trader_score_v0": np.linspace(0.0, 100.0, 80),
        },
        index=dates,
    )

    summary, records = run_setup_research({"AAA": frame}, min_sample_size=1, cooldown_bars=0)

    assert list(records.columns) == RECORD_COLUMNS
    assert list(summary.columns) == SUMMARY_COLUMNS
    assert set(summary["setup_event"]) == set(SETUP_EVENT_NAMES)
    assert not records.empty
    assert "trader_score_crosses_threshold" in set(records["setup_event"])


def test_setup_research_small_sample_is_inconclusive():
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    frame = pd.DataFrame(
        {
            "target": np.linspace(100.0, 110.0, 10),
            "benchmark": 100.0,
            "final_signal": [-1.0, 1.0] * 5,
            "viscosity": 0.0,
            "relative_component": np.linspace(0.0, 1.0, 10),
            "compression_score_v0": 85.0,
            "compression_score": 85.0,
            "compression_duration": range(10),
            "setup_readiness_score": np.linspace(0.0, 100.0, 10),
            "relative_accumulation_score": np.linspace(0.0, 100.0, 10),
            "extension_risk_score": 0.0,
            "trader_score_v0": np.linspace(0.0, 100.0, 10),
        },
        index=dates,
    )

    summary, _records = run_setup_research({"AAA": frame}, min_sample_size=999, cooldown_bars=0)

    assert set(summary["classification"]) == {"inconclusive"}
