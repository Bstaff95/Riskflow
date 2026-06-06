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
PYTHONPATH=src python3 -m riskflow ceo approval-record --run-id <run_id> --approval-id <id> --decision approved|rejected --user-confirmed
PYTHONPATH=src python3 -m riskflow ceo approval-apply --run-id <run_id> --approval-id <id> --user-confirmed --apply
```

It writes:

- `approval_queue.yaml`
- `approval_queue.md`
- `approval_status.yaml`
- `approval_decision_ledger.jsonl`
- `approval_apply_<id>.yaml`

## Boundary

Approval records are authority records only. They do not apply product changes, clear stop files, resume stopped runtimes, change Pine defaults, change `core_signal_v0`, or change production scores, states, rankings, or alerts.

`approval-apply` is the second explicit closure step. Promotion approval closure
is shadow-only and still does not mutate production. Clear-stop approval can
remove stop files only through this explicit apply command.

Related:

- [[Promotion Proposal Gate]]
- [[Approval Apply]]
- [[True CEO Autonomy]]
- [[CEO Heartbeat]]
- [[Executive KPIs]]
- [[Process Score Is Not Product Evidence]]
