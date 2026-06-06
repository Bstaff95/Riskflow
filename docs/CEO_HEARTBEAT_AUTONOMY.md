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

True CEO mode is a governed operating system, not permission to do anything. It
allocates research budget across evidence, candidate validation, infrastructure,
memory quality, and product translation while preserving explicit user approval
for production changes.

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

The CEO should act as orchestrator, capital allocator, referee, memory editor,
and risk officer. It should stop repeated bad loops, not merely keep tools busy.

## Run Id And Runtime Authority

A CEO run is active only when generated runtime artifacts say it is active.
Obsidian maps, Prime checkpoints, and dated session notes are routing memory,
not runtime authority.

Before any CEO action, inspect `heartbeat_status.yaml`, `trace_grade.yaml`, and
`ceo_operating_dashboard.yaml` for the chosen `run_id`. If no `run_id` is
explicitly supplied and no single active run is verified, plan a fresh run id.

Stopped runs require explicit user approval before clearing stop files, mutating
runtime queues, or resuming. Smoke runs are test artifacts, not continuation
targets.

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

Every heartbeat wake starts with inspection:

```bash
git status --short

PYTHONPATH=src python3 -m riskflow ceo heartbeat-status \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo status \
  --run-id <run_id> \
  --show-lab-status

PYTHONPATH=src python3 -m riskflow ceo trace-grade \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo flight-dashboard \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo operating-dashboard \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo evidence-debt-register \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo approval-queue \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo executive-kpis \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo role-queue \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo replay \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo eval-suite \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo eval-fixtures \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo portfolio-allocator \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo mission-score \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo strategy-capital-dashboard \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo memory-delta \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo guardrail-audit \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo preflight-gate \
  --run-id <run_id> \
  --enforce-memory-delta

PYTHONPATH=src python3 -m riskflow ceo dispatch-receipt \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo blocker-stack \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo incident-register \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo repair-plan \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo artifact-coherence \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo resumption-brief \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo run-index \
  --limit 25
```

`ceo status` is the first quick-read command. In addition to lab progress and
true-blocker state, it surfaces the latest existing blocker stack, top blocker,
operating incident count, dispatch receipt status, safe-to-dispatch flag, and
the blocker stack's next repair command. It also prints resumption status and a
default handoff command; if the resumption brief is missing, that command is
`ceo resumption-brief`. When `repair_plan.yaml` exists, it also prints repair
plan status, runnable repair count, diagnostic refresh count, top repair, top
repair kind, and repair next command.

Only run the binding action when the heartbeat and trace grade do not indicate
`stop_requested`, a true blocker, a production-promotion gate, or an unresolved
self-audit intervention:

