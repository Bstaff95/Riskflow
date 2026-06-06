---
rf_type: concept
concept_id: ceo_mission_score
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use mission-score to identify which Riskflow mission dimension has the weakest evidence coverage before allocating another CEO block.
not_product_proof: true
---

# CEO Mission Score

The CEO Mission Score turns Riskflow's broad mission into eight scored
dimensions:

- bullish permission
- warning/blocker
- invalidation
- reset quality
- gradient interpretation
- path management
- cross-asset/regime usefulness
- archive/do-not-repeat memory

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo mission-score --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/mission_score.yaml`
- `reports/ceo_runs/<run_id>/mission_score.md`

## CEO Meaning

The score answers whether Riskflow is becoming better at the actual product
mission, not whether the autonomous process merely produced more artifacts.

The lowest mission dimension becomes the default next evidence question unless
approval, stop, preflight, trace, or promotion gates take priority.

## Boundary

This is diagnostic only. It does not validate a candidate, approve product
language, change formulas, change Pine defaults, or mutate production behavior.

Related:

- [[CEO Operating Dashboard]]
- [[CEO Portfolio Allocator]]
- [[CEO Strategy Capital Dashboard]]
- [[Evidence Debt Register]]
- [[Archive Do Not Repeat]]
- [[Process Score Is Not Product Evidence]]
