from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .research_outcomes import (
    apply_event_cooldown,
    benchmark_label_at,
    entry_date_at,
    event_cluster_id,
    forward_max_drawdown,
    forward_relative_return,
    forward_return,
    hit_rate_or_nan,
    max_share,
    mean_or_nan,
    median_or_nan,
    quantile_or_nan,
    split_half_medians,
    worst_cluster_median,
)


GRAMMAR_SEARCH_MODEL = "riskflow_grammar_search_v0"
DEFAULT_GRAMMAR_SEARCH_GRID = "research/grammar/rule_search_grid.yaml"
DEFAULT_TIMEFRAME_HORIZONS = {
    "1d": (3, 7, 14, 30),
    "12h": (6, 14, 28, 60),
    "4h": (18, 42, 84, 180),
    "1h": (72, 168, 336, 720),
}
DEFAULT_TIMEFRAME_COOLDOWNS = {
    "1d": 30,
    "12h": 60,
    "4h": 120,
    "1h": 360,
}
MAX_SYMBOL_EVENT_SHARE = 0.55
MAX_CLUSTER_EVENT_SHARE = 0.60


@dataclass(frozen=True)
class RuleFamilySpec:
    family_id: str
    direction: str
    detector: str
    parameter_grid: dict[str, list[Any]]
    description: str = ""


@dataclass(frozen=True)
class RuleVariant:
    variant_id: str
    family_id: str
    direction: str
    detector: str
    params: dict[str, Any]


def _slug_value(value: Any) -> str:
    text = str(value).lower().replace("-", "neg_").replace(".", "_")
    return "".join(char if char.isalnum() or char == "_" else "_" for char in text).strip("_")


