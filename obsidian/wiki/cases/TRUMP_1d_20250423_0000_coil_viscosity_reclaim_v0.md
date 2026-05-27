---
observation_id: TRUMP_1d_20250423_0000_coil_viscosity_reclaim_v0
symbol: TRUMP
timeframe: 1d
date: 2025-04-23T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# TRUMP 1d 2025-04-23 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Under Zero Coil]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/03_TRUMP_20250423_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_TRUMP`
- Final signal / viscosity: `-0.6388364523036949` / `-1.7460963912165577`
- Relative component: `-1.19206943963427`
- Compression score: `60.46268430384472`
- 3/7/14/30 bar forward relative return: `0.1180359788292173` / `-0.0815484736609788` / `-0.2120458771683991` / `-0.3555620003023531`
- Outcome label: `false_positive`

## Tags

`below_zero`, `coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `relative_component_observed`, `under_zero`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/03_TRUMP_20250423_0000.png`
