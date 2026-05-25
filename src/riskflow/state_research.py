from __future__ import annotations

import numpy as np
import pandas as pd

from .event_study import HORIZONS
from .signal_research import _forward_max_drawdown, _future_relative_return
from .state_registry import STATE_MODEL_V0, get_state_model_spec


DEFAULT_MIN_SAMPLE_SIZE = 5
DEFAULT_ENTRY_LAG_BARS = 1
MAX_SYMBOL_STATE_SHARE = 0.55
MAX_CLUSTER_STATE_SHARE = 0.60

STATES = get_state_model_spec(STATE_MODEL_V0).states

RECORD_COLUMNS = [
    "symbol",
    "date",
    "timeframe",
    "benchmark",
    "state_model",
    "state",
    "state_confidence",
    "state_duration",
    "state_run_id",
    "next_state",
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
    "state",
    "state_model",
    "sample_size",
    "unique_symbols",
    "unique_event_dates",
    "unique_event_clusters",
    "max_symbol_state_share",
    "max_cluster_state_share",
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
    "avg_state_duration",
    "median_state_duration",
    "most_common_next_state",
    "transition_to_emerging_leader_rate",
    "transition_to_confirmed_leader_rate",
    "transition_to_breakdown_rate",
    "classification",
    "notes",
]

TRANSITION_COLUMNS = [
    "from_state",
    "to_state",
    "transition_count",
    "transition_probability",
    "avg_duration_before_transition",
    "median_duration_before_transition",
]


