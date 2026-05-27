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

Before changing the core formula, collect at least:

- 15 clean bullish hits
- 10 bullish false positives
- 10 missed breakouts
- 10 bearish or weakness examples
- 5 noisy or ambiguous edge cases

Include both `4h` and `1d`. Avoid clustering every case in the same market window.

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
5. Test features with Layer 7 evidence.
6. Only then decide whether the user-facing layer should be waves, markers, ribbons, or something else.

## Cross-Market Generalization

Memes are the discovery sandbox, not the final proof.

After a primitive looks useful on memes, validate it on:

- crypto majors and large-cap alts
- alt sectors or narratives
- equities versus SPY/QQQ or sector baskets

The final product should not be overfit to twenty speculative meme coins.
