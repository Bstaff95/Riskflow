# Riskflow

Riskflow is a local quant research lab for studying capital flow, relative leadership, and compressed setups before they become obvious. The importable Python package is named `riskflow`.

This is research software. It is not a trading bot, not investment advice, and not a guarantee of future returns.

## Long-Term Vision

The eventual system should become a probabilistic capital-flow graph:

1. Compare asset classes, sectors, subgroups, and individual assets.
2. Detect where leadership is migrating.
3. Find assets gaining relative strength inside strengthening groups.
4. Prefer candidates that remain compressed before full repricing.
5. Study state transitions and forward relative returns.

Future versions can add crypto sector hierarchies, stocks, commodities, macro assets, nested relative strength, Markov state transitions, historical analog search, and a dashboard.

## V1 Scope

V1 is intentionally small: daily crypto meme coins versus an equal-weight meme basket.

It can:

- Load local OHLCV CSV files.
- Build an equal-weight return index benchmark.
- Calculate a Pine-style relative strength signal.
- Calculate adaptive viscosity and gradient driver fields.
- Calculate asset-relative compression features.
- Classify simple lifecycle states.
- Score opportunities with transparent rules and setup-quality components.
- Export leaderboard CSV, HTML, and Obsidian markdown reports.
- Run simple event studies focused on forward relative returns.
- Run a separate Layer 3 signal-research pass for challenger indicators.
- Run Layer 4 setup research, Layer 5 state research, and Layer 6 score research without changing default leaderboard behavior.
- Use a Layer 7 evidence engine to harden event studies with entry lag, cooldowns, concentration diagnostics, and Obsidian reports.
- Add optional Layer 8 multi-timeframe context sidecars without changing default ranking or scan schema.
- Export Layer 9 capital-flow graph tables and graph evidence without changing default ranking.
- Run Layer 10 transition evidence reports without turning observed rates into forecasts.
- Use a Signal Grammar Lab to turn TradingView-style visual reads into structured observations, grammar primitives, and later evidence-tested events.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

The package uses `pandas`, `numpy`, `PyYAML`, `matplotlib`, and `pytest`.

## Data Format

Put real daily CSV files in `data/raw`.

Supported filenames:

- `DOGE.csv`
- `DOGE_1d.csv`
- lowercase equivalents such as `doge.csv`

Required columns:

```csv
date,open,high,low,close,volume
2024-01-01,0.09,0.10,0.08,0.095,1000000
```

TradingView CSV exports are supported. Columns such as `time`, `Date`, `Open`, `High`, `Low`, `Close`, and `Volume` are normalized automatically. If volume is missing, Riskflow fills it with `0` because v1 calculations do not use volume.

To use TradingView data:

1. Open the symbol and timeframe in TradingView.
2. Export chart data to CSV.
3. Rename the file to match the Riskflow symbol, such as `DOGE_1d.csv` or `BRETT_1d.csv`.
4. Put it in `data/raw`.

The loader parses the date/time column as the index, sorts rows, keeps the last duplicate date, and converts OHLCV columns to numeric values.

## Resample Timeframes

Riskflow can derive higher-timeframe OHLCV files from lower-timeframe CSVs. This reduces TradingView exports: for the research stack, export `1d` and `1h` data, then derive the rest locally.

```bash
python3 -m riskflow resample --config configs/meme_universe.yaml --from-timeframe 1d --to-timeframe 1w 3d
python3 -m riskflow resample --config configs/meme_universe.yaml --from-timeframe 1h --to-timeframe 12h 4h
```

Or run the preset:

```bash
python3 -m riskflow resample --config configs/meme_universe.yaml --preset research-mtf
```

Resampling uses standard OHLCV aggregation: first open, highest high, lowest low, last close, and summed volume.

If CSVs are missing, the CLI emits warnings or fails clearly. It does not generate fake production reports.

## Run A Scan

```bash
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/latest_meme_leaderboard.csv`
- `reports/latest_meme_leaderboard.html`
- `obsidian/reports/latest_meme_scan.md`

