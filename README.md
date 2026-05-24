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
- Score opportunities with transparent rules.
- Export leaderboard CSV, HTML, and Obsidian markdown reports.
- Run simple event studies focused on forward relative returns.

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

The loader parses `date` as the index, sorts rows, keeps the last duplicate date, and converts OHLCV columns to numeric values.

If CSVs are missing, the CLI emits warnings or fails clearly. It does not generate fake production reports.

## Run A Scan

```bash
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/latest_meme_leaderboard.csv`
- `reports/latest_meme_leaderboard.html`
- `obsidian/reports/latest_meme_scan.md`

Leaderboard fields include signal, relative component, viscosity, compression score, lifecycle state, opportunity score, and notes about missing data.

## Run Event Study

```bash
python3 -m riskflow event-study --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

- `reports/event_study_summary.csv`
- `reports/event_study_summary.html`

The key metric is forward relative return versus the meme basket over 3, 7, 14, and 30 bars.

## Run Tests

```bash
python3 -m pytest
```

Tests use synthetic data only. They cover bootstrap z-scores, missing-member basket math, indicator output contracts, compression score bounds, state validity, and event-study schema.

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

## Research Warning

This project is for exploratory research and education. It can contain bugs, incomplete assumptions, survivorship bias, bad data, exchange-specific artifacts, and unstable rules. Do your own validation before relying on any output.
