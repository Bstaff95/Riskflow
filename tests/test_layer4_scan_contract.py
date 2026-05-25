import pandas as pd

from riskflow.config import AssetConfig, BenchmarkConfig, UniverseConfig
from riskflow.cli import build_analysis_frames, build_leaderboard


def _ohlcv(start: float) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    close = pd.Series([start + idx * 0.5 for idx in range(40)], index=dates)
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


def test_leaderboard_includes_layer4_columns_and_existing_columns():
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(),
        min_active_members=1,
        assets=[
            AssetConfig(symbol="AAA", name="AAA", sector="memes", subgroup="test"),
            AssetConfig(symbol="BBB", name="BBB", sector="memes", subgroup="test"),
        ],
    )
    raw_frames = {"AAA": _ohlcv(100.0), "BBB": _ohlcv(50.0)}

    analysis_frames, _basket, _warnings = build_analysis_frames(universe, raw_frames)
    leaderboard = build_leaderboard(universe, analysis_frames)

    existing_columns = {"symbol", "final_signal", "compression_score", "state", "opportunity_score"}
    layer4_columns = {
        "compression_score_v0",
        "leader_quality_score",
        "compression_quality_score",
        "relative_accumulation_score",
        "setup_readiness_score",
        "extension_risk_score",
        "data_quality_score",
        "trader_score_v0",
        "trader_rank",
        "setup_state_v0",
        "setup_tags",
        "opportunity_score_v0",
    }
    assert existing_columns.issubset(leaderboard.columns)
    assert layer4_columns.issubset(leaderboard.columns)
