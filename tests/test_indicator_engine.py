import pandas as pd

from riskflow.config import IndicatorSettings
from riskflow.indicator_engine import (
    INDICATOR_COLUMNS,
    _rolling_vol_normalized,
    adaptive_viscosity,
    calculate_indicator,
)


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


def test_default_indicator_settings_match_current_tradingview_research_setup():
    settings = IndicatorSettings()

    assert settings.z_len == 200
    assert settings.use_risk is False
    assert settings.component_z_clamp == 3.5
    assert settings.viscosity_lookback == 20
    assert settings.viscosity_fast == 2
    assert settings.viscosity_slow == 34
    assert settings.viscosity_impulse_boost == 0.65
    assert settings.viscosity_zero_zone_boost == 0.35


def test_gradient_volatility_normalization_uses_pine_population_stdev():
    series = pd.Series([0.0, 2.0])

    result = _rolling_vol_normalized(series, lookback=2, clamp=2.0)

    assert result.iloc[1] == 2.0


def test_viscosity_impulse_boost_reacts_faster_near_zero():
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    signal = pd.Series([-1.5, -1.4, -1.3, -1.2, -0.5, 0.4, 0.7, 0.6], index=dates)

    boosted = adaptive_viscosity(signal, impulse_boost=0.65, zero_zone_boost=0.35)
    unboosted = adaptive_viscosity(signal, impulse_boost=0.0, zero_zone_boost=0.0)

    assert boosted.iloc[5] > unboosted.iloc[5]
