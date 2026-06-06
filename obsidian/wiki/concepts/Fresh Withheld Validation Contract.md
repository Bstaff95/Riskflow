---
rf_type: concept
concept_id: fresh_withheld_validation_contract
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Freeze fresh or withheld validation rules before building a promotion-eligible executor.
not_product_proof: true
---

# Fresh Withheld Validation Contract

Fresh Withheld Validation Contract is the CEO artifact that freezes what a
promotion-eligible validation run must obey.

It exists after [[Frozen Candidate Validation]] source replay and local adapter
rerun. It does not execute validation. It freezes:

- snapshot rules
- benchmark and symbol locking requirements
- pass/fail thresholds
- required controls
- promotion constraints

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo fresh-withheld-validation-contract --run-id <run_id>
```

It writes:

- `fresh_withheld_validation_contract.yaml`
- `fresh_withheld_validation_contract.md`

The YAML includes artifact fingerprints for the frozen plan, rerun result,
fresh-data preflight, and rerun grid so a future executor can prove it consumed
the same inputs.

The ready next action is `ceo fresh-withheld-validation-executor`.

The executor writes:

- `fresh_withheld_validation_execution_result.yaml`
- `fresh_withheld_validation_execution_result.md`

If the executor is missing snapshot authority, this command writes the manifest
draft:

```bash
PYTHONPATH=src python3 -m riskflow ceo fresh-withheld-snapshot-manifest --run-id <run_id> --apply
```

It writes:

- `fresh_withheld_snapshot_manifest.yaml`
- `fresh_withheld_snapshot_manifest.md`

It blocks unless `fresh_withheld_snapshot_manifest.yaml` proves:

- snapshot type is `fresh` or `withheld`
- no overlap with source evidence
- rule shape is frozen
- active assets exist with pinned CSV hashes
- source-evidence cutoff is declared
- fresh snapshot cutoff or withheld split id is declared
- fresh snapshot cutoff is after the source-evidence cutoff
- active asset latest dates reach the claimed fresh cutoff
- withheld split manifest is ready, matches the declared withheld split id and
  source-evidence cutoff, and is fingerprinted into snapshot authority

For withheld validation, first write the split authority manifest:

```bash
PYTHONPATH=src python3 -m riskflow ceo withheld-split-manifest \
  --run-id <run_id> \
  --apply \
  --withheld-split-id <split_id> \
  --source-evidence-cutoff <date>
```

Use the declaration command instead of hand-editing the manifest:

```bash
PYTHONPATH=src python3 -m riskflow ceo fresh-withheld-snapshot-declare \
  --run-id <run_id> \
  --apply \
  --snapshot-type withheld \
  --withheld-split-id <split_id> \
  --source-evidence-cutoff <date> \
  --confirm-no-overlap
```

With a valid manifest and `frozen_validation_rerun_grid.yaml`, the executor
runs the frozen grammar-search grid and writes shadow-only validation artifacts.
The executor also blocks if contract, manifest, preflight, grid, or active CSV
fingerprints drift. Withheld authority also blocks if the matching
`withheld_split_manifest.yaml` fingerprint is absent or changed. Completed
execution is not a passing validation result unless the frozen contract
thresholds pass. The result remains non-promotional until
[[Promotion Proposal Gate]] and explicit user approval.

Threshold pass/fail is semantic. A matched-null requirement must pass by
explicit status or by p-value under the declared maximum. Directional forward
relative return must clear the declared minimum. Required lag or cooldown
sensitivity controls need explicit pass statuses; lag/cooldown columns alone do
not pass the gate.

## Guardrail

Contract readiness is not validation. It does not change `core_signal_v0`,
rankings, states, scores, alerts, Pine behavior, or TradingView defaults.

Related:

- [[Fresh Data Validation Gate]]
- [[Frozen Candidate Validation]]
- [[Promotion Proposal Gate]]
- [[Approval Queue]]
- [[Process Score Is Not Product Evidence]]
