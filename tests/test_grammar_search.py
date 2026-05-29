from __future__ import annotations

import pandas as pd

from riskflow.cli import main
from riskflow.grammar_search import (
    GRAMMAR_SEARCH_MODEL,
    detect_variant_events,
    expand_rule_variants,
    load_rule_search_grid,
    run_grammar_search,
    summarize_grammar_search_records,
)


def _grid(tmp_path):
    path = tmp_path / "rule_search_grid.yaml"
    path.write_text(
        """
model: riskflow_grammar_search_v0
families:
  - family_id: zone_reclaim_retest
    direction: positive
    detector: zone_reclaim_retest
    parameter_grid:
      level: [-1.5, 0.0]
      mode: [reclaim]
      tolerance: [0.1]
      hold_bars: [3]
  - family_id: hot_leader_reset
    direction: negative
    detector: hot_leader_reset
    parameter_grid:
      prior_window: [5]
      hot_level: [1.5]
      cooloff_level: [1.0]
      require_below_viscosity: [true]
""",
        encoding="utf-8",
    )
    return path


def _analysis_frame(periods: int = 80) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    signal_values = (
        [-2.0, -1.8, -1.6, -1.4, -1.0, -0.6, -0.2, 0.1, 0.4, 0.7]
        + [1.8, 1.7, 1.5, 1.2, 0.8, 0.4, -0.1, -0.3, -0.2, 0.0]
        + [0.2, 0.4, 0.6, 0.8, 1.0] * 12
    )[:periods]
    final_signal = pd.Series(signal_values, index=dates, dtype=float)
    target = pd.Series([100.0 + idx * 1.5 for idx in range(periods)], index=dates)
    benchmark = pd.Series([100.0 + idx * 0.5 for idx in range(periods)], index=dates)
    return pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "benchmark_used": "MEME_BASKET",
            "final_signal": final_signal,
            "viscosity": final_signal.ewm(span=5, adjust=False).mean() - 0.05,
            "relative_component": final_signal.diff().fillna(0.0),
            "gradient_driver": final_signal,
            "compression_score": 75.0,
            "grammar_clean_chop_quality": False,
            "grammar_chaotic_chop_quality": False,
            "grammar_bullish_divergence_20": False,
            "grammar_bearish_divergence_20": False,
            "grammar_gradient_momentum_divergence_20": False,
        },
        index=dates,
    )


def test_load_and_expand_rule_search_grid(tmp_path) -> None:
    specs = load_rule_search_grid(_grid(tmp_path))
    variants = expand_rule_variants(specs, timeframes=["1d", "4h"])

    assert specs[0].family_id == "zone_reclaim_retest"
    assert variants[0].variant_id.startswith("grammar_search.zone_reclaim_retest.v0.tf_1d")
    assert len(variants) == 6


def test_detect_variant_events_returns_aligned_mask(tmp_path) -> None:
    specs = load_rule_search_grid(_grid(tmp_path))
    variant = expand_rule_variants(specs[:1], timeframes=["1d"])[0]
    frame = _analysis_frame()

    mask = detect_variant_events(frame, variant)

    assert mask.index.equals(frame.index)
    assert mask.dtype == bool
    assert mask.any()


