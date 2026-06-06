---
rf_type: concept
concept_id: evidence_debt_register
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Use evidence-debt-register to choose the next product-evidence debt to retire before promotion or product-language review.
not_product_proof: true
---

# Evidence Debt Register

The Evidence Debt Register is the CEO layer's per-candidate queue of missing product evidence.

It turns promotion blockers into actionable work items:

- candidate id
- product role
- blocking artifact
- missing evidence kind
- owner command
- promotion ceiling
- product-language block

## Command

```bash
PYTHONPATH=src python3 -m riskflow ceo evidence-debt-register --run-id <run_id>
```

It writes:

- `evidence_debt_register.yaml`
- `evidence_debt_register.md`

## CEO Meaning

This register is the bridge between [[CEO Operating Dashboard]] and [[Promotion Proposal Gate]].

The dashboard says where candidates sit. The promotion proposal says whether product review is blocked. The evidence-debt register says what exact missing proof must be retired next.

After [[Frozen Candidate Validation]] source replay, a missing passing result
routes to fresh or withheld validation. It should not loop back into source
replay.

It does not validate, promote, or change production behavior.

Related:

- [[CEO Operating Dashboard]]
- [[Promotion Proposal Gate]]
- [[Frozen Candidate Validation]]
- [[Champion Challenger Shadow Mode]]
- [[Process Score Is Not Product Evidence]]
- [[True CEO Autonomy]]
