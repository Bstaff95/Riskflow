# Visual Indicator Learning Loop

This document captures the working method for learning how the Riskflow oscillator actually behaves.

The goal is not to force the indicator into a black-box backtest too early. The goal is to build a feedback loop between:

- real TradingView screenshots
- visual chart reading
- indicator path behavior
- forward relative-return evidence
- missed examples
- formula or event-definition improvements

## Core Idea

Riskflow should be studied like a visual instrument and a research engine at the same time.

The TradingView chart is the frontend truth layer. If the future product includes a TradingView-style indicator, then the research process must include actual screenshots of what the user would have seen, with the same symbol, timeframe, benchmark, risk mode, price source, and indicator settings.

The Python chart is the reproducible measurement layer. It is useful for scanning many cases, calculating forward returns, and testing definitions, but it should not be treated as visually equivalent until Pine-to-Python parity is confirmed.

The user can often see patterns that are hard to describe mathematically at first:

- signal compresses around the lower band
- signal reclaims viscosity
- signal retests viscosity instead of failing
- price consolidates while relative strength improves
- impulse happens, then reset holds
- oscillator divergence appears before price fully reprices

Those observations should become named hypotheses, not instant production rules.

Example hypothesis:

> Compression around `-2` to `-1`, followed by impulse above viscosity, followed by a successful viscosity retest, may identify an early breakout setup.

This becomes a candidate event like:

```text
compression_impulse_viscosity_retest_v0
```

Then Riskflow can test whether that pattern actually led to forward relative outperformance versus the correct benchmark.

The first earlier-entry companion event is:

```text
coil_viscosity_reclaim_v0
```

This looks for a lower-zone coil around the `-2` to `-1` area, then a viscosity reclaim while the signal is still early rather than already overheated. It is meant to test the visual idea that the useful clue may happen before the dramatic impulse/retest is obvious.

Example command for 4H archeology:

```bash
PYTHONPATH=src python3 -m riskflow visual-review --config configs/meme_universe.yaml --timeframe 4h --event-mode coil-reclaim --cooldown-bars 12
```

The shorter cooldown is useful on 4H because nearby early/failed/retest attempts can occur within a few days. Longer cooldowns are still useful when building cleaner event-study samples.

The first human review of the TROLL 4H example added more precision:

- the oscillator structure looked like a `descending_wedge`
- the setup reclaimed viscosity but did not cleanly retest viscosity
- the important retests were closer to the `-2` and `-1.5` levels
- the deeper principle may be lower-band level holds followed by viscosity reclaim, not only viscosity reclaim/retest

The SPX6900 4H review added a second important pattern: the useful signal may be an earlier confluence break rather than the later generated event. The observed confluence was:

- major oscillator downtrend resistance
- drop below `-2`
- ascending wedge below the larger downtrend
- wedge breakout and downtrend breakout
- quick color shift from green toward yellow
- flat viscosity before the break
- simultaneous reclaim of `-2`, `-1.5`, viscosity, wedge resistance, and larger downtrend resistance

This suggests a future event family around `multi_level_reclaim_confluence`, not only single viscosity reclaim events.

The MOG 4H review added a more subtle persistence pattern:

- oscillator lows curling upward over time
- reclaim of viscosity and `-2`
- sustained time above viscosity even without a large impulse
- later flush below viscosity that failed quickly
- fast reclaim back above viscosity as the real trigger

This suggests a future event family around `viscosity_acceptance_flush_reclaim`, where time above viscosity and failed breakdown behavior matter more than a single clean crossover.

The TURBO 4H review added a sequence pattern:

- first oscillator downtrend break failed
- oscillator reset lower and formed a descending channel
- signal washed below `-2`
- second trend/channel break reclaimed viscosity
- quick viscosity retest held
- `-1.5` reclaim preceded expansion

This suggests a future event family around `failed_breakout_reset_reclaim`, where the second break after a failed first break can be higher quality than the first break.

The TRUMP 4H review added an important false-positive filter:

- extremely steep oscillator downtrend
- no meaningful bounce when the structure broke
- chop instead of expansion
- breakdown
- repeated underside rejection from former oscillator support

This suggests future filters should penalize `steep_oscillator_downtrend`, `weak_breakout_response`, `no_meaningful_bounce`, and `underside_support_rejection`.

The GIGA 4H review added a constructive-but-unconfirmed pattern:

- time above viscosity was constructive
- zero-line reclaim/hold failed
- the setup needed a double bottom or second base before expansion
- prior impulse spike plus immediate retrace may have required reset time

