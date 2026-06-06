---
rf_type: concept
concept_id: governed_research_lane
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Route weak, failed, or stalled findings into product-relevant lanes instead of treating them as global blockers.
not_product_proof: true
---

# Governed Research Lane

A governed research lane is a product-relevant bucket for Riskflow lab evidence.

The lane tells the lab what kind of value a belief may have:

- bullish permission
- warning blocker
- invalidation
- reset quality
- gradient interpretation
- path management
- cross-asset regime
- archive or do-not-repeat

## Why It Matters

Weak bullish evidence is not automatically useless. It may become a warning, blocker, invalidation clue, or archive rule.

Lane routing prevents the lab from treating every failed long-entry idea as a global blocker.

## Current Implementation State

The 2026-06-01 stopped run showed that some open lanes did not have supported recovery specs. In particular, `cross_asset_regime` was open but unsupported by recovery generation.

On 2026-06-05, first-pass recovery specs were added for:

- `cross_asset_regime`
- `path_management`
- `invalidation`
- `gradient_interpretation`

This is still a research-infrastructure patch, not a production finding. The next proof is a governed recovery run on a fresh run id that shows the old `governed_recovery_no_supported_specs` stall can route into valid queued tests.

## 2026-06-05 Dry-Run Evidence

Without applying to the stopped runtime, this command:

```bash
PYTHONPATH=src python3 -m riskflow lane-router recover --run-id ceo_supervised_chain_20260531_lab --max-new-hypotheses 20
```

generated:

- recovery items: `2`
- blocked lanes: `0`
- audit passed: `true`
- output plan: `reports/lab_ops/ceo_supervised_chain_20260531_lab/governance/manual/recovery_queue_plan.yaml`

The generated items were both `cross_asset_regime` tests:

- `regime_context_sensitivity`
- `regime_timeframe_transfer`

This supports the infrastructure fix, but the old stopped runtime should not be resumed or mutated without user approval.

Related:

- [[Lab Loop]]
- [[Agentic Research Loop]]
- [[Archive Do Not Repeat]]
- [[Fresh Data Validation Gate]]
