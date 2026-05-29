# Riskflow Signal Grammar Lab

This document defines the next research layer for learning what the Riskflow oscillator is actually saying before changing the core formula.

The goal is to turn human chart intuition into named, testable grammar.

## Why This Exists

The base Riskflow oscillator is already useful because it is not just a bounded momentum line. It combines price strength, relative strength, adaptive viscosity, gradient pressure, and key normalized zones. That makes it unusually readable with technical analysis:

- trendline breaks
- wedges and coils
- level reclaims
- viscosity retests
- divergences
- color or gradient weakening
- time above or below viscosity
- failed weakness in deep negative zones

The pressure-wave experiment showed that there may be another useful layer hidden inside the signal and viscosity relationship. It also showed the danger: a visually attractive layer can become lagging, redundant, or falsely constructive.

The lab exists to prevent that. Riskflow should discover the underlying grammar first, then decide the best visual expression later.

For the current autonomous operating model, use `docs/LAB_LOOP.md`. This file
defines the grammar research thesis; `docs/LAB_LOOP.md` defines the repeatable
queue, validation, promotion, and agent-checkpoint loop used to run it.

## North Star

Riskflow should eventually feel like a universal adaptive relative chart engine:

> Pick an asset, pick a benchmark or basket, and quickly see whether this is a good place for capital compared with the alternatives.

The long-term product should hide most manual presets behind an adaptive default. A user should not need to know whether they need meme weights, equity weights, or pure relative weights before the indicator becomes useful.

That does not mean weights disappear mathematically. It means preset choice becomes an internal model-selection or adaptive-weighting problem that must beat fixed baselines before becoming the default.

## Current Policy

- Keep `core_signal_v0` and the current Pine-style oscillator frozen as the trusted reference.
- Do not tune z-score length, viscosity behavior, gradient sensitivity, or component weights until the grammar has enough evidence.
- Treat pressure waves as an experimental candidate family, not the mission.
- Treat Obsidian as the synthesis layer and structured records as the evidence layer.
- Promote no visual layer, formula change, or score change without Layer 7-style evidence.

## Current State

Initial human-reviewed grammar is now sufficient to begin implementation of research sidecars.

The project should not keep collecting random bullish examples as the blocking path. Missing, bearish, and noisy cases are still useful calibration backfill, but the active sprint is to translate the recurring visual reads into measurable candidate features and events.

The next implementation should focus on:

- pressure acceptance around viscosity
- failed weakness in deep negative zones
- key-zone reclaim and retest behavior
- oscillator structure proxies
- divergence candidates
- curvature and acceleration intent
- clean chop versus noisy chop
- reset quality after overheated moves

These are research candidates only. They should not alter production scan rankings, state labels, scores, or the base TradingView indicator until evidence supports promotion.

The automated search layer now lives outside the stable sidecar. `signal_grammar_sidecar_v0` remains the hand-authored feature contract, while `grammar-search` expands structured rule families from `research/grammar/rule_search_grid.yaml` into temporary research variants.
The grid lineage and current fresh-data rerun set are summarized in `research/grammar/README.md`.

The first automated passes showed stronger evidence for warning grammar than bullish entry grammar. In particular, `hot_leader_reset` and `chaotic_chop_warning` on lower timeframes deserve chart review before any visual or scoring promotion. Second-generation bullish repair hypotheses live in `research/grammar/rule_search_grid_v2_candidate.yaml`; they test whether failed weakness, hot reset, or chaotic chop become useful after a later reclaim. Treat them as candidate discovery only unless they survive time-split validation and chart review.

The current strongest automated warning candidates are in `research/grammar/rule_search_grid_v4_failure_candidate.yaml` and the focused survivor grid `research/grammar/rule_search_grid_v5_warning_survivor_candidate.yaml`. They test `zero_rejection_warning`, `failed_strength_acceptance`, and `lower_high_rollover`. The highest-priority chart review set is `reports/grammar_search/visual_review_cluster_consistent_warnings/human_review_packet.md`, backed by `reports/grammar_search/visual_review_cluster_consistent_warnings/human_review_labels.csv` and `reports/grammar_search/visual_review_cluster_consistent_warnings/gallery.md`. It samples variants that survived time-split validation, both baseline checks, matched random-null testing, and event-cluster holdout checks. Treat this as a review queue, not a promotion decision, because some lower-timeframe cases still cover only a small number of calendar clusters. The canonical v3 amplitude-reset strict rerun produced zero strict survivors. The canonical v4 strict CLI run produced 25 strict survivors: 24 `lower_high_rollover` rows across `1d`, `12h`, and `4h`, plus one `1d` zero-rejection row. This upgrades lower-high rollover from a single `4h` idea into the main warning-grammar family to refine. The v11 `1h` zero-rejection neighborhood found 120 useful/time-split-supported rows but zero strict survivors, so keep `1h` zero rejection as review-only unless fresh data or a better independent filter restores strict evidence.

