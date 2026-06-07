# CEO Board Reporting

The CEO board report is a business-level synthesis layer. It should be written
after meaningful CEO-mode work, not after every diagnostic refresh.

## Required Questions

- What got better in Riskflow?
- What got falsified or archived?
- What customer-facing decision is now easier?
- What evidence supports that?
- What language is still forbidden?
- Where did CEO attention go?
- What remains blocked by user approval, data, validation, or specialist work?
- What is the next capital-allocation decision?

## Inputs

- `final_ceo_report.md`
- `executive_kpis.yaml`
- `portfolio_allocator.yaml`
- `mission_score.yaml`
- `strategy_capital_dashboard.yaml`
- `org_progress_score.yaml`
- `ceo_eval_suite.yaml`
- `guardrail_audit.yaml`
- `artifact_coherence.yaml`
- `role_task_queue.yaml`
- `evidence_debt_register.yaml`

## Output Shape

1. Executive summary.
2. Product/customer progress.
3. Evidence and validation state.
4. Capital allocation.
5. Risks, blockers, and asks.
6. Next decision.
7. Forbidden claims/actions.

## Guardrail

The board report is strategy memory. It cannot authorize dispatch, approve
promotion, validate a candidate, or change formulas, rankings, states, scores,
alerts, or TradingView defaults.

