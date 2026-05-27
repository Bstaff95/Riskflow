from __future__ import annotations

import pandas as pd

from riskflow.cli import main
from riskflow.signal_grammar import (
    GRAMMAR_EVENT_NAMES,
    GRAMMAR_FEATURE_COLUMNS,
    build_primitive_summary,
    build_review_plan,
    calculate_signal_grammar_features,
    detect_signal_grammar_events,
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


def _grammar_frame() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=36, freq="D")
    final_signal = pd.Series(
        [
            -2.15,
            -2.10,
            -2.08,
            -2.03,
            -2.00,
            -1.98,
            -1.95,
            -1.93,
            -1.90,
            -1.88,
            -1.45,
            -1.20,
            -0.80,
            -0.35,
            0.05,
            0.20,
            0.35,
            0.45,
            0.40,
            0.30,
            -0.10,
            0.25,
            0.45,
            0.65,
            0.80,
            1.70,
            1.80,
            1.40,
            1.10,
            0.80,
            0.50,
            0.20,
            -0.05,
            -0.20,
            -0.10,
            0.05,
        ],
        index=dates,
    )
    viscosity = pd.Series(
        [
            -1.75,
            -1.74,
            -1.73,
            -1.72,
            -1.71,
            -1.70,
            -1.69,
            -1.68,
            -1.67,
            -1.66,
            -1.62,
            -1.55,
            -1.40,
            -1.00,
            -0.40,
            -0.05,
            0.05,
            0.10,
            0.15,
            0.10,
            0.05,
            0.00,
            0.10,
            0.20,
            0.35,
            0.60,
            0.80,
            0.95,
            1.00,
            0.95,
            0.80,
            0.55,
            0.25,
            0.05,
            -0.02,
            -0.03,
        ],
        index=dates,
    )
    target = pd.Series(
        [
            100,
            99,
            98,
            97,
            96,
            95,
            94,
            93,
            92,
            91,
            92,
            93,
            94,
            95,
            96,
            98,
            100,
            102,
            104,
            106,
            105,
            107,
            108,
            109,
            111,
            113,
            115,
            116,
            117,
            118,
            119,
            120,
            121,
            122,
            121,
            123,
        ],
        index=dates,
        dtype=float,
    )
    return pd.DataFrame(
        {
            "target": target,
            "benchmark": 100.0,
            "final_signal": final_signal,
            "viscosity": viscosity,
            "gradient_driver": final_signal,
            "compression_score": 75.0,
        },
        index=dates,
    )


def test_calculate_signal_grammar_features_builds_sidecars_and_events() -> None:
    features = calculate_signal_grammar_features(_grammar_frame())

    assert list(features.columns) == GRAMMAR_FEATURE_COLUMNS
    assert set(features["grammar_model"].dropna()) == {"signal_grammar_sidecar_v0"}
    assert features["grammar_pressure_area_balance_20"].notna().any()
    assert features["grammar_minus_1_5_reclaim_after_coil_event"].any()
    assert features["grammar_zero_reclaim_confirmation_event"].any()
    assert features["grammar_hot_leader_reset_warning_event"].any()


def test_detect_signal_grammar_events_exposes_registered_candidate_masks() -> None:
    frame = _grammar_frame().join(calculate_signal_grammar_features(_grammar_frame()))

    events = detect_signal_grammar_events(frame)

    assert set(events) == set(GRAMMAR_EVENT_NAMES)
    assert events["grammar_minus_1_5_reclaim_after_coil_v0"].any()
    assert events["grammar_zero_reclaim_confirmation_v0"].any()
    assert events["grammar_hot_leader_reset_warning_v0"].any()
