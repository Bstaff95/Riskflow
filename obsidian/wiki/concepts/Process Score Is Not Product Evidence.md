---
rf_type: concept
concept_id: process_score_is_not_product_evidence
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Treat trace-grade, lab-meta, outcome-card, and memory-quality passes as process evidence only until product gates pass.
not_product_proof: true
---

# Process Score Is Not Product Evidence

Autonomous research loops can become better at satisfying their own process checks while becoming less useful for the actual product.

For Riskflow, process evidence includes:

- trace-grade scores
- loop outcome cards
- action contracts
- Obsidian memory quality
- lab-meta and governance scores
- agent critique quality

Product evidence is different:

- relative forward-return improvement versus the relevant basket
- fresh or withheld data survival
- false-positive reduction on chart review
- missed-winner analysis
- clearer entry, invalidation, or avoidance behavior
- transparent user-facing explanation

## Rule

Process scores can keep the lab orderly, but they cannot promote a signal.

Any process score above threshold must still route through:

```text
deterministic evidence -> fresh/control gate -> visual review -> product-language restraint
```

## Riskflow Implication

- `ceo trace-grade` should decide whether a CEO loop is inspectable and non-repeating.
- It should not decide whether a grammar candidate is useful.
- [[Loop Outcome Card]] should record what changed and what evidence is still missing.
- [[Fresh Data Validation Gate]] should remain the first product-evidence gate after strict historical survival.

Related:

- [[Agentic Loop Research Map]]
- [[Lab Loop]]
- [[Trace Grading For Riskflow]]
- [[Loop Outcome Card]]
- [[Fresh Data Validation Gate]]
