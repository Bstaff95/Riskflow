---
rf_type: concept
concept_id: promotion_proposal_gate
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Use promotion-proposal to summarize candidate evidence for user review only, and block promotion when validation evidence is incomplete.
not_product_proof: true
---

# Promotion Proposal Gate

The Promotion Proposal Gate is the final CEO-side artifact before any production change discussion.

It does not promote anything. It writes a proposal for user review and names the missing evidence if the candidate is not ready.

## Command

```bash
PYTHONPATH=src python3 -m riskflow ceo promotion-proposal --run-id <run_id>
```

It writes:

- `promotion_proposal.yaml`
- `promotion_proposal.md`

Use [[Evidence Debt Register]] to turn blocked proposal evidence into a concrete owner-command queue.

## Blocks By Default

The proposal blocks when evidence is missing:

- frozen candidate specs
- completed fresh/withheld validation execution
- passing fresh/withheld threshold result
- visual review queue or labels
- safe fresh-data preflight
- passing trace grade
- structured passing specialist reviews from validation referee plus product translator or risk officer

## Approval Boundary

Even if a future proposal reaches `ready_for_user_approval`, it still requires explicit user approval before any formula, Pine, score, state, ranking, or alert change. Use [[Approval Queue]] to record that pending red-authority decision.

Related:

- [[True CEO Autonomy]]
- [[Frozen Candidate Validation]]
- [[CEO Operating Dashboard]]
- [[Evidence Debt Register]]
- [[Approval Queue]]
- [[Process Score Is Not Product Evidence]]
- [[Action Contract]]
