from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .grammar_search import (
    family_timeframe_summary,
    ranked_grammar_search_summary,
    summarize_grammar_search_records,
    timeframe_cooldown,
    timeframe_horizons,
)
from .research_outcomes import (
    apply_event_cooldown,
    benchmark_label_at,
    entry_date_at,
    event_cluster_id,
    forward_max_drawdown,
    forward_relative_return,
    forward_return,
)


INDICATOR_BEHAVIOR_PRIMITIVE_MODEL = "riskflow_indicator_behavior_primitives_v0"
INDICATOR_BEHAVIOR_CONCEPT_MODEL = "riskflow_indicator_behavior_concept_library_v0"
DEFAULT_PRIMITIVE_REGISTRY = "research/indicator_behavior/primitive_registry.yaml"
DEFAULT_CONCEPT_LIBRARY = "research/indicator_behavior/concept_library.yaml"

REQUIRED_CONCEPT_FIELDS = {
    "id",
    "family",
    "direction",
    "priority",
    "primitives",
    "riskflow_inputs",
    "implementation_status",
}


@dataclass(frozen=True)
class IndicatorBehaviorConcept:
    concept_id: str
    family: str
    direction: str
    priority: str
    primitives: tuple[str, ...]
    riskflow_inputs: tuple[str, ...]
    implementation_status: str


@dataclass(frozen=True)
class IndicatorBehaviorVariant:
    variant_id: str
    family_id: str
    direction: str
    detector: str
    params: dict[str, Any]


def load_indicator_behavior_primitive_registry(
    path: str | Path = DEFAULT_PRIMITIVE_REGISTRY,
) -> dict[str, Any]:
    registry_path = Path(path)
    with registry_path.open(encoding="utf-8") as file:
        registry = yaml.safe_load(file)
    if not isinstance(registry, dict):
        raise ValueError(f"Indicator behavior primitive registry {registry_path} must contain a mapping.")
    if registry.get("model") != INDICATOR_BEHAVIOR_PRIMITIVE_MODEL:
        raise ValueError(f"Unknown indicator behavior primitive model: {registry.get('model')!r}")
    families = registry.get("primitive_families")
    if not isinstance(families, dict):
        raise ValueError("Indicator behavior primitive registry must define primitive_families.")
    return registry


def indicator_behavior_primitive_ids(registry: dict[str, Any]) -> set[str]:
    families = registry.get("primitive_families")
    if not isinstance(families, dict):
        raise ValueError("Indicator behavior primitive registry must define primitive_families.")

    primitive_ids: set[str] = set()
    for family_id, family in families.items():
        if not isinstance(family, dict):
            raise ValueError(f"Primitive family {family_id!r} must be a mapping.")
        primitives = family.get("primitives")
        if not isinstance(primitives, dict):
            raise ValueError(f"Primitive family {family_id!r} must define a primitives mapping.")
        primitive_ids.update(str(primitive_id) for primitive_id in primitives)
    return primitive_ids


def load_indicator_behavior_concepts(
    path: str | Path = DEFAULT_CONCEPT_LIBRARY,
    *,
    primitive_registry_path: str | Path = DEFAULT_PRIMITIVE_REGISTRY,
) -> list[IndicatorBehaviorConcept]:
    library_path = Path(path)
    with library_path.open(encoding="utf-8") as file:
        library = yaml.safe_load(file)
    if not isinstance(library, dict):
        raise ValueError(f"Indicator behavior concept library {library_path} must contain a mapping.")
    if library.get("model") != INDICATOR_BEHAVIOR_CONCEPT_MODEL:
        raise ValueError(f"Unknown indicator behavior concept model: {library.get('model')!r}")

    raw_concepts = library.get("concepts")
    if not isinstance(raw_concepts, list):
        raise ValueError("Indicator behavior concept library must define a concepts list.")

    registry = load_indicator_behavior_primitive_registry(primitive_registry_path)
    valid_primitives = indicator_behavior_primitive_ids(registry)
    concepts: list[IndicatorBehaviorConcept] = []
    seen_ids: set[str] = set()
    unknown_primitives: dict[str, list[str]] = {}

    for index, raw_concept in enumerate(raw_concepts, start=1):
        if not isinstance(raw_concept, dict):
            raise ValueError(f"Indicator behavior concept #{index} must be a mapping.")
        missing = REQUIRED_CONCEPT_FIELDS - set(raw_concept)
        if missing:
            raise ValueError(f"Indicator behavior concept #{index} is missing fields: {sorted(missing)}")

        concept_id = str(raw_concept["id"])
        if concept_id in seen_ids:
            raise ValueError(f"Duplicate indicator behavior concept id: {concept_id}")
        seen_ids.add(concept_id)

        primitives = tuple(str(primitive) for primitive in raw_concept["primitives"])
        unknown = [primitive for primitive in primitives if primitive not in valid_primitives]
        if unknown:
            unknown_primitives[concept_id] = unknown

        concepts.append(
            IndicatorBehaviorConcept(
                concept_id=concept_id,
                family=str(raw_concept["family"]),
                direction=str(raw_concept["direction"]),
                priority=str(raw_concept["priority"]),
                primitives=primitives,
                riskflow_inputs=tuple(str(input_name) for input_name in raw_concept["riskflow_inputs"]),
                implementation_status=str(raw_concept["implementation_status"]),
            )
        )

    if unknown_primitives:
        raise ValueError(f"Unknown indicator behavior primitives: {unknown_primitives}")

    return concepts


