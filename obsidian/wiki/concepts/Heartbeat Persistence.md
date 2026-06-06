---
rf_type: concept
concept_id: heartbeat_persistence
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use heartbeat-plan, heartbeat-tick, and heartbeat-journal to make long CEO runs resumable and auditable across wakes.
not_product_proof: true
---

# Heartbeat Persistence

Heartbeat Persistence is the durable execution layer for CEO-mode wakes.

It keeps CEO mode from depending only on chat continuity. Each tick records what was inspected, whether action was blocked, and which single bound action ran.

## Commands

```bash
PYTHONPATH=src python3 -m riskflow ceo heartbeat-plan --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo heartbeat-tick --run-id <run_id> --apply
PYTHONPATH=src python3 -m riskflow ceo heartbeat-journal --run-id <run_id>
```

It writes:

- `heartbeat_plan.yaml`
- `heartbeat_plan.md`
- `heartbeat_state.yaml`
- `heartbeat_journal.jsonl`
- `heartbeat_journal.md`

## Guardrail

`heartbeat-tick` does not sleep, daemonize, or run an unbounded loop. It refuses stop requests, true blockers, independent unsafe flight state, pending [[Approval Queue]] items, failed [[CEO Guardrail Audit]], failed [[CEO Preflight Gate]], unresolved [[CEO Memory Delta]] requirements, replay/eval gaps, and elapsed heartbeat-plan time budgets. If the only pre-action blocker is `trace_grade_failed`, plus the flight-dashboard warning derived from that trace, the tick records `pre_action_warnings` and lets `ceo execute-next` either run a bounded trace repair or write a blocked preflight result. If clear, it runs at most one `ceo execute-next` action.

Each tick now records `heartbeat_plan_budget` in `heartbeat_state.yaml` and
`heartbeat_journal.jsonl`, including elapsed hours, max hours, and whether the
time budget has elapsed.

Each tick also records the selected [[CEO Portfolio Allocator]] lane so later
review can see why attention was pointed at approvals, validation, data,
infrastructure, memory, or another operating bottleneck.

Each tick writes or consumes [[CEO Preflight Gate]] output before dispatch, so
replay, eval-suite, approval, guardrail, memory, and budget blockers become
execution constraints rather than advisory notes. Parallel diagnostic wakes can
safely refresh generated artifacts because the shared atomic writer uses unique
temporary files before replacement, avoiding fixed `.tmp` path collisions during
concurrent replay/eval/status commands.

Related:

- [[CEO Heartbeat]]
- [[Approval Queue]]
- [[Executive KPIs]]
- [[CEO Portfolio Allocator]]
- [[CEO Guardrail Audit]]
- [[CEO Preflight Gate]]
- [[Action Contract]]
- [[Loop Outcome Card]]
