# Layer 4: Setup Quality And Trader Readiness

Layer 4 is Riskflow's setup-quality layer.

Layer 3 asks:

```text
Is this asset gaining strength versus its benchmark?
```

Layer 4 asks:

```text
Is this strengthening asset actually a good setup right now?
```

## Product Modes

- Leader Mode: find relative leaders and leadership chains.
- Trader Mode: find leaders that are compressed, early, and near confirmation.
- Research Mode: test setup events against forward relative returns.
- Indicator Mode: keep the TradingView oscillator clean and RSI-like.

Leader Mode and Trader Mode are intentionally different. A great leader can be a poor current setup if it is already extended.

## Layer Ownership

- Layer 3 owns the strength signal, including `final_signal`, `relative_component`, viscosity, and gradient behavior.
- Layer 4 owns compression quality, setup readiness, extension risk, and opportunity context.
- Layer 4 must not alter the TradingView-style oscillator formula.

## Versioned Contracts

Layer 4 model identities live in `src/riskflow/setup_registry.py`.

Current v0 contracts:

```text
compression_score_v0
state_model_v0
setup_quality_v0
opportunity_score_v0
```

Do not silently change the meaning of these outputs. Future changes should run side by side first, such as:

```text
opportunity_score_v1_candidate
setup_quality_v1_candidate
```

## Setup Components

Layer 4 v0 exposes separate components instead of hiding everything inside one number:

- `leader_quality_score`: strength context from Layer 3.
- `compression_quality_score`: compression score adjusted for duration, persistence, and stale-data risk.
- `relative_accumulation_score`: relative improvement while compression is present.
- `setup_readiness_score`: reclaim and confirmation behavior.
- `extension_risk_score`: overextension, expansion, and rollover risk.
- `data_quality_score`: feed/activity guardrail so stale flatness does not look like high-quality compression.
- `trader_score_v0`: experimental future Trader Mode ranking score.
- `opportunity_score_v0`: current backward-compatible opportunity score hypothesis.

The active `opportunity_score` remains available for stable leaderboard behavior.
The main leaderboard remains stable-first. `trader_score_v0` and `trader_rank` are available for review, but they do not replace the default ranking.

## Setup Tags

Layer 4 uses secondary tags rather than expanding the primary state vocabulary.

Initial tags:

```text
compressed
relative_strength_rising
viscosity_reclaim
zero_reclaim
near_confirmation
extended
rolling_over
high_drawdown_risk
```

These tags are context, not trade instructions.

Setup notes should explain why a row looks interesting or risky, for example:

```text
relative accumulation improving
setup readiness high
extension risk high
stale or inactive data; compression quality capped
```

## Research Hooks

Layer 4 setup events should be studied against forward relative returns:

- compression above threshold
- compression duration above threshold
- compression plus relative strength rising
- setup readiness crossing threshold
- relative accumulation crossing threshold
- compressed viscosity reclaim
- compressed zero reclaim
- extension risk appearing
- trader score crossing threshold

Small samples, one-symbol dominance, and one-cluster dominance should remain inconclusive.

Run Layer 4 research with:

```bash
python3 -m riskflow setup-research --config configs/meme_universe.yaml --timeframe 1d
```

## Promotion Policy

No Layer 4 model should change leaderboard ranking, state semantics, alerts, Obsidian summaries, or TradingView labels without a documented promotion note.

A promotion note must explain:

- what changed
- why it changed
- what improved
- what got worse
- affected downstream modules
- how user interpretation changes
- whether the old version remains available
