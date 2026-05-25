# Layer 3: Adversarial Signal Research

This document captures the current Layer 3 research direction.

Layer 3 is Riskflow's signal engine layer. It should measure normalized strength, but it should not pretend to be a prediction oracle.

The working decision is:

> Keep the Pine-style oscillator as the incumbent signal, then test a small set of challenger signals against forward relative-return evidence before promoting anything.

## Research Thesis

The universal normalized framework is defensible as a measurement system.

It is not defensible as predictive truth until tested.

Riskflow should preserve the current Pine-style oscillator feel:

- centered around `0`
- familiar zones around `+2`, `+1.5`, `0`, `-1.5`, and `-2`
- useful as an RSI-like chart-reading tool
- driven by transparent normalized components

The research layer should not turn the main indicator into a cluttered signal museum. Challenger signals are research observations until they earn a role.

## Sources And Cautions

Supporting evidence:

- Time-series momentum: Moskowitz, Ooi, and Pedersen document momentum across futures asset classes.
- Cross-sectional momentum: Jegadeesh and Titman document relative strength effects in equities.
- Adaptive baselines: KAMA-style efficiency-ratio smoothing supports the current viscosity concept.

Adversarial evidence:

- Momentum can crash, especially around sharp rebounds after panic regimes.
- Volatility scaling has mixed out-of-sample evidence and can be structurally unstable.
- Technical rules are vulnerable to data-snooping bias.
- Large factor searches require higher evidence thresholds.
- Z-scores and percentiles can mislead in heavy-tailed, nonstationary markets.

Practical conclusion:

- Use normalized signals as observations.
- Test them against simple baselines.
- Promote nothing without robust forward relative-return evidence.

## Incumbent Signal

The current Pine-style `final_signal` remains the incumbent.

In research outputs it is called:

```text
core_signal_v0
```

It represents:

```text
price_component + relative_component + active-weight-scaled fusion
```

Do not replace `calculate_indicator` during this research phase.

The implementation keeps a formal signal registry in `src/riskflow/signal_registry.py`.

Current frozen core identity:

```text
signal_id: core_signal_v0
formula_version: riskflow_core_signal_v0_2026_05_24
scale: oscillator_z_like
neutral: 0
important user-facing zones: -2, -1.5, 0, +1.5, +2
```

Future formula changes must become a new side-by-side version first, such as:

```text
core_signal_v1_candidate
core_signal_v1
```

Do not silently change what `core_signal_v0` means.

## Challenger Signals

Only three challenger families are included in the first research sprint.

### Relative Vol-Adjusted Momentum

Formula:

```text
relative_ratio = target_norm / benchmark_norm
relative_log_return_k = log(relative_ratio / relative_ratio.shift(k))
relative_realized_vol = rolling_std(log(relative_ratio).diff(), k)
relative_vol_adj_momentum = relative_log_return_k / relative_realized_vol
```

Purpose:

> Is the asset outperforming its benchmark by an unusual amount relative to recent relative volatility?

### Relative Percentile Strength

Formula:

```text
relative_percentile_strength = percentile_rank(relative_log, lookback)
```

Purpose:

> Is the asset-versus-benchmark relationship high or low versus its own history?

### Cross-Sectional Relative Rank

Formula:

```text
cross_sectional_relative_rank = percentile rank of relative_log_return_k across assets on the same date
```

Purpose:

> Is this asset leading its current peer universe right now?

## Initial Variants

Use only the first small challenger set:

```text
core_signal_v0
relative_vol_adj_momentum_20
relative_vol_adj_momentum_50
relative_percentile_strength_50
relative_percentile_strength_100
cross_sectional_relative_rank_20
cross_sectional_relative_rank_50
```

Skip larger parameter grids until the small loop proves useful.

## Required Baselines

Every challenger should be compared against:

- `core_signal_v0`
- raw relative return
- simple relative momentum rank
- asset/benchmark ratio trend
- buy-and-hold relative benchmark

A fancy signal that cannot beat simple relative return should not be promoted.

## Evidence Gates

A challenger can be promoted only if it:

- improves median `14` or `30` bar forward relative return versus baseline
- improves or preserves hit rate
- does not depend on one symbol or one event cluster
- works across at least two nearby lookbacks
- has acceptable drawdown for its forward return
- can be explained in one sentence
- does not require per-asset weights
- survives rerun after Layer 2 ex-target baskets exist

The code enforces first-pass guardrails:

- same symbol/variant events use a default `30` bar cooldown
- forward returns start after a default `1` bar entry lag
- summary rows report unique symbols, unique event dates, unique event clusters, max symbol share, and max cluster share
- concentrated results are marked `inconclusive`
- challengers must beat both `core_signal_v0` and their matching simple baseline before being classified as `supporting_feature`

`supporting_feature` does not mean production promotion. It means the feature deserves more review.

Classifications:

- `core`: the incumbent Pine-style signal
- `supporting_feature`: useful context, but not enough as a standalone core signal
- `experimental`: interesting, still under review
- `inconclusive`: sample or stability is insufficient
- `rejected`: noisy, redundant, or fragile

Default interpretation:

- Small sample means `inconclusive`, not good.
- One massive winner does not count as robust evidence.
- Better average but worse median is suspicious.

## Research Output Shape

The research event-study table should be tidy:

```text
symbol
date
timeframe
benchmark
signal_variant
lookback
signal_value
event_name
forward_relative_return_3
forward_relative_return_7
forward_relative_return_14
forward_relative_return_30
max_drawdown_14
max_drawdown_30
```

The summary should classify every variant with the evidence gates above.

Initial event triggers are intentionally simple:

- `core_signal_v0`: crosses above `0`
- `relative_vol_adj_momentum`: crosses above `1.0`
- percentile and cross-sectional rank signals: cross above `70`
- raw relative-return and ratio-trend baselines: cross above `0`

These are not optimized thresholds. They are first-pass leadership triggers that keep the research loop small.

## Promotion Policy

No Layer 3 challenger can affect the leaderboard, states, opportunity score, or TradingView indicator until it is promoted in a documented version change.

A promotion note must explain:

- what changed
- why it changed
- what improved
- what got worse
- which downstream modules are affected
- how TradingView interpretation changes
- whether the old signal remains available for comparison

## Product Modes

Layer 3 should support future product modes without mixing them together:

- Leader Mode: find relative leaders and leadership chains.
- Trader Mode: find tradable compressed setups with timing evidence.
- Research Mode: test signals and event outcomes.
- Indicator Mode: keep the user-facing oscillator clean and readable.

Research Mode can be complex. Indicator Mode should stay simple.

## What To Defer

Do not build yet:

- robust MAD z-score as a default
- large parameter sweeps
- risk environment fusion
- multi-timeframe signal voting
- final universal one-indicator redesign
- machine learning
- per-sector weights
- cross-asset gold/stocks testing

These may be valuable, but they belong after the small challenger set proves the research loop is useful.

## First Question To Answer

> Does any simple relative challenger outperform the current Pine-style signal at predicting forward relative returns versus the meme basket?

If not, keep the Pine engine and focus on improving Layer 2 benchmarks and Layer 4 compression/setup quality.
