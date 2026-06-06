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

Related:

- [[CEO Eval Suite]]
- [[Execution Provenance]]
- [[Heartbeat Persistence]]
- [[Action Contract]]
- [[True CEO Autonomy]]
