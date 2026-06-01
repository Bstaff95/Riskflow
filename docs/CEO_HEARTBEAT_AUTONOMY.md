# CEO Heartbeat Autonomy

This document is the operating contract for Codex-supervised Riskflow CEO
heartbeat runs.

Use it when the user asks Codex to run Riskflow autonomously for hours, overnight,
or until stopped. The heartbeat operator is accountable for executive judgment.
The Python command is only the executor.

## Mission

Riskflow is a local research lab for improving a market-structure indicator. CEO
mode should improve the company behind the indicator: the evidence process, the
research engine, the data hygiene, the product translation layer, the reporting
layer, and the next-decision quality.

The product goal is not a buy/sell indicator. The product goal is a clearer
interpreter of:

- relative strength and weakness;
- warning and blocker conditions;
- bullish permission;
- invalidation;
- reset quality;
- path quality;
- gradient interpretation;
- cross-asset and regime usefulness;
- archive and do-not-repeat knowledge.

Production formulas, Pine/TradingView defaults, production states, rankings,
scores, alerts, and `core_signal_v0` must not change without explicit user
approval in the active thread.

## Prime Directive

Every heartbeat wake must follow this loop:

```text
inspect -> diagnose -> execute one bounded action -> audit -> report
```

Do not optimize for activity. Optimize for compounding evidence and better
decisions.

A wake counts as progress only if it produces at least one of:

- evidence that changes a belief's confidence, product role, or blocker status;
- a cleaner separation between permission, blocker, invalidation, reset quality,
  gradient interpretation, path quality, or archive;
- a completed validation, decomposition, control, or champion/challenger action;
- a new or improved research command that removes a repeated manual bottleneck;
- a queue decision: promote, refine, broaden, pair, invert, archive, or
  agent_review;
- an exact capability gap with acceptance criteria;
- a stop decision with a clear reason.

These do not count as progress:

- running more loops with the same conclusion;
- repeating the same candidate family without belief movement;
- same-sample parameter tuning labeled as validation;
- queue generation without evidence impact;
- a higher metric caused only by narrower sample-derived filters;
- a report that does not produce a next decision;
- product excitement without validation;
- ignoring `capability_gap.yaml` or `ceo_self_audit.yaml`.

## Canonical Command Flow

Initial setup:

```bash
PYTHONPATH=src python3 -m riskflow ceo plan \
  --run-id <run_id> \
  --objective bullish-positive
```

Every heartbeat wake:

```bash
git status --short

PYTHONPATH=src python3 -m riskflow ceo heartbeat-status \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo status \
  --run-id <run_id> \
  --show-lab-status

PYTHONPATH=src python3 -m riskflow ceo execute-next \
  --run-id <run_id> \
  --objective bullish-positive \
  --apply
```

Manual stop:

```bash
PYTHONPATH=src python3 -m riskflow ceo stop \
  --run-id <run_id> \
  --reason user_requested
```

Final report:

```bash
PYTHONPATH=src python3 -m riskflow ceo report --run-id <run_id>
```

Do not bypass `ceo execute-next` during heartbeat mode. Do not manually run
`ceo run-block`, `lab-ops run`, or `lab-loop run-supervised` unless
`execute-next`, a capability gap, or the active user explicitly requires that
specific command.

Reason: `execute-next` binds the latest CEO decision to the matching action. If
the decision is `run_champion_challenger`, it runs champion/challenger work. If
the decision is unsupported, it writes `capability_gap.yaml` instead of silently
running another generic research block.

## Required Inspection Artifacts

Before acting, inspect the current state enough to understand whether it is safe
and useful to continue.

CEO artifacts:

```text
reports/ceo_runs/<run_id>/heartbeat_status.yaml
reports/ceo_runs/<run_id>/executive_decision_packet.md
reports/ceo_runs/<run_id>/binding_action_result.yaml
reports/ceo_runs/<run_id>/ceo_action_ledger.jsonl
reports/ceo_runs/<run_id>/ceo_self_audit.yaml
reports/ceo_runs/<run_id>/capability_gap.yaml
reports/ceo_runs/<run_id>/product_delta_scoreboard.yaml
reports/ceo_runs/<run_id>/champion_challenger_action_plan.yaml
reports/ceo_runs/<run_id>/champion_challenger_results.yaml
reports/ceo_runs/<run_id>/risk_register.yaml
reports/ceo_runs/<run_id>/knowledge_graph_delta.yaml
```

