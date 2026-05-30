---
rf_type: setup_journey
journey_id: viscosity_acceptance_zero_confirmed
direction: bullish
status: candidate
promotion_level: L0_registered
claim_type: bullish_entry
setup_class: acceptance_confirmation_gate
primary_timeframes: [4h, 1d]
setup_conditions:
  - time_above_viscosity
  - viscosity_acceptance
  - prior_failed_impulse_spike
repair:
  - second_base_required
entry_triggers:
  - zero_reclaim
  - viscosity_reclaim
confirmation:
  - zero_retest_hold
  - second_base_or_double_bottom
invalidation:
  - zero_reclaim_failure
  - equilibrium_rejection
  - failed_impulse_spike
permission_filters:
  - warning_absent_or_cleared
required_controls:
  - acceptance_only
  - trigger_only
  - blocker_present
  - inverted_direction
source_cases:
  - GIGA_4h_20260415_constructive_unconfirmed_human_review
path_objective:
  min_sample_size: 30
  min_unique_symbols: 12
  min_event_clusters: 12
  min_mfe_mae_ratio: 1.25
branch_budget:
  max_generation: 2
---

# Viscosity Acceptance Zero Confirmed

## Claim

Time above viscosity may be constructive but not actionable until zero-line
confirmation or a second base appears. The setup should compare acceptance-only
against zero-confirmed acceptance.

## Source Cases

- [[GIGA_4h_20260415_constructive_unconfirmed_human_review]]

## Evidence Status

Candidate only. The source case explicitly says the initial structure was not
ready, so this journey should test confirmation gates before entry.

