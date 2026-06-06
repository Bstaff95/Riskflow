---
rf_type: concept
concept_id: ceo_memory_delta
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use memory-delta to decide whether a CEO run deserves durable Obsidian handoff memory.
not_product_proof: true
---

# CEO Memory Delta

CEO memory delta is the governed bridge between generated CEO artifacts and
durable Obsidian routing memory.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo memory-delta --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo memory-delta --run-id <run_id> --apply
```

Without `--apply`, it writes:

- `reports/ceo_runs/<run_id>/memory_delta.yaml`
- `reports/ceo_runs/<run_id>/memory_delta.md`

With `--apply`, it writes one curated Obsidian map note when a durable memory
delta is required.

## What It Records

- replay status
- eval-suite status
- selected portfolio lane
- knowledge-graph delta recommendations
- exact CEO artifact refs
- reopen conditions

## Boundary

Memory delta notes are routing memory. They are not runtime authority,
validation proof, product proof, or approval to mutate production behavior.

Related:

- [[CEO Eval Suite]]
- [[CEO Replay]]
- [[CEO Portfolio Allocator]]
- [[CEO State Machine]]
- [[Memory Quality Gate]]
- [[True CEO Autonomy]]
