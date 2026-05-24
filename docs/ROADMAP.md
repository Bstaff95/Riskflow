# Riskflow Roadmap

## Stage 1: Meme MVP

Goal:

> Build a working meme-coin relative leadership and compression lab.

Current foundation:

- local package exists
- config-driven meme universe exists
- CSV loader exists
- equal-weight basket exists
- core indicator engine exists
- compression, states, scoring exist
- scan and event-study CLI exist
- resampling CLI exists for deriving 1W/3D from 1D and 12H/4H from 1H
- tests exist
- GitHub repo and Obsidian vault exist

Next priorities:

1. Add real OHLCV data files locally across the meme universe.
2. Use resampling to build the first multi-timeframe local dataset.
3. Run the first real meme leaderboard across enough assets to be meaningful.
4. Review missing/bad data warnings.
5. Tighten Pine-to-Python parity where it matters.
6. Add score component columns to leaderboard.
7. Add ex-target basket option so each coin can be compared to the basket excluding itself.
8. Improve event-study reporting and add Obsidian event-study markdown.
9. Validate whether compression plus improving relative strength predicts forward relative outperformance.

## Stage 2: Crypto Sector Engine

Add sector baskets:

- majors
- memes
- AI coins
- DeFi
- gaming
- RWA
- L1s
- L2s
- SOL ecosystem
- Base ecosystem
- ETH ecosystem

Add nested comparisons:

- sector versus broad crypto
- subgroup versus sector
- coin versus subgroup
- coin versus siblings

## Stage 3: Multi-Timeframe Engine

Use:

- weekly for regime
- 3D for swing structure
- daily for tactical confirmation
- 12H for lower swing confirmation
- 4H for timing and reset
- 1H for intraday structure and source data for 4H/12H resampling

Potential labels:

- early reversal
- confirmed leader
- chop needed
- overheated
- failed reclaim
- compressed gem

## Stage 4: Probabilistic Transitions

After lifecycle states are validated:

- transition matrices
- conditional transitions by parent state
- expansion/chop/failure probabilities

Do not build this before states and event studies have enough evidence.

## Stage 5: Historical Analog Search

Find prior setups with similar:

- parent sector state
- asset state
- compression
- relative component
- signal slope
- drawdown profile
- forward relative-return outcome

## Stage 6: Dashboard/Product

Only after the local engine is useful:

- capital-flow map
- sector rotation map
- opportunity leaderboard
- alerts
- reports
- visual graph

## Stage 7: Global Markets

Extend the same normalized architecture into:

- stocks
- commodities
- gold and silver
- bonds and rates
- DXY and FX
- semiconductors
- memory stocks
- AI stocks
- energy
- small caps
