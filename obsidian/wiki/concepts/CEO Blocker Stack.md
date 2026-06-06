---
rf_type: concept
concept_id: ceo_blocker_stack
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use blocker-stack when CEO mode is blocked and a fresh session needs the ordered reason and safest next command.
not_product_proof: true
---

# CEO Blocker Stack

The CEO Blocker Stack is the one-page answer to: why can't CEO mode act?

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo blocker-stack --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/blocker_stack.yaml`
- `reports/ceo_runs/<run_id>/blocker_stack.md`

## What It Orders

- Stop requests.
- Pending [[Approval Queue]] items.
- [[CEO Preflight Gate]] blockers.
- [[CEO Dispatch Receipt]] blocked state.
- [[CEO Replay]] gaps.
- [[CEO Eval Suite]] blocking cases.
- [[CEO Memory Delta]] requirements.
- [[Evidence Debt Register]] work.

## Boundary

This is diagnostic synthesis only. It does not clear blockers, approve
promotions, execute actions, validate market evidence, authorize product
language, or change production behavior.

Related:

- [[CEO Resumption Brief]]
- [[CEO Dispatch Receipt]]
- [[CEO Preflight Gate]]
- [[CEO Replay]]
- [[CEO Eval Suite]]
- [[True CEO Autonomy]]
