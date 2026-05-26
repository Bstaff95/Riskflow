from __future__ import annotations

import numpy as np
import pandas as pd

from riskflow.cli import build_analysis_frames, main
from riskflow.config import AssetConfig, BenchmarkConfig, UniverseConfig
from riskflow.visual_review import VisualReviewSettings, build_visual_review_records, run_visual_review


def _raw_frame(multiplier: float = 1.0) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=90, freq="D")
    close = np.full(len(index), 100.0 * multiplier)
    close[55:] *= 1.6
    return pd.DataFrame(
        {
            "open": close * 0.99,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": 1_000.0,
        },
        index=index,
    )


def _analysis_frame() -> pd.DataFrame:
    raw = _raw_frame()
    index = raw.index
    final_signal = pd.Series(-1.5, index=index, dtype=float)
    final_signal.iloc[45:] = np.linspace(-1.4, 1.2, len(index) - 45)
    viscosity = final_signal.ewm(span=8, adjust=False).mean() - 0.05
    benchmark = pd.Series(100.0, index=index)
    return pd.DataFrame(
        {
            "target": raw["close"],
            "benchmark": benchmark,
            "final_signal": final_signal,
            "viscosity": viscosity,
            "relative_component": final_signal * 0.8,
            "price_component": final_signal * 0.5,
            "compression_score": 72.0,
            "state": "Relative Accumulation",
            "setup_tags": "compressed,relative_strength_rising",
            "benchmark_used": "MEME_BASKET_EX_TEST",
        },
        index=index,
    )


def test_visual_review_records_include_visual_pattern_clues() -> None:
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(name="MEME_BASKET", exclude_self=True),
        min_active_members=1,
        assets=[AssetConfig(symbol="TEST", name="Test Coin", sector="memes", subgroup="test")],
    )
    records = build_visual_review_records(
        universe,
        {"TEST": _analysis_frame()},
        settings=VisualReviewSettings(min_forward_relative_return=0.25, max_events=3, min_signal_std=0.0),
    )

    assert not records.empty
    assert {"pre_event_signal_band_share", "recent_viscosity_reclaim", "signal_zone"}.issubset(records.columns)
    assert records["benchmark"].eq("MEME_BASKET_EX_TEST").all()
    assert records["forward_relative_return_30"].notna().all()


def test_impulse_retest_visual_review_selects_pattern_without_forward_filter() -> None:
    index = pd.date_range("2024-01-01", periods=120, freq="D")
    close = pd.Series(np.linspace(100.0, 150.0, len(index)), index=index)
    signal = pd.Series(-1.4, index=index, dtype=float)
    signal.iloc[70:78] = np.linspace(-1.2, 2.2, 8)
    signal.iloc[78:88] = np.linspace(2.0, 0.55, 10)
    signal.iloc[88:] = 0.65
    viscosity = signal.ewm(span=10, adjust=False).mean()
    frame = pd.DataFrame(
        {
            "target": close,
            "benchmark": pd.Series(100.0, index=index),
            "final_signal": signal,
            "viscosity": viscosity,
            "relative_component": signal * 0.7,
            "price_component": signal * 0.5,
            "compression_score": 65.0,
            "state": "Relative Accumulation",
            "setup_tags": "compressed,viscosity_reclaim",
            "benchmark_used": "MEME_BASKET_EX_TEST",
        },
        index=index,
    )
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(name="MEME_BASKET", exclude_self=True),
        min_active_members=1,
        assets=[AssetConfig(symbol="TEST", name="Test Coin", sector="memes", subgroup="test")],
    )
    records = build_visual_review_records(
        universe,
        {"TEST": frame},
        settings=VisualReviewSettings(
            event_mode="impulse-retest",
            min_forward_relative_return=99.0,
            min_signal_std=0.0,
            max_events=3,
        ),
    )

    assert not records.empty
    assert records["event_name"].eq("compression_impulse_viscosity_retest_v0").all()
    assert records["pattern_score"].notna().all()


