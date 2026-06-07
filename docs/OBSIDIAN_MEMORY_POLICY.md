# Obsidian Memory Policy

Riskflow uses Obsidian as the curated research memory layer.

## Track In Git

Track curated markdown notes that help future Codex sessions and future humans recover the project thinking:

- `obsidian/Riskflow Home.md`
- `obsidian/wiki/Indicator Observation Library.md`
- `obsidian/wiki/concepts/*.md`
- `obsidian/wiki/cases/*.md`
- `obsidian/wiki/maps/*.md`
- durable decision, hypothesis, experiment, and postmortem markdown when intentionally written

These notes should contain human-reviewed observations, concept definitions, research synthesis, and links between cases and concepts.

## Keep Ignored

Keep generated or heavy artifacts out of Git:

- `reports/`
- `obsidian/reports/`
- raw OHLCV data
- processed data
- screenshots and image exports inside the wiki
- Obsidian app state such as `.obsidian/workspace.json`

## Rule Of Thumb

If a note helps preserve reasoning, track it.

If a file can be regenerated, is large, or is raw market data, ignore it.

## Signal Grammar Notes

The Signal Grammar Lab should use Obsidian for:

- human-reviewed chart cases
- concept pages
- setup-journey hypotheses
- compact evidence summaries
- grammar hubs
- links between cases, concepts, and research questions

Python remains the evidence engine. Obsidian stores the research memory, not the final proof.

## Knowledge Graph Bridge

Use `python3 -m riskflow obsidian-kg` to turn curated notes into a research graph.

Useful commands:

```bash
PYTHONPATH=src python3 -m riskflow obsidian-kg validate
PYTHONPATH=src python3 -m riskflow obsidian-kg audit
PYTHONPATH=src python3 -m riskflow obsidian-kg index
```

`validate` enforces hard graph rules. `audit` writes
`research/knowledge_graph/obsidian_kg_audit.yaml` and `.md` with memory-quality
issues such as orphaned notes, unresolved wikilinks, missing action-changing
concept metadata, and maps without linked concepts. Audit findings are a cleanup
queue, not product evidence.

Allowed durable note types:

- `case`: one chart/date/symbol/timeframe observation
- `concept`: reusable visual or measurable Riskflow idea
- `setup_journey`: staged setup hypothesis such as context -> repair -> trigger -> confirmation -> invalidation
- `evidence_summary`: compact reviewed result pointing back to exact local CSV/YAML/report evidence
- `ceo_session_map`: curated CEO/agentic session memory that records run id, runtime state, source artifacts, next allowed action, reopen conditions, and production effect
- `ceo_run_registry`: compact routing note for which CEO runs are active, stopped, smoke-only, or do-not-resume
- `ceo_business_strategy`: curated business thesis, customer segment, product wedge, forbidden claims, and evidence requirements
- `ceo_board_report`: concise board-style synthesis of progress, falsifications, customer value, risks, asks, and next decision
- `customer_discovery`: curated user-learning note with workflow pain, exact language, alternatives, objections, WTP signal, and changed assumption
- `business_assumption_register`: compact assumption table with status, evidence, next test, and kill condition
- `pricing_packaging`: package hypothesis, value metric, proof required before charging, and billing/productization guardrails
- `gtm_experiment`: lightweight go-to-market experiment hypothesis, audience, ask, success signal, failure signal, and approval requirement

Generated graph tables, compiled queues, and generated grammar grids remain outside the curated vault unless a human or Codex intentionally promotes a concise summary.

If Obsidian memory conflicts with generated CEO artifacts, generated artifacts
win for runtime decisions. The next action is reconcile or report the conflict,
not `ceo execute-next`.

Do not call a setup validated from Obsidian links alone. A bullish setup requires Python evidence, strict referee checks, controls, and promotion gates.

## Lab Director Memory

The lab director writes generated evidence marts, belief graphs, experiment
plans, audits, and reports under `reports/lab_director/`. These are generated
artifacts and should stay out of Git by default.

Promote only concise reviewed summaries into Obsidian. A promoted note should
identify:

- the belief or failed assumption;
- exact source loop/report paths;
- evidence level, contract tier, confidence, and blockers;
- the next required test;
- whether the finding is an entry, permission filter, blocker, invalidation,
  path-management clue, gradient sidecar candidate, or archive.

Obsidian should remember what the lab learned and what not to repeat. It should
not override the Python evidence engine or mark a setup validated from prose
alone.
