# Layer 10: Transition Evidence

Layer 10 turns lifecycle states into auditable historical path evidence.

It does **not** make Riskflow a Markov engine, prediction model, probability product, or TradingView odds label. The first model is `transition_research_v0`, a research-only layer that studies completed `state_model_v0` transitions and reports observed historical transition rates with uncertainty and context.

## Ownership

Layer 10 owns:

- completed state-run transition records
- observed transition-rate tables
- transition outcome evidence after state changes
- chain/MTF conditioned transition diagnostics
- uncertainty and concentration warnings for transition claims

Layer 10 does not own:

- lifecycle-state definitions
- score formulas
- setup-quality formulas
- signal formulas
- leaderboard ranking
- TradingView visuals
- calibrated probability labels

## Language Rules

Use:

- observed transition rate
- historical transition tendency
- transition evidence
- sample quality
- uncertainty interval
- fragile / inconclusive estimate

Avoid:

- true probability
- prediction
- chance of profit
- buy probability
- odds
- forecast

Example:

```text
Observed transition rate: 38% across 52 historical cases.
Evidence: watchlist.
```

Not:

```text
38% chance of breakout.
```

## Current Implementation

`transition_research_v0` defines a transition event as:

```text
the final bar of a completed state run where next_state exists and differs from from_state
```

Same-state persistence is not counted as a transition. It remains duration evidence.

The command:

```bash
PYTHONPATH=src python3 -m riskflow transition-research --config configs/meme_universe.yaml --timeframe 1d
```

exports:

- `reports/transition_research_records.csv`
- `reports/transition_research_summary.csv`
- `reports/transition_matrix_unconditional.csv`
- `reports/transition_matrix_conditioned.csv`
- `reports/transition_research_summary.html`
- `obsidian/reports/latest_transition_research.md`

Optional MTF conditioning:

```bash
PYTHONPATH=src python3 -m riskflow transition-research --config configs/meme_universe.yaml --timeframe 1d --mtf-preset research-mtf
```

## Evidence Rules

Transition research uses Layer 7-style evidence discipline:

- forward relative return versus benchmark is primary
- medians and hit rates matter more than averages
- drawdown must be monitored
- sample size gates are conservative
- one-symbol and one-calendar-cluster dominance are fragile
- Wilson intervals are shown with observed rates

Classifications:

- `useful`
- `watchlist`
- `inconclusive`
- `fragile`

Low sample size defaults to `inconclusive`. Concentration risk defaults to `fragile`.

## Promotion Gates

Transition evidence can influence future product behavior only after it:

- has enough samples across symbols and clusters
- has bounded uncertainty that still supports the claim
- improves median 14/30 bar forward relative return
- improves or preserves hit rate
- does not worsen drawdown materially
- survives first-half / second-half style stability checks in a future pass
- remains versioned beside the incumbent interpretation
- includes a written promotion note

Until then, transition evidence remains research context only.

## Deferred

Do not implement yet:

- production Markov chains
- hidden Markov models
- hidden semi-Markov models
- Bayesian changepoint transition alerts
- calibrated probability labels
- probability badges in TradingView
- transition-based ranking or alerting
- position sizing from transition evidence

Those can be explored after real data, state validation, and transition evidence show durable signal.
