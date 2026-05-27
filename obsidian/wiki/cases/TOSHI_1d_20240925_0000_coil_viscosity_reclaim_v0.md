---
observation_id: TOSHI_1d_20240925_0000_coil_viscosity_reclaim_v0
symbol: TOSHI
timeframe: 1d
date: 2024-09-25T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# TOSHI 1d 2024-09-25 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/26_TOSHI_20240925_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_TOSHI`
- Final signal / viscosity: `-1.2543324824773547` / `-2.2084962249049`
- Relative component: `-1.5652633901910613`
- Compression score: `60.91269841269841`
- 3/7/14/30 bar forward relative return: `-0.1790408982578927` / `-0.021832418109697` / `-0.2370001696875177` / `-0.5876985347035475`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/26_TOSHI_20240925_0000.png`
