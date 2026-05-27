---
observation_id: TURBO_4h_20260321_failed_breakout_reset_reclaim_human_review
symbol: TURBO
timeframe: 4h
date: 2026-03-21T04:00:00
review_status: human_reviewed
human_label: clean_hit_sequence
---

# TURBO 4H Human Review - Failed Breakout Reset Reclaim

Related generated case id: `TURBO_4h_20260321_0400_coil_viscosity_reclaim_v0`

## Human Read

The biggest signal was the large oscillator downtrend break, but the sequence matters.

What happened:

- earlier oscillator downtrend break looked promising
- first break made a new oscillator high
- first break failed and price went lower
- second structure formed a descending channel
- signal washed below `-2`
- signal reclaimed viscosity
- signal quickly retested viscosity
- signal reclaimed `-1.5`
- expansion happened after the second break/reclaim sequence

## Human Tags

`clean_hit_sequence`, `failed_first_trendline_break`, `failed_first_breakout`, `second_trendline_break`, `descending_channel`, `channel_breakout`, `lower_band_washout`, `viscosity_reclaim`, `viscosity_retest_hold`, `minus_one_point_five_reclaim`, `failed_breakout_reset_reclaim`

## Linked Concepts

- [[Bullish Setup Grammar]]
- [[Structure Grammar]]
- [[Reset Grammar]]
- [[Failed First Trendline Break]]
- [[Failed First Breakout]]
- [[Second Trendline Break]]
- [[Descending Channel]]
- [[Channel Breakout]]
- [[Viscosity Reclaim]]
- [[Viscosity Retest Hold]]
- [[Minus One Point Five Reclaim]]
- [[Failed Breakout Reset Reclaim]]

## Principle

A first oscillator trendline break can fail. A second break may be stronger if the oscillator resets deeply below `-2`, then reclaims viscosity, retests it, and reclaims `-1.5`.

## Next Test Idea

Search for cases with:

```text
failed_first_trendline_break
second_trendline_break
lower_band_washout
viscosity_reclaim
viscosity_retest_hold
minus_one_point_five_reclaim
```

Then compare them against simple first-break and simple viscosity-reclaim events.
