---
observation_id: BONK_1d_20250411_0000_coil_viscosity_reclaim_v0
symbol: BONK
timeframe: 1d
date: 2025-04-11T00:00:00
pattern_label: coil_viscosity_reclaim_v0
review_status: needs_human_review
human_label: unreviewed
---

# BONK 1d 2025-04-11 00:00

Pattern: [[Coil Viscosity Reclaim v0]]

Concepts: [[False Positive]], [[Lower Band Accumulation]], [[Viscosity Reclaim]]

## Chart

![Chart](/Users/Shared/Riskflow/reports/visual_review/images/21_BONK_20250411_0000.png)

## Evidence

- Benchmark: `MEME_BASKET_EX_BONK`
- Final signal / viscosity: `-1.238626039919184` / `-1.641517197822175`
- Relative component: `-0.390748676175697`
- Compression score: `35.81349206349205`
- 3/7/14/30 bar forward relative return: `-0.039895226360031` / `-0.0518990086228929` / `-0.1407332092622177` / `-0.2782065013730563`
- Outcome label: `false_positive`

## Tags

`coil`, `compression`, `compression_observed`, `ex_target_benchmark`, `false_positive`, `human_review_needed`, `lower_gate`, `negative_chop_band`, `relative_component_observed`, `viscosity_reclaim`

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `reports/visual_review/events.csv`
- Image path: `reports/visual_review/images/21_BONK_20250411_0000.png`
