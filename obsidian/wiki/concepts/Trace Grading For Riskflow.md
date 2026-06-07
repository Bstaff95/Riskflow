---
rf_type: concept
concept_id: trace_grading_for_riskflow
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Run trace-grade before continuing or judging CEO autonomy, and treat the result as process-only.
not_product_proof: true
---

# Trace Grading For Riskflow

Trace grading means evaluating an agent workflow by inspecting the full path of model decisions, tool calls, handoffs, guardrails, and outputs, not just the final result.

## Riskflow Translation

Riskflow CEO and lab runs already write trace-like artifacts:

- `reports/ceo_runs/<run_id>/ceo_action_ledger.jsonl`
- `reports/ceo_runs/<run_id>/action_contract.yaml`
- `reports/ceo_runs/<run_id>/binding_action_result.yaml`
- `reports/ceo_runs/<run_id>/ceo_self_audit.yaml`
- `reports/lab_ops/<run_id>/run_journal.jsonl`
- `reports/lab_ops/<run_id>/governance/block_*/research_map.yaml`

The first repeatable grader now exists:

```bash
PYTHONPATH=src python3 -m riskflow ceo trace-grade --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/trace_grade.yaml`
- `reports/ceo_runs/<run_id>/trace_grade.md`

## Candidate Grading Criteria

- Did the loop inspect the required artifacts before acting?
- Did it choose exactly one bounded main action?
- Did the action match the latest CEO decision packet?
- If an [[Action Contract]] exists, did it match the binding action?
- Did it produce belief movement, validation, a capability gap, or a stop decision?
- Did it avoid production changes?
- Did its evidence provenance point to the artifacts that actually changed the action?
- Did it avoid a named prior no-progress failure instead of repeating it?
- Did loop meltdown detection flag repeated manual gates, repeated no-progress
  fingerprints, or unresolved capability-builder loops?
- Did it update durable memory only when the finding was worth preserving?
- Did it avoid repeating the same no-progress action?

## Product Value

This would make long flights or overnight sessions less dependent on chat continuity. A future Codex session could read a compact loop-grade report and know whether the prior autonomy actually compounded learning.

## First Trace Grade

On `2026-06-05`, the grader was first run against `ceo_supervised_chain_20260531`.

Initial result before the fresh/control support update:

- score: `85`
- verdict: `warn`
- latest decision: `run_champion_challenger`
- stop requested: `true`
- issue: `unsupported_next_action`
- unsupported action: `run_fresh_or_control_validation_for_promising_shadow_challengers`
- recommended next action: `honor_stop_request`

Historical note:

The live files at `reports/ceo_runs/ceo_supervised_chain_20260531/trace_grade.yaml` and `.md` are overwritten by reruns. They now show the post-update grade below, not the initial `85`/`warn` result.

## 2026-06-05 Support Update

The unsupported next action above now has a bounded executor:

```bash
PYTHONPATH=src python3 -m riskflow ceo fresh-control-validation --run-id <run_id> --apply
```

Trace grading should now treat `run_fresh_or_control_validation_for_promising_shadow_challengers` as supported. The plan it writes is still not validation proof; it only routes the next safe action.

Trace grading now also reports [[Execution Provenance]] and [[Failure Avoidance Rate]] fields. These are process-quality checks: they can show whether a CEO loop is becoming more inspectable and less repetitive, but they cannot promote a Riskflow signal.

Trace grading also reports [[Loop Meltdown Detection]]. If
`loop_meltdown.strategy_change_required` is true, the next heartbeat must follow
the recommended intervention rather than continue generic research. A repeated
manual gate means stop for manual data import or curation until CSV state
changes.

A single manual data-import gate is also blocking. If the latest action has
`status: manual_gate`, the decision is `import_or_curate_fresh_ohlcv_data`, or
the next action names `import_or_curate_fresh_ohlcv_data`, trace grade should
fail with `manual_data_import_required` and recommend
`stop_for_manual_data_import`. That prevents preflight, resumption, action
board, and decision quality from advertising a safe `execute-next` wrapper for
manual CSV work. `execute-next` also refuses
`import_or_curate_fresh_ohlcv_data` directly by writing a blocked dispatch
receipt and `manual_gate` binding result.

Trace grades also carry `trace_scope: process_only`, `product_evidence_status: not_evaluated`, and `product_language_allowed: false`.

The trace verdict, score, recommended next action, issues, and manual
data-import requirement are now first-class handoff fields in [[CEO Operator
Brief]], [[CEO Run Index]], and `ceo status`. A fresh session should not need to
open raw YAML just to learn why trace blocked dispatch.

## 2026-06-06 Repair Route Update

Trace grading now treats `repair_fresh_withheld_contract_inputs` as a supported
bounded repair route. It is not a new executor capability. `execute-next` maps
that route back to `ceo frozen-candidate-validation`, which is the existing
bounded command that rebuilds missing fresh/withheld contract inputs before the
contract is retried.

Rerunning trace grade on `ceo_supervised_chain_20260531` now removes the
unsupported-next-action issue for this repair route. The old run still fails
trace because stop files, self-audit intervention, repeated prior failure, and
loop meltdown remain part of the operating contract.

Related:

- [[Agentic Research Loop]]
- [[Lab Loop]]
- [[Agentic Loop Research Map]]
- [[Champion Challenger Shadow Mode]]
- [[Execution Provenance]]
- [[Failure Avoidance Rate]]
- [[Loop Meltdown Detection]]
- [[Process Score Is Not Product Evidence]]
