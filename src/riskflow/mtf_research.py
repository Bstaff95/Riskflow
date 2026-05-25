from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .mtf import MTF_CONTEXT_MODEL_V0
from .research_outcomes import (
    HORIZONS,
    apply_event_cooldown,
    benchmark_label_at,
    entry_date_at,
    event_cluster_id,
    forward_max_drawdown,
    forward_relative_return,
    hit_rate_or_nan,
    max_share,
    mean_or_nan,
    median_or_nan,
)


DEFAULT_MIN_SAMPLE_SIZE = 20
DEFAULT_ENTRY_LAG_BARS = 1
DEFAULT_COOLDOWN_BARS = 30
MAX_SYMBOL_SHARE = 0.55
MAX_CLUSTER_SHARE = 0.60

MTF_EVENT_NAMES = (
    "state_relative_accumulation",
    "state_emerging_leader",
    "compressed_viscosity_reclaim",
    "compressed_zero_reclaim",
    "setup_readiness_above_70",
)

RECORD_COLUMNS = [
    "symbol",
    "date",
    "timeframe",
    "benchmark",
    "mtf_context_model",
    "mtf_event",
    "mtf_support_group",
    "mtf_leader_context",
    "mtf_trader_context",
    "mtf_alignment_tags",
    "mtf_conflict_tags",
    "event_value",
    "entry_lag_bars",
    "entry_date",
    "cooldown_bars",
    "event_cluster_id",
    "forward_relative_return_3",
    "forward_relative_return_7",
    "forward_relative_return_14",
    "forward_relative_return_30",
    "max_drawdown_14",
    "max_drawdown_30",
]

SUMMARY_COLUMNS = [
    "mtf_event",
    "sample_size",
    "aligned_sample_size",
    "non_aligned_sample_size",
    "incomplete_sample_size",
    "unique_symbols",
    "unique_event_dates",
    "unique_event_clusters",
    "max_symbol_share",
    "max_cluster_share",
    "aligned_median_forward_relative_return_14",
    "non_aligned_median_forward_relative_return_14",
    "aligned_minus_non_aligned_spread_14",
    "aligned_hit_rate_forward_relative_return_14",
    "non_aligned_hit_rate_forward_relative_return_14",
    "aligned_median_forward_relative_return_30",
    "non_aligned_median_forward_relative_return_30",
    "aligned_minus_non_aligned_spread_30",
    "aligned_hit_rate_forward_relative_return_30",
    "non_aligned_hit_rate_forward_relative_return_30",
    "aligned_median_max_drawdown_14",
    "non_aligned_median_max_drawdown_14",
    "aligned_median_max_drawdown_30",
    "non_aligned_median_max_drawdown_30",
    "classification",
    "notes",
]


def _crosses_above(series: pd.Series, threshold: float) -> pd.Series:
    return (series > threshold) & (series.shift(1) <= threshold)


def _detect_mtf_events(frame: pd.DataFrame) -> dict[str, pd.Series]:
    final_signal = pd.to_numeric(frame.get("final_signal"), errors="coerce")
    viscosity = pd.to_numeric(frame.get("viscosity"), errors="coerce")
    compression = pd.to_numeric(frame.get("compression_score"), errors="coerce")
    setup_readiness = pd.to_numeric(frame.get("setup_readiness_score"), errors="coerce")
    state = frame.get("state", pd.Series(index=frame.index, dtype=object)).astype("string")
    above_viscosity = final_signal > viscosity
    viscosity_reclaim = above_viscosity & ~above_viscosity.shift(1, fill_value=False).astype(bool)
    zero_reclaim = _crosses_above(final_signal, 0.0)
    return {
        "state_relative_accumulation": ((state == "Relative Accumulation") & (state.shift(1) != "Relative Accumulation")).fillna(False),
        "state_emerging_leader": ((state == "Emerging Leader") & (state.shift(1) != "Emerging Leader")).fillna(False),
        "compressed_viscosity_reclaim": ((compression >= 70.0) & viscosity_reclaim).fillna(False),
        "compressed_zero_reclaim": ((compression >= 70.0) & zero_reclaim).fillna(False),
        "setup_readiness_above_70": _crosses_above(setup_readiness, 70.0).fillna(False),
    }


