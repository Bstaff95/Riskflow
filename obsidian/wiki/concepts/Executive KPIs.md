---
rf_type: concept
concept_id: executive_kpis
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use executive-kpis as the compact CEO scoreboard for approvals, evidence debt, candidates, validation, trace health, repair lane, and product-language safety.
not_product_proof: true
---

# Executive KPIs

Executive KPIs are the compact operating scoreboard for CEO mode.

They answer whether the Riskflow operating system is getting clearer, safer, and more decisive, instead of merely creating more artifacts.

## Command

```bash
PYTHONPATH=src python3 -m riskflow ceo executive-kpis --run-id <run_id>
```

It writes:

- `executive_kpis.yaml`
- `executive_kpis.md`

## Tracked Signals

- open approval count
- evidence debt count
- candidate count
- capability backlog count
- trace score and verdict
- loop/no-progress repeat counts
- fresh/withheld validation threshold status
- promotion status
- top blocker
- repair-plan status
- top repair
- top repair kind
- repair next command
- product-language safety

Executive KPIs are process and governance metrics. They are not product evidence and do not validate a candidate.

Related:

- [[Approval Queue]]
- [[CEO Operating Dashboard]]
- [[CEO Repair Plan]]
- [[Evidence Debt Register]]
- [[Trace Grading For Riskflow]]
- [[True CEO Autonomy]]
