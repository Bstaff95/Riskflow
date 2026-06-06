---
rf_type: concept
concept_id: ceo_resumption_brief
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Run resumption-brief before resuming a CEO run from a fresh session or noisy handoff.
not_product_proof: true
---

# CEO Resumption Brief

The CEO Resumption Brief is the one-page cockpit handoff for a CEO run.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo resumption-brief --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/resumption_brief.yaml`
- `reports/ceo_runs/<run_id>/resumption_brief.md`

## What It Answers

- Is the run stopped?
- Is [[CEO Preflight Gate]] blocked?
- Are replay, eval-suite, mission score, and strategy capital artifacts present?
- Is the next step diagnostic-only, blocked, or safe for one bound action?
- What exact command should a fresh session run next?

## Boundary

This brief synthesizes trust artifacts. It does not replace preflight, mutate
runtime state, validate market evidence, authorize product language, or approve
production changes.

If the brief says stopped or blocked, the next command must not be
`execute-next --apply`.

Related:

- [[CEO Preflight Gate]]
- [[CEO Replay]]
- [[CEO Eval Suite]]
- [[CEO Mission Score]]
- [[CEO Strategy Capital Dashboard]]
- [[True CEO Autonomy]]
- [[Agentic Governance For CEO Mode]]
