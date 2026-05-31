from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .lab_director import (
    DEFAULT_DIRECTOR_GRID_DIR,
    DEFAULT_DIRECTOR_QUEUE_PATH,
    DEFAULT_DIRECTOR_REPORT_ROOT,
    LabDirectorOptions,
    run_director_plan_next,
)
from .lab_loop import (
    BULLISH_POSITIVE_OBJECTIVE,
    DEFAULT_CONCEPT_SCOREBOARD_PATH,
    DEFAULT_QUEUE_PATH,
    DEFAULT_REPORT_ROOT,
    DEFAULT_RUNTIME_QUEUE_PATH,
    DEFAULT_STATE_PATH,
    LabLoopOptions,
    atomic_write_json,
    atomic_write_text,
    atomic_write_yaml,
    data_fingerprint,
    git_commit,
    load_lab_state,
)
from .lab_supervisor import (
    DEFAULT_EVIDENCE_LEDGER_PATH,
    DEFAULT_SUPERVISOR_POLICY_PATH,
    SupervisorOptions,
    run_supervised_epochs,
)
from .meta_research import DEFAULT_META_REPORT_ROOT, LabMetaOptions, run_meta_from_director_result


LAB_OPS_MANIFEST_MODEL = "riskflow_lab_ops_run_manifest_v0"
LAB_OPS_STATUS_MODEL = "riskflow_lab_ops_latest_status_v0"
LAB_OPS_CHECKPOINT_MODEL = "riskflow_lab_ops_checkpoint_v0"
LAB_OPS_REPORT_ROOT = Path("reports/lab_ops")
LAB_OPS_RUNTIME_ROOT = Path("research/lab_loop/autonomous_runs")


@dataclass(frozen=True)
class LabOpsOptions:
    objective: str = BULLISH_POSITIVE_OBJECTIVE
    run_id: str | None = None
    queue_path: Path = DEFAULT_DIRECTOR_QUEUE_PATH
    config_path: Path = Path("configs/meme_universe.yaml")
    data_dir: Path = Path("data/raw")
    timeframes: tuple[str, ...] = ("1d", "12h", "4h", "1h")
    max_epochs: int = 50
    epoch_size: int = 5
    director_checkpoint_epochs: int = 2
    max_hours: float | None = None
    min_sample_size: int = 20
    entry_lag_bars: int = 1
    cooldown_bars: int | None = None
    strict_referee: bool = True
    strict_null_iterations: int = 300
    strict_random_seed: int = 29
    checkpoint_interval: int = 5
    max_errors: int = 10
    max_generated_artifact_mb: int = 5000
    apply: bool = False
    resume: bool = False
    dry_run: bool = False
    source_root: Path = Path(".")
    report_root: Path = LAB_OPS_REPORT_ROOT
    runtime_root: Path = LAB_OPS_RUNTIME_ROOT
    supervisor_policy_path: Path = DEFAULT_SUPERVISOR_POLICY_PATH
    max_new_hypotheses: int = 30


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_run_id(objective: str = BULLISH_POSITIVE_OBJECTIVE) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = "".join(ch if ch.isalnum() else "_" for ch in objective.lower()).strip("_")
    return f"auto_{stamp}_{slug or 'lab'}"


def resolve_run_id(options: LabOpsOptions) -> str:
    return options.run_id or make_run_id(options.objective)


def run_dir(options: LabOpsOptions, run_id: str) -> Path:
    return options.report_root / run_id


def runtime_dir(options: LabOpsOptions, run_id: str) -> Path:
    return options.runtime_root / run_id


def _runtime_paths(options: LabOpsOptions, run_id: str) -> dict[str, Path]:
    root = runtime_dir(options, run_id)
    return {
        "root": root,
        "runtime_queue": root / "runtime_queue.yaml",
        "state": root / "lab_state.json",
        "concept_scoreboard": root / "concept_scoreboard.yaml",
        "evidence_ledger": root / "evidence_ledger.yaml",
        "director_queue": root / "director_candidate_queue.yaml",
        "generated_lab_grids": root / "generated_grids" / "lab_loop",
        "generated_director_grids": root / "generated_grids" / "director",
        "stop_request": root / "stop.request",
        "pause_request": root / "pause.request",
        "lock": root / "lab_ops.lock",
        "lab_loop_lock": root / "lab_loop.lock",
    }


def _choose_seed_queue(path: Path) -> Path:
    if path.exists():
        return path
    if DEFAULT_QUEUE_PATH.exists():
        return DEFAULT_QUEUE_PATH
    return path


