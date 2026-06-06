---
rf_type: concept
concept_id: failure_avoidance_rate
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Use trace-grade failure-avoidance status to stop direct repeats of named no-progress conditions.
not_product_proof: true
---

# Failure Avoidance Rate

Failure Avoidance Rate is a useful way to evaluate whether a research loop actually learned from past errors.

In Riskflow terms, the question is:

> When the same failure condition appears again, does the loop avoid it and route somewhere better?

Examples:

- old stop file present -> honor stop instead of continuing
- no supported recovery specs -> broaden supported lanes instead of repeating the same recovery scan
- promising shadow challenger -> route to fresh/control validation instead of product language
- missing mixed metric sources -> repair sources without blocking the whole candidate family
- unresolved self-audit -> resolve intervention instead of executing the same action again

## Riskflow Measurement

Riskflow can approximate this locally by comparing:

- previous `binding_action_result.yaml`
- `next_allowed_actions`
- current `decision_packet.yaml`
- current `action_contract.yaml`
- current `action_outcome_card.yaml`
- `trace_grade.yaml`

The score should ask whether the next action avoided a named prior failure, not whether the loop produced more artifacts.

## Future Action Changed

If `trace_grade.yaml` reports `repeated_prior_failure`, the next heartbeat must route to research-infra repair, hypothesis-source broadening, fresh-data request, or stop. It should not repeat the same decision again.

If `trace_grade.yaml` reports `loop_meltdown.strategy_change_required`, treat
that as a stronger no-repeat signal. Repeated manual gates should stop for data
import or curation; repeated capability-builder loops should build the missing
capability or stop.

Related:

- [[Trace Grading For Riskflow]]
- [[Loop Meltdown Detection]]
- [[Archive Do Not Repeat]]
- [[Archive Do Not Repeat - CEO 20260531]]
- [[Loop Outcome Card]]
- [[Process Score Is Not Product Evidence]]