def summarize_indicator_behavior_concepts(
    concepts: list[IndicatorBehaviorConcept],
) -> dict[str, dict[str, int] | int]:
    return {
        "concept_count": len(concepts),
        "family_counts": dict(Counter(concept.family for concept in concepts)),
        "direction_counts": dict(Counter(concept.direction for concept in concepts)),
        "priority_counts": dict(Counter(concept.priority for concept in concepts)),
        "implementation_status_counts": dict(Counter(concept.implementation_status for concept in concepts)),
    }


def first_batch_indicator_behavior_concepts(
    concepts: list[IndicatorBehaviorConcept],
) -> list[IndicatorBehaviorConcept]:
    return [concept for concept in concepts if concept.priority == "first_batch"]


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
    return mask.fillna(False).astype(float).rolling(max(1, window), min_periods=1).sum() > 0.0


def _rolling_slope(series: pd.Series, window: int) -> pd.Series:
    lookback = max(1, int(window))
    return (series - series.shift(lookback)) / float(lookback)


def _scaled_threshold(series: pd.Series, threshold: float) -> float:
    finite = pd.to_numeric(series, errors="coerce").dropna()
    if threshold <= 1.0 and not finite.empty and finite.quantile(0.95) > 2.0:
        return threshold * 100.0
    return threshold


