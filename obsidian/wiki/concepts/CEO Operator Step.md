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

After the attempt or refusal, it refreshes [[CEO Action Board]] again and records
before/after status.

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
- [[True CEO Autonomy]]
