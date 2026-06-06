---
rf_type: concept
concept_id: ceo_operating_dashboard
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Use operating-dashboard to inspect candidate, capability, data, memory, trace, and risk portfolios before choosing a CEO action.
not_product_proof: true
---

# CEO Operating Dashboard

The CEO Operating Dashboard is the portfolio view for Riskflow autonomy.

It differs from the flight dashboard:

- flight dashboard answers whether it is safe to continue
- operating dashboard answers where CEO attention should be allocated

## Command

```bash
PYTHONPATH=src python3 -m riskflow ceo operating-dashboard --run-id <run_id>
```

It writes:

- `ceo_operating_dashboard.yaml`
- `ceo_operating_dashboard.md`

## Portfolios

The dashboard combines:

- candidate portfolio
- [[Capability Backlog]]
- [[Evidence Debt Register]]
- [[Approval Queue]]
- [[Executive KPIs]]
- data gate
- memory portfolio
- trace and loop-meltdown status
- risk portfolio

## CEO Meaning

This is a step toward [[True CEO Autonomy]]. It lets a fresh session inspect the state of the research company without reading every generated artifact first.

It is still process state only. It does not validate candidates, change formulas, or authorize product language.

Related:

- [[True CEO Autonomy]]
- [[Capability Backlog]]
- [[Evidence Debt Register]]
- [[Approval Queue]]
- [[Executive KPIs]]
- [[CEO Heartbeat]]
- [[Action Contract]]
- [[Loop Meltdown Detection]]
- [[Frozen Candidate Validation]]
- [[Process Score Is Not Product Evidence]]
