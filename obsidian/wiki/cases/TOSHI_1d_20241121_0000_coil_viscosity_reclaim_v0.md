---
observation_id: TOSHI_1d_20241121_0000_coil_viscosity_reclaim_v0
symbol: TOSHI
timeframe: 1d
date: 2024-11-21T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# TOSHI 1d 2024-11-21 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/27_TOSHI_20241121_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_TOSHI`
- Final signal / viscosity: `0.0295703696915794` / `-0.233868940629761`
- Relative component: `-1.5582191446015243`
- Compression score: `32.93650793650794`
- 3/7/14/30 bar forward relative return: `-0.0466436093058012` / `-0.2416710885662892` / `0.0724955098748949` / `-0.3875277822146383`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `constructive`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `relative_component_observed`, `viscosity_reclaim`, `zero_zone`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/27_TOSHI_20241121_0000.png`
