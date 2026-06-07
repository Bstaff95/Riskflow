---
rf_type: concept
concept_id: ceo_decision_quality
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use decision-quality to inspect why CEO mode selected one action over the runner-up before execution.
not_product_proof: true
---

# CEO Decision Quality

CEO Decision Quality is the explainable routing card for CEO mode.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo decision-quality --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/decision_quality.yaml`
- `reports/ceo_runs/<run_id>/decision_quality.md`

## What It Shows

- effective runtime action
- effective runtime command kind
- effective runtime can-execute flag
- runtime blocked flag and block reason
- selected action
- selected strategic route advisory when the selected route is not executable
- selected score
- runner-up action
- confidence
- expected artifact
- stop condition
- runtime authority status from [[CEO Action Board]]
- executable next action and command
- whether the executable action can run now
- runtime-authorized strategic route when a safe `execute-next` wrapper is the executable action
- what blocks the selected strategic route when a manual gate or other higher-authority item outranks it
- scored alternatives
- why each unselected alternative lost

## Boundary

Decision quality is diagnostic only. It explains routing but does not approve
execution, clear manual gates, validate market evidence, authorize product
language, or change production behavior.

When the selected action differs from the current action-board authority,
`selected_action_blocked_by` is the plain safety answer. For example, a selected
validation or research route can remain strategically sensible while a manual
gate is still the only lawful runtime authority.

Read effective runtime fields first. `selected_action` is the strategic routing
choice; it is not permission to act unless `selected_action_is_executable_now`
is true. When it is false, `selected_strategic_route_advisory` repeats the
selected route as advisory-only.

When [[CEO Action Board]] exposes a safe bounded `execute-next` wrapper, the
wrapper is the operator action and the selected action is the strategic route
behind it. The authorized strategic route must come from the resumption/action
board route contract, not from decision quality's own selected action. In that
case `runtime_authorized_strategic_route` should match the selected action and
`selected_action_is_executable_now` can be true only when the primary command is
the bounded `execute-next` wrapper. If the route does not match, or if the
command is not the bounded wrapper, decision quality must show the selected
action as blocked by the different executable wrapper.

If [[CEO Action Board]] status is `manual_gate_required`, decision quality must
force runtime execution off even if a stale primary action still says
`can_execute_now: true`. Manual-gate board status outranks wrapper route
matching.

Related:

- [[CEO Action Board]]
- [[CEO Operator Step]]
- [[CEO Strategy Capital Dashboard]]
- [[True CEO Autonomy]]
