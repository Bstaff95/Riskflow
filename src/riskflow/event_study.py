from __future__ import annotations

import numpy as np
import pandas as pd


HORIZONS = (3, 7, 14, 30)
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


def _future_return(series: pd.Series, horizon: int) -> pd.Series:
    return series.shift(-horizon) / series - 1.0


def _future_relative_return(target: pd.Series, benchmark: pd.Series, horizon: int) -> pd.Series:
    target_return = _future_return(target, horizon)
    benchmark_return = _future_return(benchmark, horizon)
    return ((1.0 + target_return) / (1.0 + benchmark_return)) - 1.0


def _forward_max_drawdown(close: pd.Series, horizon: int) -> pd.Series:
    values = pd.to_numeric(close, errors="coerce").to_numpy(dtype=float)
    output = np.full(len(values), np.nan, dtype=float)
    for idx, current in enumerate(values):
        if np.isnan(current) or current == 0.0:
            continue
        future = values[idx + 1 : idx + horizon + 1]
        future = future[~np.isnan(future)]
        if len(future) == 0:
            continue
        output[idx] = float(np.min(future / current - 1.0))
    return pd.Series(output, index=close.index)


def event_records_for_asset(symbol: str, frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    target = working["target"]
    benchmark = working["benchmark"]
    masks = detect_events(working)

    metric_frame = pd.DataFrame(index=working.index)
    for horizon in HORIZONS:
        metric_frame[f"forward_return_{horizon}"] = _future_return(target, horizon)
        metric_frame[f"forward_relative_return_{horizon}"] = _future_relative_return(target, benchmark, horizon)
    metric_frame["max_drawdown_14"] = _forward_max_drawdown(target, 14)
    metric_frame["max_drawdown_30"] = _forward_max_drawdown(target, 30)

    records: list[dict[str, object]] = []
    for event_name, mask in masks.items():
        event_dates = working.index[mask]
        for event_date in event_dates:
            record: dict[str, object] = {
                "symbol": symbol,
                "date": event_date,
                "event": event_name,
            }
            for column in metric_frame.columns:
                record[column] = metric_frame.loc[event_date, column]
            records.append(record)
    return pd.DataFrame.from_records(records)


def summarize_event_records(records: pd.DataFrame) -> pd.DataFrame:
    def numeric_column(frame: pd.DataFrame, column: str) -> pd.Series:
        if frame.empty or column not in frame.columns:
            return pd.Series(dtype=float)
        return pd.to_numeric(frame[column], errors="coerce")

    def mean_or_nan(series: pd.Series) -> float:
        valid = series.dropna()
        return float(valid.mean()) if not valid.empty else np.nan

    def median_or_nan(series: pd.Series) -> float:
        valid = series.dropna()
        return float(valid.median()) if not valid.empty else np.nan

    def hit_rate_or_nan(series: pd.Series) -> float:
        valid = series.dropna()
        return float((valid > 0.0).mean()) if not valid.empty else np.nan

    rows: list[dict[str, object]] = []
    for event_name in EVENT_NAMES:
        event_records = records[records["event"] == event_name] if not records.empty else pd.DataFrame()
        row: dict[str, object] = {
            "event": event_name,
            "sample_size": int(len(event_records)),
        }
        for horizon in HORIZONS:
            forward_return = numeric_column(event_records, f"forward_return_{horizon}")
            relative_return = numeric_column(event_records, f"forward_relative_return_{horizon}")
            row[f"avg_forward_return_{horizon}"] = mean_or_nan(forward_return)
            row[f"median_forward_return_{horizon}"] = median_or_nan(forward_return)
            row[f"avg_forward_relative_return_{horizon}"] = mean_or_nan(relative_return)
            row[f"median_forward_relative_return_{horizon}"] = median_or_nan(relative_return)
            row[f"hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(relative_return)
        for horizon in (14, 30):
            drawdown = numeric_column(event_records, f"max_drawdown_{horizon}")
            row[f"avg_max_drawdown_{horizon}"] = mean_or_nan(drawdown)
            row[f"median_max_drawdown_{horizon}"] = median_or_nan(drawdown)
        rows.append(row)

    return pd.DataFrame(rows, columns=summary_columns())


def run_event_study(analysis_frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    records = [
        event_records_for_asset(symbol, frame)
        for symbol, frame in analysis_frames.items()
        if not frame.empty
    ]
    event_records = pd.concat(records, ignore_index=True) if records else pd.DataFrame()
    return summarize_event_records(event_records), event_records
