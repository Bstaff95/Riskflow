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

## Bullish-Positive Objective

Use `--objective bullish-positive` when the mission is to find actual long setup
evidence rather than warnings found during bullish-looking tests.

In this mode, a `bullish_setup` hypothesis cannot promote just because it found
a strict survivor. It must pass a bullish evidence contract:

- direction is `positive`;
- terminal forward relative median is positive;
- edge versus unconditional and same-cluster baselines is positive;
- matched-null and time-split validation pass;
- event diversity clears the bullish thresholds;
- the path is tradeable, with positive MFE and acceptable MFE/MAE.

The bullish contract is tiered so the lab can learn from asymmetric meme-coin
paths without promoting them too early:

- `blocker`: bullish-looking setup produced strict negative evidence;
- `archive`: no useful positive rows or no tradeable path;
- `path_watchlist`: path quality exists but strict validation is missing;
- `asymmetric_candidate`: positive relative path and MFE/MAE are strong while
  hit rate remains below the normal clean-entry threshold;
- `strict_validated`: full bullish contract pass and the only tier that sets
  `passes_bullish_contract: true`.

If a bullish-looking setup produces strict negative evidence, the loop treats it
as a failed setup blocker, not as a bullish promotion. Each bullish loop writes
`bullish_evidence.yaml`, and each epoch with bullish evidence writes
`bullish_leaderboard.csv`.

Bullish queue items may add optional metadata:

- `claim_type`: `bullish_entry`, `bullish_permission`, `warning_blocker`, or
  `control`;
- `setup_class`: a short family label, such as `post_underperformance`;
- `path_objective`: local thresholds for event diversity, MAE, or MFE/MAE;
- `branch_budget`: local lineage caps for the supervisor.

When the runtime queue is exhausted under `--objective bullish-positive`, the
supervisor reseeds bullish near-misses before warning-only branches. A near-miss
can reseed only when it has a bullish evidence file, passes the path gate, and
contains positive useful rows. It still does not promote unless the full bullish
contract passes.

Generated follow-ups carry canonical lineage metadata (`root_id`,
`lineage_fingerprint`, and reseed signatures) so the supervisor can cool weak
families and skip duplicate reseeds without relying on truncated IDs. A long run
that stops with no runnable hypotheses should be treated as evidence exhaustion,
not as permission to keep brute-forcing the same queue.

The bullish supervisor now treats discovery as a portfolio. For a 5-loop epoch,
it prefers three distinct new bullish setup roots, one control/blocker, and one
validation or refinement slot when those candidates exist. A weak family that
keeps producing path-gate-only evidence without a bullish contract pass is cooled
instead of recursively reseeded. Non-contract children may seed one bounded
follow-up from the original family, but later-generation near-misses must add a
new setup class or wait for fresh evidence.

Example:

```bash
PYTHONPATH=src python3 -m riskflow lab-loop run-supervised \
  --objective bullish-positive \
  --epochs 20 \
  --epoch-size 5 \
  --strict-referee \
  --strict-null-iterations 1000 \
  --timeframes 1d 12h 4h 1h \
  --resume
```

Open-ended `lab-loop run` remains available for controlled testing, but the
preferred research mode is `lab-loop run-epoch`.

## Obsidian Knowledge Graph Input

Use Obsidian setup-journey notes when the lab needs new bullish hypotheses from
human visual knowledge rather than another same-sample refinement.

Workflow:

```bash
PYTHONPATH=src python3 -m riskflow obsidian-kg validate
PYTHONPATH=src python3 -m riskflow obsidian-kg compile-queue \
  --direction bullish \
  --include-research-grammar \
  --max-research-families 80
PYTHONPATH=src python3 -m riskflow lab-loop run-supervised \
  --objective bullish-positive \
  --queue research/lab_loop/obsidian_candidate_queue.yaml \
  --epochs 10 \
  --epoch-size 5 \
  --strict-referee
```

The compiler reads curated `setup_journey` notes and writes a normal lab-loop
queue plus generated grammar grids. Each compiled journey includes full setup,
trigger-only, permission, blocker-present, and direction-control tests. Obsidian
chooses what to test; the Python evidence engine decides whether it is true.
When the vault has too few curated setup journeys, `--include-research-grammar`
adds compact one-family bullish candidates from prior `research/grammar` grids
so the supervisor has enough distinct setup classes to run broad discovery.

