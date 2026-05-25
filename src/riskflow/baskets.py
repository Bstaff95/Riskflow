from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


BENCHMARK_DIAGNOSTIC_COLUMNS = [
    "basket_index",
    "average_return",
    "benchmark_active_members",
    "benchmark_missing_members",
    "benchmark_member_count",
    "benchmark_min_active_members",
    "benchmark_passed",
]


def build_equal_weight_return_index_frame(
    closes: Mapping[str, pd.Series],
    min_active_members: int = 3,
    start_value: float = 100.0,
    name: str = "BASKET",
) -> pd.DataFrame:
    if min_active_members < 1:
        raise ValueError("min_active_members must be >= 1")
    if not closes:
        raise ValueError("At least one close series is required")

    close_frame = pd.DataFrame({symbol: series.astype(float) for symbol, series in closes.items()}).sort_index()
    member_count = len(close_frame.columns)
    active_prices = close_frame.notna().sum(axis=1)
    returns = close_frame.pct_change(fill_method=None)
    active_returns = returns.notna().sum(axis=1)
    average_return = returns.mean(axis=1, skipna=True).where(active_returns >= min_active_members)

    index = pd.Series(np.nan, index=close_frame.index, name=name, dtype=float)
    valid_start_dates = active_prices[active_prices >= min_active_members].index
    if not valid_start_dates.empty:
        start_date = valid_start_dates[0]
        value = float(start_value)
        started = False
        for date in close_frame.index:
            if date < start_date:
                continue
            if not started:
                index.loc[date] = value
                started = True
                continue
            period_return = average_return.loc[date]
            if pd.isna(period_return):
                index.loc[date] = np.nan
                continue
            value *= 1.0 + float(period_return)
            index.loc[date] = value

    active_members = active_returns.where(active_returns > 0, active_prices)
    frame = pd.DataFrame(
        {
            "basket_index": index,
            "average_return": average_return,
            "benchmark_active_members": active_members.astype(int),
            "benchmark_missing_members": (member_count - active_members).clip(lower=0).astype(int),
            "benchmark_member_count": member_count,
            "benchmark_min_active_members": min_active_members,
            "benchmark_passed": index.notna() & (active_members >= min_active_members),
        },
        index=close_frame.index,
    )
    return frame[BENCHMARK_DIAGNOSTIC_COLUMNS]


def build_equal_weight_return_index(
    closes: Mapping[str, pd.Series],
    min_active_members: int = 3,
    start_value: float = 100.0,
    name: str = "BASKET",
) -> pd.Series:
    frame = build_equal_weight_return_index_frame(
        closes,
        min_active_members=min_active_members,
        start_value=start_value,
        name=name,
    )
    return frame["basket_index"].rename(name)
