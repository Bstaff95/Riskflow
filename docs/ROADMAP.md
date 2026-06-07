# Riskflow Roadmap

For the adaptable long-term product vision, see `docs/END_STATE.md`. The roadmap should stay grounded in what we can test next; the end-state guide should stay flexible and evidence-driven.

For the business operating thesis, first customer, product wedge, and CEO
business cadence, see `docs/RISKFLOW_AS_BUSINESS.md`,
`docs/CUSTOMER_DISCOVERY.md`, `docs/PRICING_AND_PACKAGING.md`,
`docs/BUSINESS_METRICS.md`, `docs/COMPETITIVE_POSITIONING.md`,
`docs/CEO_STRATEGY_MEMO.md`, `docs/BUSINESS_PRODUCT_ROADMAP.md`,
`docs/CEO_DELEGATION_MODEL.md`, `docs/CEO_OPERATING_CADENCE.md`,
`docs/CEO_WEEKLY_REVIEW_TEMPLATE.md`, and `docs/CEO_BOARD_REPORTING.md`.

## Active Sprint: Signal Grammar Candidate Sprint

The active near-term mission is to convert the human-reviewed oscillator grammar into measurable research sidecars.

Do this before collecting more random winner examples or tuning the core indicator.

The operating model for this sprint is now `docs/LAB_LOOP.md`. The lab should
run from a ranked hypothesis queue, encode exact measurable rules, validate
across `1d`, `12h`, `4h`, and `1h`, and promote candidates only through the
L0 to L5 evidence ladder. The three standing tracks are warning/avoidance,
bullish setup journeys, and entry/invalidation logic. Bullish research should
prioritize staged journeys rather than one-bar trigger tests.

Current implementation note:

