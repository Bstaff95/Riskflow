---
rf_type: concept
concept_id: specialist_role_orchestration
status: active
updated_at: 2026-06-07
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
- `role_result_validation.yaml`
- `role_task_ledger.jsonl`

`role-dispatch` converts pending queue items into review-only specialist packets.
Each packet includes the exact question, source artifacts, authority boundaries,
and expected `riskflow_ceo_specialist_result_v0` schema.

`role-result` validates the result before appending `role_task_ledger.jsonl`.
Approval/manual-gate tasks use `result_resolution_mode:
manual_gate_blocked_record`, `approval_authority: user_only`, and a
user-confirmed `approval-record` closure command. They also expose a separate
`--status blocked` role-result command with no specialist artifact. They cannot
be completed by a specialist YAML artifact because only the user can approve the
gate.

Completed non-manual specialist tasks must point to a readable
`riskflow_ceo_specialist_result_v0` YAML artifact with:

- matching `task_id`
- matching `role_id`
- `status: complete`
- non-empty `finding`
- non-empty `evidence_refs`
- non-empty `recommended_next_action`
- `product_language_allowed: false`
- `production_effect: none`
- `promotion_authority: none`

Invalid completions write `role_result_validation.yaml` and do not append the
ledger, so they cannot close a task. Blocked tasks can be recorded without an
artifact, but they remain blocked work and do not count as clean role closure.

Rebuilding `role-queue` consumes valid `role_task_ledger.jsonl` entries.
Completed and blocked specialist results are reflected back into
`role_task_queue.yaml` with pending, completed, and blocked counts, so role work
can close the loop instead of remaining a detached note.

Accepted completed results also store the resolved artifact path and SHA-256.
When `role-queue` is rebuilt, it rechecks that artifact. If the artifact is
missing, has no recorded hash, or no longer matches the accepted hash, the task
is changed from complete to blocked with `validation_status:
provenance_drift`. That keeps a stale or edited specialist note from silently
closing CEO work.

The queue also records pending manual count, pending autonomous count,
completed count, blocked count, the top pending task id, top pending role id,
top pending owner command, result resolution mode, whether the task requires a
manual gate, and the closure command. It separately records the top autonomous
pending task, role, packet, and result command so review-only specialist work
can be routed without pretending a manual gate has been cleared. It also
records the top blocked task, role, packet, result mode, validation status,
closure command, review status, accepted result path, finding, and next action
so a fresh session can tell whether the remaining role-readiness gap is missing
evidence, provenance drift, or an accepted blocked specialist finding. Accepted
blocked specialist results remain blocked work; they explain what evidence is
missing instead of authorizing product language. Older queue artifacts without the
closure field are summarized by synthesizing it from task id and result mode.
[[CEO Eval Suite]] treats any
pending or blocked task as not closed, even when no role ledger exists yet. The
queue also includes the expected top packet path plus command templates for
`role-dispatch` and the next `role-result`.

When the only pending role task is manual, `next_action` points to waiting for
user approval or recording the manual gate as blocked instead of saying to
assign another autonomous specialist task.

When no role work remains, `next_action` is
`defer_to_runtime_authority_surface`. That means the role lane has no extra work
to add; it does not authorize dispatch.

Use [[CEO Org Progress Score]] to check whether specialist work changed a
decision or only created activity. Accepted completions without merge receipts,
blocked work, or missing decision deltas are still CEO operating gaps.

`role-dispatch` marks the top pending packet directly with `top_task_id`,
`top_role_id`, `top_packet_path`, `top_result_resolution_mode`,
`top_closure_command`, and `next_role_result_command`, so a fresh session can
work the highest-priority specialist task without scanning every packet first.

Run-generated [[Promotion Proposal Gate]] artifacts now require evidenceful
specialist reviews before they can become `ready_for_user_approval`:
`validation_referee` plus either `product_translator` or `risk_officer`.

For promotion review, a completed role task is not enough by itself. Its
`result_path` must point to a structured YAML review artifact that:

- has an explicit passing/approved review status or decision
- matches the role/task when those fields are present
- keeps `production_effect: none`
- does not set `product_language_allowed: true`

Task-level specialist `status: complete` means the review work was closed, not
that promotion was approved. Missing visual-review evidence should be recorded
as blocked or as a non-approving review, with `product_language_allowed: false`;
it must not unlock product language.

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
- [[CEO Org Progress Score]]
- [[Evidence Debt Register]]
- [[True CEO Autonomy]]
- [[Process Score Is Not Product Evidence]]