Lab artifacts:

```text
reports/lab_ops/<lab_run_id>/latest_status.yaml
reports/lab_ops/<lab_run_id>/run_manifest.yaml
reports/lab_ops/<lab_run_id>/run_journal.jsonl
reports/lab_ops/<lab_run_id>/governance/block_*/lane_assignment.yaml
reports/lab_ops/<lab_run_id>/governance/block_*/validation_decision.yaml
reports/lab_ops/<lab_run_id>/governance/block_*/research_map.yaml
reports/lab_ops/<lab_run_id>/governance/block_*/blocker_audit.yaml
```

If generated artifacts contradict each other, stop and report the contradiction
instead of continuing.

## Autonomy Levels

### Green: May Do Autonomously

Codex may do these without asking:

- inspect CEO, lab-ops, director, meta, governance, and research-map state;
- run `ceo execute-next`;
- run bounded research blocks only through `execute-next`;
- run champion/challenger shadow comparisons;
- generate and validate research queues;
- build or improve research-only commands;
- add tests for research infrastructure;
- write generated reports under ignored report paths;
- create chart-review queues or galleries;
- run tests and compile checks;
- consult agents for critique, architecture, research strategy, or audit;
- use online research for methodology, then convert it into local safeguards;
- update docs that describe implemented research workflow changes.

### Yellow: May Do, But Must Flag Clearly

Codex may do these, but must report them explicitly:

- change research strategy;
- build new research infrastructure;
- create new queue families;
- run long research batches;
- update curated docs or Obsidian summaries;
- recommend data import or freshness work;
- archive major branches;
- propose product-facing sidecars.

### Red: Requires Explicit User Approval

Codex must not do these without explicit user approval:

- change `core_signal_v0`;
- change production indicator formulas;
- change Pine or TradingView defaults;
- change production states, scores, rankings, or alerts;
- promote an L4/L5 candidate into production behavior;
- commit or push;
- delete data, reports, queues, or ledgers;
- overwrite curated Obsidian notes;
- claim a setup is validated without fresh, withheld, or frozen-spec evidence.

## Decision Handling

Map CEO decisions to heartbeat behavior:

```text
run_champion_challenger
  -> run execute-next; inspect champion_challenger_results.yaml.

continue_governed_research
  -> run execute-next; this may run one bounded governed block.

patch_research_infra
  -> run execute-next; if a capability gap appears, patch research infra only.

broaden_hypothesis_source
  -> run execute-next; prefer director, Obsidian, chart-review, or agent-derived sources.

request_fresh_data
  -> stop unless fresh data can be imported safely under the data-import workflow.

stop_true_blocker
  -> stop and report the blocker.

stop_requested
  -> stop and do not clear stop files without user approval.
```

Choose exactly one main action per heartbeat. Do not run a chain of unrelated
commands just because the repo has tools available.

## Handling Capability Gaps

`capability_gap.yaml` is not failure. It is an instruction to build missing
research infrastructure.

When `capability_gap.yaml` exists:

1. Read `missing_capability`.
2. Read `reason`.
3. Read `required_command`.
4. Read every `acceptance_criteria` item.
5. Confirm `forbidden_changes`.
6. Patch only research infrastructure, tests, and docs.
7. Run focused tests.
8. Rerun `ceo execute-next`.
9. Inspect `binding_action_result.yaml`.

Do not continue running generic research blocks while a capability gap remains
unresolved.

Good reasons to build a new command:

- the same inspection is being done manually every cycle;
- CEO mode cannot execute its own decision;
- the lab cannot distinguish process failure from hypothesis failure;
- queue generation requires repeated manual synthesis;
- reports do not answer the next executive decision;
- validation, freshness, or product-delta checks are too manual;
- prior commands cannot express the required research action.

Bad reasons to build a new command:

- a hypothesis failed;
- results are frustrating;
- a report looks unimpressive;
- automation feels better than clearer evidence.

Before building a command, define:

- input artifacts;
- output artifacts;
- non-production guarantee;
- pass/fail tests;
- how it improves the next decision.

## Self-Audit And No-Progress Rules

After every `execute-next`, inspect:

```text
reports/ceo_runs/<run_id>/binding_action_result.yaml
reports/ceo_runs/<run_id>/ceo_action_ledger.jsonl
reports/ceo_runs/<run_id>/ceo_self_audit.yaml
```

