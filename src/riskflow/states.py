from __future__ import annotations

import math
from numbers import Real

import pandas as pd

from .state_registry import STATE_MODEL_V0, get_state_model_spec


VALID_STATES = set(get_state_model_spec(STATE_MODEL_V0).states)
STATE_DETAIL_COLUMNS = ["state", "state_model", "state_confidence", "state_reason", "state_tags"]


def _is_number(value: object) -> bool:
    return isinstance(value, Real) and not math.isnan(float(value))


def _bounded(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _state_tags(
    *,
    final: float,
    relative: float,
    viscosity: float,
    compression: float,
    signal_slope: float,
    grad_slope: float,
    previous_final: float,
    previous_viscosity: float,
) -> list[str]:
    tags: list[str] = []
    above_viscosity = final > viscosity

    tags.append("above_viscosity" if above_viscosity else "below_viscosity")
    tags.append("relative_positive" if relative > 0.0 else "relative_negative")
    tags.append("signal_positive" if final > 0.0 else "signal_negative")

    if abs(final) < 0.25 and abs(relative) < 0.25:
        tags.append("dead_money")
    if abs(final) < 0.35:
        tags.append("near_zero")
    if not math.isnan(compression) and compression >= 70.0:
        tags.append("compressed")
    if not math.isnan(compression) and compression < 35.0:
        tags.append("expanded")
    if final > 2.0:
        tags.append("overheated")
    tags.append("signal_slope_rising" if signal_slope >= 0.0 else "signal_slope_falling")
    tags.append("gradient_rising" if grad_slope >= 0.0 else "rolling_over")

    previous_values_valid = _is_number(previous_final) and _is_number(previous_viscosity)
    if previous_values_valid and above_viscosity and float(previous_final) <= float(previous_viscosity):
        tags.append("viscosity_reclaim")
    if _is_number(previous_final) and final > 0.0 and float(previous_final) <= 0.0:
        tags.append("zero_reclaim")

    return sorted(set(tags))


def _unknown_details(reason: str) -> dict[str, object]:
    return {
        "state": "Unknown",
        "state_model": STATE_MODEL_V0,
        "state_confidence": 0.0,
        "state_reason": reason,
        "state_tags": "",
    }


def classify_state_details(row: pd.Series) -> dict[str, object]:
    final_signal = row.get("final_signal")
    relative_component = row.get("relative_component")
    viscosity = row.get("viscosity")
    compression_score = row.get("compression_score")
    slope = row.get("signal_slope", 0.0)
    gradient_slope = row.get("gradient_slope", 0.0)
    previous_final = row.get("previous_final_signal", math.nan)
    previous_viscosity = row.get("previous_viscosity", math.nan)

    if not (_is_number(final_signal) and _is_number(relative_component)):
        return _unknown_details("missing final signal or relative component")
    if not _is_number(viscosity):
        return _unknown_details("missing viscosity baseline")

    final = float(final_signal)
    relative = float(relative_component)
    viscosity_value = float(viscosity)
    compression = float(compression_score) if _is_number(compression_score) else math.nan
    signal_slope = float(slope) if _is_number(slope) else 0.0
    grad_slope = float(gradient_slope) if _is_number(gradient_slope) else 0.0
    above_viscosity = final > viscosity_value
    tags = _state_tags(
        final=final,
        relative=relative,
        viscosity=viscosity_value,
        compression=compression,
        signal_slope=signal_slope,
        grad_slope=grad_slope,
        previous_final=float(previous_final) if _is_number(previous_final) else math.nan,
        previous_viscosity=float(previous_viscosity) if _is_number(previous_viscosity) else math.nan,
    )

    state = "Unknown"
    confidence = 25.0
    reason = "mixed signal without a clean lifecycle classification"

    if final > 2.0 and (math.isnan(compression) or compression < 45.0):
        state = "Overheated"
        confidence = 80.0 + min(15.0, (final - 2.0) * 10.0)
        reason = "signal is highly extended while compression is low or unavailable"
    elif final > 1.0 and not above_viscosity and grad_slope < 0.0:
        state = "Distribution"
        confidence = 75.0 + min(15.0, (final - viscosity_value) * -5.0 if final < viscosity_value else 0.0)
        reason = "strong prior signal is below viscosity while the gradient is rolling over"
    elif final < 0.0 and not above_viscosity and relative < 0.0:
        state = "Breakdown"
        confidence = 75.0 + min(15.0, abs(final) * 5.0 + abs(relative) * 5.0)
        reason = "negative signal, negative relative strength, and below viscosity"
    elif _is_number(compression_score) and compression >= 70.0 and -1.5 <= final <= 0.5:
        state = "Compression"
        confidence = 65.0 + min(25.0, (compression - 70.0) * 0.6 + max(0.0, 0.5 - abs(final)) * 10.0)
        reason = "asset is compressed while the signal remains early rather than extended"
    elif (
        relative > 0.0
        and final < 0.5
        and _is_number(compression_score)
        and compression >= 50.0
        and signal_slope >= 0.0
    ):
        state = "Relative Accumulation"
        confidence = 70.0 + min(20.0, relative * 10.0 + signal_slope * 20.0)
        reason = "relative strength is positive or improving while setup remains compressed and early"
    elif above_viscosity and relative > 0.0 and final < 1.5:
        state = "Emerging Leader"
        confidence = 72.0 + min(18.0, relative * 8.0 + max(0.0, final - viscosity_value) * 8.0)
        reason = "signal is above viscosity with positive relative strength before major extension"
    elif final > 0.0 and above_viscosity and relative > 0.0:
        state = "Confirmed Leader"
        confidence = 78.0 + min(17.0, final * 4.0 + relative * 6.0)
        reason = "positive signal, positive relative strength, and above viscosity"
    elif final < 0.0 and relative < 0.0:
        state = "Weak"
        confidence = 60.0 + min(20.0, abs(final) * 5.0 + abs(relative) * 5.0)
        reason = "signal and relative strength are both negative"
    elif abs(final) < 0.25 and abs(relative) < 0.25:
        state = "Dead Money"
        confidence = 55.0 + min(20.0, max(0.0, 0.25 - abs(final)) * 30.0)
        reason = "signal and relative strength are both close to neutral"

    return {
        "state": state,
        "state_model": STATE_MODEL_V0,
        "state_confidence": round(_bounded(confidence), 2),
        "state_reason": reason,
        "state_tags": ",".join(tags),
    }


def classify_state(row: pd.Series) -> str:
    return str(classify_state_details(row)["state"])


def classify_state_frame(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    if "gradient_driver" in working.columns:
        working["gradient_slope"] = working["gradient_driver"].diff()
    else:
        working["gradient_slope"] = 0.0
    working["previous_final_signal"] = working["final_signal"].shift(1) if "final_signal" in working.columns else math.nan
    working["previous_viscosity"] = working["viscosity"].shift(1) if "viscosity" in working.columns else math.nan

    details = pd.DataFrame(
        [classify_state_details(row) for _, row in working.iterrows()],
        index=working.index,
        columns=STATE_DETAIL_COLUMNS,
    )
    details["state"] = details["state"].astype("string")
    details["state_model"] = details["state_model"].astype("string")
    details["state_reason"] = details["state_reason"].astype("string")
    details["state_tags"] = details["state_tags"].astype("string")
    details["state_confidence"] = pd.to_numeric(details["state_confidence"], errors="coerce").fillna(0.0)
    return details


def classify_states(frame: pd.DataFrame) -> pd.Series:
    return classify_state_frame(frame)["state"].astype("string")
