import numpy as np
import pandas as pd
import pytest

from riskflow.setup_quality import SETUP_QUALITY_COLUMNS, calculate_setup_quality
from riskflow.setup_registry import OPPORTUNITY_SCORE_V0, get_setup_spec


def _frame() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    return pd.DataFrame(
        {
            "final_signal": [-1.0, -0.8, -0.4, 0.1, 0.4, 0.7, 1.0, 2.4],
            "relative_component": [-0.5, -0.2, 0.0, 0.2, 0.5, 0.7, 0.8, 1.2],
            "relative_log": np.linspace(-0.1, 0.2, 8),
            "viscosity": [-0.6, -0.6, -0.5, -0.2, 0.1, 0.4, 0.8, 1.4],
            "gradient_driver": [-1.0, -0.7, -0.2, 0.2, 0.5, 0.9, 1.1, 0.8],
            "compression_score": [80.0, 82.0, 84.0, 86.0, 75.0, 65.0, 30.0, 15.0],
            "compression_score_v0": [80.0, 82.0, 84.0, 86.0, 75.0, 65.0, 30.0, 15.0],
            "compression_duration": [1, 2, 3, 4, 5, 0, 0, 0],
            "compression_stability": [100.0, 100.0, 100.0, 100.0, 90.0, 70.0, 40.0, 10.0],
            "stale_data_flag": False,
            "state": ["Compression"] * 8,
        },
        index=dates,
    )


def test_setup_quality_outputs_expected_columns_and_bounds():
    result = calculate_setup_quality(_frame())

    assert list(result.columns) == SETUP_QUALITY_COLUMNS
    score_columns = [
        "leader_quality_score",
        "compression_quality_score",
        "relative_accumulation_score",
        "setup_readiness_score",
        "extension_risk_score",
        "data_quality_score",
        "trader_score_v0",
        "opportunity_score_v0",
    ]
    for column in score_columns:
        assert result[column].between(0.0, 100.0).all()


def test_relative_accumulation_requires_relative_improvement():
    rising = _frame()
    flat = rising.copy()
    flat["relative_component"] = 0.1

    rising_result = calculate_setup_quality(rising)
    flat_result = calculate_setup_quality(flat)

    assert rising_result["relative_accumulation_score"].iloc[4] > flat_result["relative_accumulation_score"].iloc[4]


def test_setup_readiness_detects_reclaims():
    result = calculate_setup_quality(_frame())

    assert result["setup_readiness_score"].iloc[3] > result["setup_readiness_score"].iloc[2]
    assert "zero_reclaim" in result["setup_tags"].iloc[3]


def test_extension_risk_rises_for_overheated_expanded_asset():
    result = calculate_setup_quality(_frame())

    assert result["extension_risk_score"].iloc[-1] > result["extension_risk_score"].iloc[3]
    assert "extended" in result["setup_tags"].iloc[-1]


def test_stale_data_caps_compression_quality():
    frame = _frame()
    frame["stale_data_flag"] = True
    frame["compression_score_v0"] = 95.0
    frame["compression_score"] = 95.0

    result = calculate_setup_quality(frame)

    assert result["compression_quality_score"].max() <= 10.0
    assert result["data_quality_score"].max() < 60.0
    assert "stale" in result["setup_notes"].iloc[-1]


def test_trader_score_penalizes_extension_risk():
    normal = _frame()
    extended = normal.copy()
    extended["final_signal"] = 2.8
    extended["compression_score_v0"] = 10.0
    extended["compression_score"] = 10.0

    normal_result = calculate_setup_quality(normal)
    extended_result = calculate_setup_quality(extended)

    assert normal_result["trader_score_v0"].iloc[3] > extended_result["trader_score_v0"].iloc[3]


def test_setup_notes_explain_multiple_conditions():
    frame = _frame()
    frame.loc[frame.index[-1], "stale_data_flag"] = True

    result = calculate_setup_quality(frame)

    assert ";" in result["setup_notes"].iloc[-1]


def test_setup_registry_rejects_unknown_ids():
    assert get_setup_spec(OPPORTUNITY_SCORE_V0).role == "opportunity_score"
    with pytest.raises(KeyError):
        get_setup_spec("unknown_setup_model")
