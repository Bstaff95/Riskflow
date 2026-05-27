---
observation_id: TRUMP_1d_20260313_0000_coil_viscosity_reclaim_v0
symbol: TRUMP
timeframe: 1d
date: 2026-03-13T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# TRUMP 1d 2026-03-13 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Under Zero Coil]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/06_TRUMP_20260313_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_TRUMP`
- Final signal / viscosity: `-0.421059585271785` / `-1.2221141237701716`
- Relative component: `1.3189879336673995`
- Compression score: `21.52777777777777`
- 3/7/14/30 bar forward relative return: `-0.1575276291360071` / `-0.1665557332242901` / `-0.2077059472427398` / `-0.3069031050519178`
- Outcome label: `false_positive`

## Tags

`below_zero`, `coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `relative_component_observed`, `under_zero`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/06_TRUMP_20260313_0000.png`
