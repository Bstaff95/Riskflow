---
rf_type: concept
concept_id: archive_do_not_repeat
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Check archived or saturated branches and reopen conditions before spending CEO or lab-loop budget on similar research.
not_product_proof: true
---

# Archive Do Not Repeat

Archive Do Not Repeat is the memory rule for saturated, duplicate, or falsified Riskflow research branches.

## Purpose

The lab should remember not only what worked, but what should stop consuming loop budget.

Good archive memory includes:

- family or hypothesis id
- why it was archived
- source run and report paths
- whether it failed as entry, permission, blocker, invalidation, or product translation
- what would be required to reopen it

## Current Riskflow Need

The stopped `ceo_supervised_chain_20260531_lab` recovery plan contained many `already_seen` skipped items. That is useful evidence: the lab had exhausted repeated recovery paths, but the next-action router did not yet have enough alternate lane support.

The first durable archive map is [[Archive Do Not Repeat - CEO 20260531]].

## Guardrail

Archive does not mean permanently false. It means "do not blindly repeat under the same data, rule shape, and validation contract."

Related:

- [[Governed Research Lane]]
- [[Agent Memory As Research Infrastructure]]
- [[Agentic Research Loop]]
- [[Lab Loop]]