```bash

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

The final report should include the latest decision packet plus trace grade,
flight dashboard, operating dashboard, mission score, strategy capital
dashboard, decision quality, replay, eval suite, guardrail audit, preflight gate, dispatch
receipt, blocker stack, operating incident register, repair plan, action board,
operator brief, artifact coherence, resumption brief,
approval queue, executive KPIs, capability backlog, fresh/withheld validation
contract, role dispatch, promotion proposal, and evidence-debt links/status. It
is a handoff report, not approval to change production behavior.

For a fresh session or noisy-thread handoff, run `ceo resumption-brief` before
any action. It writes `resumption_brief.yaml` / `.md` and answers whether the
run is stopped, blocked by preflight, diagnostic-only, or safe for one bound
`execute-next --apply` action. It synthesizes existing trust artifacts; it does
not authorize product language or replace preflight.

If you are unsure which run should be inspected first, run `ceo run-index`
before choosing a run id. It writes `run_index.yaml` / `.md` at the CEO report
root and lists recent runs by stopped, blocked, diagnostic, actionable, or
missing-resumption status plus dispatch-receipt status, dispatch reason, and
top-blocker, incident-count, repair-plan, and top-repair summaries when
available, plus operator-brief status/summary and the safest next command. It is diagnostic only; it does not
clear stops, generate approvals, or execute run actions.

`ceo artifact-coherence` writes `artifact_coherence.yaml` / `.md` and checks
whether trust artifacts belong to the same run/lab ids and were generated after
the latest binding action. If the resumption brief would otherwise say safe but
coherence fails, the brief downgrades to `diagnostic_stale_artifacts`.

`ceo dispatch-receipt` writes `dispatch_receipt.yaml` / `.md` and fingerprints
the exact trust artifacts that would allow or block one `execute-next --apply`
dispatch. The direct command is diagnostic-only and must not append an action
ledger or overwrite `action_contract.yaml`. During `execute-next`, the receipt
is generated immediately before a bound dispatch or blocked result. The latest
alias remains `dispatch_receipt.yaml`, while immutable per-action snapshots live
under `dispatch_receipts/`; receipt-backed binding action results record the
snapshot path/hash so replay can audit old dispatches after the latest alias
changes.

`ceo blocker-stack` writes `blocker_stack.yaml` / `.md` and orders the current
run blockers by authority: stop requests, pending approvals, preflight blockers,
dispatch blocks, replay gaps, eval failures, memory deltas, and evidence debt.
It is a diagnostic synthesis only; it does not clear blockers or execute
actions.

`ceo incident-register` writes `operating_incident_register.yaml` / `.md` and
turns blocked dispatches, repeated preflight blockers, replay gaps, eval
failures, artifact-coherence failures, and guardrail failures into grouped
repair incidents with owner commands and closure conditions. It is repair memory
only; it is not another gate.

`ceo repair-plan` writes `repair_plan.yaml` / `.md` and ranks the current
blocker-stack and incident-register repairs into one operating backlog with the
top repair, exact next command, closure condition, and whether a manual gate is
required. Each repair item declares a command kind: `runnable_cli`,
`diagnostic_refresh`, `manual_gate`, or `implementation_required`. This prevents
symbolic owner labels such as `repair_failing_eval_suite_case` from being
misread as commands Codex can run. Diagnostic refreshes are safe to run but are
counted separately from runnable repairs because they refresh evidence rather
than close the repair by themselves. It is diagnostic-only; it does not approve
gates or execute repairs.

`ceo action-board` writes `action_board.yaml` / `.md` as the operator-facing CEO
cockpit for the current run. It refreshes resumption, repair-plan, dispatch
receipt, and executive-KPI artifacts, then separates the primary action from
manual gates, runnable repairs, diagnostic refreshes, implementation repairs,
and blocked actions. It is diagnostic-only: it does not execute the primary
action, clear manual gates, or authorize production behavior changes. A fresh
session should read it when it needs one plain next-action surface instead of
manually reconciling multiple YAML files.

`ceo decision-quality` writes `decision_quality.yaml` / `.md` and explains the
current executive routing choice. It records the selected action, runner-up,
confidence, expected artifact, stop condition, and scored alternatives with
rejection reasons. It is diagnostic-only and does not approve execution.

`ceo operator-step --apply` writes `operator_step.yaml` / `.md` as one audited
operator transaction. It refreshes the action board, executes exactly one
internal bounded `execute-next` dispatch only when the board marks that dispatch
safe, refreshes the action board again, and records before/after status. It
refuses manual gates, diagnostic refreshes, implementation repairs, unsupported
command kinds, and arbitrary shell commands from YAML. It is the closest thing
to a "CEO do the next safe thing" command, but it still cannot approve gates,
promote product behavior, change formulas, or authorize product language.

`ceo operator-brief` writes `operator_brief.yaml` / `.md` as the plain-English
CEO handoff card: current situation, primary action, recommended next command,
why, refused actions, and evidence refs. It summarizes status, action-board,
decision-quality, and the latest operator-step without approving execution.

Do not bypass `ceo execute-next` during heartbeat mode. Do not manually run
`ceo run-block`, `lab-ops run`, or `lab-loop run-supervised` unless
`execute-next`, a capability gap, or the active user explicitly requires that
specific command.

For durable scheduler-style runs, create a plan and then run one persisted tick
per Codex wake or external scheduler invocation:

```bash
PYTHONPATH=src python3 -m riskflow ceo heartbeat-plan \
  --run-id <run_id> \
  --interval-minutes 15 \
  --max-hours 8

