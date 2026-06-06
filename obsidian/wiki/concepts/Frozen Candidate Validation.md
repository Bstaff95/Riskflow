---
rf_type: concept
concept_id: frozen_candidate_validation
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Convert safe fresh-data preflight plus fresh/control plans into frozen validation specs before any product language.
not_product_proof: true
---

# Frozen Candidate Validation

Frozen Candidate Validation is the handoff between promising shadow evidence and guarded validation execution.

It exists to prevent Riskflow from turning same-sample discoveries into product claims. A candidate can only move toward product language after its rule shape, metrics, controls, and data coverage are frozen before results are inspected.

## Current Implementation

The CEO command is:

```bash
PYTHONPATH=src python3 -m riskflow ceo frozen-candidate-validation --run-id <run_id>
```

In heartbeat mode, prefer reaching this through `ceo execute-next --apply`.
Direct use is guarded by the enforced CEO preflight gate and must stop on
stop-request, true-blocker, approval, guardrail, replay/eval, or hard
memory-delta blockers.

It reads:

- `fresh_control_validation_plan.yaml`
- `fresh_data_preflight.yaml`

It writes:

- `frozen_candidate_validation_plan.yaml`
- `frozen_candidate_validation_plan.md`

The first artifact freezes validation specs. A second command can replay those
frozen specs against existing source artifacts:

```bash
PYTHONPATH=src python3 -m riskflow ceo frozen-validation-executor --run-id <run_id>
```

It writes:

- `frozen_validation_execution_result.yaml`
- `frozen_validation_execution_result.md`
- `frozen_validation_rerun_grid.yaml` when execution adapters are ready

Source replay does not promote candidates, change formulas, or make product
claims. It is not fresh validation.

When `variant_records.csv` contains the selected grammar-search variant, the
frozen spec stores execution-adapter metadata: detector, direction, timeframe,
benchmark, entry lag, cooldown, and params.

When a rerun grid exists, a third command can run the frozen adapter shape
through grammar-search on local data:

```bash
PYTHONPATH=src python3 -m riskflow ceo frozen-validation-rerun --run-id <run_id>
```

It writes:

- `frozen_validation_rerun_result.yaml`
- `frozen_validation_rerun_result.md`
- CSV artifacts under `frozen_validation_rerun/`

Adapter rerun evidence is still not promotional. It verifies that a frozen
adapter can execute against local data and then routes to fresh or withheld
snapshot rules plus predeclared pass/fail thresholds.

The CEO command [[Fresh Withheld Validation Contract]] freezes those snapshot
rules and pass/fail thresholds before a future executor can run promotion-
eligible validation.

After source replay or adapter rerun, the next capability debt is fresh or
withheld validation execution. Do not treat source replay or local adapter
rerun as a passing validation result.

The source-replay result writes a fresh-execution contract naming the next
inputs: fresh or withheld OHLCV snapshot, matching benchmark/basket snapshot,
rerunnable grammar-search adapter, and predeclared pass/fail thresholds.

When adapters are ready, source replay writes `frozen_validation_rerun_grid.yaml`
as a one-family grammar-search grid handoff.

If future fresh or withheld validation results pass, [[Promotion Proposal Gate]]
is the next artifact before any production discussion. It still requires
explicit user approval.

## Spec Contract

Each spec preserves:

- candidate belief id
- champion and challenger names
- product role
- validation route
- eligible timeframes
- ready local symbols by timeframe
- required metrics
- required controls
- source evidence paths
- no post-result threshold tuning
- execution-adapter metadata when source variant records are available

## CEO Meaning

If `ceo fresh-data-preflight` is safe, `ceo execute-next` can route into frozen spec compilation.

If the preflight is not ready, CEO mode should stop at `import_or_curate_fresh_ohlcv_data` rather than repeat preflight or generic research.

Related:

- [[Fresh Data Validation Gate]]
- [[Fresh Withheld Validation Contract]]
- [[Champion Challenger Shadow Mode]]
- [[Action Contract]]
- [[Promotion Proposal Gate]]
- [[Execution Provenance]]
- [[Process Score Is Not Product Evidence]]
