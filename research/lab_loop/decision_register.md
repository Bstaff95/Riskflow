# Riskflow Lab Decision Register

Append durable lab decisions here when they affect research direction,
promotion standards, or future loop behavior.

## 2026-05-29: Use A Bounded Autonomous Lab Loop

Decision:

Riskflow should run a bounded autonomous research loop rather than an ad hoc
brainstorm or endless brute-force search.

Why:

- The user wants the lab to keep learning without jumping across unrelated
  ideas.
- The 99-component run showed that broad brute force can find weaknesses, but
  bullish trade setups need staged definitions and trade-path outcomes.
- Agent review converged on a fixed operating system: queue, encoding,
  validation, promotion, notes, and occasional agent checkpoints.

Policy:

- Keep production formulas, states, scores, rankings, and TradingView defaults
  unchanged during research loops.
- Use `docs/LAB_LOOP.md` as the operating manual.
- Use `research/lab_loop/hypothesis_queue.yaml` as the ranked backlog.
- Promote candidates only through the L0 to L5 ladder.
- Use agents every 3 to 5 loops, after major survivor/dead-loop evidence, or
  before changing direction.

## 2026-05-29: Bullish Research Must Use Setup Journeys

Decision:

Bullish setups should be tested as staged journeys, not isolated events.

Canonical sequence:

```text
weakness/compression -> repair -> reclaim -> retest/hold -> continuation
```

Why:

- Single trigger tests produced weak positive evidence.
- The user's chart intuition is usually sequence-based: context, repair,
  trigger, confirmation, and invalidation.
- A setup can be useful if it gives favorable excursion before later mean
  reversion, even when terminal 30-bar return is mediocre.

Required outcomes:

- max favorable excursion;
- max adverse excursion;
- time to first upside;
- time underwater before upside;
- terminal forward relative return;
- retest versus no-retest behavior;
- lag and cooldown sensitivity.

## 2026-05-29: Relative Failed Breakout Is A Warning Candidate, Not Production Logic

Decision:

Daily relative failed breakout is the current strongest warning candidate, but
it is not ready for production gradient, score, or Pine logic.

Why:

- It survived stricter testing better than the other all-component concepts.
- Stress testing showed sensitivity to entry lag and cooldown.
- Current evidence supports continued testing, not promotion.

Next action:

Rerun after data refresh using the current baseline and refined candidates in
`research/grammar/rule_search_grid_v19_relative_failed_breakout_current_candidates.yaml`.

## 2026-05-29: Gradient Logic Comes After Evidence

Decision:

Do not encode new grammar into gradient behavior until a candidate survives the
promotion ladder far enough to justify visual/product work.

Why:

- The gradient is intuitive and product-important, so weak evidence could make
  the indicator feel smarter while actually becoming overfit or confusing.
- Research should first establish which grammar helps trade selection versus the
  basket.

Policy:

Gradient translation begins only after a candidate reaches at least
`L4_fresh_data_survivor`, unless the user explicitly asks for a separate visual
prototype.