This suggests future filters should distinguish `viscosity_acceptance_unconfirmed` from `viscosity_acceptance_zero_confirmed`. The zero line may be the confirmation gate between basing and actionable momentum.

The BONK 4H review added a noisy-strength filter:

- oscillator highs curled upward
- signal action was very volatile
- no real compression
- impulses were immediately sold off
- signal could not sustain strength

This suggests future filters should penalize `chaotic_oscillator_pa`, `impulse_sold_off`, `no_compression`, and `failed_strength_acceptance`.

The PEPE 1D review added a divergence sequence:

- price came off a capitulatory low
- oscillator rejected near zero
- price made a higher high while the oscillator made a lower high
- that bearish divergence warned of weakness
- price later double bottomed
- oscillator made higher lows during the double bottom
- that bullish divergence preceded another leg higher

This confirms that the Riskflow oscillator should be treated as TA-readable for both bullish and bearish divergences, not only reclaim/breakout patterns.

The TRUMP 1D April 2025 review added a higher-timeframe nuance:

- earlier downtrend break caught the pump before the generated event
- tight chop above `-2`
- `-1.5` reclaim on a small candle before the move
- failure to reach zero and weak color shift warned the setup was not fully confirmed
- this may identify a pump, but not necessarily a durable trend reversal

This suggests future daily filters should distinguish `early_break_pump_candidate` from `confirmed_reversal`.

A follow-up TRUMP 1D review added color/gradient divergence as a warning signal:

- the second push failed to make a higher signal high
- the second push also had weaker oscillator color
- this created a pressure-quality divergence, not only a line-level divergence
- weaker color on a second push may warn that the bounce has less force behind it

This suggests future filters should track `color_divergence`, `weaker_second_color_push`, and `gradient_momentum_divergence`. The color engine may carry information about pressure quality that is not obvious from signal level alone.

The SHIB 1D August 2025 review added another false-positive filter:

- signal weakly chopped above and below viscosity
- a wedge existed, but colors stayed weak
- the signal failed to make meaningful higher highs
- oscillator movement was volatile rather than compressed
- the later wedge break came with signal higher highs but price lower highs
- that was hidden bearish divergence, not clean bullish confirmation

This suggests future filters should penalize `weak_viscosity_chop`, `wedge_without_confirmation`, `weak_colors`, `no_compression`, `unstructured_volatility`, and `hidden_bearish_divergence`.

The TOSHI 1D September 2024 review added a low-is-in versus trade-ready distinction:

- the main signal was the longer-term oscillator downtrend break
- signal based under `-1.5` before that break
- the break was explosive once it reached the long-term downtrend
- price still needed to chop after the signal break
- the low appeared to be in before price became cleanly trade-ready

The zoomed-in TOSHI review added a lower-zone weakness-exhaustion idea:

- signal rejected under viscosity while already very low
- instead of accelerating lower, it coiled tightly underneath
- it failed to make significantly lower lows
- that may mean relative weakness stopped accelerating

This suggests future event families should separate `low_in_before_price_confirmation` from immediate entry triggers, and test `coil_under_viscosity` / `relative_weakness_fails_to_accelerate` as reversal-watchlist primitives.

The BRETT 1D August 2025 review added a failed-reversal-watchlist filter:

- oscillator downtrend broke earlier than August
- signal never got strong after the break
- signal chopped around viscosity instead of accepting it as support
- signal could not break the zero line
- price kept making lower lows
- there was not enough compression

This suggests oscillator trendline breaks need confirmation gates. Daily reversal candidates should be separated into `failed_reversal_watchlist` versus confirmed reversal based on zero-line confirmation, sustained time above viscosity, price stabilization, and compression. Clean daily uptrends often keep the signal above viscosity most of the time.

## Regime And Time Clustering Warning

Early visual-review examples are clustered around a similar March-April 2026 market window. That is useful for first-pass grammar discovery, but weak for generalization. The library should deliberately include:

- different date clusters
- different timeframes
- clean hits and false positives
- missed breakouts
- different market regimes

Because the oscillator is designed to be TA-readable, the observation library should treat oscillator technical analysis as first-class research language. Useful tags include:

- `oscillator_trendline_break`
- `descending_wedge`
- `ascending_triangle`
- `bullish_divergence`
- `bearish_divergence`
- `higher_low`
- `lower_high`
- `failed_breakdown`
- `support_retest`
- `resistance_reclaim`
- `zero_line_support`
- `viscosity_support`
- `lower_band_support`
- `upper_band_rejection`

These tags describe what the oscillator structure did. They do not prove edge until repeated observations and forward relative-return evidence support them.

