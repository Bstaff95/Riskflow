---
observation_id: SHIB_1d_20250510_0000_coil_viscosity_reclaim_v0
symbol: SHIB
timeframe: 1d
date: 2025-05-10T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# SHIB 1d 2025-05-10 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/30_SHIB_20250510_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_SHIB`
- Final signal / viscosity: `-1.1621465136999107` / `-1.4497503935018554`
- Relative component: `-2.261145761083591`
- Compression score: `60.01984126984127`
- 3/7/14/30 bar forward relative return: `-0.012888700560809` / `-0.0348437092816106` / `-0.115903757086361` / `-0.147517820337599`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/30_SHIB_20250510_0000.png`
