from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .config import UniverseConfig
from .flow_graph import (
    NON_SUPPORTIVE_CHAIN_LABELS,
    SUPPORTIVE_CHAIN_LABELS,
    append_chain_context,
)
from .research_outcomes import (
    HORIZONS,
    entry_date_at,
    event_cluster_id,
    forward_max_drawdown,
    forward_relative_return,
    hit_rate_or_nan,
    max_share,
    median_or_nan,
)
from .state_registry import STATE_MODEL_V0, get_state_model_spec
from .state_research import _state_runs
from .transition_registry import TRANSITION_RESEARCH_V0


DEFAULT_MIN_SAMPLE_SIZE = 5
DEFAULT_ENTRY_LAG_BARS = 1
MAX_SYMBOL_SHARE = 0.55
MAX_CLUSTER_SHARE = 0.60
WILSON_Z_80 = 1.2815515655446004

STATES = get_state_model_spec(STATE_MODEL_V0).states

RECORD_COLUMNS = [
    "symbol",
    "transition_date",
    "timeframe",
    "benchmark",
    "transition_model",
    "state_model",
    "from_state",
    "to_state",
    "from_state_duration",
    "state_run_id",
    "chain_label",
    "chain_support_group",
    "mtf_leader_context",
    "mtf_condition_group",
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
    "transition_model",
    "state_model",
    "from_state",
    "to_state",
    "sample_size",
    "from_state_transition_count",
    "unique_symbols",
    "unique_event_dates",
    "unique_event_clusters",
    "max_symbol_transition_share",
    "max_cluster_transition_share",
    "observed_transition_rate",
    "wilson_80_lower",
    "wilson_80_upper",
    "median_duration_before_transition",
    "median_forward_relative_return_3",
    "hit_rate_forward_relative_return_3",
    "median_forward_relative_return_7",
    "hit_rate_forward_relative_return_7",
    "median_forward_relative_return_14",
    "hit_rate_forward_relative_return_14",
    "median_forward_relative_return_30",
    "hit_rate_forward_relative_return_30",
    "median_max_drawdown_14",
    "median_max_drawdown_30",
    "classification",
    "notes",
]

CONDITIONED_COLUMNS = [
    "transition_model",
    "condition_type",
    "condition_group",
    "from_state",
    "to_state",
    "sample_size",
    "condition_from_state_transition_count",
    "unique_symbols",
    "unique_event_clusters",
    "max_symbol_transition_share",
    "max_cluster_transition_share",
    "observed_transition_rate",
    "wilson_80_lower",
    "wilson_80_upper",
    "median_forward_relative_return_14",
    "hit_rate_forward_relative_return_14",
    "median_forward_relative_return_30",
    "hit_rate_forward_relative_return_30",
    "median_max_drawdown_30",
    "classification",
    "notes",
]


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").astype(float)


def _chain_support_group(row: pd.Series) -> str:
    chain_label = str(row.get("chain_label", ""))
    if chain_label in SUPPORTIVE_CHAIN_LABELS:
        return "supportive"
    if chain_label in NON_SUPPORTIVE_CHAIN_LABELS:
        return "non_supportive"
    return "incomplete"


def _mtf_condition_group(row: pd.Series) -> str:
    if "mtf_leader_context" not in row.index:
        return "not_requested"
    context = str(row.get("mtf_leader_context", ""))
    if not context or context == "<NA>" or context == "Incomplete Data":
        return "incomplete"
    if context in {"Aligned Leader", "Early HTF Turn"}:
        return "aligned"
    return "non_aligned"


def _wilson_interval(successes: int, total: int, z: float = WILSON_Z_80) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    p_hat = successes / total
    denominator = 1.0 + z**2 / total
    center = (p_hat + z**2 / (2.0 * total)) / denominator
    margin = (z / denominator) * math.sqrt((p_hat * (1.0 - p_hat) / total) + (z**2 / (4.0 * total**2)))
    return float(max(0.0, center - margin)), float(min(1.0, center + margin))


def transition_records_for_asset(
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
    run_id, duration, next_state = _state_runs(state)

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

    working = frame.copy()
    working["_state"] = state
    working["_state_model"] = state_model
    working["_state_run_id"] = run_id
    working["_state_duration"] = duration
    working["_next_state"] = next_state

    run_ends = working.sort_index().groupby("_state_run_id", as_index=False).tail(1)
    run_ends = run_ends[
        run_ends["_next_state"].notna()
        & (run_ends["_next_state"].astype("string") != run_ends["_state"].astype("string"))
    ]

    records: list[dict[str, object]] = []
    for transition_date, row in run_ends.iterrows():
        if pd.isna(target.loc[transition_date]) or pd.isna(benchmark.loc[transition_date]):
            continue
        transition_position = frame.index.get_loc(transition_date)
        record: dict[str, object] = {
            "symbol": symbol,
            "transition_date": transition_date,
            "timeframe": timeframe,
            "benchmark": benchmark_name,
            "transition_model": TRANSITION_RESEARCH_V0,
            "state_model": row.get("_state_model", STATE_MODEL_V0),
            "from_state": row.get("_state", "Unknown"),
            "to_state": row.get("_next_state", "Unknown"),
            "from_state_duration": int(row.get("_state_duration", 0)),
            "state_run_id": f"{symbol}:{int(row.get('_state_run_id'))}",
            "chain_label": row.get("chain_label", "Incomplete Chain"),
            "chain_support_group": _chain_support_group(row),
            "mtf_leader_context": row.get("mtf_leader_context", "not_requested"),
            "mtf_condition_group": _mtf_condition_group(row),
            "entry_lag_bars": entry_lag_bars,
            "entry_date": entry_date_at(frame.index, transition_position, entry_lag_bars),
            "event_cluster_id": event_cluster_id(transition_date),
        }
        for column in metrics.columns:
            record[column] = metrics.loc[transition_date, column]
        records.append(record)
    return pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)


