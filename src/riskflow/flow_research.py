from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import UniverseConfig
from .flow_graph import (
    CAPITAL_FLOW_GRAPH_V0,
    NON_SUPPORTIVE_CHAIN_LABELS,
    SUPPORTIVE_CHAIN_LABELS,
    append_chain_context,
)
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
    median_or_nan,
)


DEFAULT_MIN_SAMPLE_SIZE = 20
DEFAULT_ENTRY_LAG_BARS = 1
DEFAULT_COOLDOWN_BARS = 30
MAX_SYMBOL_SHARE = 0.55
MAX_CLUSTER_SHARE = 0.60

FLOW_EVENT_NAMES = (
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
    "graph_model",
    "flow_event",
    "chain_support_group",
    "chain_label",
    "chain_support_score",
    "chain_alignment_tags",
    "chain_conflict_tags",
    "chain_confidence",
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
    "flow_event",
    "sample_size",
    "supportive_sample_size",
    "non_supportive_sample_size",
    "incomplete_sample_size",
    "unique_symbols",
    "unique_event_dates",
    "unique_event_clusters",
    "max_symbol_share",
    "max_cluster_share",
    "supportive_median_forward_relative_return_14",
    "non_supportive_median_forward_relative_return_14",
    "supportive_minus_non_supportive_spread_14",
    "supportive_hit_rate_forward_relative_return_14",
    "non_supportive_hit_rate_forward_relative_return_14",
    "supportive_median_forward_relative_return_30",
    "non_supportive_median_forward_relative_return_30",
    "supportive_minus_non_supportive_spread_30",
    "supportive_hit_rate_forward_relative_return_30",
    "non_supportive_hit_rate_forward_relative_return_30",
    "supportive_median_max_drawdown_14",
    "non_supportive_median_max_drawdown_14",
    "supportive_median_max_drawdown_30",
    "non_supportive_median_max_drawdown_30",
    "classification",
    "notes",
]


def _crosses_above(series: pd.Series, threshold: float) -> pd.Series:
    return (series > threshold) & (series.shift(1) <= threshold)


def _detect_flow_events(frame: pd.DataFrame) -> dict[str, pd.Series]:
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
    chain_label = str(row.get("chain_label", ""))
    if chain_label in SUPPORTIVE_CHAIN_LABELS:
        return "supportive"
    if chain_label in NON_SUPPORTIVE_CHAIN_LABELS:
        return "non_supportive"
    return "incomplete"