def build_run_manifest(options: LabOpsOptions, run_id: str, *, status: str = "planned") -> dict[str, Any]:
    paths = _runtime_paths(options, run_id)
    seed_queue = _choose_seed_queue(options.queue_path)
    try:
        fingerprint = data_fingerprint(options.data_dir, tuple(options.timeframes))
    except Exception:
        fingerprint = ""
    return {
        "model": LAB_OPS_MANIFEST_MODEL,
        "run_id": run_id,
        "objective": options.objective,
        "created_at": utc_now_iso(),
        "started_at": None,
        "completed_at": None,
        "git_commit": git_commit(),
        "seed_queue_path": str(seed_queue),
        "runtime_queue_path": str(paths["runtime_queue"]),
        "state_path": str(paths["state"]),
        "max_epochs": options.max_epochs,
        "epoch_size": options.epoch_size,
        "max_hours": options.max_hours,
        "max_loops": options.max_epochs * options.epoch_size,
        "max_errors": options.max_errors,
        "director_checkpoint_epochs": options.director_checkpoint_epochs,
        "checkpoint_interval": options.checkpoint_interval,
        "strict_referee": options.strict_referee,
        "timeframes": list(options.timeframes),
        "data_fingerprint": fingerprint,
        "apply_enabled": options.apply,
        "commit_policy": "never_auto_commit",
        "status": status,
    }


def _write_manifest(options: LabOpsOptions, run_id: str, manifest: dict[str, Any]) -> Path:
    path = run_dir(options, run_id) / "run_manifest.yaml"
    atomic_write_yaml(path, manifest)
    return path


def _read_manifest(options: LabOpsOptions, run_id: str) -> dict[str, Any]:
    path = run_dir(options, run_id) / "run_manifest.yaml"
    if not path.exists():
        return {}
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _append_journal(options: LabOpsOptions, run_id: str, event_type: str, payload: dict[str, Any] | None = None) -> None:
    path = run_dir(options, run_id) / "run_journal.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": utc_now_iso(), "event": event_type, "payload": payload or {}}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_status(options: LabOpsOptions, run_id: str, status: dict[str, Any]) -> Path:
    path = run_dir(options, run_id) / "latest_status.yaml"
    status = {"model": LAB_OPS_STATUS_MODEL, "generated_at": utc_now_iso(), **status}
    atomic_write_yaml(path, status)
    return path


def _artifact_health(root: Path) -> dict[str, Any]:
    files = [path for path in root.rglob("*") if path.is_file()]
    total_bytes = sum(path.stat().st_size for path in files)
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / 1_000_000, 3),
    }


def _write_budget_status(options: LabOpsOptions, run_id: str, *, completed_epochs: int, started_at: float) -> dict[str, Any]:
    elapsed_hours = (time.monotonic() - started_at) / 3600.0
    budget = {
        "run_id": run_id,
        "completed_epochs": completed_epochs,
        "max_epochs": options.max_epochs,
        "elapsed_hours": round(elapsed_hours, 4),
        "max_hours": options.max_hours,
        "epoch_budget_reached": completed_epochs >= options.max_epochs,
        "hour_budget_reached": options.max_hours is not None and elapsed_hours >= options.max_hours,
    }
    atomic_write_yaml(run_dir(options, run_id) / "budget_status.yaml", budget)
    return budget


class _OpsLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.fd: int | None = None

    def __enter__(self) -> "_OpsLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"lab-ops lock already exists at {self.path}") from exc
        os.write(self.fd, utc_now_iso().encode("utf-8"))
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def run_lab_ops_plan(options: LabOpsOptions) -> dict[str, Any]:
    run_id = resolve_run_id(options)
    manifest = build_run_manifest(options, run_id, status="planned")
    manifest_path = _write_manifest(options, run_id, manifest)
    status_path = _write_status(
        options,
        run_id,
        {
            "run_id": run_id,
            "status": "planned",
            "manifest": str(manifest_path),
            "runtime_root": str(runtime_dir(options, run_id)),
            "report_root": str(run_dir(options, run_id)),
        },
    )
    return {"run_id": run_id, "manifest": manifest, "paths": {"manifest": manifest_path, "status": status_path}}


def _director_options_for_run(options: LabOpsOptions, run_id: str) -> LabDirectorOptions:
    paths = _runtime_paths(options, run_id)
    return LabDirectorOptions(
        state_path=paths["state"],
        runtime_queue_path=paths["runtime_queue"],
        concept_scoreboard_path=paths["concept_scoreboard"],
        evidence_ledger_path=paths["evidence_ledger"],
        report_root=run_dir(options, run_id) / "lab_loop",
        director_report_root=run_dir(options, run_id) / "director",
        output_queue_path=paths["director_queue"],
        generated_grid_dir=paths["generated_director_grids"],
        objective=options.objective,
        max_new_hypotheses=options.max_new_hypotheses,
        source_root=options.source_root,
        apply=options.apply,
        apply_to_runtime=options.apply,
    )


