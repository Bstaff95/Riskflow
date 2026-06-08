# CEO Heartbeat Autonomy

This document is the operating contract for Codex-supervised Riskflow CEO
heartbeat runs.

For company-building context, pair this contract with
`docs/RISKFLOW_AS_BUSINESS.md`, `docs/CUSTOMER_DISCOVERY.md`,
`docs/CUSTOMER_OUTREACH_DRAFTS.md`, `docs/PRICING_AND_PACKAGING.md`,
`docs/BUSINESS_METRICS.md`, `docs/COMPETITIVE_POSITIONING.md`,
`docs/CEO_STRATEGY_MEMO.md`, `docs/BUSINESS_PRODUCT_ROADMAP.md`,
`docs/CEO_DELEGATION_MODEL.md`, `docs/CEO_OPERATING_CADENCE.md`,
`docs/CEO_WEEKLY_REVIEW_TEMPLATE.md`, and `docs/CEO_BOARD_REPORTING.md`.

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

External agent-system research reinforces this contract: approvals should
interrupt before risky execution, paused runs need durable resumable state,
guardrails should be explicit and separately inspectable, tools should be
evaluated against observed failures, and parallel specialist work still needs
one accountable orchestrator. The Obsidian note
`obsidian/wiki/concepts/CEO Agentic Systems Research Alignment.md` stores the
background source anchors. It is design memory, not runtime authority.

## Run Id And Runtime Authority

A CEO run is active only when generated runtime artifacts say it is active.
Obsidian maps, Prime checkpoints, and dated session notes are routing memory,
not runtime authority.

Before any CEO action, inspect `heartbeat_status.yaml`, `trace_grade.yaml`, and
`ceo_operating_dashboard.yaml` for the chosen `run_id`. If no `run_id` is
explicitly supplied and no single active run is verified, plan a fresh run id.

Dashboard `safe_to_continue` fields are process-safety diagnostics, not dispatch
authority. Flight, operating, and strategy-capital dashboards must be read with
their `safe_to_continue_scope`, `dispatch_authority`, and
`runtime_authority_note` fields. Actual dispatch authority comes from `ceo
status`, approval queue, action board, resumption brief, preflight gate, and
dispatch receipt.

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

PYTHONPATH=src python3 -m riskflow ceo sidecar-evidence-brief \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo data-gate-brief \
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

PYTHONPATH=src python3 -m riskflow ceo action-board \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo operator-brief \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo artifact-coherence \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo resumption-brief \
  --run-id <run_id>

PYTHONPATH=src python3 -m riskflow ceo run-index \
  --limit 25