def flow_records_for_asset(
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
    for event_name, raw_mask in _detect_flow_events(frame).items():
        mask = apply_event_cooldown(raw_mask, cooldown_bars)
        for event_date in frame.index[mask]:
            event_position = frame.index.get_loc(event_date)
            row = frame.loc[event_date]
            record: dict[str, object] = {
                "symbol": symbol,
                "date": event_date,
                "timeframe": timeframe,
                "benchmark": benchmark_label_at(frame, event_date, benchmark_name),
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "flow_event": event_name,
                "chain_support_group": _support_group(row),
                "chain_label": row.get("chain_label"),
                "chain_support_score": row.get("chain_support_score"),
                "chain_alignment_tags": row.get("chain_alignment_tags"),
                "chain_conflict_tags": row.get("chain_conflict_tags"),
                "chain_confidence": row.get("chain_confidence"),
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


def build_flow_research_records(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
    cooldown_bars: int = DEFAULT_COOLDOWN_BARS,
) -> pd.DataFrame:
    enriched = append_chain_context(universe, analysis_frames, timeframe=timeframe)
    records = [
        flow_records_for_asset(
            symbol,
            frame,
            timeframe=timeframe,
            benchmark_name=universe.benchmark.name,
            entry_lag_bars=entry_lag_bars,
            cooldown_bars=cooldown_bars,
        )
        for symbol, frame in enriched.items()
        if not frame.empty
    ]
    non_empty = [record for record in records if not record.empty]
    return pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame(columns=RECORD_COLUMNS)


def _group(records: pd.DataFrame, event_name: str, group_name: str) -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(columns=RECORD_COLUMNS)
    return records[(records["flow_event"] == event_name) & (records["chain_support_group"] == group_name)]


def _spread(supportive: pd.DataFrame, non_supportive: pd.DataFrame, column: str) -> float:
    supportive_median = median_or_nan(supportive.get(column, pd.Series(dtype=float)))
    non_supportive_median = median_or_nan(non_supportive.get(column, pd.Series(dtype=float)))
    if pd.isna(supportive_median) or pd.isna(non_supportive_median):
        return np.nan
    return float(supportive_median - non_supportive_median)


def _classify_row(row: dict[str, object], *, min_sample_size: int) -> tuple[str, str]:
    supportive_n = int(row["supportive_sample_size"])
    non_supportive_n = int(row["non_supportive_sample_size"])
    if supportive_n < min_sample_size or non_supportive_n < min_sample_size:
        return "inconclusive", f"supportive and non-supportive groups both need min_sample_size={min_sample_size}"
    if float(row["max_symbol_share"]) > MAX_SYMBOL_SHARE:
        return "fragile", "too many observations come from one symbol"
    if float(row["max_cluster_share"]) > MAX_CLUSTER_SHARE:
        return "fragile", "too many observations come from one calendar cluster"

    spread_14 = float(row["supportive_minus_non_supportive_spread_14"])
    spread_30 = float(row["supportive_minus_non_supportive_spread_30"])
    supportive_hit_14 = float(row["supportive_hit_rate_forward_relative_return_14"])
    non_supportive_hit_14 = float(row["non_supportive_hit_rate_forward_relative_return_14"])
    supportive_drawdown_30 = float(row["supportive_median_max_drawdown_30"])
    non_supportive_drawdown_30 = float(row["non_supportive_median_max_drawdown_30"])
    values = (spread_14, spread_30, supportive_hit_14, non_supportive_hit_14)
    if any(math.isnan(value) for value in values):
        return "inconclusive", "comparison evidence unavailable"

    hit_preserved = supportive_hit_14 + 0.02 >= non_supportive_hit_14
    drawdown_ok = (
        math.isnan(supportive_drawdown_30)
        or math.isnan(non_supportive_drawdown_30)
        or supportive_drawdown_30 >= non_supportive_drawdown_30 - 0.05
    )
    if spread_14 > 0.0 and spread_30 > 0.0 and hit_preserved and drawdown_ok:
        return "useful", "supportive chains improved median outcomes without obvious hit-rate/drawdown damage"
    if (spread_14 > 0.0 or spread_30 > 0.0) and hit_preserved:
        return "watchlist", "mixed but potentially useful chain-support evidence"
    return "fragile", "supportive chains did not improve the matched baseline"


def summarize_flow_research_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for event_name in FLOW_EVENT_NAMES:
        event_records = records[records["flow_event"] == event_name] if not records.empty else pd.DataFrame(columns=RECORD_COLUMNS)
        supportive = _group(records, event_name, "supportive")
        non_supportive = _group(records, event_name, "non_supportive")
        incomplete = _group(records, event_name, "incomplete")
        row: dict[str, object] = {
            "flow_event": event_name,
            "sample_size": int(len(event_records)),
            "supportive_sample_size": int(len(supportive)),
            "non_supportive_sample_size": int(len(non_supportive)),
            "incomplete_sample_size": int(len(incomplete)),
            "unique_symbols": int(event_records["symbol"].nunique()) if not event_records.empty else 0,
            "unique_event_dates": int(event_records["date"].nunique()) if not event_records.empty else 0,
            "unique_event_clusters": int(event_records["event_cluster_id"].nunique()) if not event_records.empty else 0,
            "max_symbol_share": max_share(event_records["symbol"]) if not event_records.empty else np.nan,
            "max_cluster_share": max_share(event_records["event_cluster_id"]) if not event_records.empty else np.nan,
        }
        for horizon in (14, 30):
            column = f"forward_relative_return_{horizon}"
            row[f"supportive_median_forward_relative_return_{horizon}"] = median_or_nan(
                supportive.get(column, pd.Series(dtype=float)),
            )
            row[f"non_supportive_median_forward_relative_return_{horizon}"] = median_or_nan(
                non_supportive.get(column, pd.Series(dtype=float)),
            )
            row[f"supportive_minus_non_supportive_spread_{horizon}"] = _spread(supportive, non_supportive, column)
            row[f"supportive_hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(
                supportive.get(column, pd.Series(dtype=float)),
            )
            row[f"non_supportive_hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(
                non_supportive.get(column, pd.Series(dtype=float)),
            )
            drawdown_column = f"max_drawdown_{horizon}"
            row[f"supportive_median_max_drawdown_{horizon}"] = median_or_nan(
                supportive.get(drawdown_column, pd.Series(dtype=float)),
            )
            row[f"non_supportive_median_max_drawdown_{horizon}"] = median_or_nan(
                non_supportive.get(drawdown_column, pd.Series(dtype=float)),
            )
        row["classification"], row["notes"] = _classify_row(row, min_sample_size=min_sample_size)
        rows.append(row)
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def run_flow_research(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
    cooldown_bars: int = DEFAULT_COOLDOWN_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = build_flow_research_records(
        universe,
        analysis_frames,
        timeframe=timeframe,
        entry_lag_bars=entry_lag_bars,
        cooldown_bars=cooldown_bars,
    )
    return summarize_flow_research_records(records, min_sample_size=min_sample_size), records
