---
observation_id: TOSHI_1d_20241106_0000_coil_viscosity_reclaim_v0
symbol: TOSHI
timeframe: 1d
date: 2024-11-06T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# TOSHI 1d 2024-11-06 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/17_TOSHI_20241106_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_TOSHI`
- Final signal / viscosity: `-1.1295132906595575` / `-1.583120350061679`
- Relative component: `-1.694249921358078`
- Compression score: `80.2579365079365`
- 3/7/14/30 bar forward relative return: `-0.0874729212563243` / `0.0468865110814162` / `-0.1144544359290143` / `-0.0596300729971899`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/17_TOSHI_20241106_0000.png`
