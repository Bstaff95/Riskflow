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
    layer5_columns = {
        "state_model",
        "state_confidence",
        "state_reason",
        "state_tags",
    }
    assert existing_columns.issubset(leaderboard.columns)
    assert layer4_columns.issubset(leaderboard.columns)
    assert layer5_columns.issubset(leaderboard.columns)


def test_ex_target_benchmark_columns_are_reported_when_enabled():
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(exclude_self=True),
        min_active_members=2,
        assets=[
            AssetConfig(symbol="AAA", name="AAA", sector="memes", subgroup="test"),
            AssetConfig(symbol="BBB", name="BBB", sector="memes", subgroup="test"),
            AssetConfig(symbol="CCC", name="CCC", sector="memes", subgroup="test"),
        ],
    )
    raw_frames = {"AAA": _ohlcv(100.0), "BBB": _ohlcv(50.0), "CCC": _ohlcv(25.0)}

    analysis_frames, _basket, warnings = build_analysis_frames(universe, raw_frames)
    leaderboard = build_leaderboard(universe, analysis_frames)
    aaa = leaderboard[leaderboard["symbol"] == "AAA"].iloc[0]

    assert not warnings
    assert aaa["benchmark_used"] == "MEME_BASKET_EX_AAA"
    assert bool(aaa["benchmark_target_excluded"]) is True
    assert bool(aaa["benchmark_fallback_used"]) is False
    assert aaa["benchmark_active_members"] == 2
    assert aaa["benchmark_member_count"] == 2
    assert aaa["benchmark_confidence"] in {"medium", "high"}
    assert analysis_frames["AAA"]["benchmark_used"].iloc[-1] == "MEME_BASKET_EX_AAA"


def test_ex_target_fallback_is_marked_when_too_few_peers_exist():
    universe = UniverseConfig(
        name="test",
        benchmark=BenchmarkConfig(exclude_self=True),
        min_active_members=2,
        assets=[
            AssetConfig(symbol="AAA", name="AAA", sector="memes", subgroup="test"),
            AssetConfig(symbol="BBB", name="BBB", sector="memes", subgroup="test"),
        ],
    )
    raw_frames = {"AAA": _ohlcv(100.0), "BBB": _ohlcv(50.0)}

    analysis_frames, _basket, warnings = build_analysis_frames(universe, raw_frames)
    leaderboard = build_leaderboard(universe, analysis_frames)
    aaa = leaderboard[leaderboard["symbol"] == "AAA"].iloc[0]

    assert warnings
    assert aaa["benchmark_used"] == "MEME_BASKET"
    assert bool(aaa["benchmark_target_excluded"]) is False
    assert bool(aaa["benchmark_fallback_used"]) is True
    assert aaa["benchmark_confidence"] != "high"
    assert "too_few_members_for_ex_target" == aaa["benchmark_fallback_reason"]
    assert analysis_frames["AAA"]["benchmark_used"].iloc[-1] == "MEME_BASKET"