- `signal_grammar_sidecar_v0` now adds first-pass research columns and Layer 7 candidate events for pressure acceptance, failed weakness, zone reclaim/retest, curvature intent, divergence warnings, chop quality, and reset warnings.
- These columns are visible in scan outputs and evaluated by `event-study`, but they do not change `core_signal_v0`, state labels, setup scores, opportunity ranking, or TradingView defaults.
- `grammar-search` now expands structured rule-family grids from `research/grammar/rule_search_grid.yaml` across `1d`, `12h`, `4h`, and `1h` so the lab can brute-force candidate grammar variants without hand-registering each idea as a stable sidecar event.
- `lab-loop` now provides the first autonomous runner around the queue and grammar-search engine. It writes ignored runtime state and reports, updates an ignored runtime queue, and generates refinement grids under `research/lab_loop/generated_grids/`. Treat it as research automation only, not production promotion.
- `lab-director` now provides the first native research-intelligence layer above the runner. It builds an evidence mart, belief graph, audited experiment plan, and optional director queue so queue exhaustion or asymmetric evidence turns into a sharper next experiment instead of blind reseeding. Treat it as experiment design only; it must not change production formulas, states, scores, rankings, or TradingView defaults.
- `lab-meta` now scores the research process itself. It diagnoses duplicate research, weak belief movement, weak validation progress, same-sample overfit, product-role ambiguity, queue exhaustion, and Goodhart risk, then recommends one audited intervention such as decompose, validate, broaden, add controls, request fresh data, or stop saturated research.
- `lab-ops` now wraps long autonomous runs with run-scoped state, manifests, journals, checkpoints, process scorecards, status/report commands, stop requests, and explicit terminal reasons. Treat it as an unattended research runner only; it never commits, pushes, or changes production indicator behavior.
- Governed lab-ops now adds blocker audit, research-lane routing, validation governance, recovery queues, and a research map so the lab can tell the difference between a failed bullish setup, a useful warning/blocker, a permission filter, validation debt, and a true global blocker. Treat these as process/governance sidecars; they do not promote product logic by themselves.
- `ceo` now provides the first executive operating layer above governed lab runs. It runs bounded blocks, writes company-status, decision-packet, heartbeat-status, heartbeat-plan/tick/journal, flight-dashboard, operating-dashboard, portfolio-allocator, mission-score, strategy-capital-dashboard, memory-delta, guardrail-audit, preflight-gate, dispatch-receipt, blocker-stack, incident-register, repair-plan, repair-apply, artifact-coherence, resumption-brief, run-index, approval-queue/status/decision-ledger/apply-closure, executive-kpis, role-registry/task-queue/task-ledger, capability-backlog, guarded evidence-debt-register, guarded promotion-proposal, stop-request, action-contract, binding-action, action-outcome, self-audit, trace-grade, replay, eval-suite, eval-fixtures, capability-gap, champion/challenger, champion/challenger visual-review queue, fresh/control-validation, fresh-data-preflight, frozen-candidate-validation, frozen-validation-executor, frozen-validation-rerun, fresh/withheld-validation-contract, withheld-split-manifest, fresh/withheld-snapshot-manifest/declaration, manifest-gated and fingerprint-gated fresh/withheld-validation-executor, research-infra patch, and hypothesis-source broadening artifacts, separates research-infra/understanding/chart-facing deltas, flags fake progress, records evidence provenance and failure avoidance, keeps process scores separate from product evidence, evaluates mission coverage across the eight Riskflow product dimensions, allocates 100 diagnostic CEO attention points across safety/validation/translation/research/memory lanes, writes a one-page fresh-session resumption card before continuation, indexes recent CEO runs before fresh-session selection, fingerprints dispatch trust artifacts before allowed or blocked execution, orders current blockers by authority before acting, groups recurring operating incidents into repair memory, ranks blockers and incidents into a repair backlog with closure conditions, executes exactly one allowlisted repair-plan item with before/after closure evidence, checks artifact freshness/coherence before trusting that card, evaluates fresh/withheld threshold pass/fail before promotion readiness, pins active CSV and split-manifest hashes before fresh/withheld execution, guards direct validation/evidence/authority CLI dispatch through preflight, carries stop-request and true-blocker authority inside the unified gate, uses an in-process CEO dispatch context so imported action-writer calls cannot accidentally mutate validation/evidence/authority artifacts outside bound dispatch, guarded direct preflight, or diagnostic refresh, and keeps product candidates in champion/challenger shadow mode until a promotion proposal is explicitly approved. Overnight CEO mode should be driven by persisted or Codex-thread heartbeats that inspect the latest packet and run one bound action through preflight, not by a blind multi-hour Python loop or by manually falling back to `run-block`.
- The CEO layer should evolve toward governed research capital allocation: candidate portfolio, evidence portfolio, capability backlog, memory delta queue, risk register, and explicit stop/escalation gates. This is the path from operator to acting CEO without granting production-write authority.
- The new CEO eval suite is the first objective 9.9-readiness harness. It scores replayability, state-machine transition legality, action-contract consistency, dispatch-receipt backing/fingerprints, approval gating, production guardrails, guardrail-audit health, hard artifact-coherence health, fresh/withheld validation authority, pending/blocked and validated role-result closure, trace-grade usability, evidence-debt visibility, mission coverage, and strategy-capital attention allocation from artifacts a fresh session can inspect. Hard failures can block dispatch; missing guardrail/coherence payloads cannot default to green; pending or blocked role work prevents 9.9-readiness until closed by valid non-manual specialist records or resolved by the proper manual approval path; advisory strategy-capital gaps lower readiness without becoming red blockers by themselves.
- `ceo org-progress-score` is the first agent-employee progress diagnostic. It scores whether specialist work changed decisions or merely created activity, and flags pending work, blocked work, accepted completions without merge receipts, and completed work without decision deltas. It is diagnostic only and does not merge, approve, validate, or dispatch.
- CEO eval fixtures now provide deterministic policy regression cases for critical transitions, including champion/challenger -> fresh/control validation and approval wait -> approval apply.
- The portfolio allocator and strategy capital dashboard are the first CEO capital-allocation primitives. The allocator ranks operating lanes; the strategy dashboard converts mission coverage, approval/preflight safety, validation authority, candidate translation, evidence debt, role queues, and memory signals into 100 `ceo_attention_points`. These points allocate executive attention only, not trading or production capital.
- `ceo memory-delta` turns memory updates into a governed artifact and optional curated Obsidian handoff note with exact CEO artifact refs.
- Run-generated promotion proposals now require specialist review closure: validation referee plus product translator or risk officer. Completed non-manual specialist tasks now need validated `riskflow_ceo_specialist_result_v0` YAML before `role_task_ledger.jsonl` can close them; approval/manual-gate role tasks are user-only and can only be recorded as blocked, not completed by specialist artifacts.
- `ceo guardrail-audit` and `ceo preflight-gate` are the first unified dispatch safety layer: artifacts now scan for accidental production/product-language violations, and direct `execute-next` plus heartbeat dispatch block on trace, approval, replay, eval, guardrail, memory, and heartbeat-budget blockers. Trace-failure repair decisions can still proceed when the gate's only blocker is the trace failure they are meant to repair.
- The CEO dispatch-context guard is intentionally not a security boundary, but it prevents accidental in-process bypasses: action writers require bound dispatch, guarded direct preflight, or diagnostic/preflight refresh context. Diagnostic refreshes may write summary artifacts, but they do not append `binding_action_result.yaml` or `ceo_action_ledger.jsonl`.
- Initial automated evidence is stronger for warning grammar than for bullish entry grammar. The best current candidate set is v4/v5 failure warning grammar, especially lower-high rollover after baseline, matched-null, symbol-split, event-cluster holdout, entry-lag sensitivity, and cooldown sensitivity testing. The canonical v4 strict CLI run found 25 strict survivors: 10 `1d` lower-high, 10 `12h` lower-high, 4 `4h` lower-high, and 1 `1d` zero-rejection row. `research/grammar/rule_search_grid_v6_4h_lower_high_warning_candidate.yaml` remains the conservative `4h` fresh-data rerun spec, but its self-null pool is too narrow to be proof by itself. The v7 wider-neighborhood pass in `research/grammar/rule_search_grid_v7_4h_lower_high_neighborhood_candidate.yaml` reduced 1,066 time-split-supported rows to 39 strict survivors after unconditional, same-cluster, and matched-null checks, so the durable `4h` thesis is a narrower below-viscosity lower-high island, not every lower-high parameterization. The v8 all-timeframe refined generalization pass did not broaden that specific `4h` shape: only `4h` kept strict survivors after the same referee. The v9 false-positive-filter probe improved `4h` strict survivor quality with pressure-gap and pressure-distance filters, and `research/grammar/rule_search_grid_v10_4h_lower_high_filtered_rerun_candidate.yaml` packages that filtered shape as a tiny fresh-data hypothesis. Current stale-sample strict CLI comparison gives v6 4 strict survivors and v10 9 strict survivors, all `4h`; use that as a reference for the next fresh-data comparison, not as promotion proof. The higher-timeframe branch is now `1d`, not `12h`: v12 found 45 strict survivors all on `1d`, and `research/grammar/rule_search_grid_v13_1d_lower_high_rerun_candidate.yaml` packages the daily shape as an 18-row fresh-data rerun grid with 17 stale-sample strict survivors. V13 is entry-lag and cooldown sensitive: lag 0 failed strict validation while lag 1 and lag 2 survived, and 60-day cooldown removed strict survivors, so treat it as next-bar/follow-through warning grammar with possible cluster dependence. `research/grammar/rule_search_grid_v14_1d_lower_high_viscosity_filter_candidate.yaml` is a sample-derived daily filtered challenger that improves median return and retains some 60-day cooldown support, but narrows breadth. The v11 `1h` zero-rejection neighborhood produced no strict survivors despite all variants being useful/time-split-supported, so keep that family review-only. Keep testing repair/reclaim ideas, but require time-split validation and visual review before treating any bullish variant as useful.

