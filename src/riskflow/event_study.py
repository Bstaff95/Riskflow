from __future__ import annotations

import numpy as np
import pandas as pd

from .event_registry import DEFAULT_EVENT_COOLDOWN_BARS, DEFAULT_EVENT_ENTRY_LAG_BARS, EVENT_REGISTRY, get_event_spec
from .research_outcomes import (
    HORIZONS,
    apply_event_cooldown,
    entry_date_at,
    event_cluster_id,
    forward_max_drawdown,
    forward_relative_return,
    forward_return,
    hit_rate_or_nan,
    max_share,
    mean_or_nan,
    median_or_nan,
    quantile_or_nan,
    split_half_medians,
    worst_cluster_median,
)


DEFAULT_MIN_SAMPLE_SIZE = 20
MAX_SYMBOL_EVENT_SHARE = 0.55
MAX_CLUSTER_EVENT_SHARE = 0.60

EVENT_NAMES = (
    "signal_crosses_above_viscosity",
    "signal_crosses_above_zero",
    "relative_component_crosses_above_zero",
    "final_signal_reclaims_minus_1_5",
    "compression_80_relative_rising",
    "state_becomes_emerging_leader",
    "state_becomes_confirmed_leader",
    "signal_crosses_below_viscosity",
    "signal_fails_near_zero",
    "compression_score_above_80",
    "compression_duration_above_threshold",
    "compression_plus_relative_rising",
    "setup_readiness_score_crosses_threshold",
    "relative_accumulation_score_crosses_threshold",
    "compressed_viscosity_reclaim",
    "compressed_zero_reclaim",
    "extension_risk_score_crosses_high",
)

RECORD_COLUMNS = [
    "symbol",
    "date",
    "timeframe",
    "benchmark",
    "event",
    "event_id",
    "event_family",
    "event_version",
    "event_value",
    "entry_lag_bars",
    "entry_date",
    "cooldown_bars",
    "event_cluster_id",
    "forward_return_3",
    "forward_relative_return_3",
    "forward_return_7",
    "forward_relative_return_7",
    "forward_return_14",
    "forward_relative_return_14",
    "forward_return_30",
    "forward_relative_return_30",
    "max_drawdown_14",
    "max_drawdown_30",
]


def summary_columns() -> list[str]:
    columns = ["event", "sample_size"]
    for horizon in HORIZONS:
        columns.extend(
            [
                f"avg_forward_return_{horizon}",
                f"median_forward_return_{horizon}",
                f"avg_forward_relative_return_{horizon}",
                f"median_forward_relative_return_{horizon}",
                f"hit_rate_forward_relative_return_{horizon}",
            ]
        )
    columns.extend(
        [
            "avg_max_drawdown_14",
            "median_max_drawdown_14",
            "avg_max_drawdown_30",
            "median_max_drawdown_30",
            "event_id",
            "event_family",
            "event_version",
            "unique_symbols",
            "unique_event_dates",
            "unique_event_clusters",
            "max_symbol_event_share",
            "max_cluster_event_share",
        ]
    )
    for horizon in HORIZONS:
        columns.extend(
            [
                f"p25_forward_relative_return_{horizon}",
                f"p75_forward_relative_return_{horizon}",
            ]
        )
    columns.extend(
        [
            "first_half_median_forward_relative_return_30",
            "second_half_median_forward_relative_return_30",
            "worst_cluster_median_forward_relative_return_30",
            "classification",
            "notes",
        ]
    )
    return columns


def _crosses_above(series: pd.Series, threshold: float) -> pd.Series:
    return (series > threshold) & (series.shift(1) <= threshold)


def _crosses_below(series: pd.Series, threshold: float) -> pd.Series:
    return (series < threshold) & (series.shift(1) >= threshold)


