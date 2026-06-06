---
rf_type: concept
concept_id: ceo_operating_incident_register
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use incident-register to turn safely blocked CEO actions and replay/eval failures into repair memory.
not_product_proof: true
---

# CEO Operating Incident Register

The CEO Operating Incident Register is repair memory for CEO mode.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo incident-register --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/operating_incident_register.yaml`
- `reports/ceo_runs/<run_id>/operating_incident_register.md`

## What It Groups

- Blocked binding actions.
- [[CEO Dispatch Receipt]] blocked states.
- Repeated [[CEO Preflight Gate]] blockers.
- [[CEO Replay]] gaps and illegal transitions.
- [[CEO Eval Suite]] blocking cases.
- [[CEO Artifact Coherence]] failures.
- [[CEO Guardrail Audit]] failures.

Each incident has a stable key, severity, occurrence count, evidence path/hash,
owner command, and closure condition.

## Boundary

This is diagnostic repair memory only. It does not block dispatch by itself,
clear blockers, approve promotions, validate market evidence, authorize product
language, or change production behavior.

Related:

- [[CEO Blocker Stack]]
- [[CEO Dispatch Receipt]]
- [[CEO Replay]]
- [[CEO Eval Suite]]
- [[True CEO Autonomy]]