Leaderboard fields include signal, relative component, viscosity, compression score, setup-quality components, lifecycle state, state model/reason/tags, opportunity score, setup tags, and notes about missing data.

Layer 2 benchmark diagnostics are included in the leaderboard. For the meme config, Riskflow uses ex-target baskets when viable, such as `MEME_BASKET_EX_BRETT`, so each coin is compared against peers without including itself. If too few peers are active, it falls back to the configured basket and marks the fallback, confidence, active-member count, and audit notes.

Optional multi-timeframe context:

```bash
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d --context-timeframes 1w 3d 12h 4h
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d --mtf-preset research-mtf
```

When MTF is requested, Riskflow appends `mtf_context_v0` columns such as leader context, trader context, alignment tags, conflict tags, and selected 1W/3D/12H/4H signal fields. Without those flags, scan output columns remain unchanged.

## Run Event Study

```bash
python3 -m riskflow event-study --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/event_study_summary.csv`
- `reports/event_study_records.csv`
- `reports/event_study_summary.html`
- `obsidian/reports/latest_event_study.md`

The key metric is forward relative return versus the meme basket over 3, 7, 14, and 30 bars. The command defaults to a one-bar entry lag so outcomes start after the event bar closes.

Useful evidence guardrails:

```bash
python3 -m riskflow event-study --entry-lag-bars 1 --cooldown-bars 30 --min-sample-size 20
```

Layer 7 event-study reports include event classifications, concentration diagnostics, first-half/second-half checks, and notes. They are research evidence, not trade instructions.

## Visual Indicator Learning

Riskflow treats the TradingView-style oscillator as a visual instrument and a research object. The current goal is not to keep adding overlays until something looks impressive. The goal is to learn the oscillator grammar first:

- viscosity acceptance and retests
- `-2`, `-1.5`, `0`, `1.5`, and `2` level behavior
- oscillator trendline and wedge breaks
- failed weakness in deep negative zones
- bullish and bearish divergences
- color or gradient weakening
- time and signed area above or below viscosity

The workflow is documented in `docs/VISUAL_INDICATOR_LEARNING_LOOP.md` and `docs/SIGNAL_GRAMMAR_LAB.md`. Structured observations live in `research/observations/`; grammar primitives live in `research/grammar/primitive_registry.yaml`; Obsidian pages under `obsidian/wiki/` are the human synthesis layer.

Pressure waves are currently experimental. They may become the final extra visual layer, but only if reviewed examples and Layer 7 evidence show they add leading signal, improve false-positive control, and remain readable.

Summarize the current grammar lab coverage:

```bash
python3 -m riskflow grammar-lab
```

Outputs:

- `reports/grammar_lab/primitive_summary.csv`
- `reports/grammar_lab/review_plan.md`
- `obsidian/wiki/maps/Signal Grammar Lab.md`

## Run Setup Research

```bash
python3 -m riskflow setup-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/setup_research_summary.csv`
- `reports/setup_research_summary.html`
- `reports/setup_research_records.csv`

This command tests Layer 4 setup events, such as compression plus relative strength rising, setup readiness, extension risk, and `trader_score_v0` threshold events. It does not change the default leaderboard ranking.

## Run State Research

```bash
python3 -m riskflow state-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/state_research_summary.csv`
- `reports/state_research_summary.html`
- `reports/state_research_records.csv`
- `reports/state_transition_matrix.csv`
- `obsidian/reports/latest_state_research.md`

State research evaluates whether lifecycle labels have historically separated future relative returns, drawdowns, duration, and next-state transitions. It does not replace the active `state_model_v0` labels.

## Run Score Research

```bash
python3 -m riskflow score-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/score_research_records.csv`
- `reports/score_research_bucket_summary.csv`
- `reports/score_research_ic_summary.csv`
- `reports/score_research_score_summary.csv`
- `reports/score_research_summary.html`
- `obsidian/reports/latest_score_research.md`

Score research tests whether high `opportunity_score_v0`, `trader_score_v0`, and setup component scores actually rank future relative outperformance. It uses date-wise buckets, top-minus-bottom spreads, rank IC, drawdown, and concentration diagnostics. It does not retune scores or change default leaderboard sorting.