def _optional_numeric(frame: pd.DataFrame, column: str, default: float = np.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def detect_events(frame: pd.DataFrame) -> dict[str, pd.Series]:
    final_signal = frame["final_signal"]
    relative = frame["relative_component"]
    viscosity = frame["viscosity"]
    compression = frame["compression_score"]
    compression_duration = _optional_numeric(frame, "compression_duration", default=0.0)
    setup_readiness = _optional_numeric(frame, "setup_readiness_score", default=0.0)
    relative_accumulation = _optional_numeric(frame, "relative_accumulation_score", default=0.0)
    extension_risk = _optional_numeric(frame, "extension_risk_score", default=0.0)
    state = frame["state"].astype("string")
    above_viscosity = final_signal > viscosity
    previous_above_viscosity = above_viscosity.shift(1, fill_value=False).astype(bool)
    viscosity_reclaim = (above_viscosity & ~previous_above_viscosity).fillna(False)
    zero_reclaim = _crosses_above(final_signal, 0.0).fillna(False)

    return {
        "signal_crosses_above_viscosity": viscosity_reclaim,
        "signal_crosses_above_zero": zero_reclaim,
        "relative_component_crosses_above_zero": _crosses_above(relative, 0.0).fillna(False),
        "final_signal_reclaims_minus_1_5": _crosses_above(final_signal, -1.5).fillna(False),
        "compression_80_relative_rising": ((compression >= 80.0) & (relative.diff() > 0.0)).fillna(False),
        "state_becomes_emerging_leader": ((state == "Emerging Leader") & (state.shift(1) != "Emerging Leader")).fillna(False),
        "state_becomes_confirmed_leader": ((state == "Confirmed Leader") & (state.shift(1) != "Confirmed Leader")).fillna(False),
        "signal_crosses_below_viscosity": ((~above_viscosity) & previous_above_viscosity).fillna(False),
        "signal_fails_near_zero": (
            (final_signal < 0.0)
            & final_signal.shift(1).between(-0.25, 0.25)
            & (final_signal.diff() < 0.0)
        ).fillna(False),
        "compression_score_above_80": _crosses_above(compression, 80.0).fillna(False),
        "compression_duration_above_threshold": _crosses_above(compression_duration, 5.0).fillna(False),
        "compression_plus_relative_rising": ((compression >= 70.0) & (relative.diff() > 0.0)).fillna(False),
        "setup_readiness_score_crosses_threshold": _crosses_above(setup_readiness, 70.0).fillna(False),
        "relative_accumulation_score_crosses_threshold": _crosses_above(relative_accumulation, 65.0).fillna(False),
        "compressed_viscosity_reclaim": ((compression >= 70.0) & viscosity_reclaim).fillna(False),
        "compressed_zero_reclaim": ((compression >= 70.0) & zero_reclaim).fillna(False),
        "extension_risk_score_crosses_high": _crosses_above(extension_risk, 70.0).fillna(False),
    }


def _event_value(frame: pd.DataFrame, event_name: str, event_date: pd.Timestamp) -> object:
    spec = get_event_spec(event_name)
    column = spec.value_column
    if column is None or column not in frame.columns:
        return np.nan
    return frame[column].loc[event_date]


def event_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = DEFAULT_EVENT_ENTRY_LAG_BARS,
    cooldown_bars: int = DEFAULT_EVENT_COOLDOWN_BARS,
) -> pd.DataFrame:
    working = frame.copy()
    target = pd.to_numeric(working["target"], errors="coerce").astype(float)
    benchmark = pd.to_numeric(working["benchmark"], errors="coerce").astype(float)
    masks = detect_events(working)

    metric_frame = pd.DataFrame(index=working.index)
    for horizon in HORIZONS:
        metric_frame[f"forward_return_{horizon}"] = forward_return(target, horizon, entry_lag_bars)
        metric_frame[f"forward_relative_return_{horizon}"] = forward_relative_return(
            target,
            benchmark,
            horizon,
            entry_lag_bars,
        )
    metric_frame["max_drawdown_14"] = forward_max_drawdown(target, 14, entry_lag_bars)
    metric_frame["max_drawdown_30"] = forward_max_drawdown(target, 30, entry_lag_bars)

    records: list[dict[str, object]] = []
    for event_name, raw_mask in masks.items():
        spec = get_event_spec(event_name)
        mask = apply_event_cooldown(raw_mask, cooldown_bars)
        event_dates = working.index[mask]
        for event_date in event_dates:
            event_position = working.index.get_loc(event_date)
            record: dict[str, object] = {
                "symbol": symbol,
                "date": event_date,
                "timeframe": timeframe,
                "benchmark": benchmark_name,
                "event": event_name,
                "event_id": event_name,
                "event_family": spec.family,
                "event_version": spec.version,
                "event_value": _event_value(working, event_name, event_date),
                "entry_lag_bars": entry_lag_bars,
                "entry_date": entry_date_at(working.index, event_position, entry_lag_bars),
                "cooldown_bars": cooldown_bars,
                "event_cluster_id": event_cluster_id(event_date),
            }
            for column in metric_frame.columns:
                record[column] = metric_frame.loc[event_date, column]
            records.append(record)
    return pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)


