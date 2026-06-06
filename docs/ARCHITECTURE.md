# Riskflow Architecture

Riskflow is currently a local Python package plus config files, tests, reports, and an Obsidian research vault.

## Repository Layout

```text
configs/              YAML universe and runtime settings
data/raw/             local OHLCV CSV input files, ignored by git
data/processed/       derived data, ignored by git
docs/                 durable project memory and architecture notes
notebooks/            starter research notebooks
obsidian/             research vault and generated markdown reports
research/             structured observations, grammar registries, and research fixtures
reports/              generated CSV/HTML reports, ignored by git
src/riskflow/         Python package
tests/                pytest test suite
tradingview/          canonical Pine indicator reference and experimental Pine variants
AGENTS.md            coding-agent instructions
README.md            user-facing project overview
```

## Main Data Flow

```text
configs/meme_universe.yaml
        |
        v
data_loader.py loads OHLCV CSVs
        |
        v
resample.py optionally derives higher timeframes
        |
        v
baskets.py builds equal-weight return basket
        |
        v
indicator_engine.py calculates relative strength signal
        |
        v
compression.py calculates asset-relative compression
        |
        v
states.py classifies lifecycle state
        |
        v
scoring.py calculates opportunity score
        |
        v
mtf.py optionally appends completed multi-timeframe context
        |
        v
flow_graph.py optionally builds graph nodes/edges/chains
        |
        v
reports.py exports CSV/HTML/Obsidian markdown
        |
        v
visual_review.py optionally renders chart snapshots for human pattern review
```

## Universe Model Direction

The current `configs/meme_universe.yaml` is intentionally simple: each asset has a symbol, name, sector, and subgroup.

The target direction is more flexible. Riskflow should evolve from a rigid tree taxonomy into a tagged, graph-ready universe model.

Important separations:

- Asset identity: the canonical research symbol and what the asset is.
- Data identity: the TradingView/exchange/API symbols used to fetch candles.
- Memberships: structural, tactical, and research groupings.
- Benchmark policy: the preferred comparison basket or parent.
- Quality metadata: label confidence, feed notes, liquidity tier, and data warnings.

This matters because assets often belong to multiple useful groups. For example, BRETT can be a meme, a Base ecosystem asset, a high-beta meme, and a member of the current meme MVP scan. The architecture should support that without forcing one permanent category.

For v1, keep the YAML simple unless the extra metadata is needed by code. When expanding Layer 1, prefer backward-compatible additions over schema churn.

## Benchmark And Tag Direction

Layer 2 is documented in `docs/LAYER_2_BENCHMARKS_AND_TAGS.md`.

The target direction is a configurable benchmark engine with:

- ex-target baskets
- basket viability diagnostics
- benchmark roles and fallback policies
- benchmark confidence
- audit notes explaining why each comparison was chosen
- basket-as-asset support
- controlled primary states and secondary tags

The architecture should keep observations separate from interpretations. Raw features such as signal, relative component, compression score, and active member count should stay distinct from derived labels such as state, tags, confidence, and opportunity score.

Current implementation supports `benchmark.exclude_self` for per-asset ex-target baskets, but the default meme universe keeps `exclude_self: false` to stay aligned with the TradingView selected-basket indicator. The selected benchmark is stored in each analysis frame's numeric `benchmark` column, while audit columns such as `benchmark_used`, `benchmark_target_excluded`, `benchmark_fallback_used`, active/missing member counts, and `benchmark_confidence` explain the comparison.

## Signal Research Direction

Layer 3 is documented in `docs/LAYER_3_SIGNAL_RESEARCH.md`.

The current Pine-style `final_signal` remains the production incumbent and is treated as `core_signal_v0` in research outputs. Challenger signals are tested in a separate research path before any leaderboard or opportunity-score changes.

Signal definitions live in `signal_registry.py`. This registry is the contract layer between research experiments and downstream consumers such as states, scoring, reports, and TradingView-style interpretation. Future indicator formulas should be added as new versioned signals, not silent edits to `core_signal_v0`.

The first challenger families are:

- relative volatility-adjusted momentum
- relative percentile strength
- cross-sectional relative rank

Riskflow should preserve the current oscillator-style user experience while testing whether challenger observations improve forward relative-return evidence.

Visual review is the human-in-the-loop bridge for this layer. The `visual-review` command finds historical strong forward relative breakouts, renders local chart snapshots from the Python engine, and tags visual clues such as negative signal chop, viscosity reclaim, relative component, compression, and state. It is a review surface only; it does not promote formulas or mutate production frames.

