# Layer 7: Evidence Engine And Event-Study Hardening

Layer 7 is Riskflow's evidence layer.

Layer 3 creates strength signals. Layer 4 creates setup-quality features. Layer 5 creates lifecycle states. Layer 6 ranks attention. Layer 7 asks:

```text
Did any of this actually work afterward?
```

## Core Principle

Evidence is the referee.

An attractive signal, setup label, state, or score is still only a hypothesis until it survives forward relative-return testing, drawdown checks, concentration diagnostics, and stability review.

Events answer:

```text
Did this condition work?
```

Rankings answer:

```text
Did this ordering help attention?
```

Scores are attention priorities, not probabilities.

## Layer Ownership

Layer 7 owns:

- event-study methodology
- event metadata contracts
- shared outcome math
- entry lag and cooldown policy
- forward return and forward relative return calculations
- drawdown calculations
- concentration diagnostics
- evidence classifications
- evidence reports
- promotion gates

Layer 7 does not own:

- signal formulas
- setup formulas
- compression math
- score formulas
- lifecycle-state labels
- TradingView UI
- ML or probability calibration

## Shared Outcome Contract

Outcome math lives in `src/riskflow/research_outcomes.py`.

Shared defaults:

```text
horizons = 3, 7, 14, 30 bars
default event-study entry lag = 1 bar
default event-study cooldown = 30 bars
primary outcomes = 14 and 30 bar forward relative returns
```

Forward relative return versus the benchmark is the primary research target. Absolute forward return is secondary.

This protects the project from mistaking broad meme-sector beta for true leadership.

## Event Registry

Event metadata lives in `src/riskflow/event_registry.py`.

Each event has:

- `event_id`
- family
- version
- default trigger
- default entry lag
- default cooldown
- priority
- direction
- value column
- description

The registry is metadata-first. It is not a rule engine yet. Detection logic remains in the relevant modules, but event ids should not drift silently.

## Hardened Event Study

Run the Layer 7 baseline evidence command with:

```bash
python3 -m riskflow event-study --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

```text
reports/event_study_summary.csv
reports/event_study_records.csv
reports/event_study_summary.html
obsidian/reports/latest_event_study.md
```

Event records include:

```text
symbol
date
timeframe
benchmark
event
event_id
event_family
event_version
event_value
entry_lag_bars
entry_date
cooldown_bars
event_cluster_id
forward returns
forward relative returns
max drawdowns
```

The CLI default `entry_lag_bars=1` means outcomes begin after the event bar closes. This avoids pretending the user could act before the signal existed.

## Evidence Classification

Layer 7 uses conservative classifications:

```text
useful
watchlist
inconclusive
fragile
```

Default interpretation:

- low sample size means `inconclusive`
- one-symbol dominance is `fragile`
- one-calendar-cluster dominance is `fragile`
- missing forward-return data is `inconclusive`
- positive median 14/30 bar forward relative return plus acceptable hit rate and drawdown can be `useful`
- mixed evidence is `watchlist`
- weak median, poor hit rate, or poor drawdown is `fragile`

Means are secondary because meme returns are fat-tailed. A single massive winner should not promote a weak rule.

## Promotion Gates

A signal, setup event, state model, or score candidate can be promoted only if it:

- improves median 14 or 30 bar forward relative return
- improves or preserves hit rate
- does not materially worsen median drawdown
- survives symbol and calendar-cluster concentration checks
- works in first-half and second-half samples
- beats simple baselines where applicable
- is versioned side by side against the incumbent
- has a written promotion note

Promotion notes should include:

```text
what changed
why it changed
evidence delta
what got worse
affected modes
affected reports
TradingView interpretation impact
whether the old version remains available
```

## Fragility Rules

A result should be demoted if it depends on:

- one symbol
- one month or calendar cluster
- one huge outlier
- overlapping events counted as independent evidence
- one benchmark construction choice
- a hand-picked threshold
- a good average with poor median
- a better return with much worse drawdown

## Research Backlog

Documented but deferred:

- ex-target basket evidence reruns
- universe survivorship controls
- full cluster-bootstrap confidence intervals
- Benjamini-Hochberg FDR
- White Reality Check
- Hansen SPA
- Romano-Wolf stepwise testing
- CSCV / Probability of Backtest Overfitting
- Deflated Sharpe
- ML/probability calibration
- transition probabilities

These are real issues, but adding them before the simple evidence layer is stable would create false precision.

## Practical Success Criteria

Layer 7 is doing its job if:

- event outcomes use shared math
- event records include entry lag and cooldown
- reports show concentration risk
- Obsidian reports include a plain-language verdict
- research outputs can say `fragile` even when a table looks exciting
- future score/state/signal changes need evidence before promotion
- Layer 8 multi-timeframe logic has a strong referee before complexity increases
