# Indicator Behavior Encoding

This directory registers broad indicator-behavior concepts as Riskflow-native
research specifications.

The files here do not change production formulas, TradingView defaults,
Riskflow states, rankings, scores, or Pine output. They define what each idea
would mean in terms of the columns Riskflow already calculates or can calculate
as sidecars.

## Files

- `primitive_registry.yaml` defines the measurable building blocks.
- `concept_library.yaml` maps the 99 researched concepts onto those primitives.

## Promotion Path

Concepts start at `L0_registered`. A concept can only become a gradient,
warning, marker, score modifier, or Pine candidate after it survives:

1. mechanical implementation without lookahead;
2. single-concept event studies;
3. duplicate event pruning;
4. time-split validation;
5. strict baseline and random-null checks;
6. fresh-data rerun after the rule is frozen.

Only `L4_fresh_validation_survivor` or better should be considered for
indicator changes.

## Riskflow Mapping Rule

Each concept must be expressed with:

- `final_signal` for oscillator position and shape;
- `viscosity` for the adaptive baseline;
- `gradient_driver` for color/pressure behavior;
- `relative_component` for leadership versus the basket;
- `compression_score` for squeeze/chop context;
- `target`, `benchmark`, and forward relative return for outcomes;
- optional `grammar_*` sidecar columns when an existing primitive already
  measures the behavior.

