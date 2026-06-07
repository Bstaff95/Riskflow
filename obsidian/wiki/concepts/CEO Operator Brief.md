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
- trace health: verdict, score, recommended next action, issues, and manual
  data-import requirement
- effective operator status and manual-gate-active state
- primary action
- effective runtime action and runtime blocked reason
- decision-quality selected route versus runtime authority
- advisory selected route when the strategic route is not executable
- decision-quality executable action, can-execute flag, and blocked-by reason
- recommended next command
- approval work status and user-confirmed record/apply commands
- specialist work status
- specialist pending/completed/blocked counts
- top pending specialist task and packet
- top blocked specialist task, packet, validation, closure command, review
  status, accepted result path, finding, and next action
- top result-resolution mode and closure command
- next role-result command template
- why
- refused actions
- evidence refs

It summarizes [[CEO Action Board]], [[CEO Decision Quality]], [[Trace Grading
For Riskflow]], and the latest [[CEO Operator Step]]. It also summarizes
[[Specialist Role Orchestration]] so a
fresh session can see the highest-priority pending role packet and the top
blocked evidence packet plus closure command without scanning every dispatch
packet. The
decision-quality fields are especially important when a selected strategic
route is sensible but runtime authority still belongs to a manual gate or
diagnostic repair.

Read effective operator status before trusting any selected strategic route.

## Boundary

Operator brief is diagnostic only. It does not approve execution, clear manual
gates, authorize product language, validate market evidence, or change
production behavior.

Related:

- [[CEO Action Board]]
- [[CEO Operator Step]]
- [[CEO Decision Quality]]
- [[Trace Grading For Riskflow]]
- [[True CEO Autonomy]]
