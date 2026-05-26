# Riskflow Pressure Wave Test Matrix

This is the fixed visual test set for pressure-wave candidates. Do not optimize to one chart. A version only matters if it works across clean winners, failed setups, bearish reads, noisy chop, and multiple timeframes.

## Active Candidate

```text
V9 Riskflow Big Pressure Waves [Area Gap Prototype]
```

Current provisional rating: `825 / 1000`.

V9 is promising because the fast/slow fill finally looks like a true pressure object rather than a second copy of the main signal. It still needs a full matrix pass before we trust it.

## Cases

| Case ID | Symbol | TF | Approx Focus Date | Scenario | What To Look For | Expected Visual Behavior |
|---|---:|---:|---:|---|---|---|
| WAVE-001 | TROLL | 4H | Apr 2026 | Clean bullish expansion | Descending wedge, -2/-1.5 retests, viscosity reclaim, impulse before run | Fast wave should curl above slow before the move; fill should turn constructive without becoming too noisy |
| WAVE-002 | SPX6900 | 4H | Apr 5 2026 | Early bullish breakout | Major signal downtrend break, wedge break, fast color shift, flat viscosity break | Wave should show pressure shift before or near the downtrend break, not only after price moves |
| WAVE-003 | TURBO | 4H | Mar 2026 | Second breakout works after first fails | Descending channel, prior failed break, reclaim viscosity, retest, -1.5 reclaim | First false break should look less convincing than second break |
| WAVE-004 | MOG | 4H | Apr-May 2026 | Hard-to-read bullish setup | Rising oscillator bottoms, time above viscosity, quick recovery after dump below viscosity | Slow wave should show improving pressure even when main line is messy |
| WAVE-005 | TOSHI3 | 1D | Sep 25 2024 | Early structural reversal | Long-term downtrend break, basing below -1.5/-2, weakness fails to accelerate | Wave should show negative pressure decaying before the obvious full reversal |
| WAVE-006 | TRUMP | 4H | Apr 12 2026 | Failed bullish-looking setup | Steep signal downtrend, weak bounce, underside rejection, breakdown | Wave should avoid giving a strong bullish read |
| WAVE-007 | GIGA | 4H | May 2026 | Ambiguous pre-run failure | Above viscosity but failed zero reclaim, spike and immediate retrace, later double bottom needed | Wave should show incomplete pressure, not full confirmation |
| WAVE-008 | SHIB | 1D | Aug-Oct 2025 | Weak chop / bearish warning | Choppy wedge, weak colors, poor structure, hidden bearish divergence | Wave should look weak or conflicted, not quietly bullish |
| WAVE-009 | PEPE | 1D | Nov 9 2023 | Divergence / continuation study | Price higher high with signal lower high, then double bottom with signal higher low | Wave should help distinguish bearish exhaustion from later bullish pressure return |
| WAVE-010 | BONK | 4H | Mar-Apr 2026 | Noisy false-positive risk | Volatile impulses sold off, rising highs but no compression or sustained pressure | Wave should avoid treating random spikes as durable pressure |

## Required Screenshots Per Candidate

Save verified TradingView screenshots here:

```text
reports/tradingview_review/wave_tests/<version>/<case_id>_<symbol>_<tf>.png
```

Optional annotated screenshots can add `_annotated` before `.png`.

## Review Template

For each case:

```text
Case:
Candidate version:
Screenshot path:
Visual clarity /200:
Leading usefulness /200:
False-positive control /200:
Confluence readability /150:
Visual polish /150:
Cross-chart robustness /100:
Total /1000:
Human read:
What improved:
What got worse:
Next one-change iteration:
```

## Candidate History

### V7

Finite rolling signed-area model. It introduced the right idea, but the waves were too saturated and pinned, making them look stochastic-like instead of pressure-like.

### V8

Reduced amplitude and cleaner fast/slow gap. Better, but still too close to a secondary signal/viscosity pair.

### V9

Leaky fast/slow area reservoirs around viscosity. Best current candidate. The fill between waves is the main object. Needs matrix scoring before further Pine changes.
