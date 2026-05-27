---
observation_id: MEW_1d_20260323_0000_coil_viscosity_reclaim_v0
symbol: MEW
timeframe: 1d
date: 2026-03-23T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# MEW 1d 2026-03-23 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/28_MEW_20260323_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_MEW`
- Final signal / viscosity: `-1.128914859086766` / `-1.4025982192186477`
- Relative component: `-0.2400778154911137`
- Compression score: `82.53968253968253`
- 3/7/14/30 bar forward relative return: `-0.0114950184810443` / `-0.0302449821033602` / `-0.0278451568287534` / `-0.1356906134004208`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/28_MEW_20260323_0000.png`