For the current bullish-entry mission, prefer the targeted queue before another
broad run:

```bash
PYTHONPATH=src python3 -m riskflow obsidian-kg compile-targeted-bullish-queue
PYTHONPATH=src python3 -m riskflow lab-loop validate-queue \
  --queue research/lab_loop/targeted_bullish_candidate_queue.yaml
```

This queue focuses on regime-confirmed reclaim, deeper reset reclaim,
parent-context failed-weakness permission/blocker logic, and fresh-leader
follow-up as a filter rather than a standalone long trigger.

## Lab Director

The meta-supervisor enforces queue hygiene. The lab director is the native
research-intelligence layer above it. It turns completed loop artifacts into:

- an evidence mart;
- a belief graph;
- an audited next-experiment plan;
- an optional director-designed queue.

Use it after a 5-10 epoch block, a queue-exhaustion stop, or any major
asymmetric/strict finding:

```bash
PYTHONPATH=src python3 -m riskflow lab-director inspect
PYTHONPATH=src python3 -m riskflow lab-director plan-next \
  --objective bullish-positive
```

`inspect` and `plan-next` write generated artifacts under
`reports/lab_director/` and do not mutate the runtime queue. To intentionally
create the next runnable queue:

```bash
PYTHONPATH=src python3 -m riskflow lab-director plan-next \
  --objective bullish-positive \
  --max-new-hypotheses 30 \
  --apply
PYTHONPATH=src python3 -m riskflow lab-loop validate-queue \
  --queue research/lab_loop/director_candidate_queue.yaml
```

For a closed-loop run, use:

```bash
PYTHONPATH=src python3 -m riskflow lab-director run \
  --objective bullish-positive \
  --queue research/lab_loop/director_candidate_queue.yaml \
  --epochs 20 \
  --epoch-size 5 \
  --director-checkpoint-epochs 2 \
  --strict-referee \
  --resume \
  --apply
```

Director rules:

- evidence creates beliefs, not product truth;
- `asymmetric_candidate` findings become decomposition/control tests, not
  gradient or indicator changes;
- strict survivors require fresh/frozen validation before product translation;
- every director queue is audited before it can be applied;
- no director output may change production formulas, states, scores, rankings,
  or TradingView defaults.

The current first use case is decomposing the `deep_reset_regime_reclaim_entry`
lead from the targeted bullish pilot: reset depth, reclaim timing, compression,
warning absence, parent context, timeframe transfer, entry lag, and cooldown.

## Meta-Research And Lab Ops

`lab-meta` scores whether the research process itself is learning. It reads the
director evidence mart, belief graph, plan, and audit, then writes:

- `process_scorecard.yaml`;
- `process_diagnosis.yaml`;
- `process_intervention_plan.yaml`;
- `meta_audit.yaml`;
- `meta_research_report.md`.

Use it to decide whether the lab should continue, decompose, validate, broaden,
add controls, request fresh data, request visual review, or stop saturated
research:

```bash
PYTHONPATH=src python3 -m riskflow lab-meta inspect
PYTHONPATH=src python3 -m riskflow lab-meta plan \
  --objective bullish-positive
PYTHONPATH=src python3 -m riskflow lab-meta replay \
  --snapshot reports/lab_director/<session>
```

The meta layer measures process quality only. It does not promote product logic
and it does not change production formulas, states, scores, rankings, or
TradingView defaults.

`lab-ops` is the long-run wrapper for unattended research. It creates a
run-scoped runtime queue/state directory, checkpoints every director block,
runs `lab-meta`, and stops with explicit machine-readable reasons:

```bash
PYTHONPATH=src python3 -m riskflow lab-ops plan \
  --objective bullish-positive \
  --max-epochs 200 \
  --epoch-size 5

PYTHONPATH=src python3 -m riskflow lab-ops run \
  --objective bullish-positive \
  --max-epochs 200 \
  --epoch-size 5 \
  --director-checkpoint-epochs 2 \
  --strict-referee \
  --apply
```

For enterprise-style autonomous runs, use governed mode:

```bash
PYTHONPATH=src python3 -m riskflow lab-ops run \
  --objective bullish-positive \
  --max-epochs 200 \
  --epoch-size 5 \
  --director-checkpoint-epochs 2 \
  --strict-referee \
  --governed \
  --apply
```

