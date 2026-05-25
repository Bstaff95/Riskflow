from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from riskflow.cli import LEADERBOARD_COLUMNS, build_analysis_frames, build_leaderboard, main
from riskflow.config import AssetConfig, BenchmarkConfig, UniverseConfig
from riskflow.transition_registry import TRANSITION_RESEARCH_V0, get_transition_research_spec
from riskflow.transition_research import (
    CONDITIONED_COLUMNS,
    RECORD_COLUMNS,
    SUMMARY_COLUMNS,
    build_transition_research_records,
    run_transition_research,
    summarize_conditioned_transition_records,
    summarize_transition_research_records,
    transition_records_for_asset,
)


def _frame(states: list[str] | None = None, periods: int = 60) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    if states is None:
        states = (
            ["Compression"] * 5
            + ["Relative Accumulation"] * 6
            + ["Emerging Leader"] * 7
            + ["Confirmed Leader"] * 8
            + ["Breakdown"] * (periods - 26)
        )
    target = pd.Series(100.0 * np.cumprod(np.full(periods, 1.012)), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(np.full(periods, 1.004)), index=dates)
    return pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "state": states[:periods],
            "state_model": "state_model_v0",
            "final_signal": np.linspace(-1.0, 1.0, periods),
            "relative_component": np.linspace(-0.5, 1.0, periods),
            "viscosity": 0.0,
            "above_viscosity": [idx >= min(20, periods) for idx in range(periods)],
            "setup_readiness_score": np.linspace(10.0, 90.0, periods),
            "extension_risk_score": 10.0,
        },
        index=dates,
    )


def _universe() -> UniverseConfig:
    return UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(name="MEME_BASKET"),
        min_active_members=1,
        assets=[
            AssetConfig(symbol="AAA", name="AAA", sector="memes", subgroup="base_memes"),
            AssetConfig(symbol="BBB", name="BBB", sector="memes", subgroup="base_memes"),
        ],
    )


def _write_csv(path: Path, periods: int = 80, start: float = 100.0) -> None:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    lines = ["date,open,high,low,close,volume"]
    for idx, date in enumerate(dates):
        value = start + idx * 0.5
        lines.append(f"{date.date()},{value},{value * 1.02},{value * 0.98},{value},1000")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_transition_registry_accepts_known_and_rejects_unknown():
    spec = get_transition_research_spec(TRANSITION_RESEARCH_V0)

    assert spec.transition_model_id == TRANSITION_RESEARCH_V0
    with pytest.raises(KeyError):
        get_transition_research_spec("not_a_transition_model")


def test_transition_records_are_completed_state_runs_with_forward_returns():
    records = transition_records_for_asset("AAA", _frame(), entry_lag_bars=1)

    assert list(records.columns) == RECORD_COLUMNS
    assert len(records) == 4
    assert records.iloc[0]["from_state"] == "Compression"
    assert records.iloc[0]["to_state"] == "Relative Accumulation"
    assert records.iloc[0]["from_state_duration"] == 5
    assert records["forward_relative_return_14"].notna().any()


def test_same_state_continuation_is_excluded_from_transition_counts():
    states = ["Compression"] * 3 + ["Emerging Leader"] * 2 + ["Compression"] * 4
    records = transition_records_for_asset("AAA", _frame(states=states, periods=len(states)), entry_lag_bars=0)

    assert len(records) == 2
    assert set(zip(records["from_state"], records["to_state"])) == {
        ("Compression", "Emerging Leader"),
        ("Emerging Leader", "Compression"),
    }


def test_transition_summary_rates_and_wilson_intervals_are_bounded():
    summary, records, unconditional, conditioned = run_transition_research(
        _universe(),
        {"AAA": _frame(), "BBB": _frame()},
        min_sample_size=1,
    )

    assert list(summary.columns) == SUMMARY_COLUMNS
    assert list(unconditional["observed_transition_rate"].between(0.0, 1.0).unique()) == [True]
    assert (summary["wilson_80_lower"] <= summary["wilson_80_upper"]).all()
    assert summary["wilson_80_lower"].between(0.0, 1.0).all()
    assert summary["wilson_80_upper"].between(0.0, 1.0).all()
    assert not records.empty
    assert list(conditioned.columns) == CONDITIONED_COLUMNS


def test_low_sample_is_inconclusive_and_symbol_concentration_is_fragile():
    records = transition_records_for_asset("AAA", _frame())

    low_sample = summarize_transition_research_records(records, min_sample_size=999)
    assert set(low_sample["classification"]) == {"inconclusive"}

    concentrated = summarize_transition_research_records(records, min_sample_size=1)
    row = concentrated[(concentrated["from_state"] == "Compression") & (concentrated["to_state"] == "Relative Accumulation")].iloc[0]
    assert row["classification"] == "fragile"
    assert "one symbol" in row["notes"]