PYTHONPATH=src python3 -m riskflow ceo heartbeat-tick \
  --run-id <run_id> \
  --apply

PYTHONPATH=src python3 -m riskflow ceo heartbeat-journal \
  --run-id <run_id>
```

`heartbeat-tick` does not sleep or loop. It inspects the required CEO artifacts,
refuses stop requests, true blockers, independent unsafe flight state, pending
approvals, failed guardrails, unresolved memory deltas, replay/eval gaps, and
elapsed heartbeat-plan time budgets, then runs at most one `execute-next` action
and appends `heartbeat_journal.jsonl`. The enforced preflight gate now carries
stop-request and true-blocker authority too, so direct guarded commands cannot
bypass those runtime gates. When the only pre-action blocker is a failed trace
grade, plus the flight-dashboard warning derived from that trace, the tick
records `pre_action_warnings` and delegates to `execute-next`; direct dispatch
must then either run a bounded trace-repair action or write a blocked preflight
result.

Generated CEO/lab YAML and Markdown writes use unique temporary files before
replacement, so concurrent diagnostic commands such as replay and eval-suite do
not fight over a shared `.tmp` path.

Reason: `execute-next` binds the latest CEO decision to the matching action. If
the decision is `run_champion_challenger`, it runs champion/challenger work. If
the previous champion/challenger result asks for fresh/control validation, it
writes a fresh/control validation plan instead of repeating the same comparison.
If that plan requires data, `request_fresh_data` runs `ceo fresh-data-preflight`
to inspect local OHLCV readiness. A safe preflight can then route to
`ceo frozen-candidate-validation`, which writes frozen validation specs from the
prior plan and data coverage. A not-ready preflight routes to the manual
`import_or_curate_fresh_ohlcv_data` gate instead of looping.

When frozen specs are ready, `ceo frozen-validation-executor` may replay them
against existing source artifacts. This is source replay only. It can prove that
the spec has executable artifact lineage, but it is not fresh validation and
does not authorize product language.

Frozen specs include execution-adapter metadata when their source
`variant_records.csv` contains the selected grammar-search variant. That
adapter is the handoff toward future fresh or withheld reruns.
Source replay also writes `frozen_validation_rerun_grid.yaml` when adapters are
ready. `ceo frozen-validation-rerun` can run that frozen one-family
grammar-search adapter grid on local data and write
`frozen_validation_rerun_result.yaml` / `.md` plus CSV artifacts under
`frozen_validation_rerun/`. This rerun is still non-promotional: it checks that
the frozen adapter is executable against local data, then routes to fresh or
withheld snapshot definition before product language.

`ceo fresh-withheld-validation-contract` freezes the next validation contract:
snapshot rules, pass/fail gates, benchmark/symbol locking requirements, and
promotion constraints. It is still contract-only; it does not execute validation
or authorize product language. A ready contract routes to
`ceo fresh-withheld-validation-executor`.

`ceo fresh-withheld-validation-executor` is manifest-gated. It consumes
`fresh_withheld_validation_contract.yaml` and refuses to run validation unless
`fresh_withheld_snapshot_manifest.yaml` declares a fresh or withheld snapshot,
no source-evidence overlap, frozen rule shape, active assets, source-evidence
cutoff, and either a fresh snapshot cutoff or withheld split id. It also blocks
when recorded contract, manifest, preflight, grid, active CSV, or withheld split
manifest fingerprints drift. With a valid manifest and
`frozen_validation_rerun_grid.yaml`, it runs the frozen
grammar-search grid and writes shadow-only CSV/YAML/Markdown results. Completed
execution is not a passing validation result unless the frozen contract
thresholds pass. Threshold checks are semantic, not just presence checks:
matched-null p-values or explicit statuses must pass, directional forward
relative return must clear the declared minimum, and explicit lag/cooldown
pass statuses are required when lag/cooldown controls are required. Mere
availability of matched-null delta, lag, or cooldown columns is not enough. The
output is still not automatic promotion or product language.

`ceo fresh-withheld-snapshot-manifest --apply` writes the manifest draft and
active data inventory. It leaves snapshot authority fields unset unless
freshness or withheld status is explicitly proven. The executor should block on
draft manifests rather than infer validation authority from local CSV readiness.
Use `ceo withheld-split-manifest --apply --withheld-split-id <id>
--source-evidence-cutoff <date>` to write `withheld_split_manifest.yaml` / `.md`
before declaring withheld authority. Use
`ceo fresh-withheld-snapshot-declare --apply` to set the explicit fresh cutoff
or withheld split id, source-evidence cutoff, and no-overlap confirmation
without hand-editing YAML. These authority commands are direct mutations and
must pass preflight plus explicit `--apply`; they still do not execute
validation or authorize product language. Fresh snapshot declarations also require parseable
cutoff dates, a snapshot cutoff after the source-evidence cutoff, active asset
latest dates at or beyond the claimed fresh cutoff, and active CSV hashes carried
from fresh-data preflight into snapshot authority. The executor repeats these
checks so hand-edited manifests cannot bypass them. Withheld declarations
require `withheld_split_manifest.yaml` to be ready, match the requested split id
and source-evidence cutoff, and be fingerprinted into the snapshot manifest.

After source replay, capability backlog and evidence-debt routing should point
to fresh or withheld validation execution. Do not repeat source replay as if it
were a passing validation result.

`ceo approval-queue` is the red-authority holding pen. It records promotion
approval, stopped-run resume, and clear-stop decisions as pending user approval
items. `ceo approval-record --approval-id <id> --decision approved|rejected
--user-confirmed` appends an immutable decision ledger row only; it does not
apply product changes, clear stop files, or mutate production formulas.

`ceo executive-kpis` is the compact CEO scoreboard. It summarizes open
approvals, evidence debt, candidate count, capability backlog, trace verdict,
loop/no-progress counts, validation threshold status, top blocker, operating
incident count, and product-language safety. Use it to decide whether the
operating system is improving or just creating artifacts.

`ceo role-queue` turns evidence debts, pending approvals, and capability backlog
items into specialist role tasks for research director, validation referee,
product translator, risk officer, memory editor, and data steward review.
`ceo role-dispatch` writes `role_dispatch.yaml` / `.md` and markdown packets
under `role_dispatch_packets/` for each pending task. Each packet includes the
exact specialist question, source artifacts, review-only authority boundaries,
and expected `riskflow_ceo_specialist_result_v0` schema.
`ceo role-result --task-id <id> --status complete|blocked` records the result in
`role_task_ledger.jsonl`. Rebuilding `ceo role-queue` consumes that ledger and
marks tasks complete or blocked so specialist work can close the loop. This
coordinates specialist work only; it does not validate statistics or apply
production changes.

Run-generated promotion proposals now require evidenceful specialist reviews:
`validation_referee` plus either `product_translator` or `risk_officer`.
Completed role tasks must point to structured YAML review artifacts with a
passing/approved decision, matching role/task metadata when present,
`production_effect: none`, and no `product_language_allowed: true`. Missing,
unreadable, mismatched, rejected, or unsafe review artifacts are reported as
`completed_specialist_reviews` evidence debt and block
`ready_for_user_approval`. If the specialist gate is omitted entirely, the
proposal builder treats it as not evaluated and blocks by default.

`ceo replay` reconstructs a run from append-only ledgers and key artifact
fingerprints, including action, heartbeat, approval, role, preflight, and
guardrail artifacts. It also checks adjacent action transitions against the
previous action's `next_allowed_actions`, so illegal state-machine jumps become
visible. If `ceo_action_ledger.jsonl` is missing, replay may use
`binding_action_result.yaml` for diagnosis, but that fallback is a replay gap
and is not considered fully replayable.
`ceo eval-suite` grades whether the CEO run is replayable,
state-machine-consistent, contract-consistent, approval-aware, production-safe,
dispatch-receipt backed, validation-gated, role-closure aware, evidence-debt
visible, mission-scored, and strategy-capital aware. This is the first objective
9.9-readiness harness for CEO mode. Hard failures can block dispatch through
preflight; advisory readiness gaps, such as a missing strategy-capital
dashboard, lower 9.9 readiness without becoming a red dispatch blocker by
themselves. Dispatch receipt cases check that the latest binding action has a
matching receipt path/hash and that the receipt fingerprints the trust artifacts
used for dispatch.

`ceo eval-fixtures` runs deterministic policy fixtures for known transition
rules, such as champion/challenger routing to fresh/control validation instead
of generic research and approval waits routing only to approval apply. Fixtures
test the CEO operating policy, not market evidence.

`ceo portfolio-allocator` scores CEO operating lanes: approval governance,
validation authority, candidate product translation, evidence debt, research
infrastructure, specialist review, trace reliability, and memory handoff. It
selects the highest-value bottleneck for attention. This is operating guidance
only; it does not validate product evidence or mutate production behavior.

`ceo mission-score` scores Riskflow's coverage across bullish permission,
warning/blocker, invalidation, reset quality, gradient interpretation, path
management, cross-asset/regime usefulness, and archive/do-not-repeat memory.
It converts scattered candidates and evidence debt into a plain mission score,
lowest mission dimension, and next required evidence. It is diagnostic only and
does not authorize product language.

`ceo strategy-capital-dashboard` allocates 100 `ceo_attention_points` across
approval/safety, validation authority, candidate translation, warning research,
bullish permission research, reset/gradient/path research, cross-asset regime
validation, and archive memory. The points are CEO attention, not trading or
production capital. Approval, stop, failed preflight, failed trace, and
promotion gates outrank research allocation.

`ceo resumption-brief` is the one-page cockpit handoff. It inspects preflight,
replay, eval-suite, mission score, strategy capital, and the latest decision
packet to produce a resume status and exact next command. If preflight is
blocked or a stop request exists, the next command must not be
`execute-next --apply`.

`ceo artifact-coherence` is the same-cockpit, same-flight check. It catches
missing, stale, or mismatched trust artifacts so a fresh session does not resume
from green lights that belong to an older action.

`ceo dispatch-receipt` is the dispatch audit trail. It answers: these exact
artifact hashes, this action contract, this preflight result, and this approval
state are why the CEO action was allowed or blocked. It does not approve
production behavior.

`ceo blocker-stack` is the one-page "why can't the CEO act?" answer. It orders
competing blockers by authority and gives the safest next command from the
current resumption brief.

`ceo incident-register` is the "what went wrong and how do we stop repeating
it?" register. It groups recurring operating failures by stable incident key and
records evidence paths/hashes plus closure conditions.

`ceo executive-kpis` includes approval count, evidence debt, trace health,
validation status, top blocker, operating incident count, and repair-plan
status/top repair/top repair kind so the CEO scoreboard points at the current
operating repair lane without overstating autonomy.

`ceo run-index` is the fleet board for CEO runs. It scans `reports/ceo_runs`,
summarizes each run's resumption/preflight state, records mission and strategy
summary fields when present, records the latest dispatch-receipt status/reason,
top blocker, operating incident count, repair-plan status, and top repair, and
top repair kind, and points to the next diagnostic or governed command. Use it
before resuming from a long/noisy handoff when multiple run ids exist.

`ceo memory-delta` turns the advisory knowledge-graph delta into a governed
handoff artifact. Without `--apply`, it writes `memory_delta.yaml` / `.md` only.
With `--apply`, it writes one curated Obsidian map note when a durable memory
delta is required. The note is routing memory, not runtime authority or product
proof.

`ceo guardrail-audit` scans CEO YAML artifacts for accidental non-`none`
production effects or product-language permission. `ceo preflight-gate` unifies
trace, approval, replay, eval, guardrail, memory, and heartbeat-budget status
into one dispatch gate. Direct `ceo execute-next` and `heartbeat-tick` both
consume this gate before running a bound action. Trace-failure repair decisions
may proceed only when the trace failure is the gate's sole blocker and the
chosen decision is an explicit repair/intervention route such as self-audit
routing, research-infra patching, hypothesis-source broadening, or fresh-data
preflight. Validation executors do not bypass a failed trace gate.

Preflight blockers include category metadata so a fresh operator can distinguish
runtime authority, approval authority, trace reliability, replay integrity, eval
readiness, product guardrails, memory handoff, and heartbeat-budget blockers.

CEO action writers also require an in-process dispatch context. Bound
`execute-next` uses `bound_dispatch`; guarded direct CLI commands use
`guarded_direct` after preflight; report/eval/preflight refreshes use
diagnostic contexts only for summary-style artifacts such as fresh/withheld
contract refresh, promotion proposal staging, and evidence-debt staging.
Diagnostic refresh does not append `binding_action_result.yaml` or
`ceo_action_ledger.jsonl`, and it cannot run heavy mutators such as run-block,
queue repair, broadening, or snapshot authority writers.

`ceo approval-record` remains ledger-only. `ceo approval-apply --approval-id
<id> --user-confirmed --apply` is the second explicit step for closing a
recorded approval. Promotion approval closure is still shadow-only and does not
mutate production formulas, Pine defaults, rankings, scores, states, or alerts.
Clear-stop approval can remove stop files only through this second explicit
apply path. `approval-apply` inspects the preflight gate first and proceeds only
when the blockers are the approval/runtime blockers that approval is designed to
resolve.
apply command.

If the decision is unsupported, it writes `capability_gap.yaml` instead of
silently running another generic research block.

## Required Inspection Artifacts

Before acting, inspect the current state enough to understand whether it is safe
and useful to continue.

CEO artifacts:

```text
reports/ceo_runs/<run_id>/heartbeat_status.yaml
reports/ceo_runs/<run_id>/executive_decision_packet.md
reports/ceo_runs/<run_id>/action_contract.yaml
reports/ceo_runs/<run_id>/action_contract.md
reports/ceo_runs/<run_id>/binding_action_result.yaml
reports/ceo_runs/<run_id>/action_outcome_card.yaml
reports/ceo_runs/<run_id>/action_outcome_card.md
reports/ceo_runs/<run_id>/ceo_action_ledger.jsonl
reports/ceo_runs/<run_id>/ceo_self_audit.yaml
reports/ceo_runs/<run_id>/trace_grade.yaml
reports/ceo_runs/<run_id>/ceo_flight_dashboard.yaml
reports/ceo_runs/<run_id>/ceo_operating_dashboard.yaml
reports/ceo_runs/<run_id>/ceo_operating_dashboard.md
reports/ceo_runs/<run_id>/ceo_replay.yaml
reports/ceo_runs/<run_id>/ceo_eval_suite.yaml
reports/ceo_runs/<run_id>/ceo_eval_fixtures.yaml
reports/ceo_runs/<run_id>/portfolio_allocator.yaml
reports/ceo_runs/<run_id>/memory_delta.yaml
reports/ceo_runs/<run_id>/guardrail_audit.yaml
reports/ceo_runs/<run_id>/preflight_gate.yaml
reports/ceo_runs/<run_id>/promotion_proposal.yaml
reports/ceo_runs/<run_id>/promotion_proposal.md
reports/ceo_runs/<run_id>/capability_backlog.yaml
reports/ceo_runs/<run_id>/capability_backlog.md
reports/ceo_runs/<run_id>/capability_gap.yaml
reports/ceo_runs/<run_id>/product_delta_scoreboard.yaml
reports/ceo_runs/<run_id>/champion_challenger_action_plan.yaml
reports/ceo_runs/<run_id>/champion_challenger_results.yaml
reports/ceo_runs/<run_id>/champion_challenger_visual_review_queue.yaml
reports/ceo_runs/<run_id>/champion_challenger_visual_review_queue.md
reports/ceo_runs/<run_id>/fresh_control_validation_plan.yaml
reports/ceo_runs/<run_id>/fresh_control_validation_plan.md
reports/ceo_runs/<run_id>/fresh_data_preflight.yaml
reports/ceo_runs/<run_id>/fresh_data_preflight.md
reports/ceo_runs/<run_id>/frozen_candidate_validation_plan.yaml
reports/ceo_runs/<run_id>/frozen_candidate_validation_plan.md
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
- generate champion/challenger visual-review queues for human or agent chart
  review;
