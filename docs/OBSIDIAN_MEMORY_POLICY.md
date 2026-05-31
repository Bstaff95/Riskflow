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

Allowed durable note types:

- `case`: one chart/date/symbol/timeframe observation
- `concept`: reusable visual or measurable Riskflow idea
- `setup_journey`: staged setup hypothesis such as context -> repair -> trigger -> confirmation -> invalidation
- `evidence_summary`: compact reviewed result pointing back to exact local CSV/YAML/report evidence

Generated graph tables, compiled queues, and generated grammar grids remain outside the curated vault unless a human or Codex intentionally promotes a concise summary.

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
