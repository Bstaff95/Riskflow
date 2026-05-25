from __future__ import annotations

import numpy as np
import pandas as pd

from .features import rolling_percentile_rank
from .research_outcomes import (
    HORIZONS,
    apply_event_cooldown as _apply_event_cooldown,
    event_cluster_id,
    forward_max_drawdown as _forward_max_drawdown,
    forward_relative_return as _future_relative_return,
    hit_rate_or_nan as _hit_rate,
    max_share as _max_share,
    mean_or_nan as _mean,
    median_or_nan as _median,
)
from .signal_registry import (
    CORE_SIGNAL_V0,
    CORE_SIGNAL_V0_FORMULA_VERSION,
    DEFAULT_SIGNAL_RESEARCH_COOLDOWN_BARS,
    DEFAULT_SIGNAL_RESEARCH_ENTRY_LAG_BARS,
    get_signal_spec,
    signal_ids_by_role,
)


CORE_VARIANT = CORE_SIGNAL_V0
CHALLENGER_VARIANTS = signal_ids_by_role("challenger")
BASELINE_VARIANTS = signal_ids_by_role("baseline")
SIGNAL_VARIANTS = (CORE_VARIANT, *CHALLENGER_VARIANTS, *BASELINE_VARIANTS)
DEFAULT_MIN_SAMPLE_SIZE = 5
MAX_SYMBOL_EVENT_SHARE = 0.55
MAX_CLUSTER_EVENT_SHARE = 0.60
BASELINE_BY_CHALLENGER = {
    "relative_vol_adj_momentum_20": "baseline_raw_relative_return_20",
    "relative_vol_adj_momentum_50": "baseline_raw_relative_return_50",
    "relative_percentile_strength_50": "baseline_ratio_trend_50",
    "relative_percentile_strength_100": "baseline_buy_and_hold_relative",
    "cross_sectional_relative_rank_20": "baseline_simple_relative_momentum_rank_20",
    "cross_sectional_relative_rank_50": "baseline_simple_relative_momentum_rank_50",
}


