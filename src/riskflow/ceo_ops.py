from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .lab_loop import atomic_write_text, atomic_write_yaml, load_yaml_file
from .lab_ops import (
    LAB_OPS_REPORT_ROOT,
    LAB_OPS_RUNTIME_ROOT,
    LabOpsOptions,
    run_lab_ops_report,
    run_lab_ops_run,
    run_lab_ops_status,
)


CEO_MANIFEST_MODEL = "riskflow_ceo_manifest_v0"
CEO_COMPANY_STATUS_MODEL = "riskflow_ceo_company_status_v0"
CEO_PRODUCT_DELTA_MODEL = "riskflow_ceo_product_delta_scoreboard_v0"
CEO_INFRA_DELTA_MODEL = "riskflow_ceo_research_infra_delta_v0"
CEO_UNDERSTANDING_DELTA_MODEL = "riskflow_ceo_understanding_delta_v0"
CEO_RISK_REGISTER_MODEL = "riskflow_ceo_risk_register_v0"
CEO_KNOWLEDGE_GRAPH_DELTA_MODEL = "riskflow_ceo_knowledge_graph_delta_v0"

CEO_REPORT_ROOT = Path("reports/ceo_runs")

PRODUCT_LANES = {
    "bullish_permission",
    "warning_blocker",
    "invalidation",
    "reset_quality",
    "gradient_interpretation",
    "path_management",
    "cross_asset_regime",
}

TERMINAL_TRUE_BLOCKERS = {
    "missing_market_data",
    "state_corrupt",
    "artifact_hygiene_required",
    "director_audit_failed",
    "meta_audit_failed",
    "governed_recovery_audit_failed",
}


@dataclass(frozen=True)
class CeoOpsOptions:
    objective: str = "bullish-positive"
    run_id: str | None = None
    lab_run_id: str | None = None
    queue_path: Path = Path("research/lab_loop/hypothesis_queue.yaml")
    config_path: Path = Path("configs/meme_universe.yaml")
    data_dir: Path = Path("data/raw")
    timeframes: tuple[str, ...] = ("1d", "12h", "4h", "1h")
    block_epochs: int = 2
    epoch_size: int = 5
    max_hours: float | None = None
    min_sample_size: int = 20
    entry_lag_bars: int = 1
    cooldown_bars: int | None = None
    strict_referee: bool = True
    strict_null_iterations: int = 300
    strict_random_seed: int = 29
    checkpoint_interval: int = 5
    apply: bool = False
    resume: bool = False
    dry_run: bool = False
    source_root: Path = Path(".")
    report_root: Path = CEO_REPORT_ROOT
    lab_ops_report_root: Path = LAB_OPS_REPORT_ROOT
    lab_ops_runtime_root: Path = LAB_OPS_RUNTIME_ROOT
    max_new_hypotheses: int = 30


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_ceo_run_id(objective: str = "bullish-positive") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = "".join(ch if ch.isalnum() else "_" for ch in objective.lower()).strip("_")
    return f"ceo_{stamp}_{slug or 'riskflow'}"


def resolve_ceo_run_id(options: CeoOpsOptions) -> str:
    return options.run_id or make_ceo_run_id(options.objective)


def resolve_lab_run_id(options: CeoOpsOptions, ceo_run_id: str) -> str:
    return options.lab_run_id or f"{ceo_run_id}_lab"


def ceo_dir(options: CeoOpsOptions, ceo_run_id: str) -> Path:
    return options.report_root / ceo_run_id


def _latest_child(path: Path, pattern: str) -> Path | None:
    if not path.exists():
        return None
    matches = sorted(path.glob(pattern), key=lambda item: item.stat().st_mtime)
    return matches[-1] if matches else None


def _load_yaml_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = load_yaml_file(path)
    return payload if isinstance(payload, dict) else {}


def _lab_root(options: CeoOpsOptions, lab_run_id: str) -> Path:
    return options.lab_ops_report_root / lab_run_id


def _latest_governance_dir(options: CeoOpsOptions, lab_run_id: str) -> Path | None:
    return _latest_child(_lab_root(options, lab_run_id) / "governance", "block_*")


