# Riskflow Pressure Wave Testing Loop

This document defines the visual QA loop for the experimental pressure-wave overlay in the TradingView indicator.

The goal is not to make a decorative second oscillator. The goal is to create a subtle, intuitive pressure layer that helps answer:

- Is relative pressure accumulating before the main signal confirms?
- Is the setup gaining or losing internal thrust?
- Is the fast pressure wave leading the slow pressure wave in a useful way?
- Is a bullish-looking setup actually supported by sustained pressure above viscosity?
- Is a weak or failed setup identifiable before it becomes obvious on price?

## Current Status

Pressure waves are an experimental candidate family inside the broader Signal Grammar Lab. They are not the mission by themselves.

The wave work should pause as a formula-iteration loop until the observation library clarifies which grammar primitives actually matter. The current candidate can still be reviewed, scored, and preserved, but it should not drive core oscillator tuning or product decisions yet.

## Current Candidate

The active visual candidate is:

```text
V9 Riskflow Big Pressure Waves [Area Gap Prototype]
```

V9 measures signed area around the adaptive viscosity baseline. It uses separate fast and slow area reservoirs:

- positive pressure: signal above viscosity, weighted by distance
- negative pressure: signal below viscosity, weighted by distance
- fast wave: shorter memory of signed pressure balance
- slow wave: longer memory of signed pressure balance
- fill: the fast/slow gap, used as a visual lead-lag cue

This is deliberately different from a moving average of the signal line. The visual question is whether the chart is spending more useful pressure above or below viscosity, and whether that pressure is accelerating or fading.

## Design Target

A 900+/1000 version should feel like:

- a pressure wave, not a second signal line
- smoother than the main oscillator, but not late
- subtle enough to sit behind the main signal
- clear when fast pressure is leading slow pressure
- honest during failed setups
- readable on phone screenshots
- useful on both 4H tactical examples and 1D structural examples

## Score Rubric

Each candidate version is scored out of 1000.

```text
Visual clarity:          200
Leading usefulness:      200
False-positive control:  200
Confluence readability:  150
Visual polish:           150
Cross-chart robustness:  100
```

### Visual Clarity

Does the pressure layer make the setup easier to read, or does it add noise?

### Leading Usefulness

Does the pressure wave curl, cross, or build before the obvious zero-line confirmation?

### False-Positive Control

Does it avoid looking bullish during weak chop, steep failed bounces, and noisy sold-off impulses?

### Confluence Readability

Can a human quickly see whether the fast wave, slow wave, main signal, viscosity, and key levels agree?

### Visual Polish

Does it look good enough to be a user-facing indicator layer?

### Cross-Chart Robustness

Does it still make sense across bullish, bearish, failed, noisy, 4H, and 1D examples?

## Promotion Rules

A pressure-wave candidate cannot be treated as the new preferred visual layer unless:

- the average score across the fixed matrix is at least 900
- no important false-positive case scores below 750
- it improves at least two known weak examples without degrading the clean TROLL/SPX/TURBO cases
- the interpretation can be explained in one or two sentences
- it is visually useful before zero-line confirmation, not only after confirmation
- it remains optional and does not alter the core signal, viscosity, ranking, states, or research outputs

## Iteration Rules

Change one major thing at a time.

Allowed iteration knobs:

- fast area length
- slow area length
- area-memory formula
- smoothing level
- normalization length
- fill color logic
- opacity
- zero deadband
- signal gating
- threshold labels

Do not change the base oscillator while testing the wave layer.

## Screenshot Protocol

For each candidate:

1. Load the Pine candidate in TradingView.
2. Capture the same fixed cases from `research/wave_tests/wave_test_matrix.md`.
3. Save screenshots under:

```text
reports/tradingview_review/wave_tests/<version>/
```

4. Verify each screenshot before using it.
5. Score the candidate in `research/wave_tests/wave_scorecard.csv`.
6. Record what improved and what got worse.

## Human Review Questions

For each screenshot, ask:

- What should I be looking for here?
- Did the wave help me see the setup earlier?
- Did the fill between waves clarify bullish or bearish pressure?
- Did the wave avoid giving a fake green light?
- Would this be useful on mobile?
- What would I change visually?

## Research Bridge

If a visual behavior repeats across enough cases, convert it into a testable feature or event later.

Candidate measurable ideas:

- fast wave crossing above slow wave below zero
- fast/slow gap expanding upward while signal is below zero
- slow wave rising while signal chops below zero
- pressure area turning positive before viscosity reclaim
- negative pressure failing to expand below -1.5 or -2
- bearish fast/slow cross above zero after weaker color push

These should be tested with Layer 7-style evidence before they affect any production score or signal.

## Relationship To Signal Grammar Lab

The wave layer currently maps mostly to the `pressure_acceptance` and `curvature_intent` grammar families.

Known limitations from the first matrix pass:

- It can look too broad or late on some clean reversals.
- It can become falsely constructive in weak-chop or steep-downtrend failures.
- It does not explain divergence, trendline breaks, or color weakening by itself.
- It may be better as one ingredient in a setup-quality visual rather than the entire intelligence layer.

Do not optimize the wave only to TROLL/SPX-style clean winners. A useful wave must also handle TRUMP, SHIB, BONK, PEPE divergence cases, and ambiguous GIGA-style bases.
