---
rf_type: concept
concept_id: loop_outcome_card
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Inspect the last action's progress class, provenance, failure avoidance, product-evidence gap, and next allowed actions before repeating or routing.
not_product_proof: true
---

# Loop Outcome Card

A Loop Outcome Card is a compact wake-to-wake summary for a Riskflow CEO action.

## Riskflow Implementation

Every binding CEO action now writes:

- `reports/ceo_runs/<run_id>/action_outcome_card.yaml`
- `reports/ceo_runs/<run_id>/action_outcome_card.md`

This applies to new bound actions after the implementation. Older stopped runs may not contain outcome cards for historical actions.

The card pairs with [[Action Contract]] and summarizes:

- decision
- action taken
- status
- progress class
- next allowed actions
- evidence provenance
- failure-avoidance status
- product-evidence delta and missing product evidence
- self-audit status
- whether a memory delta is required
- forbidden production changes

## Why It Matters

Long agentic loops fail when a future wake has to reconstruct intent from scattered artifacts. The outcome card makes the next heartbeat inspect the last action directly before choosing whether to continue, repair memory, build capability, request fresh data, or stop.

The card is not evidence that a market candidate is valid. It is process evidence for the agentic loop.

## Future Action Changed

If the outcome card says `product_language_allowed: false`, future reports must keep product language in shadow/planning terms until fresh/control evidence and visual review justify stronger wording.

Related:

- [[CEO Heartbeat]]
- [[Action Contract]]
- [[Trace Grading For Riskflow]]
- [[Agentic Research Loop]]
- [[Agent Memory As Research Infrastructure]]
- [[Archive Do Not Repeat]]
- [[Process Score Is Not Product Evidence]]
