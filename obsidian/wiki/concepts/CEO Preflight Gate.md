---
rf_type: concept
concept_id: ceo_preflight_gate
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use preflight-gate before direct execute-next or long-running heartbeat dispatch so generated artifacts govern execution.
not_product_proof: true
---

# CEO Preflight Gate

The CEO preflight gate is the unified dispatch gate for direct `ceo
execute-next` and long-running CEO autonomy.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo preflight-gate --run-id <run_id> --enforce-memory-delta
```

It writes:

- `reports/ceo_runs/<run_id>/preflight_gate.yaml`
- `reports/ceo_runs/<run_id>/preflight_gate.md`

## Inputs

- [[Trace Grading For Riskflow]]
- [[Approval Queue]]
- [[CEO Replay]]
- [[CEO Eval Suite]]
- [[CEO Guardrail Audit]]
- [[CEO Memory Delta]]
- [[Heartbeat Persistence]]

## Boundary

The gate decides whether dispatch is safe. It does not validate market evidence,
approve product language, or mutate production behavior. Manual dispatch audits
should use `--enforce-memory-delta`; direct `execute-next` and
`heartbeat-tick` consume the enforced gate before action. Direct guarded
commands such as `run-block`, frozen/fresh-withheld validation commands, and
snapshot authority commands also consume this gate before mutation. Stop
requests and true blockers are gate blockers, not just heartbeat advice. Empty
first-run action history is treated as bootstrap, not a replay failure. A
trace-failure repair decision can proceed only when the trace failure is the
only blocker and the selected action is an explicit repair route. Validation
executors do not bypass a failed trace gate.

Blockers carry category metadata: runtime authority, approval authority, trace
reliability, replay integrity, eval readiness, product guardrail, memory
handoff, or heartbeat budget. Use the category to decide whether the next move
is user approval, artifact repair, memory curation, data/import work, or stop.

Direct CLI validation, evidence, and authority commands are now covered by the
gate, including promotion proposal and evidence-debt staging. In-process action
writers also require a CEO dispatch context: `bound_dispatch`,
`guarded_direct`, `diagnostic_refresh`, or `preflight_refresh`. This prevents
accidental imported Python calls from mutating validation/evidence/authority
artifacts as if they were approved actions. Diagnostic refresh is limited to
summary-style artifacts such as fresh/withheld contract refresh, promotion
proposal staging, and evidence-debt staging; it cannot run heavy mutators such
as run-block, queue repair, broadening, or snapshot authority writers.
Diagnostic refreshes may write summary artifacts, but they do not append
`binding_action_result.yaml` or `ceo_action_ledger.jsonl`. `approval-apply`
inspects the preflight gate and can proceed only when the blockers are the
approval/runtime blockers the recorded approval is meant to resolve.

Related:

- [[True CEO Autonomy]]
- [[CEO Eval Suite]]
- [[CEO Guardrail Audit]]
- [[Heartbeat Persistence]]
