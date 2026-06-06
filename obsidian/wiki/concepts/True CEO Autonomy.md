---
rf_type: concept
concept_id: true_ceo_autonomy
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Treat CEO mode as a governed operating system for research capital allocation, evidence gates, memory quality, and product translation.
not_product_proof: true
---

# True CEO Autonomy

True CEO Autonomy for Riskflow does not mean unrestricted command execution. It means the agent can run the research company responsibly while staying inside the user's governance boundary.

The CEO layer should allocate attention, select the next bounded action, inspect evidence, stop bad loops, preserve memory, and escalate product changes for approval.

## Operating Model

The CEO loop should manage five portfolios:

- evidence portfolio: which beliefs have real metric movement
- candidate portfolio: which shadow candidates deserve frozen replay,
  fresh/withheld validation, specialist review, or archive
- infrastructure portfolio: which missing commands block progress
- memory portfolio: which findings change future action
- risk portfolio: which loops, data gaps, or product-language risks require stop or escalation

## Executive Roles

A true Riskflow CEO should behave as:

- orchestrator: choose one bounded next action
- capital allocator: spend research budget on the highest-leverage gap
- referee: separate process scores from product evidence
- product steward: block formula, score, state, alert, and TradingView changes without approval
- memory editor: preserve only action-changing knowledge
- risk officer: stop repeated no-progress patterns and manual gates

## Autonomy Ladder

```text
clerk -> operator -> research manager -> acting CEO -> product steward
```

Current Riskflow is moving from research manager toward acting CEO:

- action contracts constrain each step
- binding action results make the step auditable
- outcome cards and trace grades judge process quality
- loop meltdown detection blocks repeated bad loops
- preflight, replay, eval-suite, memory-delta, approval, specialist-review,
  withheld-authority, fresh-data, and frozen-validation gates protect product
  claims

Acting CEO would require:

- a durable capability backlog with closure checks
- periodic board-style reports
- budget allocation across evidence, infra, memory, and product translation
- stronger visual-review execution
- promotion proposal templates with structured specialist reviews and explicit
  user approval
- data import playbooks that stay outside production changes

## Non-Negotiables

- no production formula changes without approval
- no product language from process scores
- no repeated manual data gates
- no generic lab block when a supported binding action exists
- no Obsidian note without future action changed

## Next Implementation Direction

Build CEO mode toward an operating dashboard:

- current company state
- candidate portfolio
- blocker/risk register
- capability backlog
- memory delta queue
- next bounded action
- stop/escalation reasons

The first implementation is [[CEO Operating Dashboard]], which writes
`ceo_operating_dashboard.yaml` and `.md`.

Related:

- [[CEO Operating Dashboard]]
- [[Capability Backlog]]
- [[Promotion Proposal Gate]]
- [[CEO Heartbeat]]
- [[Action Contract]]
- [[Trace Grading For Riskflow]]
- [[Loop Meltdown Detection]]
- [[Frozen Candidate Validation]]
- [[Agent Memory As Research Infrastructure]]
- [[Process Score Is Not Product Evidence]]