- run fresh-data preflight against local CSV coverage;
- compile frozen validation specs from approved shadow candidates and safe data
  preflight;
- write CEO operating dashboards that summarize candidate, capability, data,
  memory, trace, and risk portfolios;
- write guarded promotion proposals for user review, without applying product
  changes;
- write standalone capability backlogs for research-infrastructure gaps;
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

Default to `ceo execute-next --apply`. Use direct commands only for explicit
diagnosis, repair, or when `execute-next`, a capability gap, or the active user
names that command. Guarded direct validation/evidence/authority commands
consume the enforced preflight gate before mutation; authority artifact commands
also require explicit `--apply`.

Map CEO decisions to heartbeat behavior:

```text
run_champion_challenger
  -> run execute-next; inspect champion_challenger_results.yaml.

run_fresh_or_control_validation_for_promising_shadow_challengers
  -> run execute-next, or only under the direct-command exception above, ceo fresh-control-validation --apply; inspect fresh_control_validation_plan.yaml.

continue_governed_research
  -> run execute-next; this may run one bounded governed block.

patch_research_infra
  -> run execute-next, or only under the direct-command exception above, ceo patch-research-infra --apply; inspect research_infra_patch_plan.yaml.

broaden_hypothesis_source
  -> run execute-next, or only under the direct-command exception above, ceo broaden-hypothesis-source --apply; inspect hypothesis_source_broadening_plan.yaml.

request_fresh_data
  -> run execute-next, or only under the direct-command exception above, ceo fresh-data-preflight; inspect fresh_data_preflight.yaml.

run_frozen_candidate_validation
  -> run execute-next, or only under the direct-command exception above, ceo frozen-candidate-validation; inspect frozen_candidate_validation_plan.yaml.

import_or_curate_fresh_ohlcv_data
  -> stop at the manual/data gate; do not rerun CEO automation until CSVs change or the user authorizes the import workflow.

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
reports/ceo_runs/<run_id>/action_contract.yaml
reports/ceo_runs/<run_id>/action_outcome_card.yaml
reports/ceo_runs/<run_id>/ceo_action_ledger.jsonl
reports/ceo_runs/<run_id>/ceo_self_audit.yaml
reports/ceo_runs/<run_id>/trace_grade.yaml
```

