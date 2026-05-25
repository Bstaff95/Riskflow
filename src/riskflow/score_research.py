from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .research_outcomes import (
    HORIZONS,
    event_cluster_id,
    forward_max_drawdown as _forward_max_drawdown,
    forward_relative_return as _future_relative_return,
    hit_rate_or_nan as _hit_rate,
    max_share as _max_share,
    mean_or_nan as _mean,
    median_or_nan as _median,
    split_half_medians as _split_half_medians,
    std_or_nan as _std,
    worst_cluster_median as _worst_cluster_median,
)
from .score_registry import EXTENSION_RISK_SCORE, RESEARCH_SCORE_IDS, get_score_spec


DEFAULT_BUCKET_COUNT = 10
DEFAULT_MIN_SYMBOLS_PER_DATE = 5
DEFAULT_MIN_BUCKET_SAMPLE_SIZE = 20
DEFAULT_ENTRY_LAG_BARS = 1
MAX_SYMBOL_SCORE_SHARE = 0.55
MAX_CLUSTER_SCORE_SHARE = 0.60

RECORD_COLUMNS = [
    "symbol",
    "date",
    "timeframe",
    "benchmark",
    "score_id",
    "score_role",
    "score_direction",
    "raw_score_value",
    "score_value",
    "rank_percentile",
    "bucket",
    "requested_bucket_count",
    "effective_bucket_count",
    "bucket_fallback",
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

BUCKET_SUMMARY_COLUMNS = [
    "score_id",
    "bucket",
    "sample_size",
    "unique_symbols",
    "unique_event_dates",
    "unique_event_clusters",
    "max_symbol_share",
    "max_cluster_share",
    "avg_forward_relative_return_3",
    "median_forward_relative_return_3",
    "hit_rate_forward_relative_return_3",
    "top_minus_bottom_spread_3",
    "avg_forward_relative_return_7",
    "median_forward_relative_return_7",
    "hit_rate_forward_relative_return_7",
    "top_minus_bottom_spread_7",
    "avg_forward_relative_return_14",
    "median_forward_relative_return_14",
    "hit_rate_forward_relative_return_14",
    "top_minus_bottom_spread_14",
    "avg_forward_relative_return_30",
    "median_forward_relative_return_30",
    "hit_rate_forward_relative_return_30",
    "top_minus_bottom_spread_30",
    "avg_max_drawdown_14",
    "median_max_drawdown_14",
    "avg_max_drawdown_30",
    "median_max_drawdown_30",
    "first_half_median_forward_relative_return_30",
    "second_half_median_forward_relative_return_30",
    "worst_cluster_median_forward_relative_return_30",
    "classification",
    "notes",
]

IC_SUMMARY_COLUMNS = [
    "score_id",
    "horizon",
    "valid_dates",
    "mean_rank_ic",
    "median_rank_ic",
    "std_rank_ic",
    "positive_rank_ic_share",
    "icir",
    "classification",
    "notes",
]

SCORE_SUMMARY_COLUMNS = [
    "score_id",
    "top_bucket",
    "top_bucket_sample_size",
    "top_bucket_median_forward_relative_return_14",
    "top_bucket_median_forward_relative_return_30",
    "top_bucket_hit_rate_forward_relative_return_14",
    "top_bucket_median_max_drawdown_30",
    "top_minus_bottom_spread_14",
    "top_minus_bottom_spread_30",
    "mean_rank_ic_14",
    "median_rank_ic_14",
    "positive_rank_ic_share_14",
    "mean_rank_ic_30",
    "median_rank_ic_30",
    "positive_rank_ic_share_30",
    "first_half_top_bucket_median_forward_relative_return_30",
    "second_half_top_bucket_median_forward_relative_return_30",
    "classification",
    "notes",
]


def _score_values(frame: pd.DataFrame, score_id: str) -> tuple[pd.Series, pd.Series]:
    spec = get_score_spec(score_id)
    raw = pd.to_numeric(frame.get(spec.source_column), errors="coerce").astype(float)
    if score_id == EXTENSION_RISK_SCORE:
        return raw, (100.0 - raw).clip(lower=0.0, upper=100.0)
    return raw, raw.clip(lower=0.0, upper=100.0)


def _assign_datewise_buckets(records: pd.DataFrame, bucket_count: int) -> pd.DataFrame:
    if records.empty:
        return records
    if bucket_count < 1:
        raise ValueError("bucket_count must be >= 1")

    output = records.copy()
    output["rank_percentile"] = np.nan
    output["bucket"] = np.nan
    output["effective_bucket_count"] = 0
    output["bucket_fallback"] = False

    for (_score_id, _date), group in output.groupby(["score_id", "date"], sort=False):
        valid = group["score_value"].dropna()
        valid_count = int(len(valid))
        if valid_count == 0:
            continue
        effective_bucket_count = min(bucket_count, valid_count)
        ranks = valid.rank(pct=True, method="average")
        buckets = np.ceil(ranks * effective_bucket_count).clip(1, effective_bucket_count).astype(int)
        output.loc[valid.index, "rank_percentile"] = ranks
        output.loc[valid.index, "bucket"] = buckets
        output.loc[group.index, "effective_bucket_count"] = effective_bucket_count
        output.loc[group.index, "bucket_fallback"] = effective_bucket_count < bucket_count

    output["bucket"] = pd.to_numeric(output["bucket"], errors="coerce").astype("Int64")
    output["effective_bucket_count"] = output["effective_bucket_count"].astype(int)
    output["bucket_fallback"] = output["bucket_fallback"].astype(bool)
    return output


def score_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=RECORD_COLUMNS)

    target = pd.to_numeric(frame.get("target"), errors="coerce").astype(float)
    benchmark = pd.to_numeric(frame.get("benchmark"), errors="coerce").astype(float)
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
    for score_id in RESEARCH_SCORE_IDS:
        spec = get_score_spec(score_id)
        if spec.source_column not in frame.columns:
            continue
        raw_score, score_value = _score_values(frame, score_id)
        for position, date in enumerate(frame.index):
            if pd.isna(target.loc[date]) or pd.isna(benchmark.loc[date]) or pd.isna(score_value.loc[date]):
                continue
            entry_position = position + entry_lag_bars
            records.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "timeframe": timeframe,
                    "benchmark": benchmark_name,
                    "score_id": score_id,
                    "score_role": spec.role,
                    "score_direction": spec.direction,
                    "raw_score_value": raw_score.loc[date],
                    "score_value": score_value.loc[date],
                    "rank_percentile": np.nan,
                    "bucket": pd.NA,
                    "requested_bucket_count": np.nan,
                    "effective_bucket_count": 0,
                    "bucket_fallback": False,
                    "entry_lag_bars": entry_lag_bars,
                    "entry_date": frame.index[entry_position] if entry_position < len(frame.index) else pd.NaT,
                    "event_cluster_id": event_cluster_id(date),
                    "forward_relative_return_3": metrics.loc[date, "forward_relative_return_3"],
                    "forward_relative_return_7": metrics.loc[date, "forward_relative_return_7"],
                    "forward_relative_return_14": metrics.loc[date, "forward_relative_return_14"],
                    "forward_relative_return_30": metrics.loc[date, "forward_relative_return_30"],
                    "max_drawdown_14": metrics.loc[date, "max_drawdown_14"],
                    "max_drawdown_30": metrics.loc[date, "max_drawdown_30"],
                }
            )
    return pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)


