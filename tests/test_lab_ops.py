from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from riskflow.lab_ops import (
    LabOpsOptions,
    run_lab_ops_plan,
    run_lab_ops_report,
    run_lab_ops_run,
    run_lab_ops_stop,
)


def _ops_options(tmp_path: Path, *, run_id: str = "ops_test", apply: bool = False) -> LabOpsOptions:
    queue = tmp_path / "research" / "seed_queue.yaml"
    queue.parent.mkdir(parents=True)
    queue.write_text(
        yaml.safe_dump(
            {
                "model": "riskflow_lab_loop_hypothesis_queue_v0",
                "queue": [],
            }
        ),
        encoding="utf-8",
    )
    return LabOpsOptions(
        run_id=run_id,
        queue_path=queue,
        report_root=tmp_path / "reports" / "lab_ops",
        runtime_root=tmp_path / "research" / "lab_loop" / "autonomous_runs",
        max_epochs=2,
        epoch_size=5,
        director_checkpoint_epochs=1,
        apply=apply,
    )


def test_lab_ops_plan_writes_manifest_without_runtime_queue(tmp_path: Path) -> None:
    options = _ops_options(tmp_path)

    result = run_lab_ops_plan(options)

    assert result["run_id"] == "ops_test"
    assert result["paths"]["manifest"].exists()
    manifest = yaml.safe_load(result["paths"]["manifest"].read_text(encoding="utf-8"))
    assert manifest["status"] == "planned"
    assert not (tmp_path / "research" / "lab_loop" / "autonomous_runs" / "ops_test" / "runtime_queue.yaml").exists()


def test_lab_ops_stop_writes_stop_request(tmp_path: Path) -> None:
    options = _ops_options(tmp_path)

    result = run_lab_ops_stop(options, run_id="ops_test", reason="user_requested")

    assert result["stop_request"].exists()
    assert result["stop_request"].read_text(encoding="utf-8").strip() == "user_requested"


def test_lab_ops_run_requires_apply(tmp_path: Path) -> None:
    options = _ops_options(tmp_path, apply=False)

    with pytest.raises(ValueError, match="requires --apply"):
        run_lab_ops_run(options)


def test_lab_ops_report_writes_final_report(tmp_path: Path) -> None:
    options = _ops_options(tmp_path)
    run_lab_ops_plan(options)

    result = run_lab_ops_report(options, run_id="ops_test")

    assert result["paths"]["report"].exists()
    assert "Riskflow Lab Ops Final Report" in result["paths"]["report"].read_text(encoding="utf-8")
