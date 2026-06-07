---
rf_type: concept
concept_id: ceo_org_progress_score
status: active
updated_at: 2026-06-07
production_effect: none
future_action_changed: Use org-progress-score to separate real specialist decision movement from role-task activity.
not_product_proof: true
---

# CEO Org Progress Score

`ceo org-progress-score` measures whether the agent-employee layer is producing
decision movement or only activity.

It writes:

- `reports/ceo_runs/<run_id>/org_progress_score.yaml`
- `reports/ceo_runs/<run_id>/org_progress_score.md`

It tracks:

- pending role work;
- blocked role work;
- accepted completed work;
- merge receipts;
- completed work without merge receipts;
- decision-delta evidence;
- fake-progress flags.

## Boundary

This is diagnostic only. It does not merge specialist work, approve manual
gates, validate candidates, or change production behavior.

Related:

- [[Agent Employee Organization V2]]
- [[Specialist Role Orchestration]]
- [[CEO Eval Suite]]
- [[Process Score Is Not Product Evidence]]

