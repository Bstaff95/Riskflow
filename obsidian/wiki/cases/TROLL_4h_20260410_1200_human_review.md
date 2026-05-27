---
observation_id: TROLL_4h_20260410_1200_coil_viscosity_reclaim_v0
symbol: TROLL
timeframe: 4h
date: 2026-04-10T12:00:00
review_status: human_reviewed
human_label: clean_hit
---

# TROLL 4H Human Review - 2026-04-10 12:00

Related generated case: [[TROLL_4h_20260410_1200_coil_viscosity_reclaim_v0]]

## Human Read

This is a good example of the setup.

More precise read:

- the oscillator structure looked like a `descending_wedge`
- it reclaimed viscosity, but did not cleanly retest viscosity
- it retested the `-2` level first
- it then retested the `-1.5` level
- those lower-band level holds mattered before the impulse

## Human Tags

`clean_hit`, `descending_wedge`, `oscillator_trendline_break`, `minus_two_retest_hold`, `minus_one_point_five_retest_hold`, `lower_band_support`, `viscosity_reclaim_without_retest`

## Principle

This is not only `coil -> viscosity reclaim`. A better principle is:

> Lower-band support and tightening oscillator structure can reveal accumulation before viscosity becomes the obvious confirmation.

## Next Test Idea

Search for cases with:

```text
descending_wedge
lower_band_support
minus_two_retest_hold
minus_one_point_five_retest_hold
viscosity_reclaim
```

Then compare those against simple `coil_viscosity_reclaim_v0` cases.
