from __future__ import annotations

import math

import pandas as pd


def _bounded(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _number(value: object, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(numeric):
        return default
    return numeric


def score_opportunity(row: pd.Series) -> float:
    final_signal = _number(row.get("final_signal"), default=math.nan)
    relative_component = _number(row.get("relative_component"), default=math.nan)
    compression_score = _number(row.get("compression_score"), default=math.nan)
    viscosity = _number(row.get("viscosity"), default=math.nan)
    state = str(row.get("state", "Unknown"))

    if any(math.isnan(value) for value in [final_signal, relative_component, compression_score, viscosity]):
        return 0.0

    relative_strength_score = _bounded((relative_component + 1.0) / 3.0, 0.0, 1.0) * 30.0
    compression_contribution = _bounded(compression_score, 0.0, 100.0) / 100.0 * 25.0

    setup_by_state = {
        "Relative Accumulation": 22.0,
        "Emerging Leader": 25.0,
        "Confirmed Leader": 18.0,
        "Compression": 16.0,
        "Dead Money": 6.0,
        "Weak": 3.0,
        "Breakdown": 0.0,
        "Distribution": 3.0,
        "Overheated": 5.0,
        "Unknown": 0.0,
    }
    setup_readiness = setup_by_state.get(state, 0.0)

    trend_confirmation = 0.0
    if final_signal > viscosity:
        trend_confirmation += 7.0
    if final_signal > 0.0:
        trend_confirmation += 3.0

    overextension_penalty = 0.0
    if final_signal > 2.0:
        overextension_penalty += min(20.0, (final_signal - 2.0) * 12.0 + 5.0)
    if compression_score < 25.0:
        overextension_penalty += (25.0 - compression_score) / 25.0 * 8.0
    if state == "Overheated":
        overextension_penalty += 8.0

    score = (
        relative_strength_score
        + compression_contribution
        + setup_readiness
        + trend_confirmation
        - overextension_penalty
    )
    return round(_bounded(score, 0.0, 100.0), 2)


def score_dataframe(frame: pd.DataFrame) -> pd.Series:
    return frame.apply(score_opportunity, axis=1).astype(float)

