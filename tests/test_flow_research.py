from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from riskflow.cli import main
from riskflow.config import AssetConfig, BenchmarkConfig, UniverseConfig
from riskflow.flow_research import (
    RECORD_COLUMNS,
    SUMMARY_COLUMNS,
    run_flow_research,
    summarize_flow_research_records,
)


def _frame(periods: int = 90) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    target = pd.Series(100.0 * np.cumprod(np.full(periods, 1.006)), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(np.full(periods, 1.003)), index=dates)
    return pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "final_signal": np.linspace(-1.0, 2.0, periods),
            "viscosity": 0.0,
            "relative_component": np.linspace(-0.4, 1.2, periods),
            "compression_score": np.r_[np.full(periods // 2, 60.0), np.full(periods - periods // 2, 80.0)],
            "setup_readiness_score": np.linspace(0.0, 100.0, periods),
            "extension_risk_score": 10.0,
            "above_viscosity": [False] * 30 + [True] * (periods - 30),
            "state": ["Weak"] * 20 + ["Relative Accumulation"] * 25 + ["Emerging Leader"] * (periods - 45),
        },
        index=dates,
    )


def _universe() -> UniverseConfig:
    return UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(name="MEME_BASKET"),
        min_active_members=1,
        assets=[AssetConfig(symbol="AAA", name="AAA", sector="memes", subgroup="base_memes")],
    )


def _write_csv(path: Path, periods: int = 80, start: float = 100.0) -> None:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    lines = ["date,open,high,low,close,volume"]
    for idx, date in enumerate(dates):
        value = start + idx * 0.4
        lines.append(f"{date.date()},{value},{value * 1.02},{value * 0.98},{value},1000")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_flow_research_records_include_required_columns_and_returns():
    summary, records = run_flow_research(_universe(), {"AAA": _frame()}, min_sample_size=1, cooldown_bars=0)

    assert list(records.columns) == RECORD_COLUMNS
    assert list(summary.columns) == SUMMARY_COLUMNS
    assert "forward_relative_return_14" in records.columns
    assert not records.empty


def test_flow_research_low_sample_size_is_inconclusive():
    summary, _records = run_flow_research(_universe(), {"AAA": _frame(50)}, min_sample_size=999, cooldown_bars=0)

    assert set(summary["classification"]) == {"inconclusive"}


def test_supportive_minus_non_supportive_spread_is_calculated():
    records = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx),
                "timeframe": "1d",
                "benchmark": "TEST",
                "graph_model": "capital_flow_graph_v0",
                "flow_event": "state_emerging_leader",
                "chain_support_group": "supportive" if idx < 3 else "non_supportive",
                "chain_label": "Partial Chain Support" if idx < 3 else "Asset Leading Weak Parent",
                "chain_support_score": 80.0 if idx < 3 else 40.0,
                "chain_alignment_tags": "asset_ready" if idx < 3 else "",
                "chain_conflict_tags": "" if idx < 3 else "benchmark_parent_not_supportive",
                "chain_confidence": "provisional",
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

    summary = summarize_flow_research_records(records, min_sample_size=1)
    row = summary[summary["flow_event"] == "state_emerging_leader"].iloc[0]

    assert row["supportive_minus_non_supportive_spread_14"] == pytest.approx(0.08)
    assert row["supportive_minus_non_supportive_spread_30"] == pytest.approx(0.15)


def test_symbol_or_cluster_dominance_is_fragile_when_sample_sufficient():
    records = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx * 40),
                "timeframe": "1d",
                "benchmark": "TEST",
                "graph_model": "capital_flow_graph_v0",
                "flow_event": "state_emerging_leader",
                "chain_support_group": "supportive" if idx < 3 else "non_supportive",
                "chain_label": "Partial Chain Support" if idx < 3 else "Asset Leading Weak Parent",
                "chain_support_score": 80.0,
                "chain_alignment_tags": "asset_ready",
                "chain_conflict_tags": "",
                "chain_confidence": "provisional",
                "event_value": "Emerging Leader",
                "entry_lag_bars": 1,
                "entry_date": pd.Timestamp("2024-01-02") + pd.Timedelta(days=idx * 40),
                "cooldown_bars": 0,
                "event_cluster_id": f"2024-{idx + 1:02d}",
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

    summary = summarize_flow_research_records(records, min_sample_size=1)
    row = summary[summary["flow_event"] == "state_emerging_leader"].iloc[0]

    assert row["classification"] == "fragile"
    assert "one symbol" in row["notes"]


def test_flow_research_cli_creates_report_files(tmp_path: Path):
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
            "flow-research",
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
            "--cooldown-bars",
            "0",
        ]
    )

    assert exit_code == 0
    assert (report_dir / "flow_research_records.csv").exists()
    assert (report_dir / "flow_research_summary.csv").exists()
    assert (report_dir / "flow_research_summary.html").exists()
    assert (obsidian_dir / "reports" / "latest_flow_graph.md").exists()
