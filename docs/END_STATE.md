# Riskflow End-State Guide

This document is a living guide, not a fixed blueprint.

Riskflow's cathedral-scale goal is to become a probabilistic capital-flow research engine that finds compressed assets near the end of strengthening market rotation chains. The current shape of that idea is useful, but it should stay open to revision as evidence accumulates.

The purpose of this guide is to keep the long-term destination visible while preventing premature overbuilding.

## North Star

Riskflow should eventually answer:

> Where is capital flowing, which leadership chains are strengthening, which asset is the best expression of that flow, and is that asset still early enough to offer asymmetric upside?

The ideal future output is not simply:

> This chart is bullish.

It is closer to:

> This asset sits inside a strengthening parent chain, is improving versus its relevant benchmark, remains compressed versus its own history, is nearing or reclaiming trend, and similar historical setups had favorable forward relative-return outcomes.

## Working Thesis

The current thesis is:

> The best asymmetric opportunities are often compressed assets at the end of strengthening capital-flow chains.

This thesis should be tested, not assumed.

Riskflow should be built so each part can be falsified:

- Does relative strength versus a parent basket predict forward outperformance?
- Does compression improve the risk-adjusted opportunity set?
- Do lifecycle states transition in repeatable ways?
- Does parent-sector support increase the odds of an asset-level expansion?
- Do multi-timeframe alignments add useful signal, or just complexity?

## Layer Model

### Layer 0: Data Foundation

Clean OHLCV data by symbol and timeframe.

Current version:

- TradingView CSV exports
- `1d` and `1h` base files
- local resampling into `1w`, `3d`, `12h`, and `4h`

Future possibilities:

- exchange APIs
- Parquet or DuckDB storage
- data quality scoring
- corporate-action handling for equities
- macro and cross-asset data feeds

This layer must stay boring and trustworthy. Bad data makes every higher layer look smarter than it is.

### Layer 1: Universe And Hierarchy

Define what belongs to what.

Current version:

- meme universe
- symbol metadata
- sector and subgroup labels
- meme basket

Future possibilities:

- Crypto -> Memes -> Base Memes -> BRETT
- Stocks -> Semiconductors -> Memory -> MU
- Global Markets -> Asset Classes -> Sectors -> Subgroups -> Assets

Layer 1 should evolve into a tagged, graph-ready universe model rather than a rigid tree.

The important distinction is:

- asset identity: what the thing is
- data identity: where its candles came from
- memberships: which sectors, narratives, ecosystems, scans, and baskets it belongs to
- benchmark policy: what it should be compared against
- quality metadata: how trustworthy the data and labels are

A useful future asset shape may look like:

```yaml
assets:
  - symbol: BRETT
    name: Brett
    identity:
      asset_type: crypto
      sector: memes
      ecosystem: base
      tags: [base_memes, high_beta, risk_on]
    data:
      tradingview: BYBIT:BRETTUSDT
      preferred_timeframes: [1d, 1h]
    memberships:
      structural: [memes, base_ecosystem]
      tactical: [high_beta_memes]
      research: [meme_universe_v1]
    benchmark_policy:
      primary: base_meme_basket
      fallback: meme_basket
      exclude_self: true
    quality:
      liquidity_tier: mid
      label_confidence: medium
      feed_notes: "Prefer BYBIT feed."
```

This is where the future graph starts, but without probabilities yet. The key design choice is to avoid forcing every asset into one box. Assets can belong to multiple useful groups at the same time.

Open Layer 1 design questions:

- Which labels are structural versus tactical versus temporary research notes?
- Which memberships should be time-varying?
- How should we track label confidence and source/provenance?
- Should benchmark policy live on the asset, the group, the scan, or all three with clear override rules?
- What minimum metadata is required before an asset is allowed into a leaderboard?

### Layer 2: Baskets And Relative Benchmarks

Define what each asset should be judged against.

Current version:

- equal-weight meme basket
- coin versus meme basket

Next likely improvements:

- ex-target baskets, where a coin is compared to a basket excluding itself
- subgroup baskets
- sector baskets
- broad crypto basket

The target direction is a benchmark engine that builds and validates baskets, excludes the target asset when appropriate, supports fallback policies, labels benchmark purpose, measures breadth/concentration, treats baskets as synthetic assets, and explains why each comparison was chosen.

Layer 2 should also keep state/tag language disciplined:

- one primary lifecycle state
- a small controlled list of secondary tags
- benchmark confidence
- benchmark audit notes
- raw observations separated from interpretations

See `docs/LAYER_2_BENCHMARKS_AND_TAGS.md` for the working Layer 2 design.

This layer protects the system from confusing absolute gains with leadership.

### Layer 3: Signal Engine

Measure normalized strength.

Current version:

- Pine-inspired price component
- asset-versus-benchmark relative component
- optional risk placeholder
- rolling z-score normalization
- component clamp
- root-sum-square weight-scaled fusion
- viscosity baseline
- gradient driver

Future work should tighten Pine-to-Python parity only where it improves research validity. Exact visual parity is less important than stable, testable behavior.

