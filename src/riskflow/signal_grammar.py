from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml


SIGNAL_GRAMMAR_MODEL = "riskflow_signal_grammar_primitives_v0"

DEFAULT_TARGETS = {
    "clean_bullish_hits": 15,
    "bullish_false_positives": 10,
    "missed_breakouts": 10,
    "bearish_or_weakness_examples": 10,
    "noisy_or_ambiguous_edge_cases": 5,
}

GRAMMAR_FEATURE_MODEL = "signal_grammar_sidecar_v0"

GRAMMAR_FEATURE_COLUMNS = [
    "grammar_model",
    "grammar_pressure_distance",
    "grammar_time_above_viscosity_5",
    "grammar_time_above_viscosity_10",
    "grammar_time_above_viscosity_20",
    "grammar_sustained_above_viscosity_10",
    "grammar_pressure_area_above_20",
    "grammar_pressure_area_below_20",
    "grammar_pressure_area_balance_20",
    "grammar_pressure_area_delta_5",
    "grammar_fast_pressure",
    "grammar_slow_pressure",
    "grammar_fast_slow_pressure_gap",
    "grammar_signal_slope_3",
    "grammar_signal_slope_5",
    "grammar_signal_accel_3",
    "grammar_signal_curvature_up",
    "grammar_signal_curvature_down",
    "grammar_low_zone",
    "grammar_coil_under_viscosity",
    "grammar_tight_coil_below_viscosity",
    "grammar_rising_oscillator_lows",
    "grammar_relative_weakness_fails_to_accelerate",
    "grammar_minus_2_reclaim",
    "grammar_minus_2_retest_hold",
    "grammar_minus_1_5_reclaim",
    "grammar_minus_1_5_retest_hold",
    "grammar_zero_reclaim",
    "grammar_zero_retest_hold",
    "grammar_zero_rejection",
    "grammar_plus_1_5_lost",
    "grammar_upper_band_rejection",
    "grammar_bullish_divergence_20",
    "grammar_bearish_divergence_20",
    "grammar_gradient_momentum_divergence_20",
    "grammar_viscosity_cross_count_20",
    "grammar_clean_chop_quality",
    "grammar_chaotic_chop_quality",
    "grammar_recent_hot_leader_20",
    "grammar_hot_leader_cooloff",
    "grammar_reset_quality_watch",
    "grammar_pressure_acceptance_event",
    "grammar_viscosity_acceptance_flush_reclaim_event",
    "grammar_low_zone_failed_weakness_event",
    "grammar_minus_1_5_reclaim_after_coil_event",
    "grammar_zero_reclaim_confirmation_event",
    "grammar_curvature_up_from_low_zone_event",
    "grammar_bullish_divergence_reclaim_event",
    "grammar_clean_chop_reclaim_event",
    "grammar_zero_rejection_event",
    "grammar_bearish_divergence_warning_event",
    "grammar_chaotic_chop_warning_event",
    "grammar_hot_leader_reset_warning_event",
]

GRAMMAR_EVENT_NAMES = (
    "grammar_pressure_acceptance_v0",
    "grammar_viscosity_acceptance_flush_reclaim_v0",
    "grammar_low_zone_failed_weakness_v0",
    "grammar_minus_1_5_reclaim_after_coil_v0",
    "grammar_zero_reclaim_confirmation_v0",
    "grammar_curvature_up_from_low_zone_v0",
    "grammar_bullish_divergence_reclaim_v0",
    "grammar_clean_chop_reclaim_v0",
    "grammar_zero_rejection_v0",
    "grammar_bearish_divergence_warning_v0",
    "grammar_chaotic_chop_warning_v0",
    "grammar_hot_leader_reset_warning_v0",
)

SCENARIO_TAGS = {
    "clean_bullish_hits": {
        "fast_clean_hit",
        "slow_hit",
        "delayed_hit",
        "viscosity_reclaim",
        "viscosity_retest_hold",
        "minus_one_point_five_reclaim",
        "minus_two_reclaim",
    },
    "bullish_false_positives": {
        "false_positive",
        "failed_breakout",
        "failed_reversal_watchlist",
        "weak_breakout_response",
        "failed_strength_acceptance",
    },
    "missed_breakouts": {
        "missed_breakout",
        "low_in_before_price_confirmation",
        "price_needs_chop",
        "zero_confirmation_missing",
    },
    "bearish_or_weakness_examples": {
        "bearish_divergence",
        "hidden_bearish_divergence",
        "color_divergence",
        "gradient_momentum_divergence",
        "zero_rejection",
        "upper_band_rejection",
        "underside_support_rejection",
    },
    "noisy_or_ambiguous_edge_cases": {
        "mixed_or_flat",
        "chaotic_oscillator_pa",
        "unstructured_volatility",
        "unstable_strength",
        "constructive_wave_without_signal_confirmation",
    },
}