def test_cluster_concentration_is_fragile_when_sample_sufficient():
    records = pd.concat(
        [transition_records_for_asset(f"S{idx}", _frame(), entry_lag_bars=1).head(1) for idx in range(4)],
        ignore_index=True,
    )
    records["transition_date"] = pd.Timestamp("2024-01-05")
    records["event_cluster_id"] = "2024-01"

    summary = summarize_transition_research_records(records, min_sample_size=1)
    row = summary[(summary["from_state"] == "Compression") & (summary["to_state"] == "Relative Accumulation")].iloc[0]

    assert row["classification"] == "fragile"
    assert "calendar cluster" in row["notes"]


def test_conditioned_summary_includes_chain_and_mtf_groups_without_fake_weakness():
    records = transition_records_for_asset("AAA", _frame())
    records["chain_support_group"] = ["supportive", "non_supportive", "incomplete", "supportive"]
    records["mtf_condition_group"] = ["aligned", "non_aligned", "incomplete", "not_requested"]

    conditioned = summarize_conditioned_transition_records(records, min_sample_size=999)

    assert set(conditioned["condition_type"]) == {"chain_support_group", "mtf_condition_group"}
    assert {"supportive", "non_supportive", "incomplete"}.issubset(set(conditioned["condition_group"]))
    assert {"aligned", "non_aligned", "not_requested"}.issubset(set(conditioned["condition_group"]))
    assert set(conditioned["classification"]) == {"inconclusive"}


def test_missing_mtf_context_is_not_requested_and_incomplete_chain_is_explicit():
    frame = _frame(periods=12)
    records = transition_records_for_asset("AAA", frame)

    assert records["mtf_condition_group"].eq("not_requested").all()
    assert records["chain_support_group"].eq("incomplete").all()


def test_transition_research_preserves_default_scan_schema():
    universe = _universe()
    raw_frames = {
        "AAA": pd.DataFrame(
            {
                "open": np.linspace(100.0, 130.0, 80),
                "high": np.linspace(101.0, 131.0, 80),
                "low": np.linspace(99.0, 129.0, 80),
                "close": np.linspace(100.0, 130.0, 80),
                "volume": 1000.0,
            },
            index=pd.date_range("2024-01-01", periods=80, freq="D"),
        ),
        "BBB": pd.DataFrame(
            {
                "open": np.linspace(50.0, 90.0, 80),
                "high": np.linspace(51.0, 91.0, 80),
                "low": np.linspace(49.0, 89.0, 80),
                "close": np.linspace(50.0, 90.0, 80),
                "volume": 1000.0,
            },
            index=pd.date_range("2024-01-01", periods=80, freq="D"),
        ),
    }
    analysis_frames, _basket, _warnings = build_analysis_frames(universe, raw_frames)
    _records = build_transition_research_records(universe, analysis_frames)
    leaderboard = build_leaderboard(universe, analysis_frames)

    assert list(leaderboard.columns) == LEADERBOARD_COLUMNS
    assert "transition_model" not in leaderboard.columns


def test_transition_research_cli_creates_report_files(tmp_path: Path):
    config_path = tmp_path / "universe.yaml"
    data_dir = tmp_path / "raw"
    report_dir = tmp_path / "reports"
    obsidian_dir = tmp_path / "obsidian"
    data_dir.mkdir()
    config_path.write_text(
        """
name: test_meme_universe
benchmark:
  type: equal_weight_basket
  name: MEME_BASKET
min_active_members: 1
assets:
  - symbol: AAA
    name: AAA
    sector: memes
    subgroup: base_memes
  - symbol: BBB
    name: BBB
    sector: memes
    subgroup: sol_memes
""",
        encoding="utf-8",
    )
    _write_csv(data_dir / "AAA_1d.csv", 80, 100.0)
    _write_csv(data_dir / "BBB_1d.csv", 80, 50.0)

    exit_code = main(
        [
            "transition-research",
            "--config",
            str(config_path),
            "--data-dir",
            str(data_dir),
            "--report-dir",
            str(report_dir),
            "--obsidian-dir",
            str(obsidian_dir),
            "--timeframe",
            "1d",
            "--min-sample-size",
            "1",
        ]
    )

    assert exit_code == 0
    assert (report_dir / "transition_research_records.csv").exists()
    assert (report_dir / "transition_research_summary.csv").exists()
    assert (report_dir / "transition_matrix_unconditional.csv").exists()
    assert (report_dir / "transition_matrix_conditioned.csv").exists()
    assert (report_dir / "transition_research_summary.html").exists()
    assert (obsidian_dir / "reports" / "latest_transition_research.md").exists()