The later all-component indicator-behavior work encoded 99 concepts into
Riskflow-native measurable events. The broad result was asymmetric: useful
evidence appeared mainly in warning/avoidance grammar, not bullish single-event
entry grammar. The main current survivor is daily relative failed breakout, but
it remains a warning candidate rather than production logic because stress
testing showed entry-lag and cooldown sensitivity. Future bullish research
should therefore test staged setup journeys instead of isolated events:
weakness or compression, repair, reclaim, retest/hold, then continuation.

For fresh-data reruns, use `research/grammar/rule_search_grid_v6_4h_lower_high_warning_candidate.yaml` as the conservative `4h` lower-high rollover candidate spec. Do not use the v6 self-null result as proof by itself; the v6 pool is intentionally narrow, so broader v4/v5 baselines remain the evidence source. The wider v7 neighborhood grid in `research/grammar/rule_search_grid_v7_4h_lower_high_neighborhood_candidate.yaml` confirms a narrower `4h` survivor island: 39 of 1,066 time-split-supported variants also beat unconditional, same-cluster, and matched-random-null checks. The stable `4h` constraints are below-viscosity, `recent_window=5`, and non-negative relative-slope allowance; `lookback=34`, `recent_window=3`, and strict negative relative-slope variants did not survive the stricter ladder. The refined v8 all-timeframe generalization grid in `research/grammar/rule_search_grid_v8_lower_high_refined_generalization_candidate.yaml` did not broaden this specific `4h` shape after strict checks; only `4h` kept strict survivors. The v9 false-positive-filter grid in `research/grammar/rule_search_grid_v9_4h_lower_high_false_positive_filter_candidate.yaml` improves `4h` strict-survivor quality with pressure-gap and pressure-distance filters, and `research/grammar/rule_search_grid_v10_4h_lower_high_filtered_rerun_candidate.yaml` packages that filtered shape as a tiny fresh-data hypothesis. On the current stale local sample, strict CLI comparison produced 4 v6 strict survivors versus 9 v10 strict survivors, all on `4h`; v10 had stronger median terminal relative return, but because v9/v10 came from current-sample failures, treat them as challenger specs rather than the default.

The higher-timeframe lower-high branch is now separate. The v12 refinement grid in `research/grammar/rule_search_grid_v12_higher_tf_lower_high_refinement_candidate.yaml` found 45 strict survivors, all on `1d`, with no `12h` survivors. The stable daily shape is `recent_window=8`, `min_lower_high_gap=0.50`, no below-viscosity requirement, and max relative slope of `0.0` or `0.05`. The tiny fresh-data rerun spec is `research/grammar/rule_search_grid_v13_1d_lower_high_rerun_candidate.yaml`; on stale data it produced 17 strict survivors out of 18 rows, median terminal relative return -0.205978, median matched-null p 0.013333, and median 26 event clusters. Entry-lag sensitivity matters: v13 had zero strict survivors at lag 0, 17 at lag 1, and 16 at lag 2, so interpret it as a next-bar/follow-through warning rather than a same-close warning. Cooldown sensitivity is a caution: v13 had 11 strict survivors at 15-day cooldown, 17 at 30-day cooldown, and zero at 60-day cooldown, so repeated warning clusters may matter. The v13 review packet is `reports/grammar_search/visual_review_v13_1d_lower_high_atlas/human_review_packet.md`. A sample-derived v14 viscosity-filter challenger in `research/grammar/rule_search_grid_v14_1d_lower_high_viscosity_filter_candidate.yaml` improved median terminal return to -0.224578 and median null edge to 0.066679, but reduced median event clusters to 20. V14 also failed lag 0 and strengthened at lag 2, reinforcing that the daily branch is follow-through warning grammar. Unlike v13, v14 retained 17 strict survivors at 60-day cooldown, so the viscosity filter may reduce cluster dependence. The v14 review packet is `reports/grammar_search/visual_review_v14_1d_lower_high_viscosity_filter_atlas/human_review_packet.md`. Treat v14 as a filtered challenger rather than the broader default.

## Research Objects

### Observations

An observation is a human-reviewed chart case. It should record:

- symbol
- timeframe
- date window
- benchmark
- risk mode
- setup type
- visual tags
- outcome label
- user interpretation
- Codex interpretation
- possible measurable feature

Observations belong in `research/observations/` and the connected Obsidian wiki.

### Grammar Primitives

A primitive is one small visual or mathematical idea, such as:

