---
rf_type: concept
concept_id: hypothesis_source_broadening
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Route broaden_hypothesis_source through Obsidian/research-source queue compilation instead of repeating saturated research families.
not_product_proof: true
---

# Hypothesis Source Broadening

Hypothesis Source Broadening is the bounded CEO route for `broaden_hypothesis_source`.

It writes:

- `reports/ceo_runs/<run_id>/hypothesis_source_broadening_plan.yaml`
- `reports/ceo_runs/<run_id>/hypothesis_source_broadening_plan.md`
- `reports/ceo_runs/<run_id>/hypothesis_source_broadening_queue.yaml`

The route compiles Obsidian setup journeys and research grammar sources into shadow lab queue items.

## Guardrail

Compiled hypotheses are source-broadening candidates, not product evidence. They must still run through the lab loop, strict referee, fresh/control validation, and visual review before product language.

## Future Action Changed

When the lab has no open lane or useful chart-facing candidate, broaden sources through this route before burning budget on another same-family loop.

Related:

- [[Agent Memory As Research Infrastructure]]
- [[Memory Quality Gate]]
- [[Lab Loop]]
- [[Agentic Research Loop]]
- [[Process Score Is Not Product Evidence]]