@dataclass(frozen=True)
class GrammarLabPaths:
    primitive_summary_csv: Path
    review_plan_md: Path
    obsidian_note_md: Path | None = None


def load_primitive_registry(path: str | Path = "research/grammar/primitive_registry.yaml") -> dict:
    registry_path = Path(path)
    with registry_path.open(encoding="utf-8") as file:
        registry = yaml.safe_load(file)
    if not isinstance(registry, dict):
        raise ValueError(f"Grammar registry {registry_path} must contain a mapping.")
    model = registry.get("model")
    if model != SIGNAL_GRAMMAR_MODEL:
        raise ValueError(f"Unknown grammar registry model: {model!r}")
    if not isinstance(registry.get("primitive_families"), dict):
        raise ValueError("Grammar registry must define primitive_families.")
    return registry


def _split_tags(value: object) -> set[str]:
    if value is None or pd.isna(value):
        return set()
    if isinstance(value, (list, tuple, set)):
        raw_tags = value
    else:
        raw_tags = str(value).replace("|", ",").split(",")
    return {str(tag).strip() for tag in raw_tags if str(tag).strip()}


def _as_numeric(frame: pd.DataFrame, column: str, default: float = np.nan) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").astype(float)


def _crosses_above(series: pd.Series, threshold: float) -> pd.Series:
    return ((series > threshold) & (series.shift(1) <= threshold)).fillna(False)


def _crosses_below(series: pd.Series, threshold: float) -> pd.Series:
    return ((series < threshold) & (series.shift(1) >= threshold)).fillna(False)


def _rolling_true_count(mask: pd.Series, window: int) -> pd.Series:
    return mask.astype(float).rolling(window, min_periods=1).sum()


def _recent(mask: pd.Series, window: int) -> pd.Series:
    return _rolling_true_count(mask.fillna(False), window) > 0.0


def _rolling_cross_count(mask: pd.Series, window: int) -> pd.Series:
    changes = mask.astype("boolean").ne(mask.astype("boolean").shift(1)).fillna(False)
    return changes.astype(float).rolling(window, min_periods=1).sum()


def _retest_hold(
    signal: pd.Series,
    level: float,
    reclaim: pd.Series,
    *,
    lookback: int = 12,
    tolerance: float = 0.15,
) -> pd.Series:
    recent_reclaim = _recent(reclaim, lookback)
    near_level = signal.between(level - tolerance, level + tolerance)
    holding = signal >= level - tolerance
    curling = signal.diff() >= 0.0
    return (recent_reclaim & near_level & holding & curling).fillna(False)


