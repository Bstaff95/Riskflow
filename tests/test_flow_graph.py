from pathlib import Path

import numpy as np
import pandas as pd

from riskflow.cli import LEADERBOARD_COLUMNS, build_analysis_frames, build_leaderboard, main
from riskflow.config import AssetConfig, BenchmarkConfig, UniverseConfig
from riskflow.flow_graph import (
    CAPITAL_FLOW_GRAPH_V0,
    EDGE_COLUMNS,
    NODE_COLUMNS,
    build_flow_graph_tables,
    edge_id,
    node_id,
)


def _ohlcv(start: float, periods: int = 60) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    close = pd.Series(start + np.arange(periods) * 0.5, index=dates)
    return pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": 1000.0,
        },
        index=dates,
    )


def _universe() -> UniverseConfig:
    return UniverseConfig(
        name="test_meme_universe",
        benchmark=BenchmarkConfig(name="MEME_BASKET"),
        min_active_members=1,
        assets=[
            AssetConfig(symbol="AAA", name="AAA", sector="memes", subgroup="base_memes"),
            AssetConfig(symbol="BBB", name="BBB", sector="memes", subgroup="sol_memes"),
        ],
    )


def _write_csv(path: Path, start: float, periods: int = 65) -> None:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    lines = ["date,open,high,low,close,volume"]
    for idx, date in enumerate(dates):
        value = start + idx * 0.5
        lines.append(f"{date.date()},{value},{value * 1.02},{value * 0.98},{value},1000")
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
    subgroup: base_memes
  - symbol: BBB
    name: BBB
    sector: memes
    subgroup: sol_memes
""",
        encoding="utf-8",
    )


def test_flow_graph_builds_expected_nodes_edges_and_deterministic_ids():
    universe = _universe()
    raw_frames = {"AAA": _ohlcv(100.0), "BBB": _ohlcv(50.0)}
    analysis_frames, _basket, _warnings = build_analysis_frames(universe, raw_frames)

    nodes, edges, chains = build_flow_graph_tables(universe, analysis_frames, timeframe="1d")

    assert list(nodes.columns) == NODE_COLUMNS
    assert list(edges.columns) == EDGE_COLUMNS
    assert set(nodes["node_type"]) == {"universe", "basket", "sector", "subgroup", "asset"}
    assert node_id("asset", "AAA") in set(nodes["node_id"])
    assert edge_id(node_id("subgroup", "memes:base_memes"), node_id("asset", "AAA"), "contains") in set(edges["edge_id"])
    assert edge_id(node_id("asset", "AAA"), node_id("subgroup", "memes:base_memes"), "belongs_to") in set(edges["edge_id"])
    assert {"contains", "belongs_to", "benchmarked_against", "child_vs_parent"}.issubset(set(edges["edge_type"]))
    assert set(chains["asset_symbol"]) == {"AAA", "BBB"}
    assert chains["graph_model"].eq(CAPITAL_FLOW_GRAPH_V0).all()


def test_missing_parent_context_creates_incomplete_chain_and_bounded_score():
    universe = _universe()
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    frame = pd.DataFrame(
        {
            "target": np.linspace(100.0, 108.0, 8),
            "benchmark": np.nan,
            "final_signal": 1.0,
            "relative_component": 1.0,
            "above_viscosity": True,
            "state": "Emerging Leader",
            "setup_readiness_score": 90.0,
            "extension_risk_score": 10.0,
        },
        index=dates,
    )

    _nodes, _edges, chains = build_flow_graph_tables(universe, {"AAA": frame}, timeframe="1d")

    assert chains.iloc[0]["chain_label"] == "Incomplete Chain"
    assert chains["chain_support_score"].between(0.0, 100.0).all()
    assert chains.iloc[0]["chain_support_score"] <= 40.0


def test_default_scan_schema_unchanged_by_flow_graph_layer():
    universe = _universe()
    raw_frames = {"AAA": _ohlcv(100.0), "BBB": _ohlcv(50.0)}
    analysis_frames, _basket, _warnings = build_analysis_frames(universe, raw_frames)

    leaderboard = build_leaderboard(universe, analysis_frames)

    assert list(leaderboard.columns) == LEADERBOARD_COLUMNS
    assert "chain_label" not in leaderboard.columns


def test_flow_graph_cli_creates_outputs(tmp_path: Path):
    config_path = tmp_path / "universe.yaml"
    data_dir = tmp_path / "raw"
    report_dir = tmp_path / "reports"
    obsidian_dir = tmp_path / "obsidian"
    data_dir.mkdir()
    _write_config(config_path)
    _write_csv(data_dir / "AAA_1d.csv", 100.0)
    _write_csv(data_dir / "BBB_1d.csv", 50.0)

    exit_code = main(
        [
            "flow-graph",
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
    )

    assert exit_code == 0
    assert (report_dir / "flow_graph_nodes.csv").exists()
    assert (report_dir / "flow_graph_edges.csv").exists()
    assert (report_dir / "flow_graph_chains.csv").exists()
    assert (obsidian_dir / "reports" / "latest_flow_graph.md").exists()
