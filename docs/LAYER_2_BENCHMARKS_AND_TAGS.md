# Layer 2: Benchmarks, Relative Context, And Tags

This document captures the current Layer 2 design direction.

Layer 2 answers:

> What should each asset be compared against, how trustworthy is that comparison, and how should the result be described without creating a label jungle?

The goal is scalable infrastructure for future sectors and asset classes, while keeping the v1 meme workflow simple enough to build, read, and test.

## Core Principle

Riskflow should not confuse absolute performance with leadership.

A coin that rises 20% while its parent basket rises 40% is not leading. A coin that rises 5% while its peers fall may be showing early leadership.

Layer 2 exists to make those comparisons explicit, validated, and explainable.

## Practical V1 Build Targets

These are the concepts worth building first.

### 1. Ex-Target Baskets

Compare each asset against a basket that excludes itself when possible.

Example:

- less clean: `BRETT` versus `MEME_BASKET` including `BRETT`
- cleaner: `BRETT` versus `MEME_BASKET_EX_BRETT`

This is the highest-priority Layer 2 improvement because it makes peer outperformance cleaner.

### 2. Basket Viability Diagnostics

Every benchmark basket should report basic health.

Minimum useful diagnostics:

- active member count
- missing member count
- minimum-active-members pass/fail
- target excluded yes/no
- fallback used yes/no
- benchmark confidence

Future diagnostics:

- history length
- missing data percentage
- weight concentration
- largest member influence
- feed quality warnings
- survivorship-bias warnings

### 3. Benchmark Policy And Fallbacks

Riskflow should eventually support explicit benchmark policies.

Example:

```yaml
benchmark_policy:
  role: opportunity_cost
  primary: base_meme_basket
  fallback:
    - meme_basket
    - broad_crypto
  exclude_self: true
```

Fallbacks matter because small subgroups may not have enough active members. If the ideal benchmark is weak, Riskflow should choose the next best benchmark and explain why.

### 4. Basket Method Types

Equal-weight return baskets are the v1 default.

Future method types may include:

- equal-weight return
- liquidity-weight
- market-cap-weight
- volatility-adjusted
- inverse-volatility-weight
- custom-weight

Do not build all of these now. The important design point is that basket construction should have a named method so future research remains reproducible.

### 5. Basket-As-Asset Concept

Baskets should eventually become first-class synthetic assets.

Examples:

- `MEME_BASKET`
- `BASE_MEME_BASKET`
- `SOL_MEME_BASKET`
- `HIGH_BETA_MEME_BASKET`

This allows the same engine to analyze:

- `BRETT` versus `BASE_MEME_BASKET`
- `BASE_MEME_BASKET` versus `MEME_BASKET`
- `MEME_BASKET` versus broad crypto

This is essential for the eventual capital-flow chain.

## Benchmark Roles

Not every benchmark answers the same question.

Useful roles:

- `opportunity_cost`: is the asset outperforming its peer opportunity set?
- `sibling_leadership`: is the asset leading direct competitors?
- `sector_support`: is the parent sector or basket itself supportive?
- `broad_market_context`: is the broader asset class supportive?
- `risk_context`: is the broader risk environment supportive?

Reports should eventually show which role the selected benchmark served.

## Benchmark Confidence

Every relative signal should carry context about benchmark quality.

Initial confidence inputs:

- active member count
- missing member count
- target excluded yes/no
- fallback used yes/no
- sufficient history yes/no

Future confidence inputs:

- concentration risk
- shared data source problems
- label confidence
- survivorship-bias risk
- correlation/crowding

The point is not to make confidence perfect. The point is to avoid treating all relative signals as equally reliable.

## Audit Trail

Riskflow should explain why each comparison was chosen.

Example note:

> Compared against `MEME_BASKET_EX_BRETT`; Base meme basket was unavailable because it had only 2 active members.

The audit trail should be boring, plain, and useful. It is a trust feature.

## Breadth And Leadership Concentration

For baskets and sectors, Riskflow should eventually track whether leadership is broad or narrow.

Useful questions:

- How many basket members are above viscosity?
- How many have positive relative components?
- How many are improving?
- Is the basket rising because many members are participating, or because one name is carrying it?

These features help separate healthy sector rotation from narrow, fragile leadership.

## Regime And State Tags

Regime/state language should apply at multiple levels:

- assets
- baskets/sectors
- edges/relationships
- chains

Examples:

- asset state: `BRETT` is `Emerging Leader`
- basket regime: `MEME_BASKET` is in `healthy_expansion`
- edge state: `BRETT` versus `MEME_BASKET` is `relative_momentum_rising`
- chain state: `BRETT -> Base Memes -> Memes -> Crypto` is aligned

### Primary State

Use one primary lifecycle state per asset or basket.

Initial state vocabulary:

- Unknown
- Weak
- Compression
- Relative Accumulation
- Emerging Leader
- Confirmed Leader
- Overheated
- Distribution
- Breakdown
- Reset / Chop Needed

### Secondary Tags

Use a small controlled list. Limit display to a handful of tags per asset.

Initial practical tags:

- `compressed`
- `relative_improving`
- `relative_deteriorating`
- `above_viscosity`
- `reclaiming_viscosity`
- `overextended`
- `narrow_leadership`
- `low_confidence`
- `data_warning`
- `conflicting_signals`

Future tags can be added only when they have clear definitions and appear in reports or research tests.

### Basket Regime Tags

Possible basket/sector regimes:

- `healthy_expansion`
- `broad_accumulation`
- `narrow_leadership`
- `chop`
- `risk_off`
- `overheated`
- `breakdown`
- `low_confidence`

### Edge Tags

Possible relationship tags:

- `child_outperforming_parent`
- `child_underperforming_parent`
- `relative_momentum_rising`
- `relative_momentum_falling`
- `reclaiming_relative_zero`
- `losing_relative_trend`

## Tag Registry

Riskflow should eventually maintain a registry of allowed tags and definitions.

The registry should define:

- tag name
- where it applies: asset, basket, edge, or chain
- required observations
- plain-English definition
- version or last-reviewed date

This prevents tags from multiplying randomly and losing meaning.

## Observation Versus Interpretation

Riskflow should keep raw observations separate from interpretations.

Observations:

- final signal
- relative component
- compression score
- signal slope
- above viscosity
- basket breadth
- active member count

Interpretations:

- primary state
- secondary tags
- opportunity score
- benchmark confidence
- notes

This separation is non-negotiable architecturally. It allows Riskflow to change state rules later without corrupting the raw feature history.

## Ideas To Delay

These ideas are useful, but not needed for the first practical Layer 2 build:

- interpretation confidence
- maturity tags
- invalidation tags
- timeframe agreement score
- signal freshness
- crowding or obviousness proxy
- manual research workflow tags
- benchmark correlation awareness
- time-varying basket membership
- full survivorship-bias controls

They should stay on the radar, but building them now would likely make v1 harder to understand.

## Recommended Build Order

1. Add ex-target basket support.
2. Add basket viability diagnostics.
3. Add benchmark confidence and audit notes.
4. Add benchmark policy/fallback structure.
5. Add subgroup basket definitions only where member counts are viable.
6. Add basket-as-asset handling.
7. Add controlled secondary tags and a tag registry.
8. Add breadth and leadership concentration features.

## Minimal Practical Output Shape

For each leaderboard row, the target shape is:

```text
symbol
primary_state
secondary_tags
benchmark_used
benchmark_role
benchmark_confidence
exclude_self
fallback_used
relative_component
compression_score
opportunity_score
notes
```

This gives Riskflow enough structure to scale without making the v1 reports unreadable.
