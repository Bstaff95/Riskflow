---
rf_type: setup_journey
journey_id: failed_first_break_second_base_reclaim
direction: bullish
status: candidate
promotion_level: L0_registered
claim_type: bullish_entry
setup_class: post_failed_break_reset_reclaim
primary_timeframes: [4h, 1d]
setup_conditions:
  - failed_first_trendline_break
  - deep_reset_below_minus_two
  - second_base_or_second_structure
repair:
  - relative_weakness_fails_to_accelerate
entry_triggers:
  - viscosity_reclaim
  - minus_one_point_five_reclaim
confirmation:
  - viscosity_retest_hold
  - second_structure_break
invalidation:
  - reclaim_loss
  - weak_breakout_response
  - warning_refire
permission_filters:
  - warning_absent_or_cleared
required_controls:
  - trigger_only
  - permission_only
  - blocker_present
  - inverted_direction
source_cases:
  - TURBO_4h_20260321_failed_breakout_reset_reclaim_human_review
path_objective:
  min_sample_size: 30
  min_unique_symbols: 12
  min_event_clusters: 12
  min_mfe_mae_ratio: 1.25
branch_budget:
  max_generation: 2
---

# Failed First Break Second Base Reclaim

## Claim

A first oscillator trendline break can fail. The better bullish setup may be the
second structure after a deeper reset, followed by viscosity reclaim, retest
hold, and reclaim of the lower gate.

## Source Cases

- [[TURBO_4h_20260321_failed_breakout_reset_reclaim_human_review]]

## Evidence Status

Candidate only. This note is a hypothesis source for the Python grammar lab, not
proof.