def test_coil_reclaim_visual_review_selects_early_lower_zone_reclaim() -> None:
    index = pd.date_range("2024-01-01", periods=120, freq="D")
    close = pd.Series(np.linspace(100.0, 145.0, len(index)), index=index)
    signal = pd.Series(-1.35, index=index, dtype=float)
    signal.iloc[40:72] = -1.55 + np.sin(np.linspace(0, 5, 32)) * 0.18
    signal.iloc[72] = -1.25
    signal.iloc[73] = -0.85
    signal.iloc[74:] = np.linspace(-0.55, 1.4, len(index) - 74)
    viscosity = signal.ewm(span=18, adjust=False).mean() - 0.08
    frame = pd.DataFrame(
        {
            "target": close,
            "benchmark": pd.Series(100.0, index=index),
            "final_signal": signal,
            "viscosity": viscosity,
            "relative_component": signal * 0.8 + 0.35,
            "price_component": signal * 0.45,
            "compression_score": 58.0,
            "state": "Relative Accumulation",
            "setup_tags": "compressed,relative_strength_rising,viscosity_reclaim",
            "benchmark_used": "MEME_BASKET_EX_TEST",
        },
        index=index,
    )
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(name="MEME_BASKET", exclude_self=True),
        min_active_members=1,
        assets=[AssetConfig(symbol="TEST", name="Test Coin", sector="memes", subgroup="test")],
    )

    records = build_visual_review_records(
        universe,
        {"TEST": frame},
        settings=VisualReviewSettings(
            event_mode="coil-reclaim",
            min_forward_relative_return=99.0,
            min_signal_std=0.0,
            max_events=3,
        ),
    )

    assert not records.empty
    assert records["event_name"].eq("coil_viscosity_reclaim_v0").all()
    assert records["final_signal"].max() < 1.0
    assert records["recent_viscosity_reclaim"].all()


def test_run_visual_review_writes_gallery_and_images(tmp_path) -> None:
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(name="MEME_BASKET", exclude_self=True),
        min_active_members=1,
        assets=[AssetConfig(symbol="TEST", name="Test Coin", sector="memes", subgroup="test")],
    )
    records, paths = run_visual_review(
        universe,
        {"TEST": _raw_frame()},
        {"TEST": _analysis_frame()},
        report_dir=tmp_path,
        settings=VisualReviewSettings(min_forward_relative_return=0.25, max_events=2, min_signal_std=0.0),
    )

    assert paths["events_csv"].exists()
    assert paths["gallery_md"].exists()
    assert not records.empty
    assert all(path.endswith(".png") for path in records["image_path"])
    assert all(pd.notna(path) for path in records["image_path"])


def test_visual_review_cli_creates_outputs(tmp_path) -> None:
    config_path = tmp_path / "universe.yaml"
    data_dir = tmp_path / "raw"
    data_dir.mkdir()
    config_path.write_text(
        """
name: test_universe
benchmark:
  type: equal_weight_basket
  name: MEME_BASKET
  exclude_self: true
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
""".strip(),
        encoding="utf-8",
    )
    _raw_frame(1.0).to_csv(data_dir / "AAA_1d.csv", index_label="date")
    _raw_frame(1.1).assign(close=lambda frame: frame["close"] * 0 + 100.0).to_csv(
        data_dir / "BBB_1d.csv",
        index_label="date",
    )

    status = main(
        [
            "visual-review",
            "--config",
            str(config_path),
            "--data-dir",
            str(data_dir),
            "--report-dir",
            str(tmp_path / "reports"),
            "--timeframe",
            "1d",
            "--min-forward-relative-return",
            "0.20",
            "--max-events",
            "2",
            "--min-signal-std",
            "0",
        ]
    )

    assert status == 0
    assert (tmp_path / "reports" / "visual_review" / "events.csv").exists()
    assert (tmp_path / "reports" / "visual_review" / "gallery.md").exists()


def test_visual_review_does_not_change_analysis_frame_contract() -> None:
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(name="MEME_BASKET", exclude_self=True),
        min_active_members=1,
        assets=[
            AssetConfig(symbol="AAA", name="AAA", sector="memes", subgroup="test"),
            AssetConfig(symbol="BBB", name="BBB", sector="memes", subgroup="test"),
        ],
    )
    frames = {"AAA": _raw_frame(1.0), "BBB": _raw_frame(1.1)}
    analysis_frames, _basket, _warnings = build_analysis_frames(universe, frames)
    before_columns = {symbol: tuple(frame.columns) for symbol, frame in analysis_frames.items()}
    run_visual_review(
        universe,
        frames,
        analysis_frames,
        report_dir="/tmp/riskflow_visual_review_test",
        settings=VisualReviewSettings(min_forward_relative_return=0.20, max_events=1, min_signal_std=0.0),
    )
    after_columns = {symbol: tuple(frame.columns) for symbol, frame in analysis_frames.items()}

    assert after_columns == before_columns
