from __future__ import annotations

import json

import pandas as pd

from riskflow.cli import main
from riskflow.observation_library import build_observation_records, export_observation_library


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "TROLL",
                "name": "Troll",
                "date": "2026-04-10 12:00:00",
                "timeframe": "4h",
                "benchmark": "MEME_BASKET_EX_TROLL",
                "event_name": "coil_viscosity_reclaim_v0",
                "forward_relative_return_3": 0.25,
                "forward_relative_return_7": 0.18,
                "forward_relative_return_14": 0.08,
                "forward_relative_return_30": 0.10,
                "final_signal": -0.35,
                "viscosity": -1.23,
                "relative_component": -0.41,
                "price_component": -0.18,
                "compression_score": 40.59,
                "state": "Weak",
                "setup_tags": "relative_strength_rising,viscosity_reclaim",
                "pattern_score": 74.0,
                "recent_viscosity_reclaim": True,
                "signal_zone": "below_zero",
                "image_path": "reports/visual_review/images/02_TROLL_20260410_1200.png",
                "notes": "selected by early indicator pattern",
            }
        ]
    )


def test_build_observation_records_adds_tags_and_ids(tmp_path) -> None:
    records = build_observation_records(_events(), source_path=tmp_path / "events.csv")

    assert records.loc[0, "observation_id"] == "TROLL_4h_20260410_1200_coil_viscosity_reclaim_v0"
    assert records.loc[0, "pattern_label"] == "coil_viscosity_reclaim_v0"
    assert records.loc[0, "review_status"] == "needs_human_review"
    assert "viscosity_reclaim" in records.loc[0, "tags"]
    assert records.loc[0, "outcome_label"] == "fast_clean_hit"


def test_export_observation_library_writes_records_and_obsidian_notes(tmp_path) -> None:
    events_csv = tmp_path / "events.csv"
    _events().to_csv(events_csv, index=False)

    paths = export_observation_library(
        events_csv,
        output_dir=tmp_path / "research" / "observations",
        obsidian_dir=tmp_path / "obsidian",
    )

    assert paths.records_jsonl.exists()
    assert paths.records_csv.exists()
    assert paths.schema_yaml.exists()
    assert paths.index_md.exists()
    assert (paths.cases_dir / "TROLL_4h_20260410_1200_coil_viscosity_reclaim_v0.md").exists()
    assert (paths.patterns_dir / "Coil Viscosity Reclaim v0.md").exists()
    assert (paths.concepts_dir / "Viscosity Reclaim.md").exists()

    first_record = json.loads(paths.records_jsonl.read_text(encoding="utf-8").splitlines()[0])
    assert first_record["symbol"] == "TROLL"
    assert first_record["human_label"] == "unreviewed"


def test_observation_library_cli_creates_outputs(tmp_path) -> None:
    events_csv = tmp_path / "events.csv"
    _events().to_csv(events_csv, index=False)

    status = main(
        [
            "observation-library",
            "--events-csv",
            str(events_csv),
            "--output-dir",
            str(tmp_path / "research" / "observations"),
            "--obsidian-dir",
            str(tmp_path / "obsidian"),
        ]
    )

    assert status == 0
    assert (tmp_path / "research" / "observations" / "observation_records.jsonl").exists()
    assert (tmp_path / "obsidian" / "wiki" / "Indicator Observation Library.md").exists()
