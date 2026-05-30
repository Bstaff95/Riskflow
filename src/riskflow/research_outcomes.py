from __future__ import annotations

import numpy as np
import pandas as pd


HORIZONS = (3, 7, 14, 30)


def forward_return(
    series: pd.Series,
    horizon: int,
    entry_lag_bars: int = 0,
) -> pd.Series:
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if entry_lag_bars < 0:
        raise ValueError("entry_lag_bars must be >= 0")

    source = pd.to_numeric(series, errors="coerce").astype(float)
    entry = source.shift(-entry_lag_bars)
    exit_ = source.shift(-(entry_lag_bars + horizon))
    return exit_ / entry - 1.0


def forward_relative_return(
    target: pd.Series,
    benchmark: pd.Series,
    horizon: int,
    entry_lag_bars: int = 0,
) -> pd.Series:
    target_return = forward_return(target, horizon, entry_lag_bars)
    benchmark_return = forward_return(benchmark, horizon, entry_lag_bars)
    return ((1.0 + target_return) / (1.0 + benchmark_return)) - 1.0


def forward_max_drawdown(
    close: pd.Series,
    horizon: int,
    entry_lag_bars: int = 0,
) -> pd.Series:
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if entry_lag_bars < 0:
        raise ValueError("entry_lag_bars must be >= 0")

    values = pd.to_numeric(close, errors="coerce").to_numpy(dtype=float)
    output = np.full(len(values), np.nan, dtype=float)
    for idx in range(len(values)):
        entry_position = idx + entry_lag_bars
        if entry_position >= len(values):
            continue
        current = values[entry_position]
        if np.isnan(current) or current == 0.0:
            continue
        future = values[entry_position + 1 : entry_position + horizon + 1]
        future = future[~np.isnan(future)]
        if len(future) == 0:
            continue
        output[idx] = float(min(np.min(future / current - 1.0), 0.0))
    return pd.Series(output, index=close.index)


def forward_max_favorable_excursion(
    close: pd.Series,
    horizon: int,
    entry_lag_bars: int = 0,
) -> pd.Series:
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if entry_lag_bars < 0:
        raise ValueError("entry_lag_bars must be >= 0")

    values = pd.to_numeric(close, errors="coerce").to_numpy(dtype=float)
    output = np.full(len(values), np.nan, dtype=float)
    for idx in range(len(values)):
        entry_position = idx + entry_lag_bars
        if entry_position >= len(values):
            continue
        current = values[entry_position]
        if np.isnan(current) or current == 0.0:
            continue
        future = values[entry_position + 1 : entry_position + horizon + 1]
        future = future[~np.isnan(future)]
        if len(future) == 0:
            continue
        output[idx] = float(max(np.max(future / current - 1.0), 0.0))
    return pd.Series(output, index=close.index)


def entry_date_at(index: pd.Index, position: int, entry_lag_bars: int) -> object:
    entry_position = position + entry_lag_bars
    return index[entry_position] if entry_position < len(index) else pd.NaT


def apply_event_cooldown(mask: pd.Series, cooldown_bars: int) -> pd.Series:
    if cooldown_bars < 0:
        raise ValueError("cooldown_bars must be >= 0")
    events = mask.fillna(False).astype(bool)
    if cooldown_bars == 0:
        return events

    keep = pd.Series(False, index=events.index)
    last_kept_position: int | None = None
    for position, has_event in enumerate(events.to_numpy()):
        if not has_event:
            continue
        if last_kept_position is None or position - last_kept_position > cooldown_bars:
            keep.iloc[position] = True
            last_kept_position = position
    return keep


def event_cluster_id(date: object) -> str:
    return pd.Timestamp(date).strftime("%Y-%m")


def benchmark_label_at(frame: pd.DataFrame, date: object, default: str) -> str:
    for column in ("benchmark_used", "benchmark_name"):
        if column not in frame.columns:
            continue
        value = frame[column].loc[date]
        if pd.notna(value) and str(value):
            return str(value)
    return default


def mean_or_nan(series: pd.Series) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    return float(valid.mean()) if not valid.empty else np.nan


def median_or_nan(series: pd.Series) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    return float(valid.median()) if not valid.empty else np.nan


def quantile_or_nan(series: pd.Series, quantile: float) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    return float(valid.quantile(quantile)) if not valid.empty else np.nan


def std_or_nan(series: pd.Series) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    return float(valid.std(ddof=0)) if not valid.empty else np.nan


def hit_rate_or_nan(series: pd.Series) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    return float((valid > 0.0).mean()) if not valid.empty else np.nan


def max_share(series: pd.Series) -> float:
    valid = series.dropna()
    if valid.empty:
        return np.nan
    return float(valid.value_counts(normalize=True).iloc[0])


def split_half_medians(records: pd.DataFrame, column: str) -> tuple[float, float]:
    if records.empty or column not in records.columns:
        return np.nan, np.nan
    dates = pd.Series(pd.to_datetime(records["date"].dropna().unique())).sort_values(ignore_index=True)
    if dates.empty:
        return np.nan, np.nan
    midpoint = dates.iloc[len(dates) // 2]
    first = records[pd.to_datetime(records["date"]) <= midpoint]
    second = records[pd.to_datetime(records["date"]) > midpoint]
    return median_or_nan(first[column]), median_or_nan(second[column])


def worst_cluster_median(records: pd.DataFrame, column: str) -> float:
    if records.empty or column not in records.columns or "event_cluster_id" not in records.columns:
        return np.nan
    medians = records.groupby("event_cluster_id")[column].median(numeric_only=True)
    valid = medians.dropna()
    return float(valid.min()) if not valid.empty else np.nan
