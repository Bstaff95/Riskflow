---
observation_id: TURBO_1d_20260312_0000_coil_viscosity_reclaim_v0
symbol: TURBO
timeframe: 1d
date: 2026-03-12T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# TURBO 1d 2026-03-12 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Under Zero Coil]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/01_TURBO_20260312_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_TURBO`
- Final signal / viscosity: `-0.2733160917124349` / `-1.416157979963416`
- Relative component: `1.567108463895175`
- Compression score: `63.59126984126984`
- 3/7/14/30 bar forward relative return: `-0.112388294645758` / `-0.1168010076519878` / `-0.023102448478272` / `-0.0663556883978588`
- Outcome label: `false_positive`

## Tags

`below_zero`, `coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `relative_component_observed`, `under_zero`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/01_TURBO_20260312_0000.png`
