---
observation_id: FLOKI_1d_20241106_0000_coil_viscosity_reclaim_v0
symbol: FLOKI
timeframe: 1d
date: 2024-11-06T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# FLOKI 1d 2024-11-06 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/29_FLOKI_20241106_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_FLOKI`
- Final signal / viscosity: `-1.439194363602002` / `-1.793318997942675`
- Relative component: `-2.1404657958805173`
- Compression score: `78.17460317460318`
- 3/7/14/30 bar forward relative return: `0.144009776087183` / `-0.1294317175967622` / `-0.000456869152139` / `-0.1421608144663273`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/29_FLOKI_20241106_0000.png`
