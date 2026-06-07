---
rf_type: concept
concept_id: ceo_replay
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use ceo replay to reconstruct CEO runs from ledgers instead of relying on chat continuity.
not_product_proof: true
---

# CEO Replay

CEO replay reconstructs a Riskflow CEO run from append-only ledgers and key
artifact fingerprints.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo replay --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/ceo_replay.yaml`
- `reports/ceo_runs/<run_id>/ceo_replay.md`

## What It Uses

- `ceo_action_ledger.jsonl`
- `heartbeat_journal.jsonl`
- `approval_decision_ledger.jsonl`
- `role_task_ledger.jsonl`
- `repair_apply_ledger.jsonl`
- `operator_step_ledger.jsonl`
- `guardrail_audit.yaml`
- `preflight_gate.yaml`
- `action_contract.yaml`
- `binding_action_result.yaml`
- `trace_grade.yaml`
- `approval_queue.yaml`
- `role_task_queue.yaml`

## Why It Matters

A fresh Codex session should be able to inspect one run id and know what
happened, what was blocked, what was approved, what specialists reviewed, and
whether the next action is safe.

If `ceo_action_ledger.jsonl` is missing, replay may reconstruct a diagnostic
single-action timeline from `binding_action_result.yaml`, but that fallback is a
replay gap. It is not equivalent to append-only replay.

Replay distinguishes current unsafe transitions from legacy policy drift. Known
old no-snapshot transitions can be tagged `legacy_policy_gap` so historical runs
remain understandable, but receipt-backed or policy-versioned current actions
must still follow the previous action's `next_allowed_actions`.

Replay also validates operator-step ledger rows: before/after action-board
snapshot paths must exist and match their recorded SHA-256 hashes, otherwise the
run has an operator-step replay gap.

Replay validates repair-apply ledger rows the same way: before/after
repair-plan snapshot paths must exist under `repair_apply_plans/` and match
their recorded SHA-256 hashes, otherwise the run has a repair-apply replay gap.
Old no-action manual-gate repair-apply rows that predate those snapshots can be
classified as `legacy_snapshot_gap`; replay keeps them visible without treating
them as current unsafe execution.

Related:

- [[CEO Eval Suite]]
- [[Execution Provenance]]
- [[Heartbeat Persistence]]
- [[Action Contract]]
- [[True CEO Autonomy]]