The working research method is documented in `docs/VISUAL_INDICATOR_LEARNING_LOOP.md`. This loop treats visual chart examples, missed breakouts, false positives, and setting mismatches as first-class research artifacts.

The observation library is the Karpathy-style LLM wiki layer for this loop. Machine-readable records live under `research/observations/`; Obsidian synthesis pages live under `obsidian/wiki/`. Python remains the evidence engine, while Obsidian stores connected cases, pattern pages, concepts, and human notes.

The Obsidian knowledge-graph bridge (`obsidian_kg.py`) makes that synthesis layer actionable without turning it into a proof engine. It parses curated case, concept, setup-journey, and evidence-summary notes, exports node/edge tables, validates required graph metadata, writes memory-quality audit reports, and compiles bullish setup journeys into lab-loop hypothesis queues plus generated grammar grids. The grammar lab still decides truth through CSV/YAML evidence, strict referee checks, and promotion gates.

The next research layer is the Signal Grammar Lab, documented in `docs/SIGNAL_GRAMMAR_LAB.md`. It keeps the base oscillator frozen while translating human visual reads into grammar primitives such as `pressure_acceptance`, `failed_weakness`, `zone_reclaim_retest`, `oscillator_structure`, `divergence_quality`, and `curvature_intent`. The primitive registry lives in `research/grammar/primitive_registry.yaml`.

The automated grammar-search layer is a research-only hypothesis generator. `grammar_search.py` expands structured rule families from `research/grammar/rule_search_grid.yaml` across selected timeframes, evaluates forward absolute and relative returns with Layer 7 outcome helpers, and exports ranked candidate variants for chart review. It also exports family/timeframe robustness, duplicate outcome clusters, focused chart-review queues, and time-split validation so top-ranked variants can be separated from more durable candidates. Use optional `grammar-search --strict-referee` for stricter baseline/null validation against same-timeframe, same-cluster, and matched random baselines. Follow-up learning-loop reports can add visual galleries and false-positive atlases for survivors. It does not change `core_signal_v0`, production state labels, setup scores, opportunity ranking, or TradingView defaults.

Pressure waves are currently an experimental candidate family inside the grammar lab, not the mission itself. Future user-facing visual layers should be chosen only after reviewed observations and Layer 7 evidence show which grammar primitives actually improve timing, false-positive control, and forward relative-return outcomes.

## Setup Quality Direction

Layer 4 is documented in `docs/LAYER_4_SETUP_QUALITY.md`.

Layer 4 separates leader quality from setup quality. The current implementation keeps stable leaderboard behavior while adding versioned setup-quality columns, setup tags, compression duration, data-quality context, extension risk context, and a non-default `trader_score_v0` for future Trader Mode review.

Setup definitions live in `setup_registry.py`. This prevents silent changes to compression, state, setup-quality, and opportunity-score semantics.

## Lifecycle State Direction

Layer 5 is documented in `docs/LAYER_5_LIFECYCLE_STATES.md`.

The active deterministic state model is `state_model_v0`. The state layer keeps the backward-compatible `state` column while adding state model id, confidence, reason, and tags. Future state logic should be added as side-by-side candidate models rather than silent edits to the production state vocabulary.

State research evaluates whether state labels preserve useful future information. The `state-research` command exports state-level forward relative returns, duration diagnostics, concentration checks, and transition matrices without changing production scan behavior.

## Opportunity Score Direction

Layer 6 is documented in `docs/LAYER_6_OPPORTUNITY_SCORING.md`.

The active leaderboard score remains `opportunity_score_v0`, exposed through the backward-compatible `opportunity_score` column. Layer 6 validates whether high-scored assets actually deserve attention by studying date-wise buckets, top-minus-bottom spreads, rank IC, forward relative returns, drawdowns, and concentration risk.

Score identities live in `score_registry.py`. Future score formulas should be added as versioned candidates, not silent edits to the active leaderboard ranking.

## Evidence Engine Direction

Layer 7 is documented in `docs/LAYER_7_EVIDENCE_ENGINE.md`.

Layer 7 hardens event-study methodology and shared evidence math. It owns forward outcome calculations, event metadata contracts, entry lag, cooldown, concentration diagnostics, classifications, and promotion gates. It does not change signal, setup, state, or score formulas.

