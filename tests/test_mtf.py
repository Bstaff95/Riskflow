from pathlib import Path

import numpy as np
import pandas as pd

from riskflow.cli import main
from riskflow.mtf import (
    MTF_LEADERBOARD_COLUMNS,
    asof_join_completed_context,
    classify_mtf_context_row,
    timeframe_duration,
)


def _analysis_frame(dates: pd.DatetimeIndex, state: str = "Confirmed Leader") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "target": np.linspace(100.0, 110.0, len(dates)),
            "benchmark": np.linspace(100.0, 105.0, len(dates)),
            "state": state,
            "final_signal": 1.0,
            "relative_component": 0.5,
            "viscosity": 0.0,
            "above_viscosity": True,
            "compression_score": 75.0,
            "setup_readiness_score": 80.0,
            "extension_risk_score": 20.0,
            "signal_slope": 0.1,
        },
        index=dates,
    )


def _write_csv(path: Path, periods: int = 70, freq: str = "D", start: float = 100.0, step: float = 0.5) -> None:
    dates = pd.date_range("2024-01-01", periods=periods, freq=freq)
    lines = ["date,open,high,low,close,volume"]
    for idx, date in enumerate(dates):
        value = start + idx * step
        lines.append(f"{date},{value},{value * 1.02},{value * 0.98},{value},1000")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_config(path: Path) -> None:
    path.write_text(
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
    subgroup: test
  - symbol: BBB
    name: BBB
    sector: memes
    subgroup: test
""",
        encoding="utf-8",
    )


def test_timeframe_duration_and_available_at_math():
    assert timeframe_duration("1w") == pd.Timedelta(days=7)
    assert timeframe_duration("3d") == pd.Timedelta(days=3)
    assert timeframe_duration("12h") == pd.Timedelta(hours=12)
    assert timeframe_duration("4h") == pd.Timedelta(hours=4)


def test_weekly_context_unavailable_before_completed_candle_close():
    primary_dates = pd.date_range("2024-01-01", periods=8, freq="D")
    context_dates = pd.DatetimeIndex([pd.Timestamp("2024-01-01")])
    primary = _analysis_frame(primary_dates, state="Relative Accumulation")
    context = _analysis_frame(context_dates, state="Confirmed Leader")

    joined = asof_join_completed_context(
        primary,
        context,
        primary_timeframe="1d",
        context_timeframe="1w",
    )

    assert pd.isna(joined.loc[pd.Timestamp("2024-01-06"), "mtf_1w_state"])
    assert joined.loc[pd.Timestamp("2024-01-07"), "mtf_1w_state"] == "Confirmed Leader"


def test_asof_join_uses_last_completed_context_bar_only():
    primary_dates = pd.date_range("2024-01-01", periods=7, freq="D")
    context_dates = pd.DatetimeIndex([pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-04")])
    primary = _analysis_frame(primary_dates, state="Relative Accumulation")
    context = _analysis_frame(context_dates, state="Confirmed Leader")
    context.loc[pd.Timestamp("2024-01-01"), "final_signal"] = 1.0
    context.loc[pd.Timestamp("2024-01-04"), "final_signal"] = 2.0

    joined = asof_join_completed_context(
        primary,
        context,
        primary_timeframe="1d",
        context_timeframe="3d",
    )

    assert pd.isna(joined.loc[pd.Timestamp("2024-01-02"), "mtf_3d_final_signal"])
    assert joined.loc[pd.Timestamp("2024-01-03"), "mtf_3d_final_signal"] == 1.0
    assert joined.loc[pd.Timestamp("2024-01-06"), "mtf_3d_final_signal"] == 2.0


def test_mtf_labels_classify_aligned_tactical_conflicted_and_incomplete():
    base = pd.Series(
        {
            "primary_available_at": pd.Timestamp("2024-01-10"),
            "state": "Emerging Leader",
            "final_signal": 1.0,
            "relative_component": 0.5,
            "above_viscosity": True,
            "setup_readiness_score": 80.0,
            "extension_risk_score": 20.0,
            "mtf_1w_context_available_at": pd.Timestamp("2024-01-08"),
            "mtf_1w_state": "Confirmed Leader",
            "mtf_1w_final_signal": 1.0,
            "mtf_1w_relative_component": 0.5,
            "mtf_1w_above_viscosity": True,
            "mtf_3d_context_available_at": pd.Timestamp("2024-01-10"),
            "mtf_3d_state": "Confirmed Leader",
            "mtf_3d_final_signal": 1.0,
            "mtf_3d_relative_component": 0.5,
            "mtf_3d_above_viscosity": True,
            "mtf_4h_context_available_at": pd.Timestamp("2024-01-10"),
            "mtf_4h_state": "Compression",
            "mtf_4h_final_signal": 0.1,
            "mtf_4h_compression_score": 80.0,
        }
    )

    aligned = classify_mtf_context_row(base, context_timeframes=("1w", "3d", "4h"))
    assert aligned["mtf_leader_context"] == "Aligned Leader"
    assert aligned["mtf_trader_context"] == "Setup Ready"

    tactical_row = base.copy()
    tactical_row["mtf_1w_state"] = "Unknown"
    tactical_row["mtf_1w_final_signal"] = 0.0
    tactical_row["mtf_1w_relative_component"] = 0.0
    tactical_row["mtf_1w_above_viscosity"] = False
    tactical_row["mtf_3d_state"] = "Unknown"
    tactical_row["mtf_3d_final_signal"] = 0.0
    tactical_row["mtf_3d_relative_component"] = 0.0
    tactical_row["mtf_3d_above_viscosity"] = False
    tactical = classify_mtf_context_row(tactical_row, context_timeframes=("1w", "3d"))
    assert tactical["mtf_leader_context"] == "Tactical Leader"

    conflict_row = base.copy()
    conflict_row["mtf_1w_state"] = "Breakdown"
    conflict_row["mtf_1w_final_signal"] = -1.0
    conflict_row["mtf_1w_relative_component"] = -0.5
    conflicted = classify_mtf_context_row(conflict_row, context_timeframes=("1w", "3d"))
    assert conflicted["mtf_leader_context"] == "Conflicted Leader"

    incomplete_row = base.drop(labels=["mtf_1w_context_available_at"])
    incomplete = classify_mtf_context_row(incomplete_row, context_timeframes=("1w", "3d"))
    assert incomplete["mtf_leader_context"] == "Incomplete Data"


def test_scan_schema_unchanged_without_mtf_and_extended_with_mtf(tmp_path: Path):
    config_path = tmp_path / "universe.yaml"
    data_dir = tmp_path / "raw"
    report_dir = tmp_path / "reports"
    obsidian_dir = tmp_path / "obsidian"
    data_dir.mkdir()
    _write_config(config_path)
    for symbol in ("AAA", "BBB"):
        _write_csv(data_dir / f"{symbol}_1d.csv", start=50.0 if symbol == "AAA" else 60.0)
        _write_csv(data_dir / f"{symbol}_1w.csv", periods=12, freq="7D", start=50.0 if symbol == "AAA" else 60.0)
        _write_csv(data_dir / f"{symbol}_3d.csv", periods=24, freq="3D", start=50.0 if symbol == "AAA" else 60.0)

    assert main(
        [
            "scan",
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
        ]
    ) == 0
    no_mtf = pd.read_csv(report_dir / "latest_meme_leaderboard.csv")
    assert not set(MTF_LEADERBOARD_COLUMNS).intersection(no_mtf.columns)

    assert main(
        [
            "scan",
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
            "--context-timeframes",
            "1w",
            "3d",
        ]
    ) == 0
    with_mtf = pd.read_csv(report_dir / "latest_meme_leaderboard.csv")
    assert set(MTF_LEADERBOARD_COLUMNS).issubset(with_mtf.columns)
