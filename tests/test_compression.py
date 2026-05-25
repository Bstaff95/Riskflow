import pandas as pd

from riskflow.compression import calculate_compression_features


def test_compression_score_is_bounded_0_to_100():
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    close = pd.Series([100.0 + idx * 0.5 for idx in range(40)], index=dates)
    ohlcv = pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": 1000.0,
        },
        index=dates,
    )

    result = calculate_compression_features(ohlcv)
    score = result["compression_score"].dropna()

    assert not score.empty
    assert score.between(0.0, 100.0).all()


def test_compression_duration_counts_sustained_compression():
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    close = pd.Series(
        [100, 102, 98, 103, 97, 104, 96, 105, 95, 106] + [100.0 + idx * 0.01 for idx in range(30)],
        index=dates,
    )
    ohlcv = pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1000.0,
        },
        index=dates,
    )

    result = calculate_compression_features(ohlcv)

    assert "compression_score_v0" in result.columns
    assert "compression_duration" in result.columns
    assert result["compression_duration"].iloc[-1] >= result["compression_duration"].iloc[-5]
    assert result["compression_stability"].dropna().between(0.0, 100.0).all()


def test_stale_flat_data_is_flagged():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    close = pd.Series(100.0, index=dates)
    ohlcv = pd.DataFrame(
        {
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 0.0,
        },
        index=dates,
    )

    result = calculate_compression_features(ohlcv)

    assert bool(result["stale_data_flag"].iloc[-1])