def _lab_options_for_run(options: LabOpsOptions, run_id: str, *, resume: bool) -> LabLoopOptions:
    paths = _runtime_paths(options, run_id)
    return LabLoopOptions(
        queue_path=_choose_seed_queue(options.queue_path),
        runtime_queue_path=paths["runtime_queue"],
        state_path=paths["state"],
        lock_path=paths["lab_loop_lock"],
        report_root=run_dir(options, run_id) / "lab_loop",
        generated_grid_dir=paths["generated_lab_grids"],
        concept_scoreboard_path=paths["concept_scoreboard"],
        config_path=options.config_path,
        data_dir=options.data_dir,
        timeframes=tuple(options.timeframes),
        max_loops=options.epoch_size,
        max_hours=options.max_hours,
        min_sample_size=options.min_sample_size,
        entry_lag_bars=options.entry_lag_bars,
        cooldown_bars=options.cooldown_bars,
        strict_referee=options.strict_referee,
        strict_null_iterations=options.strict_null_iterations,
        strict_random_seed=options.strict_random_seed,
        checkpoint_interval=options.checkpoint_interval,
        resume=resume,
        dry_run=options.dry_run,
        auto_refine=False,
        auto_gate_followups=True,
        objective=options.objective,
    )


def _supervisor_options_for_run(options: LabOpsOptions, run_id: str) -> SupervisorOptions:
    paths = _runtime_paths(options, run_id)
    return SupervisorOptions(
        state_path=paths["state"],
        runtime_queue_path=paths["runtime_queue"],
        concept_scoreboard_path=paths["concept_scoreboard"],
        evidence_ledger_path=paths["evidence_ledger"],
        policy_path=options.supervisor_policy_path,
        epoch_size=options.epoch_size,
        apply=True,
        objective=options.objective,
    )


def _write_checkpoint(
    options: LabOpsOptions,
    run_id: str,
    *,
    block_number: int,
    state: dict[str, Any],
    director_result: dict[str, Any],
    meta_result: dict[str, Any],
) -> Path:
    checkpoint = {
        "model": LAB_OPS_CHECKPOINT_MODEL,
        "generated_at": utc_now_iso(),
        "run_id": run_id,
        "block_number": block_number,
        "state": state,
        "director": {
            "research_mode": director_result.get("plan", {}).get("research_mode"),
            "audit_passed": director_result.get("audit", {}).get("passed"),
            "runtime_added": director_result.get("runtime_added", 0),
            "report": str(director_result.get("paths", {}).get("report", "")),
        },
        "meta": {
            "overall_process_score": meta_result.get("scorecard", {}).get("overall_process_score"),
            "intervention_type": (meta_result.get("intervention") or {}).get("intervention_type"),
            "audit_passed": (meta_result.get("audit") or {}).get("passed"),
            "report": str(meta_result.get("paths", {}).get("report", "")),
        },
    }
    path = run_dir(options, run_id) / "checkpoints" / f"checkpoint_{block_number:04d}.yaml"
    atomic_write_yaml(path, checkpoint)
    return path


