# Layer 6: Opportunity Score Validation And Hardening

Layer 6 is Riskflow's ranking validation layer.

Layer 3 asks:

```text
Is this asset gaining normalized strength versus its benchmark?
```

Layer 4 asks:

```text
Is this strengthening asset actually a good setup right now?
```

Layer 5 asks:

```text
What lifecycle state is this asset in?
```

Layer 6 asks:

```text
Do high-ranked assets actually deserve attention?
```

## Core Principle

Scores are attention priorities, not probabilities.

An `opportunity_score` of `85` does not mean there is an 85% chance of success. It means the current rule set thinks this asset deserves more attention than lower-scored assets. Layer 6 exists to test whether that attention ordering has evidence behind it.

Ranking quality matters more than decimal precision. The useful question is not whether a score should be `81.3` or `82.1`. The useful question is whether top-score buckets historically outperform lower-score buckets on forward relative returns without unacceptable drawdown or concentration risk.

## Layer Ownership

Layer 6 owns:

- score registry contracts
- ranking validation
- attention tier research
- score promotion policy
- bucket behavior
- rank IC diagnostics
- concentration diagnostics

Layer 6 does not own:

- signal formulas
- compression math
- setup-quality features
- lifecycle-state labels
- TradingView oscillator behavior

Those are upstream layers. Layer 6 evaluates their outputs as ranking inputs.

## Active Score Contract

The active leaderboard score remains:

```text
opportunity_score_v0
```

The backward-compatible public column remains:

```text
opportunity_score
```

For now:

```text
opportunity_score = opportunity_score_v0
```

Do not silently change this mapping.

`trader_score_v0` remains experimental. It can be researched and reviewed, but it does not replace default leaderboard sorting.

Future scoring work should use a side-by-side candidate contract:

```text
opportunity_score_v1_candidate
```

That candidate is documented as a future contract only. It is not active logic in this layer.

## Score Registry

Score identities live in `src/riskflow/score_registry.py`.

Current research targets:

```text
opportunity_score_v0
trader_score_v0
leader_quality_score
compression_quality_score
relative_accumulation_score
setup_readiness_score
extension_risk_score
data_quality_score
```

`extension_risk_score` is inverted for ranking research because lower extension risk is better for attention. The raw score still remains available in scan outputs.

The registry is intentionally explicit. Unknown score ids should fail fast so research outputs do not accidentally mix untracked formulas.

## Score Research

Run Layer 6 research with:

```bash
python3 -m riskflow score-research --config configs/meme_universe.yaml --timeframe 1d
```

Default settings:

```text
bucket_count = 10
min_symbols_per_date = 5
min_bucket_sample_size = 20
entry_lag_bars = 1
```

If a date cannot form true deciles, Riskflow uses the largest valid bucket count for that date and records the fallback in the output notes. This matters for the current 20-coin meme universe because missing data can reduce the number of symbols available on a given date.

Outputs:

```text
reports/score_research_records.csv
reports/score_research_bucket_summary.csv
reports/score_research_ic_summary.csv
reports/score_research_score_summary.csv
reports/score_research_summary.html
obsidian/reports/latest_score_research.md
```

## Research Records

Each score observation records:

```text
symbol
date
timeframe
benchmark
score_id
score_value
date-wise rank percentile
date-wise bucket
entry lag
entry date
event cluster id
3/7/14/30 bar forward relative returns
14/30 bar max drawdowns
```

Forward relative return is the key target. A coin that rises less than the meme basket is not showing leadership even if the absolute chart went up.

## Summary Diagnostics

Layer 6 reports:

- bucket sample size
- unique symbols
- unique dates
- unique calendar clusters
- max symbol share
- max cluster share
- average and median forward relative returns
- hit rates
- max drawdown summaries
- top-minus-bottom bucket spread
- date-wise Spearman rank IC
- first-half versus second-half stability
- classification: `useful`, `watchlist`, `inconclusive`, or `fragile`

Default interpretation:

- low sample size means `inconclusive`
- good average but bad median is suspicious
- one symbol driving results is `fragile`
- one calendar cluster driving results is `fragile`
- positive top-minus-bottom spread is required for stronger evidence
- positive rank IC on enough dates is required before promoting a score

## Promotion Gates

A future `opportunity_score_v1_candidate` can challenge `opportunity_score_v0` only if it:

- improves top-bucket median 14 or 30 bar forward relative return
- improves or preserves hit rate
- produces positive top-minus-bottom bucket spread
- has positive mean and median rank IC
- has positive IC on at least 55% of valid dates
- avoids symbol concentration above 55%
- avoids calendar-cluster concentration above 60%
- does not materially worsen median 30-bar drawdown
- works in both first-half and second-half samples
- beats simple baselines such as `leader_quality_score`, `relative_accumulation_score`, and `trader_score_v0`
- remains explainable as score components, not optimized black-box weights

Promotion should come with a short note explaining:

- what changed
- why it changed
- which evidence improved
- what got worse
- whether the old score remains available
- downstream effects on leaderboard, reports, alerts, TradingView interpretation, and Obsidian language

## Downstream Guardrails

Do not use Layer 6 to quietly retune upstream formulas.

Changing `opportunity_score` can affect:

- default leaderboard order
- top opportunity reports
- future alerts
- user trust in Trader Mode
- event-study triggers
- Obsidian summaries
- future dashboard ranking
- future TradingView labels or markers

Because of that, score changes should always be versioned and researched side by side first.

## What Layer 6 Does Not Build Yet

Layer 6 does not build:

- machine learning
- learning-to-rank models
- optimized score weights
- probability calibration
- per-symbol tuning
- per-sector tuning
- multi-timeframe voting
- live alerts

Research backlog:

- `opportunity_score_v1_candidate` after enough score-research evidence exists.
- Attention tiers such as `elite`, `strong`, `watch`, `avoid`.
- Defensive or capital-protection scores after the meme MVP proves useful.
- Cross-timeframe rank stability after Layer 8 multi-timeframe context exists.

## Practical Success Criteria

Layer 6 is doing its job if:

- default leaderboard sorting remains stable
- every researched score has an explicit registry id
- top buckets can be compared against bottom buckets
- rank IC is reported date by date
- concentration risk is visible
- score research can reject attractive but unearned scoring ideas
- future score candidates must beat `opportunity_score_v0` before promotion