## Multi-Timeframe Context Direction

Layer 8 is documented in `docs/LAYER_8_MULTI_TIMEFRAME_CONTEXT.md`.

Layer 8 adds optional `mtf_context_v0` sidecar fields. It uses completed-candle `available_at` timestamps and as-of joins so higher-timeframe context is never visible before the bar closes. MTF context is research and interpretation support only; it does not change default scan schemas, scores, states, or leaderboard ranking unless explicitly requested and later promoted with Layer 7 evidence.

## Capital-Flow Graph Direction

Layer 9 is documented in `docs/LAYER_9_CAPITAL_FLOW_GRAPH.md`.

Layer 9 adds optional `capital_flow_graph_v0` table outputs for nodes, edges, and chains. It treats capital flow as inferred relative leadership context, not literal fund-flow proof. Current subgroup and sector graph nodes are structural placeholders until Layer 2 adds independent subgroup/sector baskets and benchmark confidence.

## Transition Evidence Direction

Layer 10 is documented in `docs/LAYER_10_TRANSITION_EVIDENCE.md`.

Layer 10 adds `transition_research_v0`, a research-only layer for completed lifecycle-state transitions. It reports observed historical transition rates, Wilson uncertainty intervals, forward relative-return outcomes, concentration diagnostics, and optional chain/MTF conditioning. It does not add production Markov logic, probability labels, ranking changes, or TradingView odds.

## Package Modules

