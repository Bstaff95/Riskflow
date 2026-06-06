---
rf_type: concept
concept_id: agent_memory_as_research_infrastructure
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Store only curated memory that changes future routing, evidence checks, or no-repeat decisions.
not_product_proof: true
---

# Agent Memory As Research Infrastructure

Agent memory is useful only when it helps the next loop choose better actions than it would from the raw context alone.

In Riskflow, memory has three layers:

- repo docs for durable project direction
- generated reports for raw machine evidence
- Obsidian for curated research synthesis

This note is the ontology and policy note. [[Memory Quality Gate]] is the acceptance checklist for whether a specific note deserves durable graph space.

## Riskflow Policy

Obsidian should remember:

- what was learned
- what failed
- what should not be repeated
- which product role a candidate might serve
- exact source paths for evidence
- the next required test

Obsidian should not decide truth. Python evidence, strict referee checks, controls, fresh data, and promotion gates decide truth.

[[Memory Quality Gate]] defines the standard for which notes deserve durable graph space: they must change a future action, not merely summarize activity.

## Upgrade Direction

The research lab needs memory records that are small enough to survive context resets but exact enough to guide execution.

A good memory record includes:

- run id
- hypothesis id
- variant id when available
- artifact paths
- product role
- evidence tier
- blocker status
- next action
- reason not to repeat stale work

## Failure Modes

- broad summaries without source paths
- generated reports promoted wholesale into the wiki
- memory that preserves excitement but not falsification
- memory that cannot be compiled into new queues or audits

## Future Action Changed

When adding or updating Obsidian memory, include the action it changes. If the note does not change a future action, leave the detail in generated reports instead of promoting it into the curated graph.

Related:

- [[Agentic Research Loop]]
- [[Lab Loop]]
- [[Signal Grammar Lab]]
- [[Agentic Loop Research Map]]
- [[Memory Quality Gate]]
