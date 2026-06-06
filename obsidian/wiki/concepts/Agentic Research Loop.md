---
rf_type: concept
concept_id: agentic_research_loop
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Use bounded inspect-act-audit-memory loops instead of open-ended command repetition.
not_product_proof: true
---

# Agentic Research Loop

An agentic research loop is a bounded cycle where an agent observes state, chooses a next action, executes through tools, audits the result, records durable memory, and decides whether to continue.

For Riskflow, the useful loop is not "keep running commands." It is:

```text
inspect -> diagnose -> execute one bounded action -> audit -> record -> choose next action
```

## Riskflow Role

This concept extends [[Lab Loop]] and [[Signal Grammar Lab]] from indicator research into research-system research.

[[CEO Heartbeat]] is the concrete Riskflow implementation of this broader loop pattern.

The loop should improve at least one of:

- research infrastructure
- evidence quality
- hypothesis quality
- blocker and warning separation
- product translation
- Obsidian memory
- next-decision quality

## Strong Pattern

The best agentic systems separate:

- planner or orchestrator
- executor
- critic or referee
- memory writer
- citation or evidence linker

Riskflow already has pieces of this through CEO mode, lab-ops, lab-meta, blocker audit, lane routing, validation governance, and Obsidian. CEO actions now write [[Action Contract]] artifacts before acting and [[Loop Outcome Card]] artifacts after acting, so future sessions can inspect both intent and result before continuing.

## Failure Modes

- activity without belief movement
- repeated queue generation without new evidence
- same-sample tuning mislabeled as validation
- self-critique from the same weak perspective
- Obsidian prose treated as proof
- stopping because one lane is exhausted while other lanes remain open

## Research Questions

- Can each CEO heartbeat be graded like an agent trace?
- Can every stop reason map to one supported next action?
- Can Obsidian memory preserve why a branch should not be repeated?
- Can subagents improve critique without duplicating the main agent's work?

## Future Action Changed

Before starting another long autonomous run, require a bounded action route, a trace-gradeable outcome, and an Obsidian memory target. If any of those are missing, build the missing route instead of continuing the loop.

Related:

- [[Lab Loop]]
- [[CEO Heartbeat]]
- [[Agentic Loop Research Map]]
- [[Trace Grading For Riskflow]]
- [[Action Contract]]
- [[Agent Memory As Research Infrastructure]]
