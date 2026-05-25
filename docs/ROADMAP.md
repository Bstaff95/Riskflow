# Riskflow Roadmap

For the adaptable long-term product vision, see `docs/END_STATE.md`. The roadmap should stay grounded in what we can test next; the end-state guide should stay flexible and evidence-driven.

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
8. Add basket viability diagnostics, benchmark confidence, and benchmark audit notes.
9. Add the Layer 3 challenger-signal research path without changing production leaderboard behavior.
10. Improve event-study reporting and add Obsidian event-study markdown.
11. Validate whether compression plus improving relative strength predicts forward relative outperformance.
12. Review Layer 4 setup-quality components and decide when Trader Mode should get a separate ranking.
13. Validate `state_model_v0` with state-level event studies before adding transition probabilities.
14. Use `state-research` to decide whether `state_model_v1_candidate` should be built as an evidence-weighted challenger.
15. Use `score-research` to validate whether `opportunity_score_v0`, `trader_score_v0`, and setup component scores actually rank future relative outperformance.
16. Do not build `opportunity_score_v1_candidate` until score research shows what v0 gets wrong.
17. Harden Layer 7 evidence outputs before adding multi-timeframe logic so future complexity has a reliable referee.
18. Use event-study records and Obsidian reports to decide which L3/L4/L5/L6 candidates deserve promotion notes.
19. Use Layer 8 MTF context as an optional sidecar only, with completed-candle joins and no default ranking changes.
20. Run `mtf-research` to test whether 3D/1W support and 12H/4H reset context improve primary daily outcomes.

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

Current Layer 8 implementation is intentionally conservative:

- `mtf_context_v0` appends optional context columns only when requested.
- Higher-timeframe joins use completed-candle `available_at` timestamps.
- `mtf-research` compares aligned versus non-aligned primary events.
- No MTF voting score, probability label, alerting layer, or leaderboard promotion exists yet.

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
