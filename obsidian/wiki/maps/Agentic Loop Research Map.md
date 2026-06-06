---
rf_type: map
map_id: agentic_loop_research_map
status: active
created_at: 2026-06-05
updated_at: 2026-06-06
production_effect: none
linked_maps:
  - Agentic Lab Session - Bullish Positive - 2026-06-05
  - Archive Do Not Repeat - CEO 20260531
linked_concepts:
  - Agentic Research Loop
  - CEO Heartbeat
  - Action Contract
  - Loop Outcome Card
  - Trace Grading For Riskflow
  - Execution Provenance
  - Failure Avoidance Rate
  - Loop Meltdown Detection
  - Process Score Is Not Product Evidence
  - Research Infra Patch Plan
  - Hypothesis Source Broadening
  - Frozen Candidate Validation
  - Fresh Withheld Validation Contract
  - True CEO Autonomy
  - CEO Operating Dashboard
  - Evidence Debt Register
  - Approval Queue
  - Approval Apply
  - Executive KPIs
  - Heartbeat Persistence
  - Specialist Role Orchestration
  - CEO Replay
  - CEO Eval Suite
  - CEO State Machine
  - CEO Portfolio Allocator
  - CEO Memory Delta
  - CEO Guardrail Audit
  - CEO Preflight Gate
---

# Agentic Loop Research Map

This map tracks outside research and local implications for making Riskflow's CEO heartbeat, lab-loop, evidence governance, and Obsidian memory stronger.

Created during the 2026-06-05 flight research goal.

## Core Takeaway

Riskflow already has the right skeleton: bounded CEO heartbeats, governed lab loops, strict referee checks, lane routing, self-audits, and curated Obsidian memory.

The 9.9/10 upgrade is to make every autonomous loop more inspectable and outcome-scored:

```text
orchestrator -> specialist agents -> executor -> referee -> memory writer -> next-action router
```

## Transferable Patterns

### ReAct

Source: https://arxiv.org/abs/2210.03629

ReAct's useful lesson is interleaving reasoning with actions. For Riskflow, this supports the current CEO heartbeat policy: do not produce a long abstract plan without tool-grounded inspection, and do not run tools without a stated hypothesis.

### Reflexion

Source: https://arxiv.org/abs/2303.11366

Reflexion turns feedback into verbal memory rather than model weight updates. Riskflow's equivalent is concise Obsidian evidence summaries and no-repeat notes after a loop fails, stalls, or finds a stronger product role.

### Self-Refine

Source: https://arxiv.org/abs/2303.17651

Self-refinement is useful as a pattern for draft -> critique -> revise. In Riskflow, it should be split across roles: generator, critic, and evidence referee should not all grade themselves with the same incentives.

### Reward Hacking In Self-Refinement

Source: https://arxiv.org/abs/2407.04549

Iterative self-refinement can improve the evaluator's score while degrading real user preference. Riskflow should treat this as a direct warning against optimizing lab-meta/process scores without checking product-facing evidence, fresh data, and human chart intuition.

### Voyager

Source: https://arxiv.org/abs/2305.16291

Voyager combines an automatic curriculum, skill library, and self-verification. Riskflow's analogue is a queue curriculum plus reusable research commands. The risk is open-ended exploration without a hard promotion ladder.

### SWE-agent

Source: https://arxiv.org/abs/2405.15793

SWE-agent shows that the agent-computer interface matters. For Riskflow, every repeated manual inspection should become a clear CLI or report surface with stable paths, concise outputs, and test coverage.

### Toolformer

Source: https://arxiv.org/abs/2302.04761

Toolformer reinforces the idea that tool use is itself a learned interface problem: which tool, when to call it, what arguments to pass, and how to use the result. Riskflow should make CEO actions narrower, with explicit preconditions, outputs, and stop conditions.

### Memory Architectures

Sources:

- https://arxiv.org/abs/2304.03442
- https://arxiv.org/abs/2310.08560

Generative Agents and MemGPT point toward memory as an active operating layer, not a passive transcript. Riskflow's memory should be compact, retrievable, and action-changing: what changed, what failed, what not to repeat, and what exact next test is required.

### Tree Search And Debate

Sources:

- https://arxiv.org/abs/2305.10601
- https://arxiv.org/abs/2305.14325

Tree/debate methods are useful when strategy is uncertain and alternatives are meaningfully different. They are not a reason to run always-on debate. Riskflow should reserve multi-agent critique for high-uncertainty strategy changes, promotion proposals, and confusing evidence branches.

