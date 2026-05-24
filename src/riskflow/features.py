from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    """Bootstrap rolling z-score with zero for valid flat windows."""
    if window < 1:
        raise ValueError("window must be >= 1")

    source = pd.to_numeric(series, errors="coerce").astype(float)
    mean = source.rolling(window=window, min_periods=1).mean()
    std = source.rolling(window=window, min_periods=1).std(ddof=0)
    zscore = (source - mean) / std.replace(0.0, np.nan)
    zscore = zscore.where(~(source.notna() & (std.isna() | (std == 0.0))), 0.0)
    return zscore.where(source.notna())


def clamp_series(series: pd.Series, limit: float) -> pd.Series:
    if limit <= 0:
        raise ValueError("limit must be positive")
    return series.clip(lower=-limit, upper=limit)


def safe_log(series: pd.Series) -> pd.Series:
    source = pd.to_numeric(series, errors="coerce").astype(float)
    return np.log(source.where(source > 0.0))


def normalize_to_first_valid(series: pd.Series) -> pd.Series:
    source = pd.to_numeric(series, errors="coerce").astype(float)
    valid = source[source > 0.0].dropna()
    if valid.empty:
        return pd.Series(np.nan, index=source.index, name=source.name)
    return source / valid.iloc[0]


def rolling_percentile_rank(series: pd.Series, window: int) -> pd.Series:
    """Percentile rank of the latest value against its trailing history."""
    if window < 1:
        raise ValueError("window must be >= 1")

    source = pd.to_numeric(series, errors="coerce").astype(float)

    def percentile(values: pd.Series) -> float:
        latest = values.iloc[-1]
        valid = values.dropna()
        if pd.isna(latest) or valid.empty:
            return np.nan
        return float((valid <= latest).sum() / len(valid) * 100.0)

    return source.rolling(window=window, min_periods=1).apply(percentile, raw=False)