def build_score_research_records(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    bucket_count: int = DEFAULT_BUCKET_COUNT,
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    records = [
        score_records_for_asset(
            symbol,
            frame,
            timeframe=timeframe,
            benchmark_name=benchmark_name,
            entry_lag_bars=entry_lag_bars,
        )
        for symbol, frame in analysis_frames.items()
        if not frame.empty
    ]
    if not records:
        return pd.DataFrame(columns=RECORD_COLUMNS)
    output = pd.concat(records, ignore_index=True)
    output["requested_bucket_count"] = bucket_count
    return _assign_datewise_buckets(output, bucket_count)


def _spread_by_score_bucket(records: pd.DataFrame, score_id: str, horizon: int) -> float:
    score_records = records[records["score_id"] == score_id]
    valid = score_records.dropna(subset=["bucket", f"forward_relative_return_{horizon}"])
    if valid.empty:
        return np.nan
    top_bucket = valid["bucket"].max()
    bottom_bucket = valid["bucket"].min()
    top = pd.to_numeric(valid[valid["bucket"] == top_bucket][f"forward_relative_return_{horizon}"], errors="coerce")
    bottom = pd.to_numeric(valid[valid["bucket"] == bottom_bucket][f"forward_relative_return_{horizon}"], errors="coerce")
    if top.dropna().empty or bottom.dropna().empty:
        return np.nan
    return float(top.median() - bottom.median())


def _classify_bucket_row(row: dict[str, object], *, min_bucket_sample_size: int) -> tuple[str, str]:
    sample_size = int(row["sample_size"])
    notes: list[str] = []
    if sample_size < min_bucket_sample_size:
        return "inconclusive", f"sample size below min_bucket_sample_size={min_bucket_sample_size}"
    if float(row["max_symbol_share"]) > MAX_SYMBOL_SCORE_SHARE:
        return "fragile", "too many observations come from one symbol"
    if float(row["max_cluster_share"]) > MAX_CLUSTER_SCORE_SHARE:
        return "fragile", "too many observations come from one calendar cluster"

    median_14 = float(row["median_forward_relative_return_14"])
    median_30 = float(row["median_forward_relative_return_30"])
    hit_14 = float(row["hit_rate_forward_relative_return_14"])
    spread_14 = float(row["top_minus_bottom_spread_14"])
    spread_30 = float(row["top_minus_bottom_spread_30"])
    first_half = float(row["first_half_median_forward_relative_return_30"])
    second_half = float(row["second_half_median_forward_relative_return_30"])
    if any(math.isnan(value) for value in (median_14, median_30, hit_14)):
        return "inconclusive", "insufficient forward-relative-return data"
    if any(math.isnan(value) for value in (spread_14, spread_30)):
        notes.append("spread unavailable")
    if (not math.isnan(first_half)) and (not math.isnan(second_half)) and (first_half > 0.0) != (second_half > 0.0):
        notes.append("first-half and second-half evidence diverges")
    if median_14 > 0.0 and median_30 > 0.0 and hit_14 >= 0.55 and spread_14 > 0.0 and spread_30 > 0.0:
        return "useful", "; ".join(notes) or "positive median returns and positive top-minus-bottom spread"
    if median_14 > 0.0 or median_30 > 0.0 or hit_14 >= 0.52:
        return "watchlist", "; ".join(notes) or "some positive evidence, but not enough for useful classification"
    return "fragile", "; ".join(notes) or "weak or negative forward relative-return evidence"


def summarize_score_buckets(
    records: pd.DataFrame,
    *,
    min_bucket_sample_size: int = DEFAULT_MIN_BUCKET_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for score_id in RESEARCH_SCORE_IDS:
        score_records = records[records["score_id"] == score_id] if not records.empty else pd.DataFrame()
        buckets = sorted(score_records["bucket"].dropna().unique()) if not score_records.empty else []
        for bucket in buckets:
            bucket_records = score_records[score_records["bucket"] == bucket]
            row: dict[str, object] = {
                "score_id": score_id,
                "bucket": int(bucket),
                "sample_size": int(len(bucket_records)),
                "unique_symbols": int(bucket_records["symbol"].nunique()) if not bucket_records.empty else 0,
                "unique_event_dates": int(bucket_records["date"].nunique()) if not bucket_records.empty else 0,
                "unique_event_clusters": int(bucket_records["event_cluster_id"].nunique()) if not bucket_records.empty else 0,
                "max_symbol_share": _max_share(bucket_records["symbol"]) if not bucket_records.empty else np.nan,
                "max_cluster_share": _max_share(bucket_records["event_cluster_id"]) if not bucket_records.empty else np.nan,
            }
            for horizon in HORIZONS:
                relative_return = pd.to_numeric(bucket_records[f"forward_relative_return_{horizon}"], errors="coerce")
                row[f"avg_forward_relative_return_{horizon}"] = _mean(relative_return)
                row[f"median_forward_relative_return_{horizon}"] = _median(relative_return)
                row[f"hit_rate_forward_relative_return_{horizon}"] = _hit_rate(relative_return)
                row[f"top_minus_bottom_spread_{horizon}"] = _spread_by_score_bucket(records, score_id, horizon)
            for horizon in (14, 30):
                drawdown = pd.to_numeric(bucket_records[f"max_drawdown_{horizon}"], errors="coerce")
                row[f"avg_max_drawdown_{horizon}"] = _mean(drawdown)
                row[f"median_max_drawdown_{horizon}"] = _median(drawdown)
            first_half, second_half = _split_half_medians(bucket_records, "forward_relative_return_30")
            row["first_half_median_forward_relative_return_30"] = first_half
            row["second_half_median_forward_relative_return_30"] = second_half
            row["worst_cluster_median_forward_relative_return_30"] = _worst_cluster_median(
                bucket_records,
                "forward_relative_return_30",
            )
            row["classification"], row["notes"] = _classify_bucket_row(
                row,
                min_bucket_sample_size=min_bucket_sample_size,
            )
            if bucket_records["bucket_fallback"].any():
                fallback_note = "bucket fallback used on some dates"
                row["notes"] = f"{row['notes']}; {fallback_note}" if row["notes"] else fallback_note
            rows.append(row)
    return pd.DataFrame(rows, columns=BUCKET_SUMMARY_COLUMNS)


def summarize_rank_ic(
    records: pd.DataFrame,
    *,
    min_symbols_per_date: int = DEFAULT_MIN_SYMBOLS_PER_DATE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for score_id in RESEARCH_SCORE_IDS:
        score_records = records[records["score_id"] == score_id] if not records.empty else pd.DataFrame()
        for horizon in HORIZONS:
            column = f"forward_relative_return_{horizon}"
            ics: list[float] = []
            for _date, date_records in score_records.groupby("date"):
                valid = date_records[["score_value", column]].dropna()
                if len(valid) < min_symbols_per_date:
                    continue
                if valid["score_value"].nunique() < 2 or valid[column].nunique() < 2:
                    continue
                ic = valid["score_value"].corr(valid[column], method="spearman")
                if pd.notna(ic):
                    ics.append(float(ic))
            series = pd.Series(ics, dtype=float)
            mean_ic = _mean(series)
            std_ic = _std(series)
            row = {
                "score_id": score_id,
                "horizon": horizon,
                "valid_dates": int(len(series)),
                "mean_rank_ic": mean_ic,
                "median_rank_ic": _median(series),
                "std_rank_ic": std_ic,
                "positive_rank_ic_share": _hit_rate(series),
                "icir": float(mean_ic / std_ic) if pd.notna(mean_ic) and pd.notna(std_ic) and std_ic != 0.0 else np.nan,
            }
            row["classification"], row["notes"] = _classify_ic_row(row)
            rows.append(row)
    return pd.DataFrame(rows, columns=IC_SUMMARY_COLUMNS)


def _classify_ic_row(row: dict[str, object]) -> tuple[str, str]:
    valid_dates = int(row["valid_dates"])
    if valid_dates < 5:
        return "inconclusive", "too few valid dates for rank IC"
    mean_ic = float(row["mean_rank_ic"])
    median_ic = float(row["median_rank_ic"])
    positive_share = float(row["positive_rank_ic_share"])
    if any(math.isnan(value) for value in (mean_ic, median_ic, positive_share)):
        return "inconclusive", "rank IC unavailable"
    if mean_ic > 0.0 and median_ic > 0.0 and positive_share >= 0.55:
        return "useful", "positive mean/median rank IC with acceptable positive-date share"
    if mean_ic > 0.0 or median_ic > 0.0 or positive_share >= 0.52:
        return "watchlist", "some positive rank IC evidence"
    return "fragile", "weak or negative rank IC evidence"


def summarize_scores(bucket_summary: pd.DataFrame, ic_summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for score_id in RESEARCH_SCORE_IDS:
        score_buckets = bucket_summary[bucket_summary["score_id"] == score_id] if not bucket_summary.empty else pd.DataFrame()
        if score_buckets.empty:
            top_bucket = np.nan
            top = pd.Series(dtype=object)
        else:
            top_bucket = int(score_buckets["bucket"].max())
            top = score_buckets[score_buckets["bucket"] == top_bucket].iloc[0]
        score_ic = ic_summary[ic_summary["score_id"] == score_id] if not ic_summary.empty else pd.DataFrame()
        ic_14 = score_ic[score_ic["horizon"] == 14].iloc[0] if not score_ic[score_ic["horizon"] == 14].empty else pd.Series(dtype=object)
        ic_30 = score_ic[score_ic["horizon"] == 30].iloc[0] if not score_ic[score_ic["horizon"] == 30].empty else pd.Series(dtype=object)
        row = {
            "score_id": score_id,
            "top_bucket": top_bucket,
            "top_bucket_sample_size": int(top.get("sample_size", 0)) if not top.empty else 0,
            "top_bucket_median_forward_relative_return_14": top.get("median_forward_relative_return_14", np.nan),
            "top_bucket_median_forward_relative_return_30": top.get("median_forward_relative_return_30", np.nan),
            "top_bucket_hit_rate_forward_relative_return_14": top.get("hit_rate_forward_relative_return_14", np.nan),
            "top_bucket_median_max_drawdown_30": top.get("median_max_drawdown_30", np.nan),
            "top_minus_bottom_spread_14": top.get("top_minus_bottom_spread_14", np.nan),
            "top_minus_bottom_spread_30": top.get("top_minus_bottom_spread_30", np.nan),
            "mean_rank_ic_14": ic_14.get("mean_rank_ic", np.nan),
            "median_rank_ic_14": ic_14.get("median_rank_ic", np.nan),
            "positive_rank_ic_share_14": ic_14.get("positive_rank_ic_share", np.nan),
            "mean_rank_ic_30": ic_30.get("mean_rank_ic", np.nan),
            "median_rank_ic_30": ic_30.get("median_rank_ic", np.nan),
            "positive_rank_ic_share_30": ic_30.get("positive_rank_ic_share", np.nan),
            "first_half_top_bucket_median_forward_relative_return_30": top.get(
                "first_half_median_forward_relative_return_30",
                np.nan,
            ),
            "second_half_top_bucket_median_forward_relative_return_30": top.get(
                "second_half_median_forward_relative_return_30",
                np.nan,
            ),
        }
        row["classification"], row["notes"] = _classify_score_row(row, top)
        rows.append(row)
    return pd.DataFrame(rows, columns=SCORE_SUMMARY_COLUMNS)


def _classify_score_row(row: dict[str, object], top_bucket: pd.Series) -> tuple[str, str]:
    if int(row["top_bucket_sample_size"]) == 0:
        return "inconclusive", "no top-bucket observations"
    top_classification = str(top_bucket.get("classification", "inconclusive")) if not top_bucket.empty else "inconclusive"
    if top_classification in {"inconclusive", "fragile"}:
        return top_classification, str(top_bucket.get("notes", "top bucket not validated"))
    median_14 = float(row["top_bucket_median_forward_relative_return_14"])
    median_30 = float(row["top_bucket_median_forward_relative_return_30"])
    spread_14 = float(row["top_minus_bottom_spread_14"])
    spread_30 = float(row["top_minus_bottom_spread_30"])
    mean_ic_14 = float(row["mean_rank_ic_14"])
    median_ic_14 = float(row["median_rank_ic_14"])
    positive_ic_14 = float(row["positive_rank_ic_share_14"])
    values = (median_14, median_30, spread_14, spread_30, mean_ic_14, median_ic_14, positive_ic_14)
    if any(math.isnan(value) for value in values):
        return "inconclusive", "top bucket or rank IC evidence incomplete"
    if (
        median_14 > 0.0
        and median_30 > 0.0
        and spread_14 > 0.0
        and spread_30 > 0.0
        and mean_ic_14 > 0.0
        and median_ic_14 > 0.0
        and positive_ic_14 >= 0.55
    ):
        return "useful", "top bucket and rank IC evidence are positive"
    if median_14 > 0.0 or median_30 > 0.0 or mean_ic_14 > 0.0:
        return "watchlist", "mixed but potentially useful score evidence"
    return "fragile", "score does not show useful ranking evidence"


def run_score_research(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    bucket_count: int = DEFAULT_BUCKET_COUNT,
    min_symbols_per_date: int = DEFAULT_MIN_SYMBOLS_PER_DATE,
    min_bucket_sample_size: int = DEFAULT_MIN_BUCKET_SAMPLE_SIZE,
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    records = build_score_research_records(
        analysis_frames,
        timeframe=timeframe,
        benchmark_name=benchmark_name,
        bucket_count=bucket_count,
        entry_lag_bars=entry_lag_bars,
    )
    bucket_summary = summarize_score_buckets(records, min_bucket_sample_size=min_bucket_sample_size)
    ic_summary = summarize_rank_ic(records, min_symbols_per_date=min_symbols_per_date)
    score_summary = summarize_scores(bucket_summary, ic_summary)
    return score_summary, bucket_summary, ic_summary, records
