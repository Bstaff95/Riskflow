# Riskflow Architecture

Riskflow is currently a local Python package plus config files, tests, reports, and an Obsidian research vault.

## Repository Layout

```text
configs/              YAML universe and runtime settings
data/raw/             local OHLCV CSV input files, ignored by git
data/processed/       derived data, ignored by git
docs/                 durable project memory and architecture notes
notebooks/            starter research notebooks
obsidian/             research vault and generated markdown reports
reports/              generated CSV/HTML reports, ignored by git
src/riskflow/         Python package
tests/                pytest test suite
AGENTS.md            coding-agent instructions
README.md            user-facing project overview
```

## Main Data Flow

```text
configs/meme_universe.yaml
        |
        v
data_loader.py loads OHLCV CSVs
        |
        v
resample.py optionally derives higher timeframes
        |
        v
baskets.py builds equal-weight return basket
        |
        v
indicator_engine.py calculates relative strength signal
        |
        v
compression.py calculates asset-relative compression
        |
        v
states.py classifies lifecycle state
        |
        v
scoring.py calculates opportunity score
        |
        v
reports.py exports CSV/HTML/Obsidian markdown
```

## Package Modules

- `config.py`: YAML loading into dataclasses.
- `data_loader.py`: local OHLCV CSV discovery, validation, and loading.
- `resample.py`: OHLCV timeframe derivation, such as 1D to 1W/3D and 1H to 12H/4H.
- `baskets.py`: equal-weight return-index construction.
- `features.py`: shared numerical helpers such as rolling z-score, logs, percentiles.
- `indicator_engine.py`: Pine-style normalized component engine, viscosity, gradient driver.
- `compression.py`: ATR%, range%, realized vol, Bollinger-style width, compression score.
- `states.py`: deterministic lifecycle state classification.
- `scoring.py`: explainable opportunity score.
- `event_study.py`: event detection and forward absolute/relative return summaries.
- `reports.py`: CSV, HTML, and Obsidian markdown export helpers.
- `cli.py`: command-line entry points.

## CLI Commands

```bash
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow event-study --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow resample --config configs/meme_universe.yaml --preset research-mtf
```

## Generated Files

Generated outputs are intentionally ignored by git:

- `data/raw/*`
- `data/processed/*`
- `reports/*`
- `obsidian/reports/*`

Only `.gitkeep` placeholders should be committed in those directories.

## Current Gaps To Remember

- The Python engine is conceptually aligned with the Pine script, but not full one-to-one parity yet.
- The basket output currently focuses on the basket index; richer active-member diagnostics can be added.
- Event-study markdown export is not yet as complete as scan markdown reporting.
- Real market data is not included in the repo.
