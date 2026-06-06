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

- selected action
- selected score
- runner-up action
- confidence
- expected artifact
- stop condition
- scored alternatives
- why each unselected alternative lost

## Boundary

Decision quality is diagnostic only. It explains routing but does not approve
execution, clear manual gates, validate market evidence, authorize product
language, or change production behavior.

Related:

- [[CEO Action Board]]
- [[CEO Operator Step]]
- [[CEO Strategy Capital Dashboard]]
- [[True CEO Autonomy]]
