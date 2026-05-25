from __future__ import annotations

import numpy as np
import pandas as pd

from .scoring import score_opportunity


SETUP_QUALITY_COLUMNS = [
    "leader_quality_score",
    "compression_quality_score",
    "relative_accumulation_score",
    "setup_readiness_score",
    "extension_risk_score",
    "data_quality_score",
    "trader_score_v0",
    "opportunity_score_v0",
    "setup_state_v0",
    "setup_tags",
    "setup_notes",
]


def _numeric(frame: pd.DataFrame, column: str, default: float = np.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").astype(float)


def _bounded(series: pd.Series, lower: float = 0.0, upper: float = 100.0) -> pd.Series:
    return series.clip(lower=lower, upper=upper)


def _zero_cross_up(series: pd.Series) -> pd.Series:
    return ((series > 0.0) & (series.shift(1) <= 0.0)).fillna(False)


def calculate_setup_quality(frame: pd.DataFrame) -> pd.DataFrame:
    final_signal = _numeric(frame, "final_signal")
    relative_component = _numeric(frame, "relative_component")
    viscosity = _numeric(frame, "viscosity")
    compression = _numeric(frame, "compression_score_v0")
    if compression.isna().all():
        compression = _numeric(frame, "compression_score")
    compression_stability = _numeric(frame, "compression_stability", default=0.0).fillna(0.0)
    compression_duration = _numeric(frame, "compression_duration", default=0.0).fillna(0.0)
    flat_close_bars = _numeric(frame, "flat_close_bars", default=0.0).fillna(0.0)
    gradient_driver = _numeric(frame, "gradient_driver")
    if "stale_data_flag" in frame.columns:
        stale_data = frame["stale_data_flag"].astype("boolean").fillna(False).astype(bool)
    else:
        stale_data = pd.Series(False, index=frame.index, dtype=bool)

    output = pd.DataFrame(index=frame.index)

    relative_level = ((relative_component + 1.0) / 3.0).clip(lower=0.0, upper=1.0)
    signal_level = ((final_signal + 1.0) / 3.0).clip(lower=0.0, upper=1.0)
    output["leader_quality_score"] = _bounded((relative_level * 0.65 + signal_level * 0.35) * 100.0).fillna(0.0)

    persistence_boost = (compression_stability / 100.0 * 0.35) + (compression_duration.clip(upper=10.0) / 10.0 * 0.15)
    output["compression_quality_score"] = _bounded(compression * (0.50 + persistence_boost)).fillna(0.0)
    output.loc[stale_data, "compression_quality_score"] = output.loc[stale_data, "compression_quality_score"].clip(upper=10.0)

    relative_slope = relative_component.diff()
    relative_improvement = (relative_slope / 0.15).clip(lower=0.0, upper=1.0)
    relative_positive = ((relative_component + 0.25) / 1.25).clip(lower=0.0, upper=1.0)
    compression_context = (compression / 100.0).clip(lower=0.0, upper=1.0)
    output["relative_accumulation_score"] = _bounded(
        (relative_improvement * 0.40 + relative_positive * 0.30 + compression_context * 0.30) * 100.0
    ).fillna(0.0)

    above_viscosity = (final_signal > viscosity).fillna(False)
    viscosity_reclaim = (above_viscosity & ~(final_signal.shift(1) > viscosity.shift(1)).fillna(False)).fillna(False)
    zero_reclaim = _zero_cross_up(final_signal)
    minus_1_5_reclaim = ((final_signal > -1.5) & (final_signal.shift(1) <= -1.5)).fillna(False)
    gradient_turn_up = (gradient_driver.diff() > 0.0).fillna(False)
    near_confirmation = (
        (relative_component > 0.0)
        & (compression >= 50.0)
        & (final_signal.between(-0.25, 0.75) | above_viscosity)
    ).fillna(False)

    output["setup_readiness_score"] = _bounded(
        above_viscosity.astype(float) * 25.0
        + viscosity_reclaim.astype(float) * 20.0
        + zero_reclaim.astype(float) * 20.0
        + minus_1_5_reclaim.astype(float) * 10.0
        + gradient_turn_up.astype(float) * 10.0
        + near_confirmation.astype(float) * 15.0
    )

    relative_log = _numeric(frame, "relative_log")
    recent_relative_return_7 = np.expm1(relative_log - relative_log.shift(7)).fillna(0.0)
    recent_relative_return_14 = np.expm1(relative_log - relative_log.shift(14)).fillna(0.0)
    gradient_rollover = ((gradient_driver.diff() < 0.0) & (final_signal > 1.0)).fillna(False)
    distance_from_viscosity = (final_signal - viscosity).clip(lower=0.0)
    output["extension_risk_score"] = _bounded(
        ((final_signal - 2.0).clip(lower=0.0) / 1.5).clip(upper=1.0) * 35.0
        + ((35.0 - compression).clip(lower=0.0) / 35.0).clip(upper=1.0) * 25.0
        + (recent_relative_return_7.clip(lower=0.0, upper=0.50) / 0.50) * 15.0
        + (recent_relative_return_14.clip(lower=0.0, upper=0.80) / 0.80) * 10.0
        + gradient_rollover.astype(float) * 10.0
        + (distance_from_viscosity.clip(upper=1.5) / 1.5) * 5.0
    ).fillna(0.0)

    output["data_quality_score"] = _bounded(
        100.0
        - stale_data.astype(float) * 70.0
        - (flat_close_bars.clip(upper=10.0) / 10.0) * 20.0
        - ((compression >= 90.0) & stale_data).astype(float) * 10.0
    ).fillna(100.0)

    output["trader_score_v0"] = _bounded(
        output["leader_quality_score"] * 0.20
        + output["compression_quality_score"] * 0.20
        + output["relative_accumulation_score"] * 0.25
        + output["setup_readiness_score"] * 0.25
        + output["data_quality_score"] * 0.10
        - output["extension_risk_score"] * 0.25
    ).fillna(0.0)

    output["opportunity_score_v0"] = frame.apply(score_opportunity, axis=1).astype(float)
    output["setup_state_v0"] = _setup_state(output)
    output["setup_tags"] = _setup_tags(
        compressed=(compression >= 70.0).fillna(False),
        relative_strength_rising=(relative_slope > 0.0).fillna(False),
        viscosity_reclaim=viscosity_reclaim,
        zero_reclaim=zero_reclaim,
        near_confirmation=near_confirmation,
        extended=((final_signal > 2.0) | (compression < 25.0)).fillna(False),
        rolling_over=gradient_rollover,
        high_drawdown_risk=(output["extension_risk_score"] >= 70.0).fillna(False),
    )
    output["setup_notes"] = _setup_notes(output, stale_data)
    return output[SETUP_QUALITY_COLUMNS]


def _setup_state(frame: pd.DataFrame) -> pd.Series:
    state = pd.Series("No Setup", index=frame.index, dtype="string")
    state = state.mask(frame["compression_quality_score"] >= 70.0, "Compression")
    state = state.mask(frame["relative_accumulation_score"] >= 65.0, "Relative Accumulation")
    state = state.mask(frame["setup_readiness_score"] >= 70.0, "Setup Ready")
    state = state.mask(frame["extension_risk_score"] >= 70.0, "Extended Risk")
    return state


def _setup_tags(**masks: pd.Series) -> pd.Series:
    rows: list[str] = []
    names = {
        "compressed": "compressed",
        "relative_strength_rising": "relative_strength_rising",
        "viscosity_reclaim": "viscosity_reclaim",
        "zero_reclaim": "zero_reclaim",
        "near_confirmation": "near_confirmation",
        "extended": "extended",
        "rolling_over": "rolling_over",
        "high_drawdown_risk": "high_drawdown_risk",
    }
    index = next(iter(masks.values())).index if masks else pd.Index([])
    for idx in index:
        tags = [label for key, label in names.items() if bool(masks[key].loc[idx])]
        rows.append(",".join(tags))
    return pd.Series(rows, index=index, dtype="string")


def _setup_notes(frame: pd.DataFrame, stale_data: pd.Series) -> pd.Series:
    rows: list[str] = []
    for idx in frame.index:
        parts: list[str] = []
        if bool(stale_data.loc[idx]):
            parts.append("stale or inactive data; compression quality capped")
        if float(frame.loc[idx, "data_quality_score"]) < 60.0:
            parts.append("data quality weak")
        if float(frame.loc[idx, "extension_risk_score"]) >= 70.0:
            parts.append("extension risk high")
        if float(frame.loc[idx, "setup_readiness_score"]) >= 70.0:
            parts.append("setup readiness high")
        if float(frame.loc[idx, "relative_accumulation_score"]) >= 65.0:
            parts.append("relative accumulation improving")
        if float(frame.loc[idx, "compression_quality_score"]) >= 70.0:
            parts.append("persistent compression")
        rows.append("; ".join(parts[:3]))
    return pd.Series(rows, index=frame.index, dtype="string")