def run_lab_ops_run(options: LabOpsOptions) -> dict[str, Any]:
    if not options.apply:
        raise ValueError("lab-ops run requires --apply; use lab-ops plan for non-mutating planning")
    run_id = resolve_run_id(options)
    paths = _runtime_paths(options, run_id)
    paths["root"].mkdir(parents=True, exist_ok=True)
    run_dir(options, run_id).mkdir(parents=True, exist_ok=True)

    manifest = _read_manifest(options, run_id) if options.resume else {}
    if not manifest:
        manifest = build_run_manifest(options, run_id, status="running")
    manifest["status"] = "running"
    manifest["started_at"] = manifest.get("started_at") or utc_now_iso()
    _write_manifest(options, run_id, manifest)
    _append_journal(options, run_id, "run_started", {"resume": options.resume})

    completed_epochs = 0
    completed_blocks = 0
    errors = 0
    terminal_status = "completed"
    stop_reason = ""
    started_at = time.monotonic()
    last_state: dict[str, Any] = {}
    last_meta: dict[str, Any] = {}

    try:
        with _OpsLock(paths["lock"]):
            while completed_epochs < options.max_epochs:
                if paths["stop_request"].exists():
                    terminal_status = "stopped"
                    stop_reason = "user_stop_requested"
                    break
                budget = _write_budget_status(options, run_id, completed_epochs=completed_epochs, started_at=started_at)
                if budget["hour_budget_reached"]:
                    terminal_status = "stopped"
                    stop_reason = "budget_hours_reached"
                    break
                block_epochs = min(max(1, options.director_checkpoint_epochs), options.max_epochs - completed_epochs)
                completed_blocks += 1
                _append_journal(options, run_id, "epoch_block_started", {"block": completed_blocks, "epochs": block_epochs})
                lab_options = _lab_options_for_run(options, run_id, resume=options.resume or completed_epochs > 0)
                supervisor_options = _supervisor_options_for_run(options, run_id)
                last_state = run_supervised_epochs(lab_options, supervisor_options, epochs=block_epochs, epoch_size=options.epoch_size)
                completed_epochs += block_epochs
                _append_journal(
                    options,
                    run_id,
                    "epoch_block_completed",
                    {
                        "block": completed_blocks,
                        "completed_epochs": completed_epochs,
                        "status": last_state.get("status"),
                        "last_completed_loop": last_state.get("last_completed_loop"),
                    },
                )

                director_options = _director_options_for_run(options, run_id)
                _append_journal(options, run_id, "director_started", {"block": completed_blocks})
                director_result = run_director_plan_next(director_options)
                _append_journal(
                    options,
                    run_id,
                    "director_completed",
                    {
                        "block": completed_blocks,
                        "audit_passed": director_result.get("audit", {}).get("passed"),
                        "runtime_added": director_result.get("runtime_added", 0),
                    },
                )
                meta_options = LabMetaOptions(
                    director_options=director_options,
                    meta_report_root=run_dir(options, run_id) / "meta",
                    session_id=f"block_{completed_blocks:04d}",
                )
                last_meta = run_meta_from_director_result(meta_options, director_result, include_intervention=True)
                _append_journal(
                    options,
                    run_id,
                    "process_score_updated",
                    {
                        "block": completed_blocks,
                        "score": last_meta.get("scorecard", {}).get("overall_process_score"),
                        "intervention": (last_meta.get("intervention") or {}).get("intervention_type"),
                    },
                )
                checkpoint_path = _write_checkpoint(
                    options,
                    run_id,
                    block_number=completed_blocks,
                    state=last_state,
                    director_result=director_result,
                    meta_result=last_meta,
                )
                artifact_health = _artifact_health(run_dir(options, run_id))
                _write_status(
                    options,
                    run_id,
                    {
                        "run_id": run_id,
                        "status": "running",
                        "completed_epochs": completed_epochs,
                        "completed_blocks": completed_blocks,
                        "last_completed_loop": last_state.get("last_completed_loop"),
                        "last_checkpoint": str(checkpoint_path),
                        "artifact_health": artifact_health,
                    },
                )
                if artifact_health["total_mb"] > options.max_generated_artifact_mb:
                    terminal_status = "stopped"
                    stop_reason = "artifact_hygiene_required"
                    break
                if not director_result.get("audit", {}).get("passed"):
                    terminal_status = "failed"
                    stop_reason = "director_audit_failed"
                    break
                if not (last_meta.get("audit") or {}).get("passed"):
                    terminal_status = "failed"
                    stop_reason = "meta_audit_failed"
                    break
                intervention_type = (last_meta.get("intervention") or {}).get("intervention_type")
                if intervention_type in {
                    "request_visual_review",
                    "request_fresh_data",
                    "process_policy_change",
                    "stop_research_saturated",
                }:
                    terminal_status = "stopped"
                    stop_reason = str(intervention_type)
                    break
                if last_state.get("requires_new_candidate_queue") and not director_result.get("runtime_added"):
                    terminal_status = "stopped"
                    stop_reason = "no_runnable_and_no_valid_director_plan"
                    break
    except Exception as exc:
        errors += 1
        terminal_status = "failed"
        stop_reason = f"exception:{type(exc).__name__}"
        _append_journal(options, run_id, "failure_recorded", {"error": str(exc), "type": type(exc).__name__})
        atomic_write_yaml(
            run_dir(options, run_id) / "recovery_plan.yaml",
            {
                "run_id": run_id,
                "generated_at": utc_now_iso(),
                "reason": stop_reason,
                "message": str(exc),
                "recommended_action": "Inspect latest_status.yaml, run_journal.jsonl, runtime queue, and state before resuming.",
            },
        )
        if errors > options.max_errors:
            stop_reason = "budget_errors_reached"

    manifest["status"] = terminal_status
    manifest["completed_at"] = utc_now_iso()
    manifest["completed_epochs"] = completed_epochs
    manifest["completed_blocks"] = completed_blocks
    manifest["stop_reason"] = stop_reason
    _write_manifest(options, run_id, manifest)
    stop_payload = {"run_id": run_id, "status": terminal_status, "reason": stop_reason, "generated_at": utc_now_iso()}
    atomic_write_yaml(run_dir(options, run_id) / "stop_reason.yaml", stop_payload)
    _write_status(
        options,
        run_id,
        {
            "run_id": run_id,
            "status": terminal_status,
            "stop_reason": stop_reason,
            "completed_epochs": completed_epochs,
            "completed_blocks": completed_blocks,
            "last_completed_loop": last_state.get("last_completed_loop"),
            "latest_process_score": last_meta.get("scorecard", {}).get("overall_process_score"),
            "latest_intervention": (last_meta.get("intervention") or {}).get("intervention_type"),
        },
    )
    _append_journal(options, run_id, "run_completed", stop_payload)
    report_path = run_lab_ops_report(options, run_id=run_id)["paths"]["report"]
    return {
        "run_id": run_id,
        "status": terminal_status,
        "stop_reason": stop_reason,
        "completed_epochs": completed_epochs,
        "completed_blocks": completed_blocks,
        "paths": {
            "manifest": run_dir(options, run_id) / "run_manifest.yaml",
            "status": run_dir(options, run_id) / "latest_status.yaml",
            "report": report_path,
        },
    }


