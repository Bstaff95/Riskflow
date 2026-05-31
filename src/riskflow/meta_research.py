from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .lab_director import LabDirectorOptions, run_director_inspect, run_director_plan_next, utc_now_iso
from .lab_loop import atomic_write_text, atomic_write_yaml, load_yaml_file


META_RESEARCH_MODEL = "riskflow_lab_meta_research_v0"
PROCESS_SCORECARD_MODEL = "riskflow_lab_process_scorecard_v0"
PROCESS_DIAGNOSIS_MODEL = "riskflow_lab_process_diagnosis_v0"
PROCESS_INTERVENTION_MODEL = "riskflow_lab_process_intervention_plan_v0"
META_AUDIT_MODEL = "riskflow_lab_meta_audit_v0"

DEFAULT_META_REPORT_ROOT = Path("reports/lab_meta")

PRODUCT_CATEGORIES = (
    "permission",
    "blocker",
    "reset_quality",
    "gradient_interpretation",
    "path_management",
    "cross_asset_usefulness",
    "archive",
)

VALID_INTERVENTIONS = {
    "continue_current_queue",
    "decompose_top_belief",
    "validate_frozen_rule",
    "broaden_idea_pool",
    "add_negative_controls",
    "stress_test_false_positives",
    "request_visual_review",
    "request_fresh_data",
    "archive_saturated_family",
    "process_policy_change",
    "stop_research_saturated",
}


@dataclass(frozen=True)
class LabMetaOptions:
    director_options: LabDirectorOptions = field(default_factory=LabDirectorOptions)
    meta_report_root: Path = DEFAULT_META_REPORT_ROOT
    snapshot_path: Path | None = None
    session_id: str | None = None


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> int:
    if not math.isfinite(value):
        return int(low)
    return int(round(max(low, min(high, value))))


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    number = _as_float(value)
    return int(number) if number is not None else 0


def _load_yaml_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_yaml_file(path)


def _latest_meta_scorecards(meta_report_root: Path, *, exclude_session: str | None = None) -> list[dict[str, Any]]:
    scorecards: list[dict[str, Any]] = []
    if not meta_report_root.exists():
        return scorecards
    for path in sorted(meta_report_root.glob("*/process_scorecard.yaml"), key=lambda item: item.stat().st_mtime):
        if exclude_session and path.parent.name == exclude_session:
            continue
        try:
            payload = load_yaml_file(path)
        except Exception:
            continue
        if isinstance(payload, dict):
            scorecards.append(payload)
    return scorecards[-5:]


def classify_product_categories(belief: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(value)
        for value in (
            belief.get("claim_kind", ""),
            belief.get("setup_class", ""),
            " ".join(str(item) for item in belief.get("suspected_drivers", [])),
            " ".join(str(item) for item in belief.get("known_failure_modes", [])),
            belief.get("plain_english_claim", ""),
        )
    ).lower()
    categories: set[str] = set()
    if belief.get("status") in {"archived", "rejected"} or belief.get("evidence_level") in {"rejected", "L1_seen"}:
        categories.add("archive")
    if any(token in text for token in ("blocker", "warning", "bearish", "lower_high", "avoid", "false positive")):
        categories.add("blocker")
    if any(token in text for token in ("permission", "filter", "fresh_leader", "failed_weakness", "regime")):
        categories.add("permission")
    if any(token in text for token in ("reset", "reclaim", "retest", "recent_signal_low", "deep")):
        categories.add("reset_quality")
    if any(token in text for token in ("gradient", "color", "viscosity", "slope", "acceleration", "curvature")):
        categories.add("gradient_interpretation")
    if any(token in text for token in ("path", "entry", "lag", "cooldown", "drawdown", "mfe", "mae")):
        categories.add("path_management")
    if len(belief.get("timeframes", []) or []) > 1 or len(belief.get("root_ids", []) or []) > 1:
        categories.add("cross_asset_usefulness")
    if not categories:
        categories.add("path_management")
    return sorted(categories)


