---
rf_type: concept
concept_id: loop_meltdown_detection
status: active
updated_at: 2026-06-05
production_effect: none
future_action_changed: Stop repeated manual gates or repeated no-progress fingerprints before CEO mode burns more research budget.
not_product_proof: true
---

# Loop Meltdown Detection

Loop Meltdown Detection asks whether the CEO loop is repeatedly producing the same decision/action/status pattern without a new evidence path.

It is stricter than ordinary failure avoidance. A single failed action can be useful if it names a gap. A repeated manual gate or repeated no-progress fingerprint means the loop should change strategy or stop.

## Current Fields

`ceo_self_audit.yaml` and `trace_grade.yaml` now include `loop_meltdown`.

The summary tracks:

- current decision/action/status fingerprint
- repeated decision count
- repeated fingerprint count
- recent no-progress count
- manual gate count
- capability-builder count
- whether a strategy change is required
- recommended intervention

## Riskflow Rule

If repeated manual gates appear, stop for manual data import or curation. Do not rerun fresh-data preflight until the CSV state changes.

If repeated capability-builder next actions appear, build the missing capability or stop.

If repeated no-progress fingerprints appear, route to research-infra repair, hypothesis-source broadening, or a stop report.

## Product Boundary

Loop meltdown is process evidence only. It says the autonomy loop is stuck or unsafe to repeat. It does not say anything about whether a trading signal works.

Related:

- [[Trace Grading For Riskflow]]
- [[Failure Avoidance Rate]]
- [[Action Contract]]
- [[Process Score Is Not Product Evidence]]
- [[Archive Do Not Repeat]]
