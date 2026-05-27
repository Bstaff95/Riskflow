from __future__ import annotations

from dataclasses import dataclass


CORE_EVENT = "core_event"
SETUP_EVENT = "setup_event"
STATE_EVENT = "state_event"
SIGNAL_EVENT = "signal_event"
SCORE_EVENT = "score_event"
GRAMMAR_EVENT = "grammar_event"

DEFAULT_EVENT_ENTRY_LAG_BARS = 1
DEFAULT_EVENT_COOLDOWN_BARS = 30


@dataclass(frozen=True)
class EventSpec:
    event_id: str
    family: str
    version: int
    default_trigger: float | None
    default_entry_lag_bars: int
    default_cooldown_bars: int
    priority: int
    direction: str
    value_column: str | None
    description: str


def _spec(
    event_id: str,
    family: str,
    *,
    trigger: float | None = None,
    priority: int = 100,
    direction: str = "positive",
    value_column: str | None = None,
    description: str,
) -> EventSpec:
    return EventSpec(
        event_id=event_id,
        family=family,
        version=0,
        default_trigger=trigger,
        default_entry_lag_bars=DEFAULT_EVENT_ENTRY_LAG_BARS,
        default_cooldown_bars=DEFAULT_EVENT_COOLDOWN_BARS,
        priority=priority,
        direction=direction,
        value_column=value_column,
        description=description,
    )


