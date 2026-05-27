---
observation_id: MOG_1d_20260420_0000_coil_viscosity_reclaim_v0
symbol: MOG
timeframe: 1d
date: 2026-04-20T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# MOG 1d 2026-04-20 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/15_MOG_20260420_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_MOG`
- Final signal / viscosity: `-1.4013634073847372` / `-1.870797030171692`
- Relative component: `-1.1779835441575046`
- Compression score: `79.76190476190476`
- 3/7/14/30 bar forward relative return: `0.007461091650851` / `-0.0263228306489996` / `-0.1427723677367208` / `-0.2195342392379893`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/15_MOG_20260420_0000.png`