def _load_latest_governance(options: CeoOpsOptions, lab_run_id: str) -> dict[str, Any]:
    root = _latest_governance_dir(options, lab_run_id)
    if root is None:
        return {"paths": {}}
    return {
        "blocker_audit": _load_yaml_if_exists(root / "blocker_audit.yaml"),
        "lane_assignment": _load_yaml_if_exists(root / "lane_assignment.yaml"),
        "validation_governance": _load_yaml_if_exists(root / "validation_decision.yaml"),
        "research_map": _load_yaml_if_exists(root / "research_map.yaml"),
        "paths": {
            "root": root,
            "blocker_audit": root / "blocker_audit.yaml",
            "lane_assignment": root / "lane_assignment.yaml",
            "validation_governance": root / "validation_decision.yaml",
            "research_map": root / "research_map.yaml",
        },
    }


def _load_lab_status(options: CeoOpsOptions, lab_run_id: str) -> dict[str, Any]:
    return _load_yaml_if_exists(_lab_root(options, lab_run_id) / "latest_status.yaml")


def _load_lab_manifest(options: CeoOpsOptions, lab_run_id: str) -> dict[str, Any]:
    return _load_yaml_if_exists(_lab_root(options, lab_run_id) / "run_manifest.yaml")


def _next_block_number(options: CeoOpsOptions, ceo_run_id: str) -> int:
    root = ceo_dir(options, ceo_run_id)
    if not root.exists():
        return 1
    existing = sorted(root.glob("executive_decision_packet_*.md"))
    return len(existing) + 1


def build_ceo_manifest(options: CeoOpsOptions, ceo_run_id: str, lab_run_id: str) -> dict[str, Any]:
    return {
        "model": CEO_MANIFEST_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "objective": options.objective,
        "default_block_epochs": options.block_epochs,
        "default_epoch_size": options.epoch_size,
        "timeframes": list(options.timeframes),
        "strict_referee": options.strict_referee,
        "governed_lab_ops": True,
        "commit_policy": "never_auto_commit",
        "production_change_policy": "proposal_only",
        "production_effect": "none",
    }


