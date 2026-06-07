---
rf_type: concept
concept_id: ceo_operating_dashboard
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use operating-dashboard to inspect candidate, capability, role readiness, data, memory, trace, and risk portfolios before choosing a CEO action.
not_product_proof: true
---

# CEO Operating Dashboard

The CEO Operating Dashboard is the portfolio view for Riskflow autonomy.

It differs from the flight dashboard:

- flight dashboard answers whether its own process-safety checks found a blocker
- operating dashboard answers where CEO attention should be allocated

The `safe_to_continue` field is not dispatch authority. The generated YAML,
markdown, and CLI output include `safe_to_continue_scope`,
`dispatch_authority`, and `runtime_authority_note`; actual action authority
still comes from `ceo status`, [[Approval Queue]], [[CEO Action Board]], [[CEO
Resumption Brief]], [[CEO Preflight Gate]], and [[CEO Dispatch Receipt]].

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
- [[Specialist Role Orchestration]]
- data gate
- memory portfolio
- trace verdict, score, recommended next action, issues, loop-meltdown status,
  and manual data-import requirement
- role orchestration status, pending/completed/blocked counts, and top blocked
  specialist review/finding/next action
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
- [[Trace Grading For Riskflow]]
- [[Loop Meltdown Detection]]
- [[Frozen Candidate Validation]]
- [[Process Score Is Not Product Evidence]]
