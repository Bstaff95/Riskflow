# Riskflow Grammar Search Grids

These YAML files are research grids for `python3 -m riskflow grammar-search`.
They are hypothesis generators only. They do not change `core_signal_v0`,
production states, scores, rankings, or TradingView defaults.

Use `--strict-referee` for comparable evidence:

```bash
PYTHONPATH=src python3 -m riskflow grammar-search \
  --config configs/meme_universe.yaml \
  --timeframes 1d 12h 4h 1h \
  --grid research/grammar/<grid>.yaml \
  --report-dir reports/<run_name> \
  --min-sample-size 20 \
  --strict-referee \
  --strict-null-iterations 300
```

## Grid Lineage

- `rule_search_grid.yaml`: original broad grammar-search grid.
- `rule_search_grid_v2_candidate.yaml`: bullish repair/reclaim follow-up; no durable support.
- `rule_search_grid_v3_warning_candidate.yaml`: amplitude reset warnings; useful but not standalone after stricter baselines.
- `rule_search_grid_v4_failure_candidate.yaml`: broad failure-warning grid. Canonical strict CLI rerun found 25 strict survivors, dominated by lower-high rollover.
- `rule_search_grid_v5_warning_survivor_candidate.yaml`: focused v4 survivor grid; useful for fast reruns, but its narrow null pool is not proof.
- `rule_search_grid_v6_4h_lower_high_warning_candidate.yaml`: conservative `4h` lower-high fresh-data rerun spec.
- `rule_search_grid_v7_4h_lower_high_neighborhood_candidate.yaml`: wider `4h` lower-high neighborhood; confirms a narrower survivor island.
- `rule_search_grid_v8_lower_high_refined_generalization_candidate.yaml`: tests whether the refined `4h` shape generalizes; strict survivors stayed `4h` only.
- `rule_search_grid_v9_4h_lower_high_false_positive_filter_candidate.yaml`: sample-derived `4h` false-positive filter probe.
- `rule_search_grid_v10_4h_lower_high_filtered_rerun_candidate.yaml`: tiny filtered `4h` challenger for fresh-data reruns.
- `rule_search_grid_v11_1h_zero_rejection_neighborhood_candidate.yaml`: retests `1h` zero rejection; produced no strict survivors.
- `rule_search_grid_v12_higher_tf_lower_high_refinement_candidate.yaml`: higher-timeframe lower-high refinement; strict survivors were daily only.
- `rule_search_grid_v13_1d_lower_high_rerun_candidate.yaml`: tiny daily lower-high fresh-data rerun spec.
- `rule_search_grid_v14_1d_lower_high_viscosity_filter_candidate.yaml`: sample-derived daily viscosity-filter challenger.
- `rule_search_grid_v15_frozen_indicator_behavior_survivors.yaml`: frozen explicit detectors for the first-batch indicator-behavior strict survivors. Under a 1000-iteration null rerun, only daily relative failed breakout remained a strict survivor.
- `rule_search_grid_v16_all_component_strict_survivors.yaml`: frozen explicit detectors for the all-99 indicator-behavior strict survivors. Under a 1000-iteration null rerun, only daily relative failed breakout remained a strict survivor.
- `rule_search_grid_v17_relative_failed_breakout_filter_probe.yaml`: sample-derived false-positive filter probe for the daily relative failed breakout survivor. One filtered variant survived with fewer events and stronger median underperformance; treat as fresh-data validation material only.
- `rule_search_grid_v18_relative_failed_breakout_refinement_probe.yaml`: broader refinement probe for relative failed breakout. The robust refinement was compression >= 45 plus viscosity-cross-count >= 3, not the more aggressive high-signal/high-gradient filters.
- `rule_search_grid_v19_relative_failed_breakout_current_candidates.yaml`: compact baseline-versus-refined grid for lag/cooldown stress. Both candidates only survived at lag 1 and 30-bar cooldown, so promotion remains blocked pending fresh-data validation.

## Current Fresh-Data Rerun Set

After OHLCV refresh, rerun these under the same strict referee:

- Conservative `4h`: `rule_search_grid_v6_4h_lower_high_warning_candidate.yaml`
- Filtered `4h`: `rule_search_grid_v10_4h_lower_high_filtered_rerun_candidate.yaml`
- Broad daily: `rule_search_grid_v13_1d_lower_high_rerun_candidate.yaml`
- Filtered daily: `rule_search_grid_v14_1d_lower_high_viscosity_filter_candidate.yaml`
- Frozen indicator behavior survivors: `rule_search_grid_v15_frozen_indicator_behavior_survivors.yaml`
- Frozen all-99 indicator behavior survivors: `rule_search_grid_v16_all_component_strict_survivors.yaml`
- Relative failed breakout filter probe: `rule_search_grid_v17_relative_failed_breakout_filter_probe.yaml`
- Relative failed breakout refinement probe: `rule_search_grid_v18_relative_failed_breakout_refinement_probe.yaml`
- Current relative failed breakout candidates: `rule_search_grid_v19_relative_failed_breakout_current_candidates.yaml`

Compare the resulting `grammar_search_strict_referee.csv` files against the
stale-sample references in `reports/grammar_search/learning_loop/autonomous_loop_end_report.md`.

## Review Packets

- Daily lower-high atlas: `reports/grammar_search/visual_review_v13_1d_lower_high_atlas/human_review_packet.md`
- Filtered daily lower-high atlas: `reports/grammar_search/visual_review_v14_1d_lower_high_viscosity_filter_atlas/human_review_packet.md`
- `4h` lower-high false-positive atlas: `reports/grammar_search/visual_review_v8_4h_lower_high_false_positive_atlas/human_review_packet.md`
- Cluster-consistent warnings: `reports/grammar_search/visual_review_cluster_consistent_warnings/human_review_packet.md`