def _rolling_quantile_threshold(series: pd.Series, window: int, quantile: float) -> pd.Series:
    return series.rolling(max(5, window), min_periods=max(3, window // 2)).quantile(quantile)


def _pct_change(series: pd.Series) -> pd.Series:
    return series.pct_change(fill_method=None)


def _local_lower_high(series: pd.Series, *, lookback: int = 20, recent_window: int = 5, gap: float = 0.1) -> pd.Series:
    prior_high = series.shift(recent_window).rolling(lookback, min_periods=max(3, lookback // 2)).max()
    recent_high = series.rolling(recent_window, min_periods=max(2, recent_window // 2)).max()
    return (recent_high <= prior_high - gap).fillna(False)


def _local_higher_low(series: pd.Series, *, lookback: int = 20, recent_window: int = 5, gap: float = 0.1) -> pd.Series:
    prior_low = series.shift(recent_window).rolling(lookback, min_periods=max(3, lookback // 2)).min()
    recent_low = series.rolling(recent_window, min_periods=max(2, recent_window // 2)).min()
    return (recent_low >= prior_low + gap).fillna(False)


def _baseline_retest_hold(signal: pd.Series, viscosity: pd.Series, *, lookback: int = 12, tolerance: float = 0.2) -> pd.Series:
    reclaimed = _crosses_above(signal - viscosity, 0.0)
    recent_reclaim = _recent(reclaimed.shift(1, fill_value=False), lookback)
    near_baseline = (signal - viscosity).abs() <= tolerance
    holding = signal >= viscosity - tolerance
    return (recent_reclaim & near_baseline & holding & (_rolling_slope(signal, 3) >= 0.0)).fillna(False)


def _baseline_retest_fail(signal: pd.Series, viscosity: pd.Series, *, lookback: int = 12, tolerance: float = 0.2) -> pd.Series:
    reclaimed = _crosses_above(signal - viscosity, 0.0)
    recently_near = _recent(((signal - viscosity).abs() <= tolerance).shift(1, fill_value=False), lookback)
    return (
        _recent(reclaimed.shift(1, fill_value=False), lookback)
        & recently_near
        & _crosses_below(signal - viscosity, 0.0)
    ).fillna(False)


def detect_indicator_behavior_primitive(
    frame: pd.DataFrame,
    primitive_id: str,
    *,
    context_window: int = 10,
) -> pd.Series:
    signal = _as_numeric(frame, "final_signal")
    viscosity = _as_numeric(frame, "viscosity")
    gradient = _as_numeric(frame, "gradient_driver")
    relative = _as_numeric(frame, "relative_component")
    target = _as_numeric(frame, "target")
    benchmark = _as_numeric(frame, "benchmark")
    compression = _as_numeric(frame, "compression_score", default=0.0)
    volume = _as_numeric(frame, "volume", default=0.0)
    pressure = signal - viscosity

    if primitive_id == "signal_below_low_band":
        return (signal <= -1.5).fillna(False)
    if primitive_id == "signal_above_high_band":
        return (signal >= 1.5).fillna(False)
    if primitive_id == "signal_cross_above_low_band":
        return (_crosses_above(signal, -1.5) | _crosses_above(signal, -1.0)).fillna(False)
    if primitive_id == "signal_cross_below_high_band":
        return (_crosses_below(signal, 1.5) | _crosses_below(signal, 1.0)).fillna(False)
    if primitive_id == "signal_cross_above_zero":
        return _crosses_above(signal, 0.0)
    if primitive_id == "signal_cross_below_zero":
        return _crosses_below(signal, 0.0)
    if primitive_id == "zero_rejection_from_below":
        sidecar = _as_bool(frame, "grammar_zero_rejection")
        near_zero = signal.between(-0.35, 0.25)
        return (sidecar | (near_zero & (signal.diff() < 0.0) & (signal < viscosity))).fillna(False)
    if primitive_id == "zero_retest_hold_from_above":
        sidecar = _as_bool(frame, "grammar_zero_retest_hold")
        near_zero = signal.between(-0.2, 0.35)
        return (sidecar | (near_zero & (signal.diff() >= 0.0) & (signal >= viscosity))).fillna(False)

    if primitive_id == "signal_higher_low":
        return (_as_bool(frame, "grammar_rising_oscillator_lows") | _local_higher_low(signal)).fillna(False)
    if primitive_id == "signal_lower_high":
        return _local_lower_high(signal).fillna(False)
    if primitive_id == "signal_slope_up":
        return ((_as_numeric(frame, "grammar_signal_slope_3", default=signal.diff()) > 0.0) | (_rolling_slope(signal, 5) > 0.0)).fillna(False)
    if primitive_id == "signal_slope_down":
        return ((_as_numeric(frame, "grammar_signal_slope_3", default=signal.diff()) < 0.0) | (_rolling_slope(signal, 5) < 0.0)).fillna(False)
    if primitive_id == "signal_accelerating_up":
        return (_as_bool(frame, "grammar_signal_curvature_up") | ((_rolling_slope(signal, 3) > _rolling_slope(signal, 3).shift(1)) & (signal.diff() > 0.0))).fillna(False)
    if primitive_id == "signal_decelerating_up":
        return ((signal > 0.0) & (signal.diff() <= 0.0)).fillna(False)
    if primitive_id == "signal_accelerating_down":
        return (_as_bool(frame, "grammar_signal_curvature_down") | ((_rolling_slope(signal, 3) < _rolling_slope(signal, 3).shift(1)) & (signal.diff() < 0.0))).fillna(False)
    if primitive_id == "signal_repairing_from_down":
        return ((signal < 0.0) & (signal.diff() > 0.0) & (signal.diff().diff() >= 0.0)).fillna(False)

    if primitive_id == "price_lower_low_signal_higher_low":
        return (_as_bool(frame, "grammar_bullish_divergence_20") | ((target <= target.shift(5).rolling(20, min_periods=10).min()) & _local_higher_low(signal))).fillna(False)
    if primitive_id == "price_higher_high_signal_lower_high":
        return (_as_bool(frame, "grammar_bearish_divergence_20") | ((target >= target.shift(5).rolling(20, min_periods=10).max()) & _local_lower_high(signal))).fillna(False)
    if primitive_id == "relative_lower_low_signal_higher_low":
        return ((relative <= relative.shift(5).rolling(20, min_periods=10).min()) & _local_higher_low(signal)).fillna(False)
    if primitive_id == "relative_higher_high_signal_lower_high":
        return ((relative >= relative.shift(5).rolling(20, min_periods=10).max()) & _local_lower_high(signal)).fillna(False)
    if primitive_id == "gradient_momentum_divergence":
        return (_as_bool(frame, "grammar_gradient_momentum_divergence_20") | ((target.diff(5) > 0.0) & (gradient.diff(5) < 0.0))).fillna(False)

    if primitive_id == "viscosity_reclaim":
        return _crosses_above(pressure, 0.0)
    if primitive_id == "viscosity_loss":
        return _crosses_below(pressure, 0.0)
    if primitive_id == "time_above_viscosity":
        sidecar = _as_numeric(frame, "grammar_time_above_viscosity_10")
        return ((sidecar >= 6.0) | (pressure.gt(0.0).rolling(10, min_periods=1).mean() >= 0.6)).fillna(False)
    if primitive_id == "sustained_above_viscosity":
        return (_as_bool(frame, "grammar_sustained_above_viscosity_10") | (pressure.gt(0.0).rolling(10, min_periods=1).mean() >= 0.7)).fillna(False)
    if primitive_id == "pressure_area_positive":
        return (_as_numeric(frame, "grammar_pressure_area_balance_20", default=pressure.rolling(20, min_periods=1).sum()) > 0.0).fillna(False)
    if primitive_id == "pressure_area_negative":
        return (_as_numeric(frame, "grammar_pressure_area_balance_20", default=pressure.rolling(20, min_periods=1).sum()) < 0.0).fillna(False)
    if primitive_id == "baseline_flat":
        return ((viscosity.diff().abs().rolling(10, min_periods=5).mean() <= 0.06) & (signal.rolling(10, min_periods=5).std(ddof=0) <= 0.45)).fillna(False)
    if primitive_id == "baseline_slope_up":
        return (_rolling_slope(viscosity, 5) > 0.0).fillna(False)
    if primitive_id == "baseline_slope_down":
        return (_rolling_slope(viscosity, 5) < 0.0).fillna(False)
    if primitive_id == "baseline_retest_hold":
        return _baseline_retest_hold(signal, viscosity)
    if primitive_id == "baseline_retest_fail":
        return _baseline_retest_fail(signal, viscosity)

    if primitive_id == "gradient_positive_expanding":
        return ((gradient > 0.0) & (gradient.diff(3) > 0.0)).fillna(False)
    if primitive_id == "gradient_positive_fading":
        return ((gradient > 0.0) & (gradient.diff(3) < 0.0)).fillna(False)
    if primitive_id == "gradient_negative_expanding":
        return ((gradient < 0.0) & (gradient.diff(3) < 0.0)).fillna(False)
    if primitive_id == "gradient_negative_repairing":
        return ((gradient < 0.0) & (gradient.diff(3) > 0.0)).fillna(False)
    if primitive_id == "fast_pressure_cross_up":
        gap = _as_numeric(frame, "grammar_fast_slow_pressure_gap", default=pressure.ewm(span=3, adjust=False).mean() - pressure.ewm(span=10, adjust=False).mean())
        return _crosses_above(gap, 0.0)
    if primitive_id == "fast_pressure_cross_down":
        gap = _as_numeric(frame, "grammar_fast_slow_pressure_gap", default=pressure.ewm(span=3, adjust=False).mean() - pressure.ewm(span=10, adjust=False).mean())
        return _crosses_below(gap, 0.0)

    if primitive_id == "compression_high":
        return (compression >= _scaled_threshold(compression, 0.70)).fillna(False)
    if primitive_id == "compression_low":
        return (compression <= _scaled_threshold(compression, 0.30)).fillna(False)
    if primitive_id == "compression_release_up":
        high = compression.shift(1).rolling(context_window, min_periods=3).max() >= _scaled_threshold(compression, 0.70)
        return (high & (compression.diff() < 0.0) & (gradient > 0.0) & (signal.diff() > 0.0)).fillna(False)
    if primitive_id == "compression_release_down":
        high = compression.shift(1).rolling(context_window, min_periods=3).max() >= _scaled_threshold(compression, 0.70)
        return (high & (compression.diff() < 0.0) & (gradient < 0.0) & (signal.diff() < 0.0)).fillna(False)
    if primitive_id == "range_expansion_up":
        target_return = _pct_change(target)
        move = target_return.abs()
        return ((target_return > 0.0) & (move >= _rolling_quantile_threshold(move, 20, 0.8))).fillna(False)
    if primitive_id == "range_expansion_down":
        target_return = _pct_change(target)
        move = target_return.abs()
        return ((target_return < 0.0) & (move >= _rolling_quantile_threshold(move, 20, 0.8))).fillna(False)
    if primitive_id == "range_expansion_unconfirmed":
        move = _pct_change(target).abs()
        return ((move >= _rolling_quantile_threshold(move, 20, 0.8)) & ((gradient.diff(3) <= 0.0) | (relative.diff(3) <= 0.0))).fillna(False)

    volume_median = volume.rolling(20, min_periods=5).median().replace(0.0, np.nan)
    if primitive_id == "volume_spike":
        return (volume >= volume_median * 2.0).fillna(False)
    if primitive_id == "volume_dryup":
        return (volume <= volume_median * 0.6).fillna(False)
    if primitive_id == "volume_spike_failed_reclaim":
        return (detect_indicator_behavior_primitive(frame, "volume_spike") & _recent(_crosses_above(pressure, 0.0), context_window) & (pressure < 0.0)).fillna(False)
    if primitive_id == "volume_spike_confirmed_reclaim":
        return (detect_indicator_behavior_primitive(frame, "volume_spike") & _crosses_above(pressure, 0.0)).fillna(False)
    if primitive_id == "signed_volume_accumulation":
        signed = np.sign(target.diff()).fillna(0.0) * volume
        return ((signed.rolling(20, min_periods=5).sum() > 0.0) & (relative.diff(5) > 0.0)).fillna(False)
    if primitive_id == "volume_divergent_breakout":
        return (detect_indicator_behavior_primitive(frame, "range_expansion_up") & (volume < volume_median) & (gradient.diff(3) <= 0.0)).fillna(False)

    if primitive_id == "relative_improving":
        return (_rolling_slope(relative, 5) > 0.0).fillna(False)
    if primitive_id == "relative_deteriorating":
        return (_rolling_slope(relative, 5) < 0.0).fillna(False)
    if primitive_id == "relative_reclaim":
        return _crosses_above(relative, 0.0)
    if primitive_id == "relative_failed_breakout":
        prior_high = relative.shift(1).rolling(20, min_periods=10).max()
        breakout = relative > prior_high
        return (_recent(breakout.shift(1, fill_value=False), 5) & (relative < prior_high)).fillna(False)
    if primitive_id == "relative_lower_high":
        return _local_lower_high(relative, gap=0.05).fillna(False)
    if primitive_id == "peer_decoupling_bull":
        return ((relative.diff(5) > 0.0) & (benchmark.diff(5) <= 0.0)).fillna(False)
    if primitive_id == "peer_decoupling_bear":
        return ((relative.diff(5) < 0.0) & (benchmark.diff(5) >= 0.0)).fillna(False)
    if primitive_id == "correlation_spike_risk_off":
        same_direction = np.sign(_pct_change(target)).eq(np.sign(_pct_change(benchmark)))
        return (same_direction.rolling(20, min_periods=10).mean() >= 0.75).fillna(False)

    if primitive_id == "higher_tf_positive_bias":
        return ((signal > viscosity) & (relative.diff(5) > 0.0)).fillna(False)
    if primitive_id == "higher_tf_negative_bias":
        return ((signal < viscosity) & (relative.diff(5) < 0.0)).fillna(False)
    if primitive_id == "lower_tf_reclaim":
        return _crosses_above(pressure, 0.0)
    if primitive_id == "lower_tf_bounce_fail":
        return (_recent(_crosses_above(pressure, 0.0), context_window) & (pressure < 0.0)).fillna(False)
    if primitive_id == "mtf_compression_stack":
        return (compression >= _scaled_threshold(compression, 0.70)).fillna(False)

    return pd.Series(False, index=frame.index, dtype=bool)


def detect_indicator_behavior_events(frame: pd.DataFrame, variant: IndicatorBehaviorVariant) -> pd.Series:
    context_window = int(variant.params.get("context_window", 10))
    primitive_masks = [
        _recent(
            detect_indicator_behavior_primitive(frame, primitive_id, context_window=context_window),
            context_window,
        )
        for primitive_id in variant.params.get("primitives", [])
    ]
    if not primitive_masks:
        return pd.Series(False, index=frame.index, dtype=bool)
    mask = primitive_masks[0].copy()
    for primitive_mask in primitive_masks[1:]:
        mask &= primitive_mask
    return mask.fillna(False)


def expand_indicator_behavior_variants(
    concepts: list[IndicatorBehaviorConcept],
    *,
    timeframes: list[str] | tuple[str, ...] = ("1d",),
    priority: str | None = "first_batch",
    context_windows: list[int] | tuple[int, ...] = (10,),
) -> list[IndicatorBehaviorVariant]:
    variants: list[IndicatorBehaviorVariant] = []
    selected = [concept for concept in concepts if priority is None or concept.priority == priority]
    for timeframe in timeframes:
        normalized_timeframe = timeframe.strip().lower()
        for concept in selected:
            for context_window in context_windows:
                variant_id = (
                    f"indicator_behavior.{concept.concept_id}.v0."
                    f"tf_{normalized_timeframe}.ctx_{int(context_window)}"
                )
                variants.append(
                    IndicatorBehaviorVariant(
                        variant_id=variant_id,
                        family_id=concept.concept_id,
                        direction=concept.direction,
                        detector="primitive_context_all",
                        params={
                            "timeframe": normalized_timeframe,
                            "context_window": int(context_window),
                            "primitives": list(concept.primitives),
                            "implementation_status": concept.implementation_status,
                        },
                    )
                )
    return variants


def _variant_records_for_asset(
    symbol: str,
    frame: pd.DataFrame,
    variant: IndicatorBehaviorVariant,
    *,
    timeframe: str,
    benchmark_name: str,
    horizons: tuple[int, ...],
    entry_lag_bars: int,
    cooldown_bars: int,
) -> pd.DataFrame:
    target = _as_numeric(frame, "target")
    benchmark = _as_numeric(frame, "benchmark")
    raw_mask = detect_indicator_behavior_events(frame, variant)
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


def indicator_behavior_records(
    analysis_frames_by_timeframe: dict[str, dict[str, pd.DataFrame]],
    variants: list[IndicatorBehaviorVariant],
    *,
    benchmark_name: str = "MEME_BASKET",
    entry_lag_bars: int = 1,
    cooldown_bars_by_timeframe: dict[str, int] | None = None,
) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    variants_by_timeframe: dict[str, list[IndicatorBehaviorVariant]] = {}
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


def run_indicator_behavior_search(
    analysis_frames_by_timeframe: dict[str, dict[str, pd.DataFrame]],
    *,
    concept_library_path: str | Path = DEFAULT_CONCEPT_LIBRARY,
    primitive_registry_path: str | Path = DEFAULT_PRIMITIVE_REGISTRY,
    timeframes: list[str] | tuple[str, ...] = ("1d",),
    priority: str | None = "first_batch",
    context_windows: list[int] | tuple[int, ...] = (10,),
    benchmark_name: str = "MEME_BASKET",
    min_sample_size: int = 20,
    entry_lag_bars: int = 1,
    cooldown_bars_by_timeframe: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[IndicatorBehaviorVariant]]:
    concepts = load_indicator_behavior_concepts(
        concept_library_path,
        primitive_registry_path=primitive_registry_path,
    )
    normalized_timeframes = [timeframe.strip().lower() for timeframe in timeframes]
    variants = expand_indicator_behavior_variants(
        concepts,
        timeframes=normalized_timeframes,
        priority=priority,
        context_windows=context_windows,
    )
    records = indicator_behavior_records(
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
