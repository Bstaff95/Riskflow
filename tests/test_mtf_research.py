from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from riskflow.cli import main
from riskflow.mtf_research import (
    RECORD_COLUMNS,
    SUMMARY_COLUMNS,
    summarize_mtf_research_records,
    run_mtf_research,
)


def _frame(symbol_bias: float = 0.0, periods: int = 90) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    target = pd.Series(100.0 * np.cumprod(np.full(periods, 1.006 + symbol_bias)), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(np.full(periods, 1.004)), index=dates)
    weak_len = min(20, periods)
    accumulation_len = min(25, max(periods - weak_len, 0))
    leader_len = max(periods - weak_len - accumulation_len, 0)
    states = ["Weak"] * weak_len + ["Relative Accumulation"] * accumulation_len + ["Emerging Leader"] * leader_len
    aligned_len = periods // 2
    non_aligned_len = periods - aligned_len
    frame = pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "final_signal": np.linspace(-1.0, 2.0, periods),
            "viscosity": 0.0,
            "relative_component": np.linspace(-0.2, 1.2, periods),
            "compression_score": np.r_[np.full(periods // 2, 60.0), np.full(periods - periods // 2, 80.0)],
            "setup_readiness_score": np.linspace(0.0, 100.0, periods),
            "state": states,
            "mtf_context_available": True,
            "mtf_leader_context": ["Aligned Leader"] * aligned_len + ["Tactical Leader"] * non_aligned_len,
            "mtf_trader_context": ["Setup Ready"] * aligned_len + ["Wait For Confirmation"] * non_aligned_len,
            "mtf_alignment_tags": ["htf_supportive"] * aligned_len + [""] * non_aligned_len,
            "mtf_conflict_tags": "",
        },
        index=dates,
    )
    return frame


def _write_csv(path: Path, periods: int = 80, freq: str = "D", start: float = 100.0, step: float = 0.4) -> None:
    dates = pd.date_range("2024-01-01", periods=periods, freq=freq)
    lines = ["date,open,high,low,close,volume"]
    for idx, date in enumerate(dates):
        value = start + idx * step
        lines.append(f"{date},{value},{value * 1.02},{value * 0.98},{value},1000")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_mtf_research_records_include_required_columns_and_forward_returns():
    summary, records = run_mtf_research({"AAA": _frame(0.001)}, min_sample_size=1, cooldown_bars=0)

    assert list(records.columns) == RECORD_COLUMNS
    assert list(summary.columns) == SUMMARY_COLUMNS
    assert "forward_relative_return_14" in records.columns
    assert not records.empty


def test_aligned_minus_non_aligned_spread_is_calculated():
    records = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx),
                "timeframe": "1d",
                "benchmark": "TEST",
                "mtf_context_model": "mtf_context_v0",
                "mtf_event": "state_emerging_leader",
                "mtf_support_group": "aligned" if idx < 3 else "non_aligned",
                "mtf_leader_context": "Aligned Leader" if idx < 3 else "Tactical Leader",
                "mtf_trader_context": "Setup Ready",
                "mtf_alignment_tags": "htf_supportive" if idx < 3 else "",
                "mtf_conflict_tags": "",
                "event_value": "Emerging Leader",
                "entry_lag_bars": 1,
                "entry_date": pd.Timestamp("2024-01-02") + pd.Timedelta(days=idx),
                "cooldown_bars": 0,
                "event_cluster_id": f"2024-0{idx + 1}",
                "forward_relative_return_3": 0.01,
                "forward_relative_return_7": 0.01,
                "forward_relative_return_14": 0.10 if idx < 3 else 0.02,
                "forward_relative_return_30": 0.20 if idx < 3 else 0.05,
                "max_drawdown_14": -0.01,
                "max_drawdown_30": -0.02,
            }
            for idx in range(6)
        ],
        columns=RECORD_COLUMNS,
    )

    summary = summarize_mtf_research_records(records, min_sample_size=1)
    row = summary[summary["mtf_event"] == "state_emerging_leader"].iloc[0]

    assert row["aligned_minus_non_aligned_spread_14"] == 0.08
    assert row["aligned_minus_non_aligned_spread_30"] == pytest.approx(0.15)


def test_mtf_research_small_sample_is_inconclusive():
    summary, _records = run_mtf_research({"AAA": _frame(0.001, periods=30)}, min_sample_size=999, cooldown_bars=0)

    assert set(summary["classification"]) == {"inconclusive"}


def test_mtf_research_cli_creates_report_files(tmp_path: Path):
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
    subgroup: test
  - symbol: BBB
    name: BBB
    sector: memes
    subgroup: test
""",
        encoding="utf-8",
    )
    for symbol, start in (("AAA", 50.0), ("BBB", 60.0)):
        _write_csv(data_dir / f"{symbol}_1d.csv", periods=80, freq="D", start=start)
        _write_csv(data_dir / f"{symbol}_1w.csv", periods=14, freq="7D", start=start)
        _write_csv(data_dir / f"{symbol}_3d.csv", periods=30, freq="3D", start=start)
        _write_csv(data_dir / f"{symbol}_12h.csv", periods=160, freq="12h", start=start)
        _write_csv(data_dir / f"{symbol}_4h.csv", periods=240, freq="4h", start=start)

    exit_code = main(
        [
            "mtf-research",
            "--config",
            str(config_path),
            "--data-dir",
            str(data_dir),
            "--report-dir",
            str(report_dir),
            "--obsidian-dir",
            str(obsidian_dir),
            "--primary-timeframe",
            "1d",
            "--context-timeframes",
            "1w",
            "3d",
            "12h",
            "4h",
            "--min-sample-size",
            "1",
            "--cooldown-bars",
            "0",
        ]
    )

    assert exit_code == 0
    assert (report_dir / "mtf_research_records.csv").exists()
    assert (report_dir / "mtf_research_summary.csv").exists()
    assert (report_dir / "mtf_research_summary.html").exists()
    assert (obsidian_dir / "reports" / "latest_mtf_research.md").exists()
