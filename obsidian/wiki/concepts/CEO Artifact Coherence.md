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
- The action contract decision matches the latest binding action decision.
- The latest binding action points at an immutable `dispatch_receipts/` snapshot
  whose stored hash still matches the receipt file.
- Authority trust artifacts that existed when the receipt snapshot was written
  still match the receipt's recorded SHA-256 fingerprints.
- Mutable diagnostics such as trace grade, replay, eval suite, guardrail audit,
  and approval queue/status can refresh during later preflights; drift there is
  visible evidence but not hard-blocking by itself.
- Handoff diagnostics such as [[CEO Repair Apply]], [[CEO Action Board]],
  [[CEO Decision Quality]], and [[CEO Operator Brief]] are tracked for
  freshness. Missing or stale versions are advisory because they can mislead a
  fresh session, but they are not direct dispatch authority by themselves.
- Handoff semantics agree across [[CEO Action Board]], [[CEO Decision Quality]],
  and [[CEO Operator Brief]]. For example, if the board says manual gate, the
  decision-quality effective runtime action must also be blocked and the
  operator brief must say it is waiting on the manual gate. The board primary
  action also must not remain marked executable under manual-gate status.
  Semantic mismatches are advisory, but they are high-signal handoff problems.
- A live `stop.request` plus stale safe handoff artifacts is a handoff semantic
  issue. If the board, decision-quality, or operator brief still says bounded
  action while a stop file exists, artifact coherence records
  `live_stop_runtime_authority_mismatch` as advisory evidence.
- Legacy actions that were recorded before receipt snapshots or transition
  policy evidence remain visible as advisory issues when the latest action has
  no current transition evidence. They should not be treated like hard
  receipt-backed authority drift.

## Boundary

This is a freshness, lineage, and trust-alignment check only. It does not judge
market evidence, validate candidates, or authorize product language. Hard
artifact-coherence failures are consumed by [[CEO Preflight Gate]] as dispatch
blockers.

Status values:

- `pass`: no coherence issues.
- `pass_with_advisory_issues`: visible legacy or non-hard drift exists, but
  `hard_issue_count` is zero.
- `fail`: at least one hard trust issue exists.

If [[CEO Resumption Brief]] would otherwise say safe but artifact coherence has
hard issues, the brief should downgrade to `diagnostic_stale_artifacts`.

Related:

- [[CEO Resumption Brief]]
- [[CEO Preflight Gate]]
- [[CEO Replay]]
- [[CEO Eval Suite]]
- [[Execution Provenance]]
- [[Agentic Governance For CEO Mode]]
