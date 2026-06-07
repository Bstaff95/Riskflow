---
rf_type: concept
concept_id: ceo_operator_step
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use operator-step as the audited one-step CEO transaction when the action board says bounded dispatch is safe.
not_product_proof: true
---

# CEO Operator Step

CEO Operator Step is the guarded "do the next safe thing" command for CEO mode.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo operator-step --run-id <run_id> --apply
```

It writes:

- `reports/ceo_runs/<run_id>/operator_step.yaml`
- `reports/ceo_runs/<run_id>/operator_step.md`

## What It Does

It refreshes [[CEO Action Board]], reads the primary action, and executes exactly
one internal bounded `execute-next` dispatch only when the board says bounded
dispatch is safe.

It does not execute repair-plan items. Use [[CEO Repair Apply]] for one exact,
allowlisted repair key.

After the attempt or refusal, it refreshes [[CEO Action Board]] again and records
before/after status plus the executed action's `meaningful_progress` flag.
It also writes immutable before/after action-board snapshots under
`operator_step_boards/` and records their SHA-256 hashes in
`operator_step.yaml`. Each step appends `operator_step_ledger.jsonl`, and
[[CEO Replay]] checks that the ledger's board snapshot paths and hashes are
still valid.

Manual-gate results, capability gaps without progress, and explicit no-progress
results are not counted as useful execution. They receive distinct
operator-step statuses so the next session can tell the difference between
"work was done" and "the bounded dispatch hit a wall."

## Refusals

It refuses:

- manual gates
- diagnostic refreshes counted as repairs
- implementation-required repairs
- unsupported command kinds
- arbitrary shell commands from YAML

## Boundary

It cannot clear approvals, approve production changes, change formulas, change
Pine defaults, authorize product language, or validate market evidence by
itself.

Related:

- [[CEO Action Board]]
- [[CEO Dispatch Receipt]]
- [[CEO Preflight Gate]]
- [[CEO Repair Plan]]
- [[CEO Repair Apply]]
- [[True CEO Autonomy]]
