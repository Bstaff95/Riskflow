import numpy as np
import pandas as pd

from riskflow.event_study import EVENT_NAMES, summary_columns, run_event_study


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

    summary, records = run_event_study({"AAA": frame})

    assert list(summary.columns) == summary_columns()
    assert set(summary["event"]) == set(EVENT_NAMES)
    assert not records.empty
    assert "setup_readiness_score_crosses_threshold" in set(records["event"])
