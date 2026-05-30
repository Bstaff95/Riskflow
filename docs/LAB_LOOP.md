# Riskflow Lab Loop

This document is the durable operating model for the Riskflow research lab.

The lab should run as a bounded autonomous research system, not an open-ended
idea grind. Its job is to discover, test, and rank Riskflow indicator structures
that improve trade selection versus the relevant basket.

## Mission

Find Riskflow structures that improve:

- long-entry quality;
- avoidance and weakness warnings;
- timing;
- invalidation;
- gradient or visual interpretation after evidence exists.

The lab must keep production formulas, states, rankings, scores, and
TradingView defaults unchanged unless a future promotion decision explicitly
changes that policy.

## Research Tracks

### Warning And Avoidance

This track finds cases where Riskflow should say: do not chase this.

Current examples:

- relative failed breakout;
- lower-high rollover after leadership;
- failed strength acceptance;
- gradient fade after strength.

Warnings matter even if they are not buy signals. They can become invalidation,
cooldown, downgrade, or no-chase logic.

### Bullish Setup Journeys

Bullish trade setups should be tested as staged journeys, not isolated one-bar
events.

Canonical journey:

```text
weakness/compression -> repair -> reclaim -> retest/hold -> continuation
```

Each staged setup should define:

- `stage_0_context`
- `stage_1_repair`
- `stage_2_trigger`
- `stage_3_confirmation`
- `stage_4_invalidation`

The lab should measure whether the journey improves trade quality, not only
whether the final trigger has a positive median forward return.

### Entry And Invalidation

Every useful setup should eventually produce both:

- an entry trigger;
- an invalidation trigger.

Example:

```text
Entry: compression + relative repair + viscosity reclaim + retest hold
Invalidation: reclaim fails, gradient fades, relative breakout fails, or signal loses viscosity
```

Warning rules should feed this track. A bullish setup can be allowed, downgraded,
blocked, or reset based on whether warning grammar is active.

## Epoch Loop

The canonical unit of research is an epoch, not an open-ended loop.

An epoch is 5 to 10 completed tests followed by a required Codex supervisor
review. The Python runner executes evidence; Codex decides what the evidence
means and what should run next.

Every epoch should follow the same order:

1. Pull ranked hypotheses from `research/lab_loop/hypothesis_queue.yaml`.
2. Run 5 to 10 bounded tests across `1d`, `12h`, `4h`, and `1h`.
3. Run strict validation:
   - time split;
   - unconditional baseline;
   - same-timeframe and same-cluster baseline;
   - matched random null;
   - symbol and cluster concentration;
   - entry-lag sensitivity;
   - cooldown sensitivity.
4. Write epoch artifacts:
   - manifest;
   - tested hypotheses;
   - concept scoreboard;
   - branch decisions;
   - next-epoch suggestions.
5. Codex reviews false positives, missed winners, and boundary cases when a survivor is
   promising or confusing.
6. Assign each concept exactly one branch decision:
   - promote;
   - refine;
   - broaden;
   - pair;
   - invert;
   - archive;
   - agent_review.
7. Update the next epoch intentionally. Do not treat same-sample refinements as
   validation.

## Research Gates

A strict survivor does not move straight to product translation. The runner now
appends research-gate follow-ups before more narrow optimization:

- attribution gates: same setup positive and negative, warning active/absent/cleared
  where applicable, and setup-only controls;
- validation gates: same frozen rule shape at alternate entry lags and cooldowns;
- direction gates: opposite-direction controls to confirm the sign of the edge.

Runtime queue items may carry their own `timeframes`, `entry_lag_bars`, and
`cooldown_bars` overrides. This lets a single epoch mix discovery, attribution,
and validation tests without changing production formulas or TradingView
defaults.

Promotion meaning after this change:

- strict survivor means "advance to gates";
- attribution survivor means "the cause is clearer";
- validation survivor means "candidate can move toward fresh-data review";
- no candidate becomes gradient or indicator logic until it has passed those
  gates and a Codex supervisor review.

Open-ended `lab-loop run` remains available for controlled testing, but the
preferred research mode is `lab-loop run-epoch`.

## Agent Checkpoints

Use agents after evidence accumulates, not after every run.

Trigger an agent checkpoint after:

- 3 full loops;
- a major survivor appears;
- 2 or 3 dead loops;
- a proposed research-direction change;
- a candidate is being considered for indicator or gradient logic.

Recommended agent roles:

- quant skeptic: overfit checks, null quality, sample size, concentration;
- indicator translator: whether findings map cleanly to Riskflow primitives and
  gradient behavior;
- trade-setup designer: whether tested patterns resemble usable setups;
- research operator: what to test next to maximize learning per run.

Checkpoint inputs should be small:

- last 3 loop summaries;
- current survivors;
- current failures;
- hypothesis queue;
- data freshness;
- proposed next loop.

## Promotion Ladder

Use this ladder for every concept.

```text
L0_registered
L1_encoded
L2_discovered
L3_strict_survivor
L4_fresh_data_survivor
L5_indicator_candidate
```