```

`ceo status` is the first quick-read command. In addition to lab progress and
true-blocker state, it prints live stop-request state and applies it as a
runtime-authority override. If a stop file exists after older safe artifacts
were generated, status reports `manual_gate_required`, forces
safe-to-dispatch false, and routes the default handoff command to
`ceo approval-queue` instead of the stale `execute-next` command. The displayed
action-board, decision-quality, and operator-brief fields are also forced to
manual-gate state in the status view. It also
surfaces the latest existing blocker stack, top blocker,
operating incident count, dispatch receipt status, safe-to-dispatch flag, and
trace-grade verdict/score/recommended next action/issues/manual-data flag plus
replay/eval/operator-step/artifact-coherence health. It also prints resumption
status and a default handoff command; if the resumption brief is missing, that
command is `ceo resumption-brief`. When `repair_plan.yaml` exists, it also
prints repair plan status, runnable repair count, diagnostic refresh count, top
repair, top repair kind, and repair next command. When approvals are pending, it
prints the top approval kind, reason, source, required user decision, authority,
fingerprint, and record/apply commands. When `evidence_debt_register.yaml`
exists, it prints open debt count, candidate/global debt split, archived
non-promotional candidate count, next debt action, and report path. When
`role_task_queue.yaml` exists, it also prints role queue status,
pending/completed/blocked counts, top pending specialist task, top blocked
specialist task, top packet paths, blocked task closure command, and the next
role-result command template. When
`decision_quality.yaml` exists, it
also prints the selected strategic action, confidence, runtime authority,
executable next action, can-execute flag, runtime-authorized strategic route
behind any safe `execute-next` wrapper, and blocked-by reason.

`ceo heartbeat-status` is also a quick-read command, but it must not overrule
runtime authority. If the action board, decision-quality, or operator brief
already declares a manual gate, heartbeat status reports
`continue_recommended: false`, `manual_gate_active: true`, and the runtime block
reason even if the older strategic decision packet still recommends continuing.
When a data-gate brief exists, heartbeat status also surfaces the data-gate
status, required timeframes, CSV requirement count, candidate unlock count,
next data action, report path, candidate-unlock table path, import-checklist
counts/path, and data-gate handoff audit status so operators do not need a
second command to understand a manual OHLCV gate. When sidecar
learning and evidence-debt artifacts exist, heartbeat status also surfaces the
top visual-review candidate, sidecar lead/control/archive/review/blocked split,
lead/control/archive candidate actions, and evidence-debt candidate/global/archive
split so nonstop operators can see what was learned and what still blocks
champion/challenger promotion from the first check. When a
`sidecar_post_data_validation_playbook.yaml` exists, quick status surfaces also
print the playbook status, current action, visual-label gate, pre-validation
blockers, and can-execute candidate count. This keeps post-data
champion/challenger validation from being mistaken as executable while fresh
data, visual labels, quality remediation, or shadow guardrails are still open.
When a `sidecar_visual_label_source_patch_plan.csv` exists, status surfaces also
print source-cell patch counts, pending cells, blocked cells, source files, and
source rows so label work can be sized without opening the worksheet.
`ceo status` and `ceo run-index` use the same manual-data handoff policy: live
stop requests and pending approvals still take precedence, but a manual OHLCV
gate with no pending approval routes the default or latest next command to
`ceo data-gate-brief` instead of another preflight wrapper.

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
repair apply, operator brief, artifact coherence, resumption brief,
approval queue, executive KPIs, capability backlog, fresh/withheld validation
contract, role dispatch, role result validation, promotion proposal,
sidecar evidence brief, and evidence-debt links/status. It is a handoff report, not approval to change
production behavior. Its role snapshot includes top blocked role review status,
accepted result path, recommended evidence action, and finding so final handoff
does not lose accepted blocked specialist context. The report reuses freshly generated trust artifacts inside
one refresh pass where possible so the handoff is faster without weakening
authority checks. Reused trust artifacts must match the active run/lab ids, and
operator surfaces still recheck live stop/manual-gate state before exposing any
bounded action.

For a fresh session or noisy-thread handoff, run `ceo resumption-brief` before
any action. It writes `resumption_brief.yaml` / `.md` and answers whether the
run is stopped, blocked by preflight, diagnostic-only, or safe for one bound
`execute-next --apply` action. It synthesizes existing trust artifacts; it does
not authorize product language or replace preflight. When it is safe for one
bound action, it records an independently derived `authorized_strategic_route`
and `authorized_route_source` from the current action contract or
strategy-capital dashboard, so downstream surfaces can prove what
`execute-next` is expected to run.

If you are unsure which run should be inspected first, run `ceo run-index`
before choosing a run id. It writes `run_index.yaml` / `.md` at the CEO report
root and lists recent runs by stopped, blocked, diagnostic, actionable, or
missing-resumption status plus dispatch-receipt status, dispatch reason, and
top-blocker, incident-count, repair-plan, and top-repair summaries when
available, plus repair-apply status/closure, role-result-validation status,
role completed/blocked counts, top blocked role task and closure command,
operator-brief status/summary, and the safest next command. It is diagnostic only; it does not
clear stops, generate approvals, or execute run actions.

`ceo artifact-coherence` writes `artifact_coherence.yaml` / `.md` and checks
whether trust artifacts belong to the same run/lab ids and were generated after
the latest binding action. It also checks semantic trust alignment: the current
action contract must match the latest binding action, and that binding action
must carry an immutable `dispatch_receipts/` snapshot path/hash that still
matches the receipt file. If the receipt fingerprinted trust artifacts that
existed at dispatch time, authority artifacts must still match the receipt's
recorded SHA-256 values. Mutable diagnostics such as trace grade, replay, eval
suite, guardrail audit, and approval queue/status can refresh during later
preflights; their fingerprint drift is visible in coherence but is not a hard
dispatch blocker by itself. It also tracks handoff diagnostics such as
`approval_queue.yaml`, `approval_status.yaml`, `role_task_queue.yaml`,
`role_dispatch.yaml`, `role_result_validation.yaml`, `repair_apply.yaml`,
`action_board.yaml`, `decision_quality.yaml`, and `operator_brief.yaml`;
missing or stale versions of these are advisory because they can mislead a
fresh session, but they are not direct dispatch authority. If the current
repair plan is manual-gated or has zero runnable repairs, missing
`repair_apply.yaml` is reported as `not_required_by_current_repair_plan`
instead of as a missing handoff artifact.
It also checks semantic agreement between action-board, decision-quality, and
operator-brief. For example, when the action board says `manual_gate_required`,
decision-quality must show a blocked effective runtime action and
operator-brief must say `waiting_on_manual_gate`; the action-board primary
action also must not remain marked `can_execute_now: true`. These semantic
mismatches are advisory, but they are high-signal handoff problems.
Legacy actions recorded before dispatch receipts or transition policy evidence
can produce `pass_with_advisory_issues`: the issues remain visible, but
`hard_issue_count: 0` means they should not block handoff by themselves. If the
resumption brief would otherwise say safe but hard coherence fails, the brief
downgrades to `diagnostic_stale_artifacts`.

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
If a live stop request exists, the stack's top-level next command routes to
`ceo approval-queue` even when reused handoff artifacts still contain a stale
safe `execute-next` command. It is a diagnostic synthesis only; it does not
clear blockers or execute actions.

`ceo incident-register` writes `operating_incident_register.yaml` / `.md` and
turns blocked dispatches, repeated preflight blockers, replay gaps, eval
failures, artifact-coherence failures, and guardrail failures into grouped
repair incidents with owner commands and closure conditions. It is repair memory
only; it is not another gate.

`ceo repair-plan` writes `repair_plan.yaml` / `.md` and ranks the current
blocker-stack and incident-register repairs into one operating backlog with the
top repair, governed next command, closure condition, and whether a manual gate
is required. Each repair item declares a command kind: `runnable_cli`,
`diagnostic_refresh`, `manual_gate`, or `implementation_required`. This prevents
symbolic owner labels such as `repair_failing_eval_suite_case` from being
misread as commands Codex can run. Diagnostic refreshes are safe to run but are
counted separately from runnable repairs because they refresh evidence rather
than close the repair by themselves. Implementation-required items include a
structured playbook with target files, target functions, focused tests, and
acceptance criteria; the playbook is a coding contract, not an executable
command. It is diagnostic-only; it does not approve gates or execute repairs.
For executable repair items, `next_command` points to `ceo repair-apply
--repair-key <repair_key> --apply`, not the lower-level owner command.

`ceo repair-apply --repair-key <repair_key> --apply` writes
`repair_apply.yaml` / `.md` plus `repair_apply_ledger.jsonl` as the governed
executor for one repair-plan item. It refreshes the repair plan before acting,
finds the exact repair key, refuses manual gates and implementation-required
repairs, executes only allowlisted internal CEO commands, and runs executable
repairs through bound CEO action context rather than raw shell text. It then
refreshes the repair plan again, writes immutable before/after repair-plan
snapshots under `repair_apply_plans/`, appends the attempt and snapshot hashes
to the repair-apply ledger, and records whether the repair actually closed.
Diagnostic refreshes may execute, but they do not count as closed unless the
after-plan clears or changes the repair key. If the same repair key remains but
reclassifies into a manual gate or implementation-required item, `repair-apply` records
`repair_reclassified_not_closed` instead of pretending the repair closed. It
never runs shell text from YAML, clears approvals, promotes product behavior,
changes formulas, or authorizes product language.

`ceo action-board` writes `action_board.yaml` / `.md` as the operator-facing CEO
cockpit for the current run. It refreshes resumption, repair-plan, dispatch
receipt, and executive-KPI artifacts, then separates the primary action from
manual gates, runnable repairs, diagnostic refreshes, implementation repairs,
and blocked actions. It is diagnostic-only: it does not execute the primary
action, clear manual gates, or authorize production behavior changes. A fresh
session should read it when it needs one plain next-action surface instead of
manually reconciling multiple YAML files.
When any manual gate exists, the board must not expose a runnable action under
`runnable_repairs`. Otherwise-runnable dispatch or repair items are demoted to
blocked actions with `blocked_by_runtime_authority: manual_gate_required`, so a
fresh session cannot accidentally treat a lower-priority queue item as safe.

`ceo decision-quality` writes `decision_quality.yaml` / `.md` and explains the
current executive routing choice. It records the selected action, runner-up,
confidence, expected artifact, stop condition, and scored alternatives with
rejection reasons. It also refreshes `ceo action-board` and records runtime
authority fields first: effective runtime action, command kind, can-execute
flag, runtime-blocked flag, runtime block reason, authority status, executable
next action/command, and what blocks the selected strategic route when manual
gates, diagnostic refreshes, implementation repairs, or different bounded
actions outrank it. If the selected strategic route is not executable now,
`selected_strategic_route_advisory` repeats it explicitly as advisory only.
When the action board exposes a safe bounded `execute-next` wrapper, it copies
the independently derived
`authorized_strategic_route` from the resumption brief. Decision quality only
marks the selected action executable when it matches that route; it does not
self-authorize a wrapper by assuming `execute-next` will run the selected
route. When `sidecar_evidence_brief.yaml` exists, decision quality uses its
warning/reset sidecar candidate counts, visual-review readiness, fresh-data
blocked counts, champion, and champion/challenger status in the scored
alternatives. This prevents sidecar candidates from disappearing when the
generic product-delta candidate count is empty, but it still leaves runtime
authority with the action board and manual gates. It is diagnostic-only and
does not approve execution.

`ceo sidecar-evidence-brief` writes `sidecar_evidence_brief.yaml` / `.md` plus
`sidecar_evidence_candidates.csv`. The CSV is the compact sortable handoff for
warning/reset sidecar candidates: candidate id, role, champion/challenger,
metric summary, visual-review readiness, validation route, evidence-debt
blockers, promotion ceiling, and production-effect guardrail. It is evidence
reporting only; it does not run validation, clear data gates, or promote
product behavior.

The same command also writes `sidecar_visual_review_handoff.csv`. This is the
operator handoff for chart review: one row per sidecar candidate with review
questions, required labels, gallery and label-CSV paths, visual priority,
champion/challenger context, metric summary, same-sample blockers, fresh-data
gate status, and production guardrails. It helps a fresh session or human
reviewer inspect the warning/reset candidates without treating visual review as
fresh validation.
It also writes `sidecar_visual_label_worklist.csv` / `.md`, a row-level
candidate-matched checklist for visual examples whose required human labels are
still blank or incomplete. The worklist is review-only and exposes exact
variant, family-timeframe, and family-context matches so label completion is not
confused with validation authority.
It also writes `sidecar_visual_label_review_batches.csv` / `.md`, a bounded
batching layer over the pending worklist rows. Batches keep source label row
numbers, image paths, candidate ids, and match type, and remain review-only.
It also writes `sidecar_visual_label_progress.csv` / `.md`, a candidate-level
progress bridge from the worklist and batches into the champion/challenger
quality audit. It records matched, pending, and completed label rows plus the
next review batch without treating visual labels as validation.
It also writes `sidecar_visual_label_next_batch.csv` / `.md`, a focused
worksheet for the current next review batch. It keeps source label row numbers,
image paths, blank label fields, and source-update instructions so review work
can start without scanning the full worklist.
It also writes `sidecar_visual_label_rubric.yaml` / `.md`, a review-only field
contract for the current batch. It defines the preferred label values and
acceptance criteria for completing visual labels without treating the labels as
validation or promotion authority.
It also writes `sidecar_visual_label_source_patch_plan.csv` / `.yaml` /
`.md`, a per-cell expansion of the source-update manifest. Each row identifies
one missing authoritative source-label cell, the source CSV row, the label
field, allowed values, image ref, and the after-update verification command. It
is a human label-entry checklist only; it does not infer labels, write source
CSVs, validate candidates, promote candidates, or alter production behavior.
It also writes `sidecar_visual_label_completion_audit.csv` / `.yaml` / `.md`,
which checks the current next batch against the rubric and reports completed,
missing, and invalid label rows. The audit is review-quality evidence only; it
does not validate, promote, or alter production behavior.
Quick CEO status, heartbeat, and run-index surfaces also print the top
visual-review candidate, focus, priority, gallery, and label CSV so the next
chart-review action is visible without opening the raw handoff table.

It also writes `sidecar_champion_challenger_evidence.csv`. This table is the
compact base-vs-challenger evidence matrix for warning/reset sidecars: champion
baseline returns and hit rate, role delta, drawdown and MFE/MAE, sample breadth,
event diversity, matched-null evidence, strict-survivor status, same-sample
promotion blockers, and the conservative operator evidence decision. It is
interpretation support only; it does not validate, promote, or change Riskflow
production behavior.

It also writes `sidecar_champion_challenger_quality_audit.yaml` / `.md`. This
audit checks champion identity, challenger naming, core metric coverage,
role-benefit fields, validation status, event-diversity concentration, and
shadow production guardrails. Hard findings mean the packet is structurally
unsafe; advisory findings preserve review-only weaknesses such as low event
diversity or archive/failure-mode metric gaps. Quick operator surfaces summarize
those hard/advisory findings so the reason for a lead, control, or archived
sidecar is visible without opening the raw audit YAML.

It also writes `sidecar_quality_remediation_plan.yaml` / `.md`. This plan
translates champion/challenger quality findings into candidate-specific
remediation routes: human visual-label work, data-gated diversity/control
checks, archive-only failure-mode handling, or hard quality repair. The plan is
a handoff only. It does not clear manual data gates, fabricate labels, validate
candidates, approve product language, or change production behavior. Quick CEO
status and heartbeat surfaces print the plan path, status, required action, and
autonomous/human/diversity/archive counts so quality advisories do not get
mistaken for either validation proof or runnable autonomous work.

It also writes `sidecar_candidate_decision_cards.md`. This is the human-readable
candidate-by-candidate handoff that translates the candidate table, visual
handoff, champion/challenger matrix, frozen-spec review, and evidence debts into
shadow-only handling, required next action, and product-language guardrails. It
is an operator translation layer, not product approval.

It also writes `sidecar_shadow_guardrail_audit.yaml` / `.md`. This audit fails
if a sidecar candidate escapes the shadow ceiling, allows product language,
claims production effect, or marks validation complete while a manual data gate
is active. A passing audit only proves shadow guardrails held; it does not prove
the candidate.

It also writes `sidecar_evidence_source_manifest.csv`. This manifest gives one
row per sidecar candidate with the exact metric-source, visual-review,
frozen-spec, validation-plan, and evidence-debt refs needed for fresh-session
traceability. It is a source map, not validation evidence by itself.

It also writes `sidecar_evidence_source_health.csv` / `.yaml` / `.md`. This
audit checks whether the metric CSVs, visual-review files, and review-only
frozen-spec result paths cited by the source manifest exist locally and have
the expected file or directory shape. It is a source-ref health audit only; it
does not validate, promote, or alter production behavior.

It also writes `sidecar_evidence_source_fingerprints.csv` / `.yaml` / `.md`.
This audit records SHA-256 fingerprints, file sizes, CSV row counts, and
directory file counts for the locally resolved evidence refs. It lets a fresh
session detect source drift after the sidecar packet was generated. It is a
provenance audit only; it does not validate, promote, or alter production
behavior.

It also writes `sidecar_candidate_learning_ledger.csv` / `.yaml` / `.md`. This
ledger translates the existing sidecar packet into one operator-learning row per
candidate: lead post-data candidate, diversity control only, archive failure
mode, review-only candidate, or quality-blocked review-only. It records the
quality audit status, source-health and fingerprint status, data-gate unlock
status, validation authority, queue/design status, next allowed action, and
shadow production guardrails. It is a learning handoff only; it does not
validate, promote, authorize product language, or alter production behavior.
Quick CEO status, heartbeat, run-index, and final reports also surface the
current lead, diversity-control, and archive candidate IDs plus their next
required or allowed actions from this ledger.

It also writes `sidecar_evidence_gap_matrix.csv`. This matrix expands each
candidate into one row per required champion/challenger evidence dimension:
forward relative return, hit rate, drawdown, MFE/MAE, missed-upside and
avoided-downside, event diversity, lag sensitivity, cooldown sensitivity,
visual review, frozen-spec governance, fresh/control validation, and shadow
production guardrails. It is an evidence-readiness checklist, not a promotion
approval.

It also writes `sidecar_candidate_readiness_summary.csv` / `.md`. This is the
compact one-row-per-candidate triage view derived from the gap matrix:
readiness tier, primary blocker, ready/blocker/missing/advisory dimension
counts, strongest same-sample signal, required next action, and shadow
production guardrails. It does not validate or promote any sidecar.

It also writes `sidecar_validation_queue.csv` / `.md`. This queue orders the
shadow candidates for post-data fresh/control validation once OHLCV has been
imported and preflight passes. While the manual data gate is active, it is only
a validation-order handoff; it does not run validation, clear blockers, or
authorize promotion.

It also writes `sidecar_post_data_validation_playbook.yaml` / `.md`. This is
the guarded runtime handoff for what to do only after pre-validation gates are
clean. It records the current required action, visual-label completion status,
visual-label gate, pre-validation blockers, can-execute state, and the required
sequence through fresh-data preflight, sidecar-evidence refresh, frozen-candidate
validation, executor, and rerun. Candidate-bearing packets require an explicit
`visual_label_batch_complete` audit before the visual-label gate passes; a
missing or no-pending completion audit is not enough to authorize validation.
The playbook is a handoff only; it does not import data, validate, promote, or
change production behavior.

It also writes `sidecar_champion_challenger_validation_design.yaml` / `.md`.
This pre-registers the post-data champion/challenger validation design for each
warning/reset sidecar candidate: champion, challenger, required metrics,
controls, acceptance criteria, stop conditions, visual-review refs, frozen-shape
fields, evidence debts, and shadow authority scope. It is a validation-design
handoff only; it does not execute validation or promote candidates.

It also writes `sidecar_data_gate_unlock_matrix.csv` / `.yaml` / `.md`. This
matrix ties each warning/reset sidecar candidate to the fresh-data preflight
state: required timeframes, blocked timeframes, CSV requirement count, unlock
status, validation authority, post-unlock action, and stop condition. It is a
data-gate handoff only; it does not import data, execute validation, or promote
candidates.

When the data gate is blocked, `ceo data-gate-brief` also writes
`data_gate_import_checklist.csv` / `.yaml` / `.md`. This checklist expands the
CSV requirement table into one row per required symbol-timeframe CSV, including
current preflight status, required action, expected path, manual import
instruction, next verification command, and a per-row guardrail that import
completion alone cannot authorize validation. It is a manual OHLCV handoff
only; it does not write `data/raw`, run validation, promote candidates, or alter
production Riskflow behavior.

It also writes `data_gate_handoff_audit.yaml` / `.md`. This audit checks that the
CSV requirement table, import plan, import batches, symbol matrix, and import
checklist agree on row counts, expected paths, pending import counts, verification
commands, and handoff-only guardrails. Passing this audit means the manual data
handoff artifacts are internally consistent; it does not mean data has been
imported, validation is safe, or any candidate is approved for promotion.

It also writes `sidecar_evidence_consistency_audit.yaml` / `.md`. This audit
cross-checks the sidecar packet for candidate-ID agreement across the evidence
brief, validation design, data-gate unlock matrix, shadow guardrail audit,
candidate learning ledger, post-data playbook, quality-remediation plan, current
handoff, and decision matrix. It also checks visual-label worksheet/source-update
alignment, evidence-debt manual-gate handoff, archive-only debt leakage,
quality-remediation issue counts/status/archive classification, manual-gate
validation authority, manual-gate remediation autoclear policy, and shadow
production guardrails. It is a packet-integrity check only; it does not validate
or promote candidates.

It also writes `sidecar_evidence_packet_index.yaml` / `.md`. This packet index
lists the sidecar evidence artifacts, existence status, CSV row counts, purpose,
authority scope, and production-effect guardrail so a fresh session can audit
the sidecar package quickly. It is an artifact index only, not evidence
validation.

It also writes `sidecar_current_decision_packet.yaml` / `.md`. This is the
current executive handoff over the sidecar package, separate from any older
strategic CEO packet. It records the active hold/continue decision, candidate
handling decisions, evidence debt state, quality-remediation status/counts, and
per-candidate remediation findings, required actions, clearance gates, and
autonomous-clearance flags. It is still a shadow-only handoff: it does not clear
the manual data gate, validate candidates, authorize product language, or change
production behavior.

When validation-referee specialist results have captured candidate frozen
shapes but the governed `frozen_candidate_validation_plan.yaml` is still
missing, `ceo sidecar-evidence-brief` also writes
`sidecar_frozen_spec_review.csv`. This table is review-only: it records the
exact candidate shape, entry lag, cooldown, outcome column, sample size,
cluster breadth, no-tuning controls, and required metrics. It does not retire
the official frozen-plan debt, authorize the frozen validator, or substitute
for fresh/control validation.
If the action board status is `manual_gate_required`, decision quality must
force `effective_runtime_can_execute_now: false` even when a stale primary
action still carries `can_execute_now: true`; manual-gate board status outranks
all wrapper route matching.

`ceo operator-step --apply` writes `operator_step.yaml` / `.md` as one audited
operator transaction. It refreshes the action board, executes exactly one
internal bounded `execute-next` dispatch only when the board marks that dispatch
safe, refreshes the action board again, and records before/after status plus
the executed action's `meaningful_progress` flag. It also snapshots the
before/after action boards under `operator_step_boards/` and records their
hashes, so the audit trail can show which board authorized the one attempted
dispatch. Each step also appends `operator_step_ledger.jsonl`; `ceo replay`
validates those snapshot paths and hashes. Manual-gate,
capability-gap-without-progress, and no-progress action results get distinct
operator-step statuses instead of being counted as useful execution. It refuses
manual gates, diagnostic refreshes, implementation repairs, unsupported command
kinds, and arbitrary shell commands from YAML. It is the closest thing to a "CEO
do the next safe thing" command, but it still cannot approve gates, promote
product behavior, change formulas, or authorize product language.

`ceo operator-brief` writes `operator_brief.yaml` / `.md` as the plain-English
CEO handoff card: current situation, trace health, primary action, recommended next command,
approval work status, user-confirmed approval record/apply commands, specialist
work status, completed/blocked role counts, top specialist packet, top blocked
role packet, blocked-role closure command, next role-result command, the current
data-gate import plan, import batches, symbol matrix, candidate unlocks, fresh
preflight handoff, the current sidecar decision packet state, sidecar
quality-remediation status/counts, the current sidecar visual-label work batch,
entry sheet, source-update manifest, rubric, completion audit, why, refused
actions, and evidence refs.
It also writes `manual_gate_clearance_packet.yaml` / `.md`, a cross-gate
decision surface that combines runtime authority, fresh-data readiness,
visual-label completion, and the post-data validation playbook into one
`can_start_post_data_validation` field. A blocked packet is expected while
manual data imports or visual labels are pending. A passing packet only means the
research validation gate can be considered by governed commands; it does not
promote candidates, change production behavior, or authorize product language.
It summarizes status, action-board,
decision-quality, approval queue, role queue, and the latest operator-step
without approving execution.

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
refuses stop requests, true blockers, flight-dashboard-local process-safety blockers, pending
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

Evidence-debt routing must also respect sidecar candidate-learning classes.
When `sidecar_candidate_learning_ledger.yaml` marks a candidate as
`archive_failure_mode`, `ceo evidence-debt-register` should keep it visible as
archived non-promotional learning rather than queueing fresh-data or validation
debts for it.
When a manual fresh-data gate is active, the register must keep the strategic
evidence-debt action visible while separately naming the current runtime
handoff, usually `import_or_curate_fresh_ohlcv_data`. Do not treat
`build_or_run_frozen_validation_executor` as executable while fresh-data
preflight is not ready.

`ceo approval-queue` is the red-authority holding pen. It records promotion
approval, stopped-run resume, and clear-stop decisions as pending user approval
items. `ceo approval-record --approval-id <id> --decision <approved|rejected>
--user-confirmed` appends an immutable decision ledger row only; it does not
apply product changes, clear stop files, or mutate production formulas.
The queue and status artifacts also surface the top pending approval id plus
exact `approval-record` and `approval-apply` command templates so a fresh
session can show the explicit user-confirmed path without inventing an approval
decision.
`approval-record` only accepts a currently pending approval id and stores the
approval kind, source artifact, and approval-item fingerprint in the decision
ledger. `approval-apply` rebuilds the approval queue and requires the recorded
fingerprint to match the current approval item before honoring the ledger row,
so stale approval records cannot clear newer stop requests.

`ceo executive-kpis` is the compact CEO scoreboard. It summarizes open
approvals, evidence debt, candidate count, sidecar candidate-learning
lead/control/archive/review/blocked counts, capability backlog, trace verdict,
score, recommended next action, issues, manual-data flag, loop/no-progress
counts, validation threshold status, top blocker, repair lane, role-queue
readiness, top blocked specialist review/finding/next action, operating
incident count, and product-language safety. Use it to decide whether the
operating system is improving or just creating artifacts. If approvals, repair
lanes, and trace health are clear but role work is pending or blocked, the KPI
next action follows the role queue's closure or evidence action. If the
scoreboard is clear, the KPI next action is
`defer_to_runtime_authority_surface`, which means the operator must check
status/resumption/action-board/preflight instead of treating the KPI card as
permission to dispatch.

`ceo role-queue` turns evidence debts, pending approvals, and capability backlog
items into specialist role tasks for research director, validation referee,
product translator, risk officer, memory editor, and data steward review.
`ceo role-dispatch` writes `role_dispatch.yaml` / `.md` and markdown packets
under `role_dispatch_packets/` for each pending task. Each packet includes the
exact specialist question, source artifacts, review-only authority boundaries,
and expected `riskflow_ceo_specialist_result_v0` schema.
`ceo role-result --task-id <id> --status complete|blocked` records the result in
`role_task_ledger.jsonl` only after validation. Approval/manual-gate tasks carry
`result_resolution_mode: manual_gate_blocked_record`, `approval_authority:
user_only`, the approval-record command as their closure command, and a separate
`--status blocked` result command with no specialist artifact. They cannot be
completed by a specialist YAML artifact. Evidence/capability
tasks carry `result_resolution_mode: specialist_result_required`; completed
non-manual tasks must provide a readable `riskflow_ceo_specialist_result_v0`
YAML artifact whose task/role ids match, whose evidence refs/finding/next action
are present, and whose authority fields keep `product_language_allowed: false`,
`production_effect: none`, and `promotion_authority: none`. Failed validation
writes `role_result_validation.yaml` and does not append the ledger, so an
invalid specialist note cannot close the queue. Blocked tasks may be recorded
without an artifact, but they remain blocked work. Accepted completed results
record the resolved artifact path and SHA-256 in `role_task_ledger.jsonl`.
Rebuilding `ceo role-queue` rechecks that artifact; if it is missing, lacks a
recorded hash, or no longer matches the accepted hash, the task becomes blocked
with `validation_status: provenance_drift` instead of remaining complete. The
queue also records pending manual and pending autonomous counts plus completed
and blocked counts, the top pending task/role/owner command, expected top packet
path, role-dispatch command, result-resolution mode, closure command, and next
role-result command template. It also records the top autonomous pending task,
packet, and result command so review-only specialist work can be routed while a
manual gate remains blocked. Top blocked task, role, packet, result mode,
validation status, closure command, review status, accepted result path,
finding, and next action are first-class fields, so a fresh session can see
whether role-readiness still fails because a result is missing, provenance
drifted, or an accepted blocked specialist finding requires new evidence.
Accepted `--status blocked` specialist results remain blocked work; they
explain the evidence gap rather than close the queue. Older queues without the
closure field are summarized by synthesizing it from the task id and result
mode. `ceo role-dispatch` also marks the top packet directly. If only manual role tasks
remain pending, role-queue next action points to user approval or a manual-gate
blocked record instead of autonomous specialist assignment. Pending,
blocked, or provenance-drifted tasks mean the role lane is not closed for
9.9-readiness, even when a role-result ledger exists. This coordinates
specialist work only; it does not validate statistics or apply production
changes. If no role work remains, role-queue defers to
`defer_to_runtime_authority_surface` rather than claiming dispatch authority.

`ceo org-progress-score` writes `org_progress_score.yaml` / `.md` as an
agent-employee progress diagnostic. It flags pending work, blocked work,
accepted completions without merge receipts, and completed work without decision
deltas. It is diagnostic only and has
`dispatch_authority: not_granted_by_org_progress_score`.

Run-generated promotion proposals now require evidenceful specialist reviews:
`validation_referee` plus either `product_translator` or `risk_officer`.
Completed role tasks must point to structured YAML review artifacts with an
explicit passing/approved review status or decision, matching role/task metadata
when present, `production_effect: none`, and no `product_language_allowed:
true`. A task-level specialist `status: complete` only means the review task was
closed; it is not promotion approval by itself. Missing, unreadable,
mismatched, rejected, non-approving, or unsafe review artifacts are reported as
`completed_specialist_reviews` evidence debt and block
`ready_for_user_approval`. If visual-review evidence is missing, record the
product-translator task as blocked or as a non-approving review; do not let it
authorize product language. If the specialist gate is omitted entirely, the
proposal builder treats it as not evaluated and blocks by default.

`ceo replay` reconstructs a run from append-only ledgers and key artifact
fingerprints, including action, heartbeat, approval, repair-apply, role, preflight, and
guardrail artifacts. It also checks adjacent action transitions against the
previous action's `next_allowed_actions`, so illegal state-machine jumps become
visible. Legacy no-snapshot rows that match known older transition policy are
reported as `legacy_policy_gap` instead of unsafe current transitions; current
receipt-backed or policy-versioned rows remain strict. Repair-apply ledger rows
must include immutable before/after repair-plan snapshot refs and hashes.
Old no-action manual-gate repair-apply rows that predate snapshot support are
reported as `legacy_snapshot_gap`, not as current replay failures. If
`ceo_action_ledger.jsonl` is missing, replay may use
`binding_action_result.yaml` for diagnosis, but that fallback is a replay gap
and is not considered fully replayable.
`ceo eval-suite` grades whether the CEO run is replayable,
state-machine-consistent, contract-consistent, approval-aware, production-safe,
guardrail-audit clean, hard-artifact-coherence clean, dispatch-receipt backed,
validation-gated, role-closure aware, evidence-debt visible, mission-scored, and
strategy-capital aware. This is the first objective 9.9-readiness harness for
CEO mode. Hard failures can block dispatch through preflight. A failing
guardrail audit or a hard artifact-coherence issue now fails 9.9 readiness
directly, not only through preflight. Missing guardrail/coherence payloads do
not default to green. Eval-suite refreshes mission score, guardrail audit, and
artifact coherence before scoring; mutable diagnostic fingerprint drift from
trace/replay/eval/guardrail/mission/coherence remains visible but advisory.
Pending role tasks and invalid completed role results now fail the role-closure
case so the suite cannot claim readiness while specialist work is still waiting.
Advisory readiness gaps, such as a
missing strategy-capital dashboard, lower 9.9 readiness without becoming a red
dispatch blocker by themselves. Dispatch receipt cases check that the latest
binding action has a matching receipt path/hash and that the receipt
fingerprints required dispatch trust artifacts. `memory_delta` is fingerprinted
when present, but preflight enforces hard memory deltas directly and receipt
coverage does not require a memory-delta artifact to exist before first
dispatch.
Before scoring role closure, `ceo eval-suite` refreshes `ceo role-queue` so
accepted specialist artifacts are re-hashed and any post-acceptance drift
becomes blocked `provenance_drift` work.
The role-closure eval evidence includes the top blocked task, role, accepted
blocked review status, recommended evidence action, and finding, so a fresh
session can see why the queue is still open without opening the specialist
artifact first.
Eval-suite also scores live runtime authority directly. A stop request, pending
approval, unsafe preflight, manual-gate action board, waiting operator brief, or
blocked decision-quality runtime authority fails the critical
`runtime_authority_manual_gates_clear` case even when stale diagnostic artifacts
look safe.
For legacy latest actions with no dispatch receipt or transition-policy
evidence, eval-suite does not hard-fail just because current diagnostic
`action_contract.yaml` or `dispatch_receipt.yaml` points at a later decision.
Receipt-backed or policy-versioned current actions remain strict.

`ceo eval-fixtures` runs deterministic policy fixtures for known transition
rules, such as champion/challenger routing to fresh/control validation instead
of generic research and approval waits routing only to approval apply. Fixtures
test the CEO operating policy, not market evidence. Normal run ids always run
the fixture suite; only internal fixture-created subruns can skip nested
fixtures through an explicit non-CLI option, so run naming cannot bypass the
policy regression checks. A skipped or zero-case fixture result fails
`policy_eval_fixtures_pass`; it may be useful for recursion control, but it
cannot count as 9.9 fixture coverage.

`ceo portfolio-allocator` scores CEO operating lanes: approval governance,
validation authority, candidate product translation, evidence debt, research
infrastructure, specialist review, trace reliability, and memory handoff. It
selects the highest-value bottleneck for attention. This is operating guidance
only; it does not validate product evidence or mutate production behavior. Its
actions are labeled `portfolio_attention_only`, and
`dispatch_authority: not_granted_by_portfolio_allocator` means status,
resumption, action-board, preflight, and dispatch-receipt artifacts still own
runtime authority.

`ceo mission-score` scores Riskflow's coverage across bullish permission,
warning/blocker, invalidation, reset quality, gradient interpretation, path
management, cross-asset/regime usefulness, and archive/do-not-repeat memory.
It converts scattered candidates and evidence debt into a plain mission score,
lowest mission dimension, and next required evidence. It is diagnostic only and
does not authorize product language. Its actions are labeled
`mission_strategy_only`, with
`dispatch_authority: not_granted_by_mission_score`.

`ceo strategy-capital-dashboard` allocates 100 `ceo_attention_points` across
approval/safety, validation authority, candidate translation, warning research,
bullish permission research, reset/gradient/path research, cross-asset regime
validation, and archive memory. The points are CEO attention, not trading or
production capital. Approval, stop, failed preflight, failed trace, and
promotion gates outrank research allocation. Non-safety buckets may use
`defer_to_runtime_authority_surface`; that is an attention placeholder, not a
runtime permission.

`ceo resumption-brief` is the one-page cockpit handoff. It inspects preflight,
replay, eval-suite, mission score, strategy capital, and the latest decision
packet to produce a resume status and exact next command. It echoes preflight
trace source status: verdict, score, recommended next action, issues, and
manual-data flag. If preflight is
blocked or a stop request exists, the next command must not be
`execute-next --apply`.

`ceo artifact-coherence` is the same-cockpit, same-flight check. It catches
missing, stale, mismatched, or hard receipt-fingerprint-drifted trust artifacts
so a fresh session does not resume from green lights that belong to an older
action. Mutable diagnostic refresh drift remains visible as evidence, but does
not automatically block dispatch. It also records a live `stop.request` plus
stale safe handoff artifacts as advisory `live_stop_runtime_authority_mismatch`
under `handoff_semantics`.

`ceo dispatch-receipt` is the dispatch audit trail. It answers: these exact
artifact hashes, this action contract, this preflight result, and this approval
state are why the CEO action was allowed or blocked. It does not approve
production behavior.
Binding action writers running under bound dispatch or guarded-direct context
must attach a matching immutable receipt snapshot. If no matching receipt exists,
they create an action contract when needed, require a passing preflight gate, and
write a fresh receipt before appending the action ledger. Blocked/no-op results
can write a blocked receipt from a failed preflight so refusals remain auditable;
unsafe non-blocked actions are refused.

`ceo blocker-stack` is the one-page "why can't the CEO act?" answer. It orders
competing blockers by authority and gives the safest next command from the
current resumption brief, except that a live stop request always forces the
next command to `ceo approval-queue`.

`ceo incident-register` is the "what went wrong and how do we stop repeating
it?" register. It groups recurring operating failures by stable incident key and
records evidence paths/hashes plus closure conditions.

`ceo executive-kpis` includes approval count, evidence debt, trace health,
validation status, top blocker, operating incident count, repair-plan
status/top repair/top repair kind, role readiness, and top blocked specialist
review/finding/next action so the CEO scoreboard points at the current operating
repair or role-evidence lane without overstating autonomy. Failed, warning, or
manual-data-required trace health is itself an attention condition; if
approvals, repairs, and trace health are clear but roles are pending or blocked,
the KPI next action follows the role queue's closure or evidence action.

`ceo run-index` is the fleet board for CEO runs. It scans `reports/ceo_runs`,
summarizes each run's resumption/preflight state, records mission and strategy
summary fields when present, records the latest dispatch-receipt status/reason,
trace-grade verdict/score/recommended next action/manual-data flag/issues,
top blocker, operating incident count, repair-plan status, top repair, top
repair kind, repair-apply status/closure, replay status, operator-step replay
status/count, eval-suite score/readiness blockers, artifact-coherence
status/issue count/top issue/top issue severity/top issue types, approval
status/top approval record-apply commands, and role-result-validation status,
role-queue status, pending role counts, top pending role task, top blocked role
task/closure/review status/result/finding/next action, sidecar candidate-learning
ledger status plus lead/control/archive/review/blocked counts, synthesized
effective operator status, evidence-debt count plus candidate/global/archive
split, and manual-gate-active state. It downgrades cached
"safe" runs to blocked when approval, dispatch, replay, eval, hard
artifact-coherence, action-board, operator-brief, or decision-quality runtime
authority disagrees. Read effective operator status before trusting dispatch
safety. Live stop requests override stale safe artifact fields in the run-index
row: dispatch is shown blocked, operator/decision authority is shown as
`manual_gate_required`, and the next command routes to `ceo approval-queue`. Use it before
resuming from a long/noisy handoff when multiple run ids exist.

`ceo memory-delta` turns the advisory knowledge-graph delta into a governed
handoff artifact. Without `--apply`, it writes `memory_delta.yaml` / `.md` only.
With `--apply`, it writes one curated Obsidian map note when a durable memory
delta is required. The note is routing memory, not runtime authority or product
proof.

`ceo guardrail-audit` scans CEO YAML artifacts, including nested trust snapshots
under `dispatch_receipts/` and `operator_step_boards/`, for accidental
non-`none` production effects or product-language permission. `ceo preflight-gate` unifies
trace, approval, replay, eval, guardrail, artifact-coherence, memory, and
heartbeat-budget status into one dispatch gate. Its source status and CLI output
include trace verdict, score, recommended next action, issues, and manual-data
flag so blocked preflight can explain the trace-level reason without opening raw
YAML. Direct `ceo execute-next` and `heartbeat-tick` both
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
reports/ceo_runs/<run_id>/dispatch_receipt.yaml
reports/ceo_runs/<run_id>/dispatch_receipts/*.yaml
reports/ceo_runs/<run_id>/blocker_stack.yaml
reports/ceo_runs/<run_id>/operating_incident_register.yaml
reports/ceo_runs/<run_id>/repair_plan.yaml
reports/ceo_runs/<run_id>/repair_apply.yaml
reports/ceo_runs/<run_id>/repair_apply_ledger.jsonl
reports/ceo_runs/<run_id>/action_board.yaml
reports/ceo_runs/<run_id>/operator_step.yaml
reports/ceo_runs/<run_id>/operator_step_ledger.jsonl
reports/ceo_runs/<run_id>/operator_step_boards/*.yaml
reports/ceo_runs/<run_id>/operator_brief.yaml
reports/ceo_runs/<run_id>/decision_quality.yaml
reports/ceo_runs/<run_id>/artifact_coherence.yaml
reports/ceo_runs/<run_id>/resumption_brief.yaml
reports/ceo_runs/run_index.yaml
reports/ceo_runs/<run_id>/approval_queue.yaml
reports/ceo_runs/<run_id>/approval_status.yaml
reports/ceo_runs/<run_id>/approval_decision_ledger.jsonl
reports/ceo_runs/<run_id>/approval_apply.yaml
reports/ceo_runs/<run_id>/approval_apply_ledger.jsonl
reports/ceo_runs/<run_id>/executive_kpis.yaml
reports/ceo_runs/<run_id>/role_registry.yaml
reports/ceo_runs/<run_id>/role_task_queue.yaml
reports/ceo_runs/<run_id>/role_dispatch.yaml
reports/ceo_runs/<run_id>/role_result_validation.yaml
reports/ceo_runs/<run_id>/role_task_ledger.jsonl
reports/ceo_runs/<run_id>/mission_score.yaml
reports/ceo_runs/<run_id>/strategy_capital_dashboard.yaml
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

`ceo_flight_dashboard.yaml`, `ceo_operating_dashboard.yaml`, and
`strategy_capital_dashboard.yaml` include scope/authority fields beside
`safe_to_continue`. Treat a true value as "this diagnostic surface did not find
its own blocker," not as permission to run `execute-next`.
`portfolio_allocator.yaml`, `mission_score.yaml`, and
`capability_backlog.yaml` are attention, mission-strategy, and
research-infrastructure surfaces, not dispatch authority. When an advisory lane
or empty backlog has no concrete work, it uses
`defer_to_runtime_authority_surface`; check status, resumption brief,
action-board, and preflight before any bound CEO action.

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
  memory, trace, and risk portfolios, including trace verdict, score,
  recommended next action, issues, loop-meltdown state, and manual-data flag;
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

A single manual data-import gate also blocks dispatch immediately. If the latest
action has `status: manual_gate`, the decision is
`import_or_curate_fresh_ohlcv_data`, or the next action names
`import_or_curate_fresh_ohlcv_data`, trace grade should fail with
`manual_data_import_required` and recommend `stop_for_manual_data_import`.
Preflight, resumption, action-board, and decision-quality must not convert that
state into a safe `execute-next` wrapper. `execute-next` itself also refuses
`import_or_curate_fresh_ohlcv_data` by writing a blocked dispatch receipt and a
`manual_gate` binding result, even if an upstream diagnostic is stale.
Use `ceo data-gate-brief` to summarize the exact blocked sidecar candidates,
required timeframes, CSV import/refresh matrix with expected paths, fresh-data
role blockers, sidecar learning lead/control/archive/review/blocked counts, a
candidate-level data-unlock table, and next verification command. That brief is
diagnostic-only; it does not import data, run validation, or clear the manual
gate.

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