def _as_numeric(frame: pd.DataFrame, column: str, default: float = np.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").astype(float)


def _as_bool(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    return frame[column].fillna(False).astype(bool)


def _crosses_above(series: pd.Series, threshold: float) -> pd.Series:
    return ((series > threshold) & (series.shift(1) <= threshold)).fillna(False)


def _crosses_below(series: pd.Series, threshold: float) -> pd.Series:
    return ((series < threshold) & (series.shift(1) >= threshold)).fillna(False)


def _recent(mask: pd.Series, window: int) -> pd.Series:
    return mask.fillna(False).astype(float).rolling(window, min_periods=1).sum() > 0.0


def timeframe_horizons(timeframe: str) -> tuple[int, ...]:
    normalized = timeframe.strip().lower()
    return DEFAULT_TIMEFRAME_HORIZONS.get(normalized, DEFAULT_TIMEFRAME_HORIZONS["1d"])


def timeframe_cooldown(timeframe: str) -> int:
    normalized = timeframe.strip().lower()
    return DEFAULT_TIMEFRAME_COOLDOWNS.get(normalized, DEFAULT_TIMEFRAME_COOLDOWNS["1d"])


def load_rule_search_grid(path: str | Path = DEFAULT_GRAMMAR_SEARCH_GRID) -> list[RuleFamilySpec]:
    grid_path = Path(path)
    with grid_path.open(encoding="utf-8") as file:
        raw = yaml.safe_load(file)
    if not isinstance(raw, dict):
        raise ValueError(f"Grammar search grid {grid_path} must contain a mapping.")
    if raw.get("model") != GRAMMAR_SEARCH_MODEL:
        raise ValueError(f"Unknown grammar search grid model: {raw.get('model')!r}")
    families = raw.get("families")
    if not isinstance(families, list):
        raise ValueError("Grammar search grid must define a families list.")

    specs: list[RuleFamilySpec] = []
    for family in families:
        if not isinstance(family, dict):
            raise ValueError("Each grammar search family must be a mapping.")
        parameter_grid = family.get("parameter_grid", {})
        if not isinstance(parameter_grid, dict):
            raise ValueError(f"Family {family.get('family_id')} parameter_grid must be a mapping.")
        normalized_grid: dict[str, list[Any]] = {}
        for key, values in parameter_grid.items():
            normalized_grid[str(key)] = values if isinstance(values, list) else [values]
        specs.append(
            RuleFamilySpec(
                family_id=str(family["family_id"]),
                direction=str(family.get("direction", "positive")),
                detector=str(family["detector"]),
                parameter_grid=normalized_grid,
                description=str(family.get("description", "")),
            )
        )
    return specs


def expand_rule_variants(specs: list[RuleFamilySpec], *, timeframes: list[str] | tuple[str, ...]) -> list[RuleVariant]:
    variants: list[RuleVariant] = []
    for timeframe in timeframes:
        normalized_timeframe = timeframe.strip().lower()
        for spec in specs:
            keys = sorted(spec.parameter_grid)
            values = [spec.parameter_grid[key] for key in keys]
            combinations = product(*values) if keys else [()]
            for combo in combinations:
                params = dict(zip(keys, combo))
                id_parts = [
                    f"grammar_search.{spec.family_id}.v0",
                    f"tf_{normalized_timeframe}",
                    *[f"{key}_{_slug_value(params[key])}" for key in keys],
                ]
                variants.append(
                    RuleVariant(
                        variant_id=".".join(id_parts),
                        family_id=spec.family_id,
                        direction=spec.direction,
                        detector=spec.detector,
                        params={**params, "timeframe": normalized_timeframe},
                    )
                )
    return variants


def _reclaim_trigger(signal: pd.Series, viscosity: pd.Series, trigger: str, level: float | None = None) -> pd.Series:
    if trigger == "viscosity_reclaim":
        return ((signal > viscosity) & (signal.shift(1) <= viscosity.shift(1))).fillna(False)
    if trigger == "level_reclaim":
        return _crosses_above(signal, float(level if level is not None else 0.0))
    if trigger == "minus_2_reclaim":
        return _crosses_above(signal, -2.0)
    if trigger == "minus_1_5_reclaim":
        return _crosses_above(signal, -1.5)
    if trigger == "zero_reclaim":
        return _crosses_above(signal, 0.0)
    if trigger == "plus_1_5_lost":
        return _crosses_below(signal, 1.5)
    return pd.Series(False, index=signal.index, dtype=bool)


def _loss_trigger(signal: pd.Series, viscosity: pd.Series, trigger: str, level: float | None = None) -> pd.Series:
    if trigger == "viscosity_loss":
        return ((signal < viscosity) & (signal.shift(1) >= viscosity.shift(1))).fillna(False)
    if trigger == "zero_loss":
        return _crosses_below(signal, 0.0)
    if trigger == "plus_1_5_lost":
        return _crosses_below(signal, 1.5)
    if trigger == "level_loss":
        return _crosses_below(signal, float(level if level is not None else 0.0))
    return pd.Series(False, index=signal.index, dtype=bool)


def _failed_weakness_mask(
    signal: pd.Series,
    relative: pd.Series,
    *,
    lookback: int,
    zone_max: float,
    low_tolerance: float,
    min_slope: float,
    relative_slope_min: float,
) -> pd.Series:
    prior_low = signal.shift(1).rolling(lookback, min_periods=max(3, lookback // 2)).min()
    near_or_higher_low = signal >= prior_low - low_tolerance
    slope = (signal - signal.shift(max(1, lookback // 2))) / max(1, lookback // 2)
    relative_slope = (relative - relative.shift(max(1, lookback // 2))) / max(1, lookback // 2)
    return ((signal <= zone_max) & near_or_higher_low & (slope >= min_slope) & (relative_slope >= relative_slope_min)).fillna(False)


def _lower_high_mask(
    series: pd.Series,
    *,
    lookback: int,
    recent_window: int,
    min_prior_high: float,
    min_lower_high_gap: float,
) -> pd.Series:
    prior_window = series.shift(recent_window).rolling(lookback, min_periods=max(3, lookback // 2))
    recent_window_values = series.shift(1).rolling(recent_window, min_periods=max(2, recent_window // 2))
    prior_high = prior_window.max()
    recent_high = recent_window_values.max()
    return ((prior_high >= min_prior_high) & (recent_high <= prior_high - min_lower_high_gap)).fillna(False)


def _relative_failed_breakout_mask(
    relative: pd.Series,
    *,
    lookback: int,
    fail_window: int,
    min_breakout_margin: float,
) -> pd.Series:
    prior_high = relative.shift(1).rolling(lookback, min_periods=max(3, lookback // 2)).max()
    breakout = relative > prior_high + min_breakout_margin
    recent_breakout = _recent(breakout.shift(1, fill_value=False), fail_window)
    return (recent_breakout & (relative < prior_high)).fillna(False)


def _fast_slow_pressure_gap(frame: pd.DataFrame, signal: pd.Series, viscosity: pd.Series) -> pd.Series:
    pressure = signal - viscosity
    return _as_numeric(
        frame,
        "grammar_fast_slow_pressure_gap",
        default=pressure.ewm(span=3, adjust=False).mean() - pressure.ewm(span=10, adjust=False).mean(),
    )


def detect_variant_events(frame: pd.DataFrame, variant: RuleVariant) -> pd.Series:
    signal = _as_numeric(frame, "final_signal")
    viscosity = _as_numeric(frame, "viscosity")
    relative = _as_numeric(frame, "relative_component")
    gradient = _as_numeric(frame, "gradient_driver")
    compression = _as_numeric(frame, "compression_score", default=0.0)
    params = variant.params

    detector = variant.detector
    if detector == "pressure_acceptance":
        window = int(params.get("window", 20))
        min_time_above = float(params.get("min_time_above", 0.65))
        min_balance = float(params.get("min_balance", 0.0))
        min_delta = float(params.get("min_delta", 0.0))
        zone_max = params.get("zone_max")
        pressure = signal - viscosity
        time_above = (pressure > 0.0).astype(float).rolling(window, min_periods=1).mean()
        balance = pressure.clip(lower=0.0).rolling(window, min_periods=1).sum() - pressure.clip(upper=0.0).abs().rolling(
            window,
            min_periods=1,
        ).sum()
        mask = (time_above >= min_time_above) & (balance >= min_balance) & (balance.diff(max(1, window // 4)) >= min_delta)
        if zone_max is not None:
            mask &= signal <= float(zone_max)
        return mask.fillna(False)

    if detector == "low_zone_coil_reclaim":
        coil_window = int(params.get("coil_window", 12))
        range_max = float(params.get("range_max", 0.7))
        std_max = float(params.get("std_max", 0.35))
        zone_max = float(params.get("zone_max", -1.0))
        recent_window = int(params.get("recent_window", 10))
        trigger = str(params.get("trigger", "viscosity_reclaim"))
        signal_range = signal.rolling(coil_window, min_periods=max(3, coil_window // 2)).max() - signal.rolling(
            coil_window,
            min_periods=max(3, coil_window // 2),
        ).min()
        signal_std = signal.rolling(coil_window, min_periods=max(3, coil_window // 2)).std(ddof=0)
        coiled = (signal_range <= range_max) & (signal_std <= std_max) & (signal.rolling(coil_window, min_periods=1).min() <= zone_max)
        return (_recent(coiled, recent_window) & _reclaim_trigger(signal, viscosity, trigger)).fillna(False)

    if detector == "failed_weakness":
        lookback = int(params.get("lookback", 10))
        zone_max = float(params.get("zone_max", -1.0))
        low_tolerance = float(params.get("low_tolerance", 0.25))
        min_slope = float(params.get("min_slope", 0.0))
        relative_slope_min = float(params.get("relative_slope_min", -0.05))
        return _failed_weakness_mask(
            signal,
            relative,
            lookback=lookback,
            zone_max=zone_max,
            low_tolerance=low_tolerance,
            min_slope=min_slope,
            relative_slope_min=relative_slope_min,
        )

    if detector == "failed_weakness_reclaim":
        lookback = int(params.get("lookback", 13))
        zone_max = float(params.get("zone_max", -1.5))
        low_tolerance = float(params.get("low_tolerance", 0.25))
        min_slope = float(params.get("min_slope", 0.0))
        relative_slope_min = float(params.get("relative_slope_min", -0.05))
        recent_window = int(params.get("recent_window", 8))
        trigger = str(params.get("trigger", "viscosity_reclaim"))
        weakness = _failed_weakness_mask(
            signal,
            relative,
            lookback=lookback,
            zone_max=zone_max,
            low_tolerance=low_tolerance,
            min_slope=min_slope,
            relative_slope_min=relative_slope_min,
        )
        recent_weakness = weakness.shift(1).astype("boolean").fillna(False).astype(bool)
        return (_recent(recent_weakness, recent_window) & _reclaim_trigger(signal, viscosity, trigger)).fillna(False)

    if detector == "zone_reclaim_retest":
        level = float(params.get("level", 0.0))
        tolerance = float(params.get("tolerance", 0.15))
        hold_bars = int(params.get("hold_bars", 3))
        mode = str(params.get("mode", "reclaim"))
        reclaim = _crosses_above(signal, level)
        if mode == "reclaim":
            return reclaim
        recent_reclaim = _recent(reclaim, hold_bars + 1)
        near_level = signal.between(level - tolerance, level + tolerance)
        holding = signal >= level - tolerance
        return (recent_reclaim & near_level & holding & (signal.diff() >= 0.0)).fillna(False)

    if detector == "curvature_from_low_zone":
        zone_max = float(params.get("zone_max", -1.0))
        slope_window = int(params.get("slope_window", 3))
        accel_min = float(params.get("accel_min", 0.0))
        confirm_below = float(params.get("confirm_below", 0.0))
        slope = (signal - signal.shift(slope_window)) / slope_window
        accel = slope.diff(slope_window) / slope_window
        recent_low = _recent(signal <= zone_max, slope_window * 3)
        return (recent_low & (signal <= confirm_below) & (slope > slope.shift(1)) & (accel >= accel_min)).fillna(False)

    if detector == "divergence_reclaim":
        divergence = str(params.get("divergence", "bullish"))
        confirm = str(params.get("confirm", "viscosity_reclaim"))
        recent_window = int(params.get("recent_window", 10))
        if divergence == "bearish":
            divergence_mask = _as_bool(frame, "grammar_bearish_divergence_20") | _as_bool(
                frame,
                "grammar_gradient_momentum_divergence_20",
            )
            confirm_mask = _reclaim_trigger(signal, viscosity, confirm)
            if confirm in {"viscosity_loss", "below_viscosity"}:
                confirm_mask = ((signal < viscosity) & (signal.shift(1) >= viscosity.shift(1))).fillna(False)
            return (_recent(divergence_mask, recent_window) & confirm_mask).fillna(False)
        divergence_mask = _as_bool(frame, "grammar_bullish_divergence_20")
        return (_recent(divergence_mask, recent_window) & _reclaim_trigger(signal, viscosity, confirm)).fillna(False)

    if detector == "chop_quality":
        chop_type = str(params.get("chop_type", "clean"))
        min_quality = float(params.get("min_quality", 0.55))
        trigger = str(params.get("trigger", "viscosity_reclaim"))
        recent_window = int(params.get("recent_window", 10))
        column = "grammar_clean_chop_quality" if chop_type == "clean" else "grammar_chaotic_chop_quality"
        quality = _as_bool(frame, column)
        if chop_type == "chaotic":
            return (quality & (compression <= float(params.get("max_compression", 70.0)))).fillna(False)
        quality_score = _as_numeric(frame, "compression_score", default=0.0) / 100.0
        return (_recent(quality & (quality_score >= min_quality), recent_window) & _reclaim_trigger(signal, viscosity, trigger)).fillna(False)

    if detector == "hot_leader_reset":
        prior_window = int(params.get("prior_window", 20))
        hot_level = float(params.get("hot_level", 1.5))
        cooloff_level = float(params.get("cooloff_level", 1.0))
        require_below_viscosity = bool(params.get("require_below_viscosity", True))
        prior_hot = signal.shift(1).rolling(prior_window, min_periods=max(3, prior_window // 2)).max() >= hot_level
        mask = prior_hot & (signal <= cooloff_level) & (gradient.diff() < 0.0)
        if require_below_viscosity:
            mask &= signal < viscosity
        return mask.fillna(False)

    if detector == "amplitude_reset_warning":
        prior_window = int(params.get("prior_window", 13))
        hot_level = float(params.get("hot_level", 1.5))
        cooloff_level = float(params.get("cooloff_level", 1.5))
        min_signal_range = float(params.get("min_signal_range", 2.0))
        max_compression = params.get("max_compression")
        require_below_viscosity = bool(params.get("require_below_viscosity", True))
        prior = signal.shift(1).rolling(prior_window, min_periods=max(3, prior_window // 2))
        prior_hot = prior.max() >= hot_level
        prior_range = prior.max() - prior.min()
        mask = prior_hot & (prior_range >= min_signal_range) & (signal <= cooloff_level)
        if require_below_viscosity:
            mask &= signal < viscosity
        if max_compression is not None:
            mask &= compression <= float(max_compression)
        return mask.fillna(False)

    if detector == "zero_rejection_warning":
        lookback = int(params.get("lookback", 5))
        level = float(params.get("level", 0.0))
        tolerance = float(params.get("tolerance", 0.25))
        require_below_viscosity = bool(params.get("require_below_viscosity", True))
        max_compression = params.get("max_compression")
        recent_test = signal.shift(1).rolling(lookback, min_periods=max(2, lookback // 2)).max() >= level - tolerance
        mask = recent_test & (signal < level) & (signal.diff() < 0.0) & (gradient.diff() < 0.0)
        if require_below_viscosity:
            mask &= signal < viscosity
        if max_compression is not None:
            mask &= compression <= float(max_compression)
        return mask.fillna(False)

    if detector == "failed_strength_acceptance":
        acceptance_window = int(params.get("acceptance_window", 10))
        min_recent_time_above = float(params.get("min_recent_time_above", 0.5))
        min_prior_signal = float(params.get("min_prior_signal", 0.5))
        trigger = str(params.get("trigger", "viscosity_loss"))
        max_relative_slope = float(params.get("max_relative_slope", 0.0))
        above_viscosity = signal > viscosity
        recent_time_above = above_viscosity.shift(1).astype(float).rolling(
            acceptance_window,
            min_periods=max(2, acceptance_window // 2),
        ).mean()
        prior_signal = signal.shift(1).rolling(acceptance_window, min_periods=max(2, acceptance_window // 2)).max()
        relative_slope = (relative - relative.shift(max(1, acceptance_window // 2))) / max(1, acceptance_window // 2)
        return (
            (recent_time_above >= min_recent_time_above)
            & (prior_signal >= min_prior_signal)
            & _loss_trigger(signal, viscosity, trigger)
            & (relative_slope <= max_relative_slope)
        ).fillna(False)

    if detector == "lower_high_rollover":
        lookback = int(params.get("lookback", 20))
        recent_window = int(params.get("recent_window", 6))
        min_prior_high = float(params.get("min_prior_high", 1.0))
        min_lower_high_gap = float(params.get("min_lower_high_gap", 0.35))
        require_below_viscosity = bool(params.get("require_below_viscosity", False))
        max_relative_slope = float(params.get("max_relative_slope", 0.0))
        min_fast_slow_pressure_gap = params.get("min_fast_slow_pressure_gap")
        max_pressure_area_balance = params.get("max_pressure_area_balance")
        max_pressure_distance = params.get("max_pressure_distance")
        min_viscosity = params.get("min_viscosity")
        max_time_above_viscosity_5 = params.get("max_time_above_viscosity_5")
        max_time_above_viscosity_10 = params.get("max_time_above_viscosity_10")
        relative_slope = (relative - relative.shift(max(1, recent_window))) / max(1, recent_window)
        mask = (
            _lower_high_mask(
                signal,
                lookback=lookback,
                recent_window=recent_window,
                min_prior_high=min_prior_high,
                min_lower_high_gap=min_lower_high_gap,
            )
            & (signal.diff() < 0.0)
            & (gradient.diff() < 0.0)
            & (relative_slope <= max_relative_slope)
        )
        if require_below_viscosity:
            mask &= signal < viscosity
        if min_fast_slow_pressure_gap is not None:
            mask &= _as_numeric(frame, "grammar_fast_slow_pressure_gap") >= float(min_fast_slow_pressure_gap)
        if max_pressure_area_balance is not None:
            mask &= _as_numeric(frame, "grammar_pressure_area_balance_20") <= float(max_pressure_area_balance)
        if max_pressure_distance is not None:
            mask &= _as_numeric(frame, "grammar_pressure_distance") <= float(max_pressure_distance)
        if min_viscosity is not None:
            mask &= viscosity >= float(min_viscosity)
        if max_time_above_viscosity_5 is not None:
            mask &= _as_numeric(frame, "grammar_time_above_viscosity_5") <= float(max_time_above_viscosity_5)
        if max_time_above_viscosity_10 is not None:
            mask &= _as_numeric(frame, "grammar_time_above_viscosity_10") <= float(max_time_above_viscosity_10)
        return mask.fillna(False)

    if detector == "relative_failed_breakout_warning":
        lookback = int(params.get("lookback", 20))
        fail_window = int(params.get("fail_window", 5))
        context_window = int(params.get("context_window", 5))
        min_breakout_margin = float(params.get("min_breakout_margin", 0.0))
        min_gradient = float(params.get("min_gradient", 0.0))
        gradient_diff_window = int(params.get("gradient_diff_window", 3))
        require_viscosity_loss = bool(params.get("require_viscosity_loss", True))
        min_signal = params.get("min_signal")
        min_viscosity = params.get("min_viscosity")
        max_relative_component = params.get("max_relative_component")
        max_pressure_area_delta = params.get("max_pressure_area_delta")
        max_prior_relative_high = params.get("max_prior_relative_high")
        min_time_above_viscosity_20 = params.get("min_time_above_viscosity_20")
        min_viscosity_cross_count_20 = params.get("min_viscosity_cross_count_20")
        min_compression = params.get("min_compression")
        failed_relative_breakout = _relative_failed_breakout_mask(
            relative,
            lookback=lookback,
            fail_window=fail_window,
            min_breakout_margin=min_breakout_margin,
        )
        gradient_fade = (gradient > min_gradient) & (gradient.diff(gradient_diff_window) < 0.0)
        mask = _recent(failed_relative_breakout, context_window) & _recent(gradient_fade, context_window)
        if require_viscosity_loss:
            mask &= _recent(_loss_trigger(signal, viscosity, "viscosity_loss"), context_window)
        if min_signal is not None:
            mask &= signal >= float(min_signal)
        if min_viscosity is not None:
            mask &= viscosity >= float(min_viscosity)
        if max_relative_component is not None:
            mask &= relative <= float(max_relative_component)
        if max_pressure_area_delta is not None:
            mask &= _as_numeric(frame, "grammar_pressure_area_delta_5") <= float(max_pressure_area_delta)
        if max_prior_relative_high is not None:
            prior_relative_high = relative.shift(1).rolling(lookback, min_periods=max(3, lookback // 2)).max()
            mask &= prior_relative_high <= float(max_prior_relative_high)
        if min_time_above_viscosity_20 is not None:
            mask &= _as_numeric(frame, "grammar_time_above_viscosity_20") >= float(min_time_above_viscosity_20)
        if min_viscosity_cross_count_20 is not None:
            mask &= _as_numeric(frame, "grammar_viscosity_cross_count_20") >= float(min_viscosity_cross_count_20)
        if min_compression is not None:
            mask &= compression >= float(min_compression)
        return mask.fillna(False)

    if detector == "bearish_divergence_fade_warning":
        lookback = int(params.get("lookback", 20))
        recent_window = int(params.get("recent_window", 5))
        context_window = int(params.get("context_window", 20))
        min_prior_signal_high = float(params.get("min_prior_signal_high", 0.0))
        min_lower_high_gap = float(params.get("min_lower_high_gap", 0.1))
        min_gradient = float(params.get("min_gradient", 0.0))
        gradient_diff_window = int(params.get("gradient_diff_window", 3))
        price_higher_high = _as_numeric(frame, "target").ge(
            _as_numeric(frame, "target").shift(recent_window).rolling(lookback, min_periods=max(3, lookback // 2)).max()
        )
        signal_lower_high = _lower_high_mask(
            signal,
            lookback=lookback,
            recent_window=recent_window,
            min_prior_high=min_prior_signal_high,
            min_lower_high_gap=min_lower_high_gap,
        )
        divergence = _as_bool(frame, "grammar_bearish_divergence_20") | (price_higher_high & signal_lower_high)
        gradient_fade = (gradient > min_gradient) & (gradient.diff(gradient_diff_window) < 0.0)
        return (_recent(divergence, context_window) & _recent(gradient_fade, context_window)).fillna(False)

    if detector == "failed_baseline_breakout_warning":
        lookback = int(params.get("lookback", 20))
        recent_window = int(params.get("recent_window", 5))
        context_window = int(params.get("context_window", 10))
        min_prior_signal_high = float(params.get("min_prior_signal_high", 0.0))
        min_lower_high_gap = float(params.get("min_lower_high_gap", 0.1))
        require_gradient_fade = bool(params.get("require_gradient_fade", False))
        viscosity_reclaim = _reclaim_trigger(signal, viscosity, "viscosity_reclaim")
        viscosity_loss = _loss_trigger(signal, viscosity, "viscosity_loss")
        signal_lower_high = _lower_high_mask(
            signal,
            lookback=lookback,
            recent_window=recent_window,
            min_prior_high=min_prior_signal_high,
            min_lower_high_gap=min_lower_high_gap,
        )
        mask = (
            _recent(viscosity_reclaim, context_window)
            & _recent(signal_lower_high, context_window)
            & _recent(viscosity_loss, context_window)
        )
        if require_gradient_fade:
            mask &= _recent((gradient > 0.0) & (gradient.diff(3) < 0.0), context_window)
        return mask.fillna(False)

    if detector == "overbought_pressure_cross_down_warning":
        context_window = int(params.get("context_window", 20))
        high_level = float(params.get("high_level", 1.5))
        loss_level = float(params.get("loss_level", 1.0))
        min_gradient = float(params.get("min_gradient", 0.0))
        overbought = signal >= high_level
        loses_high_zone = _crosses_below(signal, loss_level)
        pressure_gap = _fast_slow_pressure_gap(frame, signal, viscosity)
        fast_cross_down = _crosses_below(pressure_gap, 0.0)
        gradient_fade = (gradient > min_gradient) & (gradient.diff(3) < 0.0)
        return (
            _recent(overbought, context_window)
            & _recent(loses_high_zone | fast_cross_down, context_window)
            & _recent(gradient_fade, context_window)
        ).fillna(False)

    if detector == "bear_pressure_cross_from_high_warning":
        context_window = int(params.get("context_window", 10))
        high_level = float(params.get("high_level", 1.0))
        max_relative_slope = float(params.get("max_relative_slope", 0.0))
        pressure_gap = _fast_slow_pressure_gap(frame, signal, viscosity)
        fast_cross_down = _crosses_below(pressure_gap, 0.0)
        relative_slope = (relative - relative.shift(context_window)) / max(1, context_window)
        return (
            _recent(signal >= high_level, context_window)
            & _recent(fast_cross_down, context_window)
            & (relative_slope <= max_relative_slope)
        ).fillna(False)

    if detector == "volatility_bulge_exhaustion_warning":
        context_window = int(params.get("context_window", 10))
        high_level = float(params.get("high_level", 1.0))
        range_window = int(params.get("range_window", 20))
        range_quantile = float(params.get("range_quantile", 0.8))
        min_gradient = float(params.get("min_gradient", 0.0))
        target_return = _as_numeric(frame, "target").pct_change(fill_method=None)
        move = target_return.abs()
        bulge_threshold = move.rolling(range_window, min_periods=max(3, range_window // 2)).quantile(range_quantile)
        upside_bulge = (target_return > 0.0) & (move >= bulge_threshold)
        gradient_fade = (gradient > min_gradient) & (gradient.diff(3) < 0.0)
        return (
            _recent(upside_bulge, context_window)
            & _recent(signal >= high_level, context_window)
            & _recent(gradient_fade, context_window)
        ).fillna(False)

    if detector == "late_cycle_leader_exhaustion_warning":
        lookback = int(params.get("lookback", 20))
        recent_window = int(params.get("recent_window", 5))
        context_window = int(params.get("context_window", 5))
        signal_high_level = float(params.get("signal_high_level", 1.0))
        min_relative_prior_high = float(params.get("min_relative_prior_high", 0.0))
        min_relative_lower_high_gap = float(params.get("min_relative_lower_high_gap", 0.05))
        relative_lower_high = _lower_high_mask(
            relative,
            lookback=lookback,
            recent_window=recent_window,
            min_prior_high=min_relative_prior_high,
            min_lower_high_gap=min_relative_lower_high_gap,
        )
        gradient_fade = (gradient > 0.0) & (gradient.diff(3) < 0.0)
        return (
            _recent(relative_lower_high, context_window)
            & _recent(signal >= signal_high_level, context_window)
            & _recent(gradient_fade, context_window)
        ).fillna(False)

    if detector == "post_reset_reclaim":
        prior_window = int(params.get("prior_window", 20))
        hot_level = float(params.get("hot_level", 1.5))
        reset_level = float(params.get("reset_level", 1.0))
        reset_window = int(params.get("reset_window", 8))
        require_below_viscosity = bool(params.get("require_below_viscosity", True))
        trigger = str(params.get("trigger", "viscosity_reclaim"))
        relative_slope_min = float(params.get("relative_slope_min", -0.05))
        prior_hot = signal.shift(1).rolling(prior_window, min_periods=max(3, prior_window // 2)).max() >= hot_level
        reset = prior_hot & (signal <= reset_level)
        if require_below_viscosity:
            reset &= signal < viscosity
        relative_slope = (relative - relative.shift(max(1, reset_window // 2))) / max(1, reset_window // 2)
        recent_reset = reset.shift(1).astype("boolean").fillna(False).astype(bool)
        return (
            _recent(recent_reset, reset_window)
            & _reclaim_trigger(signal, viscosity, trigger)
            & (relative_slope >= relative_slope_min)
        ).fillna(False)

    if detector == "chaotic_chop_resolution":
        recent_window = int(params.get("recent_window", 8))
        max_chop_compression = float(params.get("max_chop_compression", 70.0))
        min_current_compression = float(params.get("min_current_compression", 50.0))
        trigger = str(params.get("trigger", "viscosity_reclaim"))
        chaotic = _as_bool(frame, "grammar_chaotic_chop_quality") & (compression <= max_chop_compression)
        recent_chaotic = chaotic.shift(1).astype("boolean").fillna(False).astype(bool)
        return (
            _recent(recent_chaotic, recent_window)
            & (compression >= min_current_compression)
            & _reclaim_trigger(signal, viscosity, trigger)
        ).fillna(False)

    if detector == "compression_reclaim":
        min_compression = float(params.get("min_compression", 70.0))
        trigger = str(params.get("trigger", "viscosity_reclaim"))
        return ((compression >= min_compression) & _reclaim_trigger(signal, viscosity, trigger)).fillna(False)

    return pd.Series(False, index=frame.index, dtype=bool)


def _variant_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    variant: RuleVariant,
    *,
    timeframe: str,
    benchmark_name: str,
    horizons: tuple[int, ...],
    entry_lag_bars: int,
    cooldown_bars: int,
) -> pd.DataFrame:
    target = _as_numeric(frame, "target")
    benchmark = _as_numeric(frame, "benchmark")
    raw_mask = detect_variant_events(frame, variant)
    mask = apply_event_cooldown(raw_mask, cooldown_bars)
    dates = frame.index[mask]

    metric_frame = pd.DataFrame(index=frame.index)
    for horizon in horizons:
        metric_frame[f"forward_return_{horizon}"] = forward_return(target, horizon, entry_lag_bars)
        metric_frame[f"forward_relative_return_{horizon}"] = forward_relative_return(
            target,
            benchmark,
            horizon,
            entry_lag_bars,
        )
    drawdown_horizon = max(horizons)
    metric_frame[f"max_drawdown_{drawdown_horizon}"] = forward_max_drawdown(target, drawdown_horizon, entry_lag_bars)

    records: list[dict[str, Any]] = []
    params_json = json.dumps(variant.params, sort_keys=True)
    for date in dates:
        position = frame.index.get_loc(date)
        record: dict[str, Any] = {
            "symbol": symbol,
            "date": date,
            "timeframe": timeframe,
            "benchmark": benchmark_label_at(frame, date, benchmark_name),
            "variant_id": variant.variant_id,
            "family_id": variant.family_id,
            "detector": variant.detector,
            "direction": variant.direction,
            "params": params_json,
            "entry_lag_bars": entry_lag_bars,
            "entry_date": entry_date_at(frame.index, position, entry_lag_bars),
            "cooldown_bars": cooldown_bars,
            "event_cluster_id": event_cluster_id(date),
        }
        for column in metric_frame.columns:
            record[column] = metric_frame.loc[date, column]
        records.append(record)
    return pd.DataFrame.from_records(records)


def grammar_search_records(
    analysis_frames_by_timeframe: dict[str, dict[str, pd.DataFrame]],
    variants: list[RuleVariant],
    *,
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = 1,
    cooldown_bars_by_timeframe: dict[str, int] | None = None,
) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    variants_by_timeframe: dict[str, list[RuleVariant]] = {}
    for variant in variants:
        timeframe = str(variant.params.get("timeframe", "1d"))
        variants_by_timeframe.setdefault(timeframe, []).append(variant)

    for timeframe, analysis_frames in analysis_frames_by_timeframe.items():
        horizons = timeframe_horizons(timeframe)
        cooldown_bars = (
            cooldown_bars_by_timeframe.get(timeframe, timeframe_cooldown(timeframe))
            if cooldown_bars_by_timeframe
            else timeframe_cooldown(timeframe)
        )
        for variant in variants_by_timeframe.get(timeframe, []):
            for symbol, frame in analysis_frames.items():
                if frame.empty:
                    continue
                frame_records = _variant_records_for_asset(
                    symbol,
                    frame,
                    variant,
                    timeframe=timeframe,
                    benchmark_name=benchmark_name,
                    horizons=horizons,
                    entry_lag_bars=entry_lag_bars,
                    cooldown_bars=cooldown_bars,
                )
                if not frame_records.empty:
                    records.append(frame_records)
    if not records:
        return pd.DataFrame()
    return pd.concat(records, ignore_index=True)


def _classify_variant(row: pd.Series, *, min_sample_size: int) -> tuple[str, str]:
    sample_size = int(row.get("sample_size", 0))
    if sample_size < min_sample_size:
        return "inconclusive", f"sample size below min_sample_size={min_sample_size}"
    if float(row.get("max_symbol_event_share", np.nan)) > MAX_SYMBOL_EVENT_SHARE:
        return "fragile", "too many events come from one symbol"
    if float(row.get("max_cluster_event_share", np.nan)) > MAX_CLUSTER_EVENT_SHARE:
        return "fragile", "too many events come from one calendar cluster"

    primary = float(row.get("median_forward_relative_return_primary", np.nan))
    secondary = float(row.get("median_forward_relative_return_secondary", np.nan))
    hit_primary = float(row.get("hit_rate_forward_relative_return_primary", np.nan))
    drawdown = float(row.get("median_max_drawdown", np.nan))
    first_half = float(row.get("first_half_median_forward_relative_return_secondary", np.nan))
    second_half = float(row.get("second_half_median_forward_relative_return_secondary", np.nan))
    stable = not any(np.isnan(value) for value in (first_half, second_half)) and min(first_half, second_half) > -0.05
    acceptable_drawdown = np.isnan(drawdown) or drawdown > -0.35

    if str(row.get("direction")) == "negative":
        miss_rate = 1.0 - hit_primary if not np.isnan(hit_primary) else np.nan
        if primary < 0.0 and secondary < 0.0 and miss_rate >= 0.55:
            return "useful", "negative variant preceded underperformance"
        if primary < 0.0 or secondary < 0.0 or miss_rate >= 0.52:
            return "watchlist", "mixed but potentially useful downside evidence"
        return "fragile", "negative variant did not precede underperformance"

    if primary > 0.0 and secondary > 0.0 and hit_primary >= 0.55 and acceptable_drawdown and stable:
        return "useful", "positive relative returns with split-half stability"
    if (primary > 0.0 or secondary > 0.0 or hit_primary >= 0.52) and acceptable_drawdown:
        return "watchlist", "mixed but potentially useful upside evidence"
    return "fragile", "positive variant has weak or negative forward relative evidence"


def _rank_score(row: pd.Series) -> float:
    def finite_float(column: str, default: float) -> float:
        value = pd.to_numeric(pd.Series([row.get(column, default)]), errors="coerce").iloc[0]
        return default if pd.isna(value) else float(value)

    direction = str(row.get("direction"))
    median_primary = finite_float("median_forward_relative_return_primary", 0.0)
    median_secondary = finite_float("median_forward_relative_return_secondary", 0.0)
    hit_primary = finite_float("hit_rate_forward_relative_return_primary", 0.5)
    drawdown = finite_float("median_max_drawdown", 0.0)
    symbol_penalty = finite_float("max_symbol_event_share", 1.0)
    cluster_penalty = finite_float("max_cluster_event_share", 1.0)
    sign = -1.0 if direction == "negative" else 1.0
    return (
        sign * (median_primary * 60.0 + median_secondary * 40.0)
        + (hit_primary - 0.5) * 20.0 * sign
        + max(drawdown, -1.0) * 5.0
        - symbol_penalty * 4.0
        - cluster_penalty * 4.0
    )


def summarize_grammar_search_records(
    records: pd.DataFrame,
    *,
    variants: list[RuleVariant],
    min_sample_size: int = 20,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant in variants:
        variant_records = records[records["variant_id"] == variant.variant_id] if not records.empty else pd.DataFrame()
        horizons = timeframe_horizons(str(variant.params.get("timeframe", "1d")))
        primary = horizons[-2]
        secondary = horizons[-1]
        drawdown_column = f"max_drawdown_{secondary}"
        row: dict[str, Any] = {
            "variant_id": variant.variant_id,
            "family_id": variant.family_id,
            "detector": variant.detector,
            "direction": variant.direction,
            "timeframe": variant.params.get("timeframe", "1d"),
            "params": json.dumps(variant.params, sort_keys=True),
            "sample_size": int(len(variant_records)),
            "unique_symbols": int(variant_records["symbol"].nunique()) if not variant_records.empty else 0,
            "unique_event_dates": int(variant_records["date"].nunique()) if not variant_records.empty else 0,
            "unique_event_clusters": int(variant_records["event_cluster_id"].nunique()) if not variant_records.empty else 0,
            "max_symbol_event_share": max_share(variant_records["symbol"]) if not variant_records.empty else np.nan,
            "max_cluster_event_share": max_share(variant_records["event_cluster_id"]) if not variant_records.empty else np.nan,
        }
        for horizon in horizons:
            relative = variant_records.get(f"forward_relative_return_{horizon}", pd.Series(dtype=float))
            forward = variant_records.get(f"forward_return_{horizon}", pd.Series(dtype=float))
            row[f"avg_forward_return_{horizon}"] = mean_or_nan(forward)
            row[f"median_forward_return_{horizon}"] = median_or_nan(forward)
            row[f"avg_forward_relative_return_{horizon}"] = mean_or_nan(relative)
            row[f"median_forward_relative_return_{horizon}"] = median_or_nan(relative)
            row[f"hit_rate_forward_relative_return_{horizon}"] = hit_rate_or_nan(relative)
            row[f"p25_forward_relative_return_{horizon}"] = quantile_or_nan(relative, 0.25)
            row[f"p75_forward_relative_return_{horizon}"] = quantile_or_nan(relative, 0.75)
        row["median_forward_relative_return_primary"] = row[f"median_forward_relative_return_{primary}"]
        row["median_forward_relative_return_secondary"] = row[f"median_forward_relative_return_{secondary}"]
        row["hit_rate_forward_relative_return_primary"] = row[f"hit_rate_forward_relative_return_{primary}"]
        row["median_max_drawdown"] = median_or_nan(variant_records.get(drawdown_column, pd.Series(dtype=float)))
        first_half, second_half = split_half_medians(variant_records, f"forward_relative_return_{secondary}")
        row["first_half_median_forward_relative_return_secondary"] = first_half
        row["second_half_median_forward_relative_return_secondary"] = second_half
        row["worst_cluster_median_forward_relative_return_secondary"] = worst_cluster_median(
            variant_records,
            f"forward_relative_return_{secondary}",
        )
        row["classification"], row["notes"] = _classify_variant(pd.Series(row), min_sample_size=min_sample_size)
        row["rank_score"] = _rank_score(pd.Series(row))
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["classification", "rank_score"], ascending=[True, False])


def ranked_grammar_search_summary(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return summary
    class_order = {"useful": 0, "watchlist": 1, "fragile": 2, "inconclusive": 3}
    ranked = summary.copy()
    ranked["_class_order"] = ranked["classification"].map(class_order).fillna(9)
    ranked = ranked.sort_values(
        ["_class_order", "rank_score", "sample_size"],
        ascending=[True, False, False],
    ).drop(columns=["_class_order"])
    return ranked


def family_timeframe_summary(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    ranked = ranked_grammar_search_summary(summary)
    return ranked.groupby(["family_id", "timeframe"], as_index=False).head(1).reset_index(drop=True)


def family_timeframe_robustness(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for (family_id, timeframe), group in summary.groupby(["family_id", "timeframe"], dropna=False):
        direction = str(group["direction"].dropna().iloc[0]) if "direction" in group and group["direction"].notna().any() else "positive"
        primary = pd.to_numeric(group["median_forward_relative_return_primary"], errors="coerce")
        secondary = pd.to_numeric(group["median_forward_relative_return_secondary"], errors="coerce")
        if direction == "negative":
            best_primary = primary.min()
            worst_primary = primary.max()
            best_secondary = secondary.min()
            worst_secondary = secondary.max()
        else:
            best_primary = primary.max()
            worst_primary = primary.min()
            best_secondary = secondary.max()
            worst_secondary = secondary.min()
        rows.append(
            {
                "family_id": family_id,
                "timeframe": timeframe,
                "direction": direction,
                "variants": int(len(group)),
                "useful": int((group["classification"] == "useful").sum()),
                "watchlist": int((group["classification"] == "watchlist").sum()),
                "fragile": int((group["classification"] == "fragile").sum()),
                "inconclusive": int((group["classification"] == "inconclusive").sum()),
                "best_rank_score": pd.to_numeric(group["rank_score"], errors="coerce").max(),
                "median_rank_score": pd.to_numeric(group["rank_score"], errors="coerce").median(),
                "median_sample_size": pd.to_numeric(group["sample_size"], errors="coerce").median(),
                "best_sample_size": pd.to_numeric(group["sample_size"], errors="coerce").max(),
                "best_primary": best_primary,
                "worst_primary": worst_primary,
                "best_secondary": best_secondary,
                "worst_secondary": worst_secondary,
            }
        )
    grouped = pd.DataFrame(rows)
    grouped["useful_watchlist_rate"] = (grouped["useful"] + grouped["watchlist"]) / grouped["variants"]
    return grouped.sort_values(
        ["useful_watchlist_rate", "best_rank_score", "best_sample_size"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def duplicate_outcome_clusters(summary: pd.DataFrame, *, precision: int = 6) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    cluster_columns = [
        "family_id",
        "timeframe",
        "direction",
        "classification",
        "sample_size",
        "unique_symbols",
        "unique_event_clusters",
        "median_forward_relative_return_primary",
        "median_forward_relative_return_secondary",
        "hit_rate_forward_relative_return_primary",
        "median_max_drawdown",
        "max_symbol_event_share",
        "max_cluster_event_share",
    ]
    available_columns = [column for column in cluster_columns if column in summary.columns]
    clustered = summary.copy()
    for column in available_columns:
        if pd.api.types.is_numeric_dtype(clustered[column]):
            clustered[column] = clustered[column].round(precision)
    duplicates = (
        clustered.groupby(available_columns, dropna=False)
        .agg(
            duplicate_count=("variant_id", "count"),
            example_variant=("variant_id", "first"),
        )
        .reset_index()
    )
    duplicates = duplicates[duplicates["duplicate_count"] > 1]
    return duplicates.sort_values("duplicate_count", ascending=False).reset_index(drop=True)


def chart_review_queue(
    ranked: pd.DataFrame,
    records: pd.DataFrame,
    *,
    top_variant_count: int = 20,
    max_events_per_variant: int = 12,
    max_events_per_symbol: int = 2,
) -> pd.DataFrame:
    if ranked.empty or records.empty:
        return pd.DataFrame()
    candidates = ranked[ranked["classification"].isin(["useful", "watchlist"])].copy()
    if candidates.empty:
        return pd.DataFrame()
    candidates = candidates.sort_values(["classification", "rank_score"], ascending=[True, False])
    top_variants = candidates.head(top_variant_count)["variant_id"].tolist()
    queue = records[records["variant_id"].isin(top_variants)].copy()
    if queue.empty:
        return queue

    def outcome_column_for_timeframe(timeframe: object) -> str:
        horizon = timeframe_horizons(str(timeframe))[-1]
        return f"forward_relative_return_{horizon}"

    queue["review_outcome_column"] = queue["timeframe"].map(outcome_column_for_timeframe)
    queue["review_outcome"] = [
        pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
        for (_, row), column in zip(queue.iterrows(), queue["review_outcome_column"])
    ]
    queue["review_abs_outcome"] = pd.to_numeric(queue["review_outcome"], errors="coerce").abs()
    queue = queue.sort_values(["variant_id", "review_abs_outcome"], ascending=[True, False])
    selected: list[pd.DataFrame] = []
    for _variant_id, group in queue.groupby("variant_id", sort=False):
        balanced = group.groupby("symbol", group_keys=False).head(max_events_per_symbol)
        selected.append(balanced.head(max_events_per_variant))
    if not selected:
        return pd.DataFrame()
    return pd.concat(selected, ignore_index=True)


def _parse_record_dates(values: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(values, errors="coerce", format="mixed")
    except TypeError:
        return pd.to_datetime(values, errors="coerce")


def _terminal_relative_outcomes(records: pd.DataFrame) -> pd.DataFrame:
    outcome_records = records.copy()

    def outcome_column_for_timeframe(timeframe: object) -> str:
        horizon = timeframe_horizons(str(timeframe))[-1]
        return f"forward_relative_return_{horizon}"

    outcome_records["terminal_outcome_column"] = outcome_records["timeframe"].map(outcome_column_for_timeframe)
    outcome_records["terminal_relative_return"] = [
        pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
        for (_, row), column in zip(outcome_records.iterrows(), outcome_records["terminal_outcome_column"])
    ]
    return outcome_records


def time_split_validation(
    ranked: pd.DataFrame,
    records: pd.DataFrame,
    *,
    min_validation_sample: int = 10,
) -> pd.DataFrame:
    if ranked.empty or records.empty:
        return pd.DataFrame()
    outcome_records = _terminal_relative_outcomes(records)
    outcome_records["date"] = _parse_record_dates(outcome_records["date"])
    outcome_records = outcome_records[
        outcome_records["date"].notna() & outcome_records["terminal_relative_return"].notna()
    ].copy()
    if outcome_records.empty:
        return ranked.copy()

    cutoffs = outcome_records.groupby("timeframe")["date"].quantile(0.5).to_dict()
    outcome_records["time_split"] = [
        "validation" if row.date > cutoffs[row.timeframe] else "discovery"
        for row in outcome_records.itertuples()
    ]

    rows: list[dict[str, Any]] = []
    for (variant_id, split), group in outcome_records.groupby(["variant_id", "time_split"]):
        outcomes = pd.to_numeric(group["terminal_relative_return"], errors="coerce")
        rows.append(
            {
                "variant_id": variant_id,
                "time_split": split,
                "split_sample_size": int(outcomes.notna().sum()),
                "split_unique_symbols": int(group["symbol"].nunique()),
                "split_unique_clusters": int(group["event_cluster_id"].nunique()),
                "split_median_terminal_relative_return": outcomes.median(),
                "split_hit_rate_terminal_relative_return": (outcomes > 0.0).mean(),
                "split_p25_terminal_relative_return": outcomes.quantile(0.25),
                "split_p75_terminal_relative_return": outcomes.quantile(0.75),
            }
        )
    if not rows:
        return ranked.copy()
    split = pd.DataFrame(rows)
    wide = split.pivot(index="variant_id", columns="time_split")
    wide.columns = ["_".join(column).strip() for column in wide.columns.to_flat_index()]
    wide = wide.reset_index()
    validation = ranked.merge(wide, on="variant_id", how="left")

    def sign_consistent(row: pd.Series) -> bool:
        discovery = row.get("split_median_terminal_relative_return_discovery")
        validation_value = row.get("split_median_terminal_relative_return_validation")
        if pd.isna(discovery) or pd.isna(validation_value):
            return False
        if row.get("direction") == "negative":
            return float(discovery) < 0.0 and float(validation_value) < 0.0
        return float(discovery) > 0.0 and float(validation_value) > 0.0

    validation["time_split_sign_consistent"] = validation.apply(sign_consistent, axis=1)
    validation_sample = (
        validation["split_sample_size_validation"]
        if "split_sample_size_validation" in validation.columns
        else pd.Series(0, index=validation.index)
    )
    validation["validation_sample_ok"] = pd.to_numeric(validation_sample, errors="coerce").fillna(0) >= min_validation_sample
    validation["validation_status"] = np.select(
        [
            validation["time_split_sign_consistent"] & validation["validation_sample_ok"],
            validation["time_split_sign_consistent"],
        ],
        ["time_split_supported", "direction_supported_low_sample"],
        default="not_time_split_supported",
    )
    status_order = {
        "time_split_supported": 0,
        "direction_supported_low_sample": 1,
        "not_time_split_supported": 2,
    }
    validation["_status_order"] = validation["validation_status"].map(status_order).fillna(9)
    return validation.sort_values(
        ["_status_order", "classification", "rank_score"],
        ascending=[True, True, False],
    ).drop(columns=["_status_order"]).reset_index(drop=True)


def strict_baseline_referee(
    ranked: pd.DataFrame,
    records: pd.DataFrame,
    analysis_frames_by_timeframe: dict[str, dict[str, pd.DataFrame]],
    *,
    entry_lag_bars: int = 1,
    null_iterations: int = 300,
    random_seed: int = 29,
    min_validation_sample: int = 10,
) -> pd.DataFrame:
    """Compare grammar variants against unconditional, cluster, and matched random baselines."""
    if ranked.empty or records.empty:
        return pd.DataFrame()
    if null_iterations < 1:
        raise ValueError("null_iterations must be >= 1")

    validation = time_split_validation(
        ranked,
        records,
        min_validation_sample=min_validation_sample,
    )
    validation_status = (
        validation.set_index("variant_id")["validation_status"].to_dict()
        if not validation.empty and "validation_status" in validation.columns
        else {}
    )

    eligible_by_timeframe: dict[str, pd.DataFrame] = {}
    for timeframe, analysis_frames in analysis_frames_by_timeframe.items():
        horizon = timeframe_horizons(timeframe)[-1]
        parts: list[pd.DataFrame] = []
        for symbol, frame in analysis_frames.items():
            if frame.empty or not {"target", "benchmark"}.issubset(frame.columns):
                continue
            outcomes = forward_relative_return(
                frame["target"],
                frame["benchmark"],
                horizon,
                entry_lag_bars=entry_lag_bars,
            )
            part = pd.DataFrame(
                {
                    "symbol": symbol,
                    "date": frame.index,
                    "event_cluster_id": [event_cluster_id(date) for date in frame.index],
                    "terminal_relative_return": outcomes.to_numpy(),
                }
            ).dropna(subset=["terminal_relative_return"])
            if not part.empty:
                parts.append(part)
        eligible_by_timeframe[timeframe] = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    rng = np.random.default_rng(random_seed)
    rows: list[dict[str, Any]] = []
    for ranked_row in ranked.itertuples(index=False):
        variant_id = str(getattr(ranked_row, "variant_id"))
        timeframe = str(getattr(ranked_row, "timeframe"))
        direction = str(getattr(ranked_row, "direction"))
        horizon = timeframe_horizons(timeframe)[-1]
        terminal_column = f"forward_relative_return_{horizon}"
        if terminal_column not in records.columns:
            continue
        variant_records = records[records["variant_id"] == variant_id].dropna(subset=[terminal_column]).copy()
        eligible = eligible_by_timeframe.get(timeframe, pd.DataFrame())
        if variant_records.empty or eligible.empty:
            continue

        event_median = median_or_nan(variant_records[terminal_column])
        unconditional_median = median_or_nan(eligible["terminal_relative_return"])
        clusters = sorted(variant_records["event_cluster_id"].dropna().unique())
        cluster_pool = eligible[eligible["event_cluster_id"].isin(clusters)]
        cluster_median = median_or_nan(cluster_pool["terminal_relative_return"])

        values_by_symbol_cluster = {
            key: group["terminal_relative_return"].to_numpy(dtype=float)
            for key, group in eligible.groupby(["symbol", "event_cluster_id"])
        }
        values_by_cluster = {
            key: group["terminal_relative_return"].to_numpy(dtype=float)
            for key, group in eligible.groupby("event_cluster_id")
        }
        all_values = eligible["terminal_relative_return"].to_numpy(dtype=float)
        group_counts = variant_records.groupby(["symbol", "event_cluster_id"]).size()
        null_medians = np.empty(null_iterations, dtype=float)
        for iteration in range(null_iterations):
            draws: list[np.ndarray] = []
            for key, count in group_counts.items():
                pool = values_by_symbol_cluster.get(key)
                if pool is None or len(pool) == 0:
                    pool = values_by_cluster.get(key[1])
                if pool is None or len(pool) == 0:
                    pool = all_values
                draws.append(rng.choice(pool, size=int(count), replace=True))
            null_medians[iteration] = float(np.median(np.concatenate(draws)))

        null_median = float(np.median(null_medians))
        if direction == "negative":
            directional_edge_vs_unconditional = unconditional_median - event_median
            directional_edge_vs_cluster = cluster_median - event_median
            directional_edge_vs_null = null_median - event_median
            p_value = float((null_medians <= event_median).mean())
        else:
            directional_edge_vs_unconditional = event_median - unconditional_median
            directional_edge_vs_cluster = event_median - cluster_median
            directional_edge_vs_null = event_median - null_median
            p_value = float((null_medians >= event_median).mean())

        rows.append(
            {
                "variant_id": variant_id,
                "family_id": getattr(ranked_row, "family_id"),
                "timeframe": timeframe,
                "direction": direction,
                "classification": getattr(ranked_row, "classification"),
                "rank_score": getattr(ranked_row, "rank_score"),
                "sample_size": int(getattr(ranked_row, "sample_size")),
                "unique_symbols": int(getattr(ranked_row, "unique_symbols")),
                "unique_event_clusters": int(getattr(ranked_row, "unique_event_clusters")),
                "validation_status": validation_status.get(variant_id, ""),
                "terminal_outcome_column": terminal_column,
                "event_median_terminal_relative_return": event_median,
                "unconditional_median_terminal_relative_return": unconditional_median,
                "same_cluster_median_terminal_relative_return": cluster_median,
                "directional_edge_vs_unconditional": directional_edge_vs_unconditional,
                "directional_edge_vs_cluster": directional_edge_vs_cluster,
                "passes_unconditional_median_edge": directional_edge_vs_unconditional > 0.0,
                "passes_cluster_median_edge": directional_edge_vs_cluster > 0.0,
                "matched_null_median_terminal_relative_return": null_median,
                "matched_null_directional_edge": directional_edge_vs_null,
                "matched_null_p_value": p_value,
                "matched_null_iterations": null_iterations,
            }
        )

    if not rows:
        return pd.DataFrame()
    referee = pd.DataFrame(rows)
    referee["passes_both_baselines"] = (
        referee["passes_unconditional_median_edge"] & referee["passes_cluster_median_edge"]
    )
    referee["matched_null_p_lt_0_05"] = referee["matched_null_p_value"] < 0.05
    referee["strict_survivor"] = (
        referee["validation_status"].eq("time_split_supported")
        & referee["passes_both_baselines"]
        & referee["matched_null_p_lt_0_05"]
    )
    return referee.sort_values(
        ["strict_survivor", "matched_null_p_value", "matched_null_directional_edge"],
        ascending=[False, True, False],
    ).reset_index(drop=True)


def run_grammar_search(
    analysis_frames_by_timeframe: dict[str, dict[str, pd.DataFrame]],
    *,
    grid_path: str | Path = DEFAULT_GRAMMAR_SEARCH_GRID,
    timeframes: list[str] | tuple[str, ...] = ("1d",),
    benchmark_name: str = "MEME_BASKET",
    min_sample_size: int = 20,
    entry_lag_bars: int = 1,
    cooldown_bars_by_timeframe: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[RuleVariant]]:
    specs = load_rule_search_grid(grid_path)
    normalized_timeframes = [timeframe.strip().lower() for timeframe in timeframes]
    variants = expand_rule_variants(specs, timeframes=normalized_timeframes)
    records = grammar_search_records(
        analysis_frames_by_timeframe,
        variants,
        benchmark_name=benchmark_name,
        entry_lag_bars=entry_lag_bars,
        cooldown_bars_by_timeframe=cooldown_bars_by_timeframe,
    )
    summary = summarize_grammar_search_records(records, variants=variants, min_sample_size=min_sample_size)
    ranked = ranked_grammar_search_summary(summary)
    family_summary = family_timeframe_summary(summary)
    return summary, records, ranked, family_summary, variants
