---
rf_type: concept
concept_id: ceo_heartbeat
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Run exactly one bound CEO action per heartbeat and inspect the resulting action contract, outcome card, self-audit, and trace grade.
not_product_proof: true
---

# CEO Heartbeat

The CEO Heartbeat is Riskflow's supervised autonomy loop for multi-hour work.

It is the concrete Riskflow implementation of [[Agentic Research Loop]].

It should act like an executive operator, not a command repeater:

```text
inspect -> diagnose -> execute one bounded action -> audit -> report
```

## Riskflow Role

The heartbeat reads CEO and lab artifacts, chooses one bounded action, then records whether the action improved research infrastructure, understanding, or chart-facing value.

The durable operating contract is `docs/CEO_HEARTBEAT_AUTONOMY.md`.

## Required Guardrails

- no production formula changes
- no Pine or TradingView default changes
- no production score, ranking, state, or alert changes
- no commit or push without explicit user approval
- no blind loop if stop files, true blockers, capability gaps, or production-promotion decisions appear

## Current Research Question

Can every CEO heartbeat produce a loop outcome card that future sessions can grade without reading every raw report?

## Future Action Changed

If a heartbeat sees stop files, true blockers, a production-promotion gate, an unresolved self-audit intervention, or a repeated no-progress route, it must not run another generic lab block.

Related:

- [[Agentic Research Loop]]
- [[Trace Grading For Riskflow]]
- [[Agentic Loop Research Map]]
- [[Lab Loop]]