def build_transition_research_records(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> pd.DataFrame:
    enriched = append_chain_context(universe, analysis_frames, timeframe=timeframe)
    records = [
        transition_records_for_asset(
            symbol,
            frame,
            timeframe=timeframe,
            benchmark_name=universe.benchmark.name,
            entry_lag_bars=entry_lag_bars,
        )
        for symbol, frame in enriched.items()
        if not frame.empty
    ]
    non_empty = [record for record in records if not record.empty]
    return pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame(columns=RECORD_COLUMNS)


def _classify_pair(row: dict[str, object], *, min_sample_size: int) -> tuple[str, str]:
    sample_size = int(row["sample_size"])
    if sample_size < min_sample_size:
        return "inconclusive", f"sample size below min_sample_size={min_sample_size}"
    if float(row["max_symbol_transition_share"]) > MAX_SYMBOL_SHARE:
        return "fragile", "too many transition observations come from one symbol"
    if float(row["max_cluster_transition_share"]) > MAX_CLUSTER_SHARE:
        return "fragile", "too many transition observations come from one calendar cluster"

    median_14 = float(row["median_forward_relative_return_14"])
    median_30 = float(row["median_forward_relative_return_30"])
    hit_14 = float(row["hit_rate_forward_relative_return_14"])
    drawdown_30 = float(row["median_max_drawdown_30"])
    if any(math.isnan(value) for value in (median_14, median_30, hit_14)):
        return "inconclusive", "insufficient forward-relative-return data"
    if median_14 > 0.0 and median_30 > 0.0 and hit_14 >= 0.55 and (math.isnan(drawdown_30) or drawdown_30 > -0.25):
        return "useful", "positive transition outcomes with acceptable drawdown evidence"
    if median_14 > 0.0 or median_30 > 0.0 or hit_14 >= 0.52:
        return "watchlist", "mixed but potentially useful transition evidence"
    return "fragile", "transition has weak or negative forward relative-return evidence"


def _pair_row(
    records: pd.DataFrame,
    pair_records: pd.DataFrame,
    *,
    from_state: str,
    to_state: str,
    denominator: int,
    min_sample_size: int,
) -> dict[str, object]:
    sample_size = int(len(pair_records))
    lower, upper = _wilson_interval(sample_size, denominator)
    row: dict[str, object] = {
        "transition_model": TRANSITION_RESEARCH_V0,
        "state_model": STATE_MODEL_V0,
        "from_state": from_state,
        "to_state": to_state,
        "sample_size": sample_size,
        "from_state_transition_count": int(denominator),
        "unique_symbols": int(pair_records["symbol"].nunique()) if not pair_records.empty else 0,
        "unique_event_dates": int(pair_records["transition_date"].nunique()) if not pair_records.empty else 0,
        "unique_event_clusters": int(pair_records["event_cluster_id"].nunique()) if not pair_records.empty else 0,
        "max_symbol_transition_share": max_share(pair_records["symbol"]) if not pair_records.empty else np.nan,
        "max_cluster_transition_share": max_share(pair_records["event_cluster_id"]) if not pair_records.empty else np.nan,
        "observed_transition_rate": float(sample_size / denominator) if denominator else 0.0,
        "wilson_80_lower": lower,
        "wilson_80_upper": upper,
        "median_duration_before_transition": median_or_nan(pair_records.get("from_state_duration", pd.Series(dtype=float))),
    }
    for horizon in HORIZONS:
        returns = pair_records.get(f"forward_relative_return_{horizon}", pd.Series(dtype=float))
        row[f"median_forward_relative_return_{horizon}"] = median_or_nan(returns)
        row[f"hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(returns)
    for horizon in (14, 30):
        row[f"median_max_drawdown_{horizon}"] = median_or_nan(
            pair_records.get(f"max_drawdown_{horizon}", pd.Series(dtype=float)),
        )
    row["classification"], row["notes"] = _classify_pair(row, min_sample_size=min_sample_size)
    return row


def summarize_transition_research_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for from_state in STATES:
        from_records = records[records["from_state"] == from_state] if not records.empty else pd.DataFrame(columns=RECORD_COLUMNS)
        denominator = int(len(from_records))
        for to_state in STATES:
            pair_records = from_records[from_records["to_state"] == to_state]
            rows.append(
                _pair_row(
                    records,
                    pair_records,
                    from_state=from_state,
                    to_state=to_state,
                    denominator=denominator,
                    min_sample_size=min_sample_size,
                )
            )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def build_transition_matrix_unconditional(records: pd.DataFrame) -> pd.DataFrame:
    return summarize_transition_research_records(records, min_sample_size=math.inf)[
        [
            "transition_model",
            "state_model",
            "from_state",
            "to_state",
            "sample_size",
            "from_state_transition_count",
            "observed_transition_rate",
            "wilson_80_lower",
            "wilson_80_upper",
            "median_duration_before_transition",
        ]
    ].rename(columns={"sample_size": "transition_count"})


def _conditioned_row(
    group_records: pd.DataFrame,
    *,
    condition_type: str,
    condition_group: str,
    from_state: str,
    to_state: str,
    denominator: int,
    min_sample_size: int,
) -> dict[str, object]:
    pair_records = group_records[(group_records["from_state"] == from_state) & (group_records["to_state"] == to_state)]
    sample_size = int(len(pair_records))
    lower, upper = _wilson_interval(sample_size, denominator)
    row: dict[str, object] = {
        "transition_model": TRANSITION_RESEARCH_V0,
        "condition_type": condition_type,
        "condition_group": condition_group,
        "from_state": from_state,
        "to_state": to_state,
        "sample_size": sample_size,
        "condition_from_state_transition_count": int(denominator),
        "unique_symbols": int(pair_records["symbol"].nunique()) if not pair_records.empty else 0,
        "unique_event_clusters": int(pair_records["event_cluster_id"].nunique()) if not pair_records.empty else 0,
        "max_symbol_transition_share": max_share(pair_records["symbol"]) if not pair_records.empty else np.nan,
        "max_cluster_transition_share": max_share(pair_records["event_cluster_id"]) if not pair_records.empty else np.nan,
        "observed_transition_rate": float(sample_size / denominator) if denominator else 0.0,
        "wilson_80_lower": lower,
        "wilson_80_upper": upper,
        "median_forward_relative_return_14": median_or_nan(pair_records.get("forward_relative_return_14", pd.Series(dtype=float))),
        "hit_rate_forward_relative_return_14": hit_rate_or_nan(pair_records.get("forward_relative_return_14", pd.Series(dtype=float))),
        "median_forward_relative_return_30": median_or_nan(pair_records.get("forward_relative_return_30", pd.Series(dtype=float))),
        "hit_rate_forward_relative_return_30": hit_rate_or_nan(pair_records.get("forward_relative_return_30", pd.Series(dtype=float))),
        "median_max_drawdown_30": median_or_nan(pair_records.get("max_drawdown_30", pd.Series(dtype=float))),
    }
    row["classification"], row["notes"] = _classify_pair(
        {
            "sample_size": row["sample_size"],
            "max_symbol_transition_share": row["max_symbol_transition_share"],
            "max_cluster_transition_share": row["max_cluster_transition_share"],
            "median_forward_relative_return_14": row["median_forward_relative_return_14"],
            "median_forward_relative_return_30": row["median_forward_relative_return_30"],
            "hit_rate_forward_relative_return_14": row["hit_rate_forward_relative_return_14"],
            "median_max_drawdown_30": row["median_max_drawdown_30"],
        },
        min_sample_size=min_sample_size,
    )
    return row


def summarize_conditioned_transition_records(
    records: pd.DataFrame,
    *,
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    condition_groups = {
        "chain_support_group": ("supportive", "non_supportive", "incomplete"),
        "mtf_condition_group": ("aligned", "non_aligned", "incomplete", "not_requested"),
    }
    for condition_type, groups in condition_groups.items():
        for condition_group in groups:
            group_records = (
                records[records[condition_type] == condition_group]
                if not records.empty and condition_type in records.columns
                else pd.DataFrame(columns=RECORD_COLUMNS)
            )
            for from_state in STATES:
                denominator = int(len(group_records[group_records["from_state"] == from_state]))
                for to_state in STATES:
                    rows.append(
                        _conditioned_row(
                            group_records,
                            condition_type=condition_type,
                            condition_group=condition_group,
                            from_state=from_state,
                            to_state=to_state,
                            denominator=denominator,
                            min_sample_size=min_sample_size,
                        )
                    )
    return pd.DataFrame(rows, columns=CONDITIONED_COLUMNS)


def run_transition_research(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    entry_lag_bars: int = DEFAULT_ENTRY_LAG_BARS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    records = build_transition_research_records(
        universe,
        analysis_frames,
        timeframe=timeframe,
        entry_lag_bars=entry_lag_bars,
    )
    summary = summarize_transition_research_records(records, min_sample_size=min_sample_size)
    unconditional = build_transition_matrix_unconditional(records)
    conditioned = summarize_conditioned_transition_records(records, min_sample_size=min_sample_size)
    return summary, records, unconditional, conditioned
