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
    "compression_score_v0",
    "compression_duration",
    "compression_stability",
    "flat_close_bars",
    "stale_data_flag",
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


def _consecutive_true(mask: pd.Series) -> pd.Series:
    output = []
    current = 0
    for value in mask.fillna(False).astype(bool):
        current = current + 1 if value else 0
        output.append(current)
    return pd.Series(output, index=mask.index, dtype="int64")


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
    output["compression_score_v0"] = output["compression_score"]
    compressed = output["compression_score_v0"] >= 70.0
    output["compression_duration"] = _consecutive_true(compressed)
    output["compression_stability"] = (
        compressed.astype(float)
        .rolling(settings.length, min_periods=1)
        .mean()
        .mul(100.0)
        .clip(lower=0.0, upper=100.0)
    )
    close_change = close.pct_change().abs()
    output["flat_close_bars"] = _consecutive_true((close_change <= 1e-12) & close.notna())
    if "volume" in ohlcv.columns:
        volume = pd.to_numeric(ohlcv["volume"], errors="coerce")
        no_volume = volume.fillna(0.0) <= 0.0
    else:
        no_volume = pd.Series(True, index=ohlcv.index)
    output["stale_data_flag"] = (
        (output["flat_close_bars"] >= settings.length)
        & (no_volume.rolling(settings.length, min_periods=1).mean() >= 0.8)
    )
    return output[COMPRESSION_COLUMNS]
