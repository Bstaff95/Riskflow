---
rf_type: concept
concept_id: approval_apply
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Approval application is a second explicit command after approval-record, not a side effect of recording approval.
not_product_proof: true
---

# Approval Apply

`approval-record` is ledger-only. `approval-apply` is the second explicit step
that closes an approved red-authority item.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo approval-apply \
  --run-id <run_id> \
  --approval-id <approval_id> \
  --user-confirmed \
  --apply
```

## Current Behavior

- `promotion_proposal` writes a shadow-only closure artifact and does not mutate
  production behavior.
- `clear_stop_request` can remove CEO/lab stop files only after a recorded
  approval plus this second explicit apply command.
- Unsupported approval ids block and write an audit artifact.

## Guardrail

Approval closure does not authorize silent changes to `core_signal_v0`, Pine
defaults, rankings, scores, states, alerts, raw data, commits, or pushes.

Related:

- [[Approval Queue]]
- [[True CEO Autonomy]]
- [[CEO Eval Suite]]
