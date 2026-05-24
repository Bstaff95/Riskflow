from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CompressionSettings
from .features import rolling_percentile_rank


COMPRESSION_COLUMNS = [
    "atr_pct",
    "range_pct",
    "realized_vol",
    "bollinger_width",
    "atr_pct_percentile",
    "range_pct_percentile",
    "realized_vol_percentile",
    "bollinger_width_percentile",
    "compression_score",
]


def calculate_atr(ohlcv: pd.DataFrame, length: int) -> pd.Series:
    high = pd.to_numeric(ohlcv["high"], errors="coerce")
    low = pd.to_numeric(ohlcv["low"], errors="coerce")
    close = pd.to_numeric(ohlcv["close"], errors="coerce")
    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1, skipna=True)
    return true_range.rolling(window=length, min_periods=1).mean()


def calculate_compression_features(
    ohlcv: pd.DataFrame,
    settings: CompressionSettings | None = None,
) -> pd.DataFrame:
    settings = settings or CompressionSettings()
    if settings.length < 1:
        raise ValueError("compression length must be >= 1")
    if settings.percentile_window < 1:
        raise ValueError("compression percentile_window must be >= 1")

    high = pd.to_numeric(ohlcv["high"], errors="coerce")
    low = pd.to_numeric(ohlcv["low"], errors="coerce")
    close = pd.to_numeric(ohlcv["close"], errors="coerce")

    output = pd.DataFrame(index=ohlcv.index)
    output["atr_pct"] = calculate_atr(ohlcv, settings.length) / close
    output["range_pct"] = (high.rolling(settings.length, min_periods=1).max() - low.rolling(settings.length, min_periods=1).min()) / close
    log_returns = np.log(close / close.shift(1))
    output["realized_vol"] = log_returns.rolling(settings.length, min_periods=2).std(ddof=0)
    rolling_mean = close.rolling(settings.length, min_periods=2).mean()
    rolling_std = close.rolling(settings.length, min_periods=2).std(ddof=0)
    output["bollinger_width"] = (4.0 * rolling_std) / rolling_mean

    feature_columns = ["atr_pct", "range_pct", "realized_vol", "bollinger_width"]
    percentile_columns = []
    for column in feature_columns:
        percentile_column = f"{column}_percentile"
        output[percentile_column] = rolling_percentile_rank(output[column], settings.percentile_window)
        percentile_columns.append(percentile_column)

    average_percentile = output[percentile_columns].mean(axis=1, skipna=True)
    output["compression_score"] = (100.0 - average_percentile).clip(lower=0.0, upper=100.0)
    return output[COMPRESSION_COLUMNS]

