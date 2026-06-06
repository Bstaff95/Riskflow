---
rf_type: concept
concept_id: research_infra_patch_plan
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Route patch_research_infra through governed lane-recovery planning instead of a generic capability gap or blind lab block.
not_product_proof: true
---

# Research Infra Patch Plan

The Research Infra Patch Plan is the bounded CEO route for `patch_research_infra`.

It writes:

- `reports/ceo_runs/<run_id>/research_infra_patch_plan.yaml`
- `reports/ceo_runs/<run_id>/research_infra_patch_plan.md`
- `reports/ceo_runs/<run_id>/research_infra_recovery_queue.yaml`
- `reports/ceo_runs/<run_id>/research_infra_recovery_audit.yaml`

The route uses the existing governed lane-recovery planner. If the audit passes, it may append recovery items to the lab runtime queue.

## Guardrail

This is process infrastructure only. Recovery queue items remain shadow research work with `production_effect: none`.

## Future Action Changed

When a CEO decision says `patch_research_infra`, run the bounded route or inspect its artifact. Do not translate the decision into a generic lab block.

Related:

- [[CEO Heartbeat]]
- [[Action Contract]]
- [[Loop Outcome Card]]
- [[Agentic Research Loop]]
- [[Process Score Is Not Product Evidence]]