EVENT_REGISTRY: dict[str, EventSpec] = {
    "signal_crosses_above_viscosity": _spec(
        "signal_crosses_above_viscosity",
        CORE_EVENT,
        priority=10,
        value_column="final_signal",
        description="Final signal crosses above the adaptive viscosity baseline.",
    ),
    "signal_crosses_above_zero": _spec(
        "signal_crosses_above_zero",
        CORE_EVENT,
        trigger=0.0,
        priority=20,
        value_column="final_signal",
        description="Final signal crosses above zero.",
    ),
    "relative_component_crosses_above_zero": _spec(
        "relative_component_crosses_above_zero",
        CORE_EVENT,
        trigger=0.0,
        priority=25,
        value_column="relative_component",
        description="Relative component crosses above zero.",
    ),
    "final_signal_reclaims_minus_1_5": _spec(
        "final_signal_reclaims_minus_1_5",
        CORE_EVENT,
        trigger=-1.5,
        priority=30,
        value_column="final_signal",
        description="Final signal reclaims the lower -1.5 gate.",
    ),
    "compression_80_relative_rising": _spec(
        "compression_80_relative_rising",
        SETUP_EVENT,
        trigger=80.0,
        priority=40,
        value_column="compression_score",
        description="Compression is high while relative strength is rising.",
    ),
    "state_becomes_emerging_leader": _spec(
        "state_becomes_emerging_leader",
        STATE_EVENT,
        priority=45,
        value_column="state",
        description="Lifecycle state changes into Emerging Leader.",
    ),
    "state_becomes_confirmed_leader": _spec(
        "state_becomes_confirmed_leader",
        STATE_EVENT,
        priority=50,
        value_column="state",
        description="Lifecycle state changes into Confirmed Leader.",
    ),
    "signal_crosses_below_viscosity": _spec(
        "signal_crosses_below_viscosity",
        CORE_EVENT,
        priority=80,
        direction="negative",
        value_column="final_signal",
        description="Final signal crosses below viscosity.",
    ),
    "signal_fails_near_zero": _spec(
        "signal_fails_near_zero",
        CORE_EVENT,
        priority=85,
        direction="negative",
        value_column="final_signal",
        description="Final signal rejects near zero and turns down.",
    ),
    "compression_score_above_80": _spec(
        "compression_score_above_80",
        SETUP_EVENT,
        trigger=80.0,
        priority=55,
        value_column="compression_score",
        description="Compression score crosses above 80.",
    ),
    "compression_duration_above_threshold": _spec(
        "compression_duration_above_threshold",
        SETUP_EVENT,
        trigger=5.0,
        priority=60,
        value_column="compression_duration",
        description="Compression duration crosses the v0 threshold.",
    ),
    "compression_plus_relative_rising": _spec(
        "compression_plus_relative_rising",
        SETUP_EVENT,
        trigger=70.0,
        priority=42,
        value_column="compression_score",
        description="Compression is present and relative component is rising.",
    ),
    "setup_readiness_score_crosses_threshold": _spec(
        "setup_readiness_score_crosses_threshold",
        SETUP_EVENT,
        trigger=70.0,
        priority=35,
        value_column="setup_readiness_score",
        description="Setup readiness score crosses the v0 threshold.",
    ),
    "relative_accumulation_score_crosses_threshold": _spec(
        "relative_accumulation_score_crosses_threshold",
        SETUP_EVENT,
        trigger=65.0,
        priority=37,
        value_column="relative_accumulation_score",
        description="Relative accumulation score crosses the v0 threshold.",
    ),
    "compressed_viscosity_reclaim": _spec(
        "compressed_viscosity_reclaim",
        SETUP_EVENT,
        priority=32,
        value_column="final_signal",
        description="Compressed asset reclaims viscosity.",
    ),
    "compressed_zero_reclaim": _spec(
        "compressed_zero_reclaim",
        SETUP_EVENT,
        trigger=0.0,
        priority=34,
        value_column="final_signal",
        description="Compressed asset reclaims zero.",
    ),
    "extension_risk_score_crosses_high": _spec(
        "extension_risk_score_crosses_high",
        SETUP_EVENT,
        trigger=70.0,
        priority=90,
        direction="negative",
        value_column="extension_risk_score",
        description="Extension risk crosses high threshold.",
    ),
    "trader_score_crosses_threshold": _spec(
        "trader_score_crosses_threshold",
        SETUP_EVENT,
        trigger=70.0,
        priority=38,
        value_column="trader_score_v0",
        description="Experimental trader score crosses the v0 threshold.",
    ),
    "score_bucket_observation": _spec(
        "score_bucket_observation",
        SCORE_EVENT,
        priority=100,
        value_column="score_value",
        description="Score research observation used for ranking evidence.",
    ),
    "grammar_pressure_acceptance_v0": _spec(
        "grammar_pressure_acceptance_v0",
        GRAMMAR_EVENT,
        priority=110,
        value_column="grammar_pressure_area_balance_20",
        description="Research sidecar: sustained positive area above viscosity.",
    ),
    "grammar_viscosity_acceptance_flush_reclaim_v0": _spec(
        "grammar_viscosity_acceptance_flush_reclaim_v0",
        GRAMMAR_EVENT,
        priority=111,
        value_column="grammar_pressure_distance",
        description="Research sidecar: accepted viscosity, flushed below, then reclaimed.",
    ),
    "grammar_low_zone_failed_weakness_v0": _spec(
        "grammar_low_zone_failed_weakness_v0",
        GRAMMAR_EVENT,
        priority=112,
        value_column="grammar_signal_slope_3",
        description="Research sidecar: deep negative weakness stops accelerating and reclaims a trigger.",
    ),
    "grammar_minus_1_5_reclaim_after_coil_v0": _spec(
        "grammar_minus_1_5_reclaim_after_coil_v0",
        GRAMMAR_EVENT,
        priority=113,
        value_column="final_signal",
        description="Research sidecar: -1.5 reclaim after lower-zone coil under viscosity.",
    ),
    "grammar_zero_reclaim_confirmation_v0": _spec(
        "grammar_zero_reclaim_confirmation_v0",
        GRAMMAR_EVENT,
        priority=114,
        value_column="final_signal",
        description="Research sidecar: zero reclaim after prior viscosity acceptance.",
    ),
    "grammar_curvature_up_from_low_zone_v0": _spec(
        "grammar_curvature_up_from_low_zone_v0",
        GRAMMAR_EVENT,
        priority=115,
        value_column="grammar_signal_accel_3",
        description="Research sidecar: slope and acceleration curl upward from a recent low zone.",
    ),
    "grammar_bullish_divergence_reclaim_v0": _spec(
        "grammar_bullish_divergence_reclaim_v0",
        GRAMMAR_EVENT,
        priority=116,
        value_column="final_signal",
        description="Research sidecar: price/oscillator bullish divergence with reclaim confirmation.",
    ),
    "grammar_clean_chop_reclaim_v0": _spec(
        "grammar_clean_chop_reclaim_v0",
        GRAMMAR_EVENT,
        priority=117,
        value_column="compression_score",
        description="Research sidecar: compressed clean oscillator chop plus reclaim.",
    ),
    "grammar_zero_rejection_v0": _spec(
        "grammar_zero_rejection_v0",
        GRAMMAR_EVENT,
        priority=130,
        direction="negative",
        value_column="final_signal",
        description="Research sidecar: oscillator rejects near zero and turns down.",
    ),
    "grammar_bearish_divergence_warning_v0": _spec(
        "grammar_bearish_divergence_warning_v0",
        GRAMMAR_EVENT,
        priority=131,
        direction="negative",
        value_column="gradient_driver",
        description="Research sidecar: price strength with weaker oscillator or gradient highs.",
    ),
    "grammar_chaotic_chop_warning_v0": _spec(
        "grammar_chaotic_chop_warning_v0",
        GRAMMAR_EVENT,
        priority=132,
        direction="negative",
        value_column="grammar_viscosity_cross_count_20",
        description="Research sidecar: violent oscillator chop around viscosity.",
    ),
    "grammar_hot_leader_reset_warning_v0": _spec(
        "grammar_hot_leader_reset_warning_v0",
        GRAMMAR_EVENT,
        priority=133,
        direction="negative",
        value_column="final_signal",
        description="Research sidecar: hot leader cooloff or reset warning after +1.5/+2 pressure.",
    ),
}


def get_event_spec(event_id: str) -> EventSpec:
    try:
        return EVENT_REGISTRY[event_id]
    except KeyError as exc:
        raise KeyError(f"Unknown event_id: {event_id}") from exc
