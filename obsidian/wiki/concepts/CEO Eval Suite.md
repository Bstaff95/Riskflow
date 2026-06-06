---
rf_type: concept
concept_id: ceo_eval_suite
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Run ceo eval-suite before trusting extended CEO autonomy or claiming 9.9 readiness.
not_product_proof: true
---

# CEO Eval Suite

The CEO eval suite is the first objective grader for Riskflow CEO mode. It does
not judge whether a market signal is good. It judges whether the CEO operating
loop is safe enough and replayable enough to keep working.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo eval-suite --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo eval-fixtures --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/ceo_eval_suite.yaml`
- `reports/ceo_runs/<run_id>/ceo_eval_suite.md`
- `reports/ceo_runs/<run_id>/ceo_eval_fixtures.yaml`
- `reports/ceo_runs/<run_id>/ceo_eval_fixtures.md`

## What It Grades

- [[CEO Replay]] can reconstruct the action timeline.
- [[CEO State Machine]] transitions are legal.
- The latest [[Action Contract]] matches the latest binding action.
- The latest [[CEO Dispatch Receipt]] backs the binding action with a matching
  path/hash and trust-artifact fingerprint set.
- Pending [[Approval Queue]] items block red-authority work.
- Production guardrails still say `production_effect: none`.
- [[Fresh Withheld Validation Contract]] authority is respected.
- [[Specialist Role Orchestration]] results close or block role tasks.
- [[Trace Grading For Riskflow]] produces a next action.
- [[Evidence Debt Register]] is visible to fresh sessions.
- [[CEO Mission Score]] covers all eight product-mission dimensions.
- [[CEO Strategy Capital Dashboard]] allocates exactly 100 CEO attention points.

## Hard Versus Advisory

Hard failures can block dispatch through [[CEO Preflight Gate]] when they affect
replay, approval authority, production guardrails, validation authority, or
other execution safety. Dispatch-receipt failures are hard because they mean the
system cannot prove which gate state allowed or blocked the latest action.

Advisory failures lower 9.9 readiness without becoming red dispatch blockers by
themselves. A missing [[CEO Strategy Capital Dashboard]] is advisory: run it
before claiming extended CEO readiness, but do not treat its absence as product
authority or a stop request.

## Product Boundary

Passing the eval suite is process readiness. It is not product proof, validation
proof, or permission to mutate `core_signal_v0`, Pine defaults, rankings, scores,
states, or alerts.

`eval-fixtures` adds deterministic policy regression cases for known CEO
transition rules. These fixtures test the operating harness itself; they do not
use or validate market data.

The main `eval-suite` command now runs these fixtures and includes
`policy_eval_fixtures_pass` in the readiness score.

Related:

- [[True CEO Autonomy]]
- [[CEO Replay]]
- [[CEO State Machine]]
- [[Trace Grading For Riskflow]]
- [[Approval Queue]]
- [[Specialist Role Orchestration]]
- [[CEO Mission Score]]
- [[CEO Strategy Capital Dashboard]]
- [[CEO Dispatch Receipt]]
- [[CEO Preflight Gate]]
- [[Process Score Is Not Product Evidence]]
