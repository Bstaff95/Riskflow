from __future__ import annotations

import math

import pandas as pd


VALID_STATES = {
    "Dead Money",
    "Weak",
    "Compression",
    "Relative Accumulation",
    "Emerging Leader",
    "Confirmed Leader",
    "Overheated",
    "Distribution",
    "Breakdown",
    "Unknown",
}


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not math.isnan(float(value))


def classify_state(row: pd.Series) -> str:
    final_signal = row.get("final_signal")
    relative_component = row.get("relative_component")
    viscosity = row.get("viscosity")
    compression_score = row.get("compression_score")
    slope = row.get("signal_slope", 0.0)
    gradient_slope = row.get("gradient_slope", 0.0)

    if not (_is_number(final_signal) and _is_number(relative_component)):
        return "Unknown"
    if not _is_number(viscosity):
        return "Unknown"

    final = float(final_signal)
    relative = float(relative_component)
    viscosity_value = float(viscosity)
    compression = float(compression_score) if _is_number(compression_score) else math.nan
    signal_slope = float(slope) if _is_number(slope) else 0.0
    grad_slope = float(gradient_slope) if _is_number(gradient_slope) else 0.0
    above_viscosity = final > viscosity_value

    if final > 2.0 and (math.isnan(compression) or compression < 45.0):
        return "Overheated"
    if final > 1.0 and not above_viscosity and grad_slope < 0.0:
        return "Distribution"
    if final < 0.0 and not above_viscosity and relative < 0.0:
        return "Breakdown"
    if _is_number(compression_score) and compression >= 70.0 and -1.5 <= final <= 0.5:
        return "Compression"
    if (
        relative > 0.0
        and final < 0.5
        and _is_number(compression_score)
        and compression >= 50.0
        and signal_slope >= 0.0
    ):
        return "Relative Accumulation"
    if above_viscosity and relative > 0.0 and final < 1.5:
        return "Emerging Leader"
    if final > 0.0 and above_viscosity and relative > 0.0:
        return "Confirmed Leader"
    if final < 0.0 and relative < 0.0:
        return "Weak"
    if abs(final) < 0.25 and abs(relative) < 0.25:
        return "Dead Money"
    return "Unknown"


def classify_states(frame: pd.DataFrame) -> pd.Series:
    working = frame.copy()
    if "gradient_driver" in working.columns:
        working["gradient_slope"] = working["gradient_driver"].diff()
    else:
        working["gradient_slope"] = 0.0
    return working.apply(classify_state, axis=1).astype("string")