### Layer 4: Compression And Setup Quality

Separate leader quality from entry quality.

Current version:

- ATR percent
- rolling range percent
- realized volatility
- feature percentiles versus each asset's own history
- compression score where higher means more compressed

This layer is central. Riskflow should avoid only ranking what is already obvious and extended.

### Layer 5: Lifecycle States

Convert features into explainable market language.

Current examples:

- Unknown
- Weak
- Compression
- Relative Accumulation
- Emerging Leader
- Confirmed Leader
- Overheated
- Distribution
- Breakdown

These states are not truth yet. They are hypotheses that should be validated with event studies and later transition analysis.

### Layer 6: Opportunity Scoring

Rank what deserves attention first.

Current idea:

- relative strength contribution
- compression contribution
- setup readiness
- viscosity or trend confirmation
- overextension penalty
- data quality penalty

The score should remain explainable. If a score cannot be decomposed into understandable parts, it is probably too clever for this phase.

Layer 6 should also validate ranking behavior. High scores should be treated as attention priorities, not probabilities. The score earns trust only if top buckets beat lower buckets on forward relative returns, hit rates, drawdown, and concentration diagnostics. Future score candidates should run side by side against `opportunity_score_v0` before any default leaderboard change.

### Layer 7: Event Studies

Test whether the signals matter.

Core question:

> Did this condition historically lead to forward outperformance versus the relevant basket?

Important metrics:

- forward absolute return
- forward relative return
- hit rate
- median outcome
- drawdown
- sample size

This layer is where attractive ideas either earn more development time or get demoted.

Layer 7 should act as the evidence engine for the whole project. It should standardize outcome math, event records, entry lag, cooldowns, concentration diagnostics, and promotion gates so future signal, setup, state, and score changes cannot be promoted by vibes or one lucky outlier.

### Layer 8: Multi-Timeframe Context

Add structure across timeframes only after the single-timeframe engine is understandable.

Possible roles:

- `1w`: regime
- `3d`: swing structure
- `1d`: tactical leadership
- `12h`: lower swing confirmation
- `4h`: timing and reset
- `1h`: source/detail layer

The open question is whether multi-timeframe logic improves decision quality enough to justify the added complexity.

### Layer 9: Capital-Flow Graph

Represent markets as nodes and relationships.

Nodes may include:

- asset classes
- sectors
- narratives
- subgroups
- individual assets

Edges may include:

- child versus parent relative strength
- sibling leadership
- sector rotation
- risk-on or risk-off relationships

This is the eventual map of where capital appears to be moving through the hierarchy.

### Layer 10: Probabilistic Transitions

Estimate state-transition probabilities only after states have been validated.

Potential questions:

- What usually happens after Compression?
- What usually happens after Relative Accumulation?
- Does Emerging Leader work better when parent sector support is strong?
- Does Breakdown matter more when the parent is weakening?

This is future work. Building it too early would give false precision.

### Layer 11: Historical Analog Search

Find prior setups that resemble the current one.

Possible matching features:

- parent-sector state
- asset state
- compression
- relative component
- signal slope
- drawdown profile
- multi-timeframe alignment

This layer turns the system into market memory, but it depends on the lower layers being stable.

### Layer 12: Product And Dashboard

Build the interface after the engine earns one.

Possible future views:

- opportunity leaderboard
- capital-flow map
- sector rotation map
- alerts
- Obsidian reports
- chart snapshots
- historical outcome summaries

A dashboard should not be used to make weak logic look complete.

## Reverse-Engineered Build Path

The current best build path is:

1. Make meme data reliable.
2. Make coin-versus-basket signals reliable.
3. Make compression, states, and scoring explainable.
4. Use event studies to learn what actually works.
5. Add multi-timeframe structure cautiously.
6. Add crypto sector hierarchy.
7. Add parent-child relative chains.
8. Validate lifecycle transitions.
9. Add probabilistic transition analysis.
10. Add historical analog search.
11. Build a visual/product layer.
12. Expand beyond crypto only after the architecture proves useful.

## Design Guardrails

- Treat every major idea as a hypothesis until tested.
- Prefer transparent calculations before advanced modeling.
- Do not add complexity unless it improves evidence, clarity, or extensibility.
- Separate leader quality from setup quality.
- Focus on forward relative returns, not only absolute returns.
- Keep data quality visible.
- Avoid giving probabilistic language to unvalidated rules.
- Let the meme MVP teach us before scaling to global markets.

## Open Design Questions

These are deliberately unresolved:

- Is the Pine-style signal the best core strength measure, or one of several features?
- Should compression be a gate, a score component, or a separate entry-quality model?
- Should lifecycle states be rule-based long term, probabilistic, or hybrid?
- How much does multi-timeframe logic improve outcomes versus adding noise?
- What is the right parent benchmark for each asset?
- Should opportunity score be one number or split into leader quality, setup quality, and asymmetry?
- What minimum evidence is required before adding Markov transitions?
- What would make us decide the thesis is wrong or incomplete?

This document should evolve as Riskflow produces real evidence.
