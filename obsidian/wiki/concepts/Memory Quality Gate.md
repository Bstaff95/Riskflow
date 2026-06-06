---
rf_type: concept
concept_id: memory_quality_gate
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Reject durable notes that do not name evidence level, source artifact, production effect, and the next action changed.
not_product_proof: true
---

# Memory Quality Gate

The Memory Quality Gate is the standard for deciding whether a Riskflow Obsidian note is useful enough to keep in the durable research graph.

This note is the acceptance checklist. [[Agent Memory As Research Infrastructure]] is the broader ontology and policy note.

## Required Fields In Practice

A durable note should make these clear:

- what changed
- source run or artifact path
- evidence level
- production effect
- future action changed by the note
- condition that would reopen or invalidate the note
- `not_product_proof: true` when the note is process memory, critique, no-repeat routing, or same-sample research

## Why It Matters

Agentic loops can create impressive-looking memory that does not improve the next decision. Riskflow memory should be action-changing, not transcript-shaped.

Good memory examples:

- [[Archive Do Not Repeat - CEO 20260531]] changes whether saturated branches should be repeated.
- [[Fresh Data Validation Gate]] changes whether a candidate can receive product language.
- [[Action Contract]] changes whether a CEO heartbeat can act outside its declared scope.

## Guardrail

Obsidian memory is not statistical proof. It is a routing and synthesis layer over Python evidence, trace artifacts, strict referee checks, and human chart review.

## Audit Command

The memory-quality audit command is:

```bash
PYTHONPATH=src python3 -m riskflow obsidian-kg audit
```

It writes:

- `research/knowledge_graph/obsidian_kg_audit.yaml`
- `research/knowledge_graph/obsidian_kg_audit.md`

The audit report is a cleanup queue. It flags orphaned notes, unresolved links,
concepts without action-changing metadata, and maps without linked concepts. It
does not validate any trading setup.

Related:

- [[Agent Memory As Research Infrastructure]]
- [[Agentic Research Loop]]
- [[Archive Do Not Repeat]]
- [[Trace Grading For Riskflow]]
- [[Action Contract]]