def _classify_summary_row(row: dict[str, object], spec, *, min_sample_size: int) -> tuple[str, str]:
    sample_size = int(row["sample_size"])
    if sample_size < min_sample_size:
        return "inconclusive", f"sample size below min_sample_size={min_sample_size}"
    if float(row["max_symbol_event_share"]) > MAX_SYMBOL_EVENT_SHARE:
        return "fragile", "too many events come from one symbol"
    if float(row["max_cluster_event_share"]) > MAX_CLUSTER_EVENT_SHARE:
        return "fragile", "too many events come from one calendar cluster"

    median_14 = float(row["median_forward_relative_return_14"])
    median_30 = float(row["median_forward_relative_return_30"])
    hit_14 = float(row["hit_rate_forward_relative_return_14"])
    drawdown_30 = float(row["median_max_drawdown_30"])
    if any(np.isnan(value) for value in (median_14, median_30, hit_14)):
        return "inconclusive", "insufficient forward-relative-return evidence"
    acceptable_drawdown = np.isnan(drawdown_30) or drawdown_30 > -0.35
    if spec.direction == "negative":
        miss_rate_14 = 1.0 - hit_14
        if median_14 < 0.0 and median_30 < 0.0 and miss_rate_14 >= 0.55:
            return "useful", "negative event preceded underperformance with enough consistency"
        if median_14 < 0.0 or median_30 < 0.0 or miss_rate_14 >= 0.52:
            return "watchlist", "mixed but potentially useful downside evidence"
        return "fragile", "negative event did not precede underperformance"

    if median_14 > 0.0 and median_30 > 0.0 and hit_14 >= 0.55 and acceptable_drawdown:
        return "useful", "positive median relative returns, hit rate, and drawdown evidence"
    if (median_14 > 0.0 or median_30 > 0.0 or hit_14 >= 0.52) and acceptable_drawdown:
        return "watchlist", "mixed but potentially useful upside evidence"
    return "fragile", "positive event has weak or negative forward relative-return evidence"


def summarize_event_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for event_name in EVENT_NAMES:
        spec = EVENT_REGISTRY[event_name]
        event_records = records[records["event"] == event_name] if not records.empty else pd.DataFrame()
        row: dict[str, object] = {
            "event": event_name,
            "sample_size": int(len(event_records)),
        }
        for horizon in HORIZONS:
            forward = event_records.get(f"forward_return_{horizon}", pd.Series(dtype=float))
            relative = event_records.get(f"forward_relative_return_{horizon}", pd.Series(dtype=float))
            row[f"avg_forward_return_{horizon}"] = mean_or_nan(forward)
            row[f"median_forward_return_{horizon}"] = median_or_nan(forward)
            row[f"avg_forward_relative_return_{horizon}"] = mean_or_nan(relative)
            row[f"median_forward_relative_return_{horizon}"] = median_or_nan(relative)
            row[f"hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(relative)
        for horizon in (14, 30):
            drawdown = event_records.get(f"max_drawdown_{horizon}", pd.Series(dtype=float))
            row[f"avg_max_drawdown_{horizon}"] = mean_or_nan(drawdown)
            row[f"median_max_drawdown_{horizon}"] = median_or_nan(drawdown)

        row.update(
            {
                "event_id": event_name,
                "event_family": spec.family,
                "event_version": spec.version,
                "unique_symbols": int(event_records["symbol"].nunique()) if not event_records.empty else 0,
                "unique_event_dates": int(event_records["date"].nunique()) if not event_records.empty else 0,
                "unique_event_clusters": int(event_records["event_cluster_id"].nunique()) if not event_records.empty else 0,
                "max_symbol_event_share": max_share(event_records["symbol"]) if not event_records.empty else np.nan,
                "max_cluster_event_share": max_share(event_records["event_cluster_id"]) if not event_records.empty else np.nan,
            }
        )
        for horizon in HORIZONS:
            relative = event_records.get(f"forward_relative_return_{horizon}", pd.Series(dtype=float))
            row[f"p25_forward_relative_return_{horizon}"] = quantile_or_nan(relative, 0.25)
            row[f"p75_forward_relative_return_{horizon}"] = quantile_or_nan(relative, 0.75)
        first_half, second_half = split_half_medians(event_records, "forward_relative_return_30")
        row["first_half_median_forward_relative_return_30"] = first_half
        row["second_half_median_forward_relative_return_30"] = second_half
        row["worst_cluster_median_forward_relative_return_30"] = worst_cluster_median(
            event_records,
            "forward_relative_return_30",
        )
        row["classification"], row["notes"] = _classify_summary_row(row, spec, min_sample_size=min_sample_size)
        rows.append(row)

    return pd.DataFrame(rows, columns=summary_columns())


def run_event_study(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    entry_lag_bars: int = DEFAULT_EVENT_ENTRY_LAG_BARS,
    cooldown_bars: int = DEFAULT_EVENT_COOLDOWN_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = [
        event_records_for_asset(
            symbol,
            frame,
            timeframe=timeframe,
            benchmark_name=benchmark_name,
            entry_lag_bars=entry_lag_bars,
            cooldown_bars=cooldown_bars,
        )
        for symbol, frame in analysis_frames.items()
        if not frame.empty
    ]
    event_records = pd.concat(records, ignore_index=True) if records else pd.DataFrame(columns=RECORD_COLUMNS)
    return summarize_event_records(event_records, min_sample_size=min_sample_size), event_records