## Observation Library

Riskflow uses a lightweight LLM-wiki style observation library:

- structured records in `research/observations/`
- Obsidian wiki pages in `obsidian/wiki/`
- screenshots linked from visual-review outputs
- human labels added after review

Export the current visual-review results:

```bash
PYTHONPATH=src python3 -m riskflow observation-library --events-csv reports/visual_review/events.csv --obsidian-dir obsidian
```

The wiki is the memory and synthesis layer. The structured records are the evidence source. A pattern note can suggest a principle, but only repeated reviewed observations and forward-return evidence can promote it.

## Active Pine-Style Settings To Match First

The current TradingView research setup is the reference for visual review:

- Market Mode: `Crypto`
- Analysis Target: `Current Chart Asset`
- Price Source: `Close`
- Selected Basket: `Crypto Meme Broad Basket`
- Relative Benchmark: `Selected Basket`
- Risk Environment: `Off`
- Weight Preset: `Meme Leadership Default`
- Final Signal Normalization: `Weight-Scaled Fusion`
- Display Mode: `Final Signal`
- Candle Color Source: `Gradient Driver`
- Minimum Active Basket Members: `3`
- Force Full Price History: enabled
- Never Blank Signal: enabled
- Price / relative / risk weights: `1.20 / 0.65 / 0.85`
- Component Z-Score Lookback: `200`
- Component Z Clamp: `3.5`
- Viscosity lookback / fast / slow: `20 / 2 / 34`
- Viscosity impulse / zero-zone boosts: `0.65 / 0.35`

Riskflow Python should use these as the first parity target before judging whether a visual pattern worked or failed. If a TradingView screenshot uses different settings, record the mismatch before drawing research conclusions.

## The Loop

1. Find a real chart example.
2. Describe what the indicator seemed to show before the move.
3. Mark the event date/time and timeframe.
4. Capture or attach the actual TradingView screenshot when possible.
5. Recreate the chart locally from Riskflow data when possible.
6. Compare TradingView versus Python output and record mismatches.
7. Translate the visual idea into measurable conditions.
8. Search for similar historical cases.
9. Separate hits, misses, and false positives.
10. Ask what was missing in each case.
11. Adjust the candidate definition only if the improvement is explainable.
12. Validate with forward relative returns, hit rates, drawdowns, and concentration checks.

## Case Types

Every example should be classified into one of these buckets:

- `predicted_breakout`: indicator showed a plausible setup before price expanded.
- `missed_breakout`: price ran but current indicator/event logic did not flag it.
- `false_positive`: indicator showed a setup but price or relative performance failed.
- `late_signal`: indicator flagged only after most repricing already happened.
- `overheated_continuation`: signal looked extended but continuation still worked.
- `bad_data_or_feed`: chart behavior depends on unreliable candles or benchmark data.
- `risk_context_mismatch`: local Python result differs because risk mode, benchmark, or settings do not match TradingView.

The minimum useful review set should include all three core buckets:

- price ran and the indicator visibly helped explain it
- price ran and the indicator did not visibly help explain it
- indicator looked good and price did not run

This prevents Riskflow from only studying winners after the fact.

The misses are as important as the winners. A missed breakout can reveal whether Riskflow needs better risk context, timeframe context, benchmark structure, or event definitions.

## What To Record

For each reviewed example:

- symbol
- timeframe
- event date/time
- TradingView settings if used
- benchmark
- risk mode on/off
- price source
- screenshot path
- whether screenshot came from TradingView or local Python
- final signal level
- viscosity level
- relative component
- price component
- risk component if available
- compression score
- state
- setup tags
- forward relative return
- max drawdown after event
- visual interpretation
- whether the local Riskflow chart matches the TradingView chart

## Tuning Rules

Do not tune from one beautiful chart.

A candidate pattern can become more important only if it:

- appears across multiple symbols or time periods
- improves median forward relative return
- improves or preserves hit rate
- does not materially worsen drawdown
- does not depend on one huge winner
- remains explainable in plain language
- works versus the correct ex-target benchmark
- is tested with the same settings being visually interpreted

If TradingView uses Risk Mode ON, the Python test must eventually include comparable risk context before conclusions are trusted.

## Product Relevance

This loop is how Riskflow can become both:

- an intuitive oscillator that can be read visually, like RSI or the current hydraulic-style indicator
- a research engine that proves which visual setups deserve attention

The product goal is not only to output a leaderboard. It is to teach the system what high-quality setups look like before they are obvious, then show those setups in a way the user can understand and trust.
