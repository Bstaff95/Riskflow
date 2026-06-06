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
- What is the top [[CEO Blocker Stack]] blocker and how many [[CEO Operating
  Incident Register]] incidents are open?
- What does the current [[CEO Repair Plan]] say about repair-plan status, top
  repair, top repair kind, and repair next command?
- What does the latest [[CEO Operator Brief]] say in plain English?
- What is the resumption next command versus the repair next command?

## Boundary

This is a diagnostic index only. It does not clear stop requests, grant
approval, mutate action ledgers, execute `execute-next`, validate market
evidence, authorize product language, or approve production changes.

Use it before [[CEO Resumption Brief]] when a fresh session has multiple run ids
or when chat context is noisy.

Related:

- [[CEO Resumption Brief]]
- [[CEO Artifact Coherence]]
- [[CEO Repair Plan]]
- [[CEO Operator Brief]]
- [[CEO Preflight Gate]]
- [[CEO Heartbeat]]
- [[True CEO Autonomy]]
