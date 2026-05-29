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
        prior_low = signal.shift(1).rolling(lookback, min_periods=max(3, lookback // 2)).min()
        near_or_higher_low = signal >= prior_low - low_tolerance
        slope = (signal - signal.shift(max(1, lookback // 2))) / max(1, lookback // 2)
        relative_slope = (relative - relative.shift(max(1, lookback // 2))) / max(1, lookback // 2)
        return ((signal <= zone_max) & near_or_higher_low & (slope >= min_slope) & (relative_slope >= relative_slope_min)).fillna(False)

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
