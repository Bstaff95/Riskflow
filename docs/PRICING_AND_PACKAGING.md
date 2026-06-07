# Riskflow Pricing And Packaging

This document captures pricing hypotheses for Riskflow. It is not a billing
plan and does not authorize building paid infrastructure.

## Pricing Principle

Price should follow proven workflow value, not internal effort. Until Riskflow
has customer discovery and repeated usage evidence, every price is a hypothesis.

CEO mode should prefer manual packages that test willingness to pay before
building subscriptions, hosted services, or account systems.

Source anchors:

- YC's essential startup advice warns against scaling before making something
  people want and emphasizes unit economics:
  https://www.ycombinator.com/blog/ycs-essential-startup-advice
- First Round has a pricing topic hub collecting early pricing essays:
  https://review.firstround.com/articles/pricing/

## Package Hypotheses

### Manual Research Note

- User: active trader who wants faster watchlist triage.
- Format: weekly or ad hoc relative-leadership and warning report.
- Value metric: fewer charts to review and clearer avoid/watch decisions.
- Price band to test: low three figures per month.
- Proof required: user asks for repeated reports or says which decisions changed.
- Build guardrail: do not automate delivery until at least three repeated users
  want the same format.

### TradingView Companion

- User: trader who already lives in TradingView.
- Format: Pine indicator plus plain-English interpretation guide.
- Value metric: chart readability and reduced false excitement.
- Price band to test: comparable to premium indicator subscriptions.
- Proof required: user can explain why the indicator improved a real chart read.
- Build guardrail: do not change Pine defaults or product claims without
  promotion approval.

### Local Scanner Output

- User: researcher who wants ranked watchlists and CSV/HTML output.
- Format: local scan plus report bundle.
- Value metric: time saved triaging a universe.
- Price band to test: higher than a simple indicator if it replaces manual
  screening.
- Proof required: repeated use, saved workflow examples, and willingness to
  import data or accept curated data constraints.
- Build guardrail: do not build hosted ingestion or accounts in v1.

### Private Beta Cohort

- User: 5 to 10 serious crypto researchers.
- Format: guided usage, manual onboarding, periodic reports, feedback calls.
- Value metric: repeated usage and concrete workflow language.
- Price band to test: free design partner only if learning value is high; paid
  beta when users ask for continuity.
- Proof required: retention across multiple market weeks.
- Build guardrail: do not scale acquisition before retention or workflow value
  is visible.

## Forbidden Pricing Moves

- Do not build Stripe, auth, account management, or usage metering in v1.
- Do not price as a guaranteed alpha product.
- Do not sell alerts or automated trading calls.
- Do not imply validated probability forecasts.
- Do not package Obsidian notes as proof.

## CEO Pricing Questions

- What decision does the user pay to make easier?
- Is the value time saved, better avoidance, better watchlist focus, or stronger
  conviction?
- Which package tests the value with the least engineering?
- What would make a user renew after two weeks?
- Which objection would kill this package?

## Acceptance Gate Before Charging

Riskflow should not ask for money until at least one package has:

- one real workflow example;
- a repeated painful user problem;
- a clear output format;
- a user saying what would be worth paying for;
- product-language guardrails that avoid performance claims.

Production effect: none.
