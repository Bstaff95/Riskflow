---
rf_type: concept
concept_id: ceo_artifact_coherence
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Run artifact-coherence before trusting a resumption brief for extended CEO autonomy.
not_product_proof: true
---

# CEO Artifact Coherence

CEO Artifact Coherence is the same-cockpit, same-flight check for CEO handoff.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/artifact_coherence.yaml`
- `reports/ceo_runs/<run_id>/artifact_coherence.md`

## What It Checks

- Required trust artifacts exist.
- Artifact `run_id` and `lab_run_id` match the target run.
- Artifact hashes are recorded.
- Trust artifacts were generated after the latest binding action when a binding
  action exists.

## Boundary

This is a freshness and lineage check only. It does not judge market evidence,
validate candidates, authorize product language, or replace [[CEO Preflight
Gate]].

If [[CEO Resumption Brief]] would otherwise say safe but artifact coherence
fails, the brief should downgrade to `diagnostic_stale_artifacts`.

Related:

- [[CEO Resumption Brief]]
- [[CEO Preflight Gate]]
- [[CEO Replay]]
- [[CEO Eval Suite]]
- [[Execution Provenance]]
- [[Agentic Governance For CEO Mode]]
