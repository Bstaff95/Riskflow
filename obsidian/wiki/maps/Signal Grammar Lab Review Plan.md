# Signal Grammar Lab Review Plan

Related current hub: [[Grammar Map]]

Model: `riskflow_signal_grammar_primitives_v0`

## Verdict

The grammar lab is a research queue, not a production signal. The base oscillator should remain frozen until repeated observations and Layer 7 evidence identify which primitives matter.

Current priority: begin the Grammar Candidate Sprint. Additional missing, bearish, and noisy cases are calibration backfill, not the blocking path.

## Observation Progress

Total structured observations loaded: `30`

This table reflects generated/structured observation coverage. It does not fully capture human-reviewed wiki coverage from the live chart-review loop.

| Scenario | Current | Target | Remaining |
|---|---:|---:|---:|
| `clean_bullish_hits` | 30 | 15 | 0 |
| `bullish_false_positives` | 16 | 10 | 0 |
| `missed_breakouts` | 0 | 10 | 10 |
| `bearish_or_weakness_examples` | 0 | 10 | 10 |
| `noisy_or_ambiguous_edge_cases` | 2 | 5 | 3 |

## Primitive Family Coverage

Structured/generated primitive coverage is still incomplete:

- `adaptive_universal_weighting`: 0
- `curvature_intent`: 0
- `divergence_quality`: 0
- `failed_weakness`: 0
- `oscillator_structure`: 0
- `pressure_acceptance`: 0
- `zone_reclaim_retest`: 0

## Human-Reviewed Primitive Coverage

Human-reviewed chart work has already produced useful grammar hypotheses:

- `pressure_acceptance`: sustained above-viscosity behavior, time above viscosity, signed area above/below viscosity, flush/reclaim behavior.
- `failed_weakness`: low-zone rejection where weakness fails to accelerate, rising oscillator lows, tight coil under viscosity.
- `zone_reclaim_retest`: `-2`, `-1.5`, `0`, `1.5`, and `2` reclaim/retest behavior.
- `oscillator_structure`: downtrend breaks, descending wedges, ascending wedges, channels, second trendline breaks, failed first breaks.
- `divergence_quality`: bullish divergence, bearish divergence, hidden bearish divergence, color/gradient divergence.
- `curvature_intent`: slope turns, acceleration turns, early curl toward zero or away from overheated zones.
- `chop_quality`: clean sideways compression versus violent unstructured chop.
- `reset_quality`: hot leader cooloff, break below `1.5`, rebasing after overheated impulse.

## Missing Primitive Coverage

- `time_above_viscosity` (pressure_acceptance)
- `sustained_above_viscosity` (pressure_acceptance)
- `pressure_area_balance` (pressure_acceptance)
- `pressure_area_delta` (pressure_acceptance)
- `fast_slow_pressure_gap` (pressure_acceptance)
- `failed_viscosity_breakdown` (pressure_acceptance)
- `reclaim_after_flush` (pressure_acceptance)
- `low_zone_viscosity_rejection` (failed_weakness)
- `coil_under_viscosity` (failed_weakness)
- `tight_coil_below_viscosity` (failed_weakness)
- `relative_weakness_fails_to_accelerate` (failed_weakness)
- `rising_oscillator_lows` (failed_weakness)
- `weakness_exhaustion` (failed_weakness)
- `minus_two_reclaim` (zone_reclaim_retest)
- `minus_two_retest_hold` (zone_reclaim_retest)
- `minus_one_point_five_reclaim` (zone_reclaim_retest)
- `minus_one_point_five_retest_hold` (zone_reclaim_retest)
- `zero_reclaim` (zone_reclaim_retest)
- `zero_retest_hold` (zone_reclaim_retest)
- `zero_rejection` (zone_reclaim_retest)
- `upper_band_rejection` (zone_reclaim_retest)
- `oscillator_trendline_break` (oscillator_structure)
- `oscillator_downtrend_resistance` (oscillator_structure)
- `long_term_signal_downtrend_break` (oscillator_structure)
- `descending_wedge` (oscillator_structure)
- `ascending_wedge` (oscillator_structure)
- `descending_channel` (oscillator_structure)
- `channel_breakout` (oscillator_structure)
- `failed_first_trendline_break` (oscillator_structure)
- `second_trendline_break` (oscillator_structure)
- `bullish_divergence` (divergence_quality)
- `bearish_divergence` (divergence_quality)
- `hidden_bearish_divergence` (divergence_quality)
- `bullish_divergence_after_double_bottom` (divergence_quality)
- `color_divergence` (divergence_quality)
- `weaker_second_color_push` (divergence_quality)
- `gradient_momentum_divergence` (divergence_quality)
- `signal_slope_turn` (curvature_intent)
- `signal_acceleration_turn` (curvature_intent)
- `signal_curvature_up` (curvature_intent)
- `signal_curvature_down` (curvature_intent)
- `fast_pressure_cross` (curvature_intent)
- `slow_pressure_turn` (curvature_intent)
- `volatility_adaptive_weighting` (adaptive_universal_weighting)
- `benchmark_role_adaptive_weighting` (adaptive_universal_weighting)
- `component_information_weighting` (adaptive_universal_weighting)
- `data_quality_weighting` (adaptive_universal_weighting)

## Next Review Batch

Use new review batches only to backfill weak evidence. The next primary task is implementation of measurable sidecar features/events for the strongest human-reviewed primitives.

## Promotion Reminder

A primitive graduates only after it is measurable, appears across multiple symbols/date clusters, improves forward relative-return evidence, and remains readable on a TradingView-style chart.
