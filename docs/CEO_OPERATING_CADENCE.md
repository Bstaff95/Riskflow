# CEO Operating Cadence

This cadence turns CEO mode into repeatable company operation. It does not
authorize production behavior, product language, or runtime dispatch.

## Every Wake

Before acting:

1. Run or inspect `ceo status --show-lab-status`.
2. Inspect approval queue, action board, preflight gate, dispatch receipt,
   decision quality, operator brief, eval suite, guardrail audit, artifact
   coherence, role queue, and org progress score.
3. Confirm whether the next action is diagnostic, manual-gated, repair-only, or
   a bounded executable action.
4. Execute at most one bounded action when authority is clean.
5. Refresh reportable trust artifacts after the action.

## Daily CEO Brief

Purpose: decide the highest-value work for the day.

Required inputs:

- run index;
- executive KPIs;
- portfolio allocator;
- mission score;
- strategy capital dashboard;
- org progress score;
- top approval, blocker, and role task;
- latest eval-suite readiness.

Output:

- top objective;
- top blocker;
- top research or product-value opportunity;
- next bounded command or manual ask;
- forbidden actions.

## Weekly Strategy Review

Purpose: prevent local optimization and fake progress.

Questions:

- Which mission dimension improved?
- Which customer-facing decision got easier?
- Which candidate or lane was falsified?
- Which evidence debt is oldest or most expensive?
- Which specialist roles are blocked or unmerged?
- Which research lane should receive less attention?
- Which product claim is still unsafe?

## Monthly Board Report

Purpose: translate work into business-level progress.

Required sections:

- what got better;
- what was falsified;
- customer value moved;
- evidence level and validation gaps;
- capital allocation across lanes;
- risks and asks;
- next month decision.

## Stop And Escalation Rules

Stop or ask the user when:

- a stop request exists;
- an approval queue item is pending;
- fresh data import or snapshot authority is required;
- product language or production behavior would change;
- guardrail audit fails;
- hard artifact coherence fails;
- role work is blocked in a way that needs human evidence;
- the system is repeating work without decision movement.

