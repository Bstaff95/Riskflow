import numpy as np
import pandas as pd

from riskflow.indicator_engine import INDICATOR_COLUMNS, calculate_indicator
from riskflow.signal_registry import CORE_SIGNAL_V0, get_signal_spec
from riskflow.signal_research import (
    RECORD_COLUMNS,
    SUMMARY_COLUMNS,
    build_signal_variant_frames,
    build_signal_research_records,
    cross_sectional_relative_rank,
    relative_percentile_strength,
    relative_vol_adjusted_momentum,
    summarize_signal_research_records,
    run_signal_research,
)


def _analysis_frame(symbol_bias: float = 0.0, periods: int = 90) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    target_returns = np.full(periods, 1.006 + symbol_bias)
    benchmark_returns = np.full(periods, 1.004)
    target = pd.Series(100.0 * np.cumprod(target_returns), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(benchmark_returns), index=dates)
    indicator = calculate_indicator(target, benchmark)
    return indicator


def test_relative_vol_adjusted_momentum_handles_zero_volatility_and_short_histories():
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    flat = pd.Series([0.0, 0.0, 0.0, 0.0, np.nan, 0.0], index=dates)

    result = relative_vol_adjusted_momentum(flat, lookback=2)

    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == 0.0
    assert result.iloc[3] == 0.0
    assert pd.isna(result.iloc[4])


def test_relative_percentile_strength_is_bounded():
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    relative_log = pd.Series(np.linspace(-2.0, 2.0, 20), index=dates)

    result = relative_percentile_strength(relative_log, lookback=5)

    assert result.dropna().between(0.0, 100.0).all()


def test_cross_sectional_rank_handles_missing_symbols_and_ties():
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    relative_logs = pd.DataFrame(
        {
            "AAA": [0.0, 0.1, 0.2, 0.3],
            "BBB": [0.0, 0.1, 0.2, 0.3],
            "CCC": [0.0, np.nan, np.nan, np.nan],
        },
        index=dates,
    )

    result = cross_sectional_relative_rank(relative_logs, lookback=1)

    assert result.loc[dates[1], "AAA"] == result.loc[dates[1], "BBB"]
    assert pd.isna(result.loc[dates[1], "CCC"])
    valid = result.stack().dropna()
    assert not valid.empty
    assert valid.between(0.0, 100.0).all()


def test_challenger_outputs_do_not_alter_indicator_contract():
    frame = _analysis_frame()
    original_columns = list(frame.columns)
    original_values = frame.copy(deep=True)

    variants = build_signal_variant_frames({"AAA": frame})

    assert list(frame.columns) == INDICATOR_COLUMNS
    assert original_columns == INDICATOR_COLUMNS
    pd.testing.assert_frame_equal(frame, original_values)
    assert "relative_vol_adj_momentum_20" in variants["AAA"].columns


def test_signal_research_output_includes_required_columns():
    frames = {
        "AAA": _analysis_frame(symbol_bias=0.001, periods=120),
        "BBB": _analysis_frame(symbol_bias=0.0, periods=120),
    }

    summary, records = run_signal_research(frames, timeframe="1d", benchmark_name="TEST_BASKET", min_sample_size=1)

    assert list(records.columns) == RECORD_COLUMNS
    assert list(summary.columns) == SUMMARY_COLUMNS
    assert {"signal_variant", "event_name", "classification"}.issubset(summary.columns)


def test_insufficient_sample_size_is_inconclusive():
    frames = {"AAA": _analysis_frame(symbol_bias=0.001, periods=60)}

    summary, _records = run_signal_research(frames, min_sample_size=999)

    if not summary.empty:
        assert set(summary["classification"]) == {"inconclusive"}


def test_signal_registry_freezes_core_signal_contract():
    spec = get_signal_spec(CORE_SIGNAL_V0)

    assert spec.role == "core"
    assert spec.trigger == 0.0
    assert spec.scale_type == "oscillator_z_like"
    assert "tradingview" in spec.allowed_downstream_use


def test_core_signal_v0_golden_values_are_stable():
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    target = pd.Series([10, 10.4, 10.2, 10.9, 11.5, 11.2, 12.0, 12.4], index=dates)
    benchmark = pd.Series([100, 100.5, 101, 101.2, 101.4, 101.6, 102, 102.5], index=dates)

    result = calculate_indicator(target, benchmark)

    expected = pd.Series(
        [0.0, 1.355575, -0.153261, 2.114944, 2.240054, 1.23759, 2.176793, 2.153236],
        index=dates,
        name="final_signal",
    )
    pd.testing.assert_series_equal(result["final_signal"].round(6), expected)


def test_event_cooldown_reduces_overlapping_research_events():
    dates = pd.date_range("2024-01-01", periods=12, freq="D")
    frame = pd.DataFrame(
        {
            "target": np.linspace(100.0, 111.0, 12),
            "benchmark": np.full(12, 100.0),
            "final_signal": [-1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0],
            "target_norm": np.linspace(1.0, 1.11, 12),
            "benchmark_norm": np.ones(12),
            "relative_log": np.linspace(0.0, 0.1, 12),
        },
        index=dates,
    )

    no_cooldown = build_signal_research_records({"AAA": frame}, cooldown_bars=0, entry_lag_bars=1)
    with_cooldown = build_signal_research_records({"AAA": frame}, cooldown_bars=3, entry_lag_bars=1)

    no_cooldown_core = no_cooldown[no_cooldown["signal_variant"] == CORE_SIGNAL_V0]
    cooldown_core = with_cooldown[with_cooldown["signal_variant"] == CORE_SIGNAL_V0]
    assert len(cooldown_core) < len(no_cooldown_core)


def test_entry_lag_starts_forward_return_after_signal_bar():
    dates = pd.date_range("2024-01-01", periods=7, freq="D")
    frame = pd.DataFrame(
        {
            "target": [100.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
            "benchmark": [100.0] * 7,
            "final_signal": [-1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "target_norm": [1.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "benchmark_norm": [1.0] * 7,
            "relative_log": np.log([1.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]),
        },
        index=dates,
    )

    records = build_signal_research_records({"AAA": frame}, cooldown_bars=0, entry_lag_bars=1)
    core_event = records[records["signal_variant"] == CORE_SIGNAL_V0].iloc[0]

    assert core_event["entry_date"] == dates[2]
    assert core_event["forward_relative_return_3"] == 1.5


def test_one_symbol_dominance_forces_inconclusive():
    records = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i * 40),
                "timeframe": "1d",
                "benchmark": "TEST",
                "signal_variant": "relative_vol_adj_momentum_20",
                "signal_role": "challenger",
                "signal_version": 0,
                "lookback": 20,
                "signal_value": 1.2,
                "event_name": "relative_vol_adj_momentum_20_crosses_above_trigger",
                "entry_lag_bars": 1,
                "entry_date": pd.Timestamp("2024-01-02") + pd.Timedelta(days=i * 40),
                "event_cluster_id": f"2024-{i + 1:02d}",
                "forward_relative_return_3": 0.01,
                "forward_relative_return_7": 0.01,
                "forward_relative_return_14": 0.01,
                "forward_relative_return_30": 0.01,
                "max_drawdown_14": -0.01,
                "max_drawdown_30": -0.01,
            }
            for i in range(3)
        ]
    )

    summary = summarize_signal_research_records(records, min_sample_size=1)

    assert summary.iloc[0]["classification"] == "inconclusive"
    assert "one symbol" in summary.iloc[0]["notes"]
