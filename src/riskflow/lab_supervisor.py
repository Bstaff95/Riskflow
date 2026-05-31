from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .lab_loop import (
    BULLISH_POSITIVE_OBJECTIVE,
    TERMINAL_STATUSES,
    LabLoopOptions,
    atomic_write_json,
    atomic_write_text,
    atomic_write_yaml,
    build_refinement_grid,
    canonical_hypothesis_root,
    is_executable_hypothesis,
    lineage_fingerprint,
    load_lab_queue,
    load_lab_state,
    load_yaml_file,
    root_hypothesis_id,
    run_lab_epoch,
    strict_survivor_rows,
    utc_now_iso,
    useful_rows,
)


SUPERVISOR_MODEL = "riskflow_lab_meta_supervisor_v0"
DEFAULT_EVIDENCE_LEDGER_PATH = Path("research/lab_loop/evidence_ledger.yaml")
DEFAULT_SUPERVISOR_POLICY_PATH = Path("research/lab_loop/supervisor_policy.yaml")


@dataclass(frozen=True)
class SupervisorOptions:
    state_path: Path = Path("research/lab_loop/lab_state.json")
    runtime_queue_path: Path = Path("research/lab_loop/runtime_queue.yaml")
    concept_scoreboard_path: Path = Path("research/lab_loop/concept_scoreboard.yaml")
    evidence_ledger_path: Path = DEFAULT_EVIDENCE_LEDGER_PATH
    policy_path: Path = DEFAULT_SUPERVISOR_POLICY_PATH
    epoch_size: int = 5
    apply: bool = True
    max_generation: int = 3
    max_same_root_per_epoch: int = 2
    min_bullish_share: float = 0.35
    validation_share: float = 0.30
    min_new_bullish_roots: int = 3
    max_same_setup_class_per_epoch: int = 1
    weak_family_attempt_limit: int = 3
    weak_family_cooldown_loops: int = 25
    max_non_contract_reseed_source_generation: int = 0
    max_primitive_overlap: float = 0.70
    reseed_when_empty: bool = True
    max_reseed_per_epoch: int = 5
    max_reseeds_per_root: int = 2
    max_reseed_signature_attempts: int = 1
    generated_grid_dir: Path = Path("research/lab_loop/generated_grids")
    objective: str = "general"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_yaml_file(path)


def _is_terminal(item: dict[str, Any]) -> bool:
    return str(item.get("status", "")) in TERMINAL_STATUSES


def _item_root(item: dict[str, Any]) -> str:
    hypothesis_id = str(item.get("root_id") or item.get("id", ""))
    for marker in (
        "_supervisor_reseed_",
        "_validation_",
        "_direction_flip_counterfactual",
        "_warning_filter_off_",
        "_setup_ignore_",
        "_warning_absent_",
        "_warning_cleared_",
    ):
        if marker in hypothesis_id:
            hypothesis_id = hypothesis_id.split(marker, 1)[0]
    return root_hypothesis_id(hypothesis_id)