def _event_value(frame: pd.DataFrame, event_name: str, date: pd.Timestamp) -> object:
    column = {
        "state_relative_accumulation": "state",
        "state_emerging_leader": "state",
        "compressed_viscosity_reclaim": "compression_score",
        "compressed_zero_reclaim": "compression_score",
        "setup_readiness_above_70": "setup_readiness_score",
    }[event_name]
    return frame[column].loc[date] if column in frame.columns else np.nan


def _support_group(row: pd.Series) -> str:
    if not bool(row.get("mtf_context_available", False)):
        return "incomplete"
    leader_context = str(row.get("mtf_leader_context", ""))
    alignment_tags = str(row.get("mtf_alignment_tags", ""))
    if leader_context in {"Aligned Leader", "Early HTF Turn"} or "htf_supportive" in alignment_tags:
        return "aligned"
    return "non_aligned"


def mtf_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
    cooldown_bars: int = DEFAULT_COOLDOWN_BARS,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=RECORD_COLUMNS)

    target = pd.to_numeric(frame.get("target"), errors="coerce").astype(float)
    benchmark = pd.to_numeric(frame.get("benchmark"), errors="coerce").astype(float)
    metrics = pd.DataFrame(index=frame.index)
    for horizon in HORIZONS:
        metrics[f"forward_relative_return_{horizon}"] = forward_relative_return(
            target,
            benchmark,
            horizon,
            entry_lag_bars,
        )
    metrics["max_drawdown_14"] = forward_max_drawdown(target, 14, entry_lag_bars)
    metrics["max_drawdown_30"] = forward_max_drawdown(target, 30, entry_lag_bars)

    records: list[dict[str, object]] = []
    for event_name, raw_mask in _detect_mtf_events(frame).items():
        mask = apply_event_cooldown(raw_mask, cooldown_bars)
        for event_date in frame.index[mask]:
            event_position = frame.index.get_loc(event_date)
            row = frame.loc[event_date]
            record: dict[str, object] = {
                "symbol": symbol,
                "date": event_date,
                "timeframe": timeframe,
                "benchmark": benchmark_label_at(frame, event_date, benchmark_name),
                "mtf_context_model": MTF_CONTEXT_MODEL_V0,
                "mtf_event": event_name,
                "mtf_support_group": _support_group(row),
                "mtf_leader_context": row.get("mtf_leader_context"),
                "mtf_trader_context": row.get("mtf_trader_context"),
                "mtf_alignment_tags": row.get("mtf_alignment_tags"),
                "mtf_conflict_tags": row.get("mtf_conflict_tags"),
                "event_value": _event_value(frame, event_name, event_date),
                "entry_lag_bars": entry_lag_bars,
                "entry_date": entry_date_at(frame.index, event_position, entry_lag_bars),
                "cooldown_bars": cooldown_bars,
                "event_cluster_id": event_cluster_id(event_date),
            }
            for column in metrics.columns:
                record[column] = metrics.loc[event_date, column]
            records.append(record)
    return pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)


