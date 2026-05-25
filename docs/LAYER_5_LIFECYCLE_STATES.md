# Layer 5: Lifecycle States

Layer 5 turns raw Riskflow measurements into explainable market language.

Layer 3 answers:

> Is this asset gaining normalized strength?

Layer 4 answers:

> Is this strengthening asset a good setup right now?

Layer 5 answers:

> What lifecycle state is this asset in, why did Riskflow say that, and how stable is that label?

The end state for Layer 5 is a state inference layer. It should treat each state as a diagnosis inferred from observed traces, then test whether that diagnosis preserves useful information about future relative behavior.

## Core Principle

Lifecycle states are product language, not raw data.

That means they must be versioned, explainable, and hard to change accidentally. A state label can later drive leaderboards, TradingView labels, alerts, event studies, transition matrices, Obsidian reports, and user trust. Silent changes would corrupt interpretation.

## State Model V0

The active model is:

```text
state_model_v0
```

It is deterministic and rule-based. It is not a probabilistic truth engine.

Current primary state vocabulary:

- Unknown
- Dead Money
- Weak
- Compression
- Relative Accumulation
- Emerging Leader
- Confirmed Leader
- Overheated
- Distribution
- Breakdown

Riskflow should use exactly one primary state per asset per bar.

`state_model_v0` remains the active production state model until a side-by-side candidate proves it is better. Do not silently edit its meaning.

## State Research

State labels become useful only if assets in those states behave differently afterward.

The `state-research` command evaluates `state_model_v0` without changing production scans:

```bash
python3 -m riskflow state-research --config configs/meme_universe.yaml --timeframe 1d
```

Outputs:

```text
reports/state_research_summary.csv
reports/state_research_summary.html
reports/state_research_records.csv
reports/state_transition_matrix.csv
obsidian/reports/latest_state_research.md
```

The summary asks:

- How many observations does each state have?
- What were the 3/7/14/30 bar forward relative returns?
- What were the hit rates and drawdowns?
- How long did each state tend to last?
- What state usually came next?
- Are results concentrated in one symbol or one calendar cluster?

The transition matrix ignores same-state continuation. Duration is reported separately so a state can be persistent without pretending it transitioned to itself.

## Layer 5 Outputs

The state layer now owns these columns:

```text
state
state_model
state_confidence
state_reason
state_tags
```

`state` is the backward-compatible primary label.

`state_model` records which rule set produced the label.

`state_confidence` is a bounded 0-100 deterministic confidence score. It is not a probability. It means the current row fit the rule cleanly.

`state_reason` is a plain-language explanation of the selected state.

`state_tags` are secondary descriptors such as `compressed`, `above_viscosity`, `relative_positive`, `viscosity_reclaim`, or `rolling_over`.

## Primary State Versus Tags

Primary states should stay sparse and readable.

Secondary tags are where extra nuance belongs.

Example:

```text
state = Relative Accumulation
state_tags = compressed,relative_positive,signal_slope_rising,viscosity_reclaim
```

This avoids creating dozens of brittle states like:

```text
Compressed Relative Accumulation With Viscosity Reclaim
```

That kind of phrase can appear in reports later, but it should be composed from one state plus tags.

## Downstream Guardrails

Do not silently alter `state_model_v0`.

Future state changes should be added side by side:

```text
state_model_v1_candidate
```

A new state model can be promoted only after event studies show that it improves forward relative-return interpretation, false-positive control, or user-facing clarity.

Promotion gates for `state_model_v1_candidate`:

- improve median 14 or 30 bar forward relative return for actionable states
- improve or preserve hit rate
- reduce false positives for `Emerging Leader` and `Confirmed Leader`
- avoid dependence on one symbol or one calendar cluster
- keep state duration reasonable and avoid noisy flip-flopping
- provide clear reasons and alternate states
- keep the primary state vocabulary stable unless a separate migration note says otherwise

Changing state semantics can affect:

- leaderboard sections
- opportunity score interpretation
- Trader Mode setup labels
- event-study triggers
- future Markov transition matrices
- future TradingView labels and alerts
- Obsidian report language

Because of that, every state change should come with tests and a short promotion note.

## What Layer 5 Does Not Build Yet

Layer 5 does not build:

- Markov chains
- transition probabilities
- historical analog search
- ML state classifiers
- multi-timeframe voting
- new TradingView UI

Research backlog:

- Evidence-weighted `state_model_v1_candidate` with `state_v1_candidate`, `state_v1_confidence`, `state_v1_alternate`, `state_v1_scores`, and `state_v1_reason`.
- HMM / hidden semi-Markov challengers for hidden regimes and duration-aware state research.
- Bayesian changepoint detection for transition alerts.
- Shapelets and ordinal patterns for path-shape detection.
- Recurrence, topology, and positive-geometry ideas for future rotation-graph research rather than v1 asset state labels.

Those are later layers. Layer 5 only creates the stable language that those layers will depend on.

## Practical Success Criteria

Layer 5 is doing its job if:

- every state has a reason
- every state is tied to a model id
- confidence is bounded and deterministic
- tags add nuance without exploding the primary state list
- current scan and event-study behavior stays backward compatible
- later research can compare state models without corrupting history
- state labels are evaluated by future relative behavior, not by how good they sound