A wake made no meaningful progress if:

- `binding_action_result.status` is `blocked`, `capability_gap`, or
  `no_candidates`;
- `meaningful_progress: false`;
- the same decision repeats across recent ledger entries;
- no new candidates, validation, map movement, command, or rejection occurred;
- the same capability gap persists unchanged;
- latest lab `stop_reason` repeats without a new queue, map, or action;
- the runner produces artifacts but no decision.

Thresholds:

```text
2 no-progress wakes on same decision -> fix capability or change strategy.
3 no-progress wakes on same decision -> stop and report the no-progress pattern.
```

If `ceo_self_audit.yaml` says `intervention_required: true`, the next wake must
not run another generic block. It must resolve the gap, broaden the source,
request fresh data, or stop.

## Candidate Validation Contract

Every product-facing idea is a shadow candidate until validated.

Candidate classes:

- `shadow_grammar_candidate`;
- `shadow_blocker_candidate`;
- `shadow_permission_candidate`;
- `shadow_invalidation_candidate`;
- `shadow_gradient_candidate`;
- `shadow_score_candidate`;
- `shadow_state_candidate`;
- `shadow_alert_candidate`.

Each candidate must eventually have:

```yaml
candidate_id:
candidate_type:
product_role:
source_belief_id:
frozen_spec_path:
champion:
challenger:
primary_metric:
secondary_metrics:
required_controls:
validation_status:
promotion_blockers:
decision:
```

Validation levels:

```text
V0_idea
V1_encoded
V2_discovered
V3_attributed
V4_frozen_validated
V5_challenger_winner
V6_sidecar_ready
V7_product_candidate
```

No heartbeat may move a candidate directly from `V2_discovered` to production
work.

## Champion/Challenger Rules

Every product-facing candidate must challenge a specific incumbent.

Champions:

- signal grammar: current `core_signal_v0` behavior and existing grammar
  sidecars;
- scores: `opportunity_score_v0`, `trader_score_v0`, and simple ranking
  baselines;
- states: `state_model_v0`;
- blockers and permissions: blocker-absent and permission-absent controls;
- gradient interpretation: current oscillator and gradient behavior without the
  candidate.

Decision shape:

```yaml
decision: promote | hold | demote | reject | archive
decision_reason:
champion_compared:
challenger_result:
delta_vs_champion:
required_next_evidence:
production_effect: none
```

Promotion requires:

- beats champion for the declared product role;
- survives frozen or fresh validation;
- does not alias a simpler rule;
- does not add unacceptable complexity;
- has a clear product role;
- has no unresolved governance blocker.

Rejection should be aggressive when:

- evidence is same-sample only;
- there is no edge over champion;
- diversity is weak;
- missed-opportunity cost is high;
- score buckets are non-monotonic;
- state labels flip-flop;
- blocker logic blocks too much upside;
- gradient candidate is visually confusing;
- result depends on one cluster, symbol, timeframe, lag, or cooldown.

## Fresh/Frozen Separation

Discovery may search. Validation may not edit the rule.

Discovery:

- parameter search allowed;
- same-sample evidence allowed;
- queue expansion allowed;
- output label: `same_sample_discovery`.

Frozen validation:

- one frozen spec;
- no threshold edits;
- no new filters after seeing results;
- no selective timeframe changes;
- uses withheld time, withheld symbols, withheld clusters, or newly imported
  data;
- output label: `frozen_validation`.

Fresh-data rule:

```yaml
if data_used_to_design_candidate: cannot_be_final_proof
```

A candidate that changes after validation failure returns to discovery.

## Mandatory Metrics

All candidates:

- sample size;
- unique symbols;
- event clusters;
- timeframe coverage;
- median forward relative return;
- hit rate;
- MFE/MAE;
- median max drawdown;
- edge versus unconditional;
- edge versus same-cluster;
- matched-null result;
- time-split result;
- concentration score;
- stale-data flag;
- role clarity;
- complexity cost.

Blockers:

- harm avoided;
- missed-upside cost;
- false-block rate;
- drawdown reduction;
- blocker-active versus blocker-absent delta;
- invalidation versus permission distinction.

Scores:

- top-bucket versus lower-bucket spread;
- monotonic bucket behavior;
- rank IC;
- drawdown spread;
- turnover/churn;
- concentration;
- incremental value over `opportunity_score_v0`.

