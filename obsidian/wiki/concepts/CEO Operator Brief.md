---
rf_type: concept
concept_id: ceo_operator_brief
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use operator-brief as the plain-English CEO handoff card before deciding what to do next.
not_product_proof: true
---

# CEO Operator Brief

CEO Operator Brief is the plain-English handoff card for CEO mode.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo operator-brief --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/operator_brief.yaml`
- `reports/ceo_runs/<run_id>/operator_brief.md`

## What It Shows

- current situation
- primary action
- recommended next command
- why
- refused actions
- evidence refs

It summarizes [[CEO Action Board]], [[CEO Decision Quality]], and the latest
[[CEO Operator Step]].

## Boundary

Operator brief is diagnostic only. It does not approve execution, clear manual
gates, authorize product language, validate market evidence, or change
production behavior.

Related:

- [[CEO Action Board]]
- [[CEO Operator Step]]
- [[CEO Decision Quality]]
- [[True CEO Autonomy]]
