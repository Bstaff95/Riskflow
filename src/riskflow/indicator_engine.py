from __future__ import annotations

import numpy as np
import pandas as pd

from .config import IndicatorSettings, WeightSettings
from .features import clamp_series, normalize_to_first_valid, rolling_zscore, safe_log
from .signal_registry import CORE_SIGNAL_V0, CORE_SIGNAL_V0_FORMULA_VERSION


INDICATOR_COLUMNS = [
    "target",
    "benchmark",
    "target_norm",
    "benchmark_norm",
    "price_log",
    "relative_log",
    "price_component",
    "relative_component",
    "risk_component",
    "final_signal",
    "viscosity",
    "above_viscosity",
    "gradient_driver",
    "signal_slope",
    "signal_accel",
]


def adaptive_viscosity(
    signal: pd.Series,
    lookback: int = 20,
    fast: int = 2,
    slow: int = 34,
) -> pd.Series:
    if lookback < 1:
        raise ValueError("lookback must be >= 1")
    if fast < 1 or slow < 1:
        raise ValueError("fast and slow lengths must be >= 1")

    source = pd.to_numeric(signal, errors="coerce").astype(float)
    output = pd.Series(np.nan, index=source.index, dtype=float, name="viscosity")
    fast_sc = 2.0 / (fast + 1.0)
    slow_sc = 2.0 / (slow + 1.0)
    previous = np.nan

    for idx in range(len(source)):
        value = source.iloc[idx]
        if pd.isna(value):
            continue
        if pd.isna(previous):
            previous = float(value)
            output.iloc[idx] = previous
            continue

        start = max(0, idx - lookback)
        window = source.iloc[start : idx + 1].dropna()
        if len(window) >= 2:
            change = abs(float(window.iloc[-1] - window.iloc[0]))
            volatility = float(window.diff().abs().sum())
            efficiency_ratio = change / volatility if volatility > 0.0 else 0.0
        else:
            efficiency_ratio = 0.0

        adaptive_sc = (efficiency_ratio * (fast_sc - slow_sc) + slow_sc) ** 2
        previous = previous + adaptive_sc * (float(value) - previous)
        output.iloc[idx] = previous

    return output


def _weighted_fusion(components: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    weighted = pd.DataFrame(index=components.index)
    active_weight_square = pd.DataFrame(index=components.index)

    for name, weight in weights.items():
        component = components[name]
        weighted[name] = component * weight
        active_weight_square[name] = np.where(component.notna(), weight * weight, 0.0)

    denominator = np.sqrt(active_weight_square.sum(axis=1))
    numerator = weighted.sum(axis=1, min_count=1)
    signal = numerator / denominator.replace(0.0, np.nan)
    signal.name = "final_signal"
    return signal


ENGINE_SIGNAL_ID = CORE_SIGNAL_V0
ENGINE_FORMULA_VERSION = CORE_SIGNAL_V0_FORMULA_VERSION


def calculate_core_signal_v0(
    target_close: pd.Series,
    benchmark_close: pd.Series,
    risk_series: pd.Series | None = None,
    settings: IndicatorSettings | None = None,
    weights: WeightSettings | None = None,
) -> pd.DataFrame:
    settings = settings or IndicatorSettings()
    weights = weights or WeightSettings()

    frame = pd.DataFrame(
        {
            "target": pd.to_numeric(target_close, errors="coerce"),
            "benchmark": pd.to_numeric(benchmark_close, errors="coerce"),
        }
    ).sort_index()

    frame["target_norm"] = normalize_to_first_valid(frame["target"])
    frame["benchmark_norm"] = normalize_to_first_valid(frame["benchmark"])
    frame["price_log"] = safe_log(frame["target_norm"])
    relative_ratio = frame["target_norm"] / frame["benchmark_norm"]
    frame["relative_log"] = safe_log(relative_ratio)

    frame["price_component"] = clamp_series(
        rolling_zscore(frame["price_log"], settings.z_len),
        settings.component_z_clamp,
    )
    frame["relative_component"] = clamp_series(
        rolling_zscore(frame["relative_log"], settings.z_len),
        settings.component_z_clamp,
    )

    risk_component = pd.Series(np.nan, index=frame.index, dtype=float)
    if settings.use_risk and risk_series is not None:
        aligned_risk = pd.to_numeric(risk_series.reindex(frame.index), errors="coerce")
        risk_component = clamp_series(
            rolling_zscore(safe_log(aligned_risk), settings.z_len),
            settings.component_z_clamp,
        )
    frame["risk_component"] = risk_component

    components = pd.DataFrame(
        {
            "price": frame["price_component"],
            "relative": frame["relative_component"],
            "risk": frame["risk_component"],
        },
        index=frame.index,
    )
    active_weights = {
        "price": weights.price_weight,
        "relative": weights.relative_weight,
    }
    if settings.use_risk:
        active_weights["risk"] = weights.risk_weight

    frame["final_signal"] = _weighted_fusion(components[list(active_weights)], active_weights)
    frame["viscosity"] = adaptive_viscosity(
        frame["final_signal"],
        lookback=settings.viscosity_lookback,
        fast=settings.viscosity_fast,
        slow=settings.viscosity_slow,
    )
    frame["above_viscosity"] = frame["final_signal"] > frame["viscosity"]
    frame["signal_slope"] = frame["final_signal"].diff()
    frame["signal_accel"] = frame["signal_slope"].diff()

    slope_component = rolling_zscore(frame["signal_slope"], max(2, settings.viscosity_lookback))
    accel_component = rolling_zscore(frame["signal_accel"], max(2, settings.viscosity_lookback))
    gradient_raw = (
        frame["final_signal"]
        + settings.velocity_weight * (frame["final_signal"] - frame["viscosity"])
        + settings.slope_weight * slope_component
        + settings.accel_weight * accel_component
    )
    gradient_smoothed = gradient_raw.ewm(
        span=max(1, settings.gradient_smooth_len),
        adjust=False,
        min_periods=1,
    ).mean()
    blend = min(max(settings.gradient_smooth_blend, 0.0), 1.0)
    frame["gradient_driver"] = blend * gradient_smoothed + (1.0 - blend) * gradient_raw

    return frame[INDICATOR_COLUMNS]


def calculate_indicator(
    target_close: pd.Series,
    benchmark_close: pd.Series,
    risk_series: pd.Series | None = None,
    settings: IndicatorSettings | None = None,
    weights: WeightSettings | None = None,
) -> pd.DataFrame:
    """Return the active production indicator.

    The active production indicator currently delegates to frozen core v0.
    Future formula changes should add a new versioned function and run it
    side-by-side before promoting it here.
    """
    return calculate_core_signal_v0(
        target_close,
        benchmark_close,
        risk_series=risk_series,
        settings=settings,
        weights=weights,
    )
