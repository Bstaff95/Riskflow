---
rf_type: concept
concept_id: capability_backlog
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Use capability-backlog to prioritize research-infrastructure gaps before repeating generic CEO loops.
not_product_proof: true
---

# Capability Backlog

The Capability Backlog is the CEO layer's research-infrastructure work queue.

It extracts gaps from:

- `capability_gap.yaml`
- unsupported trace next actions
- visual-review source gaps
- fresh-data manual gates
- frozen-validation executor gaps

## Command

```bash
PYTHONPATH=src python3 -m riskflow ceo capability-backlog --run-id <run_id>
```

It writes:

- `capability_backlog.yaml`
- `capability_backlog.md`

## Riskflow Rule

If the backlog has open items, the CEO should decide whether the top item is higher leverage than another research block.

If the backlog is empty, `next_action` is `defer_to_runtime_authority_surface`.
That means this queue has no infrastructure work; it does not mean CEO mode is
authorized to dispatch. Check [[CEO Action Board]], [[CEO Resumption Brief]], and
[[CEO Preflight Gate]] for runtime authority.

The backlog is research infrastructure only. It does not change production formulas or validate candidates.

Related:

- [[CEO Operating Dashboard]]
- [[True CEO Autonomy]]
- [[Loop Meltdown Detection]]
- [[Research Infra Patch Plan]]
- [[Process Score Is Not Product Evidence]]
