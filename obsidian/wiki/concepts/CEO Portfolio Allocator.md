---
rf_type: concept
concept_id: ceo_portfolio_allocator
status: active
updated_at: 2026-06-07
production_effect: none
future_action_changed: Use portfolio-allocator to choose the highest-value CEO operating lane before extended autonomy.
not_product_proof: true
---

# CEO Portfolio Allocator

The CEO portfolio allocator ranks operating lanes by urgency and value of
information. It is the first Riskflow primitive for treating CEO mode as capital
allocation rather than task execution.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo portfolio-allocator --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/portfolio_allocator.yaml`
- `reports/ceo_runs/<run_id>/portfolio_allocator.md`

## Lanes

- approval governance
- validation authority
- candidate product translation
- evidence debt
- research infrastructure
- specialist review
- trace reliability
- memory handoff

## Boundary

The allocator chooses operating attention. It does not validate a signal,
approve product language, mutate production behavior, or replace [[CEO Eval
Suite]].

Current artifacts label this boundary directly:

- top-level `action_scope: portfolio_attention_only`
- lane-level `action_scope: portfolio_attention_only`
- `dispatch_authority: not_granted_by_portfolio_allocator`
- `runtime_authority_note` points dispatch decisions back to status, approvals,
  action board, resumption brief, preflight gate, and dispatch receipt

When an advisory lane has no concrete work, its `next_action` is
`defer_to_runtime_authority_surface`. That points the operator back to [[CEO
Action Board]], [[CEO Resumption Brief]], [[CEO Preflight Gate]], and [[CEO Run
Index]]; it is not permission to dispatch.

For mission-level coverage and cross-lane attention points, use [[CEO Mission
Score]] and [[CEO Strategy Capital Dashboard]].

Related:

- [[True CEO Autonomy]]
- [[CEO Eval Suite]]
- [[CEO Operating Dashboard]]
- [[CEO Mission Score]]
- [[CEO Strategy Capital Dashboard]]
- [[Executive KPIs]]
- [[Evidence Debt Register]]
- [[Specialist Role Orchestration]]