- `viscosity_reclaim`
- `time_above_viscosity`
- `failed_weakness`
- `zero_rejection`
- `gradient_divergence`
- `oscillator_trendline_break`
- `pressure_area_balance`

A primitive is not a strategy. It is a word in the oscillator's language.

### Composite Events

A composite event combines primitives into a setup hypothesis, such as:

- `deep_compression_reclaim`
- `failed_breakout_reset_reclaim`
- `low_zone_weakness_exhaustion`
- `viscosity_acceptance_zero_confirmed`
- `gradient_divergence_after_pump`

Composite events must be tested against forward relative returns before affecting scores, labels, or TradingView visuals.

### Candidate Visual Layers

A visual candidate is a user-facing expression of tested grammar. Current candidates include:

- pressure waves
- fast/slow pressure fill
- subtle setup markers
- pressure-quality ribbon
- level-reclaim badges
- background acceptance zones

The final indicator should probably support only one additional intelligence layer by default. If it needs many overlays to work, the product is not simple enough yet.

## First Candidate Families

The first lab should focus on these families:

1. `pressure_acceptance`
   - Time and area above or below viscosity.
   - Tests whether sustained pressure matters more than one crossover.

2. `failed_weakness`
   - Deep negative signal that stops making lower lows or fails to expand lower.
   - Tests whether relative weakness exhaustion is an early reversal clue.

3. `zone_reclaim_retest`
   - Reclaims and retests of `-2`, `-1.5`, `0`, `1.5`, and `2`.
   - Tests whether normalized levels behave like support and resistance.

4. `oscillator_structure`
   - Trendline breaks, wedges, channels, and tight coils on the oscillator itself.
   - Tests whether oscillator TA adds earlier information than simple thresholds.

5. `divergence_quality`
   - Bullish and bearish divergences between price and oscillator, plus gradient/color divergence.
   - Tests whether the oscillator warns when price moves are losing force.

6. `curvature_intent`
   - Slope, acceleration, curvature, and fast/slow derivative turns.
   - Tests whether the indicator's "turning" can be measured before zero-line confirmation.

7. `adaptive_universal_weighting`
   - Future candidate that adapts component weights from data quality, volatility, benchmark role, and component information.
   - This is not a near-term formula change.

## Example Labeling Targets

The initial observation library was created to support these targets:

- 15 clean bullish hits
- 10 bullish false positives
- 10 missed breakouts
- 10 bearish or weakness examples
- 5 noisy or ambiguous edge cases

Include both `4h` and `1d`. Avoid clustering every case in the same market window.

These targets remain useful for calibration, but they are no longer a reason to delay the first Grammar Candidate Sprint. Treat additional examples as backfill for weak or ambiguous candidates.

## Promotion Gates

A grammar primitive or visual candidate can become product-facing only if it:

- is explainable in one sentence
- appears across multiple symbols and date clusters
- improves median 14- or 30-bar forward relative returns
- improves or preserves hit rate
- does not materially worsen drawdown
- avoids one-symbol and one-cluster concentration
- improves false-positive handling, not only clean winners
- remains readable on a phone screenshot
- does not require per-asset hand tuning

Default interpretation:

- one beautiful chart = anecdote
- repeated reviewed examples = hypothesis
- forward relative-return evidence = candidate
- cross-universe evidence = product material

## Near-Term Workflow

1. Keep using TradingView screenshots as the frontend truth reference.
2. Save each reviewed case into the observation library.
3. Tag each case with grammar primitives.
4. Convert recurring tags into measurable features.
5. Run `python3 -m riskflow grammar-search --timeframes 1d 12h 4h 1h` to brute-force structured candidate families.
6. Review `reports/grammar_search/grammar_search_ranked.csv` and `obsidian/reports/latest_grammar_search.md`.
7. Check `reports/grammar_search/grammar_search_time_split_validation.csv` before trusting a ranked variant.
8. Compare candidates against same-timeframe and same-cluster baselines, then matched random-null samples when enough variants survive. Prefer `grammar-search --strict-referee` for repeatable baseline/null checks.
9. Use `reports/grammar_search/grammar_search_chart_review_queue.csv`, generated galleries, and any `human_review_packet.md` / `human_review_labels.csv` files to review the best hits, false positives, missed winners, and boundary cases.
10. Only then decide whether the user-facing layer should be waves, markers, ribbons, or something else.

The search command is a hypothesis generator, not a promotion engine. A high-ranked variant still needs baseline comparison, concentration checks, and visual review before it can become a registered event, score input, or TradingView visual layer.

## Cross-Market Generalization

Memes are the discovery sandbox, not the final proof.

After a primitive looks useful on memes, validate it on:

- crypto majors and large-cap alts
- alt sectors or narratives
- equities versus SPY/QQQ or sector baskets

The final product should not be overfit to twenty speculative meme coins.