- `config.py`: YAML loading into dataclasses.
- `data_loader.py`: local OHLCV CSV discovery, validation, and loading.
- `resample.py`: OHLCV timeframe derivation, such as 1D to 1W/3D and 1H to 12H/4H.
- `baskets.py`: equal-weight return-index construction.
- `features.py`: shared numerical helpers such as rolling z-score, logs, percentiles.
- `indicator_engine.py`: Pine-style normalized component engine, viscosity, gradient driver.
- `compression.py`: ATR%, range%, realized vol, Bollinger-style width, compression score.
- `state_registry.py`: explicit lifecycle state model identity, vocabulary, tags, and output contract.
- `states.py`: deterministic lifecycle state classification plus reasons, confidence, and state tags.
- `state_research.py`: Layer 5 state outcome research, duration diagnostics, and transition matrices.
- `scoring.py`: explainable opportunity score.
- `score_registry.py`: explicit Layer 6 score identities, research targets, roles, and active/candidate contracts.
- `score_research.py`: Layer 6 ranking validation using buckets, rank IC, forward relative returns, drawdown, and concentration diagnostics.
- `event_registry.py`: explicit Layer 7 event identities, metadata, defaults, and event-family contracts.
- `research_outcomes.py`: shared forward returns, relative returns, drawdowns, cooldowns, clustering, and summary helpers.
- `event_study.py`: event detection and forward absolute/relative return summaries.
- `mtf.py`: Layer 8 completed-candle multi-timeframe context joins and deterministic context labels.
- `mtf_research.py`: Layer 8 aligned versus non-aligned MTF evidence reports.
- `flow_graph.py`: Layer 9 table-based capital-flow graph nodes, edges, and chain context.
- `flow_research.py`: Layer 9 supportive-chain versus non-supportive-chain evidence reports.
- `transition_registry.py`: explicit Layer 10 transition research identity and language contract.
- `transition_research.py`: Layer 10 completed state-run transition evidence, observed rates, and conditioned summaries.
- `signal_registry.py`: explicit signal identities, roles, versions, triggers, and downstream-use contracts.
- `signal_grammar.py`: Signal Grammar Lab registry loading, primitive coverage summaries, review-plan exports, and research-only `signal_grammar_sidecar_v0` feature/event columns.
- `grammar_search.py`: research-only structured grammar variant expansion, event detection, forward outcome summaries, and ranking for brute-force hypothesis generation.
- `lab_loop.py`: autonomous research-loop runner that selects queued hypotheses, executes grammar-search grids, writes resumable state, records per-loop reports, updates a runtime queue, and generates refinement children without changing production formulas, scores, states, or TradingView defaults.
- `meta_research.py`: deterministic process-quality layer above the lab director. It scores whether recent research actually learned, diagnoses process failures such as duplicate research or same-sample overfit, recommends one next intervention, audits that intervention, and writes generated reports without changing production formulas, scores, states, rankings, or TradingView defaults.
- `lab_ops.py`: run-scoped autonomous lab operations wrapper. It plans, runs, resumes, stops, and reports long research runs with manifests, journals, checkpoints, budgets, process scorecards, and explicit stop reasons while keeping mutable state under generated runtime paths.
- `blocker_audit.py`, `research_lane_router.py`, `validation_governance.py`, and `research_map.py`: governed research-lab controls above `lab_ops`. They separate failed bullish setups from valid warning/blocker claims, route beliefs into product-relevant research lanes, gate validation/product translation, and maintain a durable map of what the lab knows, what is duplicated, and what remains open. The director can also generate lane-aware recovery queues when governed runs have open lanes but no runnable director queue. These are governance sidecars only and must not change production indicator behavior.
- `ceo_ops.py`: executive layer above governed `lab_ops`. It runs bounded CEO blocks, aggregates company-level status, writes decision packets, decision-quality cards, operator briefs, heartbeat status, heartbeat plans/tick journals, flight dashboards, operating dashboards, portfolio allocator outputs, memory-delta artifacts, guardrail audits, unified preflight gates, dispatch receipts with immutable snapshots, blocker stacks, operating incident registers, repair plans, action boards, operator steps, artifact-coherence checks, resumption briefs, run indexes, approval queues/status/decision/apply ledgers, executive KPIs, role registries/task queues/dispatch packets/ledgers, capability backlogs, evidence-debt registers, guarded promotion proposals, stop requests, action contracts, binding action results, action outcome cards, append-only action ledgers, self-audits, trace grades, replay reports, eval-suite reports, eval-fixture reports, capability gaps, champion/challenger shadow artifacts, champion/challenger visual-review queues, fresh/control validation plans, fresh-data preflights, frozen-candidate validation specs, frozen-validation source-replay results, frozen adapter rerun results, fresh/withheld validation contracts, fresh/withheld snapshot manifests, manifest-gated and fingerprint-gated fresh/withheld validation execution results, research-infra patch plans, and hypothesis-source broadening plans. Outcome cards, trace grades, replay reports, eval suites, eval fixtures, portfolio allocator outputs, decision-quality cards, operator briefs, memory deltas, guardrail audits, preflight gates, dispatch receipts, blocker stacks, incident registers, repair plans, action boards, operator steps, artifact-coherence checks, resumption briefs, run indexes, and role dispatch packets include evidence-provenance, failure-avoidance, loop-meltdown detection, state-transition checks, approval closure, role-result closure, validation-authority gates, lane value-of-information scoring, durable-memory routing, safety-blocker aggregation, operator next-action routing, alternatives/rejection reasons, specialist result schemas, human-readable refused actions, and process-only product-evidence fields so future wakes can tell whether the loop avoided prior no-progress patterns without mistaking process quality for product proof. `ceo execute-next` binds the latest executive decision to the matching action so product-delta decisions cannot silently become another generic research block or repeat a not-ready data gate, and it now consumes the unified preflight gate before bound dispatch. `ceo operator-step --apply` wraps the action board in one audited transaction and only invokes internal bounded dispatch when the board says it is safe. `heartbeat-tick` also consumes that gate before invoking `execute-next`.
- `signal_research.py`: experimental Layer 3 challenger signals and variant event studies.
- `setup_registry.py`: explicit Layer 4 compression/state/setup/opportunity contracts.
- `setup_quality.py`: setup component scores, setup tags, and versioned opportunity output.
- `visual_review.py`: local chart-snapshot generation for visual breakout archeology.
- `observation_library.py`: structured observation records and Obsidian wiki export for indicator-learning cases.
- `obsidian_kg.py`: Obsidian research-graph parser, validator, memory-quality auditor, index exporter, setup-journey queue compiler, and compact evidence-summary exporter.
- `reports.py`: CSV, HTML, and Obsidian markdown export helpers.
- `cli.py`: command-line entry points.

## CLI Commands

