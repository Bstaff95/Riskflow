from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .lab_director import utc_now_iso
from .lab_loop import atomic_write_yaml, load_yaml_file


BLOCKER_AUDIT_MODEL = "riskflow_blocker_audit_v0"
BLOCKER_AUDIT_ITEM_MODEL = "riskflow_blocker_audit_item_v0"

BLOCKER_DECISIONS = {
    "valid_blocker",
    "permission_filter_only",
    "too_costly",
    "noise",
    "needs_more_controls",
    "not_a_blocker",
}


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _belief_text(belief: dict[str, Any]) -> str:
    values = [
        belief.get("claim_id", ""),
        belief.get("plain_english_claim", ""),
        belief.get("claim_kind", ""),
        belief.get("setup_class", ""),
        " ".join(str(item) for item in belief.get("known_failure_modes", []) or []),
        " ".join(str(item) for item in belief.get("suspected_drivers", []) or []),
    ]
    return " ".join(str(value) for value in values).lower()


def _rows_by_trial(mart: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in mart.get("rows", []) or []:
        trial_id = str(row.get("trial_id", ""))
        if trial_id:
            rows[trial_id] = row
    return rows


def _rows_by_setup(mart: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mart.get("rows", []) or []:
        grouped[str(row.get("setup_class", "") or "unknown")].append(row)
    return grouped


def _related_rows(belief: dict[str, Any], mart: dict[str, Any]) -> list[dict[str, Any]]:
    by_trial = _rows_by_trial(mart)
    rows: list[dict[str, Any]] = []
    for trial_id in list(belief.get("supporting_trials", []) or []) + list(belief.get("contradicting_trials", []) or []):
        row = by_trial.get(str(trial_id))
        if row:
            rows.append(row)
    if rows:
        return rows
    setup = str(belief.get("setup_class", "") or "")
    return _rows_by_setup(mart).get(setup, [])


def _is_blocker_like(belief: dict[str, Any], rows: list[dict[str, Any]]) -> bool:
    text = _belief_text(belief)
    if _contains_any(text, ("blocker", "warning", "bearish", "lower_high", "avoid", "invalidation", "false positive")):
        return True
    for row in rows:
        if row.get("contract_tier") == "blocker" or row.get("claim_type") == "warning_blocker":
            return True
    return False


def _has_controls(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        if row.get("claim_type") in {"control", "warning_blocker"}:
            return True
        if row.get("discovery_stage") in {"counterexample", "validation", "causal_decomposition"}:
            return True
        if "control" in str(row.get("hypothesis_id", "")).lower():
            return True
    return False


def _score_harm_avoided(rows: list[dict[str, Any]]) -> int:
    score = 0.0
    for row in rows:
        terminal = _as_float(row.get("median_forward_relative_return")) or 0.0
        drawdown = abs(_as_float(row.get("median_drawdown")) or 0.0)
        clusters = _as_int(row.get("event_clusters"))
        symbols = _as_int(row.get("unique_symbols"))
        if terminal < 0:
            score += min(abs(terminal) * 450, 35)
        if row.get("contract_tier") == "blocker" or row.get("claim_type") == "warning_blocker":
            score += 18
        score += min(drawdown * 150, 15)
        score += min(clusters, 12) * 0.7 + min(symbols, 12) * 0.5
    return int(round(max(0, min(100, score))))


def _score_missed_upside(rows: list[dict[str, Any]]) -> int:
    score = 0.0
    for row in rows:
        terminal = _as_float(row.get("median_forward_relative_return")) or 0.0
        hit_rate = _as_float(row.get("hit_rate")) or 0.0
        if terminal > 0:
            score += min(terminal * 420, 40)
        if hit_rate > 0.52:
            score += min((hit_rate - 0.52) * 100, 20)
        if row.get("contract_tier") in {"path_watchlist", "asymmetric_candidate", "strict_validated"}:
            score += 10
    return int(round(max(0, min(100, score))))


def audit_blocker_belief(belief: dict[str, Any], mart: dict[str, Any]) -> dict[str, Any]:
    rows = _related_rows(belief, mart)
    blocker_like = _is_blocker_like(belief, rows)
    controls_available = _has_controls(rows)
    harm_avoided = _score_harm_avoided(rows)
    missed_upside = _score_missed_upside(rows)
    best_timeframes = sorted({str(row.get("timeframe", "") or "mixed") for row in rows if row.get("timeframe")})
    row_refs = [str(row.get("trial_id", "")) for row in rows[:20] if row.get("trial_id")]

    if not blocker_like:
        decision = "not_a_blocker"
        blocker_type = "failed_setup_blocker" if belief.get("evidence_level") in {"rejected", "L1_seen"} else "not_blocker"
    elif not controls_available:
        decision = "needs_more_controls"
        blocker_type = "warning_blocker"
    elif harm_avoided >= 55 and harm_avoided >= missed_upside + 15:
        decision = "valid_blocker"
        blocker_type = "warning_blocker"
    elif missed_upside > harm_avoided + 10:
        decision = "too_costly"
        blocker_type = "permission_filter_only"
    elif harm_avoided >= 35:
        decision = "permission_filter_only"
        blocker_type = "permission_filter_only"
    else:
        decision = "noise"
        blocker_type = "failed_setup_blocker"

    return {
        "model": BLOCKER_AUDIT_ITEM_MODEL,
        "blocker_id": str(belief.get("claim_id", "")),
        "belief_id": str(belief.get("claim_id", "")),
        "blocker_type": blocker_type,
        "evidence_level": belief.get("evidence_level"),
        "harm_avoided_score": harm_avoided,
        "missed_upside_cost": missed_upside,
        "controls_available": controls_available,
        "conditional_context": {
            "setup_class": belief.get("setup_class"),
            "timeframes": best_timeframes,
            "row_count": len(rows),
        },
        "approved_product_role": "warning_blocker" if decision == "valid_blocker" else "none",
        "audit_decision": decision,
        "supporting_trials": row_refs,
        "rationale": _blocker_rationale(decision, harm_avoided, missed_upside, controls_available),
    }


def _blocker_rationale(decision: str, harm_avoided: int, missed_upside: int, controls_available: bool) -> str:
    if decision == "needs_more_controls":
        return "Blocker-like evidence exists, but blocker-active versus blocker-absent controls are not sufficient."
    if decision == "valid_blocker":
        return "Harm avoided is materially higher than missed-upside cost with controls available."
    if decision == "too_costly":
        return "The candidate blocks too much upside relative to the harm it avoids."
    if decision == "permission_filter_only":
        return "The evidence is useful as a permission filter but is not strong enough for blocker status."
    if decision == "not_a_blocker":
        return "The belief does not carry blocker, warning, invalidation, or avoidance evidence."
    if controls_available:
        return "Controls exist, but harm avoided is too weak for a blocker claim."
    return "Evidence is too weak or uncited for blocker use."


def build_blocker_audit(mart: dict[str, Any], belief_graph: dict[str, Any]) -> dict[str, Any]:
    items = [audit_blocker_belief(belief, mart) for belief in belief_graph.get("beliefs", []) or []]
    blocker_items = [
        item
        for item in items
        if item["audit_decision"] != "not_a_blocker"
        or item["blocker_type"] in {"warning_blocker", "permission_filter_only", "failed_setup_blocker"}
    ]
    decisions: dict[str, int] = defaultdict(int)
    for item in blocker_items:
        decisions[str(item["audit_decision"])] += 1
    return {
        "model": BLOCKER_AUDIT_MODEL,
        "generated_at": utc_now_iso(),
        "session_id": mart.get("session_id", belief_graph.get("session_id", "ad_hoc")),
        "belief_count": len(belief_graph.get("beliefs", []) or []),
        "audited_count": len(blocker_items),
        "decision_counts": dict(sorted(decisions.items())),
        "items": blocker_items,
        "production_effect": "none",
    }


def write_blocker_audit(audit: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "blocker_audit.yaml"
    atomic_write_yaml(path, audit)
    return path


def run_blocker_audit(
    *,
    evidence_mart_path: Path,
    belief_graph_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    mart = load_yaml_file(evidence_mart_path)
    belief_graph = load_yaml_file(belief_graph_path)
    audit = build_blocker_audit(mart, belief_graph)
    path = write_blocker_audit(audit, output_dir)
    return {"audit": audit, "paths": {"audit": path}}
