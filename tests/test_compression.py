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