def run_lab_ops_stop(options: LabOpsOptions, *, run_id: str, reason: str) -> dict[str, Any]:
    paths = _runtime_paths(options, run_id)
    paths["root"].mkdir(parents=True, exist_ok=True)
    atomic_write_text(paths["stop_request"], reason.strip() + "\n")
    _append_journal(options, run_id, "stop_requested", {"reason": reason})
    return {"run_id": run_id, "stop_request": paths["stop_request"], "reason": reason}


def run_lab_ops_status(options: LabOpsOptions, *, run_id: str) -> dict[str, Any]:
    status_path = run_dir(options, run_id) / "latest_status.yaml"
    manifest_path = run_dir(options, run_id) / "run_manifest.yaml"
    return {
        "run_id": run_id,
        "status_path": status_path,
        "manifest_path": manifest_path,
        "status_text": status_path.read_text(encoding="utf-8") if status_path.exists() else "No lab-ops status found.",
        "manifest_text": manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else "",
    }


def run_lab_ops_report(options: LabOpsOptions, *, run_id: str) -> dict[str, Any]:
    root = run_dir(options, run_id)
    manifest = _read_manifest(options, run_id)
    status = (root / "latest_status.yaml").read_text(encoding="utf-8") if (root / "latest_status.yaml").exists() else ""
    journal_path = root / "run_journal.jsonl"
    journal_events: list[dict[str, Any]] = []
    if journal_path.exists():
        for line in journal_path.read_text(encoding="utf-8").splitlines()[-50:]:
            try:
                journal_events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    checkpoints = sorted((root / "checkpoints").glob("checkpoint_*.yaml")) if (root / "checkpoints").exists() else []
    lines = [
        "# Riskflow Lab Ops Final Report",
        "",
        f"Run: {run_id}",
        f"Status: {manifest.get('status', 'unknown')}",
        f"Stop reason: {manifest.get('stop_reason', '')}",
        f"Objective: {manifest.get('objective', options.objective)}",
        f"Completed epochs: {manifest.get('completed_epochs', 0)}",
        f"Completed blocks: {manifest.get('completed_blocks', 0)}",
        f"Checkpoints: {len(checkpoints)}",
        "",
        "## Latest Status",
        "",
        "```yaml",
        status.strip(),
        "```",
        "",
        "## Recent Events",
        "",
    ]
    if not journal_events:
        lines.append("- No journal events recorded.")
    for event in journal_events[-20:]:
        lines.append(f"- {event.get('at')} {event.get('event')}: {event.get('payload')}")
    latest_meta_reports = sorted((root / "meta").glob("*/meta_research_report.md")) if (root / "meta").exists() else []
    if latest_meta_reports:
        lines.extend(["", "## Latest Meta Report", "", latest_meta_reports[-1].read_text(encoding="utf-8")])
    report_path = root / "reports" / "final_report.md"
    atomic_write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return {"run_id": run_id, "paths": {"report": report_path}, "manifest": manifest}
