from __future__ import annotations

import numpy as np
import pandas as pd

from .event_study import HORIZONS
from .signal_research import (
    _apply_event_cooldown,
    _forward_max_drawdown,
    _future_relative_return,
)


SETUP_EVENT_NAMES = (
    "compression_score_above_80",
    "compression_duration_above_threshold",
    "compression_plus_relative_rising",
    "setup_readiness_score_crosses_threshold",
    "relative_accumulation_score_crosses_threshold",
    "compressed_viscosity_reclaim",
    "compressed_zero_reclaim",
    "extension_risk_score_crosses_high",
    "trader_score_crosses_threshold",
)
RECORD_COLUMNS = [
    "symbol",
    "date",
    "timeframe",
    "benchmark",
    "setup_event",
    "setup_value",
    "entry_lag_bars",
    "entry_date",
    "event_cluster_id",
    "forward_relative_return_3",
    "forward_relative_return_7",
    "forward_relative_return_14",
    "forward_relative_return_30",
    "max_drawdown_14",
    "max_drawdown_30",
]
SUMMARY_COLUMNS = [
    "setup_event",
    "sample_size",
    "unique_symbols",
    "unique_event_dates",
    "unique_event_clusters",
    "max_symbol_event_share",
    "max_cluster_event_share",
    "avg_forward_relative_return_3",
    "median_forward_relative_return_3",
    "hit_rate_forward_relative_return_3",
    "avg_forward_relative_return_7",
    "median_forward_relative_return_7",
    "hit_rate_forward_relative_return_7",
    "avg_forward_relative_return_14",
    "median_forward_relative_return_14",
    "hit_rate_forward_relative_return_14",
    "avg_forward_relative_return_30",
    "median_forward_relative_return_30",
    "hit_rate_forward_relative_return_30",
    "avg_max_drawdown_14",
    "median_max_drawdown_14",
    "avg_max_drawdown_30",
    "median_max_drawdown_30",
    "classification",
    "notes",
]
DEFAULT_SETUP_RESEARCH_COOLDOWN_BARS = 30
DEFAULT_SETUP_RESEARCH_ENTRY_LAG_BARS = 1
DEFAULT_MIN_SAMPLE_SIZE = 5
MAX_SYMBOL_EVENT_SHARE = 0.55
MAX_CLUSTER_EVENT_SHARE = 0.60


