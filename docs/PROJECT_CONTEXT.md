# Riskflow Project Context

Riskflow is a local quant research engine for finding emerging market leadership and compressed opportunity candidates.

The long-term thesis is:

> The best asymmetric opportunities are often compressed assets at the end of strengthening capital-flow chains.

In practice, that means Riskflow should eventually identify when a broad asset class is improving, when a sector or narrative inside it is gaining leadership, when a subgroup is outperforming that sector, and when an individual asset inside that subgroup is starting to lead while still compressed.

## Canonical Name

- Project: Riskflow
- Python package: `riskflow`
- GitHub repo: `https://github.com/Bstaff95/Riskflow.git`

`leaderflow` was an earlier name and should not be used for package paths or commands.

## Current V1 Scope

V1 is a local Python research lab for crypto meme coins only.

The first proof question is:

> Can Riskflow identify meme coins that are becoming relative leaders versus the meme basket before the move is obvious?

V1 should:

- load local OHLCV CSVs
- build an equal-weight meme basket
- calculate a Pine-style relative strength engine
- detect asset-relative compression
- classify simple lifecycle states
- calculate an explainable opportunity score
- export CSV, HTML, and Obsidian markdown reports
- run event studies focused on forward relative returns versus the meme basket

## What Not To Build Yet

Do not build these in v1:

- live trading bot
- web dashboard
- Markov transition engine
- ML classifier
- global macro engine
- dynamic sector discovery
- exchange/API integrations unless explicitly requested

## Core Indicator Concept

The Pine prototype combines:

- price component
- asset-versus-benchmark relative component
- optional risk environment component

Each component is normalized with log transforms and rolling z-scores, clamped, then fused using active-weight root-sum-square scaling.

The default Python v1 final signal should be weight-scaled fusion, not final z-score.

## Key Research Principle

The highest raw leader is not always the best opportunity.

Riskflow should separate:

- leader quality
- entry/setup quality
- compression
- overextension
- forward relative-return evidence

The system should prefer explainable evidence over impressive labels.

## Current Indicator Research Pivot

The current indicator work should use a Signal Grammar Lab approach.

The base Pine-style oscillator remains the trusted reference for now. Pressure waves, confluence waves, area waves, dots, ribbons, markers, and other visual layers are candidates, not conclusions.

The important discovery is that the oscillator itself appears to be technical-analysis readable. Human-reviewed examples should be logged as observations, tagged with grammar primitives, and later converted into measurable events only when patterns repeat.

Priority grammar ideas:

- viscosity acceptance and retests
- `-2`, `-1.5`, `0`, `1.5`, and `2` reclaim/retest behavior
- oscillator trendline, wedge, and channel breaks
- failed weakness in deep negative zones
- bullish and bearish divergence
- color or gradient divergence
- time and signed area above or below viscosity
- curvature and acceleration before obvious confirmation

Memes are the discovery sandbox, not the final proof. Any indicator improvement meant for the eventual product should later validate on broader crypto and equities before becoming a universal default.

## Living End-State Guide

The broad cathedral-scale vision is tracked in `docs/END_STATE.md`.

That document is intentionally a living guide rather than a fixed spec. Riskflow should use it to preserve direction while continuing to question whether each layer is the best way to accomplish the goal.
