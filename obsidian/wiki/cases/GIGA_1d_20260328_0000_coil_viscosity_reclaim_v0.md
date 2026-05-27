---
observation_id: GIGA_1d_20260328_0000_coil_viscosity_reclaim_v0
symbol: GIGA
timeframe: 1d
date: 2026-03-28T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# GIGA 1d 2026-03-28 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/18_GIGA_20260328_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_GIGA`
- Final signal / viscosity: `-1.3820618777259293` / `-1.9820999466683464`
- Relative component: `-0.5797141029950593`
- Compression score: `81.64682539682539`
- 3/7/14/30 bar forward relative return: `-0.1371378436648346` / `-0.1880736733665329` / `-0.1799159528191997` / `-0.345830800927255`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/18_GIGA_20260328_0000.png`
