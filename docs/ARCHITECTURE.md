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

## Universe Model Direction

The current `configs/meme_universe.yaml` is intentionally simple: each asset has a symbol, name, sector, and subgroup.

The target direction is more flexible. Riskflow should evolve from a rigid tree taxonomy into a tagged, graph-ready universe model.

Important separations:

- Asset identity: the canonical research symbol and what the asset is.
- Data identity: the TradingView/exchange/API symbols used to fetch candles.
- Memberships: structural, tactical, and research groupings.
- Benchmark policy: the preferred comparison basket or parent.
- Quality metadata: label confidence, feed notes, liquidity tier, and data warnings.

This matters because assets often belong to multiple useful groups. For example, BRETT can be a meme, a Base ecosystem asset, a high-beta meme, and a member of the current meme MVP scan. The architecture should support that without forcing one permanent category.

For v1, keep the YAML simple unless the extra metadata is needed by code. When expanding Layer 1, prefer backward-compatible additions over schema churn.

## Benchmark And Tag Direction

Layer 2 is documented in `docs/LAYER_2_BENCHMARKS_AND_TAGS.md`.

The target direction is a configurable benchmark engine with:

- ex-target baskets
- basket viability diagnostics
- benchmark roles and fallback policies
- benchmark confidence
- audit notes explaining why each comparison was chosen
- basket-as-asset support
- controlled primary states and secondary tags

The architecture should keep observations separate from interpretations. Raw features such as signal, relative component, compression score, and active member count should stay distinct from derived labels such as state, tags, confidence, and opportunity score.

## Signal Research Direction

Layer 3 is documented in `docs/LAYER_3_SIGNAL_RESEARCH.md`.

The current Pine-style `final_signal` remains the production incumbent and is treated as `core_signal_v0` in research outputs. Challenger signals are tested in a separate research path before any leaderboard or opportunity-score changes.

Signal definitions live in `signal_registry.py`. This registry is the contract layer between research experiments and downstream consumers such as states, scoring, reports, and TradingView-style interpretation. Future indicator formulas should be added as new versioned signals, not silent edits to `core_signal_v0`.

The first challenger families are:

- relative volatility-adjusted momentum
- relative percentile strength
- cross-sectional relative rank

Riskflow should preserve the current oscillator-style user experience while testing whether challenger observations improve forward relative-return evidence.

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
- `signal_registry.py`: explicit signal identities, roles, versions, triggers, and downstream-use contracts.
- `signal_research.py`: experimental Layer 3 challenger signals and variant event studies.
- `reports.py`: CSV, HTML, and Obsidian markdown export helpers.
- `cli.py`: command-line entry points.

## CLI Commands

```bash
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow event-study --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow signal-research --config configs/meme_universe.yaml --timeframe 1d
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
