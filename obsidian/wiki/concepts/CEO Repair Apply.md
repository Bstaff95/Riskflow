---
rf_type: concept
concept_id: ceo_repair_apply
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use repair-apply to execute one allowlisted repair-plan item and record before/after closure evidence.
not_product_proof: true
---

# CEO Repair Apply

CEO Repair Apply is the governed executor for one [[CEO Repair Plan]] item.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo repair-apply --run-id <run_id> --repair-key <repair_key> --apply
```

It writes:

- `reports/ceo_runs/<run_id>/repair_apply.yaml`
- `reports/ceo_runs/<run_id>/repair_apply.md`
- `reports/ceo_runs/<run_id>/repair_apply_ledger.jsonl`

## What It Does

It refreshes [[CEO Repair Plan]], finds the exact repair key, runs one
allowlisted internal CEO function when the repair kind is executable, uses bound
CEO action context for runnable repair commands, refreshes the plan again,
writes immutable before/after repair-plan snapshots under
`repair_apply_plans/`, appends the attempt plus snapshot refs/hashes to
`repair_apply_ledger.jsonl`, and records whether the repair closed.
Current or executed repair-apply rows must keep those immutable snapshots
replayable. Old no-action manual-gate refusals that predate snapshot support can
show up in replay as `legacy_snapshot_gap`, which preserves the audit trail
without treating the refused action as unsafe execution.

It can execute:

- allowlisted `diagnostic_refresh` commands such as coherence, replay, eval, or
  guardrail refreshes
- allowlisted generated research-infra repair commands

If the same repair key remains after execution but changes into a manual gate
or implementation-required item, repair-apply records
`repair_reclassified_not_closed`. That means the command ran, but the repair is
still open under a different authority class.

It refuses:

- `manual_gate`
- `implementation_required`
- unsupported command kinds
- arbitrary shell command text from YAML
- production approvals, stop clearing, promotion authority, and product language

## Closure Rule

A repair is closed only when the after-plan clears the repair key, reports no
repairs required, or changes the key's command kind. A diagnostic refresh by
itself is not closure.

[[CEO Replay]] treats missing or changed repair-plan snapshots as replay gaps,
because a future session must be able to verify the exact before/after repair
authority that was used.

## Boundary

This is operating repair execution only. It does not validate market evidence,
promote candidates, change `core_signal_v0`, alter Pine defaults, change
rankings, states, scores, or alerts, or authorize product-facing claims.

Related:

- [[CEO Repair Plan]]
- [[CEO Action Board]]
- [[CEO Operator Step]]
- [[CEO Blocker Stack]]
- [[CEO Operating Incident Register]]
- [[CEO Replay]]
- [[True CEO Autonomy]]
