---
rf_type: concept
concept_id: agent_employee_organization_v2
status: active
updated_at: 2026-06-07
production_effect: none
future_action_changed: Build the next specialist harness around claimable tasks, reviewer/referee loops, merge receipts, and fake-progress controls.
not_product_proof: true
---

# Agent Employee Organization V2

Riskflow already has a first specialist harness:

- `ceo role-queue`;
- `ceo role-dispatch`;
- `ceo role-result`;
- structured `riskflow_ceo_specialist_result_v0` YAML;
- SHA-256 provenance rechecks;
- manual-gate isolation;
- promotion specialist gates;
- replay and eval-suite coverage.

V2 should turn that into an agent-employee organization. The design goal is not
"more agents." The design goal is accountable work that can be claimed,
reviewed, merged, replayed, and stopped.

## Task Market

Add a pull layer:

- `role_task_market.yaml`;
- `role_claim_ledger.jsonl`;
- `role_work_leases.yaml`;
- `ceo role-market`;
- `ceo role-claim --task-id <id> --role-id <id>`;
- `ceo role-release`.

Tasks should advertise:

- `required_capabilities`;
- `allowed_roles`;
- `blocking_artifacts`;
- `evidence_gate`;
- `authority_boundary`;
- `merge_target`;
- `ttl_minutes`;
- `value_of_information_score`.

Claims should be leases, not permanent ownership. Expired or duplicate claims
should reopen automatically.

## Role Split

Worker roles:

- `hypothesis_scout`;
- `experiment_runner`;
- `visual_reviewer`;
- `data_steward`;
- `infra_mechanic`;
- `memory_editor`;
- `customer_researcher`;
- `product_manager`;
- `pricing_analyst`;
- `gtm_strategist`;
- `board_secretary`.

Review roles:

- `validation_referee`;
- `risk_officer`;
- `product_translator`;
- `adversarial_reviewer`.

The CEO/orchestrator remains accountable for merge, archive, escalation, or
reroute decisions.

Business roles are defined in `docs/CEO_DELEGATION_MODEL.md`. They may draft
customer-discovery, pricing, GTM, board, and roadmap artifacts, but they may not
contact users, build billing, publish claims, change production formulas, clear
manual gates, or grant product language.

## Review And Debate

Add:

- `role_review_queue.yaml`;
- `role_review_ledger.jsonl`;
- `referee_decision.yaml`;
- `debate_packet.yaml`.

Every nontrivial completed worker result should require at least one reviewer.
Promotion-facing or archive-facing decisions require `validation_referee` plus
either `risk_officer` or `product_translator`.

Debate should be bounded and rare. Trigger it only when:

- two valid specialist results conflict;
- a candidate is close to promotion or archive;
- evidence gates disagree.

Debate format:

- `claim`;
- `supporting_result_refs`;
- `opposing_result_refs`;
- `referee_questions`;
- `decision`;
- `why_not_alternatives`.

No open-ended debate loops. Max one pro, one con, one referee pass before CEO
merge or escalation.

## Evidence Gates

- `G0 task_valid`: source artifacts exist, authority boundary explicit, no
  production mutation.
- `G1 result_valid`: schema, role/task match, nonempty evidence refs, product
  effect none.
- `G2 provenance_valid`: source artifact hashes still match.
- `G3 review_valid`: required referee/reviewer results accepted.
- `G4 decision_delta_valid`: result changes a belief, blocker, queue, archive,
  validation plan, or memory route.
- `G5 merge_safe`: target artifact is process-only, not production formula,
  Pine, ranking, state, score, or alert behavior.

## Merge Receipts

Specialist results should not mutate runtime truth directly.

Add:

- `ceo role-merge --task-id <id> --apply`;
- `role_merge_receipt.yaml`;
- immutable merge snapshots and hashes.

Allowed merge targets:

- `evidence_debt_register`;
- `capability_backlog`;
- `research_map`;
- `memory_delta`;
- `approval_queue`;
- `archive_do_not_repeat`;
- `next_action_queue`.

## Escalation

Escalate to the user for:

- manual gates;
- production-facing changes;
- ambiguous authority;
- fresh-data import requirements;
- promotion language.

Escalate to `infra_mechanic` for repeated artifact, coherence, or eval failures.
Escalate to `risk_officer` for stale safe dispatch signals, manual-gate
mismatch, or repeated no-progress. Escalate to archive when the same candidate
fails strict referee, review, or fresh/withheld thresholds repeatedly with no
new evidence path.

## Anti-Fake-Progress

Add `org_progress_score.yaml` with hard counters:

- repeated task fingerprint;
- repeated finding;
- repeated next action;
- no belief movement;
- no artifact delta;
- queue churn;
- debate churn;
- review rubber-stamp;
- memory note without future action changed.

A completed task should not count as progress unless it closes a gate or changes
a downstream decision. [[CEO Eval Suite]] should fail 9.9 readiness if the
organization has completed work but no accepted merge receipts.

## Obsidian Gate

Obsidian remains advisory. Runtime artifacts win.

Curated notes should flow through [[CEO Memory Delta]] and include:

- `run_id`;
- `task_id`;
- `merge_receipt`;
- source artifact paths and hashes;
- decision delta;
- future action changed;
- `production_effect: none`.

Related:

- [[Specialist Role Orchestration]]
- [[CEO Operating System For Riskflow]]
- [[CEO Eval Suite]]
- [[CEO Replay]]
- [[CEO Memory Delta]]
- [[True CEO Autonomy]]
