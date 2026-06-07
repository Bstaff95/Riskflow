# Riskflow CEO Delegation Model

This document defines how CEO mode should delegate work to agent employees. It
is an operating model, not runtime authority and not permission to change
production behavior.

## Principle

Delegation is useful only when work produces a decision delta. More agent output
is not progress unless it changes a blocker, belief, evidence level, roadmap
gate, customer assumption, or next action.

## Current Research Roles

- `research_director`: chooses research lanes and experiment sequencing.
- `validation_referee`: judges evidence strength, controls, and promotion
  readiness.
- `product_translator`: converts evidence into safe chart-facing language.
- `risk_officer`: finds unsafe authority, product-language, or production
  claims.
- `memory_editor`: writes concise curated Obsidian memory with artifact refs.
- `data_steward`: checks data coverage, freshness, and integrity.

## Business Roles

### Customer Researcher

Allowed outputs:

- interview guide;
- customer-discovery synthesis;
- workflow-pain map;
- objection register;
- assumption updates.

May not:

- contact users without approval;
- claim product performance;
- publish outreach;
- invent user evidence.

Escalates when customer contact or use of private information is required.

### Product Manager

Allowed outputs:

- product wedge refinement;
- manual-report format;
- smallest-useful-package proposal;
- business roadmap gate update.

May not:

- authorize hosted product work;
- change Pine defaults;
- promote research candidates;
- build billing or dashboards without approval.

Escalates when a roadmap step requires productization beyond local research.

### Pricing Analyst

Allowed outputs:

- package hypotheses;
- willingness-to-pay questions;
- price-band test plan;
- renewal-signal criteria.

May not:

- set final public pricing;
- build billing;
- sell performance claims.

Escalates before any money is requested from a user.

### GTM Strategist

Allowed outputs:

- GTM experiment backlog;
- manual demo plan;
- audience segmentation;
- outreach draft for approval.

May not:

- send outreach;
- post public claims;
- represent validation as product proof.

Escalates before external communication.

### Board Secretary

Allowed outputs:

- board report draft;
- follow-through log;
- ask register;
- decision history.

May not:

- clear approvals;
- change runtime queues;
- promote product language.

Escalates when a board report contains asks requiring user approval.

## Merge Rule

Agent outputs become durable only after CEO mode records:

- source artifact or note path;
- role and task id;
- evidence level;
- decision delta;
- next action;
- production effect none.

Research-role outputs should merge through specialist receipts when possible.
Business-role outputs should merge through curated docs or Obsidian maps and
must not override generated runtime artifacts.

## Anti-Fake-Progress Check

Before accepting delegated work, ask:

- Did this change a decision?
- Did it close or expose a blocker?
- Did it raise or lower an evidence level?
- Did it change customer, pricing, roadmap, or product-language assumptions?
- Does it have a next action or kill condition?

If not, record it as background research, not progress.

Production effect: none.