RECORD_COLUMNS = [
    "symbol",
    "date",
    "timeframe",
    "benchmark",
    "signal_variant",
    "signal_role",
    "signal_version",
    "lookback",
    "signal_value",
    "event_name",
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
    "signal_variant",
    "event_name",
    "signal_role",
    "lookback",
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


def relative_vol_adjusted_momentum(relative_log: pd.Series, lookback: int) -> pd.Series:
    """Relative log momentum divided by trailing relative realized volatility."""
    if lookback < 1:
        raise ValueError("lookback must be >= 1")

    source = pd.to_numeric(relative_log, errors="coerce").astype(float)
    relative_return = source - source.shift(lookback)
    one_bar_return = source.diff()
    realized_vol = one_bar_return.rolling(window=lookback, min_periods=1).std(ddof=0)
    momentum = relative_return / realized_vol.replace(0.0, np.nan)

    valid_source = source.notna() & source.shift(lookback).notna()
    zero_or_missing_vol = realized_vol.isna() | (realized_vol == 0.0)
    momentum = momentum.where(~(valid_source & zero_or_missing_vol), 0.0)
    return momentum.where(valid_source)


def relative_percentile_strength(relative_log: pd.Series, lookback: int) -> pd.Series:
    """Percentile rank of the relative log ratio against its own trailing history."""
    return rolling_percentile_rank(relative_log, lookback).clip(lower=0.0, upper=100.0)


def _relative_log(frame: pd.DataFrame) -> pd.Series:
    if "relative_log" in frame.columns:
        return pd.to_numeric(frame["relative_log"], errors="coerce").astype(float)
    target_norm = pd.to_numeric(frame.get("target_norm"), errors="coerce").astype(float)
    benchmark_norm = pd.to_numeric(frame.get("benchmark_norm"), errors="coerce").astype(float)
    ratio = target_norm / benchmark_norm.replace(0.0, np.nan)
    return np.log(ratio.where(ratio > 0.0))


def _relative_log_frame(analysis_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    columns = {
        symbol: _relative_log(frame)
        for symbol, frame in analysis_frames.items()
        if not frame.empty
    }
    return pd.DataFrame(columns)


def cross_sectional_relative_rank(
    relative_logs: pd.DataFrame | dict[str, pd.Series],
    lookback: int,
) -> pd.DataFrame:
    """Percentile rank of relative momentum across symbols on each date."""
    if lookback < 1:
        raise ValueError("lookback must be >= 1")

    source = pd.DataFrame(relative_logs).apply(pd.to_numeric, errors="coerce")
    momentum = source - source.shift(lookback)
    return momentum.rank(axis=1, pct=True, method="average") * 100.0


def _buy_and_hold_relative(relative_log: pd.Series) -> pd.Series:
    source = pd.to_numeric(relative_log, errors="coerce").astype(float)
    valid = source.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=source.index)
    return source - valid.iloc[0]


def build_signal_variant_frames(analysis_frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build sidecar signal variants without mutating production analysis frames."""
    relative_logs = _relative_log_frame(analysis_frames)
    rank_20 = cross_sectional_relative_rank(relative_logs, 20) if not relative_logs.empty else pd.DataFrame()
    rank_50 = cross_sectional_relative_rank(relative_logs, 50) if not relative_logs.empty else pd.DataFrame()

    variant_frames: dict[str, pd.DataFrame] = {}
    for symbol, frame in analysis_frames.items():
        if frame.empty:
            variant_frames[symbol] = pd.DataFrame(index=frame.index)
            continue

        relative_log = _relative_log(frame)
        variants = pd.DataFrame(index=frame.index)
        variants[CORE_VARIANT] = pd.to_numeric(frame["final_signal"], errors="coerce").astype(float)
        variants["relative_vol_adj_momentum_20"] = relative_vol_adjusted_momentum(relative_log, 20)
        variants["relative_vol_adj_momentum_50"] = relative_vol_adjusted_momentum(relative_log, 50)
        variants["relative_percentile_strength_50"] = relative_percentile_strength(relative_log, 50)
        variants["relative_percentile_strength_100"] = relative_percentile_strength(relative_log, 100)
        variants["cross_sectional_relative_rank_20"] = (
            rank_20[symbol].reindex(frame.index) if symbol in rank_20.columns else np.nan
        )
        variants["cross_sectional_relative_rank_50"] = (
            rank_50[symbol].reindex(frame.index) if symbol in rank_50.columns else np.nan
        )
        variants["baseline_raw_relative_return_20"] = np.expm1(relative_log - relative_log.shift(20))
        variants["baseline_raw_relative_return_50"] = np.expm1(relative_log - relative_log.shift(50))
        variants["baseline_simple_relative_momentum_rank_20"] = variants["cross_sectional_relative_rank_20"]
        variants["baseline_simple_relative_momentum_rank_50"] = variants["cross_sectional_relative_rank_50"]
        variants["baseline_ratio_trend_20"] = relative_log - relative_log.rolling(20, min_periods=1).mean()
        variants["baseline_ratio_trend_50"] = relative_log - relative_log.rolling(50, min_periods=1).mean()
        variants["baseline_buy_and_hold_relative"] = _buy_and_hold_relative(relative_log)
        variant_frames[symbol] = variants

    return variant_frames


def _crosses_above(series: pd.Series, threshold: float) -> pd.Series:
    return ((series > threshold) & (series.shift(1) <= threshold)).fillna(False)


def research_event_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    variant_frame: pd.DataFrame,
    *,
    timeframe: str,
    benchmark_name: str,
    cooldown_bars: int = DEFAULT_SIGNAL_RESEARCH_COOLDOWN_BARS,
    entry_lag_bars: int = DEFAULT_SIGNAL_RESEARCH_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    target = pd.to_numeric(frame["target"], errors="coerce").astype(float)
    benchmark = pd.to_numeric(frame["benchmark"], errors="coerce").astype(float)

    metric_frame = pd.DataFrame(index=frame.index)
    for horizon in HORIZONS:
        metric_frame[f"forward_relative_return_{horizon}"] = _future_relative_return(
            target,
            benchmark,
            horizon,
            entry_lag_bars,
        )
    metric_frame["max_drawdown_14"] = _forward_max_drawdown(target, 14, entry_lag_bars)
    metric_frame["max_drawdown_30"] = _forward_max_drawdown(target, 30, entry_lag_bars)

    records: list[dict[str, object]] = []
    for variant_name in SIGNAL_VARIANTS:
        if variant_name not in variant_frame.columns:
            continue
        spec = get_signal_spec(variant_name)
        signal = pd.to_numeric(variant_frame[variant_name], errors="coerce").astype(float)
        event_name = f"{variant_name}_crosses_above_trigger"
        event_mask = _apply_event_cooldown(_crosses_above(signal, spec.trigger), cooldown_bars)
        event_dates = signal.index[event_mask]

        for event_date in event_dates:
            event_position = frame.index.get_loc(event_date)
            entry_position = event_position + entry_lag_bars
            entry_date = frame.index[entry_position] if entry_position < len(frame.index) else pd.NaT
            record: dict[str, object] = {
                "symbol": symbol,
                "date": event_date,
                "timeframe": timeframe,
                "benchmark": benchmark_name,
                "signal_variant": variant_name,
                "signal_role": spec.role,
                "signal_version": CORE_SIGNAL_V0_FORMULA_VERSION if variant_name == CORE_VARIANT else spec.version,
                "lookback": spec.lookback,
                "signal_value": signal.loc[event_date],
                "event_name": event_name,
                "entry_lag_bars": entry_lag_bars,
                "entry_date": entry_date,
                "event_cluster_id": event_cluster_id(event_date),
            }
            for column in metric_frame.columns:
                record[column] = metric_frame.loc[event_date, column]
            records.append(record)

    return pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)


def build_signal_research_records(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    cooldown_bars: int = DEFAULT_SIGNAL_RESEARCH_COOLDOWN_BARS,
    entry_lag_bars: int = DEFAULT_SIGNAL_RESEARCH_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    variant_frames = build_signal_variant_frames(analysis_frames)
    records = [
        research_event_records_for_asset(
            symbol,
            frame,
            variant_frames.get(symbol, pd.DataFrame(index=frame.index)),
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


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if frame.empty or column not in frame.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _reference_metrics(summary: pd.DataFrame, signal_variant: str) -> dict[str, float] | None:
    rows = summary[summary["signal_variant"] == signal_variant]
    if rows.empty:
        return None
    row = rows.iloc[0]
    return {
        "median_forward_relative_return_14": float(row["median_forward_relative_return_14"]),
        "median_forward_relative_return_30": float(row["median_forward_relative_return_30"]),
        "hit_rate_forward_relative_return_14": float(row["hit_rate_forward_relative_return_14"]),
        "hit_rate_forward_relative_return_30": float(row["hit_rate_forward_relative_return_30"]),
    }


def _beats_reference(row: dict[str, object], reference: dict[str, float] | None) -> bool:
    if reference is None:
        return False
    median_14 = float(row["median_forward_relative_return_14"])
    median_30 = float(row["median_forward_relative_return_30"])
    hit_14 = float(row["hit_rate_forward_relative_return_14"])
    hit_30 = float(row["hit_rate_forward_relative_return_30"])
    if any(np.isnan(value) for value in (median_14, median_30, hit_14, hit_30)):
        return False
    return (
        median_14 >= reference["median_forward_relative_return_14"]
        and median_30 >= reference["median_forward_relative_return_30"]
        and hit_14 >= reference["hit_rate_forward_relative_return_14"]
        and hit_30 >= reference["hit_rate_forward_relative_return_30"]
    )


def _classify_summary_row(
    row: dict[str, object],
    core_reference: dict[str, float] | None,
    baseline_reference: dict[str, float] | None,
    *,
    min_sample_size: int,
) -> tuple[str, str]:
    sample_size = int(row["sample_size"])
    variant = str(row["signal_variant"])
    role = str(row["signal_role"])
    if sample_size < min_sample_size:
        return "inconclusive", f"sample size below min_sample_size={min_sample_size}"
    if variant == CORE_VARIANT:
        return "core", "incumbent Pine-style signal"
    if role == "baseline":
        return "experimental", "simple baseline reference; not eligible for promotion"
    if float(row["max_symbol_event_share"]) > MAX_SYMBOL_EVENT_SHARE:
        return "inconclusive", "too many events come from one symbol"
    if float(row["max_cluster_event_share"]) > MAX_CLUSTER_EVENT_SHARE:
        return "inconclusive", "too many events come from one calendar cluster"
    if core_reference is None:
        return "experimental", "no sufficient core reference for this sample"

    median_14 = float(row["median_forward_relative_return_14"])
    median_30 = float(row["median_forward_relative_return_30"])
    hit_14 = float(row["hit_rate_forward_relative_return_14"])
    hit_30 = float(row["hit_rate_forward_relative_return_30"])
    drawdown_30 = float(row["median_max_drawdown_30"])
    if any(np.isnan(value) for value in (median_14, median_30, hit_14, hit_30)):
        return "inconclusive", "missing forward relative-return evidence"

    beats_core = _beats_reference(row, core_reference)
    beats_baseline = _beats_reference(row, baseline_reference)
    acceptable_drawdown = np.isnan(drawdown_30) or drawdown_30 > -0.35
    if beats_core and beats_baseline and acceptable_drawdown:
        return "supporting_feature", "beats or preserves core and baseline gates"
    if beats_core and baseline_reference is None:
        return "experimental", "beats core, but no matching baseline reference exists"
    if beats_core and not beats_baseline:
        return "experimental", "beats core, but not the matching simple baseline"
    if median_14 > 0.0 or median_30 > 0.0:
        return "experimental", "some positive evidence, but not enough to pass gates"
    return "rejected", "does not beat incumbent and baseline evidence gates"


def summarize_signal_research_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if records.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)

    grouped = records.groupby(["signal_variant", "event_name", "lookback"], dropna=False)
    for (variant, event_name, lookback), event_records in grouped:
        spec = get_signal_spec(str(variant))
        row: dict[str, object] = {
            "signal_variant": variant,
            "event_name": event_name,
            "signal_role": spec.role,
            "lookback": lookback,
            "sample_size": int(len(event_records)),
            "unique_symbols": int(event_records["symbol"].nunique()),
            "unique_event_dates": int(event_records["date"].nunique()),
            "unique_event_clusters": int(event_records["event_cluster_id"].nunique()),
            "max_symbol_event_share": _max_share(event_records["symbol"]),
            "max_cluster_event_share": _max_share(event_records["event_cluster_id"]),
        }
        for horizon in HORIZONS:
            relative_return = _numeric(event_records, f"forward_relative_return_{horizon}")
            row[f"avg_forward_relative_return_{horizon}"] = _mean(relative_return)
            row[f"median_forward_relative_return_{horizon}"] = _median(relative_return)
            row[f"hit_rate_forward_relative_return_{horizon}"] = _hit_rate(relative_return)
        for horizon in (14, 30):
            drawdown = _numeric(event_records, f"max_drawdown_{horizon}")
            row[f"avg_max_drawdown_{horizon}"] = _mean(drawdown)
            row[f"median_max_drawdown_{horizon}"] = _median(drawdown)
        rows.append(row)

    summary = pd.DataFrame(rows)
    core_rows = summary[(summary["signal_variant"] == CORE_VARIANT) & (summary["sample_size"] >= min_sample_size)]
    core_reference = _reference_metrics(core_rows, CORE_VARIANT) if not core_rows.empty else None

    classifications: list[str] = []
    notes: list[str] = []
    for row in summary.to_dict(orient="records"):
        baseline_variant = BASELINE_BY_CHALLENGER.get(str(row["signal_variant"]))
        baseline_reference = _reference_metrics(summary, baseline_variant) if baseline_variant else None
        classification, note = _classify_summary_row(
            row,
            core_reference,
            baseline_reference,
            min_sample_size=min_sample_size,
        )
        classifications.append(classification)
        notes.append(note)
    summary["classification"] = classifications
    summary["notes"] = notes
    return summary[SUMMARY_COLUMNS].sort_values(
        ["classification", "median_forward_relative_return_30", "sample_size"],
        ascending=[True, False, False],
    )


def run_signal_research(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    cooldown_bars: int = DEFAULT_SIGNAL_RESEARCH_COOLDOWN_BARS,
    entry_lag_bars: int = DEFAULT_SIGNAL_RESEARCH_ENTRY_LAG_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = build_signal_research_records(
        analysis_frames,
        timeframe=timeframe,
        benchmark_name=benchmark_name,
        cooldown_bars=cooldown_bars,
        entry_lag_bars=entry_lag_bars,
    )
    return summarize_signal_research_records(records, min_sample_size=min_sample_size), records
