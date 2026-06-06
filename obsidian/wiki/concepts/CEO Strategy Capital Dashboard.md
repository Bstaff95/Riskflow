---
rf_type: concept
concept_id: ceo_strategy_capital_dashboard
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use strategy-capital-dashboard to allocate CEO attention points across safety, validation, translation, mission gaps, and memory before extended autonomy.
not_product_proof: true
---

# CEO Strategy Capital Dashboard

The CEO Strategy Capital Dashboard converts current CEO state into 100
`ceo_attention_points`.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo strategy-capital-dashboard --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/strategy_capital_dashboard.yaml`
- `reports/ceo_runs/<run_id>/strategy_capital_dashboard.md`

## Buckets

- approval and safety
- validation authority
- candidate translation
- warning/blocker research
- bullish permission research
- reset/gradient/path research
- cross-asset regime validation
- archive memory

## CEO Meaning

This is the first layer that behaves like executive capital allocation. It
combines [[CEO Mission Score]], [[CEO Operating Dashboard]], [[CEO Portfolio
Allocator]], [[Approval Queue]], [[CEO Preflight Gate]], [[Evidence Debt
Register]], [[Capability Backlog]], specialist role queues, and heartbeat state
into one ordered action queue.

Approval, stop, failed preflight, failed trace, and promotion gates outrank
research allocation.

## Boundary

The points are CEO attention, not trading capital and not production capital.
This dashboard does not authorize product language, promotion, formula changes,
Pine/default changes, scores, rankings, states, or alerts.

Related:

- [[True CEO Autonomy]]
- [[CEO Mission Score]]
- [[CEO Portfolio Allocator]]
- [[CEO Preflight Gate]]
- [[Approval Queue]]
- [[Evidence Debt Register]]
- [[Process Score Is Not Product Evidence]]