First deliverables:

- `pressure_acceptance`: time and signed area above or below viscosity.
- `zone_reclaim_retest`: reclaim/retest behavior around `-2`, `-1.5`, `0`, `1.5`, and `2`.
- `failed_weakness`: deep negative weakness that stops accelerating lower.
- `curvature_intent`: slope, acceleration, and curl toward confirmation.
- `divergence_quality`: price versus oscillator and gradient divergence candidates.
- `chop_quality`: clean compression versus chaotic volatility.
- `reset_quality`: hot-leader cooldown and constructive rebasing.

Guardrails:

- Add these as research sidecar features/events only.
- Do not change `core_signal_v0`, production states, leaderboard ranking, opportunity scores, or TradingView interpretation by default.
- Evaluate all candidates with Layer 7-style evidence before promotion.

## Stage 1: Meme MVP

Goal:

> Build a working meme-coin relative leadership and compression lab.

Current foundation:

- local package exists
- config-driven meme universe exists
- CSV loader exists
- equal-weight basket exists
- core indicator engine exists
- compression, states, scoring exist
- scan and event-study CLI exist
- resampling CLI exists for deriving 1W/3D from 1D and 12H/4H from 1H
- tests exist
- GitHub repo and Obsidian vault exist

Next priorities:

1. Add real OHLCV data files locally across the meme universe.
2. Use resampling to build the first multi-timeframe local dataset.
3. Run the first real meme leaderboard across enough assets to be meaningful.
4. Review missing/bad data warnings.
5. Tighten Pine-to-Python parity where it matters.
6. Add score component columns to leaderboard.
7. Keep default runs aligned to the TradingView selected basket for now; use ex-target basket diagnostics only in explicit audit runs.
8. Extend benchmark hardening later into subgroup baskets, fallback policies, and basket-as-asset analysis.
9. Add the Layer 3 challenger-signal research path without changing production leaderboard behavior.
10. Improve event-study reporting and add Obsidian event-study markdown.
11. Validate whether compression plus improving relative strength predicts forward relative outperformance.
12. Review Layer 4 setup-quality components and decide when Trader Mode should get a separate ranking.
13. Validate `state_model_v0` with state-level event studies before adding transition probabilities.
14. Use `state-research` to decide whether `state_model_v1_candidate` should be built as an evidence-weighted challenger.
15. Use `score-research` to validate whether `opportunity_score_v0`, `trader_score_v0`, and setup component scores actually rank future relative outperformance.
16. Do not build `opportunity_score_v1_candidate` until score research shows what v0 gets wrong.
17. Harden Layer 7 evidence outputs before adding multi-timeframe logic so future complexity has a reliable referee.
18. Use event-study records and Obsidian reports to decide which L3/L4/L5/L6 candidates deserve promotion notes.
19. Use Layer 8 MTF context as an optional sidecar only, with completed-candle joins and no default ranking changes.
20. Run `mtf-research` to test whether 3D/1W support and 12H/4H reset context improve primary daily outcomes.
21. Use Layer 9 flow-graph tables to represent asset -> subgroup -> sector -> basket relationships without claiming literal fund flows.
22. Run `flow-research` to test whether supportive chain context improves primary asset events before any graph-based ranking promotion.
23. Use Layer 10 `transition-research` to study completed state transitions as observed historical tendencies, not forecasts.
24. Use `visual-review` to turn strong forward relative breakouts into chart galleries, then translate recurring visual patterns into testable event definitions before changing any indicator formula.
25. Research a future `confluence_wave_v0_candidate`: a MACD-like momentum wave around zero that measures acceleration across signal slope, distance from viscosity, relative improvement, compression release, level reclaims, and gradient behavior. Keep it out of production until observation-library cases and Layer 7 evidence show it improves readability and outcomes.
26. Build the Signal Grammar Lab before further core-indicator tuning. The next intelligence layer should emerge from repeated visual observations, grammar primitives, and evidence, not from one pressure-wave prototype.
27. Research a future adaptive default that can eventually hide manual weight presets. Fixed meme/crypto/equity/pure-relative presets remain baselines until an adaptive model beats them across memes, broader crypto, and equities.

