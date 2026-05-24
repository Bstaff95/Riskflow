import pandas as pd

from riskflow.indicator_engine import INDICATOR_COLUMNS, calculate_indicator


def test_indicator_engine_returns_expected_columns():
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    target = pd.Series([10.0, 10.5, 11.0, 11.2, 11.5, 12.0], index=dates)
    benchmark = pd.Series([100.0, 100.2, 100.4, 100.5, 100.7, 101.0], index=dates)

    result = calculate_indicator(target, benchmark)

    assert list(result.columns) == INDICATOR_COLUMNS


def test_indicator_signal_exists_when_valid_price_exists():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    target = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0], index=dates)
    benchmark = pd.Series([100.0, 100.0, 100.0, 100.0, 100.0], index=dates)

    result = calculate_indicator(target, benchmark)

    assert result["final_signal"].notna().all()
    assert (result["final_signal"] == 0.0).all()