Default interpretation:

- L0 and L1 are ideas and definitions.
- L2 is discovery evidence only.
- L3 is useful enough to keep testing.
- L4 is the first level that can seriously inform product behavior.
- L5 can be considered for gradient, warning, marker, score, or Pine work.

Demote or archive a candidate when it:

- survives only one fragile lag or cooldown setting;
- fails time split;
- concentrates in one symbol, cluster, or period;
- aliases a stronger simpler concept;
- requires too many sample-derived filters;
- improves median return while worsening drawdown or trade path;
- cannot be explained cleanly.

## Outcomes

Median terminal forward relative return is not enough for trade setup research.

For entries, measure:

- max favorable excursion;
- max adverse excursion;
- time to first upside;
- time underwater before upside;
- hit rate after assumed costs;
- relative return versus basket;
- drawdown-adjusted relative return;
- failure before confirmation;
- retest versus no-retest performance;
- symbol and cluster concentration;
- lag and cooldown sensitivity.

For warnings, measure:

- downside avoidance;
- post-warning underperformance;
- false-warning rate;
- whether the warning improves entry filtering or invalidation;
- how long the warning remains active.

## Current Saved Learnings

Recent all-component research encoded 99 indicator-behavior concepts into
Riskflow-native measurable ideas. The broad run found far more useful warning
evidence than positive entry evidence.

The strongest current warning candidate is daily relative failed breakout.
It is useful enough to keep testing, but not ready for production or gradient
logic because current stress testing shows it is sensitive to entry lag and
cooldown. Treat it as an L2/L3 warning candidate pending fresh-data validation.

The main correction for future bullish research is to test setup journeys
instead of single trigger events.

## Standard Commands

Supervised epoch runner:

```bash
PYTHONPATH=src python3 -m riskflow lab-loop run-epoch \
  --queue research/lab_loop/hypothesis_queue.yaml \
  --timeframes 1d 12h 4h 1h \
  --epoch-size 5 \
  --strict-referee \
  --resume
```

Open-ended runner:

```bash
PYTHONPATH=src python3 -m riskflow lab-loop run \
  --queue research/lab_loop/hypothesis_queue.yaml \
  --timeframes 1d 12h 4h 1h \
  --max-loops 100 \
  --max-hours 4 \
  --strict-referee \
  --resume
```

Inspect the latest run:

```bash
PYTHONPATH=src python3 -m riskflow lab-loop status
PYTHONPATH=src python3 -m riskflow lab-loop next
PYTHONPATH=src python3 -m riskflow lab-loop validate-queue
PYTHONPATH=src python3 -m riskflow lab-loop epoch-summary
PYTHONPATH=src python3 -m riskflow lab-loop concept-scoreboard
```

The runner writes a process-quality checkpoint every 5 completed loops by
default. Checkpoints ask whether the research is actually serving the mission,
not only whether variants are surviving:

- are we finding trade-selection evidence;
- are we testing both warnings and bullish setup journeys;
- are we learning invalidation/filtering value;
- are we over-refining one lineage;
- are failures informative or just repetitive;
- is the runner reliable enough to keep scaling.

Checkpoint reports live under each session's `checkpoints/` directory, and the
latest status file links the most recent checkpoint.

Epoch reports live under each session's `epochs/` directory. The durable concept
scoreboard lives at `research/lab_loop/concept_scoreboard.yaml`.

Meta-supervised runs add a deterministic supervisor after each epoch. The
supervisor is not an indicator change and does not modify production formulas.
It reads the latest epoch, queue, state, and concept scoreboard, then writes
auditable artifacts:

- `supervisor_input.json`;
- `supervisor_decisions.yaml`;
- `queue_patch.yaml`;
- `supervisor_summary.md`;
- `research/lab_loop/evidence_ledger.yaml`.

Use a dry-run first when changing supervisor policy:

```bash
PYTHONPATH=src python3 -m riskflow lab-loop supervise-epoch --dry-run
```

Run repeated self-improving epochs:

```bash
PYTHONPATH=src python3 -m riskflow lab-loop run-supervised \
  --epochs 50 \
  --epoch-size 5 \
  --strict-referee \
  --strict-null-iterations 1000 \
  --timeframes 1d 12h 4h 1h \
  --resume
```

The v1 supervisor is deterministic and auditable. It prioritizes strict-survivor
validation gates, reserves space for bullish setup work when available, caps
same-root dominance in the next epoch plan, cools over-deep non-validation
lineages, and records evidence decisions without changing indicator behavior.

Discovery:

```bash
python3 -m riskflow indicator-behavior-search --timeframes 1d 12h 4h 1h
```

Strict grammar validation:

```bash
python3 -m riskflow grammar-search \
  --config configs/meme_universe.yaml \
  --timeframes 1d 12h 4h 1h \
  --strict-referee
```

Verification after code changes:

```bash
python3 -m pytest
git diff --check
PYTHONPYCACHEPREFIX=/tmp/riskflow_pycache python3 -m compileall -q src
```