The action contract records the allowed command, scope, expected artifacts, stop
conditions, and forbidden changes for the selected action. The outcome card is
the compact wake-to-wake summary. It records action status, progress class, next
allowed actions, evidence provenance, failure-avoidance status, self-audit
status, and whether a memory delta is required before repeating the same action.
`ceo_self_audit.yaml` and `trace_grade.yaml` also include a loop-meltdown
summary. It counts repeated decision/action/status fingerprints, repeated manual
data gates, unresolved capability-builder loops, and recent no-progress actions.

A wake made no meaningful progress if:

- `binding_action_result.status` is `blocked`, `capability_gap`, or
  `no_candidates`;
- `binding_action_result.status` is `manual_gate`;
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

If `trace_grade.yaml` reports `loop_meltdown.strategy_change_required: true`,
the next wake must follow `recommended_next_action`. In particular, repeated
`manual_gate` status means stop for manual data import or curation; do not rerun
fresh-data preflight or generic research until CSV state changes.

Use `ceo trace-grade` when judging whether a heartbeat actually made progress.
It scores artifact completeness, meaningful progress, repeated decisions,
constraint violations, self-audit intervention requirements, and whether the
next action has a supported executor. It also reports whether the latest action
repeated a prior no-progress failure, whether the recent action ledger shows
loop meltdown, and which input/output artifacts support the action lineage. A
warning or failure is not itself a production finding; it is an instruction to
repair autonomy before burning more research budget.

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
- open evidence-debt count and next owner command;
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
    broaden_idea_pool # maps to broaden_hypothesis_source
    request_fresh_data
    request_visual_review
    write_candidate_packet
    archive_redundant_path
    build_missing_command # maps to patch_research_infra or an explicit capability_gap acceptance plan
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
