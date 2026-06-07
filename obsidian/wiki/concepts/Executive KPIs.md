---
rf_type: concept
concept_id: executive_kpis
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use executive-kpis as the compact CEO scoreboard for approvals, evidence debt, candidates, validation, trace health, repair lane, role readiness, and product-language safety.
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
- trace score, verdict, recommended next action, issues, and manual data-import
  requirement
- loop/no-progress repeat counts
- fresh/withheld validation threshold status
- promotion status
- top blocker
- repair-plan status
- top repair
- top repair kind
- repair next command
- role queue status
- role pending, completed, and blocked counts
- top blocked specialist task, role, accepted blocked review status, next action,
  and finding
- role next action
- product-language safety

Executive KPIs are process and governance metrics. They are not product evidence and do not validate a candidate.

Failed, warning, or manual-data-required [[Trace Grading For Riskflow]] is an
attention condition. When approvals and repair lanes are clear, the KPI next
action follows the trace-grade recommendation instead of claiming the operating
system is clear.

Pending or blocked [[Specialist Role Orchestration]] work is also an attention
condition. If approvals, repair lanes, and trace health are clear, the KPI next
action follows the role queue's next closure or evidence action.

When the scoreboard is clear, `next_action` is
`defer_to_runtime_authority_surface`. That means the KPI card has no operating
blocker to add; [[CEO Action Board]], [[CEO Resumption Brief]], and [[CEO
Preflight Gate]] still own runtime authority.

Related:

- [[Approval Queue]]
- [[CEO Operating Dashboard]]
- [[CEO Repair Plan]]
- [[Evidence Debt Register]]
- [[Trace Grading For Riskflow]]
- [[True CEO Autonomy]]