def _category_scores(beliefs: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    row_symbols_by_setup: dict[str, int] = {}
    row_clusters_by_setup: dict[str, int] = {}
    for row in rows:
        setup = str(row.get("setup_class", ""))
        row_symbols_by_setup[setup] = max(row_symbols_by_setup.get(setup, 0), _as_int(row.get("unique_symbols")))
        row_clusters_by_setup[setup] = max(row_clusters_by_setup.get(setup, 0), _as_int(row.get("event_clusters")))

    result: dict[str, dict[str, Any]] = {
        category: {"belief_count": 0, "top_confidence": 0, "score": 0, "belief_ids": []}
        for category in PRODUCT_CATEGORIES
    }
    for belief in beliefs:
        categories = classify_product_categories(belief)
        confidence = _as_int(belief.get("confidence_score"))
        setup = str(belief.get("setup_class", ""))
        for category in categories:
            entry = result.setdefault(category, {"belief_count": 0, "top_confidence": 0, "score": 0, "belief_ids": []})
            entry["belief_count"] += 1
            entry["top_confidence"] = max(_as_int(entry.get("top_confidence")), confidence)
            entry["belief_ids"].append(str(belief.get("claim_id", "")))
            diversity_bonus = min(row_symbols_by_setup.get(setup, 0), 20) + min(row_clusters_by_setup.get(setup, 0), 20)
            entry["score"] = max(_as_int(entry.get("score")), _clamp(confidence + diversity_bonus * 0.75))
    return result


def _dominance_penalty(counter: Counter[str], row_count: int) -> int:
    if row_count < 3 or not counter:
        return 0
    dominant_share = max(counter.values()) / row_count
    duplicate_share = sum(count for count in counter.values() if count > 1) / row_count
    return _clamp((dominant_share - 0.35) * 120 + duplicate_share * 35)


def _source_refs(mart: dict[str, Any], plan: dict[str, Any] | None, audit: dict[str, Any] | None) -> list[str]:
    refs: list[str] = []
    for key, value in (mart.get("inputs") or {}).items():
        if value:
            refs.append(f"{key}:{value}")
    for row in mart.get("rows", [])[:20]:
        for field in ("bullish_evidence_path", "source_report_dir", "source_grid_path"):
            value = str(row.get(field, "") or "")
            if value:
                refs.append(value)
    if plan:
        refs.append("next_experiment_plan")
        for experiment in plan.get("experiments", [])[:10]:
            value = str(experiment.get("generated_grid_path", "") or "")
            if value:
                refs.append(value)
    if audit:
        refs.append("director_audit")
    seen: set[str] = set()
    deduped: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            deduped.append(ref)
    return deduped[:40]


def build_process_scorecard(
    mart: dict[str, Any],
    belief_graph: dict[str, Any],
    *,
    plan: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
    prior_scorecards: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = list(mart.get("rows", []) or [])
    beliefs = list(belief_graph.get("beliefs", []) or [])
    row_count = len(rows)
    belief_count = len(beliefs)
    root_counts = Counter(str(row.get("root_id", "") or "unknown") for row in rows)
    setup_counts = Counter(str(row.get("setup_class", "") or "unknown") for row in rows)
    source_counts = Counter(str(row.get("source_grid_path", "") or "unknown") for row in rows)
    timeframe_counts = Counter(str(row.get("timeframe", "") or "mixed") for row in rows)
    stage_counts = Counter(str(row.get("discovery_stage", "") or "discovery") for row in rows)
    tiers = Counter(str(row.get("contract_tier", "") or "unknown") for row in rows)

    useful_rows = sum(1 for row in rows if row.get("contract_tier") in {"path_watchlist", "asymmetric_candidate", "strict_validated"})
    strict_rows = sum(1 for row in rows if row.get("contract_tier") == "strict_validated")
    blocker_rows = sum(1 for row in rows if row.get("contract_tier") == "blocker" or row.get("claim_type") == "warning_blocker")
    validation_rows = sum(
        1
        for row in rows
        if row.get("discovery_stage") == "validation" or row.get("contract_tier") == "strict_validated" or row.get("time_split_pass")
    )
    decomposition_rows = sum(1 for row in rows if row.get("discovery_stage") == "causal_decomposition")
    control_rows = sum(1 for row in rows if row.get("claim_type") in {"control", "warning_blocker"} or row.get("discovery_stage") in {"counterexample", "validation"})
    promising_beliefs = [belief for belief in beliefs if belief.get("evidence_level") in {"L2_discovered", "L3_attributed"}]
    attributed_beliefs = [belief for belief in beliefs if belief.get("evidence_level") == "L3_attributed"]
    top_confidence = max((_as_int(belief.get("confidence_score")) for belief in beliefs), default=0)

    unique_roots = len(root_counts)
    unique_setups = len(setup_counts)
    unique_timeframes = len(timeframe_counts)
    unique_stages = len(stage_counts)
    unique_sources = len(source_counts)
    novelty_score = _clamp(unique_roots * 5 + unique_setups * 12 + unique_timeframes * 8 + unique_stages * 10 + min(unique_sources, 20) * 1.5)
    evidence_gain_score = _clamp(useful_rows * 10 + strict_rows * 20 + blocker_rows * 6 + min(row_count, 50) * 1.2)
    belief_delta_score = _clamp(len(promising_beliefs) * 18 + len(attributed_beliefs) * 18 + top_confidence * 0.45)
    validation_progress_score = _clamp(validation_rows * 18 + strict_rows * 22 + decomposition_rows * 9 + control_rows * 5)
    decomposition_score = _clamp(decomposition_rows * 18 + sum(1 for belief in promising_beliefs if belief.get("next_required_tests")) * 8)

    category_scores = _category_scores(beliefs, rows)
    non_archive_categories = [
        category for category, payload in category_scores.items() if category != "archive" and _as_int(payload.get("belief_count")) > 0
    ]
    product_relevance_score = _clamp(sum(_as_int(payload.get("score")) for payload in category_scores.values()) / max(1, len(PRODUCT_CATEGORIES)))
    category_coverage_score = _clamp(len(non_archive_categories) / max(1, len(PRODUCT_CATEGORIES) - 1) * 100)

    redundancy_penalty = max(
        _dominance_penalty(root_counts, row_count),
        _dominance_penalty(setup_counts, row_count),
        _dominance_penalty(source_counts, row_count),
    )
    sample_reuse_penalty = max(_dominance_penalty(source_counts, row_count), _dominance_penalty(timeframe_counts, row_count))
    multiplicity_pressure = _clamp(row_count * 1.7 + max(root_counts.values(), default=0) * 5 + max(setup_counts.values(), default=0) * 4)
    low_symbol_rows = sum(1 for row in rows if 0 < _as_int(row.get("unique_symbols")) < 8)
    low_cluster_rows = sum(1 for row in rows if 0 < _as_int(row.get("event_clusters")) < 8)
    no_controls_penalty = 35 if row_count and control_rows == 0 else 0
    overfit_risk = _clamp(low_symbol_rows * 8 + low_cluster_rows * 8 + sample_reuse_penalty * 0.6 + multiplicity_pressure * 0.25 + no_controls_penalty)
    goodhart_risk_score = _clamp(max(0, novelty_score - validation_progress_score) * 0.55 + redundancy_penalty * 0.30 + sample_reuse_penalty * 0.25)
    audit_health_score = 100 if audit is None or audit.get("passed") else 20
    queue_items = len(((plan or {}).get("generated_queue") or {}).get("queue", []) or [])
    plan_stop_reason = str((plan or {}).get("stop_reason", "") or "")
    queue_health_score = _clamp(queue_items * 8 + (20 if plan and not plan_stop_reason else 0))
    next_action_quality = _clamp(queue_health_score * 0.45 + decomposition_score * 0.20 + validation_progress_score * 0.20 + product_relevance_score * 0.15)

    positive = (
        evidence_gain_score * 0.18
        + belief_delta_score * 0.18
        + validation_progress_score * 0.18
        + decomposition_score * 0.12
        + product_relevance_score * 0.14
        + novelty_score * 0.08
        + category_coverage_score * 0.05
        + next_action_quality * 0.07
    )
    penalties = redundancy_penalty * 0.12 + sample_reuse_penalty * 0.08 + overfit_risk * 0.10 + goodhart_risk_score * 0.08
    overall = _clamp(positive - penalties)
    if row_count and validation_progress_score == 0:
        overall = min(overall, 65)
    if sample_reuse_penalty > 70:
        overall = min(overall, 75)
    if row_count and control_rows == 0:
        overall = min(overall, 80)
    if audit is not None and not audit.get("passed"):
        overall = min(overall, 40)
    if plan and not queue_items and not plan_stop_reason:
        overall = min(overall, 30)

    prior_scorecards = prior_scorecards or []
    recent_repeated_failures = Counter(
        failure
        for scorecard in prior_scorecards[-3:]
        for failure in scorecard.get("process_failures", [])
        if isinstance(failure, str)
    )

    scorecard: dict[str, Any] = {
        "model": PROCESS_SCORECARD_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": mart.get("session_id", "ad_hoc"),
        "row_count": row_count,
        "belief_count": belief_count,
        "scores": {
            "novelty": novelty_score,
            "evidence_gain": evidence_gain_score,
            "belief_delta": belief_delta_score,
            "validation_progress": validation_progress_score,
            "decomposition": decomposition_score,
            "product_relevance": product_relevance_score,
            "category_coverage": category_coverage_score,
            "audit_health": audit_health_score,
            "queue_health": queue_health_score,
            "next_action_quality": next_action_quality,
        },
        "penalties": {
            "redundancy": redundancy_penalty,
            "sample_reuse": sample_reuse_penalty,
            "multiplicity_pressure": multiplicity_pressure,
            "overfit_risk": overfit_risk,
            "goodhart_risk": goodhart_risk_score,
        },
        "hard_caps": {
            "no_validation_stage_cap": row_count > 0 and validation_progress_score == 0,
            "same_sample_reuse_cap": sample_reuse_penalty > 70,
            "no_negative_or_control_tests_cap": row_count > 0 and control_rows == 0,
            "audit_failure_cap": audit is not None and not audit.get("passed"),
        },
        "overall_process_score": overall,
        "category_scores": category_scores,
        "inventory": {
            "unique_roots": unique_roots,
            "unique_setup_classes": unique_setups,
            "unique_timeframes": unique_timeframes,
            "unique_sources": unique_sources,
            "stage_counts": dict(stage_counts),
            "contract_tier_counts": dict(tiers),
            "queue_items": queue_items,
            "plan_stop_reason": plan_stop_reason,
        },
        "top_beliefs": [
            {
                "claim_id": belief.get("claim_id"),
                "evidence_level": belief.get("evidence_level"),
                "confidence_score": belief.get("confidence_score"),
                "categories": classify_product_categories(belief),
                "next_required_tests": belief.get("next_required_tests", []),
            }
            for belief in beliefs[:8]
        ],
        "score_explanations": {
            "novelty": "Counts distinct roots, setup classes, timeframes, stages, and source grids.",
            "evidence_gain": "Rewards useful, strict, blocker, and non-empty evidence rows.",
            "belief_delta": "Rewards promising or attributed beliefs with cited confidence.",
            "validation_progress": "Rewards validation, strict survivors, decomposition, controls, and counterexamples.",
            "penalties": "Penalizes repeated roots/sources/timeframes, low diversity, multiplicity pressure, and Goodhart risk.",
        },
        "supporting_artifacts": _source_refs(mart, plan, audit),
        "recent_repeated_failures": dict(recent_repeated_failures),
    }
    scorecard["process_failures"] = diagnose_process_failure(scorecard).get("failure_modes", [])
    return scorecard


def diagnose_process_failure(scorecard: dict[str, Any]) -> dict[str, Any]:
    scores = scorecard.get("scores", {})
    penalties = scorecard.get("penalties", {})
    inventory = scorecard.get("inventory", {})
    failures: list[str] = []
    warnings: list[str] = []

    if _as_int(scores.get("novelty")) < 25 and scorecard.get("row_count", 0):
        failures.append("duplicate_research")
    if _as_int(penalties.get("sample_reuse")) > 65:
        failures.append("same_sample_overfit")
    if _as_int(scores.get("belief_delta")) < 20 and scorecard.get("row_count", 0):
        failures.append("no_belief_delta")
    if _as_int(scores.get("validation_progress")) < 25 and scorecard.get("top_beliefs"):
        failures.append("weak_validation_progress")
    if _as_int(inventory.get("queue_items")) == 0 and inventory.get("plan_stop_reason"):
        failures.append("queue_exhausted")
    if inventory.get("plan_stop_reason") == "missing_source_grids_for_promising_beliefs":
        failures.append("missing_source_grids")
    if _as_int(penalties.get("redundancy")) > 70:
        failures.append("over_concentrated_root")
    if _as_int(scores.get("product_relevance")) < 25 and scorecard.get("belief_count", 0):
        failures.append("product_role_unclear")
    if _as_int(scores.get("audit_health")) < 60:
        failures.append("audit_regression")
    if _as_int(penalties.get("overfit_risk")) > 70:
        failures.append("data_stale_or_insufficient")
    if _as_int(penalties.get("goodhart_risk")) > 65:
        failures.append("goodhart_risk")
    if (
        "queue_exhausted" in failures
        and "no_belief_delta" in failures
        and _as_int(scores.get("novelty")) < 25
    ):
        failures.append("research_saturated")
    if _as_int(scores.get("category_coverage")) < 35 and scorecard.get("belief_count", 0):
        warnings.append("category_blind_spot")
    if scorecard.get("hard_caps", {}).get("no_negative_or_control_tests_cap"):
        warnings.append("negative_controls_missing")

    return {
        "model": PROCESS_DIAGNOSIS_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": scorecard.get("session_id", "ad_hoc"),
        "failure_modes": sorted(set(failures)),
        "warnings": sorted(set(warnings)),
    }


def choose_process_intervention(
    scorecard: dict[str, Any],
    diagnosis: dict[str, Any],
    belief_graph: dict[str, Any],
    *,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    failures = set(diagnosis.get("failure_modes", []))
    warnings = set(diagnosis.get("warnings", []))
    top_beliefs = list(belief_graph.get("beliefs", []) or [])
    promising = [
        belief
        for belief in top_beliefs
        if belief.get("evidence_level") in {"L2_discovered", "L3_attributed"}
        and belief.get("status") == "promising_unvalidated"
    ]
    top = promising[0] if promising else (top_beliefs[0] if top_beliefs else {})
    intervention_type = "continue_current_queue"
    rationale = "The latest scorecard shows usable learning and an audited queue is available."
    queue_requirements = ["preserve current audited queue"]

    if "audit_regression" in failures:
        intervention_type = "process_policy_change"
        rationale = "Director or meta audit failed; do not apply queue changes until the policy is fixed."
        queue_requirements = ["do not apply generated queue", "write engineering recommendation"]
    elif "research_saturated" in failures:
        intervention_type = "stop_research_saturated"
        rationale = "Recent work is exhausted, low novelty, and low belief-delta; stop instead of reseeding blindly."
        queue_requirements = ["no new queue until fresh data or new curated idea pool exists"]
    elif "missing_source_grids" in failures:
        intervention_type = "request_fresh_data"
        rationale = "Promising beliefs cannot be decomposed because their source grids are missing."
        queue_requirements = ["recover source grids or import fresh/curated source hypotheses"]
    elif "same_sample_overfit" in failures or _as_int(scorecard.get("penalties", {}).get("overfit_risk")) > 70:
        intervention_type = "add_negative_controls"
        rationale = "Current evidence has high reuse or overfit risk; freeze tuning and falsify the claim."
        queue_requirements = ["direction flip", "trigger-only control", "setup-only control", "fresh or withheld split"]
    elif top and top.get("evidence_level") == "L3_attributed":
        intervention_type = "validate_frozen_rule"
        rationale = f"{top.get('claim_id')} has attribution-level evidence and should be validated without more tuning."
        queue_requirements = ["fresh split validation", "entry-lag sensitivity", "cooldown sensitivity"]
    elif top and top.get("evidence_level") == "L2_discovered":
        intervention_type = "decompose_top_belief"
        rationale = f"{top.get('claim_id')} is promising but still needs causal decomposition."
        queue_requirements = list(top.get("next_required_tests", []) or ["ablation controls"])
    elif "duplicate_research" in failures or "no_belief_delta" in failures or "category_blind_spot" in warnings:
        intervention_type = "broaden_idea_pool"
        rationale = "The lab is not moving beliefs enough; broaden roots, categories, or grammar families."
        queue_requirements = ["new roots", "new setup classes", "under-tested product categories"]
    elif "queue_exhausted" in failures:
        intervention_type = "broaden_idea_pool"
        rationale = "The queue is exhausted without a stronger target belief; broaden rather than repeat variants."
        queue_requirements = ["new non-duplicate hypotheses", "artifact-cited rationale"]
    elif scorecard.get("inventory", {}).get("queue_items", 0) == 0:
        intervention_type = "stop_research_saturated"
        rationale = "No audited queue items are available."
        queue_requirements = ["stop with explicit reason"]

    target_beliefs = [str(top.get("claim_id"))] if top else []
    intervention = {
        "model": PROCESS_INTERVENTION_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": scorecard.get("session_id", "ad_hoc"),
        "intervention_type": intervention_type,
        "rationale": rationale,
        "target_belief_ids": target_beliefs,
        "blocked_belief_ids": [
            str(belief.get("claim_id"))
            for belief in top_beliefs
            if belief.get("status") in {"archived", "rejected"}
        ][:12],
        "policy_adjustments": _policy_adjustments_for_intervention(intervention_type),
        "queue_requirements": queue_requirements,
        "acceptance_checks": _acceptance_checks_for_intervention(intervention_type),
        "rejected_alternatives": _rejected_alternatives(intervention_type, failures),
        "production_effect": "none",
        "supporting_artifacts": scorecard.get("supporting_artifacts", []),
        "plan_context": {
            "director_research_mode": (plan or {}).get("research_mode"),
            "director_stop_reason": (plan or {}).get("stop_reason"),
            "director_queue_items": scorecard.get("inventory", {}).get("queue_items", 0),
        },
    }
    return intervention


def _policy_adjustments_for_intervention(intervention_type: str) -> list[str]:
    mapping = {
        "decompose_top_belief": ["prioritize attribution grids", "cap same-root discovery refinements"],
        "validate_frozen_rule": ["freeze parameter shape", "use validation/fresh split stages only"],
        "broaden_idea_pool": ["cool saturated roots", "reserve slots for under-tested categories"],
        "add_negative_controls": ["require falsification controls before new refinements"],
        "stress_test_false_positives": ["pair permission tests with blocker-present controls"],
        "request_visual_review": ["write chart-review queue before more automation"],
        "request_fresh_data": ["stop promotion pressure until source data/grid gap is resolved"],
        "archive_saturated_family": ["block duplicate signatures from the next queue"],
        "process_policy_change": ["write engineering proposal; do not auto-edit source"],
        "stop_research_saturated": ["stop long run with explicit saturation reason"],
    }
    return mapping.get(intervention_type, ["continue current audited research queue"])


def _acceptance_checks_for_intervention(intervention_type: str) -> list[str]:
    base = ["all generated queue items keep production_effect none", "all claims cite evidence artifacts"]
    mapping = {
        "decompose_top_belief": ["at least one ablation or control directly targets top belief drivers"],
        "validate_frozen_rule": ["no parameter expansion after freezing", "validation uses split/fresh or lag/cooldown stress"],
        "broaden_idea_pool": ["new queue avoids recent do-not-repeat signatures"],
        "add_negative_controls": ["controls include setup-only, trigger-only, or direction-flip tests"],
        "request_fresh_data": ["no promotion until missing source/data reason is resolved"],
        "process_policy_change": ["source-code change requires repeated process failure and tests"],
        "stop_research_saturated": ["final report includes why automation should stop"],
    }
    return base + mapping.get(intervention_type, ["next checkpoint improves evidence or belief delta"])


def _rejected_alternatives(intervention_type: str, failures: set[str]) -> list[str]:
    rejected: list[str] = []
    if intervention_type != "continue_current_queue" and failures:
        rejected.append("continue_current_queue rejected because process failures were detected")
    if intervention_type != "validate_frozen_rule":
        rejected.append("validate_frozen_rule deferred until attribution/frozen-rule evidence is adequate")
    if intervention_type != "process_policy_change":
        rejected.append("process_policy_change deferred because queue/policy intervention is sufficient")
    return rejected


def audit_process_intervention(intervention: dict[str, Any], *, source_root: Path = Path(".")) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    intervention_type = str(intervention.get("intervention_type", ""))
    if intervention.get("model") != PROCESS_INTERVENTION_MODEL:
        errors.append("intervention model is invalid")
    if intervention_type not in VALID_INTERVENTIONS:
        errors.append(f"intervention_type is invalid: {intervention_type}")
    if intervention.get("production_effect") not in {None, "none"}:
        errors.append("production_effect must remain none")
    if not str(intervention.get("rationale", "")).strip():
        errors.append("rationale is required")
    if not isinstance(intervention.get("queue_requirements"), list) or not intervention.get("queue_requirements"):
        errors.append("queue_requirements must be a non-empty list")
    refs = intervention.get("supporting_artifacts", [])
    if not isinstance(refs, list):
        errors.append("supporting_artifacts must be a list")
    elif not refs and intervention_type not in {"request_fresh_data", "stop_research_saturated"}:
        warnings.append("intervention has no supporting artifact references")
    for field in ("policy_adjustments", "acceptance_checks"):
        if not isinstance(intervention.get(field), list):
            errors.append(f"{field} must be a list")
    return {
        "model": META_AUDIT_MODEL,
        "generated_at": utc_now_iso(),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "production_effect": "none",
        "source_root": str(source_root),
    }


def write_meta_report(
    output_dir: Path,
    *,
    scorecard: dict[str, Any],
    diagnosis: dict[str, Any],
    intervention: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
) -> Path:
    lines = [
        "# Riskflow Meta-Research Report",
        "",
        f"Generated: {utc_now_iso()}",
        f"Session: {scorecard.get('session_id', 'ad_hoc')}",
        f"Process score: {scorecard.get('overall_process_score')}/100",
        f"Evidence rows: {scorecard.get('row_count', 0)}",
        f"Beliefs: {scorecard.get('belief_count', 0)}",
        "",
        "## How Well Did The Lab Learn?",
        "",
    ]
    for key, value in scorecard.get("scores", {}).items():
        lines.append(f"- {key}: {value}")
    for key, value in scorecard.get("penalties", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Product Categories", ""])
    for category, payload in scorecard.get("category_scores", {}).items():
        lines.append(
            f"- {category}: score={payload.get('score')} beliefs={payload.get('belief_count')} "
            f"top_confidence={payload.get('top_confidence')}"
        )
    lines.extend(["", "## Diagnosis", ""])
    failures = diagnosis.get("failure_modes", [])
    warnings = diagnosis.get("warnings", [])
    lines.append(f"- Failure modes: {', '.join(failures) if failures else 'none'}")
    lines.append(f"- Warnings: {', '.join(warnings) if warnings else 'none'}")
    if intervention:
        lines.extend(
            [
                "",
                "## Recommended Intervention",
                "",
                f"- Type: {intervention.get('intervention_type')}",
                f"- Rationale: {intervention.get('rationale')}",
                f"- Target beliefs: {', '.join(intervention.get('target_belief_ids', [])) or 'none'}",
            ]
        )
        for requirement in intervention.get("queue_requirements", []):
            lines.append(f"- Queue requirement: {requirement}")
    if audit:
        lines.extend(["", "## Meta Audit", "", f"- Passed: {audit.get('passed')}"])
        for error in audit.get("errors", []):
            lines.append(f"- Error: {error}")
        for warning in audit.get("warnings", []):
            lines.append(f"- Warning: {warning}")
    path = output_dir / "meta_research_report.md"
    atomic_write_text(path, "\n".join(lines) + "\n")
    return path


def _meta_output_dir(options: LabMetaOptions, session_id: str) -> Path:
    return options.meta_report_root / (options.session_id or session_id or "ad_hoc")


def _write_meta_artifacts(
    options: LabMetaOptions,
    *,
    scorecard: dict[str, Any],
    diagnosis: dict[str, Any],
    intervention: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
) -> dict[str, Path]:
    output_dir = _meta_output_dir(options, str(scorecard.get("session_id", "ad_hoc")))
    output_dir.mkdir(parents=True, exist_ok=True)
    scorecard_path = output_dir / "process_scorecard.yaml"
    diagnosis_path = output_dir / "process_diagnosis.yaml"
    atomic_write_yaml(scorecard_path, scorecard)
    atomic_write_yaml(diagnosis_path, diagnosis)
    paths = {
        "output_dir": output_dir,
        "scorecard": scorecard_path,
        "diagnosis": diagnosis_path,
    }
    if intervention is not None:
        intervention_path = output_dir / "process_intervention_plan.yaml"
        atomic_write_yaml(intervention_path, intervention)
        paths["intervention"] = intervention_path
    if audit is not None:
        audit_path = output_dir / "meta_audit.yaml"
        atomic_write_yaml(audit_path, audit)
        paths["audit"] = audit_path
    report_path = write_meta_report(output_dir, scorecard=scorecard, diagnosis=diagnosis, intervention=intervention, audit=audit)
    paths["report"] = report_path
    return paths


def _load_snapshot(snapshot_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    root = snapshot_path
    if root.is_file():
        root = root.parent
    mart = _load_yaml_if_exists(root / "evidence_mart.yaml")
    belief_graph = _load_yaml_if_exists(root / "belief_graph.yaml")
    plan = _load_yaml_if_exists(root / "next_experiment_plan.yaml")
    audit = _load_yaml_if_exists(root / "director_audit.yaml")
    if not mart or not belief_graph:
        raise ValueError(f"Snapshot must contain evidence_mart.yaml and belief_graph.yaml: {snapshot_path}")
    return mart, belief_graph, plan or None, audit or None


def run_meta_from_director_result(
    options: LabMetaOptions,
    director_result: dict[str, Any],
    *,
    include_intervention: bool,
) -> dict[str, Any]:
    mart = director_result["mart"]
    belief_graph = director_result["belief_graph"]
    plan = director_result.get("plan")
    director_audit = director_result.get("audit")
    prior = _latest_meta_scorecards(options.meta_report_root, exclude_session=str(mart.get("session_id", "")))
    scorecard = build_process_scorecard(mart, belief_graph, plan=plan, audit=director_audit, prior_scorecards=prior)
    diagnosis = diagnose_process_failure(scorecard)
    intervention = choose_process_intervention(scorecard, diagnosis, belief_graph, plan=plan) if include_intervention else None
    audit = audit_process_intervention(intervention, source_root=options.director_options.source_root) if intervention else None
    paths = _write_meta_artifacts(
        options,
        scorecard=scorecard,
        diagnosis=diagnosis,
        intervention=intervention,
        audit=audit,
    )
    return {
        "scorecard": scorecard,
        "diagnosis": diagnosis,
        "intervention": intervention,
        "audit": audit,
        "paths": paths,
    }


def run_lab_meta_inspect(options: LabMetaOptions) -> dict[str, Any]:
    if options.snapshot_path:
        mart, belief_graph, plan, director_audit = _load_snapshot(options.snapshot_path)
        director_result = {"mart": mart, "belief_graph": belief_graph, "plan": plan, "audit": director_audit}
    else:
        director_result = run_director_inspect(options.director_options)
    return run_meta_from_director_result(options, director_result, include_intervention=False)


def run_lab_meta_plan(options: LabMetaOptions) -> dict[str, Any]:
    if options.snapshot_path:
        mart, belief_graph, plan, director_audit = _load_snapshot(options.snapshot_path)
        director_result = {"mart": mart, "belief_graph": belief_graph, "plan": plan, "audit": director_audit}
    else:
        director_result = run_director_plan_next(options.director_options)
    return run_meta_from_director_result(options, director_result, include_intervention=True)


def read_latest_meta_status(meta_report_root: Path = DEFAULT_META_REPORT_ROOT) -> str:
    paths = sorted(meta_report_root.glob("*/process_scorecard.yaml"), key=lambda item: item.stat().st_mtime)
    if not paths:
        return "No lab-meta scorecard found."
    scorecard = yaml.safe_load(paths[-1].read_text(encoding="utf-8")) or {}
    intervention_path = paths[-1].parent / "process_intervention_plan.yaml"
    intervention = yaml.safe_load(intervention_path.read_text(encoding="utf-8")) if intervention_path.exists() else {}
    return "\n".join(
        [
            f"Session: {scorecard.get('session_id', paths[-1].parent.name)}",
            f"Process score: {scorecard.get('overall_process_score')}/100",
            f"Rows: {scorecard.get('row_count')} Beliefs: {scorecard.get('belief_count')}",
            f"Failures: {', '.join(scorecard.get('process_failures', [])) or 'none'}",
            f"Intervention: {intervention.get('intervention_type', 'not_planned')}",
            f"Report: {paths[-1].parent / 'meta_research_report.md'}",
        ]
    )


def write_process_scorecard_json(path: Path, scorecard: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scorecard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