def build_company_status(options: CeoOpsOptions, ceo_run_id: str, lab_run_id: str) -> dict[str, Any]:
    lab_status = _load_lab_status(options, lab_run_id)
    lab_manifest = _load_lab_manifest(options, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    lane_assignment = governance.get("lane_assignment", {})
    validation = governance.get("validation_governance", {})
    research_map = governance.get("research_map", {})
    stop_reason = str(lab_status.get("stop_reason") or lab_manifest.get("stop_reason") or "")
    open_lanes = list(lane_assignment.get("open_lanes", []) or lab_status.get("governance", {}).get("open_lanes", []) or [])
    true_blocker = stop_reason in TERMINAL_TRUE_BLOCKERS
    if stop_reason in {"request_fresh_data", "governed_recovery_no_supported_specs"} and open_lanes:
        true_blocker = False
    return {
        "model": CEO_COMPANY_STATUS_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "objective": options.objective,
        "lab_status": {
            "status": lab_status.get("status", lab_manifest.get("status", "unknown")),
            "stop_reason": stop_reason,
            "completed_epochs": lab_status.get("completed_epochs", lab_manifest.get("completed_epochs", 0)),
            "completed_blocks": lab_status.get("completed_blocks", lab_manifest.get("completed_blocks", 0)),
            "last_completed_loop": lab_status.get("last_completed_loop"),
            "latest_process_score": lab_status.get("latest_process_score"),
            "latest_intervention": lab_status.get("latest_intervention"),
        },
        "governance": {
            "open_lanes": open_lanes,
            "all_lanes_blocked": lane_assignment.get("all_lanes_blocked", lab_status.get("governance", {}).get("all_lanes_blocked")),
            "lane_counts": lane_assignment.get("lane_counts", {}),
            "validation_decision_counts": validation.get("decision_counts", {}),
            "product_change_allowed": bool(validation.get("product_change_allowed", False)),
        },
        "research_map": {
            "node_count": len(research_map.get("nodes", []) or []),
            "edge_count": len(research_map.get("edges", []) or []),
            "validation_debt": research_map.get("views", {}).get("validation_debt", []),
            "product_ready_candidates": research_map.get("views", {}).get("product_ready_candidates", []),
        },
        "true_blocker": true_blocker,
        "production_effect": "none",
    }


def build_product_delta_scoreboard(governance: dict[str, Any]) -> dict[str, Any]:
    lane_assignment = governance.get("lane_assignment", {})
    validation = governance.get("validation_governance", {})
    decisions_by_id = {str(item.get("belief_id", "")): item for item in validation.get("decisions", []) or []}
    candidates: list[dict[str, Any]] = []
    for assignment in lane_assignment.get("assignments", []) or []:
        lane = str(assignment.get("lane", ""))
        belief_id = str(assignment.get("belief_id", ""))
        decision = decisions_by_id.get(belief_id, {})
        if lane not in PRODUCT_LANES or decision.get("decision") == "archive":
            continue
        candidates.append(
            {
                "belief_id": belief_id,
                "product_role": lane,
                "current_gate": decision.get("current_gate", ""),
                "validation_decision": decision.get("decision", ""),
                "evidence_level": assignment.get("evidence_level"),
                "confidence_score": assignment.get("confidence_score"),
                "champion": "core_signal_v0",
                "challenger": f"core_signal_v0_plus_{belief_id}",
                "comparison_status": "needs_champion_challenger",
                "production_effect": "none",
            }
        )
    return {
        "model": CEO_PRODUCT_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "champion": "core_signal_v0",
        "candidate_count": len(candidates),
        "chart_facing_value_status": "candidate_pipeline" if candidates else "no_product_delta_yet",
        "candidates": candidates,
        "required_metrics": [
            "forward_relative_return_vs_basket",
            "hit_rate",
            "mfe_mae",
            "max_drawdown",
            "missed_upside_cost",
            "avoided_downside_benefit",
            "event_diversity",
            "lag_sensitivity",
            "cooldown_sensitivity",
        ],
        "production_effect": "none",
    }


def build_research_infra_delta(company_status: dict[str, Any], governance: dict[str, Any]) -> dict[str, Any]:
    lab_status = company_status.get("lab_status", {})
    artifacts_present = {
        "blocker_audit": bool(governance.get("blocker_audit")),
        "lane_assignment": bool(governance.get("lane_assignment")),
        "validation_governance": bool(governance.get("validation_governance")),
        "research_map": bool(governance.get("research_map")),
    }
    repeated_gap = lab_status.get("stop_reason") in {"no_runnable_and_no_valid_director_plan", "governed_recovery_no_supported_specs"}
    return {
        "model": CEO_INFRA_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "block_completed": bool(lab_status.get("completed_epochs", 0)),
        "governance_artifacts_present": artifacts_present,
        "process_score": lab_status.get("latest_process_score"),
        "latest_intervention": lab_status.get("latest_intervention"),
        "infra_delta_status": "needs_recovery_expansion" if repeated_gap else "observed",
        "recommended_infra_action": "expand_recursive_lane_recovery" if repeated_gap else "continue_bounded_ceo_blocks",
        "production_effect": "none",
    }


def build_understanding_delta(governance: dict[str, Any]) -> dict[str, Any]:
    research_map = governance.get("research_map", {})
    views = research_map.get("views", {}) or {}
    lane_assignment = governance.get("lane_assignment", {})
    validation = governance.get("validation_governance", {})
    return {
        "model": CEO_UNDERSTANDING_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "lane_counts": lane_assignment.get("lane_counts", {}),
        "open_lanes": lane_assignment.get("open_lanes", []),
        "validation_debt": views.get("validation_debt", []),
        "saturated_families": views.get("saturated_families", []),
        "top_open_questions": views.get("top_open_questions", []),
        "validation_decision_counts": validation.get("decision_counts", {}),
        "understanding_delta_status": "mapped" if research_map else "needs_research_map",
        "production_effect": "none",
    }


def build_risk_register(company_status: dict[str, Any], product_delta: dict[str, Any]) -> dict[str, Any]:
    lab_status = company_status.get("lab_status", {})
    risks: list[dict[str, Any]] = []
    if lab_status.get("completed_epochs", 0) and not product_delta.get("candidate_count"):
        risks.append(
            {
                "risk": "fake_progress",
                "severity": "high",
                "evidence": "research block completed without chart-facing candidate pipeline",
                "mitigation": "force champion/challenger or broaden product-role hypotheses",
            }
        )
    if lab_status.get("latest_intervention") == "request_fresh_data":
        risks.append(
            {
                "risk": "stale_or_insufficient_data",
                "severity": "medium",
                "evidence": "lab-meta requested fresh data",
                "mitigation": "import fresh TradingView data before promotion claims",
            }
        )
    if company_status.get("governance", {}).get("product_change_allowed"):
        risks.append(
            {
                "risk": "unexpected_product_change_permission",
                "severity": "critical",
                "evidence": "validation governance should not allow automatic product changes",
                "mitigation": "block production mutation and require user-approved promotion note",
            }
        )
    risks.append(
        {
            "risk": "production_mutation",
            "severity": "controlled",
            "evidence": "CEO mode keeps production_effect none",
            "mitigation": "promotion proposals only",
        }
    )
    return {
        "model": CEO_RISK_REGISTER_MODEL,
        "generated_at": utc_now_iso(),
        "risk_count": len(risks),
        "risks": risks,
        "production_effect": "none",
    }


def build_knowledge_graph_delta(governance: dict[str, Any]) -> dict[str, Any]:
    research_map = governance.get("research_map", {})
    views = research_map.get("views", {}) or {}
    candidates = list(views.get("product_ready_candidates", []) or [])
    validation_debt = list(views.get("validation_debt", []) or [])
    saturated = list(views.get("saturated_families", []) or [])
    return {
        "model": CEO_KNOWLEDGE_GRAPH_DELTA_MODEL,
        "generated_at": utc_now_iso(),
        "recommended_obsidian_summaries": [
            {"type": "product_candidate", "id": item, "reason": "candidate needs curated executive memory"}
            for item in candidates[:10]
        ]
        + [
            {"type": "validation_debt", "id": item, "reason": "open validation debt should be remembered"}
            for item in validation_debt[:10]
        ]
        + [
            {"type": "dead_branch", "id": item, "reason": "saturated family should not be blindly repeated"}
            for item in saturated[:10]
        ],
        "evidence_contract": [
            "run_id",
            "hypothesis_id",
            "variant_id",
            "source_csv_or_yaml",
            "evidence_level",
            "promotion_level",
            "product_role",
            "next_required_test",
        ],
        "production_effect": "none",
    }


def choose_executive_decision(
    company_status: dict[str, Any],
    product_delta: dict[str, Any],
    infra_delta: dict[str, Any],
) -> dict[str, Any]:
    lab_status = company_status.get("lab_status", {})
    open_lanes = company_status.get("governance", {}).get("open_lanes", [])
    stop_reason = str(lab_status.get("stop_reason", ""))
    if company_status.get("true_blocker"):
        decision = "stop_true_blocker"
        rationale = f"Lab stopped on true blocker: {stop_reason}"
    elif product_delta.get("candidate_count"):
        decision = "run_champion_challenger"
        rationale = "There are chart-facing candidates, but they need base-vs-challenger product-delta evidence."
    elif infra_delta.get("infra_delta_status") == "needs_recovery_expansion":
        decision = "patch_research_infra"
        rationale = "Open lanes remain, but recovery could not generate supported follow-ups."
    elif open_lanes:
        decision = "continue_governed_research"
        rationale = "Open governed lanes remain available for bounded CEO supervision."
    elif stop_reason == "request_fresh_data":
        decision = "request_fresh_data"
        rationale = "Evidence cannot advance without a fresher or broader data snapshot."
    else:
        decision = "broaden_hypothesis_source"
        rationale = "No chart-facing candidate or open lane was found; broaden sources before more brute force."
    return {
        "decision": decision,
        "rationale": rationale,
        "production_effect": "none",
    }


def _write_manifest(options: CeoOpsOptions, ceo_run_id: str, lab_run_id: str) -> Path:
    path = ceo_dir(options, ceo_run_id) / "ceo_manifest.yaml"
    atomic_write_yaml(path, build_ceo_manifest(options, ceo_run_id, lab_run_id))
    return path


def _write_artifact_set(
    options: CeoOpsOptions,
    ceo_run_id: str,
    *,
    block_number: int,
    company_status: dict[str, Any],
    product_delta: dict[str, Any],
    infra_delta: dict[str, Any],
    understanding_delta: dict[str, Any],
    risk_register: dict[str, Any],
    knowledge_graph_delta: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Path]:
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "company_status": root / "company_status.yaml",
        "product_delta": root / "product_delta_scoreboard.yaml",
        "infra_delta": root / "research_infra_delta.yaml",
        "understanding_delta": root / "understanding_delta.yaml",
        "risk_register": root / "risk_register.yaml",
        "knowledge_graph_delta": root / "knowledge_graph_delta.yaml",
        "decision_packet": root / f"executive_decision_packet_{block_number:04d}.md",
        "latest_decision_packet": root / "executive_decision_packet.md",
        "promotion_candidates": root / "promotion_candidates.md",
    }
    atomic_write_yaml(paths["company_status"], company_status)
    atomic_write_yaml(paths["product_delta"], product_delta)
    atomic_write_yaml(paths["infra_delta"], infra_delta)
    atomic_write_yaml(paths["understanding_delta"], understanding_delta)
    atomic_write_yaml(paths["risk_register"], risk_register)
    atomic_write_yaml(paths["knowledge_graph_delta"], knowledge_graph_delta)
    packet = render_executive_decision_packet(
        ceo_run_id=ceo_run_id,
        block_number=block_number,
        company_status=company_status,
        product_delta=product_delta,
        infra_delta=infra_delta,
        understanding_delta=understanding_delta,
        risk_register=risk_register,
        decision=decision,
    )
    atomic_write_text(paths["decision_packet"], packet)
    atomic_write_text(paths["latest_decision_packet"], packet)
    atomic_write_text(paths["promotion_candidates"], render_promotion_candidates(product_delta))
    return paths


