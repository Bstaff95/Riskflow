---
rf_type: concept
concept_id: action_contract
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Inspect allowed command, scope, expected artifacts, stop conditions, and forbidden changes before running a CEO action.
not_product_proof: true
---

# Action Contract

An Action Contract declares what a CEO heartbeat is allowed to do before it acts.

## Riskflow Implementation

`ceo execute-next` now writes:

- `reports/ceo_runs/<run_id>/action_contract.yaml`
- `reports/ceo_runs/<run_id>/action_contract.md`

The contract records:

- selected decision
- rationale
- allowed command
- allowed scope
- input artifacts
- expected artifacts
- stop conditions
- forbidden production changes

## Why It Matters

Agentic loops drift when the action is only implied by a plan. The contract makes the intended action explicit before execution, then [[Loop Outcome Card]] records what actually happened after execution.

For Riskflow, this is another protection against silently converting a product-delta, fresh-data, or capability-gap decision into a generic lab block.

## Future Action Changed

If the contract's decision does not match the binding action, or if the allowed command/scope is missing for a continuable CEO decision, stop the heartbeat and repair the route before executing.

Related:

- [[CEO Heartbeat]]
- [[Loop Outcome Card]]
- [[Trace Grading For Riskflow]]
- [[Agentic Research Loop]]
- [[Agent Memory As Research Infrastructure]]
