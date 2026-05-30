---
rf_type: setup_journey
journey_id: accepted_viscosity_flush_reclaim
direction: bullish
status: candidate
promotion_level: L0_registered
claim_type: bullish_entry
setup_class: post_acceptance_shakeout_reclaim
primary_timeframes: [4h, 12h]
setup_conditions:
  - rising_oscillator_lows
  - time_above_viscosity
  - viscosity_acceptance
repair:
  - failed_viscosity_breakdown
entry_triggers:
  - fast_viscosity_reclaim
  - reclaim_after_flush
confirmation:
  - relative_improving
  - sustained_above_viscosity
invalidation:
  - viscosity_loss
  - no_meaningful_bounce
  - relative_deterioration
permission_filters:
  - warning_absent_or_cleared
required_controls:
  - trigger_only
  - permission_only
  - blocker_present
  - inverted_direction
source_cases:
  - MOG_4h_20260405_viscosity_acceptance_human_review
path_objective:
  min_sample_size: 30
  min_unique_symbols: 12
  min_event_clusters: 12
  min_mfe_mae_ratio: 1.25
branch_budget:
  max_generation: 2
---

# Accepted Viscosity Flush Reclaim

## Claim

Sustained time above viscosity can be constructive without immediate impulse.
The actionable moment may be the brief flush below viscosity that fails quickly,
followed by fast reclaim and relative repair.

## Source Cases

- [[MOG_4h_20260405_viscosity_acceptance_human_review]]

## Evidence Status

Candidate only. This note compiles into lab controls and must pass numeric
evidence before it can affect indicator behavior.

