---
observation_id: TURBO_1d_20260321_0000_coil_viscosity_reclaim_v0
symbol: TURBO
timeframe: 1d
date: 2026-03-21T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# TURBO 1d 2026-03-21 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Under Zero Coil]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/02_TURBO_20260321_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_TURBO`
- Final signal / viscosity: `-0.5479492875036837` / `-1.2322384635849752`
- Relative component: `1.0627950730128333`
- Compression score: `49.6031746031746`
- 3/7/14/30 bar forward relative return: `-0.095160222563476` / `-0.0762618895006493` / `-0.0923340811739256` / `-0.1298036612077879`
- Outcome label: `false_positive`

## Tags

`below_zero`, `coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `relative_component_observed`, `under_zero`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/02_TURBO_20260321_0000.png`