### Agent Judging

Sources:

- https://arxiv.org/abs/2306.05685
- https://arxiv.org/abs/2410.10934

LLM-as-judge and agent-as-judge methods are useful for critique, but Riskflow should not let them validate statistics. Deterministic evidence checks come first; LLM critique should check coherence, missing controls, citation accuracy, and product-language overreach.

### Anthropic Multi-Agent Research

Source: https://www.anthropic.com/engineering/multi-agent-research-system

The useful pattern is orchestrator-worker research: a lead agent decomposes work, subagents search or inspect independently, and a citation/evidence pass anchors claims. Riskflow should use agents for distinct critique lanes: architecture, evidence, Obsidian memory, and product translation.

### OpenAI Agent Evals

Source: https://platform.openai.com/docs/guides/agent-evals

The practical lesson is trace grading: debug workflow behavior from traces first, then move to repeatable datasets and eval runs. Riskflow should grade CEO heartbeats from action ledgers before adding more autonomy.

### OpenAI Tracing And Guardrails

Sources:

- https://openai.github.io/openai-agents-python/tracing/
- https://openai.github.io/openai-agents-python/guardrails/

The practical lesson is that traces should include model steps, tool calls, handoffs, guardrails, and custom workflow events. Riskflow's local equivalent is `binding_action_result.yaml`, `ceo_action_ledger.jsonl`, `ceo_self_audit.yaml`, `trace_grade.yaml`, and [[Loop Outcome Card]].

Guardrails should live near the action they constrain. For Riskflow, that means the CEO dispatcher should keep production-change blocks, stop-file checks, self-audit checks, and fresh/control gates close to the command branch that would otherwise act.

Continuation update: Riskflow now applies this pattern through
`action_contract.yaml`, `binding_action_result.yaml`, `ceo_action_ledger.jsonl`,
`ceo_self_audit.yaml`, `trace_grade.yaml`, and [[Loop Meltdown Detection]].
Repeated manual data gates and repeated no-progress fingerprints must route to a
strategy change or stop instead of another generic loop.

### Anthropic Workflows Before Agents

Source: https://www.anthropic.com/research/building-effective-agents

The useful distinction is predictable workflows versus open-ended agents. Riskflow should keep known paths as explicit workflows: `execute-next`, champion/challenger, fresh/control planning, lane recovery, trace grading, and Obsidian validation. Use open-ended agents for critique, research synthesis, and ambiguous strategy only.

Continuation update: the explicit workflow chain now includes
`fresh-data-preflight`, [[Frozen Candidate Validation]], frozen adapter rerun,
[[Fresh Withheld Validation Contract]], and champion/challenger visual-review
queues before product language.

### Google Agents Companion / AgentOps

Source: https://www.kaggle.com/whitepaper-agent-companion

The useful pattern is AgentOps: treat agents as operational systems with tool
management, orchestration, memory, task decomposition, evaluation, and business
metrics. For Riskflow, the "business metric" is not loop count. It is improved
decision quality: fewer repeated failures, clearer product gates, better
candidate evidence, and more reliable handoff to fresh sessions.

This supports [[True CEO Autonomy]]: the CEO layer should manage a portfolio of
research bets, explicit risk controls, memory quality, and product-evidence
gates rather than merely run experiments.

Continuation update: [[CEO Operating Dashboard]] now materializes that portfolio
view locally across candidates, capability backlog, data gate, memory, trace,
and risk.

Continuation update: [[Evidence Debt Register]] now turns product-governance
blockers into candidate-level evidence debts with owner commands.

Continuation update: [[Approval Queue]] and [[Executive KPIs]] add the missing
authority and scoreboard layers. Red-authority decisions are recorded as pending
user approvals, and CEO runs now have compact operating metrics for approvals,
evidence debt, candidate count, capability backlog, trace health, and validation
threshold status.

Continuation update: [[Heartbeat Persistence]] adds `heartbeat-plan`,
`heartbeat-tick`, and `heartbeat-journal` so long CEO runs can resume from a
tick journal rather than chat memory. Each tick inspects gates, blocks red or
unsafe states, and runs at most one bound action.

Continuation update: [[Specialist Role Orchestration]] adds role registry,
role task queue, and role result ledger artifacts so evidence debt, approvals,
and capability gaps can be routed to validation referee, data steward, product
translator, risk officer, memory editor, or research director review.

