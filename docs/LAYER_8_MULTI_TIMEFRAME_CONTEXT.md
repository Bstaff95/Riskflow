# Layer 8: Multi-Timeframe Context

Layer 8 adds optional multi-timeframe context. It does not add a new production score, prediction engine, or default leaderboard ranking rule.

The model id is:

```text
mtf_context_v0
```

## Purpose

Layer 8 answers:

> Does completed higher/lower timeframe structure support, contradict, or qualify the primary timeframe setup?

The primary timeframe, usually `1d`, still owns the scan event. Context timeframes describe the surrounding structure.

Default scan behavior stays unchanged. MTF columns appear only when explicitly requested with `--context-timeframes` or `--mtf-preset research-mtf`.

## Timeframe Roles

```text
1w  = regime
3d  = swing
1d  = primary / tactical
12h = confirmation
4h  = timing / reset
1h  = source / detail
```

The `research-mtf` preset uses:

```text
1w 3d 12h 4h
```

The `1h` timeframe is useful as source data for resampling and later intraday research, but it is not part of the default context report.

## Temporal Safety

Completed-candle as-of joins are mandatory.

Every bar gets:

```text
available_at = bar_start + timeframe_duration
```

Context is joined only when:

```text
context.available_at <= primary.available_at
```

This prevents a higher-timeframe candle from influencing lower-timeframe analysis before that candle has closed.

Partial higher-timeframe bars are not used in `mtf_context_v0`.

## Context Labels

Leader context:

- `Aligned Leader`: primary is leadership/accumulation and 3D or 1W is supportive.
- `Tactical Leader`: primary is leadership/accumulation but higher timeframe is not yet supportive.
- `Early HTF Turn`: 3D or 1W is improving but primary is not fully confirmed.
- `Conflicted Leader`: primary is strong while higher timeframe is weak.
- `Unconfirmed`: primary lacks confirmation and higher timeframe is neutral.
- `Incomplete Data`: required context is missing or stale.

Trader context:

- `Setup Ready`: supportive context, setup readiness high, extension risk not high.
- `Reset Forming`: supportive context plus lower-timeframe compression or reset.
- `Wait For Confirmation`: context improving but primary setup not ready.
- `Chase Risk`: extension risk is high on primary or lower timeframe.
- `HTF Conflict`: tactical trigger exists but higher timeframe is against it.
- `No Trade Context`: insufficient or unusable context.

These labels are deterministic product language. They are not probabilities.

## Optional Scan Columns

When MTF is requested, the leaderboard appends `mtf_context_v0` sidecar columns such as:

- `mtf_leader_context`
- `mtf_trader_context`
- `mtf_alignment_tags`
- `mtf_conflict_tags`
- `mtf_notes`
- selected 1W, 3D, 12H, and 4H state/signal fields

The existing single-timeframe columns and default sort remain unchanged.

## MTF Research

The `mtf-research` command compares primary-timeframe events with and without MTF support.

It exports:

```text
reports/mtf_research_records.csv
reports/mtf_research_summary.csv
reports/mtf_research_summary.html
obsidian/reports/latest_mtf_research.md
```

The first research questions are:

- Do daily `Relative Accumulation` and `Emerging Leader` states perform better when 3D or 1W is supportive?
- Do daily compressed reclaim events perform better when 3D or 1W is supportive?
- Do lower-timeframe reset labels improve Trader Mode timing without worsening drawdown?

## Evidence Gates

MTF context can be promoted only if aligned samples beat matching non-aligned samples.

Minimum evidence:

- aligned and non-aligned groups both have enough observations
- aligned group improves median 14 or 30 bar forward relative return
- hit rate improves or holds steady
- median drawdown does not materially worsen
- symbol and calendar-cluster concentration checks pass

Small samples remain `inconclusive`.

## Downstream Guardrails

Layer 8 must not silently change:

- `core_signal_v0`
- `state_model_v0`
- `opportunity_score_v0`
- `trader_score_v0`
- default leaderboard sorting
- TradingView oscillator interpretation

Future TradingView use should be compact context badges or labels, not a stack of extra oscillator lines.

## Deferred

Do not implement these in Layer 8 v1:

- optimized MTF weights
- MTF voting score
- probability labels
- production ranking promotion
- alerting
- ML
- TradingView rewrite

Those require stronger evidence from Layer 7 and the new MTF research outputs.