def _numeric(frame: pd.DataFrame, column: str, default: float = np.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _crosses_above(series: pd.Series, threshold: float) -> pd.Series:
    return ((series > threshold) & (series.shift(1) <= threshold)).fillna(False)


def detect_setup_events(frame: pd.DataFrame) -> dict[str, pd.Series]:
    final_signal = _numeric(frame, "final_signal")
    viscosity = _numeric(frame, "viscosity")
    compression = _numeric(frame, "compression_score_v0")
    if compression.isna().all():
        compression = _numeric(frame, "compression_score")
    relative_component = _numeric(frame, "relative_component")
    compression_duration = _numeric(frame, "compression_duration", default=0.0)
    setup_readiness = _numeric(frame, "setup_readiness_score", default=0.0)
    relative_accumulation = _numeric(frame, "relative_accumulation_score", default=0.0)
    extension_risk = _numeric(frame, "extension_risk_score", default=0.0)
    trader_score = _numeric(frame, "trader_score_v0", default=0.0)

    above_viscosity = (final_signal > viscosity).fillna(False)
    previous_above_viscosity = above_viscosity.shift(1, fill_value=False).astype(bool)
    viscosity_reclaim = (above_viscosity & ~previous_above_viscosity).fillna(False)
    zero_reclaim = _crosses_above(final_signal, 0.0)

    return {
        "compression_score_above_80": _crosses_above(compression, 80.0),
        "compression_duration_above_threshold": _crosses_above(compression_duration, 5.0),
        "compression_plus_relative_rising": ((compression >= 70.0) & (relative_component.diff() > 0.0)).fillna(False),
        "setup_readiness_score_crosses_threshold": _crosses_above(setup_readiness, 70.0),
        "relative_accumulation_score_crosses_threshold": _crosses_above(relative_accumulation, 65.0),
        "compressed_viscosity_reclaim": ((compression >= 70.0) & viscosity_reclaim).fillna(False),
        "compressed_zero_reclaim": ((compression >= 70.0) & zero_reclaim).fillna(False),
        "extension_risk_score_crosses_high": _crosses_above(extension_risk, 70.0),
        "trader_score_crosses_threshold": _crosses_above(trader_score, 70.0),
    }


def _event_value(frame: pd.DataFrame, event_name: str, event_date: pd.Timestamp) -> float:
    value_column_by_event = {
        "compression_score_above_80": "compression_score_v0",
        "compression_duration_above_threshold": "compression_duration",
        "compression_plus_relative_rising": "relative_accumulation_score",
        "setup_readiness_score_crosses_threshold": "setup_readiness_score",
        "relative_accumulation_score_crosses_threshold": "relative_accumulation_score",
        "compressed_viscosity_reclaim": "final_signal",
        "compressed_zero_reclaim": "final_signal",
        "extension_risk_score_crosses_high": "extension_risk_score",
        "trader_score_crosses_threshold": "trader_score_v0",
    }
    column = value_column_by_event[event_name]
    if column not in frame.columns and column == "compression_score_v0":
        column = "compression_score"
    return float(pd.to_numeric(frame[column], errors="coerce").loc[event_date])


def setup_event_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    *,
    timeframe: str,
    benchmark_name: str,
    cooldown_bars: int = DEFAULT_SETUP_RESEARCH_COOLDOWN_BARS,
    entry_lag_bars: int = DEFAULT_SETUP_RESEARCH_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    target = _numeric(frame, "target")
    benchmark = _numeric(frame, "benchmark")
    metrics = pd.DataFrame(index=frame.index)
    for horizon in HORIZONS:
        metrics[f"forward_relative_return_{horizon}"] = _future_relative_return(
            target,
            benchmark,
            horizon,
            entry_lag_bars,
        )
    metrics["max_drawdown_14"] = _forward_max_drawdown(target, 14, entry_lag_bars)
    metrics["max_drawdown_30"] = _forward_max_drawdown(target, 30, entry_lag_bars)

    records: list[dict[str, object]] = []
    for event_name, raw_mask in detect_setup_events(frame).items():
        event_mask = _apply_event_cooldown(raw_mask, cooldown_bars)
        for event_date in frame.index[event_mask]:
            event_position = frame.index.get_loc(event_date)
            entry_position = event_position + entry_lag_bars
            entry_date = frame.index[entry_position] if entry_position < len(frame.index) else pd.NaT
            record: dict[str, object] = {
                "symbol": symbol,
                "date": event_date,
                "timeframe": timeframe,
                "benchmark": benchmark_name,
                "setup_event": event_name,
                "setup_value": _event_value(frame, event_name, event_date),
                "entry_lag_bars": entry_lag_bars,
                "entry_date": entry_date,
                "event_cluster_id": pd.Timestamp(event_date).strftime("%Y-%m"),
            }
            for column in metrics.columns:
                record[column] = metrics.loc[event_date, column]
            records.append(record)
    return pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)