Continuation update: [[CEO Replay]] and [[CEO Eval Suite]] add the first
objective 9.9-readiness harness. CEO replay reconstructs action, heartbeat,
approval, and role-result timelines from append-only ledgers. The eval suite
scores replayability, [[CEO State Machine]] transition legality,
action-contract consistency, approval gating, production guardrails, validation
authority, role-result closure, trace-grade usability, and evidence-debt
visibility from local artifacts.
`ceo eval-fixtures` adds deterministic policy regression cases for those
transition rules so the harness can test itself even before a long live run
exists.

Continuation update: [[Approval Apply]] closes the approval workflow without
making approval recording itself mutating. `approval-record` remains ledger-only;
`approval-apply --user-confirmed --apply` is the second explicit closure step.
Promotion approval closure is shadow-only and still does not mutate production
formulas, scores, states, rankings, alerts, Pine, or TradingView defaults.

Continuation update: [[CEO Portfolio Allocator]] adds the first value-of-
information lane selector. It ranks approval governance, validation authority,
candidate translation, evidence debt, research infrastructure, specialist
review, trace reliability, and memory handoff before choosing the highest-value
operating bottleneck.

Continuation update: [[CEO Memory Delta]] turns memory updates into a governed
artifact and optional curated Obsidian handoff note. It records exact CEO
artifact refs and reopen conditions, while keeping memory notes subordinate to
generated runtime artifacts.

Continuation update: [[CEO Guardrail Audit]] and [[CEO Preflight Gate]] start
turning generated CEO artifacts into execution constraints. The guardrail audit
scans artifacts for unsafe production or product-language claims; the preflight
gate unifies trace, replay, eval, approval, memory, and heartbeat-budget status
before direct `execute-next` or heartbeat dispatch.

### Durable Execution

Source: https://docs.langchain.com/oss/python/langgraph/durable-execution

Durable workflow systems separate state, side effects, pausing, and resuming. Riskflow's file-first approach is aligned with this: every important wake should leave enough disk state for a fresh session to resume without trusting chat memory.

The local upgrade from this session is [[Loop Outcome Card]], which gives the next wake a compact durable state summary.

### 12-Factor AgentOps

Source: https://www.12factoragentops.com/

The useful loop is context -> work -> validation -> learning. Riskflow's version is:

```text
prime docs + Obsidian maps -> bounded CEO action -> tests/trace/vault validation -> no-repeat or next-action memory
```

This supports small context packets, repo-native artifacts, and explicit learning deltas instead of transcript-dependent autonomy.

### Agent Laboratory

Source: https://arxiv.org/abs/2501.04227

Agent Laboratory stages research into literature review, experimentation, and report writing with human feedback at each stage. Riskflow should preserve this staging: literature and strategy notes first, runnable experiments second, product translation third.

### The AI Scientist

Source: https://arxiv.org/abs/2408.06292

The useful idea is end-to-end research with generated ideas, code, experiments, visualization, writing, and review. The caution is that automated review is not product truth. Riskflow can borrow the staging but must keep strict referee and human review gates.

### AlphaEvolve

Source: https://arxiv.org/abs/2506.13131

AlphaEvolve is most relevant where the objective is executable and evaluators are reliable. Riskflow should use evolutionary or search-like agents only for research infrastructure and measurable candidate grids, not subjective product claims.

### Magentic-One

Source: https://arxiv.org/abs/2411.04468

Magentic-One's orchestrator tracks progress, replans, and delegates to specialized agents. Riskflow's CEO layer should do the same, but with stronger stop and no-production guarantees.

### MemGym

Source: https://arxiv.org/abs/2605.20833

MemGym separates memory evaluation from general reasoning/tool-use performance. Riskflow should evaluate whether its memory layer improves next-action selection, not merely whether notes exist.

### EvoMemBench

Source: https://arxiv.org/abs/2605.18421

EvoMemBench evaluates memory across in-episode versus cross-episode scope and knowledge-oriented versus execution-oriented content. Riskflow's equivalent should separate fact memory from execution memory: a chart pattern note is not the same as a no-repeat routing lesson.

### Memory Mechanism Survey

Source: https://arxiv.org/abs/2603.07670

The survey's write-manage-read framing maps directly to Riskflow's Obsidian workflow. The missing local score is not "did we write a note?" but "did retrieval of that note change the next CEO or lab action?"

### Memory Mis-Evolution

Source: https://arxiv.org/abs/2604.15774

