---
rf_type: concept
concept_id: fresh_data_validation_gate
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Block product language until frozen candidates survive fresh or withheld validation rather than only planning.
not_product_proof: true
---

# Fresh Data Validation Gate

The Fresh Data Validation Gate separates same-sample discovery from evidence that may deserve product translation.

## Promotion Meaning

In Riskflow's current ladder:

```text
L0_registered -> L1_encoded -> L2_discovered -> L3_strict_survivor -> L4_fresh_data_survivor -> L5_indicator_candidate
```

An L3 strict survivor is not enough for production behavior. It should become a frozen candidate that is rerun on fresh or withheld data with the rule shape unchanged.

## Riskflow Use

Fresh validation should preserve:

- exact rule shape
- data fingerprint
- source evidence path
- event definition
- entry lag and cooldown contract
- product role
- no threshold mutation during validation

## Supported Command

The first CEO-level planning command now exists:

```bash
PYTHONPATH=src python3 -m riskflow ceo fresh-control-validation --run-id <run_id> --apply
```

It reads `champion_challenger_results.yaml` and writes:

- `fresh_control_validation_plan.yaml`
- `fresh_control_validation_plan.md`

This command does not validate a candidate by itself. It decides whether the next bounded action is fresh OHLCV import, another metric-source comparison, or governed control validation.

The plan explicitly carries:

- `validation_completed: false`
- `validation_result: not_run`
- `candidate_status_after_plan: shadow_only`
- `product_language_allowed: false`

The second CEO-level command now checks local CSV coverage before trying to
validate:

```bash
PYTHONPATH=src python3 -m riskflow ceo fresh-data-preflight --run-id <run_id>
```

It writes `fresh_data_preflight.yaml` and `.md`. Ready assets include CSV
hashes, row counts, and latest dates. If enough local assets are fresh for the
requested timeframes, the next allowed action becomes
`run_frozen_candidate_validation`. If not, CEO mode should stop at the manual
`import_or_curate_fresh_ohlcv_data` gate.

The third command compiles the frozen handoff packet:

```bash
PYTHONPATH=src python3 -m riskflow ceo frozen-candidate-validation --run-id <run_id>
```

In heartbeat mode, prefer reaching this through `ceo execute-next --apply`.
Direct use is guarded by the enforced CEO preflight gate and must stop on
stop-request, true-blocker, approval, guardrail, replay/eval, or hard
memory-delta blockers.

It writes `frozen_candidate_validation_plan.yaml` and `.md`. This artifact is
still not proof; it is the contract a future validation executor must obey.

After frozen specs, source replay and frozen adapter rerun are lineage checks
only. Product-language evidence requires a fresh/withheld validation contract,
valid snapshot authority, artifact and active-CSV fingerprint checks, semantic
threshold pass, and explicit promotion approval. The guarded chain is:

```text
frozen-validation-executor -> frozen-validation-rerun -> fresh-withheld-validation-contract -> withheld-split-manifest or fresh cutoff -> fresh-withheld-snapshot-declare -> fresh-withheld-validation-executor
```

## Why It Matters

The lab has repeatedly found promising warning/blocker and permission candidates that still need fresh/control validation. Treating those as validated would overstate the evidence.

Related:

- [[Governed Research Lane]]
- [[Frozen Candidate Validation]]
- [[Agentic Research Loop]]
- [[Lab Loop]]
- [[Trace Grading For Riskflow]]
- [[Process Score Is Not Product Evidence]]