def build_mtf_research_records(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
    cooldown_bars: int = DEFAULT_COOLDOWN_BARS,
) -> pd.DataFrame:
    records = [
        mtf_records_for_asset(
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
    non_empty = [record for record in records if not record.empty]
    return pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame(columns=RECORD_COLUMNS)


def _group(records: pd.DataFrame, event_name: str, group_name: str) -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(columns=RECORD_COLUMNS)
    return records[(records["mtf_event"] == event_name) & (records["mtf_support_group"] == group_name)]


def _spread(aligned: pd.DataFrame, non_aligned: pd.DataFrame, column: str) -> float:
    aligned_median = median_or_nan(aligned.get(column, pd.Series(dtype=float)))
    non_aligned_median = median_or_nan(non_aligned.get(column, pd.Series(dtype=float)))
    if pd.isna(aligned_median) or pd.isna(non_aligned_median):
        return np.nan
    return float(aligned_median - non_aligned_median)


def _classify_row(row: dict[str, object], *, min_sample_size: int) -> tuple[str, str]:
    aligned_n = int(row["aligned_sample_size"])
    non_aligned_n = int(row["non_aligned_sample_size"])
    if aligned_n < min_sample_size or non_aligned_n < min_sample_size:
        return "inconclusive", f"aligned and non-aligned groups both need min_sample_size={min_sample_size}"
    if float(row["max_symbol_share"]) > MAX_SYMBOL_SHARE:
        return "fragile", "too many observations come from one symbol"
    if float(row["max_cluster_share"]) > MAX_CLUSTER_SHARE:
        return "fragile", "too many observations come from one calendar cluster"

    spread_14 = float(row["aligned_minus_non_aligned_spread_14"])
    spread_30 = float(row["aligned_minus_non_aligned_spread_30"])
    aligned_hit_14 = float(row["aligned_hit_rate_forward_relative_return_14"])
    non_aligned_hit_14 = float(row["non_aligned_hit_rate_forward_relative_return_14"])
    aligned_drawdown_30 = float(row["aligned_median_max_drawdown_30"])
    non_aligned_drawdown_30 = float(row["non_aligned_median_max_drawdown_30"])
    values = (spread_14, spread_30, aligned_hit_14, non_aligned_hit_14)
    if any(math.isnan(value) for value in values):
        return "inconclusive", "comparison evidence unavailable"

    hit_preserved = aligned_hit_14 + 0.02 >= non_aligned_hit_14
    drawdown_ok = (
        math.isnan(aligned_drawdown_30)
        or math.isnan(non_aligned_drawdown_30)
        or aligned_drawdown_30 >= non_aligned_drawdown_30 - 0.05
    )
    if spread_14 > 0.0 and spread_30 > 0.0 and hit_preserved and drawdown_ok:
        return "useful", "aligned context improved median outcomes without obvious hit-rate/drawdown damage"
    if (spread_14 > 0.0 or spread_30 > 0.0) and hit_preserved:
        return "watchlist", "mixed but potentially useful MTF alignment evidence"
    return "fragile", "MTF alignment did not improve the matched single-timeframe baseline"


def summarize_mtf_research_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for event_name in MTF_EVENT_NAMES:
        event_records = records[records["mtf_event"] == event_name] if not records.empty else pd.DataFrame(columns=RECORD_COLUMNS)
        aligned = _group(records, event_name, "aligned")
        non_aligned = _group(records, event_name, "non_aligned")
        incomplete = _group(records, event_name, "incomplete")
        row: dict[str, object] = {
            "mtf_event": event_name,
            "sample_size": int(len(event_records)),
            "aligned_sample_size": int(len(aligned)),
            "non_aligned_sample_size": int(len(non_aligned)),
            "incomplete_sample_size": int(len(incomplete)),
            "unique_symbols": int(event_records["symbol"].nunique()) if not event_records.empty else 0,
            "unique_event_dates": int(event_records["date"].nunique()) if not event_records.empty else 0,
            "unique_event_clusters": int(event_records["event_cluster_id"].nunique()) if not event_records.empty else 0,
            "max_symbol_share": max_share(event_records["symbol"]) if not event_records.empty else np.nan,
            "max_cluster_share": max_share(event_records["event_cluster_id"]) if not event_records.empty else np.nan,
        }
        for horizon in (14, 30):
            column = f"forward_relative_return_{horizon}"
            row[f"aligned_median_forward_relative_return_{horizon}"] = median_or_nan(aligned.get(column, pd.Series(dtype=float)))
            row[f"non_aligned_median_forward_relative_return_{horizon}"] = median_or_nan(non_aligned.get(column, pd.Series(dtype=float)))
            row[f"aligned_minus_non_aligned_spread_{horizon}"] = _spread(aligned, non_aligned, column)
            row[f"aligned_hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(aligned.get(column, pd.Series(dtype=float)))
            row[f"non_aligned_hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(non_aligned.get(column, pd.Series(dtype=float)))
            drawdown_column = f"max_drawdown_{horizon}"
            row[f"aligned_median_max_drawdown_{horizon}"] = median_or_nan(aligned.get(drawdown_column, pd.Series(dtype=float)))
            row[f"non_aligned_median_max_drawdown_{horizon}"] = median_or_nan(
                non_aligned.get(drawdown_column, pd.Series(dtype=float)),
            )
        row["classification"], row["notes"] = _classify_row(row, min_sample_size=min_sample_size)
        rows.append(row)
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def run_mtf_research(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
    cooldown_bars: int = DEFAULT_COOLDOWN_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = build_mtf_research_records(
        analysis_frames,
        timeframe=timeframe,
        benchmark_name=benchmark_name,
        entry_lag_bars=entry_lag_bars,
        cooldown_bars=cooldown_bars,
    )
    return summarize_mtf_research_records(records, min_sample_size=min_sample_size), records
