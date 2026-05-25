import numpy as np
import pandas as pd

from riskflow.baskets import build_equal_weight_return_index, build_equal_weight_return_index_frame


def test_equal_weight_basket_ignores_missing_members_when_allowed():
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    closes = {
        "AAA": pd.Series([100.0, 110.0, 121.0, np.nan], index=dates),
        "BBB": pd.Series([50.0, 55.0, 60.5, 66.55], index=dates),
    }

    basket = build_equal_weight_return_index(closes, min_active_members=1, name="TEST")

    assert basket.iloc[0] == 100.0
    assert round(basket.iloc[1], 6) == 110.0
    assert round(basket.iloc[2], 6) == 121.0
    assert round(basket.iloc[3], 6) == 133.1


def test_equal_weight_basket_requires_min_active_returns():
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    closes = {
        "AAA": pd.Series([100.0, 110.0, 121.0, np.nan], index=dates),
        "BBB": pd.Series([50.0, 55.0, 60.5, 66.55], index=dates),
    }

    basket = build_equal_weight_return_index(closes, min_active_members=2, name="TEST")

    assert basket.iloc[0] == 100.0
    assert round(basket.iloc[1], 6) == 110.0
    assert round(basket.iloc[2], 6) == 121.0
    assert np.isnan(basket.iloc[3])


def test_equal_weight_basket_frame_reports_diagnostics():
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    closes = {
        "AAA": pd.Series([100.0, 110.0, 121.0, np.nan], index=dates),
        "BBB": pd.Series([50.0, 55.0, 60.5, 66.55], index=dates),
    }

    frame = build_equal_weight_return_index_frame(closes, min_active_members=2, name="TEST")

    assert frame.iloc[0]["basket_index"] == 100.0
    assert frame.iloc[1]["benchmark_active_members"] == 2
    assert frame.iloc[1]["benchmark_missing_members"] == 0
    assert frame.iloc[1]["benchmark_member_count"] == 2
    assert frame.iloc[1]["benchmark_min_active_members"] == 2
    assert bool(frame.iloc[1]["benchmark_passed"]) is True
    assert bool(frame.iloc[3]["benchmark_passed"]) is False