Memory can drift when noisy tool outputs, biased feedback, or contaminated notes accumulate. Riskflow's defense is a small curated memory layer, explicit [[Archive Do Not Repeat]] reopen conditions, and [[Memory Quality Gate]] rules that force each note to name the action it changes.

### BenchTrace

Source: https://arxiv.org/abs/2605.29225

BenchTrace's useful idea is targeted failure avoidance. Riskflow should track [[Failure Avoidance Rate]] locally: after a named failure mode is logged, does the next run avoid it or replay it under a new label?

### Counterfactual Trace Auditing

Source: https://arxiv.org/abs/2605.11946

Counterfactual trace auditing compares agent behavior with and without a skill, then describes how the skill changed the trace. Riskflow can use this concept cautiously for research infrastructure changes: did adding a planner reduce repeat loops, improve recovery routing, or merely create extra artifacts?

### Execution Provenance

Source: https://arxiv.org/abs/2606.04990

Recent provenance work reinforces that final answers are not enough. Riskflow should keep moving toward [[Execution Provenance]]: action contracts, ledgers, outcome cards, trace grades, and claim-level links from Obsidian summaries back to concrete evidence.

## Proposed Riskflow Improvements

1. Maintain [[Loop Outcome Card]] as the compact wake-to-wake summary.
2. Keep expanding `ceo trace-grade` from artifact checks toward richer trace-quality scoring.
3. Keep expanding stop-reason routing so repeated governed stalls map to supported validation, fresh-data, Obsidian-queue, or capability-gap actions.
4. Add an agent delegation protocol: architecture critic, evidence critic, product translator, and memory linker.
5. Add no-repeat memory notes for saturated families and failed branches.
6. Add [[Process Score Is Not Product Evidence]] as a guardrail wherever lab-meta or trace scores are reported.
7. Add a source-backed literature map for agentic-loop patterns and their local Riskflow translation.
8. Use [[Memory Quality Gate]]: every curated evidence note must state what future action it changes.
9. Add champion/challenger product-delta summaries that speak in product roles, not just metrics.
10. Add visual-review triggers for promising warning/blocker candidates before any product-facing language.
11. Maintain [[Action Contract]] before each `ceo execute-next` action: allowed command, scope, expected artifact, stop condition, and forbidden changes.
12. Split strict referee into deterministic evidence checks first and LLM critique second.
13. Treat warning grammar and bullish setup journeys as separate curricula, not one blended optimization loop.
14. Add a long-run meltdown detector: three repeats of the same no-progress condition should stop and report.
15. Extend failure-avoidance checks beyond the current repeated-prior-failure case into broader negative-transfer and stale-memory patterns.
16. Keep enriching provenance fields on outcome cards and trace grades for the specific evidence artifacts that changed the next action.
17. Extend fresh-data/import routing if the data workflow becomes safe to automate; until then, keep `import_or_curate_fresh_ohlcv_data` as a manual gate.
18. Treat [[CEO Eval Suite]] as the objective autonomy gate before calling CEO mode 9.9-ready.
19. Use [[CEO Replay]] before fresh-session continuation so the next operator can reconstruct what happened without chat history.
20. Use [[Approval Apply]] for second-step approval closure instead of letting approval ledger rows have side effects.
21. Use [[CEO Portfolio Allocator]] to explain why a heartbeat chose one lane instead of another.
22. Use [[CEO State Machine]] checks to catch action drift between bound CEO decisions.
23. Run `ceo eval-fixtures` after changing CEO dispatch or approval policy.
24. Run [[CEO Memory Delta]] at the end of meaningful CEO work before relying on chat history.
25. Run [[CEO Preflight Gate]] before long-running heartbeat dispatch.
26. Keep expanding [[CEO Guardrail Audit]] from production-effect checks toward richer tool-boundary checks.

## Local Agent Findings

Two local inspection agents audited the repo during the 2026-06-05 flight research session.

### Obsidian Architecture Finding

The best memory architecture is two-layered:

- permanent maps and concepts define the research ontology
- dated session maps summarize what an extended agentic loop actually learned

This session created [[Agentic Lab Session - Bullish Positive - 2026-06-05]] as the first active example.

### CEO/Lab Architecture Finding

The strongest current design pattern is the layered stack:

```text
lab-loop -> lab-ops -> governance -> CEO execute-next -> Obsidian memory
```

The most important original gap was that several executive decisions were labels without complete executors:

- `patch_research_infra`
- `broaden_hypothesis_source`

