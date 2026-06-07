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

When another report path passes freshly generated artifacts into the board, the
board must only reuse artifacts with matching run/lab ids and must still recheck
the live stop/manual-gate state before exposing a bounded action.

The board separates:

- primary action
- manual gates
- runnable repairs
- diagnostic refreshes
- implementation repairs
- blocked actions

If any manual gate exists, the board must not leave lower-priority work in
`runnable_repairs`. It demotes otherwise-runnable items into blocked actions
with `blocked_by_runtime_authority: manual_gate_required`. This matters because
a fresh session or agent may scan queue fields directly; the artifact should not
require priority-rule knowledge to avoid unsafe execution.

When the primary action is a repair-plan item rather than bounded dispatch, use
[[CEO Repair Apply]] to execute a specific allowlisted repair key.

## Boundary

The board is diagnostic only. It does not execute the primary action, clear
manual gates, approve production changes, validate market evidence, authorize
product language, or change production behavior.

Run at most one bounded action after reading it, then regenerate the board.

Related:

- [[CEO Resumption Brief]]
- [[CEO Repair Plan]]
- [[CEO Repair Apply]]
- [[CEO Dispatch Receipt]]
- [[Executive KPIs]]
- [[True CEO Autonomy]]
