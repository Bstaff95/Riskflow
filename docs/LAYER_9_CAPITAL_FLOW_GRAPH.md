# Layer 9: Capital-Flow Graph

Layer 9 is Riskflow's first graph-shaped capital-flow layer.

The model id is:

```text
capital_flow_graph_v0
```

## Purpose

Layer 9 answers:

> Is this asset's setup supported by its parent/subgroup/sector chain, and does that support improve forward relative returns?

In v0, "capital flow" means inferred relative leadership and rotation pressure from available price-derived data. It does not mean literal fund-flow proof.

## Ownership

Layer 9 owns:

- graph nodes
- graph edges
- chain context
- chain labels
- graph evidence reports

Layer 9 does not own:

- signal formulas
- setup-quality formulas
- lifecycle state labels
- opportunity score formulas
- probabilities
- Markov transitions
- dashboards
- TradingView UI

## Graph Contract

Nodes:

- `universe`
- `sector`
- `subgroup`
- `asset`
- `basket`

Edges:

- `contains`
- `belongs_to`
- `benchmarked_against`
- `child_vs_parent`

Chains:

```text
MEME_BASKET -> subgroup -> asset
```

Example:

```text
MEME_BASKET -> base_memes -> BRETT
```

## V0 Honesty Rules

Current subgroup and sector nodes are structural placeholders until Layer 2 adds independent subgroup/sector baskets.

That means v0 can measure:

```text
asset vs MEME_BASKET
```

It cannot yet fully prove:

```text
asset vs subgroup vs sector vs broad crypto
```

When parent data is incomplete, graph outputs should say `Incomplete Chain` instead of inventing support or weakness.

## Chain Labels

Initial labels:

- `Full Chain Support`
- `Partial Chain Support`
- `Asset Leading Weak Parent`
- `Parent Strong / Asset Not Ready`
- `Conflicted Chain`
- `Incomplete Chain`

In v0, `Full Chain Support` is reserved for future independent parent chains. The practical useful label is usually `Partial Chain Support`.

## Reports

The `flow-graph` command exports:

```text
reports/flow_graph_nodes.csv
reports/flow_graph_edges.csv
reports/flow_graph_chains.csv
obsidian/reports/latest_flow_graph.md
```

The `flow-research` command exports:

```text
reports/flow_research_records.csv
reports/flow_research_summary.csv
reports/flow_research_summary.html
obsidian/reports/latest_flow_graph.md
```

## Evidence

Graph evidence asks:

> Do primary asset events perform better when the chain context is supportive?

It compares supportive chain context versus non-supportive or incomplete chain context using Layer 7-style outcomes:

- 3/7/14/30 bar forward relative returns
- 14/30 bar drawdowns
- hit rates
- sample-size checks
- symbol concentration
- calendar-cluster concentration

Classifications:

- `useful`
- `watchlist`
- `inconclusive`
- `fragile`

## Downstream Guardrails

Layer 9 must not silently change:

- `core_signal_v0`
- `state_model_v0`
- `opportunity_score_v0`
- `trader_score_v0`
- default leaderboard sorting
- TradingView oscillator interpretation

Graph context can affect production ranking only after it beats matched non-graph baselines under Layer 7 evidence gates.

## Deferred

Do not implement these in Layer 9 v0:

- graph database
- global macro graph
- dynamic narrative discovery
- graph embeddings
- Markov chains
- probability labels
- dashboard/network visualization
- automatic graph-based leaderboard ranking

Those require stronger Layer 2 benchmark infrastructure and more real evidence.
