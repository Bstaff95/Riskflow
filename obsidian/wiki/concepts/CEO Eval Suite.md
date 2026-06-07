---
rf_type: concept
concept_id: ceo_eval_suite
status: active
updated_at: 2026-06-07
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
- The latest [[CEO Repair Apply]] receipt is backed by
  `repair_apply_ledger.jsonl` when a repair has been attempted.
- Pending [[Approval Queue]] items block red-authority work.
- Production guardrails still say `production_effect: none`.
- [[CEO Guardrail Audit]] passes without product-language or production-effect
  violations.
- [[CEO Artifact Coherence]] has no hard trust-artifact issues.
- [[Fresh Withheld Validation Contract]] authority is respected.
- [[Specialist Role Orchestration]] results close or block role tasks, with
  pending tasks preventing role-closure readiness and completed tasks requiring
  accepted specialist-result validation plus matching artifact provenance.
- [[Trace Grading For Riskflow]] produces a next action.
- [[Evidence Debt Register]] is visible to fresh sessions.
- [[CEO Mission Score]] covers all eight product-mission dimensions.
- [[CEO Strategy Capital Dashboard]] allocates exactly 100 CEO attention points.

## Hard Versus Advisory

Hard failures can block dispatch through [[CEO Preflight Gate]] when they affect
replay, approval authority, production guardrails, validation authority, or
other execution safety. Dispatch-receipt failures are hard because they mean the
system cannot prove which gate state allowed or blocked the latest action.
The failure evidence includes contract/action artifact paths, timestamps, active
receipt paths, latest-action receipt refs, and receipt hash status so a fresh
session can distinguish stale trust artifacts from missing receipt snapshots.
Dispatch trust-fingerprint checks use the immutable receipt snapshot referenced
by the latest binding action when one exists, not merely the mutable
`dispatch_receipt.yaml` alias. Required receipt fingerprints must be usable:
each required artifact entry must have `exists: true` and a nonempty SHA-256,
not only a present key.
`memory_delta` is fingerprinted when present, but it is not required receipt
coverage because [[CEO Preflight Gate]] enforces hard memory deltas directly.
Approval-apply provenance is also checked: a manual closure must point at a
current approval queue item with a matching recorded fingerprint and source
artifact, not just any old approval ledger row.

Pending, blocked, or provenance-drifted specialist tasks are a readiness failure
even when a role-result ledger exists. That prevents the CEO layer from treating
an untouched queue, a merely recorded manual gate, or an edited-after-acceptance
specialist artifact as cleanly closed.

The role-closure case chooses its next action from the queue state. Manual
pending tasks route to user approval or a manual-gate blocked record; autonomous
pending tasks route to the next specialist result; blocked tasks route to
reviewing blocked evidence or completing missing evidence; stale completed
tasks route to rebuilding and re-hashing the role queue.

Before scoring role closure, eval-suite refreshes [[Specialist Role
Orchestration]] so accepted specialist artifacts are re-hashed and stale
completed queue rows cannot hide provenance drift.
The role-closure case includes the top blocked task, role, accepted blocked
review status, recommended evidence action, and finding in its evidence string,
so the eval result explains why accepted blocked specialist work is still open
without requiring the operator to open the specialist YAML first.

Eval-suite also has a critical `runtime_authority_manual_gates_clear` case. A
live stop request, pending approval, unsafe preflight, manual-gate [[CEO Action
Board]], waiting [[CEO Operator Brief]], or blocked [[CEO Decision Quality]]
runtime authority keeps 9.9 readiness at `not_9_9_ready`, even if stale older
artifacts still look safe.

Guardrail audit and hard artifact-coherence failures are also critical
readiness blockers. A CEO run cannot claim 9.9 readiness if generated artifacts
claim product-language or production authority, or if hard coherence issues mean
the trust layer cannot prove which artifacts are current.

The command refreshes role queue, mission score, guardrail audit, and artifact
coherence before scoring. Missing guardrail/coherence payloads do not default to
green in the pure builder path. Mutable diagnostic fingerprint drift from
trace/replay/eval/guardrail/mission/coherence remains visible, but is advisory
when no immutable action contract or receipt authority is actually broken.

When the latest binding action is legacy and has no dispatch receipt or
transition-policy evidence, eval-suite does not require the current
`action_contract.yaml` or diagnostic dispatch receipt to match that old action.
[[CEO Replay]] and [[CEO Artifact Coherence]] still show the legacy drift, but
only receipt-backed or policy-versioned current actions are hard-blocked for
contract/receipt mismatch.

Advisory failures lower 9.9 readiness without becoming red dispatch blockers by
themselves. A missing [[CEO Strategy Capital Dashboard]] is advisory: run it
before claiming extended CEO readiness, but do not treat its absence as product
authority or a stop request.

## Product Boundary

Passing the eval suite is process readiness. It is not product proof, validation
proof, or permission to mutate `core_signal_v0`, Pine defaults, rankings, scores,
states, or alerts.

Each eval case carries machine-readable authority metadata:

- `action_scope: eval_diagnostic_only`
- `dispatch_authority: not_granted_by_eval_suite`
- `promotion_authority: none`
- `production_effect: none`

That means a passing case can inform [[CEO Preflight Gate]], [[CEO Dispatch
Receipt]], or an operator report, but cannot directly authorize execution,
promotion, product language, or production behavior.

`eval-fixtures` adds deterministic policy regression cases for known CEO
transition rules. These fixtures test the operating harness itself; they do not
use or validate market data.

The main `eval-suite` command now runs these fixtures and includes
`policy_eval_fixtures_pass` in the readiness score.
Normal run ids always execute the fixture suite. Nested fixture-created subruns
can skip recursive fixture execution only through an explicit internal option,
so naming a run like a fixture run does not bypass the regression checks.
Skipped or zero-case fixture results fail `policy_eval_fixtures_pass`; they are
recursion-control artifacts, not 9.9 fixture coverage.

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
