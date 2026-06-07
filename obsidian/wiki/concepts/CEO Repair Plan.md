---
rf_type: concept
concept_id: ceo_repair_plan
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use repair-plan to rank blocker-stack and incident-register findings into a repair backlog with closure conditions.
not_product_proof: true
---

# CEO Repair Plan

The CEO Repair Plan is the operating repair backlog for CEO mode.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo repair-plan --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/repair_plan.yaml`
- `reports/ceo_runs/<run_id>/repair_plan.md`

## What It Does

It refreshes [[CEO Blocker Stack]] and [[CEO Operating Incident Register]], then
ranks their findings into ordered repair items.

Each repair item includes:

- repair key
- source artifact
- severity
- owner command
- recommended command and governed repair-apply command
- closure condition
- runnable/manual/diagnostic/implementation flags
- command kind
- implementation playbook when code work is required

## Command Kinds

- `runnable_cli`: exact command that Codex can run autonomously.
- `diagnostic_refresh`: exact diagnostic command that refreshes evidence but
  does not repair by itself.
- `manual_gate`: approval, stop clear, production authority, or another user
  gate.
- `implementation_required`: symbolic repair work such as
  `repair_failing_eval_suite_case`, not an executable command.

Diagnostic refreshes are safe to run, but they are counted separately from
runnable repairs because they do not close the repair condition by themselves.

Implementation-required items include structured playbooks naming target files,
target functions, focused test selectors, acceptance criteria, and the evidence
that created the repair. These playbooks are code-work contracts for Codex or a
worker agent. They are deliberately marked non-executable by [[CEO Repair
Apply]].

Use [[CEO Repair Apply]] when one exact repair key should be executed. Repair
Plan stays diagnostic; Repair Apply owns the before/after closure receipt.
Executable repair-plan next commands should point to `ceo repair-apply`, not the
lower-level owner command.

## Boundary

This is diagnostic repair routing only. It does not approve manual gates,
execute repairs, validate market evidence, authorize product language, promote
candidate behavior, or change production behavior.

Related:

- [[CEO Blocker Stack]]
- [[CEO Operating Incident Register]]
- [[CEO Repair Apply]]
- [[CEO Dispatch Receipt]]
- [[CEO Resumption Brief]]
- [[True CEO Autonomy]]
