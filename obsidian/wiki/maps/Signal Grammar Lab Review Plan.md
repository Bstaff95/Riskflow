# Signal Grammar Lab Review Plan

Related current hub: [[Grammar Map]]

Model: `riskflow_signal_grammar_primitives_v0`

## Verdict

The grammar lab is a research queue, not a production signal. The base oscillator should remain frozen until repeated observations and Layer 7 evidence identify which primitives matter.

## Observation Progress

Total structured observations loaded: `30`

| Scenario | Current | Target | Remaining |
|---|---:|---:|---:|
| `clean_bullish_hits` | 30 | 15 | 0 |
| `bullish_false_positives` | 16 | 10 | 0 |
| `missed_breakouts` | 0 | 10 | 10 |
| `bearish_or_weakness_examples` | 0 | 10 | 10 |
| `noisy_or_ambiguous_edge_cases` | 2 | 5 | 3 |

## Primitive Family Coverage

- `adaptive_universal_weighting`: 0
- `curvature_intent`: 0
- `divergence_quality`: 0
- `failed_weakness`: 0
- `oscillator_structure`: 0
- `pressure_acceptance`: 0
- `zone_reclaim_retest`: 0

## Observed Primitives

_No primitives observed yet._

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

Prioritize the largest remaining scenario gaps first. Include both `4h` and `1d`, avoid one date cluster, and include failed/bearish examples alongside clean winners.

## Promotion Reminder

A primitive graduates only after it is measurable, appears across multiple symbols/date clusters, improves forward relative-return evidence, and remains readable on a TradingView-style chart.
