---
rf_type: concept
concept_id: lab_loop
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Use the governed research loop and promotion ladder before interpreting lab outputs as product candidates.
not_product_proof: true
---

# Lab Loop

The Lab Loop is the operating system for autonomous Riskflow research.

It keeps the lab focused on one mission:

> Find Riskflow structures that improve trade selection versus the relevant basket.

## Standing Tracks

- warning and avoidance
- bullish setup journeys
- entry and invalidation
- gradient translation only after evidence

## Loop Order

1. Pull ranked hypotheses from `research/lab_loop/hypothesis_queue.yaml`.
2. Encode exact measurable rules or staged sequences.
3. Run across `1d`, `12h`, `4h`, and `1h`.
4. Validate with time splits, baselines, matched nulls, concentration checks, lag sensitivity, and cooldown sensitivity.
5. Review false positives and missed winners when evidence justifies it.
6. Promote, refine, or archive.
7. Write what was learned.
8. Generate the next queue items from evidence.

## Promotion Ladder

```text
L0_registered
L1_encoded
L2_discovered
L3_strict_survivor
L4_fresh_data_survivor
L5_indicator_candidate
```

## Current Saved Decisions

- Bullish setups should be tested as journeys, not isolated triggers.
- Daily relative failed breakout is a warning candidate, not production logic.
- Gradient logic should wait for fresh-data evidence.
- Agents should be used after several loops, major survivors, dead-loop streaks, or possible direction changes.

Related:

- [[Signal Grammar Lab]]
- [[Grammar Map]]
- [[Indicator Grammar]]
- [[Agentic Research Loop]]
- [[Trace Grading For Riskflow]]
- [[Process Score Is Not Product Evidence]]
- [[Agentic Loop Research Map]]