def test_run_grammar_search_builds_ranked_outputs(tmp_path) -> None:
    specs = load_rule_search_grid(_grid(tmp_path))
    variants = expand_rule_variants(specs, timeframes=["1d"])
    records = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": pd.Timestamp("2024-01-10"),
                "timeframe": "1d",
                "benchmark": "MEME_BASKET",
                "variant_id": variants[0].variant_id,
                "family_id": variants[0].family_id,
                "detector": variants[0].detector,
                "direction": variants[0].direction,
                "params": "{}",
                "entry_lag_bars": 1,
                "entry_date": pd.Timestamp("2024-01-11"),
                "cooldown_bars": 1,
                "event_cluster_id": "2024-01",
                "forward_return_3": 0.08,
                "forward_relative_return_3": 0.05,
                "forward_return_7": 0.12,
                "forward_relative_return_7": 0.07,
                "forward_return_14": 0.20,
                "forward_relative_return_14": 0.10,
                "forward_return_30": 0.25,
                "forward_relative_return_30": 0.12,
                "max_drawdown_30": -0.03,
            },
            {
                "symbol": "BBB",
                "date": pd.Timestamp("2024-02-10"),
                "timeframe": "1d",
                "benchmark": "MEME_BASKET",
                "variant_id": variants[0].variant_id,
                "family_id": variants[0].family_id,
                "detector": variants[0].detector,
                "direction": variants[0].direction,
                "params": "{}",
                "entry_lag_bars": 1,
                "entry_date": pd.Timestamp("2024-02-11"),
                "cooldown_bars": 1,
                "event_cluster_id": "2024-02",
                "forward_return_3": 0.06,
                "forward_relative_return_3": 0.04,
                "forward_return_7": 0.11,
                "forward_relative_return_7": 0.06,
                "forward_return_14": 0.18,
                "forward_relative_return_14": 0.09,
                "forward_return_30": 0.22,
                "forward_relative_return_30": 0.11,
                "max_drawdown_30": -0.04,
            },
            {
                "symbol": "CCC",
                "date": pd.Timestamp("2024-03-10"),
                "timeframe": "1d",
                "benchmark": "MEME_BASKET",
                "variant_id": variants[0].variant_id,
                "family_id": variants[0].family_id,
                "detector": variants[0].detector,
                "direction": variants[0].direction,
                "params": "{}",
                "entry_lag_bars": 1,
                "entry_date": pd.Timestamp("2024-03-11"),
                "cooldown_bars": 1,
                "event_cluster_id": "2024-03",
                "forward_return_3": 0.07,
                "forward_relative_return_3": 0.05,
                "forward_return_7": 0.10,
                "forward_relative_return_7": 0.06,
                "forward_return_14": 0.17,
                "forward_relative_return_14": 0.08,
                "forward_return_30": 0.21,
                "forward_relative_return_30": 0.10,
                "max_drawdown_30": -0.02,
            },
        ]
    )

    summary = summarize_grammar_search_records(records, variants=variants, min_sample_size=3)

    row = summary[summary["variant_id"] == variants[0].variant_id].iloc[0]
    assert row["sample_size"] == 3
    assert row["classification"] == "useful"


def test_run_grammar_search_uses_analysis_frames(tmp_path) -> None:
    summary, records, ranked, family_summary, variants = run_grammar_search(
        {"1d": {"AAA": _analysis_frame(), "BBB": _analysis_frame()}},
        grid_path=_grid(tmp_path),
        timeframes=["1d"],
        min_sample_size=1,
        cooldown_bars_by_timeframe={"1d": 1},
    )

    assert len(variants) == 3
    assert "variant_id" in summary.columns
    assert "variant_id" in ranked.columns
    assert "family_id" in family_summary.columns
    assert not records.empty


def _write_csv(path, dates, offset: float) -> None:
    close = [10.0 + offset + idx * 0.2 for idx in range(len(dates))]
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": [value * 1.01 for value in close],
            "low": [value * 0.99 for value in close],
            "close": close,
            "volume": 0.0,
        }
    )
    frame.to_csv(path, index=False)


def test_grammar_search_cli_writes_outputs(tmp_path) -> None:
    config_path = tmp_path / "universe.yaml"
    config_path.write_text(
        """
name: test_universe
benchmark:
  type: equal_weight_basket
  name: MEME_BASKET
  role: opportunity_cost
  exclude_self: false
min_active_members: 2
assets:
  - symbol: AAA
    name: AAA
    sector: memes
    subgroup: test
  - symbol: BBB
    name: BBB
    sector: memes
    subgroup: test
  - symbol: CCC
    name: CCC
    sector: memes
    subgroup: test
""",
        encoding="utf-8",
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dates = pd.date_range("2024-01-01", periods=90, freq="D")
    for idx, symbol in enumerate(["AAA", "BBB", "CCC"]):
        _write_csv(data_dir / f"{symbol}_1d.csv", dates, float(idx))

    status = main(
        [
            "grammar-search",
            "--config",
            str(config_path),
            "--data-dir",
            str(data_dir),
            "--grid",
            str(_grid(tmp_path)),
            "--timeframes",
            "1d",
            "--report-dir",
            str(tmp_path / "reports" / "grammar_search"),
            "--obsidian-dir",
            str(tmp_path / "obsidian"),
            "--min-sample-size",
            "1",
            "--cooldown-bars",
            "1",
        ]
    )

    assert GRAMMAR_SEARCH_MODEL == "riskflow_grammar_search_v0"
    assert status == 0
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_ranked.csv").exists()
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_manifest.yaml").exists()
    assert (tmp_path / "obsidian" / "reports" / "latest_grammar_search.md").exists()
