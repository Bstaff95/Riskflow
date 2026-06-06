---
rf_type: concept
concept_id: specialist_role_orchestration
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use role-queue, role-dispatch, and role-result to route CEO evidence, approval, and capability work to specialist review roles.
not_product_proof: true
---

# Specialist Role Orchestration

Specialist Role Orchestration turns CEO operating debt into role-specific work.

The goal is to make future multi-agent work explicit: validation questions go to a validation referee, data gates go to a data steward, promotion gates go to risk officer/product translator review, and capability gaps go to research director work.

## Commands

```bash
PYTHONPATH=src python3 -m riskflow ceo role-queue --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo role-dispatch --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo role-result --run-id <run_id> --task-id <id> --status complete|blocked
```

It writes:

- `role_registry.yaml`
- `role_task_queue.yaml`
- `role_task_queue.md`
- `role_dispatch.yaml`
- `role_dispatch.md`
- `role_dispatch_packets/<task_id>.md`
- `role_orchestration_status.yaml`
- `role_task_ledger.jsonl`

`role-dispatch` converts pending queue items into review-only specialist packets.
Each packet includes the exact question, source artifacts, authority boundaries,
and expected `riskflow_ceo_specialist_result_v0` schema.

Rebuilding `role-queue` now consumes `role_task_ledger.jsonl`. Completed and
blocked specialist results are reflected back into `role_task_queue.yaml` with
pending, completed, and blocked counts, so role work can close the loop instead
of remaining a detached note.

Run-generated [[Promotion Proposal Gate]] artifacts now require evidenceful
specialist reviews before they can become `ready_for_user_approval`:
`validation_referee` plus either `product_translator` or `risk_officer`.

For promotion review, a completed role task is not enough by itself. Its
`result_path` must point to a structured YAML review artifact that:

- has a passing or approved review decision
- matches the role/task when those fields are present
- keeps `production_effect: none`
- does not set `product_language_allowed: true`

If promotion-proposal code is called without a specialist gate, it blocks by
default instead of assuming review closure.

## Roles

- research_director
- validation_referee
- product_translator
- risk_officer
- memory_editor
- data_steward

The queue coordinates specialist review only. It does not validate statistics, approve promotion, or apply production changes.

Related:

- [[Approval Queue]]
- [[Executive KPIs]]
- [[CEO Eval Suite]]
- [[Evidence Debt Register]]
- [[True CEO Autonomy]]
- [[Process Score Is Not Product Evidence]]
