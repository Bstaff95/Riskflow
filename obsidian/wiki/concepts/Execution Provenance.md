---
rf_type: concept
concept_id: execution_provenance
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Require CEO outcome cards and trace grades to name the input and output artifacts that changed the next action.
not_product_proof: true
---

# Execution Provenance

Execution provenance is the record of how an agent reached an output:

- which artifact or memory item influenced the decision
- which tool was called
- which command was allowed
- which output was produced
- which claim depended on which evidence
- which recovery route was selected after failure

For Riskflow, provenance should be file-first:

```text
decision packet -> action contract -> command/report -> action ledger -> outcome card -> trace grade -> Obsidian memory
```

## Riskflow Rule

Every autonomous CEO action should leave enough provenance for a fresh session to answer:

- why this action was selected
- what it was allowed to change
- what it actually changed
- what evidence supports the next action
- what would make repeating it invalid

## Product Guardrail

Provenance explains a result; it does not validate the market signal. A clean trace still needs [[Fresh Data Validation Gate]], deterministic evidence checks, and product-language restraint.

## Future Action Changed

When a future wake cannot identify which artifact caused the next action, treat the trace as incomplete and repair provenance before continuing autonomy.

Related:

- [[Action Contract]]
- [[Loop Outcome Card]]
- [[Trace Grading For Riskflow]]
- [[Process Score Is Not Product Evidence]]
- [[Agentic Research Loop]]