Governed mode adds deterministic checkpoint artifacts for blocker audit,
research-lane assignment, validation governance, and a run-scoped research map.
It treats `request_fresh_data`, visual-review needs, and saturation as
lane-specific unless every valid lane is blocked or no runnable inventory
remains. It still does not change production formulas, states, scores,
rankings, Pine behavior, or TradingView defaults.

If governed mode finds open lanes but the director cannot add runnable work, it
attempts a lane-aware recovery queue before stopping. Recovery queues are
limited to research sidecars for reset quality, warning/blocker, and bullish
permission lanes, and write `recovery_queue_plan.yaml` plus `recovery_audit.yaml`
under the current governed checkpoint.

Generated ops artifacts live under `reports/lab_ops/` and run-scoped mutable
state lives under `research/lab_loop/autonomous_runs/`. These are generated
research artifacts, not production configuration.

## CEO Autopilot

`ceo` is the executive layer above governed `lab-ops`. Use it when Codex should
actively supervise Riskflow as a company-style research/product system rather
than launch one long script-governed run.

```bash
PYTHONPATH=src python3 -m riskflow ceo status --run-id <run_id> --show-lab-status
PYTHONPATH=src python3 -m riskflow ceo heartbeat-status --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo preflight-gate --run-id <run_id> --enforce-memory-delta
PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id <run_id> --objective bullish-positive --apply
PYTHONPATH=src python3 -m riskflow ceo stop --run-id <run_id> --reason user_requested
PYTHONPATH=src python3 -m riskflow ceo report --run-id <run_id>
```

Use `ceo execute-next --apply` as the canonical CEO dispatch path. Use
`ceo run-block` only when `execute-next`, a capability gap, or the active user
explicitly requires that lower-level governed research command.

The default CEO block is two supervised epochs of five loops each. After each
block, the CEO layer writes `reports/ceo_runs/<run_id>/` artifacts that separate
research-infra delta, understanding delta, chart-facing product delta, risk
register, knowledge-graph delta, and the executive decision packet. A block is
not considered useful merely because loops ran; it must improve one of those
buckets or stop with a clear reason.

For overnight supervision, use a thread heartbeat automation instead of a giant
Python loop. A heartbeat should wake Codex, inspect heartbeat status, trace
grade, replay, eval suite, guardrail audit, memory delta, approval state,
preflight gate, and the latest decision packet, then run at most one
`ceo execute-next --run-id <run_id> --apply`. The executor binds CEO decisions
to specific actions: champion/challenger decisions run product-delta
preparation, governed-research decisions run one bounded block, and unsupported
decisions write `capability_gap.yaml` instead of falling back to blind loop
execution.
The CEO layer writes
`reports/ceo_runs/<run_id>/heartbeat_status.yaml` after reviews and stop
requests. `ceo heartbeat-status` is read-only; it must not create a new
decision packet. `ceo stop` writes both
`reports/ceo_runs/<run_id>/stop.request` and
`research/lab_loop/autonomous_runs/<lab_run_id>/stop.request`, so a later
heartbeat can see the user-requested stop before launching more work.

For the full overnight operating contract, use
`docs/CEO_HEARTBEAT_AUTONOMY.md`. Future heartbeat prompts should point Codex to
that document instead of restating the whole policy in chat.

CEO mode may build sidecar and shadow product candidates, but product-facing
changes still require explicit promotion approval. It must not silently change
`core_signal_v0`, Pine/TradingView defaults, production scores, state labels, or
leaderboard ranking.

Binding CEO action artifacts:

- `binding_action_result.yaml`: the latest decision, action taken, command,
  outputs, and next allowed actions;
- `ceo_action_ledger.jsonl`: append-only action history for no-op and repeated
  decision audits;
- `ceo_self_audit.yaml`: repeated-decision/no-progress checks;
- `capability_gap.yaml`: exact missing research-infra command or executor when
  CEO mode cannot execute its own decision;
- `champion_challenger_results.yaml`: shadow candidate comparison readiness and
  missing metric-source gaps. This artifact is not production evidence unless it
  has exact metric sources.

Standalone governance tools are available for auditing existing director
artifacts:

```bash
PYTHONPATH=src python3 -m riskflow blocker-audit inspect
PYTHONPATH=src python3 -m riskflow lane-router assign
PYTHONPATH=src python3 -m riskflow lane-router recover
PYTHONPATH=src python3 -m riskflow validation-governance review
PYTHONPATH=src python3 -m riskflow research-map update
```

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
