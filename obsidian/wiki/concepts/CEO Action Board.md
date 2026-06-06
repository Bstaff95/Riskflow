---
rf_type: concept
concept_id: ceo_action_board
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use action-board as the one-screen CEO operator cockpit before deciding what a fresh session can do next.
not_product_proof: true
---

# CEO Action Board

The CEO Action Board is the operator cockpit for a Riskflow CEO run.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo action-board --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/action_board.yaml`
- `reports/ceo_runs/<run_id>/action_board.md`

## What It Does

It refreshes [[CEO Resumption Brief]], [[CEO Repair Plan]], [[CEO Dispatch
Receipt]], and [[Executive KPIs]], then turns them into one ranked operating
surface.

The board separates:

- primary action
- manual gates
- runnable repairs
- diagnostic refreshes
- implementation repairs
- blocked actions

## Boundary

The board is diagnostic only. It does not execute the primary action, clear
manual gates, approve production changes, validate market evidence, authorize
product language, or change production behavior.

Run at most one bounded action after reading it, then regenerate the board.

Related:

- [[CEO Resumption Brief]]
- [[CEO Repair Plan]]
- [[CEO Dispatch Receipt]]
- [[Executive KPIs]]
- [[True CEO Autonomy]]