def calculate_signal_grammar_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build research-only oscillator grammar sidecars.

    These columns translate the current visual Signal Grammar Lab vocabulary into
    measurable primitives and candidate events. They intentionally do not alter
    production signal, state, setup, or score meanings.
    """
    features = pd.DataFrame(index=frame.index)
    if frame.empty:
        for column in GRAMMAR_FEATURE_COLUMNS:
            features[column] = pd.NA
        return features[GRAMMAR_FEATURE_COLUMNS]

    signal = _as_numeric(frame, "final_signal")
    viscosity = _as_numeric(frame, "viscosity")
    target = _as_numeric(frame, "target")
    gradient = _as_numeric(frame, "gradient_driver")
    compression = _as_numeric(frame, "compression_score", default=0.0)
    pressure = signal - viscosity
    above_viscosity = (pressure > 0.0).fillna(False)
    below_viscosity = (pressure < 0.0).fillna(False)

    features["grammar_model"] = GRAMMAR_FEATURE_MODEL
    features["grammar_pressure_distance"] = pressure
    for window in (5, 10, 20):
        features[f"grammar_time_above_viscosity_{window}"] = _rolling_true_count(above_viscosity, window)
    features["grammar_sustained_above_viscosity_10"] = features["grammar_time_above_viscosity_10"] >= 7.0

    positive_pressure = pressure.clip(lower=0.0)
    negative_pressure = pressure.clip(upper=0.0).abs()
    features["grammar_pressure_area_above_20"] = positive_pressure.rolling(20, min_periods=1).sum()
    features["grammar_pressure_area_below_20"] = negative_pressure.rolling(20, min_periods=1).sum()
    features["grammar_pressure_area_balance_20"] = (
        features["grammar_pressure_area_above_20"] - features["grammar_pressure_area_below_20"]
    )
    features["grammar_pressure_area_delta_5"] = features["grammar_pressure_area_balance_20"].diff(5)
    features["grammar_fast_pressure"] = pressure.ewm(span=3, adjust=False, min_periods=1).mean()
    features["grammar_slow_pressure"] = pressure.ewm(span=10, adjust=False, min_periods=1).mean()
    features["grammar_fast_slow_pressure_gap"] = features["grammar_fast_pressure"] - features["grammar_slow_pressure"]

    features["grammar_signal_slope_3"] = (signal - signal.shift(3)) / 3.0
    features["grammar_signal_slope_5"] = (signal - signal.shift(5)) / 5.0
    features["grammar_signal_accel_3"] = features["grammar_signal_slope_3"].diff(3) / 3.0
    features["grammar_signal_curvature_up"] = (
        (features["grammar_signal_slope_3"] > features["grammar_signal_slope_3"].shift(1))
        & (features["grammar_signal_accel_3"] > 0.0)
    ).fillna(False)
    features["grammar_signal_curvature_down"] = (
        (features["grammar_signal_slope_3"] < features["grammar_signal_slope_3"].shift(1))
        & (features["grammar_signal_accel_3"] < 0.0)
    ).fillna(False)

    rolling_signal_range_10 = signal.rolling(10, min_periods=3).max() - signal.rolling(10, min_periods=3).min()
    rolling_signal_std_10 = signal.rolling(10, min_periods=3).std(ddof=0)
    rolling_signal_low_10 = signal.rolling(10, min_periods=3).min()
    features["grammar_low_zone"] = (signal <= -1.5).fillna(False)
    features["grammar_coil_under_viscosity"] = (
        below_viscosity
        & signal.between(-2.6, -1.0)
        & (rolling_signal_range_10 <= 0.80)
        & (rolling_signal_std_10 <= 0.35)
    ).fillna(False)
    features["grammar_tight_coil_below_viscosity"] = (
        below_viscosity
        & signal.between(-2.4, -1.2)
        & (rolling_signal_range_10 <= 0.45)
        & (rolling_signal_std_10 <= 0.22)
    ).fillna(False)
    features["grammar_rising_oscillator_lows"] = (rolling_signal_low_10 > rolling_signal_low_10.shift(5)).fillna(False)
    features["grammar_relative_weakness_fails_to_accelerate"] = (
        (rolling_signal_low_10 <= -1.5)
        & features["grammar_rising_oscillator_lows"]
        & (features["grammar_signal_accel_3"] >= 0.0)
    ).fillna(False)

    minus_2_reclaim = _crosses_above(signal, -2.0)
    minus_1_5_reclaim = _crosses_above(signal, -1.5)
    zero_reclaim = _crosses_above(signal, 0.0)
    features["grammar_minus_2_reclaim"] = minus_2_reclaim
    features["grammar_minus_2_retest_hold"] = _retest_hold(signal, -2.0, minus_2_reclaim)
    features["grammar_minus_1_5_reclaim"] = minus_1_5_reclaim
    features["grammar_minus_1_5_retest_hold"] = _retest_hold(signal, -1.5, minus_1_5_reclaim)
    features["grammar_zero_reclaim"] = zero_reclaim
    features["grammar_zero_retest_hold"] = _retest_hold(signal, 0.0, zero_reclaim, tolerance=0.20)
    features["grammar_zero_rejection"] = (
        signal.shift(1).between(-0.25, 0.25)
        & (signal < 0.0)
        & (signal.diff() < 0.0)
    ).fillna(False)
    features["grammar_plus_1_5_lost"] = _crosses_below(signal, 1.5)
    features["grammar_upper_band_rejection"] = (
        (signal.shift(1) >= 1.5)
        & (signal < signal.shift(1))
        & (features["grammar_signal_accel_3"] < 0.0)
    ).fillna(False)

    price_low_10 = target.rolling(10, min_periods=5).min()
    signal_low_10 = signal.rolling(10, min_periods=5).min()
    price_high_10 = target.rolling(10, min_periods=5).max()
    signal_high_10 = signal.rolling(10, min_periods=5).max()
    gradient_high_10 = gradient.rolling(10, min_periods=5).max()
    features["grammar_bullish_divergence_20"] = (
        (price_low_10 <= price_low_10.shift(10) * 1.01)
        & (signal_low_10 >= signal_low_10.shift(10) + 0.15)
    ).fillna(False)
    features["grammar_bearish_divergence_20"] = (
        (price_high_10 >= price_high_10.shift(10) * 0.99)
        & (signal_high_10 <= signal_high_10.shift(10) - 0.15)
    ).fillna(False)
    features["grammar_gradient_momentum_divergence_20"] = (
        (price_high_10 >= price_high_10.shift(10) * 0.99)
        & (gradient_high_10 <= gradient_high_10.shift(10) - 0.15)
    ).fillna(False)

    signal_range_20 = signal.rolling(20, min_periods=5).max() - signal.rolling(20, min_periods=5).min()
    signal_std_20 = signal.rolling(20, min_periods=5).std(ddof=0)
    features["grammar_viscosity_cross_count_20"] = _rolling_cross_count(above_viscosity, 20)
    features["grammar_clean_chop_quality"] = (
        (compression >= 70.0)
        & (signal_range_20 <= 1.00)
        & (signal_std_20 <= 0.40)
        & (features["grammar_viscosity_cross_count_20"] <= 4.0)
    ).fillna(False)
    features["grammar_chaotic_chop_quality"] = (
        (features["grammar_viscosity_cross_count_20"] >= 6.0)
        & ((signal_range_20 >= 1.60) | (signal_std_20 >= 0.65))
    ).fillna(False)

    features["grammar_recent_hot_leader_20"] = (signal.rolling(20, min_periods=1).max() >= 1.5).fillna(False)
    features["grammar_hot_leader_cooloff"] = (
        features["grammar_recent_hot_leader_20"]
        & ((signal < viscosity) | features["grammar_plus_1_5_lost"])
        & (features["grammar_signal_slope_3"] < 0.0)
    ).fillna(False)
    features["grammar_reset_quality_watch"] = (
        features["grammar_hot_leader_cooloff"]
        & signal.between(-1.5, 1.0)
        & (compression >= 50.0)
    ).fillna(False)

    viscosity_reclaim = (above_viscosity & ~above_viscosity.shift(1, fill_value=False)).fillna(False)
    recent_coil = _recent(features["grammar_coil_under_viscosity"], 10)
    recent_failed_weakness = _recent(features["grammar_relative_weakness_fails_to_accelerate"], 10)
    recent_sustained_above = _recent(features["grammar_sustained_above_viscosity_10"], 12)
    recent_flush = _recent(below_viscosity, 3)
    recent_low_zone = _recent(features["grammar_low_zone"], 20)
    features["grammar_pressure_acceptance_event"] = (
        features["grammar_sustained_above_viscosity_10"]
        & (features["grammar_pressure_area_balance_20"] > 0.50)
        & (features["grammar_pressure_area_delta_5"] > 0.0)
    ).fillna(False)
    features["grammar_viscosity_acceptance_flush_reclaim_event"] = (
        viscosity_reclaim & recent_sustained_above.shift(1, fill_value=False) & recent_flush.shift(1, fill_value=False)
    ).fillna(False)
    features["grammar_low_zone_failed_weakness_event"] = (
        recent_failed_weakness & (viscosity_reclaim | minus_2_reclaim | minus_1_5_reclaim)
    ).fillna(False)
    features["grammar_minus_1_5_reclaim_after_coil_event"] = (minus_1_5_reclaim & recent_coil).fillna(False)
    features["grammar_zero_reclaim_confirmation_event"] = (
        zero_reclaim & _recent(above_viscosity, 10) & (features["grammar_pressure_area_balance_20"] > 0.0)
    ).fillna(False)
    features["grammar_curvature_up_from_low_zone_event"] = (
        recent_low_zone & features["grammar_signal_curvature_up"] & (features["grammar_signal_slope_3"] > 0.0)
    ).fillna(False)
    features["grammar_bullish_divergence_reclaim_event"] = (
        features["grammar_bullish_divergence_20"] & (viscosity_reclaim | minus_1_5_reclaim | zero_reclaim)
    ).fillna(False)
    features["grammar_clean_chop_reclaim_event"] = (
        features["grammar_clean_chop_quality"] & (viscosity_reclaim | minus_1_5_reclaim | zero_reclaim)
    ).fillna(False)
    features["grammar_zero_rejection_event"] = features["grammar_zero_rejection"]
    features["grammar_bearish_divergence_warning_event"] = (
        features["grammar_bearish_divergence_20"] | features["grammar_gradient_momentum_divergence_20"]
    ).fillna(False)
    features["grammar_chaotic_chop_warning_event"] = features["grammar_chaotic_chop_quality"]
    features["grammar_hot_leader_reset_warning_event"] = features["grammar_hot_leader_cooloff"]

    for column in GRAMMAR_FEATURE_COLUMNS:
        if column not in features.columns:
            features[column] = pd.NA
    return features[GRAMMAR_FEATURE_COLUMNS]


def detect_signal_grammar_events(frame: pd.DataFrame) -> dict[str, pd.Series]:
    """Return candidate grammar event masks from a frame with sidecar columns."""
    if not set(GRAMMAR_FEATURE_COLUMNS).issubset(frame.columns):
        features = calculate_signal_grammar_features(frame)
    else:
        features = frame
    event_columns = {
        "grammar_pressure_acceptance_v0": "grammar_pressure_acceptance_event",
        "grammar_viscosity_acceptance_flush_reclaim_v0": "grammar_viscosity_acceptance_flush_reclaim_event",
        "grammar_low_zone_failed_weakness_v0": "grammar_low_zone_failed_weakness_event",
        "grammar_minus_1_5_reclaim_after_coil_v0": "grammar_minus_1_5_reclaim_after_coil_event",
        "grammar_zero_reclaim_confirmation_v0": "grammar_zero_reclaim_confirmation_event",
        "grammar_curvature_up_from_low_zone_v0": "grammar_curvature_up_from_low_zone_event",
        "grammar_bullish_divergence_reclaim_v0": "grammar_bullish_divergence_reclaim_event",
        "grammar_clean_chop_reclaim_v0": "grammar_clean_chop_reclaim_event",
        "grammar_zero_rejection_v0": "grammar_zero_rejection_event",
        "grammar_bearish_divergence_warning_v0": "grammar_bearish_divergence_warning_event",
        "grammar_chaotic_chop_warning_v0": "grammar_chaotic_chop_warning_event",
        "grammar_hot_leader_reset_warning_v0": "grammar_hot_leader_reset_warning_event",
    }
    events: dict[str, pd.Series] = {}
    for event_name, column in event_columns.items():
        if column in features.columns:
            events[event_name] = features[column].fillna(False).astype(bool)
        else:
            events[event_name] = pd.Series(False, index=frame.index)
    return events


def _load_observation_records(path: str | Path) -> pd.DataFrame:
    records_path = Path(path)
    if not records_path.exists():
        return pd.DataFrame()
    records = pd.read_csv(records_path)
    if "tags" not in records.columns:
        records["tags"] = ""
    return records


def _all_registry_primitives(registry: dict) -> set[str]:
    primitives: set[str] = set()
    for family in registry["primitive_families"].values():
        primitives.update(family.get("candidate_primitives", []) or [])
    return primitives


def build_primitive_summary(registry: dict, observations: pd.DataFrame | None = None) -> pd.DataFrame:
    observations = pd.DataFrame() if observations is None else observations.copy()
    observed_tags: list[set[str]] = [_split_tags(value) for value in observations.get("tags", [])]
    rows: list[dict[str, object]] = []

    for family_name, family in registry["primitive_families"].items():
        description = str(family.get("description", ""))
        first_tests = " | ".join(str(test) for test in family.get("first_tests", []) or [])
        for primitive in family.get("candidate_primitives", []) or []:
            observation_count = sum(primitive in tags for tags in observed_tags)
            rows.append(
                {
                    "grammar_model": registry["model"],
                    "family": family_name,
                    "primitive": primitive,
                    "description": description,
                    "observation_count": int(observation_count),
                    "evidence_status": "needs_observations" if observation_count == 0 else "observed_needs_testing",
                    "first_tests": first_tests,
                }
            )
    return pd.DataFrame(rows)


def _scenario_count(records: pd.DataFrame, scenario: str) -> int:
    if records.empty:
        return 0
    tags = SCENARIO_TAGS.get(scenario, set())
    count = 0
    for _, row in records.iterrows():
        row_tags = _split_tags(row.get("tags", ""))
        label = str(row.get("outcome_label", "")).strip()
        human_label = str(row.get("human_label", "")).strip()
        if row_tags.intersection(tags) or label in tags or human_label in tags:
            count += 1
    return count


def build_review_plan(
    registry: dict,
    observations: pd.DataFrame | None = None,
    *,
    title: str = "Signal Grammar Lab Review Plan",
) -> str:
    observations = pd.DataFrame() if observations is None else observations.copy()
    targets = registry.get("review_targets", {}) or {}
    target_counts = {key: int(targets.get(key, DEFAULT_TARGETS[key])) for key in DEFAULT_TARGETS}
    primitive_summary = build_primitive_summary(registry, observations)
    observed_primitives = primitive_summary[primitive_summary["observation_count"] > 0]
    missing_primitives = primitive_summary[primitive_summary["observation_count"] == 0]
    total_observations = len(observations)

    progress_rows = []
    for scenario, target in target_counts.items():
        current = _scenario_count(observations, scenario)
        remaining = max(target - current, 0)
        progress_rows.append((scenario, current, target, remaining))

    progress_table = "\n".join(
        f"| `{scenario}` | {current} | {target} | {remaining} |"
        for scenario, current, target, remaining in progress_rows
    )
    family_counts = (
        primitive_summary.groupby("family")["observation_count"].sum().sort_values(ascending=False).to_dict()
        if not primitive_summary.empty
        else {}
    )
    family_lines = "\n".join(f"- `{family}`: {count}" for family, count in family_counts.items())
    missing_lines = "\n".join(f"- `{row.primitive}` ({row.family})" for row in missing_primitives.itertuples(index=False))
    observed_lines = "\n".join(
        f"- `{row.primitive}` ({row.family}): {row.observation_count}"
        for row in observed_primitives.sort_values("observation_count", ascending=False).itertuples(index=False)
    )

    return f"""# {title}