def build_setup_research_records(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    cooldown_bars: int = DEFAULT_SETUP_RESEARCH_COOLDOWN_BARS,
    entry_lag_bars: int = DEFAULT_SETUP_RESEARCH_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    records = [
        setup_event_records_for_asset(
            symbol,
            frame,
            timeframe=timeframe,
            benchmark_name=benchmark_name,
            cooldown_bars=cooldown_bars,
            entry_lag_bars=entry_lag_bars,
        )
        for symbol, frame in analysis_frames.items()
        if not frame.empty
    ]
    if not records:
        return pd.DataFrame(columns=RECORD_COLUMNS)
    return pd.concat(records, ignore_index=True)


def _mean(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.mean()) if not valid.empty else np.nan


def _median(series: pd.Series) -> float:
    valid = series.dropna()
    return float(valid.median()) if not valid.empty else np.nan


def _hit_rate(series: pd.Series) -> float:
    valid = series.dropna()
    return float((valid > 0.0).mean()) if not valid.empty else np.nan


def _max_share(series: pd.Series) -> float:
    valid = series.dropna()
    if valid.empty:
        return np.nan
    return float(valid.value_counts(normalize=True).iloc[0])


def summarize_setup_research_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    rows: list[dict[str, object]] = []
    for event_name in SETUP_EVENT_NAMES:
        event_records = records[records["setup_event"] == event_name]
        row: dict[str, object] = {
            "setup_event": event_name,
            "sample_size": int(len(event_records)),
            "unique_symbols": int(event_records["symbol"].nunique()) if not event_records.empty else 0,
            "unique_event_dates": int(event_records["date"].nunique()) if not event_records.empty else 0,
            "unique_event_clusters": int(event_records["event_cluster_id"].nunique()) if not event_records.empty else 0,
            "max_symbol_event_share": _max_share(event_records["symbol"]) if not event_records.empty else np.nan,
            "max_cluster_event_share": _max_share(event_records["event_cluster_id"]) if not event_records.empty else np.nan,
        }
        for horizon in HORIZONS:
            relative_return = pd.to_numeric(
                event_records.get(f"forward_relative_return_{horizon}", pd.Series(dtype=float)),
                errors="coerce",
            )
            row[f"avg_forward_relative_return_{horizon}"] = _mean(relative_return)
            row[f"median_forward_relative_return_{horizon}"] = _median(relative_return)
            row[f"hit_rate_forward_relative_return_{horizon}"] = _hit_rate(relative_return)
        for horizon in (14, 30):
            drawdown = pd.to_numeric(
                event_records.get(f"max_drawdown_{horizon}", pd.Series(dtype=float)),
                errors="coerce",
            )
            row[f"avg_max_drawdown_{horizon}"] = _mean(drawdown)
            row[f"median_max_drawdown_{horizon}"] = _median(drawdown)
        row["classification"], row["notes"] = _classify_row(row, min_sample_size=min_sample_size)
        rows.append(row)
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _classify_row(row: dict[str, object], *, min_sample_size: int) -> tuple[str, str]:
    sample_size = int(row["sample_size"])
    if sample_size < min_sample_size:
        return "inconclusive", f"sample size below min_sample_size={min_sample_size}"
    if float(row["max_symbol_event_share"]) > MAX_SYMBOL_EVENT_SHARE:
        return "inconclusive", "too many setup events come from one symbol"
    if float(row["max_cluster_event_share"]) > MAX_CLUSTER_EVENT_SHARE:
        return "inconclusive", "too many setup events come from one calendar cluster"
    median_14 = float(row["median_forward_relative_return_14"])
    median_30 = float(row["median_forward_relative_return_30"])
    hit_14 = float(row["hit_rate_forward_relative_return_14"])
    drawdown_30 = float(row["median_max_drawdown_30"])
    if any(np.isnan(value) for value in (median_14, median_30, hit_14)):
        return "inconclusive", "missing forward relative-return evidence"
    if median_14 > 0.0 and median_30 > 0.0 and hit_14 >= 0.5 and (np.isnan(drawdown_30) or drawdown_30 > -0.35):
        return "supporting_feature", "positive setup evidence; still requires review before promotion"
    if median_14 > 0.0 or median_30 > 0.0:
        return "experimental", "some positive evidence, but not enough to pass gates"
    return "rejected", "setup event did not show positive median relative evidence"


def run_setup_research(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    cooldown_bars: int = DEFAULT_SETUP_RESEARCH_COOLDOWN_BARS,
    entry_lag_bars: int = DEFAULT_SETUP_RESEARCH_ENTRY_LAG_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = build_setup_research_records(
        analysis_frames,
        timeframe=timeframe,
        benchmark_name=benchmark_name,
        cooldown_bars=cooldown_bars,
        entry_lag_bars=entry_lag_bars,
    )
    return summarize_setup_research_records(records, min_sample_size=min_sample_size), records