```bash
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow event-study --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow signal-research --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow visual-review --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow grammar-lab
PYTHONPATH=src python3 -m riskflow obsidian-kg validate
PYTHONPATH=src python3 -m riskflow obsidian-kg audit
PYTHONPATH=src python3 -m riskflow obsidian-kg compile-queue --direction bullish
python3 -m riskflow grammar-search --config configs/meme_universe.yaml --timeframes 1d 12h 4h 1h
PYTHONPATH=src python3 -m riskflow lab-loop run --max-loops 100 --max-hours 4 --strict-referee --resume
PYTHONPATH=src python3 -m riskflow lab-meta plan --objective bullish-positive
PYTHONPATH=src python3 -m riskflow lab-ops plan --objective bullish-positive --max-epochs 200 --epoch-size 5
PYTHONPATH=src python3 -m riskflow lab-ops run --objective bullish-positive --governed --apply
PYTHONPATH=src python3 -m riskflow ceo execute-next --run-id <run_id> --objective bullish-positive --apply
PYTHONPATH=src python3 -m riskflow ceo champion-challenger --run-id <run_id> --apply
PYTHONPATH=src python3 -m riskflow ceo fresh-control-validation --run-id <run_id> --apply
PYTHONPATH=src python3 -m riskflow ceo fresh-data-preflight --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo frozen-candidate-validation --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo frozen-validation-executor --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo frozen-validation-rerun --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo fresh-withheld-validation-contract --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo withheld-split-manifest --run-id <run_id> --apply --withheld-split-id <id> --source-evidence-cutoff <date>
PYTHONPATH=src python3 -m riskflow ceo fresh-withheld-snapshot-manifest --run-id <run_id> --apply
PYTHONPATH=src python3 -m riskflow ceo fresh-withheld-snapshot-declare --run-id <run_id> --apply --snapshot-type withheld --withheld-split-id <id> --source-evidence-cutoff <date> --confirm-no-overlap
PYTHONPATH=src python3 -m riskflow ceo fresh-withheld-validation-executor --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo operating-dashboard --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo capability-backlog --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo promotion-proposal --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo evidence-debt-register --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo patch-research-infra --run-id <run_id> --apply
PYTHONPATH=src python3 -m riskflow ceo broaden-hypothesis-source --run-id <run_id> --apply
PYTHONPATH=src python3 -m riskflow ceo trace-grade --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo heartbeat-status --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo replay --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo eval-suite --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo eval-fixtures --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo portfolio-allocator --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo mission-score --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo strategy-capital-dashboard --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo memory-delta --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo guardrail-audit --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo preflight-gate --run-id <run_id> --enforce-memory-delta
PYTHONPATH=src python3 -m riskflow ceo dispatch-receipt --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo blocker-stack --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo incident-register --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo repair-plan --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo artifact-coherence --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo resumption-brief --run-id <run_id>
PYTHONPATH=src python3 -m riskflow ceo run-index --limit 25
PYTHONPATH=src python3 -m riskflow ceo stop --run-id <run_id> --reason user_requested
python3 -m riskflow setup-research --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow state-research --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow score-research --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow mtf-research --config configs/meme_universe.yaml --primary-timeframe 1d --context-timeframes 1w 3d 12h 4h
python3 -m riskflow flow-graph --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow flow-research --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow transition-research --config configs/meme_universe.yaml --timeframe 1d
python3 -m riskflow resample --config configs/meme_universe.yaml --preset research-mtf
```

CEO heartbeat/autonomy default: use `ceo execute-next --apply` or
`ceo heartbeat-tick --apply`. The direct validation/evidence/authority commands
above are guarded by `ceo preflight-gate --enforce-memory-delta`; snapshot
authority commands require `--apply` and remain non-promotional.

Optional scan MTF sidecar:

```bash
python3 -m riskflow scan --config configs/meme_universe.yaml --timeframe 1d --mtf-preset research-mtf
```

## Generated Files

Generated outputs are intentionally ignored by git:

- `data/raw/*`
- `data/processed/*`
- `reports/*`
- `obsidian/reports/*`

Only `.gitkeep` placeholders should be committed in those directories.

## Current Gaps To Remember

- The Python engine is aligned with the Pine reference for the current grammar-lab measurement path: close price source, selected equal-weight meme basket, weight-scaled fusion, 200-bar component lookback, risk-off setting, viscosity parameters, and gradient normalization style. It is still not full one-to-one TradingView parity because Pine risk-auto mode, alternate display settings, TradingView feed behavior, `request.security()` calls, rendering, and overlay candle coloring are outside the Python engine. The latest audit lives at `reports/grammar_search/learning_loop/pine_python_formula_parity_audit.md`.
- Subgroup/sector baskets are still structural placeholders; only the main meme basket and per-asset ex-target variants are implemented.
- Event-study markdown export is not yet as complete as scan markdown reporting.
- Real market data is not included in the repo.
