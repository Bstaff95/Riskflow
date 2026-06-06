---
rf_type: concept
concept_id: ceo_guardrail_audit
status: active
updated_at: 2026-06-06
production_effect: none
future_action_changed: Use guardrail-audit to scan CEO artifacts for accidental production-effect or product-language violations.
not_product_proof: true
---

# CEO Guardrail Audit

The CEO guardrail audit scans CEO YAML artifacts for unsafe claims:

- `production_effect` not equal to `none`
- `product_language_allowed: true`

Command:

```bash
PYTHONPATH=src python3 -m riskflow ceo guardrail-audit --run-id <run_id>
```

It writes:

- `reports/ceo_runs/<run_id>/guardrail_audit.yaml`
- `reports/ceo_runs/<run_id>/guardrail_audit.md`

## Boundary

Passing this audit means CEO artifacts preserved basic process guardrails. It
does not prove a signal, validate a candidate, or approve product behavior.

Related:

- [[CEO Preflight Gate]]
- [[Process Score Is Not Product Evidence]]
- [[True CEO Autonomy]]