Model: `{registry['model']}`

## Verdict

The grammar lab is a research queue, not a production signal. The base oscillator should remain frozen until repeated observations and Layer 7 evidence identify which primitives matter.

## Observation Progress

Total structured observations loaded: `{total_observations}`

| Scenario | Current | Target | Remaining |
|---|---:|---:|---:|
{progress_table}

## Primitive Family Coverage

{family_lines or '_No primitive observations yet._'}

## Observed Primitives

{observed_lines or '_No primitives observed yet._'}

## Missing Primitive Coverage

{missing_lines or '_All registered primitives have at least one observation._'}

## Next Review Batch

Prioritize the largest remaining scenario gaps first. Include both `4h` and `1d`, avoid one date cluster, and include failed/bearish examples alongside clean winners.

## Promotion Reminder

A primitive graduates only after it is measurable, appears across multiple symbols/date clusters, improves forward relative-return evidence, and remains readable on a TradingView-style chart.
"""


def unknown_observation_tags(registry: dict, observations: pd.DataFrame) -> set[str]:
    known = _all_registry_primitives(registry)
    known.update(SCENARIO_TAGS.keys())
    known.update(tag for tags in SCENARIO_TAGS.values() for tag in tags)
    unknown: set[str] = set()
    for value in observations.get("tags", []):
        unknown.update(_split_tags(value) - known)
    return unknown


def export_grammar_lab(
    *,
    registry_path: str | Path = "research/grammar/primitive_registry.yaml",
    observations_csv: str | Path = "research/observations/observation_records.csv",
    output_dir: str | Path = "reports/grammar_lab",
    obsidian_dir: str | Path | None = "obsidian",
) -> GrammarLabPaths:
    registry = load_primitive_registry(registry_path)
    observations = _load_observation_records(observations_csv)
    primitive_summary = build_primitive_summary(registry, observations)
    review_plan = build_review_plan(registry, observations)

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    primitive_summary_csv = output_root / "primitive_summary.csv"
    review_plan_md = output_root / "review_plan.md"
    primitive_summary.to_csv(primitive_summary_csv, index=False)
    review_plan_md.write_text(review_plan, encoding="utf-8")

    obsidian_note: Path | None = None
    if obsidian_dir:
        obsidian_note = Path(obsidian_dir) / "wiki" / "maps" / "Signal Grammar Lab.md"
        obsidian_note.parent.mkdir(parents=True, exist_ok=True)
        obsidian_note.write_text(review_plan, encoding="utf-8")

    return GrammarLabPaths(
        primitive_summary_csv=primitive_summary_csv,
        review_plan_md=review_plan_md,
        obsidian_note_md=obsidian_note,
    )
