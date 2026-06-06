---
rf_type: concept
concept_id: agentic_governance_for_ceo_mode
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use external agent-governance research to keep CEO mode focused on runtime authority, auditability, value of information, and meaningful human approval.
not_product_proof: true
---

# Agentic Governance For CEO Mode

External research on agentic systems points toward the same design principle
Riskflow CEO mode is adopting: autonomy is only useful when execution authority
is explicit, auditable, bounded, and separable from the model's reasoning.

## Research Inputs

- Stanford Digital Economy Lab, "Authentication for AI Agents": authenticated,
  authorized, auditable delegation lets humans grant scoped authority while
  preserving accountability.
  Source: https://digitaleconomy.stanford.edu/project/loyal-agents/authentication-for-ai-agents-privacy-and-security/
- Edward Meyman, "Execution-Time Authorization for AI Agents": agent systems
  need deterministic governance boundaries between capability and authorization,
  especially before side effects.
  Source: https://papers.ssrn.com/sol3/Delivery.cfm/6300558.pdf?abstractid=6300558
- NIST, "Value of Information and Decision Pathways": information should be
  valued by how much it can improve downstream decisions, not by how much data
  it creates.
  Source: https://www.nist.gov/publications/value-information-and-decision-pathways-concepts-and-case-studies
- Mökander and Floridi, "Operationalising AI governance through ethics-based
  auditing": governance metrics are useful when they support deliberation,
  design choices, and visible embedded values, not when they pretend to certify
  ethics absolutely.
  Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC9152664/

## Translation To Riskflow

Riskflow CEO mode should keep four layers separate:

- intent: the CEO decision packet and selected action
- authority: preflight, approval queue, action contract, dispatch context
- execution: one bounded command or diagnostic artifact
- audit: replay, eval suite, guardrail audit, memory delta, final report

This matches [[Action Contract]], [[CEO Preflight Gate]], [[Approval Queue]],
[[CEO Replay]], [[CEO Eval Suite]], and [[CEO Strategy Capital Dashboard]].

## CEO Operating Rule

The model may propose strategy, but the repo must enforce authority.

That means:

- diagnostic artifacts can summarize and allocate attention
- bound dispatch or guarded direct preflight is required before action writers
- production formulas, Pine/defaults, states, scores, rankings, and alerts remain
  outside autonomous authority
- approval and stop requests are runtime authority, not prose suggestions
- value-of-information should favor tests that can change the next decision

## Current Design Implication

The strategy-capital dashboard should not act like an investment allocator. It
allocates CEO attention to the highest-value uncertainty while preserving
approval gates. A missing dashboard is an advisory 9.9-readiness gap, not a hard
dispatch blocker.

Related:

- [[True CEO Autonomy]]
- [[CEO Strategy Capital Dashboard]]
- [[CEO Mission Score]]
- [[CEO Preflight Gate]]
- [[Approval Queue]]
- [[CEO Eval Suite]]
- [[Process Score Is Not Product Evidence]]
