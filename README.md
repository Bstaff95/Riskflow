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

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

The package uses `pandas`, `numpy`, `PyYAML`, and `pytest`.

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

## Run Event Study

```bash
python3 -m riskflow event-study --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/event_study_summary.csv`
- `reports/event_study_summary.html`

The key metric is forward relative return versus the meme basket over 3, 7, 14, and 30 bars.

## Run Setup Research

```bash
python3 -m riskflow setup-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/setup_research_summary.csv`
- `reports/setup_research_summary.html`
- `reports/setup_research_records.csv`

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

This command tests Layer 4 setup events, such as compression plus relative strength rising, setup readiness, extension risk, and `trader_score_v0` threshold events. It does not change the default leaderboard ranking.

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

Agent behavior and repo guardrails live in `AGENTS.md`.

## Config

Edit `configs/meme_universe.yaml` to change the universe, benchmark settings, indicator weights, indicator settings, and compression settings.

The default active v1 weights are:

- price: `1.20`
- relative: `0.65`
- risk: configured but disabled by default

## Indicator Summary

For each asset:

1. Normalize asset and benchmark by their first valid values.
2. Use log normalized price and log relative ratio.
3. Convert price and relative logs to bootstrap rolling z-scores.
4. Clamp components to `+/- component_z_clamp`.
5. Fuse available components by weighted sum divided by root-sum-square active weights.
6. Smooth the final signal with an adaptive KAMA-like viscosity line.
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