def _item_generation(item: dict[str, Any]) -> int:
    try:
        return int(item.get("generation", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _item_priority(item: dict[str, Any]) -> int:
    try:
        return int(item.get("priority", 999) or 999)
    except (TypeError, ValueError):
        return 999


def _item_max_generation(item: dict[str, Any], options: SupervisorOptions) -> int:
    branch_budget = item.get("branch_budget", {})
    if isinstance(branch_budget, dict):
        try:
            return int(branch_budget.get("max_generation", options.max_generation))
        except (TypeError, ValueError):
            return options.max_generation
    return options.max_generation


def _completed_ids(state: dict[str, Any]) -> set[str]:
    return {str(item) for item in state.get("completed_hypothesis_ids", [])}


def _entry_root(entry: dict[str, Any]) -> str:
    return str(entry.get("root_hypothesis_id") or _item_root({"id": entry.get("hypothesis_id", "")}))


def _eligibility_block_reason(
    item: dict[str, Any],
    state: dict[str, Any],
    options: SupervisorOptions | None = None,
    *,
    weak_roots: set[str] | None = None,
) -> str:
    completed = _completed_ids(state)
    item_id = str(item.get("id", ""))
    if item_id in completed:
        return "completed"
    if _is_terminal(item):
        return "terminal"
    if not is_executable_hypothesis(item):
        return "missing_source"
    active_loop_number = int(state.get("last_completed_loop", 0) or 0) + 1
    cooldown_until = item.get("cooldown_until_loop")
    if cooldown_until is not None:
        try:
            if int(cooldown_until) > active_loop_number:
                return "cooled"
        except (TypeError, ValueError):
            pass
    if options is not None:
        generation = _item_generation(item)
        max_generation = _item_max_generation(item, options)
        if generation > max_generation and str(item.get("research_gate_stage", "")) != "validation":
            return "over_cap"
        if (
            options.objective == BULLISH_POSITIVE_OBJECTIVE
            and weak_roots is not None
            and _item_root(item) in weak_roots
        ):
            return "weak_family"
    return "runnable"


def runnable_inventory(
    queue: dict[str, Any],
    state: dict[str, Any],
    options: SupervisorOptions | None = None,
) -> dict[str, int]:
    weak_roots = set(_weak_bullish_roots(state, options)) if options is not None else set()
    counts = {
        "runnable": 0,
        "completed": 0,
        "terminal": 0,
        "cooled": 0,
        "over_cap": 0,
        "weak_family": 0,
        "missing_source": 0,
        "duplicate_signature": 0,
    }
    seen_signatures: set[str] = set()
    for item in queue.get("queue", []):
        signature = str(item.get("reseed_source_signature", "") or "")
        if signature:
            if signature in seen_signatures:
                counts["duplicate_signature"] += 1
                continue
            seen_signatures.add(signature)
        reason = _eligibility_block_reason(item, state, options, weak_roots=weak_roots)
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _eligible_items(
    queue: dict[str, Any],
    state: dict[str, Any],
    options: SupervisorOptions | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    weak_roots = set(_weak_bullish_roots(state, options)) if options is not None else set()
    for item in queue.get("queue", []):
        if _eligibility_block_reason(item, state, options, weak_roots=weak_roots) == "runnable":
            items.append(item)
    return items


def _load_epoch_decisions(state: dict[str, Any]) -> tuple[Path, list[dict[str, Any]]]:
    last_epoch = state.get("last_epoch", {})
    branch_path = Path(str(last_epoch.get("branch_decisions", "")))
    if not branch_path.exists():
        return Path(str(last_epoch.get("epoch_dir", ""))), []
    payload = load_yaml_file(branch_path)
    decisions = payload.get("decisions", [])
    if not isinstance(decisions, list):
        decisions = []
    return Path(str(last_epoch.get("epoch_dir", branch_path.parent))), decisions


def _recent_track_counts(state: dict[str, Any], *, window: int = 10) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in state.get("loop_history", [])[-window:]:
        track = str(entry.get("track", ""))
        if track:
            counts[track] = counts.get(track, 0) + 1
    return counts


def _score_item(
    item: dict[str, Any],
    *,
    promoted_roots: set[str],
    recent_tracks: dict[str, int],
    root_counts: dict[str, int],
    weak_bullish_roots: set[str],
    options: SupervisorOptions,
) -> float:
    item_id = str(item.get("id", ""))
    root = _item_root(item)
    track = str(item.get("track", ""))
    stage = str(item.get("research_gate_stage", ""))
    generation = _item_generation(item)
    priority = _item_priority(item)
    score = 1000.0 - float(priority)

    if item.get("manual_lock") == "force_next":
        score += 10000.0
    if root in promoted_roots or any(item_id.startswith(root) for root in promoted_roots):
        score += 700.0
    if stage == "validation":
        score += 500.0
    elif stage == "attribution":
        score += 250.0
    if track == "bullish_setup":
        score += 200.0
        if recent_tracks.get("warning", 0) > recent_tracks.get("bullish_setup", 0):
            score += 200.0
    if options.objective == BULLISH_POSITIVE_OBJECTIVE:
        claim_type = str(item.get("claim_type", ""))
        if track == "bullish_setup":
            score += 500.0
            if root in weak_bullish_roots:
                score -= 2000.0
            if _is_new_bullish_family(item):
                score += 450.0
        if claim_type == "bullish_entry":
            score += 350.0
        elif claim_type in {"control", "bullish_permission"}:
            score += 250.0
        elif claim_type == "warning_blocker":
            score += 150.0
    if str(item.get("promotion_level", "")).startswith("L3"):
        score += 150.0
    max_generation = _item_max_generation(item, options)
    if generation > max_generation:
        score -= 400.0 + (generation - max_generation) * 100.0
    if root_counts.get(root, 0) >= options.max_same_root_per_epoch:
        score -= 300.0
    return score


def _stable_sorted(items: list[dict[str, Any]], scores: dict[str, float]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            -scores.get(str(item.get("id", "")), 0.0),
            _item_priority(item),
            _item_generation(item),
            str(item.get("id", "")),
        ),
    )


def _item_setup_class(item: dict[str, Any]) -> str:
    return _slug_part(str(item.get("setup_class") or item.get("candidate_family_id") or _item_root(item)))


def _item_discovery_mode(item: dict[str, Any]) -> str:
    mode = str(item.get("discovery_mode", "")).strip()
    if mode:
        return mode
    stage = str(item.get("research_gate_stage", "")).strip()
    if stage:
        return stage
    return "new_family" if _item_generation(item) == 0 else "refinement"


def _is_new_bullish_family(item: dict[str, Any]) -> bool:
    if str(item.get("track", "")) != "bullish_setup":
        return False
    claim_type = str(item.get("claim_type", "bullish_entry") or "bullish_entry")
    return claim_type in {"", "bullish_entry"} and _item_discovery_mode(item) in {"new_family", "discovery"}


def _item_primitives(item: dict[str, Any]) -> set[str]:
    values = item.get("measurable_primitives", [])
    if not isinstance(values, list):
        return set()
    return {_slug_part(str(value)) for value in values if str(value).strip()}


def _primitive_overlap(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_values = _item_primitives(left)
    right_values = _item_primitives(right)
    if not left_values or not right_values:
        return 0.0
    union = left_values | right_values
    if not union:
        return 0.0
    return len(left_values & right_values) / len(union)


def _slug_part(value: str) -> str:
    slug = "".join(character if character.isalnum() or character == "_" else "_" for character in value).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.lower() or "supervisor_reseed"


def _safe_child_id(root: str, suffix: str, *, max_length: int = 96) -> str:
    safe_suffix = _slug_part(suffix)
    safe_root = _slug_part(root)
    root_length = max(8, max_length - len(safe_suffix) - 1)
    return f"{safe_root[:root_length]}_{safe_suffix}"[:max_length]


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _best_reseed_candidate(ranked: pd.DataFrame, strict_referee: pd.DataFrame) -> pd.Series | None:
    strict = strict_survivor_rows(strict_referee)
    if not strict.empty:
        candidate = strict.iloc[0]
        if "variant_id" in candidate and "variant_id" in ranked.columns:
            match = ranked[ranked["variant_id"] == candidate["variant_id"]]
            if not match.empty and "params" in match.columns:
                return match.iloc[0]
        if "params" in candidate:
            return candidate
    useful = useful_rows(ranked)
    if not useful.empty and "params" in useful.columns:
        return useful.iloc[0]
    return None


def _latest_epoch_entries(state: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_path = Path(str(state.get("last_epoch", {}).get("manifest", "")))
    loop_start = 0
    loop_end = int(state.get("last_completed_loop", 0) or 0)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        loop_start = int(manifest.get("loop_start", 0) or 0)
        loop_end = int(manifest.get("loop_end", loop_end) or loop_end)
    return [
        entry
        for entry in state.get("loop_history", [])
        if loop_start <= int(entry.get("loop_number", 0) or 0) <= loop_end
    ]


def _entry_has_reseed_evidence(entry: dict[str, Any]) -> bool:
    return int(entry.get("survivor_count", 0) or 0) > 0 or int(entry.get("useful_count", 0) or 0) > 0


def _entry_reseed_score(entry: dict[str, Any]) -> float:
    score = float(int(entry.get("survivor_count", 0) or 0) * 1000 + int(entry.get("useful_count", 0) or 0))
    if str(entry.get("track", "")) == "bullish_setup":
        score += 250.0
    score += float(int(entry.get("loop_number", 0) or 0)) / 10000.0
    return score


def _entry_bullish_evidence(entry: dict[str, Any]) -> dict[str, Any]:
    evidence_path = Path(str(entry.get("report_dir", ""))) / "bullish_evidence.yaml"
    if not evidence_path.exists():
        return {}
    return _read_yaml(evidence_path)


def _bullish_contract_roots(state: dict[str, Any]) -> set[str]:
    roots: set[str] = set()
    for entry in state.get("loop_history", []):
        if str(entry.get("track", "")) != "bullish_setup":
            continue
        evidence = _entry_bullish_evidence(entry)
        if evidence.get("passes_bullish_contract"):
            roots.add(_entry_root(entry))
    return roots


def _weak_bullish_roots(state: dict[str, Any], options: SupervisorOptions) -> dict[str, dict[str, Any]]:
    if options.objective != BULLISH_POSITIVE_OBJECTIVE or options.weak_family_attempt_limit < 1:
        return {}
    contract_roots = _bullish_contract_roots(state)
    attempts: dict[str, dict[str, Any]] = {}
    for entry in state.get("loop_history", []):
        if str(entry.get("track", "")) != "bullish_setup":
            continue
        root = _entry_root(entry)
        if root in contract_roots:
            continue
        evidence = _entry_bullish_evidence(entry)
        if evidence.get("passes_bullish_contract"):
            continue
        record = attempts.setdefault(
            root,
            {
                "attempts_without_contract": 0,
                "latest_loop": 0,
                "positive_useful_rows": 0,
                "failure_modes": {},
            },
        )
        record["attempts_without_contract"] += 1
        record["latest_loop"] = max(int(record["latest_loop"]), int(entry.get("loop_number", 0) or 0))
        record["positive_useful_rows"] += int(evidence.get("positive_useful_rows", 0) or 0)
        failure = str(evidence.get("failure_reason") or entry.get("bullish_failure_reason") or entry.get("reason") or "")
        if failure:
            modes = record["failure_modes"]
            modes[failure] = int(modes.get(failure, 0)) + 1

    current_loop = int(state.get("last_completed_loop", 0) or 0)
    weak: dict[str, dict[str, Any]] = {}
    for root, record in attempts.items():
        if int(record["attempts_without_contract"]) < options.weak_family_attempt_limit:
            continue
        weak[root] = {
            **record,
            "cooldown_until_loop": current_loop + options.weak_family_cooldown_loops,
            "reason": (
                f"{record['attempts_without_contract']} bullish attempts without a "
                "bullish-positive contract pass"
            ),
        }
    return weak


def _bullish_reseed_score(entry: dict[str, Any]) -> float:
    evidence = _entry_bullish_evidence(entry)
    score = _entry_reseed_score(entry)

    def numeric(key: str) -> float:
        try:
            value = evidence.get(key, 0)
            return float(value if value is not None else 0)
        except (TypeError, ValueError):
            return 0.0

    if evidence.get("passes_bullish_contract"):
        score += 10000.0
    if evidence.get("passes_path_gate"):
        score += 1000.0
    score += float(evidence.get("positive_useful_rows", 0) or 0) * 25.0
    score += numeric("terminal_median_relative_return") * 500.0
    score += numeric("mfe_mae_ratio") * 50.0
    score += numeric("hit_rate") * 100.0
    score += numeric("unique_event_clusters") * 10.0
    if str(evidence.get("failure_reason", "")) == "no useful positive-direction rows":
        score -= 1000.0
    return score


def _bullish_entry_can_reseed(entry: dict[str, Any], options: SupervisorOptions) -> bool:
    if options.objective != BULLISH_POSITIVE_OBJECTIVE or str(entry.get("track", "")) != "bullish_setup":
        return True
    evidence = _entry_bullish_evidence(entry)
    if not evidence:
        return False
    if evidence.get("passes_bullish_contract"):
        return True
    return bool(
        evidence.get("passes_path_gate")
        and int(evidence.get("positive_useful_rows", 0) or 0) > 0
        and str(evidence.get("failure_reason", "")) != "no useful positive-direction rows"
    )


def _select_reseed_source_entries(state: dict[str, Any], options: SupervisorOptions) -> list[dict[str, Any]]:
    latest = [
        entry
        for entry in _latest_epoch_entries(state)
        if _entry_has_reseed_evidence(entry) and _bullish_entry_can_reseed(entry, options)
    ]
    latest_keys = {(entry.get("loop_number"), entry.get("hypothesis_id")) for entry in latest}
    archive = [
        entry
        for entry in state.get("loop_history", [])
        if _entry_has_reseed_evidence(entry)
        and _bullish_entry_can_reseed(entry, options)
        and (entry.get("loop_number"), entry.get("hypothesis_id")) not in latest_keys
    ]
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[Any, Any]] = set()
    root_counts: dict[str, int] = {}
    weak_roots = set(_weak_bullish_roots(state, options))

    def add_entry(entry: dict[str, Any]) -> bool:
        if len(selected) >= options.max_reseed_per_epoch:
            return False
        key = (entry.get("loop_number"), entry.get("hypothesis_id"))
        if key in selected_keys:
            return False
        root = _entry_root(entry)
        if root_counts.get(root, 0) >= options.max_same_root_per_epoch:
            return False
        if options.objective == BULLISH_POSITIVE_OBJECTIVE and root in weak_roots:
            return False
        if (
            options.objective == BULLISH_POSITIVE_OBJECTIVE
            and str(entry.get("track", "")) == "bullish_setup"
            and not _entry_bullish_evidence(entry).get("passes_bullish_contract")
            and int(entry.get("generation", 0) or 0) > options.max_non_contract_reseed_source_generation
        ):
            return False
        selected.append(entry)
        selected_keys.add(key)
        root_counts[root] = root_counts.get(root, 0) + 1
        return True

    if options.objective == BULLISH_POSITIVE_OBJECTIVE:
        combined = [*latest, *archive]
        bullish = sorted(
            [entry for entry in combined if str(entry.get("track", "")) == "bullish_setup"],
            key=_bullish_reseed_score,
            reverse=True,
        )
        non_bullish = sorted(
            [entry for entry in combined if str(entry.get("track", "")) != "bullish_setup"],
            key=_entry_reseed_score,
            reverse=True,
        )
        bullish_target = min(
            len(bullish),
            math.ceil(options.max_reseed_per_epoch * max(options.min_bullish_share, 0.70)),
        )
        for entry in bullish:
            if sum(1 for item in selected if str(item.get("track", "")) == "bullish_setup") >= bullish_target:
                break
            add_entry(entry)
        for entry in non_bullish:
            if len(selected) >= options.max_reseed_per_epoch:
                break
            add_entry(entry)
        for entry in bullish:
            if len(selected) >= options.max_reseed_per_epoch:
                break
            add_entry(entry)
        return selected

    latest = sorted(latest, key=_entry_reseed_score, reverse=True)
    archive = sorted(archive, key=_entry_reseed_score, reverse=True)

    for entry in latest:
        add_entry(entry)

    bullish_target = min(
        len([entry for entry in [*latest, *archive] if str(entry.get("track", "")) == "bullish_setup"]),
        math.ceil(options.max_reseed_per_epoch * options.min_bullish_share),
    )
    for entry in [*latest, *archive]:
        if sum(1 for item in selected if str(item.get("track", "")) == "bullish_setup") >= bullish_target:
            break
        if str(entry.get("track", "")) == "bullish_setup":
            add_entry(entry)

    for entry in archive:
        if len(selected) >= options.max_reseed_per_epoch:
            break
        add_entry(entry)

    return selected


def _reseed_source_signature(root: str, candidate: pd.Series, generation: int) -> str:
    payload = {
        "root": root,
        "generation": generation,
        "variant_id": str(candidate.get("variant_id", "")),
        "family_id": str(candidate.get("family_id", "")),
        "detector": str(candidate.get("detector", "")),
        "direction": str(candidate.get("direction", "")),
        "timeframe": str(candidate.get("timeframe", "")),
        "params": str(candidate.get("params", "")),
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def reseed_runtime_queue_from_recent_evidence(
    *,
    queue: dict[str, Any],
    state: dict[str, Any],
    options: SupervisorOptions,
) -> list[str]:
    """Create bounded follow-up hypotheses when the runnable queue is exhausted."""
    if not options.reseed_when_empty or options.max_reseed_per_epoch < 1:
        return []
    existing_ids = {str(item.get("id", "")) for item in queue.get("queue", [])}
    existing_signature_counts: dict[str, int] = {}
    reseed_counts_by_root: dict[str, int] = {}
    for item in queue.get("queue", []):
        signature = str(item.get("reseed_source_signature", "") or "")
        if signature:
            existing_signature_counts[signature] = existing_signature_counts.get(signature, 0) + 1
        if item.get("created_from") == "meta_supervisor_reseed":
            root = _item_root(item)
            reseed_counts_by_root[root] = reseed_counts_by_root.get(root, 0) + 1
    by_id = {str(item.get("id", "")): item for item in queue.get("queue", [])}
    session_id = str(state.get("session_id") or "session")
    actions: list[str] = []
    reseeded = 0
    entries = _select_reseed_source_entries(state, options)

    for entry in entries:
        if reseeded >= options.max_reseed_per_epoch:
            break
        if int(entry.get("survivor_count", 0) or 0) <= 0 and int(entry.get("useful_count", 0) or 0) <= 0:
            continue
        parent_id = str(entry.get("hypothesis_id", ""))
        parent = by_id.get(parent_id, {})
        report_dir = Path(str(entry.get("report_dir", "")))
        ranked = _read_csv_if_exists(report_dir / "ranked.csv")
        strict_referee = _read_csv_if_exists(report_dir / "strict_referee.csv")
        candidate = _best_reseed_candidate(ranked, strict_referee)
        if candidate is None:
            continue

        parent_root = _item_root(parent or {"id": entry.get("root_hypothesis_id") or parent_id})
        if reseed_counts_by_root.get(parent_root, 0) >= options.max_reseeds_per_root:
            continue
        loop_number = int(entry.get("loop_number", 0) or 0)
        reseed_round = int(state.get("last_completed_loop", 0) or 0)
        generation = int(parent.get("generation", entry.get("generation", 0)) or 0) + 1
        max_generation = _item_max_generation(parent or entry, options)
        if generation > max_generation:
            continue
        reseed_signature = _reseed_source_signature(parent_root, candidate, generation)
        if existing_signature_counts.get(reseed_signature, 0) >= options.max_reseed_signature_attempts:
            continue
        suffix = f"supervisor_reseed_g{generation:03d}_l{loop_number:04d}_r{reseed_round:04d}_{reseeded + 1}"
        child_id = _safe_child_id(parent_root, suffix)
        if child_id in existing_ids:
            child_id = _safe_child_id(parent_root, f"{suffix}_{len(existing_ids) % 10000:04d}")
        if child_id in existing_ids:
            continue

        grid = build_refinement_grid(
            candidate,
            family_suffix=f"supervisor_reseed_l{loop_number:04d}_{reseeded + 1}",
            max_mutated_numeric_params=2,
        )
        grid_path = options.generated_grid_dir / session_id / f"{child_id}.yaml"
        atomic_write_yaml(grid_path, grid)
        direction = str(candidate.get("direction", ""))
        parent_track = str(parent.get("track") or entry.get("track") or "")
        child_track = parent_track or ("warning" if direction == "negative" else "bullish_setup")
        claim_type = str(parent.get("claim_type", "") or "")
        if options.objective == BULLISH_POSITIVE_OBJECTIVE:
            if child_track == "bullish_setup":
                claim_type = claim_type or "bullish_entry"
            elif child_track == "warning":
                claim_type = claim_type or "warning_blocker"
        child = {
            "id": child_id,
            "track": child_track,
            "status": "new",
            "promotion_level": "L1_encoded",
            "priority": reseeded,
            "root_id": parent_root,
            "parent_id": parent_id,
            "generation": generation,
            "lineage_fingerprint": lineage_fingerprint(parent_root, parent_id, child_id, generation, reseed_round),
            "reseed_source_signature": reseed_signature,
            "created_from": "meta_supervisor_reseed",
            "research_gate_stage": "reseed",
            "discovery_mode": "refinement",
            "source": str(grid_path),
            "hypothesis": f"Supervisor reseed from latest strict/useful evidence in {parent_id}.",
            "measurable_primitives": list(parent.get("measurable_primitives", [])) + ["supervisor_reseed"],
            "expected_outcome": "negative_forward_relative_return"
            if direction == "negative"
            else "positive_forward_relative_return",
            "next_action": "Run as a bounded reseed because the runtime queue exhausted runnable evidence.",
            "supervisor_priority_reason": "reseeded from latest strict/useful evidence after queue exhaustion",
        }
        if claim_type:
            child["claim_type"] = claim_type
        for key in ("setup_class", "path_objective", "branch_budget", "required_controls"):
            if key in parent:
                child[key] = parent[key]
        queue.setdefault("queue", []).append(child)
        existing_ids.add(child_id)
        existing_signature_counts[reseed_signature] = existing_signature_counts.get(reseed_signature, 0) + 1
        reseed_counts_by_root[parent_root] = reseed_counts_by_root.get(parent_root, 0) + 1
        actions.append(f"reseeded {child_id} from {parent_id}")
        reseeded += 1
    return actions


def _pick_epoch_slots(
    eligible: list[dict[str, Any]],
    *,
    promoted_roots: set[str],
    recent_tracks: dict[str, int],
    weak_bullish_roots: set[str],
    options: SupervisorOptions,
) -> list[dict[str, Any]]:
    root_counts: dict[str, int] = {}
    setup_class_counts: dict[str, int] = {}
    scores = {
        str(item.get("id", "")): _score_item(
            item,
            promoted_roots=promoted_roots,
            recent_tracks=recent_tracks,
            root_counts=root_counts,
            weak_bullish_roots=weak_bullish_roots,
            options=options,
        )
        for item in eligible
    }
    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()

    def can_add(candidate: dict[str, Any], *, enforce_setup_class: bool = False, enforce_overlap: bool = False) -> bool:
        candidate_id = str(candidate.get("id", ""))
        root = _item_root(candidate)
        if candidate_id in chosen_ids:
            return False
        if (
            _item_generation(candidate) > _item_max_generation(candidate, options)
            and str(candidate.get("research_gate_stage", "")) != "validation"
        ):
            return False
        if root_counts.get(root, 0) >= options.max_same_root_per_epoch:
            return False
        if options.objective == BULLISH_POSITIVE_OBJECTIVE and root in weak_bullish_roots:
            return False
        if enforce_setup_class and str(candidate.get("track", "")) == "bullish_setup":
            setup_class = _item_setup_class(candidate)
            if setup_class_counts.get(setup_class, 0) >= options.max_same_setup_class_per_epoch:
                return False
        if enforce_overlap and options.max_primitive_overlap < 1:
            for item in chosen:
                if _primitive_overlap(candidate, item) > options.max_primitive_overlap:
                    return False
        return True

    def add_from(
        candidates: list[dict[str, Any]],
        slots: int,
        *,
        enforce_setup_class: bool = False,
        enforce_overlap: bool = False,
    ) -> None:
        for candidate in _stable_sorted(candidates, scores):
            if len(chosen) >= options.epoch_size or slots <= 0:
                return
            if not can_add(
                candidate,
                enforce_setup_class=enforce_setup_class,
                enforce_overlap=enforce_overlap,
            ):
                continue
            candidate_id = str(candidate.get("id", ""))
            root = _item_root(candidate)
            chosen.append(candidate)
            chosen_ids.add(candidate_id)
            root_counts[root] = root_counts.get(root, 0) + 1
            setup_class = _item_setup_class(candidate)
            setup_class_counts[setup_class] = setup_class_counts.get(setup_class, 0) + 1
            slots -= 1

    if options.objective == BULLISH_POSITIVE_OBJECTIVE:
        bullish_entries = [
            item
            for item in eligible
            if _is_new_bullish_family(item) and _item_root(item) not in weak_bullish_roots
        ]
        controls = [
            item
            for item in eligible
            if str(item.get("claim_type", "")) in {"control", "bullish_permission", "warning_blocker"}
            or str(item.get("research_gate_stage", "")) in {"attribution"}
        ]
        validations = [
            item
            for item in eligible
            if str(item.get("research_gate_stage", "")) == "validation"
            or (
                str(item.get("track", "")) == "bullish_setup"
                and str(item.get("claim_type", "")) in {"", "bullish_entry"}
                and _item_generation(item) > 0
            )
        ]
        add_from(
            bullish_entries,
            min(len(bullish_entries), options.min_new_bullish_roots),
            enforce_setup_class=True,
            enforce_overlap=True,
        )
        if len(chosen) < min(options.epoch_size, options.min_new_bullish_roots):
            add_from(
                bullish_entries,
                min(len(bullish_entries), options.min_new_bullish_roots) - len(chosen),
                enforce_setup_class=True,
            )
        add_from(validations, 1)
        add_from(controls, 1, enforce_overlap=True)
        bullish_floor = min(
            len([item for item in eligible if str(item.get("track", "")) == "bullish_setup"]),
            math.ceil(options.epoch_size * max(options.min_bullish_share, 0.70)),
        )
        current_bullish = sum(1 for item in chosen if str(item.get("track", "")) == "bullish_setup")
        if current_bullish < bullish_floor:
            bullish = [
                item
                for item in eligible
                if str(item.get("track", "")) == "bullish_setup" and _item_root(item) not in weak_bullish_roots
            ]
            add_from(bullish, bullish_floor - current_bullish, enforce_setup_class=True)
        add_from(eligible, options.epoch_size - len(chosen))
        return chosen[: options.epoch_size]

    validation_slots = max(1, math.ceil(options.epoch_size * options.validation_share))
    validation = [item for item in eligible if str(item.get("research_gate_stage", "")) == "validation"]
    add_from(validation, validation_slots)

    bullish = [item for item in eligible if str(item.get("track", "")) == "bullish_setup"]
    bullish_floor = min(
        len(bullish),
        math.ceil(options.epoch_size * options.min_bullish_share),
    )
    current_bullish = sum(1 for item in chosen if str(item.get("track", "")) == "bullish_setup")
    add_from(bullish, max(0, bullish_floor - current_bullish))

    add_from(eligible, options.epoch_size - len(chosen))
    return chosen[: options.epoch_size]


def _queue_patch_for_slots(slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patch: list[dict[str, Any]] = []
    for index, item in enumerate(slots):
        patch.append(
            {
                "type": "schedule",
                "hypothesis_id": item.get("id"),
                "old_priority": _item_priority(item),
                "new_priority": index,
                "slot": index + 1,
                "reason": "selected by meta-supervisor epoch portfolio",
            }
        )
    return patch


def _queue_patch_for_caps(
    eligible: list[dict[str, Any]],
    slots: list[dict[str, Any]],
    *,
    weak_bullish_roots: dict[str, dict[str, Any]],
    options: SupervisorOptions,
) -> list[dict[str, Any]]:
    slot_roots: dict[str, int] = {}
    for item in slots:
        root = _item_root(item)
        slot_roots[root] = slot_roots.get(root, 0) + 1
    patch: list[dict[str, Any]] = []
    for item in eligible:
        if item in slots:
            continue
        root = _item_root(item)
        generation = _item_generation(item)
        max_generation = _item_max_generation(item, options)
        if root in weak_bullish_roots and options.objective == BULLISH_POSITIVE_OBJECTIVE:
            weak = weak_bullish_roots[root]
            patch.append(
                {
                    "type": "cool_family",
                    "hypothesis_id": item.get("id"),
                    "old_priority": _item_priority(item),
                    "new_priority": _item_priority(item) + 500,
                    "cooldown_until_loop": weak.get("cooldown_until_loop", 0),
                    "reason": weak.get("reason", "bullish family cooled after repeated non-contract evidence"),
                }
            )
        elif generation > max_generation and str(item.get("research_gate_stage", "")) != "validation":
            patch.append(
                {
                    "type": "cool",
                    "hypothesis_id": item.get("id"),
                    "old_priority": _item_priority(item),
                    "new_priority": _item_priority(item) + 200,
                    "reason": f"generation {generation} exceeds supervisor max_generation={max_generation}",
                }
            )
        elif slot_roots.get(root, 0) >= options.max_same_root_per_epoch and item not in slots:
            patch.append(
                {
                    "type": "tag",
                    "hypothesis_id": item.get("id"),
                    "reason": "same-root branch cap reserved other candidates for the next epoch",
                }
            )
    return patch


def build_supervisor_decision(
    *,
    state: dict[str, Any],
    queue: dict[str, Any],
    scoreboard: dict[str, Any],
    options: SupervisorOptions,
) -> dict[str, Any]:
    epoch_dir, decisions = _load_epoch_decisions(state)
    promoted_roots = {str(item.get("concept_id")) for item in decisions if item.get("decision") == "promote"}
    recent_tracks = _recent_track_counts(state)
    eligible = _eligible_items(queue, state, options)
    inventory = runnable_inventory(queue, state, options)
    weak_bullish_roots = _weak_bullish_roots(state, options)
    slots = _pick_epoch_slots(
        eligible,
        promoted_roots=promoted_roots,
        recent_tracks=recent_tracks,
        weak_bullish_roots=set(weak_bullish_roots),
        options=options,
    )
    cap_candidates = [
        item
        for item in queue.get("queue", [])
        if str(item.get("id", "")) not in _completed_ids(state)
        and not _is_terminal(item)
        and is_executable_hypothesis(item)
    ]
    queue_patch = [
        *_queue_patch_for_slots(slots),
        *_queue_patch_for_caps(cap_candidates, slots, weak_bullish_roots=weak_bullish_roots, options=options),
    ]
    concept_decisions = []
    concepts = scoreboard.get("concepts", {}) if isinstance(scoreboard.get("concepts", {}), dict) else {}
    for decision in decisions:
        concept_id = str(decision.get("concept_id", ""))
        concept = concepts.get(concept_id, {})
        strict = int(concept.get("strict_survivors", 0) or 0) if isinstance(concept, dict) else 0
        clusters = int(concept.get("event_clusters", 0) or 0) if isinstance(concept, dict) else 0
        branch_action = str(decision.get("decision", ""))
        if concept_id in weak_bullish_roots and options.objective == BULLISH_POSITIVE_OBJECTIVE:
            action = "cool_weak_family"
        elif branch_action == "promote":
            action = "validate"
        elif branch_action == "archive":
            action = "archive"
        elif branch_action == "refine" and strict == 0:
            action = "broaden" if clusters < 10 else "refine"
        else:
            action = branch_action or "review"
        concept_decisions.append(
            {
                "concept_id": concept_id,
                "action": action,
                "reason": weak_bullish_roots.get(concept_id, {}).get("reason", decision.get("reason", "")),
                "evidence": {
                    "strict_survivors": strict,
                    "event_clusters": clusters,
                    "best_timeframe": concept.get("best_timeframe", "") if isinstance(concept, dict) else "",
                    "best_median_relative_return": concept.get("best_median_relative_return")
                    if isinstance(concept, dict)
                    else None,
                    "validation_status": concept.get("validation_status", "") if isinstance(concept, dict) else "",
                },
            }
        )

    return {
        "model": SUPERVISOR_MODEL,
        "epoch": state.get("last_epoch", {}).get("epoch", ""),
        "generated_at": utc_now_iso(),
        "apply": options.apply,
        "objective": options.objective,
        "policy": {
            "epoch_size": options.epoch_size,
            "max_generation": options.max_generation,
            "max_same_root_per_epoch": options.max_same_root_per_epoch,
            "min_bullish_share": options.min_bullish_share,
            "validation_share": options.validation_share,
            "bullish_positive_mode": options.objective == BULLISH_POSITIVE_OBJECTIVE,
            "min_new_bullish_roots": options.min_new_bullish_roots,
            "max_same_setup_class_per_epoch": options.max_same_setup_class_per_epoch,
            "weak_family_attempt_limit": options.weak_family_attempt_limit,
            "weak_family_cooldown_loops": options.weak_family_cooldown_loops,
            "max_non_contract_reseed_source_generation": options.max_non_contract_reseed_source_generation,
            "max_primitive_overlap": options.max_primitive_overlap,
            "max_reseeds_per_root": options.max_reseeds_per_root,
            "max_reseed_signature_attempts": options.max_reseed_signature_attempts,
        },
        "inputs": {
            "state_path": str(options.state_path),
            "runtime_queue_path": str(options.runtime_queue_path),
            "concept_scoreboard_path": str(options.concept_scoreboard_path),
            "epoch_dir": str(epoch_dir),
            "eligible_hypotheses": len(eligible),
            "runnable_inventory": inventory,
            "recent_tracks": recent_tracks,
        },
        "weak_bullish_roots": weak_bullish_roots,
        "concept_decisions": concept_decisions,
        "next_epoch_slots": [
            {
                "slot": index + 1,
                "hypothesis_id": item.get("id"),
                "track": item.get("track"),
                "research_gate_stage": item.get("research_gate_stage", ""),
                "root_id": _item_root(item),
                "old_priority": _item_priority(item),
            }
            for index, item in enumerate(slots)
        ],
        "queue_patch": queue_patch,
    }


def apply_supervisor_decision(queue: dict[str, Any], decision: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    by_id = {str(item.get("id", "")): item for item in queue.get("queue", [])}
    for patch in decision.get("queue_patch", []):
        hypothesis_id = str(patch.get("hypothesis_id", ""))
        item = by_id.get(hypothesis_id)
        if item is None:
            continue
        patch_type = str(patch.get("type", ""))
        if patch_type in {"schedule", "cool", "cool_family"}:
            item["priority"] = int(patch.get("new_priority", item.get("priority", 999)))
            item["last_supervised_at"] = decision.get("generated_at")
            item["supervisor_action"] = "cool_weak_family" if patch_type == "cool_family" else patch_type
            item["supervisor_priority_reason"] = patch.get("reason", "")
            if "cooldown_until_loop" in patch:
                item["cooldown_until_loop"] = int(patch.get("cooldown_until_loop", 0) or 0)
                item["evidence_budget_status"] = "cooldown_weak_family"
            if "slot" in patch:
                item["supervisor_next_epoch_slot"] = int(patch["slot"])
            actions.append(f"{patch_type} {hypothesis_id} priority {patch.get('old_priority')}->{item['priority']}")
        elif patch_type == "tag":
            item["last_supervised_at"] = decision.get("generated_at")
            item["supervisor_action"] = "defer"
            item["supervisor_priority_reason"] = patch.get("reason", "")
            actions.append(f"tagged {hypothesis_id}: {patch.get('reason', '')}")
    return actions


def _latest_bullish_evidence(state: dict[str, Any], concept_id: str) -> dict[str, Any]:
    for entry in reversed(state.get("loop_history", [])):
        if _entry_root(entry) != concept_id:
            continue
        evidence_path = Path(str(entry.get("report_dir", ""))) / "bullish_evidence.yaml"
        if evidence_path.exists():
            return _read_yaml(evidence_path)
    return {}


def update_evidence_ledger(
    path: Path,
    *,
    state: dict[str, Any],
    scoreboard: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    existing = _read_yaml(path) if path.exists() else {"model": "riskflow_lab_evidence_ledger_v0", "concepts": {}}
    concepts = existing.get("concepts", {})
    if not isinstance(concepts, dict):
        concepts = {}
    scoreboard_concepts = scoreboard.get("concepts", {}) if isinstance(scoreboard.get("concepts", {}), dict) else {}
    weak_bullish_roots = decision.get("weak_bullish_roots", {})
    if not isinstance(weak_bullish_roots, dict):
        weak_bullish_roots = {}
    for concept in decision.get("concept_decisions", []):
        concept_id = str(concept.get("concept_id", ""))
        source = scoreboard_concepts.get(concept_id, {}) if isinstance(scoreboard_concepts, dict) else {}
        bullish_evidence = _latest_bullish_evidence(state, concept_id)
        prior = concepts.get(concept_id, {})
        weak = weak_bullish_roots.get(concept_id, {})
        if not isinstance(weak, dict):
            weak = {}
        concepts[concept_id] = {
            **prior,
            "track": source.get("track", prior.get("track", "")) if isinstance(source, dict) else prior.get("track", ""),
            "evidence_stage": source.get("current_promotion_level", prior.get("evidence_stage", ""))
            if isinstance(source, dict)
            else prior.get("evidence_stage", ""),
            "strict_survivors": source.get("strict_survivors", prior.get("strict_survivors", 0))
            if isinstance(source, dict)
            else prior.get("strict_survivors", 0),
            "event_clusters": source.get("event_clusters", prior.get("event_clusters", 0))
            if isinstance(source, dict)
            else prior.get("event_clusters", 0),
            "best_median_relative_return": source.get(
                "best_median_relative_return",
                prior.get("best_median_relative_return"),
            )
            if isinstance(source, dict)
            else prior.get("best_median_relative_return"),
            "last_supervisor_action": concept.get("action"),
            "last_supervisor_reason": concept.get("reason", ""),
            "latest_epoch": decision.get("epoch", ""),
            "latest_loop": state.get("last_completed_loop", 0),
            "claim_type": bullish_evidence.get("claim_type", prior.get("claim_type", "")),
            "setup_class": bullish_evidence.get("setup_class", prior.get("setup_class", "")),
            "contract_tier": bullish_evidence.get("contract_tier", prior.get("contract_tier", "")),
            "asymmetry_score": bullish_evidence.get("asymmetry_score", prior.get("asymmetry_score")),
            "path_gate": bullish_evidence.get("passes_path_gate", prior.get("path_gate", None)),
            "bullish_contract": bullish_evidence.get(
                "passes_bullish_contract",
                prior.get("bullish_contract", None),
            ),
            "failure_mode": bullish_evidence.get("failure_reason", prior.get("failure_mode", "")),
            "next_allowed_action": "validate_bullish_controls"
            if bullish_evidence.get("passes_bullish_contract")
            else ("needs_new_bullish_family" if weak else prior.get("next_allowed_action", "")),
            "attempts_without_bullish_contract": weak.get(
                "attempts_without_contract",
                prior.get("attempts_without_bullish_contract", 0),
            ),
            "suspended_until_loop": weak.get("cooldown_until_loop", prior.get("suspended_until_loop", "")),
            "retirement_reason": weak.get("reason", prior.get("retirement_reason", "")),
            "updated_at": decision.get("generated_at", utc_now_iso()),
        }
    atomic_write_yaml(
        path,
        {
            "model": "riskflow_lab_evidence_ledger_v0",
            "updated_at": utc_now_iso(),
            "concepts": concepts,
        },
    )


def write_supervisor_artifacts(
    epoch_dir: Path,
    *,
    state: dict[str, Any],
    queue: dict[str, Any],
    scoreboard: dict[str, Any],
    decision: dict[str, Any],
    actions: list[str],
) -> dict[str, str]:
    epoch_dir.mkdir(parents=True, exist_ok=True)
    input_payload = {
        "model": "riskflow_lab_supervisor_input_v0",
        "generated_at": utc_now_iso(),
        "last_completed_loop": state.get("last_completed_loop", 0),
        "queue_items": len(queue.get("queue", [])),
        "scoreboard_concepts": len(scoreboard.get("concepts", {})) if isinstance(scoreboard.get("concepts", {}), dict) else 0,
        "last_epoch": state.get("last_epoch", {}),
    }
    queue_patch = {
        "model": "riskflow_lab_supervisor_queue_patch_v0",
        "epoch": decision.get("epoch", ""),
        "applied": bool(decision.get("apply")),
        "actions": actions,
        "queue_patch": decision.get("queue_patch", []),
    }
    summary_lines = [
        f"# Lab Meta-Supervisor: {decision.get('epoch', '')}",
        "",
        f"Generated: {decision.get('generated_at', '')}",
        f"Applied: {bool(decision.get('apply'))}",
        f"Objective: {decision.get('objective', '')}",
        f"Runnable inventory: {decision.get('inputs', {}).get('runnable_inventory', {})}",
        "",
        "## Weak Bullish Families",
        *(
            [
                f"- {root}: {details.get('reason', '')}; cooldown until loop {details.get('cooldown_until_loop', '')}"
                for root, details in sorted(dict(decision.get("weak_bullish_roots", {})).items())
            ]
            or ["- None."]
        ),
        "",
        "## Next Epoch Slots",
        *[
            f"- {slot['slot']}: {slot['hypothesis_id']} ({slot.get('track')}, {slot.get('research_gate_stage') or 'standard'})"
            for slot in decision.get("next_epoch_slots", [])
        ],
        "",
        "## Queue Actions",
        *([f"- {action}" for action in actions] or ["- None."]),
        "",
        "## Concept Decisions",
        *[
            f"- {item.get('concept_id')}: {item.get('action')} - {item.get('reason', '')}"
            for item in decision.get("concept_decisions", [])
        ],
        "",
    ]
    paths = {
        "supervisor_input": str(epoch_dir / "supervisor_input.json"),
        "supervisor_decisions": str(epoch_dir / "supervisor_decisions.yaml"),
        "queue_patch": str(epoch_dir / "queue_patch.yaml"),
        "supervisor_summary": str(epoch_dir / "supervisor_summary.md"),
    }
    atomic_write_json(epoch_dir / "supervisor_input.json", input_payload)
    atomic_write_yaml(epoch_dir / "supervisor_decisions.yaml", decision)
    atomic_write_yaml(epoch_dir / "queue_patch.yaml", queue_patch)
    atomic_write_text(epoch_dir / "supervisor_summary.md", "\n".join(summary_lines))
    return paths


def supervise_latest_epoch(options: SupervisorOptions) -> dict[str, Any]:
    state = load_lab_state(options.state_path)
    if not state:
        raise ValueError(f"No lab-loop state found at {options.state_path}")
    queue = load_lab_queue(options.runtime_queue_path)
    scoreboard = _read_yaml(options.concept_scoreboard_path)
    epoch_dir = Path(str(state.get("last_epoch", {}).get("epoch_dir", "")))
    if not epoch_dir.exists():
        raise ValueError("No latest epoch directory found to supervise")
    decision = build_supervisor_decision(
        state=state,
        queue=queue,
        scoreboard=scoreboard,
        options=options,
    )
    reseed_actions: list[str] = []
    if options.apply and not decision.get("next_epoch_slots"):
        reseed_actions = reseed_runtime_queue_from_recent_evidence(
            queue=queue,
            state=state,
            options=options,
        )
        if reseed_actions:
            decision = build_supervisor_decision(
                state=state,
                queue=queue,
                scoreboard=scoreboard,
                options=options,
            )
            decision["reseeded_hypotheses"] = reseed_actions
    actions: list[str] = []
    if options.apply:
        actions = apply_supervisor_decision(queue, decision)
        actions = [*reseed_actions, *actions]
        atomic_write_yaml(options.runtime_queue_path, queue)
    post_inventory = runnable_inventory(queue, state, options)
    artifacts = write_supervisor_artifacts(
        epoch_dir,
        state=state,
        queue=queue,
        scoreboard=scoreboard,
        decision=decision,
        actions=actions,
    )
    if options.apply:
        update_evidence_ledger(
            options.evidence_ledger_path,
            state=state,
            scoreboard=scoreboard,
            decision=decision,
        )
        state["last_supervisor"] = {
            "epoch": decision.get("epoch", ""),
            "generated_at": decision.get("generated_at", ""),
            "applied": options.apply,
            "reseeded": len(reseed_actions),
            "summary": artifacts["supervisor_summary"],
            "decisions": artifacts["supervisor_decisions"],
            "queue_patch": artifacts["queue_patch"],
            "runnable_inventory": post_inventory,
        }
        state["runnable_inventory"] = post_inventory
        if state.get("status") == "completed_no_runnable_hypotheses":
            if int(post_inventory.get("runnable", 0) or 0) > 0:
                state["status"] = "completed"
                state.pop("requires_new_candidate_queue", None)
                state.pop("no_runnable_reason", None)
            elif reseed_actions:
                state["status"] = "stopped_no_runnable_after_supervision"
                state["no_runnable_reason"] = "cooled_or_exhausted_roots"
                state["requires_new_candidate_queue"] = True
            else:
                state["requires_new_candidate_queue"] = True
                state["no_runnable_reason"] = "evidence_exhausted"
        atomic_write_json(options.state_path, state)
    return {
        "decision": decision,
        "actions": actions,
        "artifacts": artifacts,
        "state": state,
    }


def run_supervised_epochs(
    lab_options: LabLoopOptions,
    supervisor_options: SupervisorOptions,
    *,
    epochs: int,
    epoch_size: int,
) -> dict[str, Any]:
    if epochs < 1:
        raise ValueError("epochs must be >= 1")
    state: dict[str, Any] = {}
    completed_epochs = 0
    for epoch_index in range(epochs):
        epoch_lab_options = LabLoopOptions(
            **{
                **lab_options.__dict__,
                "resume": True if epoch_index > 0 or lab_options.resume else lab_options.resume,
                "supervisor_max_generation": supervisor_options.max_generation,
            }
        )
        before = load_lab_state(epoch_lab_options.state_path).get("last_completed_loop", 0)
        state = run_lab_epoch(epoch_lab_options, epoch_size=epoch_size)
        after = int(state.get("last_completed_loop", 0) or 0)
        supervisor_result = supervise_latest_epoch(
            SupervisorOptions(
                **{
                    **supervisor_options.__dict__,
                    "epoch_size": epoch_size,
                }
            )
        )
        completed_epochs += 1
        reseeded = sum(1 for action in supervisor_result.get("actions", []) if action.startswith("reseeded "))
        post_state = load_lab_state(epoch_lab_options.state_path)
        post_queue = load_lab_queue(epoch_lab_options.runtime_queue_path)
        has_runnable_after_supervision = bool(_eligible_items(post_queue, post_state, supervisor_options))
        print(
            f"Supervised epoch {completed_epochs}/{epochs}: loops {before + 1}-{after}, "
            f"status={post_state.get('status')}, reseeded={reseeded}",
            flush=True,
        )
        if after <= int(before or 0):
            if not has_runnable_after_supervision:
                break
            continue
        if post_state.get("status") in {
            "completed_no_runnable_hypotheses",
            "stopped_no_runnable_after_supervision",
        } and not has_runnable_after_supervision:
            break
    state = load_lab_state(lab_options.state_path)
    state["supervised_epochs_completed"] = completed_epochs
    atomic_write_json(lab_options.state_path, state)
    return state