## Run Multi-Timeframe Research

```bash
python3 -m riskflow mtf-research --config configs/meme_universe.yaml --primary-timeframe 1d --context-timeframes 1w 3d 12h 4h
```

Outputs:

- `reports/mtf_research_records.csv`
- `reports/mtf_research_summary.csv`
- `reports/mtf_research_summary.html`
- `obsidian/reports/latest_mtf_research.md`

MTF research compares primary-timeframe events with and without completed higher/lower timeframe support. It is evidence for future context badges, not permission to change the default leaderboard ranking.

## Run Flow Graph

```bash
python3 -m riskflow flow-graph --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/flow_graph_nodes.csv`
- `reports/flow_graph_edges.csv`
- `reports/flow_graph_chains.csv`
- `obsidian/reports/latest_flow_graph.md`

The flow graph is a table-based sidecar. It maps assets, subgroups, sectors, and the current benchmark basket, then labels whether each asset has partial, conflicted, or incomplete chain support. It infers relative leadership context from price-derived data; it is not literal fund-flow proof.

## Run Flow Research

```bash
python3 -m riskflow flow-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/flow_research_records.csv`
- `reports/flow_research_summary.csv`
- `reports/flow_research_summary.html`
- `obsidian/reports/latest_flow_graph.md`

Flow research tests whether primary asset events work better when chain context is supportive. It does not change default scan ranking.

## Run Transition Research

```bash
python3 -m riskflow transition-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/transition_research_records.csv`
- `reports/transition_research_summary.csv`
- `reports/transition_matrix_unconditional.csv`
- `reports/transition_matrix_conditioned.csv`
- `reports/transition_research_summary.html`
- `obsidian/reports/latest_transition_research.md`

Transition research studies completed lifecycle-state changes, such as `Compression -> Relative Accumulation`, then reports observed historical transition rates, Wilson uncertainty intervals, forward relative returns, drawdowns, and concentration diagnostics. These are research tendencies, not predictions.

Optional MTF conditioning:

```bash
python3 -m riskflow transition-research --config configs/meme_universe.yaml --timeframe 1d --mtf-preset research-mtf
```

## Run Signal Research

```bash
python3 -m riskflow signal-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/signal_research_summary.csv`
- `reports/signal_research_summary.html`
- `reports/signal_research_records.csv`

This command keeps the Pine-style `final_signal` as `core_signal_v0`, then compares a small set of challenger and baseline signals against forward relative returns. It does not change the default leaderboard or opportunity score.

Useful research guardrails:

```bash
python3 -m riskflow signal-research --cooldown-bars 30 --entry-lag-bars 1
```

The cooldown avoids counting overlapping events from the same symbol as independent evidence. The entry lag starts forward-return measurement after the signal bar closes.

## Run Visual Review

```bash
python3 -m riskflow visual-review --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/visual_review/events.csv`
- `reports/visual_review/gallery.md`
- `reports/visual_review/images/*.png`

Visual review bridges numeric research and chart intuition. It finds historical strong forward relative breakouts, renders local chart snapshots from the Python engine, and tags what the indicator looked like before the move: signal zone, viscosity reclaim, relative component, compression, and state. It does not change the indicator, scores, states, or leaderboard ranking.

Useful controls:

```bash
python3 -m riskflow visual-review --min-forward-relative-return 0.30 --min-history-bars 40 --lookback-bars 80 --forward-bars 30
```

The observation library exports visual-review rows into machine-readable records and Obsidian wiki notes. This is the Karpathy-style research-memory layer: structured records remain the evidence source, while Obsidian connects cases, patterns, concepts, and principles.

```bash
python3 -m riskflow observation-library --events-csv reports/visual_review/events.csv --obsidian-dir obsidian
```

Outputs include:

- `research/observations/observation_records.jsonl`
- `research/observations/observation_schema.yaml`
- `obsidian/wiki/Indicator Observation Library.md`
- `obsidian/wiki/cases/*.md`
- `obsidian/wiki/patterns/*.md`
- `obsidian/wiki/concepts/*.md`

