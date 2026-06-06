---
rf_type: concept
concept_id: champion_challenger_shadow_mode
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Compare shadow candidates against base Riskflow with named product-role metrics before any promotion proposal.
not_product_proof: true
---

# Champion Challenger Shadow Mode

Champion Challenger Shadow Mode compares the base Riskflow interpretation against a sidecar candidate without changing production behavior.

## Current Champion

The champion is `core_signal_v0` and the current Pine-style Riskflow oscillator.

## Challenger

A challenger is `core_signal_v0` plus one sidecar candidate, such as a warning blocker, permission filter, invalidation clue, reset-quality feature, or gradient interpretation.

## Required Metrics

- forward relative return versus basket
- hit rate
- MFE/MAE
- max drawdown
- missed upside cost
- avoided downside benefit
- event diversity
- lag sensitivity
- cooldown sensitivity

## Current Implementation State

The latest old CEO run completed shadow comparison, but the next allowed action was fresh/control validation for promising shadow challengers.

On 2026-06-05, a first-class executor was added:

```bash
PYTHONPATH=src python3 -m riskflow ceo fresh-control-validation --run-id <run_id> --apply
```

`ceo execute-next` can also dispatch to this planner after a completed champion/challenger action asks for `run_fresh_or_control_validation_for_promising_shadow_challengers`.

The planner keeps candidates in shadow mode. It writes the next validation route and does not promote production behavior.

Champion/challenger also writes:

- `champion_challenger_visual_review_queue.yaml`
- `champion_challenger_visual_review_queue.md`

That queue records role-specific review questions, metric checklists, and
evidence paths for human or agent chart review. It is a bridge from product
metrics to visual interpretation, not product validation.

After that, `ceo fresh-data-preflight` checks whether local OHLCV coverage is
fresh enough to attempt validation. A safe preflight can route into
`ceo frozen-candidate-validation`, which creates the frozen validation spec
packet while still keeping the challenger in shadow mode.

Related:

- [[Fresh Data Validation Gate]]
- [[Frozen Candidate Validation]]
- [[Trace Grading For Riskflow]]
- [[Agentic Research Loop]]
- [[Lab Loop]]