This session closed the fresh/control-validation executor gap and added bounded routes for `patch_research_infra` and `broaden_hypothesis_source`. The remaining work is richer validation/import behavior, not basic CEO dispatch.

The 2026-06-01 stopped run confirmed the issue: open lanes remained, but recovery generated zero supported specs. This points to [[Governed Research Lane]], [[Archive Do Not Repeat]], and [[Fresh Data Validation Gate]] as near-term infrastructure concepts.

### First Local Patch From This Research

Implemented during this session:

- `ceo execute-next` now blocks if `ceo_self_audit.yaml` says `intervention_required: true` and the chosen decision is not an intervention decision.
- `ceo trace-grade` now writes trace-grade YAML/Markdown for CEO runs.
- Lane recovery now has first-pass supported specs for `cross_asset_regime`, `path_management`, `invalidation`, and `gradient_interpretation`.
- `ceo fresh-control-validation` now writes a bounded validation plan for promising champion/challenger shadow candidates.
- `ceo patch-research-infra` now writes a bounded research-infra recovery plan and may append audited governed recovery queue items.
- `ceo broaden-hypothesis-source` now compiles Obsidian/research-source hypotheses into shadow runtime queue items.
- `ceo trace-grade` and [[Loop Outcome Card]] now carry explicit process-only product-evidence fields, [[Execution Provenance]], and [[Failure Avoidance Rate]] status.
- [[Archive Do Not Repeat - CEO 20260531]] now captures the old run's saturated branches and reopen conditions.
- [[Action Contract]] now declares the selected CEO action before execution, and [[Loop Outcome Card]] summarizes each binding action afterward.
- [[CEO Replay]] now reconstructs a CEO run from action, heartbeat, approval, and role-result ledgers.
- [[CEO Eval Suite]] now grades replayability, state-machine legality, approval safety, validation gates, production guardrails, role closure, and evidence-debt visibility.
- [[Approval Apply]] now gives recorded approvals a second explicit closure step while keeping promotion approval shadow-only.
- [[CEO Portfolio Allocator]] now ranks operating lanes before extended autonomy continues.
- `ceo eval-fixtures` now regression-tests critical CEO transition policies.
- [[CEO Memory Delta]] now creates governed memory-delta artifacts and optional curated handoff notes.
- [[CEO Preflight Gate]] now gives heartbeat dispatch one unified safety decision.
- [[CEO Guardrail Audit]] now scans CEO artifacts for production-effect and product-language violations.
- Direct `ceo execute-next` now consumes [[CEO Preflight Gate]] before bound dispatch. Bootstrap runs can start without an action ledger, but real guardrail/replay/eval/approval/budget blockers stop the action.

The real stopped run `ceo_supervised_chain_20260531` originally graded as `warn` because its stop request should be honored and its next action, `run_fresh_or_control_validation_for_promising_shadow_challengers`, did not yet have a bound executor. This session added the planner; the stop request should still be honored unless the user intentionally starts a new run or clears stop files.

The lane-recovery, source-broadening, and fresh/control patches are deliberately research-only: generated queue items and validation plans still carry `production_effect: none`, and tests validate routing before any governed lab run consumes them.

## Immediate Local Research Questions

- How should `ceo trace-grade` score richer action-contract quality without overfitting to old runs?
- Which stale run stop reasons still lack supported next-action routers after extended lane recovery, source broadening, and fresh/control planning?
- Which Obsidian notes should become no-repeat memory for saturated research families?
- Can the targeted bullish queue be regenerated from setup journeys without repeating stale families?

Related:

- [[Agentic Research Loop]]
- [[Trace Grading For Riskflow]]
- [[Process Score Is Not Product Evidence]]
- [[Execution Provenance]]
- [[Failure Avoidance Rate]]
- [[Action Contract]]
- [[Loop Outcome Card]]
- [[Research Infra Patch Plan]]
- [[Hypothesis Source Broadening]]
- [[Agent Memory As Research Infrastructure]]
- [[Memory Quality Gate]]
- [[CEO Heartbeat]]
- [[Governed Research Lane]]
- [[Fresh Data Validation Gate]]
- [[Fresh Withheld Validation Contract]]
- [[Archive Do Not Repeat]]
- [[Champion Challenger Shadow Mode]]
- [[Evidence Debt Register]]
- [[Agentic Lab Session - Bullish Positive - 2026-06-05]]
- [[Lab Loop]]
- [[Signal Grammar Lab]]
- [[Indicator Grammar]]