def _numeric(frame: pd.DataFrame, column: str, default: float = np.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _state_runs(state: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    state_string = state.astype("string").fillna("Unknown")
    run_starts = state_string.ne(state_string.shift(1)).fillna(True)
    run_id = run_starts.cumsum().astype(int)
    duration = state_string.groupby(run_id).cumcount() + 1
    run_states = state_string.groupby(run_id).first()
    next_state_by_run = run_states.shift(-1)
    next_state = run_id.map(next_state_by_run)
    return run_id, duration.astype(int), next_state.astype("string")


def state_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    if frame.empty or "state" not in frame.columns:
        return pd.DataFrame(columns=RECORD_COLUMNS)

    target = _numeric(frame, "target")
    benchmark = _numeric(frame, "benchmark")
    state = frame["state"].astype("string").fillna("Unknown")
    state_model = frame.get("state_model", pd.Series(STATE_MODEL_V0, index=frame.index)).astype("string")
    state_confidence = _numeric(frame, "state_confidence", default=np.nan)
    run_id, duration, next_state = _state_runs(state)

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
    for position, date in enumerate(frame.index):
        if pd.isna(target.loc[date]) or pd.isna(benchmark.loc[date]):
            continue
        entry_position = position + entry_lag_bars
        records.append(
            {
                "symbol": symbol,
                "date": date,
                "timeframe": timeframe,
                "benchmark": benchmark_name,
                "state_model": state_model.loc[date],
                "state": state.loc[date],
                "state_confidence": state_confidence.loc[date],
                "state_duration": duration.loc[date],
                "state_run_id": f"{symbol}:{int(run_id.loc[date])}",
                "next_state": next_state.loc[date],
                "entry_lag_bars": entry_lag_bars,
                "entry_date": frame.index[entry_position] if entry_position < len(frame.index) else pd.NaT,
                "event_cluster_id": pd.Timestamp(date).strftime("%Y-%m"),
                "forward_relative_return_3": metrics.loc[date, "forward_relative_return_3"],
                "forward_relative_return_7": metrics.loc[date, "forward_relative_return_7"],
                "forward_relative_return_14": metrics.loc[date, "forward_relative_return_14"],
                "forward_relative_return_30": metrics.loc[date, "forward_relative_return_30"],
                "max_drawdown_14": metrics.loc[date, "max_drawdown_14"],
                "max_drawdown_30": metrics.loc[date, "max_drawdown_30"],
            }
        )
    return pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)


def build_state_research_records(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    records = [
        state_records_for_asset(
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


def _most_common(series: pd.Series) -> str:
    valid = series.dropna()
    if valid.empty:
        return ""
    counts = valid.astype("string").value_counts()
    return str(counts.index[0]) if not counts.empty else ""


def _rate_to_state(records: pd.DataFrame, target_state: str) -> float:
    valid = records["next_state"].dropna().astype("string") if "next_state" in records else pd.Series(dtype="string")
    if valid.empty:
        return np.nan
    return float((valid == target_state).mean())


def _classify_row(row: dict[str, object], *, min_sample_size: int) -> tuple[str, str]:
    sample_size = int(row["sample_size"])
    if sample_size < min_sample_size:
        return "inconclusive", f"sample size below min_sample_size={min_sample_size}"
    if float(row["max_symbol_state_share"]) > MAX_SYMBOL_STATE_SHARE:
        return "fragile", "too many state observations come from one symbol"
    if float(row["max_cluster_state_share"]) > MAX_CLUSTER_STATE_SHARE:
        return "fragile", "too many state observations come from one calendar cluster"

    median_14 = float(row["median_forward_relative_return_14"])
    median_30 = float(row["median_forward_relative_return_30"])
    hit_14 = float(row["hit_rate_forward_relative_return_14"])
    drawdown_30 = float(row["median_max_drawdown_30"])
    if any(np.isnan(value) for value in (median_14, median_30, hit_14)):
        return "inconclusive", "insufficient forward-relative-return data"
    if median_14 > 0.0 and median_30 > 0.0 and hit_14 >= 0.55 and drawdown_30 > -0.25:
        return "useful", "positive median forward relative returns with acceptable drawdown"
    if median_14 > 0.0 or median_30 > 0.0 or hit_14 >= 0.52:
        return "watchlist", "some positive evidence, but not enough for useful classification"
    return "fragile", "state has weak or negative forward relative-return evidence"


def summarize_state_research_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for state_name in STATES:
        state_records = records[records["state"] == state_name] if not records.empty else pd.DataFrame()
        row: dict[str, object] = {
            "state": state_name,
            "state_model": STATE_MODEL_V0,
            "sample_size": int(len(state_records)),
            "unique_symbols": int(state_records["symbol"].nunique()) if not state_records.empty else 0,
            "unique_event_dates": int(state_records["date"].nunique()) if not state_records.empty else 0,
            "unique_event_clusters": int(state_records["event_cluster_id"].nunique()) if not state_records.empty else 0,
            "max_symbol_state_share": _max_share(state_records["symbol"]) if not state_records.empty else np.nan,
            "max_cluster_state_share": _max_share(state_records["event_cluster_id"]) if not state_records.empty else np.nan,
        }
        for horizon in HORIZONS:
            relative_return = pd.to_numeric(
                state_records.get(f"forward_relative_return_{horizon}", pd.Series(dtype=float)),
                errors="coerce",
            )
            row[f"avg_forward_relative_return_{horizon}"] = _mean(relative_return)
            row[f"median_forward_relative_return_{horizon}"] = _median(relative_return)
            row[f"hit_rate_forward_relative_return_{horizon}"] = _hit_rate(relative_return)
        for horizon in (14, 30):
            drawdown = pd.to_numeric(
                state_records.get(f"max_drawdown_{horizon}", pd.Series(dtype=float)),
                errors="coerce",
            )
            row[f"avg_max_drawdown_{horizon}"] = _mean(drawdown)
            row[f"median_max_drawdown_{horizon}"] = _median(drawdown)

        run_ends = (
            state_records.sort_values(["symbol", "date"])
            .groupby("state_run_id", as_index=False)
            .tail(1)
            if not state_records.empty
            else pd.DataFrame()
        )
        duration = pd.to_numeric(run_ends.get("state_duration", pd.Series(dtype=float)), errors="coerce")
        row["avg_state_duration"] = _mean(duration)
        row["median_state_duration"] = _median(duration)
        row["most_common_next_state"] = _most_common(state_records.get("next_state", pd.Series(dtype="string")))
        row["transition_to_emerging_leader_rate"] = _rate_to_state(state_records, "Emerging Leader")
        row["transition_to_confirmed_leader_rate"] = _rate_to_state(state_records, "Confirmed Leader")
        row["transition_to_breakdown_rate"] = _rate_to_state(state_records, "Breakdown")
        row["classification"], row["notes"] = _classify_row(row, min_sample_size=min_sample_size)
        rows.append(row)
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_state_transition_matrix(records: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    transitions = pd.DataFrame(columns=["state", "next_state", "state_duration"])
    if not records.empty:
        run_ends = (
            records.sort_values(["symbol", "date"])
            .groupby("state_run_id", as_index=False)
            .tail(1)
        )
        transitions = run_ends[
            run_ends["next_state"].notna()
            & (run_ends["next_state"].astype("string") != run_ends["state"].astype("string"))
        ][["state", "next_state", "state_duration"]]

    for from_state in STATES:
        from_records = transitions[transitions["state"] == from_state]
        total = int(len(from_records))
        for to_state in STATES:
            pair_records = from_records[from_records["next_state"] == to_state]
            count = int(len(pair_records))
            durations = pd.to_numeric(pair_records.get("state_duration", pd.Series(dtype=float)), errors="coerce")
            rows.append(
                {
                    "from_state": from_state,
                    "to_state": to_state,
                    "transition_count": count,
                    "transition_probability": float(count / total) if total else 0.0,
                    "avg_duration_before_transition": _mean(durations),
                    "median_duration_before_transition": _median(durations),
                }
            )
    return pd.DataFrame(rows, columns=TRANSITION_COLUMNS)


def run_state_research(
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    benchmark_name: str = "MEME_BASKET",
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    records = build_state_research_records(
        analysis_frames,
        timeframe=timeframe,
        benchmark_name=benchmark_name,
        entry_lag_bars=entry_lag_bars,
    )
    summary = summarize_state_research_records(records, min_sample_size=min_sample_size)
    transition_matrix = build_state_transition_matrix(records)
    return summary, records, transition_matrix
