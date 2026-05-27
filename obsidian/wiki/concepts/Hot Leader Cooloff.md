# Hot Leader Cooloff

A confirmed leader cools off after the oscillator has reached a very hot zone, usually above `+2`.

## Role In The Grammar

This is a reset-watch concept, not a sell signal by itself.

## Evidence Snapshot 2026-05-27

Measured as `grammar_hot_leader_reset_warning_v0`.

- `1d`: useful, 182 samples, median 30-bar forward relative return `-0.1474`.
- `12h`: useful, 88 samples, median 30-bar forward relative return `-0.0451`.
- `4h`: useful, 192 samples, median 30-bar forward relative return `-0.0210`.
- `1h`: watchlist, 406 samples, median 30-bar forward relative return `-0.0036`.

Current read: hot-leader cooloff is evidence-backed as a reset/avoid warning. It should not be treated as a permanent bearish thesis; the next research question is when the later reheat becomes constructive.

Common sequence:

`hot_leader_impulse -> rollover_under_viscosity -> break_below_plus_1_5 -> reset_depth_watch`

## Related Concepts

- [[Confirmed Leader]]
- [[Under Viscosity Reset]]
- [[Break Below Plus One Point Five Reset]]
- [[Reset Depth Watch]]
- [[Gradient Reheat]]
- [[Time Above Viscosity]]

## Review Questions

- Does the asset remain structurally strong while cooling?
- Does the reset hold above the prior oscillator base, the 0 line, or lower-band support?
- Does a later reheat produce better entries than the first rollover?
