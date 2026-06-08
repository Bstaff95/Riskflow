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
- `rule_search_grid_v126_sidecar_reset_events_current.yaml`: compact direct-event grid for the registered reset sidecars: unstable reset warning, broad hot-leader reset warning, and constructive reset watch. It uses the `signal_grammar_event` detector so sidecar events can run through grammar-search strict referee and champion/challenger evidence paths.
- `rule_search_grid_v127_sidecar_reset_attribution_controls.yaml`: attribution-control grid for registered reset sidecars. It uses `signal_grammar_event_combo` to test broad hot-leader reset warnings with unstable-reset rows removed, unstable-overlap controls, and constructive reset watches with unstable-warning rows removed.

Build review packets from any grammar-search queue or variant-record CSV with:

```bash
PYTHONPATH=src python3 -m riskflow grammar-review-packet \
  --queue-csv reports/<run>/grammar_search_variant_records.csv \
  --output-dir reports/<run>/visual_review_packet_all_records \
  --title "Grammar Review Packet"
```

Render chart images for a review packet with:

```bash
PYTHONPATH=src python3 -m riskflow grammar-review-gallery \
  --labels-csv reports/<run>/visual_review_packet_all_records/human_review_labels.csv \
  --output-dir reports/<run>/visual_review_packet_all_records
```

## Current Reset-Sidecar Attribution Result

The strict v127 run in `reports/indicator_evidence_sprint/sidecar_reset_v127_attribution_controls/` produced no strict survivors. It still improved the reset-warning interpretation:

- `hot_reset_without_unstable_control` remained useful on `1d` and `4h`, with 71 daily events across 18 symbols and 26 clusters and 49 `4h` events across 19 symbols and 3 clusters.
- `sidecar_unstable_reset_warning_current` and `hot_reset_unstable_overlap_control` were identical in the current sample, confirming that the unstable reset event is a subset of the broad hot-leader reset event.
- The broad-minus-unstable daily control passed both median baselines but failed matched-null support (`matched_null_p_value=0.556667`), so it is evidence for shadow review, not product promotion.
- `constructive_reset_without_unstable_control` stayed fragile or inconclusive and had negative secondary forward-relative medians despite positive direction. Treat constructive reset as misclassification-prone until visual labels explain the failure mode.
- The generated all-record review packet is `reports/indicator_evidence_sprint/sidecar_reset_v127_attribution_controls/visual_review_packet_all_records/human_review_packet.md`, with labels in `human_review_labels.csv`. It prioritizes constructive-reset misclassification, missed-upside/false-warning cases, avoided-downside examples, and unstable-overlap controls ahead of unknown-outcome tail rows.
- The generated chart gallery is `reports/indicator_evidence_sprint/sidecar_reset_v127_attribution_controls/visual_review_packet_all_records/gallery.md`, with 60 rendered images and an image-backed `human_review_labels_with_images.csv`.
- The CEO sidecar packet now derives a candidate-matched human-label checklist at `reports/ceo_runs/ceo_indicator_evidence_sprint_v127_shadow/sidecar_visual_label_worklist.csv` / `.md`, bounded review batches at `sidecar_visual_label_review_batches.csv` / `.md`, candidate progress at `sidecar_visual_label_progress.csv` / `.md`, the current worksheet at `sidecar_visual_label_next_batch.csv` / `.md`, the review-only label rubric at `sidecar_visual_label_rubric.yaml` / `.md`, and the completion audit at `sidecar_visual_label_completion_audit.csv` / `.yaml` / `.md`; use them to complete required labels without treating visual review as validation.
- Lag sensitivity changed the reset-warning evidence. The v127 lag-0 control produced one strict survivor: `hot_reset_without_unstable_control` on `4h` with 49 events, 19 symbols, 3 clusters, median terminal relative return -0.085585, and matched-null p-value 0.026667. The lag-2 control produced one strict survivor: `sidecar_hot_leader_reset_warning_current` on `1d` with 86 events, 19 symbols, 27 clusters, median terminal relative return -0.189331, and matched-null p-value 0.023333. The default lag-1 control had zero strict survivors. Treat this as lag-sensitive shadow warning evidence requiring visual labels and fresh/control validation, not promotion.
- Cooldown sensitivity keeps the lag-2 daily survivor in shadow mode. At lag 2, the daily `sidecar_hot_leader_reset_warning_current` survivor appears at 30-day cooldown only; 15-day and 60-day cooldown reruns both produced zero strict survivors. Keep this as a review candidate, not validated warning logic.
- A standalone CEO shadow comparison packet for the v127 sprint is in `reports/ceo_runs/ceo_indicator_evidence_sprint_v127_shadow/`. It compares three shadow challengers against `core_signal_v0`, marks all three as `needs_fresh_or_control_validation`, writes a ready visual-review queue, and writes a fresh/control validation plan. The packet does not resume the old stopped CEO run and has production effect `none`.
- Fresh-data preflight for `ceo_indicator_evidence_sprint_v127_shadow` is `not_ready`: all 20 assets are stale across `1d`, `12h`, `4h`, and `1h`, with the local sample ending around 2026-05-24. Fresh/control validation is blocked until OHLCV is refreshed or a withheld snapshot is explicitly declared.
- Resumption brief for `ceo_indicator_evidence_sprint_v127_shadow` is `blocked_preflight`; trace grade recommends `stop_for_manual_data_import`, and the preflight gate blocks frozen validation. Do not execute further validation on that shadow run until the data import or explicit snapshot authority issue is resolved.

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
- Current reset sidecar events: `rule_search_grid_v126_sidecar_reset_events_current.yaml`
- Reset sidecar attribution controls: `rule_search_grid_v127_sidecar_reset_attribution_controls.yaml`

Compare the resulting `grammar_search_strict_referee.csv` files against the
stale-sample references in `reports/grammar_search/learning_loop/autonomous_loop_end_report.md`.

## Review Packets

- Daily lower-high atlas: `reports/grammar_search/visual_review_v13_1d_lower_high_atlas/human_review_packet.md`
- Filtered daily lower-high atlas: `reports/grammar_search/visual_review_v14_1d_lower_high_viscosity_filter_atlas/human_review_packet.md`
- `4h` lower-high false-positive atlas: `reports/grammar_search/visual_review_v8_4h_lower_high_false_positive_atlas/human_review_packet.md`
- Cluster-consistent warnings: `reports/grammar_search/visual_review_cluster_consistent_warnings/human_review_packet.md`