Near-term research factory loop:

1. Find historical forward relative breakouts.
2. Review the chart snapshots visually.
3. Name candidate patterns in plain English.
4. Convert only recurring patterns into explicit test events.
5. Use `grammar-search` to sweep structured variants across the meme universe and all active research timeframes.
6. Use Layer 7 evidence before promoting any formula, state, or score change.
7. Use the observation library as the calibration set before tuning z-score lookback, viscosity behavior, gradient sensitivity, weights, or any future confluence wave.
8. Track pressure waves as one candidate family, not the mission. The mission is the broader oscillator grammar: levels, viscosity behavior, structure, divergence, gradient quality, pressure acceptance, and failed weakness.
9. Validate any useful primitive outside the meme sandbox before treating it as product material.

See `docs/VISUAL_INDICATOR_LEARNING_LOOP.md` for the detailed chart-to-evidence workflow.
See `docs/SIGNAL_GRAMMAR_LAB.md` for the grammar-first research plan.

## Stage 2: Crypto Sector Engine

Add sector baskets:

- majors
- memes
- AI coins
- DeFi
- gaming
- RWA
- L1s
- L2s
- SOL ecosystem
- Base ecosystem
- ETH ecosystem

Add nested comparisons:

- sector versus broad crypto
- subgroup versus sector
- coin versus subgroup
- coin versus siblings

## Stage 3: Multi-Timeframe Engine

Use:

- weekly for regime
- 3D for swing structure
- daily for tactical confirmation
- 12H for lower swing confirmation
- 4H for timing and reset
- 1H for intraday structure and source data for 4H/12H resampling

Potential labels:

- early reversal
- confirmed leader
- chop needed
- overheated
- failed reclaim
- compressed gem

Current Layer 8 implementation is intentionally conservative:

- `mtf_context_v0` appends optional context columns only when requested.
- Higher-timeframe joins use completed-candle `available_at` timestamps.
- `mtf-research` compares aligned versus non-aligned primary events.
- No MTF voting score, probability label, alerting layer, or leaderboard promotion exists yet.

## Stage 4: Probabilistic Transitions

After lifecycle states are validated and L10 evidence is strong enough:

- transition matrices
- conditional transitions by parent state
- expansion/chop/failure probabilities

Current Layer 10 implementation is intentionally conservative:

- `transition_research_v0` studies completed state-run transitions.
- Outputs use observed transition rates plus Wilson uncertainty intervals.
- Chain and MTF context are optional conditioning fields.
- No Markov engine, calibrated probability label, TradingView badge, or ranking change exists yet.

Do not promote transition evidence into product probability language before states, chain context, and real data have enough evidence.

## Stage 5: Historical Analog Search

Find prior setups with similar:

- parent sector state
- asset state
- compression
- relative component
- signal slope
- drawdown profile
- forward relative-return outcome

## Stage 6: Dashboard/Product

Only after the local engine is useful:

- capital-flow map
- sector rotation map
- opportunity leaderboard
- alerts
- reports
- visual graph

## Stage 7: Global Markets

Extend the same normalized architecture into:

- stocks
- commodities
- gold and silver
- bonds and rates
- DXY and FX
- semiconductors
- memory stocks
- AI stocks
- energy
- small caps