## Run Tests

```bash
python3 -m pytest
```

Tests use synthetic data only. They cover bootstrap z-scores, missing-member basket math, indicator output contracts, compression score bounds, state validity, and event-study schema.

## Project Memory

Durable project context lives in `docs/`:

- `docs/PROJECT_CONTEXT.md` explains what Riskflow is trying to become.
- `docs/ARCHITECTURE.md` explains how the current Python package is organized.
- `docs/ROADMAP.md` explains staged next steps.
- `docs/WORKFLOW.md` explains the GitHub, Codex, and Obsidian workflow.
- `docs/LAYER_3_SIGNAL_RESEARCH.md` explains the adversarial signal-research plan.
- `docs/LAYER_4_SETUP_QUALITY.md` explains setup quality, Trader Mode readiness, and Layer 4 versioning.
- `docs/LAYER_5_LIFECYCLE_STATES.md` explains lifecycle state contracts and state research.
- `docs/LAYER_6_OPPORTUNITY_SCORING.md` explains score validation and promotion gates.
- `docs/LAYER_7_EVIDENCE_ENGINE.md` explains shared evidence methodology and promotion gates.
- `docs/LAYER_8_MULTI_TIMEFRAME_CONTEXT.md` explains optional MTF context, completed-candle joins, and MTF research.
- `docs/LAYER_9_CAPITAL_FLOW_GRAPH.md` explains capital-flow graph tables, chain context, and graph evidence.
- `docs/LAYER_7_EVIDENCE_ENGINE.md` explains event-study hardening and evidence promotion gates.
- `docs/VISUAL_INDICATOR_LEARNING_LOOP.md` explains how to turn chart intuition into testable Riskflow hypotheses.

Agent behavior and repo guardrails live in `AGENTS.md`.

## Config

Edit `configs/meme_universe.yaml` to change the universe, benchmark settings, indicator weights, indicator settings, and compression settings.

The default active v1 weights are:

- price: `1.20`
- relative: `0.65`
- risk: configured but disabled by default

The current default indicator settings are aligned to the active TradingView research setup:

- component z-score lookback: `200`
- component clamp: `3.5`
- risk environment: `off`
- viscosity lookback / fast / slow: `20 / 2 / 34`
- viscosity impulse / zero-zone boosts: `0.65 / 0.35`

## Indicator Summary

For each asset:

1. Normalize asset and benchmark by their first valid values.
2. Use log normalized price and log relative ratio.
3. Convert price and relative logs to bootstrap rolling z-scores.
4. Clamp components to `+/- component_z_clamp`.
5. Fuse available components by weighted sum divided by root-sum-square active weights.
6. Smooth the final signal with an adaptive KAMA-like viscosity line, including impulse and zero-zone boosts.
7. Build a gradient driver from signal level, distance from viscosity, slope, and acceleration.

The signal exists as soon as valid target price exists. Flat or too-short z-score windows return `0` instead of `NaN` when the source is valid.

## Compression Summary

Compression is asset-relative. V1 calculates:

- ATR percent
- rolling high-low range percent
- realized volatility
- Bollinger-style width

Each feature is converted to a trailing percentile against its own history. The final compression score is:

```text
100 - average(volatility_feature_percentiles)
```

High score means compressed or coiled. Low score means expanded or high volatility.

Layer 4 adds setup-quality context on top of compression:

- `compression_duration`
- `compression_stability`
- `leader_quality_score`
- `compression_quality_score`
- `relative_accumulation_score`
- `setup_readiness_score`
- `extension_risk_score`
- `data_quality_score`
- `trader_score_v0`
- `trader_rank`
- `setup_tags`

These are explanatory components. The active leaderboard ranking remains backward-compatible through `opportunity_score`.

## Research Warning

This project is for exploratory research and education. It can contain bugs, incomplete assumptions, survivorship bias, bad data, exchange-specific artifacts, and unstable rules. Do your own validation before relying on any output.