States:

- forward-return separation by state;
- transition usefulness;
- duration stability;
- flip-flop rate;
- occupancy distribution;
- explanation quality;
- difference from `state_model_v0`.

Gradient and grammar:

- false-positive reduction;
- path-quality improvement;
- visual-review result;
- additive value beyond simpler primitives;
- relationship to existing oscillator behavior.

## Choosing The Next Action

At every heartbeat, choose exactly one next action:

```yaml
next_action:
  type:
    run_next_block
    decompose_candidate
    validate_frozen_candidate
    audit_blocker
    broaden_idea_pool
    request_fresh_data
    request_visual_review
    write_candidate_packet
    archive_redundant_path
    build_missing_command
    stop_governance_blocked
    stop_research_saturated
  reason:
  target_candidate_ids:
  expected_output:
```

Priority order:

1. If a candidate is `V3_attributed`, run frozen validation.
2. If blocker evidence exists, run blocker audit before product interpretation.
3. If a candidate is `V2_discovered`, run decomposition or controls.
4. If validation fails, demote or archive before more tuning.
5. If no belief changed for two heartbeats, broaden, build missing machinery, or
   stop.
6. If data is stale or exhausted, request fresh data.
7. If a candidate reaches `V5`, write a candidate packet, not a production
   change.
8. If governance blocks all actions, stop clearly.

## Agent And Online Research Checkpoints

Consult agents when the decision is strategic, ambiguous, or high leverage.

Use agents after:

- 3 full epochs;
- a major survivor appears;
- 2 dead epochs;
- before retiring a major branch;
- before L4/L5 promotion;
- when novelty falls below threshold;
- when deciding whether to broaden, validate, or stop.

Preferred roles:

- skeptical quant auditor;
- pragmatic maintainer;
- outside-the-box startup operator;
- product/indicator translator;
- data-quality auditor.

Agent output is recommendation, not proof.

Use online research when methodology matters and local knowledge may be stale or
incomplete. Good topics include false discovery control, backtest overfitting,
adaptive testing bias, active learning, validation design, and research process
metrics. Convert methodology into local tests and safeguards before using it.

## Stop Conditions

Stop or pause autonomous work when:

- `stop.request` exists;
- `true_blocker: true`;
- production behavior would need to change;
- `production_change_allowed: true`;
- formula parity is uncertain;
- data is missing or stale and no honest fallback exists;
- all queues are exhausted and no valid next experiment exists;
- the same process failure repeats without a tooling fix;
- tests fail and the failure is not understood;
- generated reports contradict each other;
- evidence artifacts are missing or malformed;
- the lab cannot map a claim back to exact evidence files;
- capability gap requires non-research changes;
- repeated no-progress threshold is hit;
- user asks to stop.

Weak bullish results, warning dominance, queue exhaustion, and need for new
hypotheses are not true blockers by themselves.

## Long-Run Cadence

For 8+ hour work, use recurring heartbeat wakes instead of one blind script.
Each wake runs at most one bounded executive action.

Every 30 to 90 minutes, create or update a local outcome report.

Every 5 to 10 epochs, ask:

- Did beliefs change?
- Did validation progress?
- Did uncertainty shrink?
- Did duplicate work increase?
- Did product relevance improve?
- Is the next action still the right action?

If the same blocker appears repeatedly, stop blind execution and build or
recommend the missing machinery.

## Heartbeat Report Format

Each wake should end with this summary:

```text
CEO Heartbeat Outcome

Run id:
Lab run id:
Main action:
Result:
Meaningful progress: yes/no
Evidence:
What improved:
What failed or stalled:
Product relevance:
Files/artifacts:
Tests/checks:
Capability gap: yes/no
Self-audit intervention: yes/no
Next recommended action:
Approval needed:
```

Keep the report direct. Do not overstate findings.

## North Star

Wrong overnight behavior:

```text
run many loops -> produce long report
```

Right overnight behavior:

```text
find bottleneck -> improve machinery/evidence -> validate or archive -> report decision -> repeat
```

Riskflow gets better when each heartbeat leaves behind one of:

- stronger evidence;
- a better queue;
- a validated or falsified belief;
- a clearer product translation;
- fresher data;
- a better research command;
- a better test;
- a cleaner handoff.

If none of those happened, the heartbeat should say so plainly. The worst
failure mode is silent fake progress.
