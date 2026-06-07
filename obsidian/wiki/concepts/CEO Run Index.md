---
rf_type: concept
concept_id: ceo_run_index
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Run run-index when multiple CEO run ids exist or a fresh session needs to choose the safest run to inspect first.
not_product_proof: true
---

# CEO Run Index

The CEO Run Index is the fleet board for CEO runs.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo run-index --limit 25
```

It writes:

- `reports/ceo_runs/run_index.yaml`
- `reports/ceo_runs/run_index.md`

## What It Answers

- Which recent CEO runs exist?
- Which runs are stopped, blocked, diagnostic, actionable, or missing a
  resumption brief?
- What is the safest next command for each run?
- Which runs have mission score and strategy-capital summaries available?
- What did the latest [[CEO Dispatch Receipt]] say about dispatch status,
  safe-to-dispatch, and the reason?
- What does [[Trace Grading For Riskflow]] say about verdict, score,
  recommended next action, issues, and manual data-import requirement?
- What does [[CEO Replay]] say about replay status and issue count?
- What is the latest [[CEO Operator Step]] replay status and ledger count?
- What does [[CEO Eval Suite]] say about score, readiness, and blocking cases?
- What does [[CEO Artifact Coherence]] say about trust-artifact status, issue
  count, top issue, top issue severity, and top issue types?
- What is the top [[CEO Blocker Stack]] blocker and how many [[CEO Operating
  Incident Register]] incidents are open?
- What does the current [[CEO Repair Plan]] say about repair-plan status, top
  repair, top repair kind, and repair next command?
- What is the current [[Approval Queue]] status, top approval id, kind, reason,
  source, authority, fingerprint, and user-confirmed record/apply command path?
- What does [[CEO Decision Quality]] say about selected route, runtime
  authority, executable action, can-execute flag, and blocked-by reason?
- What is the synthesized effective operator status, and is a manual gate active?
- What are the current specialist role pending/completed/blocked counts?
- What is the top blocked specialist role task, review status, result path,
  finding, next action, and closure command when role-readiness is still
  failing?
- What does the latest [[CEO Operator Brief]] say in plain English?
- What is the resumption next command versus the repair next command?
- Did cached safe/actionable state get downgraded because approval, dispatch,
  artifact-coherence, action-board, operator-brief, or decision-quality runtime
  authority disagreed?

## Boundary

This is a diagnostic index only. It does not clear stop requests, grant
approval, mutate action ledgers, execute `execute-next`, validate market
evidence, authorize product language, or approve production changes.

Manual-gate and runtime-blocked surfaces are classification authority. If
dispatch or preflight appears safe but [[CEO Action Board]], [[CEO Operator
Brief]], or [[CEO Decision Quality]] says a manual gate is active, the run index
must classify the run as blocked.

Read `effective_operator_status` and `manual_gate_active` before trusting
`dispatch_safe_to_dispatch`.

Use it before [[CEO Resumption Brief]] when a fresh session has multiple run ids
or when chat context is noisy.

Related:

- [[CEO Resumption Brief]]
- [[CEO Artifact Coherence]]
- [[CEO Repair Plan]]
- [[CEO Operator Brief]]
- [[CEO Preflight Gate]]
- [[Trace Grading For Riskflow]]
- [[CEO Heartbeat]]
- [[True CEO Autonomy]]
