---
rf_type: concept
concept_id: ceo_operating_system_for_riskflow
status: active
updated_at: 2026-06-07
production_effect: none
future_action_changed: Use this as the CEO-mode design target for cadence, delegation, evidence, product strategy, and business-building decisions.
not_product_proof: true
---

# CEO Operating System For Riskflow

Riskflow CEO mode should not mean "run tools forever." It should mean a governed
executive layer that allocates research attention, delegates specialist work,
protects product authority, updates memory, and produces decision-grade handoffs.

This note translates outside CEO, agent, and startup operating patterns into a
Riskflow-specific design target.

## Source Anchors

- OpenAI practical guide to building agents:
  <https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/>
- OpenAI Agents SDK guardrails:
  <https://openai.github.io/openai-agents-python/guardrails/>
- OpenAI Agents SDK human-in-the-loop:
  <https://openai.github.io/openai-agents-python/human_in_the_loop/>
- Anthropic Building Effective Agents:
  <https://www.anthropic.com/engineering/building-effective-agents>
- Anthropic Demystifying Evals For AI Agents:
  <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>
- Amazon two-pizza teams and single-threaded ownership:
  <https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/>
- YC product-market-fit framing:
  <https://www.ycombinator.com/blog/the-real-product-market-fit/>

## External Pattern Translation

Agent guidance says useful agents should own a workflow, choose tools, recover
from errors, halt or hand off when blocked, and operate inside clear guardrails.
For Riskflow, that means CEO mode must always separate:

- diagnostic thinking;
- runtime authority;
- product evidence;
- user approval;
- production behavior.

Anthropic's agent guidance favors simple, composable patterns before complex
frameworks. For Riskflow, that means the next layer should be small commands and
clear artifacts, not a large opaque orchestrator.

Anthropic's eval guidance treats an eval harness as the infrastructure that runs
tasks, records trajectories, grades outputs, and aggregates results. For
Riskflow, [[CEO Eval Suite]], [[CEO Replay]], and [[CEO Dispatch Receipt]] are
the beginning of that harness.

Amazon's single-threaded ownership model maps directly to CEO-mode specialist
roles. Each specialist should own one outcome end-to-end, with clear metrics and
authority limits. [[Specialist Role Orchestration]] is the current harness for
this.

YC's product-market-fit framing says the market problem matters more than the
first solution. For Riskflow, CEO mode should keep asking: who has the painful
problem, what decision Riskflow improves, and what evidence proves the product
is useful.

## CEO Principles

1. Runtime authority beats narrative.
2. One cadence, one bounded action.
3. Research attention is capital.
4. Process health is not product evidence.
5. Specialist delegation needs accountable packets and validated results.
6. Strategy review should inspect portfolios, not only latest outputs.
7. Decision memos must force a next decision.
8. Stop rules are product quality.
9. Shadow candidates stay shadow until promotion is explicitly approved.
10. A fresh session must be able to replay the run without guessing.

## Operating Cadence

Every CEO wake should follow:

```text
inspect -> diagnose -> choose one bounded action -> execute or refuse -> audit -> record -> decide whether to continue
```

Useful cadence artifacts:

- daily brief: current run, top blocker, top opportunity, next command, no-go
  items;
- weekly strategy review: research lanes, evidence debt, validation readiness,
  data gaps, and capability gaps;
- decision memo: selected route, rejected alternatives, evidence, risk, stop
  condition;
- stop audit: why the run stopped and what must change before resuming;
- board report: progress, falsifications, attention allocation, risks, and asks.

## Agent Employee System

Current harness:

- `ceo role-queue`;
- `ceo role-dispatch`;
- `ceo role-result`;
- specialist result schema;
- provenance hashes;
- manual-gate protection;
- promotion-review gating.

Next harness target:

- specialists should pull only tasks they are authorized to handle;
- validation referee and risk officer should be able to challenge product
  translator claims;
- blocked specialist findings should automatically become evidence debt,
  capability backlog, or visual-review queue items;
- stale accepted results should be re-hashed before any readiness claim;
- no specialist can approve user-only gates or production behavior.

## Business Strategy Questions

CEO mode should maintain a business strategy layer for Riskflow:

- Who is the first sharp user?
- What decision does Riskflow make easier?
- What is the wedge: chart insight, scanner, research lab, or TradingView
  companion?
- What evidence would make a user trust it?
- Which product claims are forbidden until validation improves?
- Which workflow creates recurring value instead of one-off novelty?
- Which moat compounds: chart grammar, evidence archive, user workflow,
  relative-basket data, or specialist review memory?

## 9.9 Readiness Bar

Riskflow CEO mode is close to 9.9 when it can:

- identify the highest-leverage next action;
- refuse unsafe or fake progress;
- delegate bounded specialist work;
- run evals that catch live stop/manual-gate contradictions;
- produce concise decision memos a human would trust;
- update [[Agent Memory As Research Infrastructure]];
- preserve product authority;
- leave a fresh session with an exact next command or exact approval ask.

9.9 is not reached while any of these are true:

- stale safe commands exist without runtime override;
- approval gates are ambiguous;
- specialist work is unowned or provenance-drifted;
- product language is authorized from process evidence;
- visual-review evidence is missing for chart-facing claims;
- eval fixtures are skipped or empty;
- a stop/manual gate can coexist with "ready" readiness.

Related:

- [[True CEO Autonomy]]
- [[CEO Agentic Systems Research Alignment]]
- [[Specialist Role Orchestration]]
- [[CEO Eval Suite]]
- [[CEO Action Board]]
- [[CEO Operator Brief]]
- [[CEO Strategy Capital Dashboard]]
- [[Executive KPIs]]
