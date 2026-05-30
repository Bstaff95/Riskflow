from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .lab_loop import (
    TERMINAL_STATUSES,
    LabLoopOptions,
    atomic_write_json,
    atomic_write_text,
    atomic_write_yaml,
    build_refinement_grid,
    is_executable_hypothesis,
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
    reseed_when_empty: bool = True
    max_reseed_per_epoch: int = 5
    generated_grid_dir: Path = Path("research/lab_loop/generated_grids")


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


def _completed_ids(state: dict[str, Any]) -> set[str]:
    return {str(item) for item in state.get("completed_hypothesis_ids", [])}


def _eligible_items(queue: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    completed = _completed_ids(state)
    items: list[dict[str, Any]] = []
    for item in queue.get("queue", []):
        if str(item.get("id", "")) in completed:
            continue
        if _is_terminal(item):
            continue
        if not is_executable_hypothesis(item):
            continue
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
    if str(item.get("promotion_level", "")).startswith("L3"):
        score += 150.0
    if generation > options.max_generation:
        score -= 400.0 + (generation - options.max_generation) * 100.0
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


def _select_reseed_source_entries(state: dict[str, Any], options: SupervisorOptions) -> list[dict[str, Any]]:
    latest = [entry for entry in _latest_epoch_entries(state) if _entry_has_reseed_evidence(entry)]
    latest_keys = {(entry.get("loop_number"), entry.get("hypothesis_id")) for entry in latest}
    archive = [
        entry
        for entry in state.get("loop_history", [])
        if _entry_has_reseed_evidence(entry)
        and (entry.get("loop_number"), entry.get("hypothesis_id")) not in latest_keys
    ]
    latest = sorted(latest, key=_entry_reseed_score, reverse=True)
    archive = sorted(archive, key=_entry_reseed_score, reverse=True)
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[Any, Any]] = set()
    root_counts: dict[str, int] = {}

    def add_entry(entry: dict[str, Any]) -> bool:
        if len(selected) >= options.max_reseed_per_epoch:
            return False
        key = (entry.get("loop_number"), entry.get("hypothesis_id"))
        if key in selected_keys:
            return False
        root = _item_root({"id": entry.get("hypothesis_id", "")})
        if root_counts.get(root, 0) >= options.max_same_root_per_epoch:
            return False
        selected.append(entry)
        selected_keys.add(key)
        root_counts[root] = root_counts.get(root, 0) + 1
        return True

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

        parent_root = _item_root({"id": parent_id})
        loop_number = int(entry.get("loop_number", 0) or 0)
        reseed_round = int(state.get("last_completed_loop", 0) or 0)
        generation = int(parent.get("generation", entry.get("generation", 0)) or 0) + 1
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
        child = {
            "id": child_id,
            "track": parent.get("track") or ("warning" if direction == "negative" else "bullish_setup"),
            "status": "new",
            "promotion_level": "L1_encoded",
            "priority": reseeded,
            "parent_id": parent_id,
            "generation": generation,
            "created_from": "meta_supervisor_reseed",
            "research_gate_stage": "reseed",
            "source": str(grid_path),
            "hypothesis": f"Supervisor reseed from latest strict/useful evidence in {parent_id}.",
            "measurable_primitives": list(parent.get("measurable_primitives", [])) + ["supervisor_reseed"],
            "expected_outcome": "negative_forward_relative_return"
            if direction == "negative"
            else "positive_forward_relative_return",
            "next_action": "Run as a bounded reseed because the runtime queue exhausted runnable evidence.",
            "supervisor_priority_reason": "reseeded from latest strict/useful evidence after queue exhaustion",
        }
        queue.setdefault("queue", []).append(child)
        existing_ids.add(child_id)
        actions.append(f"reseeded {child_id} from {parent_id}")
        reseeded += 1
    return actions


def _pick_epoch_slots(
    eligible: list[dict[str, Any]],
    *,
    promoted_roots: set[str],
    recent_tracks: dict[str, int],
    options: SupervisorOptions,
) -> list[dict[str, Any]]:
    root_counts: dict[str, int] = {}
    scores = {
        str(item.get("id", "")): _score_item(
            item,
            promoted_roots=promoted_roots,
            recent_tracks=recent_tracks,
            root_counts=root_counts,
            options=options,
        )
        for item in eligible
    }
    chosen: list[dict[str, Any]] = []
    chosen_ids: set[str] = set()

    def add_from(candidates: list[dict[str, Any]], slots: int) -> None:
        for candidate in _stable_sorted(candidates, scores):
            if len(chosen) >= options.epoch_size or slots <= 0:
                return
            candidate_id = str(candidate.get("id", ""))
            root = _item_root(candidate)
            if candidate_id in chosen_ids:
                continue
            if root_counts.get(root, 0) >= options.max_same_root_per_epoch:
                continue
            chosen.append(candidate)
            chosen_ids.add(candidate_id)
            root_counts[root] = root_counts.get(root, 0) + 1
            slots -= 1

    validation_slots = max(1, math.ceil(options.epoch_size * options.validation_share))
    validation = [item for item in eligible if str(item.get("research_gate_stage", "")) == "validation"]
    add_from(validation, validation_slots)

    bullish = [item for item in eligible if str(item.get("track", "")) == "bullish_setup"]
    bullish_floor = min(len(bullish), math.ceil(options.epoch_size * options.min_bullish_share))
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
        if generation > options.max_generation and str(item.get("research_gate_stage", "")) != "validation":
            patch.append(
                {
                    "type": "cool",
                    "hypothesis_id": item.get("id"),
                    "old_priority": _item_priority(item),
                    "new_priority": _item_priority(item) + 200,
                    "reason": f"generation {generation} exceeds supervisor max_generation={options.max_generation}",
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
    eligible = _eligible_items(queue, state)
    slots = _pick_epoch_slots(
        eligible,
        promoted_roots=promoted_roots,
        recent_tracks=recent_tracks,
        options=options,
    )
    queue_patch = [
        *_queue_patch_for_slots(slots),
        *_queue_patch_for_caps(eligible, slots, options=options),
    ]
    concept_decisions = []
    concepts = scoreboard.get("concepts", {}) if isinstance(scoreboard.get("concepts", {}), dict) else {}
    for decision in decisions:
        concept_id = str(decision.get("concept_id", ""))
        concept = concepts.get(concept_id, {})
        strict = int(concept.get("strict_survivors", 0) or 0) if isinstance(concept, dict) else 0
        clusters = int(concept.get("event_clusters", 0) or 0) if isinstance(concept, dict) else 0
        branch_action = str(decision.get("decision", ""))
        if branch_action == "promote":
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
                "reason": decision.get("reason", ""),
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
        "objective": "validate_survivors_balance_tracks_cap_lineages",
        "policy": {
            "epoch_size": options.epoch_size,
            "max_generation": options.max_generation,
            "max_same_root_per_epoch": options.max_same_root_per_epoch,
            "min_bullish_share": options.min_bullish_share,
            "validation_share": options.validation_share,
        },
        "inputs": {
            "state_path": str(options.state_path),
            "runtime_queue_path": str(options.runtime_queue_path),
            "concept_scoreboard_path": str(options.concept_scoreboard_path),
            "epoch_dir": str(epoch_dir),
            "eligible_hypotheses": len(eligible),
            "recent_tracks": recent_tracks,
        },
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
        if patch_type in {"schedule", "cool"}:
            item["priority"] = int(patch.get("new_priority", item.get("priority", 999)))
            item["last_supervised_at"] = decision.get("generated_at")
            item["supervisor_action"] = patch_type
            item["supervisor_priority_reason"] = patch.get("reason", "")
            if "slot" in patch:
                item["supervisor_next_epoch_slot"] = int(patch["slot"])
            actions.append(f"{patch_type} {hypothesis_id} priority {patch.get('old_priority')}->{item['priority']}")
        elif patch_type == "tag":
            item["last_supervised_at"] = decision.get("generated_at")
            item["supervisor_action"] = "defer"
            item["supervisor_priority_reason"] = patch.get("reason", "")
            actions.append(f"tagged {hypothesis_id}: {patch.get('reason', '')}")
    return actions


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
    for concept in decision.get("concept_decisions", []):
        concept_id = str(concept.get("concept_id", ""))
        source = scoreboard_concepts.get(concept_id, {}) if isinstance(scoreboard_concepts, dict) else {}
        prior = concepts.get(concept_id, {})
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
        }
        if reseed_actions and state.get("status") == "completed_no_runnable_hypotheses":
            state["status"] = "completed"
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
        print(
            f"Supervised epoch {completed_epochs}/{epochs}: loops {before + 1}-{after}, "
            f"status={state.get('status')}, reseeded={reseeded}",
            flush=True,
        )
        post_state = load_lab_state(epoch_lab_options.state_path)
        post_queue = load_lab_queue(epoch_lab_options.runtime_queue_path)
        has_runnable_after_supervision = bool(_eligible_items(post_queue, post_state))
        if after <= int(before or 0):
            if not has_runnable_after_supervision:
                break
            continue
        if state.get("status") == "completed_no_runnable_hypotheses" and not has_runnable_after_supervision:
            break
    state = load_lab_state(lab_options.state_path)
    state["supervised_epochs_completed"] = completed_epochs
    atomic_write_json(lab_options.state_path, state)
    return state