def render_promotion_candidates(product_delta: dict[str, Any]) -> str:
    lines = [
        "# Riskflow Promotion Candidates",
        "",
        "Production changes are not allowed automatically. Items here are shadow candidates only.",
        "",
    ]
    candidates = product_delta.get("candidates", []) or []
    if not candidates:
        lines.append("- No chart-facing candidates identified yet.")
    for candidate in candidates:
        lines.append(
            "- "
            f"{candidate.get('belief_id')} "
            f"role={candidate.get('product_role')} "
            f"gate={candidate.get('current_gate')} "
            f"status={candidate.get('comparison_status')}"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_executive_decision_packet(
    *,
    ceo_run_id: str,
    block_number: int,
    company_status: dict[str, Any],
    product_delta: dict[str, Any],
    infra_delta: dict[str, Any],
    understanding_delta: dict[str, Any],
    risk_register: dict[str, Any],
    decision: dict[str, Any],
) -> str:
    lab_status = company_status.get("lab_status", {})
    governance = company_status.get("governance", {})
    lines = [
        "# Riskflow CEO Decision Packet",
        "",
        f"Run: {ceo_run_id}",
        f"Block: {block_number}",
        f"Generated: {utc_now_iso()}",
        "",
        "## Block Summary",
        "",
        f"- Objective: {company_status.get('objective')}",
        f"- Lab run: {company_status.get('lab_run_id')}",
        f"- Lab status: {lab_status.get('status')}",
        f"- Stop reason: {lab_status.get('stop_reason') or 'none'}",
        f"- Completed epochs: {lab_status.get('completed_epochs', 0)}",
        f"- Last completed loop: {lab_status.get('last_completed_loop')}",
        "",
        "## CEO Diagnosis",
        "",
        f"- Research infra: {infra_delta.get('infra_delta_status')}",
        f"- Understanding: {understanding_delta.get('understanding_delta_status')}",
        f"- Chart-facing value: {product_delta.get('chart_facing_value_status')}",
        f"- True blocker: {company_status.get('true_blocker')}",
        "",
        "## Evidence Review",
        "",
        f"- Open lanes: {', '.join(governance.get('open_lanes', []) or []) or 'none'}",
        f"- Lane counts: {governance.get('lane_counts', {})}",
        f"- Validation decisions: {governance.get('validation_decision_counts', {})}",
        f"- Validation debt: {understanding_delta.get('validation_debt', [])[:10]}",
        f"- Saturated families: {understanding_delta.get('saturated_families', [])[:10]}",
        "",
        "## Product Translation",
        "",
        f"- Champion: {product_delta.get('champion')}",
        f"- Candidate count: {product_delta.get('candidate_count')}",
        f"- Product-delta status: {product_delta.get('chart_facing_value_status')}",
        "- Production effect: none",
        "",
        "## Risk Register",
        "",
    ]
    for risk in risk_register.get("risks", []) or []:
        lines.append(f"- {risk.get('risk')}: {risk.get('severity')} - {risk.get('mitigation')}")
    lines.extend(
        [
            "",
            "## Executive Decision",
            "",
            f"- Decision: {decision.get('decision')}",
            f"- Rationale: {decision.get('rationale')}",
            "",
            "## Next Block Plan",
            "",
            _next_block_plan(decision),
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _next_block_plan(decision: dict[str, Any]) -> str:
    kind = decision.get("decision")
    if kind == "run_champion_challenger":
        return "Run product-delta champion/challenger tests for the listed shadow candidates before adding more infrastructure."
    if kind == "patch_research_infra":
        return "Patch recursive lane recovery or broaden recovery specs, run tests, then rerun one CEO block."
    if kind == "continue_governed_research":
        return "Run one more bounded governed CEO block and inspect the next decision packet."
    if kind == "request_fresh_data":
        return "Import or curate fresh OHLCV data before treating same-sample evidence as validation."
    if kind == "stop_true_blocker":
        return "Stop autonomous work and resolve the true blocker before continuing."
    return "Broaden the hypothesis source through Obsidian, visual review, web research, or agent critique."


def _lab_ops_options(options: CeoOpsOptions, lab_run_id: str) -> LabOpsOptions:
    return LabOpsOptions(
        objective=options.objective,
        run_id=lab_run_id,
        queue_path=options.queue_path,
        config_path=options.config_path,
        data_dir=options.data_dir,
        timeframes=options.timeframes,
        max_epochs=options.block_epochs,
        epoch_size=options.epoch_size,
        director_checkpoint_epochs=options.block_epochs,
        max_hours=options.max_hours,
        min_sample_size=options.min_sample_size,
        entry_lag_bars=options.entry_lag_bars,
        cooldown_bars=options.cooldown_bars,
        strict_referee=options.strict_referee,
        strict_null_iterations=options.strict_null_iterations,
        strict_random_seed=options.strict_random_seed,
        checkpoint_interval=options.checkpoint_interval,
        apply=options.apply,
        resume=options.resume,
        dry_run=options.dry_run,
        governed=True,
        source_root=options.source_root,
        report_root=options.lab_ops_report_root,
        runtime_root=options.lab_ops_runtime_root,
        max_new_hypotheses=options.max_new_hypotheses,
    )


def run_ceo_status(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    status = build_company_status(options, ceo_run_id, lab_run_id)
    if root.exists():
        atomic_write_yaml(root / "company_status.yaml", status)
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "company_status": status}


def run_ceo_plan(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = _write_manifest(options, ceo_run_id, lab_run_id)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    plan = {
        "model": "riskflow_ceo_plan_v0",
        "generated_at": utc_now_iso(),
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "objective": options.objective,
        "recommended_decision": decision,
        "next_command": (
            "PYTHONPATH=src python3 -m riskflow ceo run-block "
            f"--run-id {ceo_run_id} --objective {options.objective} --apply"
        ),
        "production_effect": "none",
    }
    plan_path = root / "ceo_plan.yaml"
    atomic_write_yaml(plan_path, plan)
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "plan": plan, "paths": {"manifest": manifest_path, "plan": plan_path}}


def run_ceo_run_block(options: CeoOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("ceo run-block requires --apply")
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    _write_manifest(options, ceo_run_id, lab_run_id)
    lab_result = run_lab_ops_run(_lab_ops_options(options, lab_run_id))
    review = run_ceo_review(options, ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "lab_result": lab_result, "review": review}


def run_ceo_review(
    options: CeoOpsOptions,
    *,
    ceo_run_id: str | None = None,
    lab_run_id: str | None = None,
) -> dict[str, Any]:
    ceo_run_id = ceo_run_id or resolve_ceo_run_id(options)
    lab_run_id = lab_run_id or resolve_lab_run_id(options, ceo_run_id)
    _write_manifest(options, ceo_run_id, lab_run_id)
    block_number = _next_block_number(options, ceo_run_id)
    company_status = build_company_status(options, ceo_run_id, lab_run_id)
    governance = _load_latest_governance(options, lab_run_id)
    product_delta = build_product_delta_scoreboard(governance)
    infra_delta = build_research_infra_delta(company_status, governance)
    understanding_delta = build_understanding_delta(governance)
    risk_register = build_risk_register(company_status, product_delta)
    knowledge_graph_delta = build_knowledge_graph_delta(governance)
    decision = choose_executive_decision(company_status, product_delta, infra_delta)
    paths = _write_artifact_set(
        options,
        ceo_run_id,
        block_number=block_number,
        company_status=company_status,
        product_delta=product_delta,
        infra_delta=infra_delta,
        understanding_delta=understanding_delta,
        risk_register=risk_register,
        knowledge_graph_delta=knowledge_graph_delta,
        decision=decision,
    )
    return {
        "run_id": ceo_run_id,
        "lab_run_id": lab_run_id,
        "block_number": block_number,
        "decision": decision,
        "paths": paths,
        "company_status": company_status,
        "product_delta": product_delta,
    }


def run_ceo_report(options: CeoOpsOptions) -> dict[str, Any]:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    root = ceo_dir(options, ceo_run_id)
    latest_packet = root / "executive_decision_packet.md"
    if not latest_packet.exists():
        review = run_ceo_review(options, ceo_run_id=ceo_run_id, lab_run_id=lab_run_id)
        latest_packet = review["paths"]["latest_decision_packet"]
    else:
        review = {
            "decision": {"decision": "see_latest_decision_packet", "rationale": "Report used existing CEO decision packet."},
            "paths": {"latest_decision_packet": latest_packet},
        }
    try:
        lab_report = run_lab_ops_report(_lab_ops_options(options, lab_run_id), run_id=lab_run_id)["paths"]["report"]
    except Exception:
        lab_report = None
    packet_path = latest_packet
    lines = [
        "# Riskflow CEO Final Report",
        "",
        f"Run: {ceo_run_id}",
        f"Lab run: {lab_run_id}",
        f"Generated: {utc_now_iso()}",
        "",
        "## Executive Decision",
        "",
        f"- Decision: {review['decision'].get('decision')}",
        f"- Rationale: {review['decision'].get('rationale')}",
        "",
        "## Reports",
        "",
        f"- CEO packet: {packet_path}",
    ]
    if lab_report:
        lines.append(f"- Lab report: {lab_report}")
    lines.extend(["", packet_path.read_text(encoding="utf-8") if packet_path.exists() else ""])
    report_path = root / "final_ceo_report.md"
    atomic_write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return {"run_id": ceo_run_id, "lab_run_id": lab_run_id, "paths": {"report": report_path, **review["paths"]}}


def run_ceo_lab_status_text(options: CeoOpsOptions) -> str:
    ceo_run_id = resolve_ceo_run_id(options)
    lab_run_id = resolve_lab_run_id(options, ceo_run_id)
    try:
        return run_lab_ops_status(_lab_ops_options(options, lab_run_id), run_id=lab_run_id)["status_text"]
    except Exception:
        return "No lab-ops status found."
