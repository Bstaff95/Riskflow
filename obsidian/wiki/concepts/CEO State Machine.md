---
rf_type: concept
concept_id: ceo_state_machine
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use ceo replay and eval-suite to catch illegal transitions between CEO actions.
not_product_proof: true
---

# CEO State Machine

The CEO state machine is the explicit allowed transition layer around
`execute-next` decisions.

Riskflow now checks adjacent action ledger entries by reading the previous
action's `next_allowed_actions` and comparing them with the next recorded
decision.

## Local Artifacts

- `ceo_action_ledger.jsonl`
- `ceo_replay.yaml`
- `ceo_eval_suite.yaml`
- `ceo_eval_fixtures.yaml`
- `action_contract.yaml`
- `binding_action_result.yaml`

## Why It Matters

CEO mode should not jump from a champion/challenger result that asks for
fresh/control validation into another generic research block. The state-machine
check makes that kind of drift visible in replay and scored in the eval suite.

`ceo eval-fixtures` now contains deterministic policy cases for these rules,
including champion/challenger routing and approval-wait routing.

Fresh/withheld contract input repair is also explicit: when
`run_fresh_withheld_validation_contract` returns
`repair_fresh_withheld_contract_inputs`, the legal next decision is
`run_frozen_candidate_validation`, not another contract retry.

Related:

- [[CEO Replay]]
- [[CEO Eval Suite]]
- [[Action Contract]]
- [[Trace Grading For Riskflow]]
- [[True CEO Autonomy]]
