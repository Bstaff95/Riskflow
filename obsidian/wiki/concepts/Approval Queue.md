---
rf_type: concept
concept_id: approval_queue
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use approval-queue, approval-record, and approval-apply to separate red-authority user decisions from autonomous CEO execution.
not_product_proof: true
---

# Approval Queue

The Approval Queue is the CEO-mode holding pen for decisions Codex must not make by itself.

## Commands

```bash
PYTHONPATH=src python3 -m riskflow ceo approval-queue --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo approval-record --run-id <run_id> --approval-id <id> --decision <approved|rejected> --user-confirmed
PYTHONPATH=src python3 -m riskflow ceo approval-apply --run-id <run_id> --approval-id <id> --user-confirmed --apply
```

It writes:

- `approval_queue.yaml`
- `approval_queue.md`
- `approval_status.yaml`
- `approval_decision_ledger.jsonl`
- `approval_apply_<id>.yaml`

## Boundary

`approval_queue.yaml` and `approval_status.yaml` include the top pending
approval id plus exact `approval-record` and `approval-apply` command templates,
so a fresh session can show the user the two explicit steps without inventing an
approval decision.
`approval_queue.md` expands each item into a review card with reason, source,
required user decision, item fingerprint, approval authority, forbidden auto
actions, record/apply commands, and closure steps. Use the markdown card before
asking the user to decide.

Approval records are authority records only. They do not apply product changes, clear stop files, resume stopped runtimes, change Pine defaults, change `core_signal_v0`, or change production scores, states, rankings, or alerts.
`approval-record` only accepts an approval id that is currently pending in the
queue, and it stores the approval kind, source artifact, and approval-item
fingerprint in the decision ledger.

`approval-apply` is the second explicit closure step. Promotion approval closure
is shadow-only and still does not mutate production. Clear-stop approval can
remove stop files only through this explicit apply command.
Before acting, it rebuilds the approval queue and requires the recorded
fingerprint to match the current approval item, so stale approval records cannot
clear a newer stop request.

Related:

- [[Promotion Proposal Gate]]
- [[Approval Apply]]
- [[True CEO Autonomy]]
- [[CEO Heartbeat]]
- [[Executive KPIs]]
- [[Process Score Is Not Product Evidence]]
