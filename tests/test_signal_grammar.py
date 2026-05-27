from __future__ import annotations

import pandas as pd

from riskflow.cli import main
from riskflow.signal_grammar import (
    build_primitive_summary,
    build_review_plan,
    export_grammar_lab,
    load_primitive_registry,
)


def _registry(tmp_path):
    path = tmp_path / "registry.yaml"
    path.write_text(
        """
model: riskflow_signal_grammar_primitives_v0
primitive_families:
  pressure_acceptance:
    description: Time and signed area around viscosity.
    candidate_primitives:
      - time_above_viscosity
      - pressure_area_balance
    first_tests:
      - Does pressure acceptance improve outcomes?
  failed_weakness:
    description: Weakness stops accelerating.
    candidate_primitives:
      - relative_weakness_fails_to_accelerate
review_targets:
  clean_bullish_hits: 2
  bullish_false_positives: 1
  missed_breakouts: 1
  bearish_or_weakness_examples: 1
  noisy_or_ambiguous_edge_cases: 1
""",
        encoding="utf-8",
    )
    return path


def _observations() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "observation_id": "A",
                "symbol": "TROLL",
                "tags": "time_above_viscosity,viscosity_reclaim,fast_clean_hit",
                "outcome_label": "fast_clean_hit",
                "human_label": "unreviewed",
            },
            {
                "observation_id": "B",
                "symbol": "TRUMP",
                "tags": "false_positive,failed_breakout",
                "outcome_label": "false_positive",
                "human_label": "unreviewed",
            },
        ]
    )


def test_load_primitive_registry_validates_model(tmp_path) -> None:
    registry = load_primitive_registry(_registry(tmp_path))

    assert registry["model"] == "riskflow_signal_grammar_primitives_v0"
    assert "pressure_acceptance" in registry["primitive_families"]


def test_build_primitive_summary_counts_observation_tags(tmp_path) -> None:
    registry = load_primitive_registry(_registry(tmp_path))
    summary = build_primitive_summary(registry, _observations())

    time_row = summary[summary["primitive"] == "time_above_viscosity"].iloc[0]
    area_row = summary[summary["primitive"] == "pressure_area_balance"].iloc[0]
    assert time_row["observation_count"] == 1
    assert time_row["evidence_status"] == "observed_needs_testing"
    assert area_row["observation_count"] == 0
    assert area_row["evidence_status"] == "needs_observations"


def test_build_review_plan_reports_targets_and_missing_primitives(tmp_path) -> None:
    registry = load_primitive_registry(_registry(tmp_path))
    plan = build_review_plan(registry, _observations())

    assert "Signal Grammar Lab Review Plan" in plan
    assert "`clean_bullish_hits` | 1 | 2 | 1" in plan
    assert "`bullish_false_positives` | 1 | 1 | 0" in plan
    assert "`pressure_area_balance`" in plan


def test_export_grammar_lab_writes_outputs(tmp_path) -> None:
    registry_path = _registry(tmp_path)
    observations_csv = tmp_path / "observations.csv"
    _observations().to_csv(observations_csv, index=False)

    paths = export_grammar_lab(
        registry_path=registry_path,
        observations_csv=observations_csv,
        output_dir=tmp_path / "reports" / "grammar_lab",
        obsidian_dir=tmp_path / "obsidian",
    )

    assert paths.primitive_summary_csv.exists()
    assert paths.review_plan_md.exists()
    assert paths.obsidian_note_md is not None
    assert paths.obsidian_note_md.exists()


def test_grammar_lab_cli_creates_outputs(tmp_path) -> None:
    registry_path = _registry(tmp_path)
    observations_csv = tmp_path / "observations.csv"
    _observations().to_csv(observations_csv, index=False)

    status = main(
        [
            "grammar-lab",
            "--registry",
            str(registry_path),
            "--observations-csv",
            str(observations_csv),
            "--output-dir",
            str(tmp_path / "reports" / "grammar_lab"),
            "--obsidian-dir",
            str(tmp_path / "obsidian"),
        ]
    )

    assert status == 0
    assert (tmp_path / "reports" / "grammar_lab" / "primitive_summary.csv").exists()
    assert (tmp_path / "obsidian" / "wiki" / "maps" / "Signal Grammar Lab.md").exists()
