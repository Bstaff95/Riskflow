---
rf_type: concept
concept_id: ceo_dispatch_receipt
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use dispatch-receipt to prove which trust artifact versions allowed or blocked one CEO execute-next dispatch.
not_product_proof: true
---

# CEO Dispatch Receipt

The CEO Dispatch Receipt is the audit trail between trust gates and one CEO
action.

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo dispatch-receipt --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/dispatch_receipt.yaml`
- `reports/ceo_runs/<run_id>/dispatch_receipt.md`
- `reports/ceo_runs/<run_id>/dispatch_receipts/<receipt_id>.yaml`

## What It Answers

- Which decision was being dispatched?
- Was one bound dispatch safe or blocked?
- Which [[CEO Preflight Gate]] blockers existed?
- How many red-authority approvals were pending?
- What were the SHA fingerprints of the trusted artifacts at dispatch time?

During `ceo execute-next --apply`, the receipt is generated immediately before
the allowed or blocked binding result. `dispatch_receipt.yaml` remains the
latest dashboard alias, but receipt-backed binding action results record the
immutable `dispatch_receipts/<receipt_id>.yaml` snapshot path and hash.
[[CEO Replay]] and [[CEO Eval Suite]] can then audit each historical dispatch
even after the latest alias changes.

## Boundary

The direct command is diagnostic-only. It does not append
`ceo_action_ledger.jsonl`, overwrite `action_contract.yaml`, clear stop
requests, approve promotions, validate market evidence, authorize product
language, or change production behavior.

Related:

- [[CEO Preflight Gate]]
- [[CEO Artifact Coherence]]
- [[CEO Resumption Brief]]
- [[Execution Provenance]]
- [[True CEO Autonomy]]
