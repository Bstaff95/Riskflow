from __future__ import annotations

import pandas as pd

from riskflow.cli import main
from riskflow.grammar_search import (
    GRAMMAR_SEARCH_MODEL,
    RuleVariant,
    chart_review_queue,
    detect_variant_events,
    duplicate_outcome_clusters,
    expand_rule_variants,
    family_timeframe_robustness,
    load_rule_search_grid,
    run_grammar_search,
    strict_baseline_referee,
    summarize_grammar_search_records,
    time_split_validation,
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


def test_second_generation_detectors_return_aligned_masks() -> None:
    frame = _analysis_frame()
    variants = [
        RuleVariant(
            variant_id="test.post_reset_reclaim",
            family_id="post_reset_reclaim",
            direction="positive",
            detector="post_reset_reclaim",
            params={
                "prior_window": 5,
                "hot_level": 1.5,
                "reset_level": 1.0,
                "reset_window": 10,
                "require_below_viscosity": False,
                "trigger": "viscosity_reclaim",
                "relative_slope_min": -1.0,
                "timeframe": "1d",
            },
        ),
        RuleVariant(
            variant_id="test.amplitude_reset_warning",
            family_id="amplitude_reset_warning",
            direction="negative",
            detector="amplitude_reset_warning",
            params={
                "prior_window": 5,
                "hot_level": 1.5,
                "cooloff_level": 1.5,
                "min_signal_range": 1.0,
                "max_compression": 80.0,
                "require_below_viscosity": False,
                "timeframe": "1d",
            },
        ),
        RuleVariant(
            variant_id="test.failed_weakness_reclaim",
            family_id="failed_weakness_reclaim",
            direction="positive",
            detector="failed_weakness_reclaim",
            params={
                "lookback": 5,
                "zone_max": -1.0,
                "low_tolerance": 0.5,
                "min_slope": 0.0,
                "relative_slope_min": -1.0,
                "recent_window": 10,
                "trigger": "zero_reclaim",
                "timeframe": "1d",
            },
        ),
        RuleVariant(
            variant_id="test.chaotic_chop_resolution",
            family_id="chaotic_chop_resolution",
            direction="positive",
            detector="chaotic_chop_resolution",
            params={
                "recent_window": 10,
                "max_chop_compression": 80.0,
                "min_current_compression": 50.0,
                "trigger": "viscosity_reclaim",
                "timeframe": "1d",
            },
        ),
    ]
    frame.loc[frame.index[3:8], "grammar_chaotic_chop_quality"] = True

    for variant in variants:
        mask = detect_variant_events(frame, variant)
        assert mask.index.equals(frame.index)
        assert mask.dtype == bool


def test_failure_warning_detectors_return_aligned_masks() -> None:
    frame = _analysis_frame()
    variants = [
        RuleVariant(
            variant_id="test.zero_rejection_warning",
            family_id="zero_rejection_warning",
            direction="negative",
            detector="zero_rejection_warning",
            params={
                "lookback": 5,
                "level": 0.0,
                "tolerance": 0.25,
                "require_below_viscosity": False,
                "max_compression": 90.0,
                "timeframe": "1d",
            },
        ),
        RuleVariant(
            variant_id="test.failed_strength_acceptance",
            family_id="failed_strength_acceptance",
            direction="negative",
            detector="failed_strength_acceptance",
            params={
                "acceptance_window": 5,
                "min_recent_time_above": 0.2,
                "min_prior_signal": 0.2,
                "trigger": "viscosity_loss",
                "max_relative_slope": 1.0,
                "timeframe": "1d",
            },
        ),
        RuleVariant(
            variant_id="test.lower_high_rollover",
            family_id="lower_high_rollover",
            direction="negative",
            detector="lower_high_rollover",
            params={
                "lookback": 5,
                "recent_window": 3,
                "min_prior_high": 1.0,
                "min_lower_high_gap": 0.1,
                "require_below_viscosity": False,
                "max_relative_slope": 1.0,
                "timeframe": "1d",
            },
        ),
    ]

    for variant in variants:
        mask = detect_variant_events(frame, variant)
        assert mask.index.equals(frame.index)
        assert mask.dtype == bool


def test_frozen_indicator_behavior_survivor_detectors_return_aligned_masks() -> None:
    frame = _analysis_frame()
    frame["relative_component"] = (
        [0.1, 0.2, 0.4, 0.8, 1.1, 0.7, 0.5, 0.3, 0.1, -0.1]
        + [0.0, 0.1, 0.2, 0.5, 0.9, 0.6, 0.4, 0.2, 0.0, -0.2]
        + [0.1] * 60
    )[: len(frame)]
    frame["gradient_driver"] = (
        [0.1, 0.4, 0.8, 1.2, 1.5, 1.1, 0.8, 0.5, 0.2, -0.1]
        + [0.1, 0.5, 0.9, 1.4, 1.8, 1.2, 0.9, 0.4, 0.0, -0.2]
        + [0.1] * 60
    )[: len(frame)]
    frame["viscosity"] = frame["final_signal"].ewm(span=5, adjust=False).mean() + 0.2
    frame["grammar_pressure_area_delta_5"] = 0.0
    frame["grammar_time_above_viscosity_20"] = 10.0
    frame["grammar_viscosity_cross_count_20"] = 1.0
    frame.loc[frame.index[15], "grammar_bearish_divergence_20"] = True
    variants = [
        RuleVariant(
            variant_id="test.relative_failed_breakout_warning",
            family_id="relative_failed_breakout_frozen",
            direction="negative",
            detector="relative_failed_breakout_warning",
            params={
                "lookback": 5,
                "fail_window": 4,
                "context_window": 5,
                "min_breakout_margin": 0.0,
                "min_gradient": 0.0,
                "gradient_diff_window": 3,
                "require_viscosity_loss": False,
                "min_signal": -10.0,
                "min_viscosity": -10.0,
                "max_relative_component": 10.0,
                "max_pressure_area_delta": 10.0,
                "max_prior_relative_high": 10.0,
                "min_time_above_viscosity_20": 0.0,
                "min_viscosity_cross_count_20": 0.0,
                "min_compression": 0.0,
                "timeframe": "1d",
            },
        ),
        RuleVariant(
            variant_id="test.bearish_divergence_fade_warning",
            family_id="bearish_divergence_fade_frozen",
            direction="negative",
            detector="bearish_divergence_fade_warning",
            params={
                "lookback": 5,
                "recent_window": 3,
                "context_window": 20,
                "min_prior_signal_high": 0.0,
                "min_lower_high_gap": 0.1,
                "min_gradient": 0.0,
                "gradient_diff_window": 3,
                "timeframe": "12h",
            },
        ),
        RuleVariant(
            variant_id="test.failed_baseline_breakout_warning",
            family_id="failed_baseline_breakout_frozen",
            direction="negative",
            detector="failed_baseline_breakout_warning",
            params={
                "lookback": 5,
                "recent_window": 3,
                "context_window": 10,
                "min_prior_signal_high": 0.0,
                "min_lower_high_gap": 0.1,
                "require_gradient_fade": False,
                "timeframe": "1d",
            },
        ),
    ]

    for variant in variants:
        mask = detect_variant_events(frame, variant)
        assert mask.index.equals(frame.index)
        assert mask.dtype == bool
        assert mask.any()


def test_all_component_strict_survivor_detectors_return_aligned_masks() -> None:
    frame = _analysis_frame()
    frame["gradient_driver"] = (
        [0.1, 0.5, 1.0, 1.6, 2.0, 1.5, 1.0, 0.7, 0.3, -0.1]
        + [0.2, 0.7, 1.2, 1.8, 2.1, 1.4, 0.9, 0.4, 0.0, -0.2]
        + [0.1] * 60
    )[: len(frame)]
    frame["relative_component"] = (
        [0.1, 0.4, 0.8, 1.2, 1.5, 0.9, 0.6, 0.2, 0.0, -0.2]
        + [0.2, 0.5, 0.9, 1.3, 1.1, 0.7, 0.4, 0.0, -0.1, -0.3]
        + [0.1] * 60
    )[: len(frame)]
    frame["target"] = pd.Series(
        [100, 102, 106, 115, 130, 125, 120, 116, 112, 110]
        + [112, 116, 125, 145, 165, 150, 140, 132, 128, 124]
        + [125 + idx for idx in range(60)],
        index=frame.index,
        dtype=float,
    )
    variants = [
        RuleVariant(
            variant_id="test.overbought_pressure_cross_down_warning",
            family_id="stoch_overbought_cross_down_frozen",
            direction="negative",
            detector="overbought_pressure_cross_down_warning",
            params={"context_window": 20, "high_level": 1.5, "loss_level": 1.0, "min_gradient": 0.0},
        ),
        RuleVariant(
            variant_id="test.bear_pressure_cross_from_high_warning",
            family_id="dmi_bear_cross_from_high_frozen",
            direction="negative",
            detector="bear_pressure_cross_from_high_warning",
            params={"context_window": 10, "high_level": 1.0, "max_relative_slope": 1.0},
        ),
        RuleVariant(
            variant_id="test.volatility_bulge_exhaustion_warning",
            family_id="volatility_bulge_exhaustion_frozen",
            direction="negative",
            detector="volatility_bulge_exhaustion_warning",
            params={"context_window": 10, "high_level": 1.0, "range_window": 5, "range_quantile": 0.6},
        ),
        RuleVariant(
            variant_id="test.late_cycle_leader_exhaustion_warning",
            family_id="late_cycle_leader_exhaustion_frozen",
            direction="negative",
            detector="late_cycle_leader_exhaustion_warning",
            params={
                "lookback": 5,
                "recent_window": 3,
                "context_window": 10,
                "signal_high_level": 1.0,
                "min_relative_prior_high": 0.5,
                "min_relative_lower_high_gap": 0.05,
            },
        ),
    ]

    for variant in variants:
        mask = detect_variant_events(frame, variant)
        assert mask.index.equals(frame.index)
        assert mask.dtype == bool
        assert mask.any()


def test_lower_high_rollover_optional_feature_filters() -> None:
    frame = _analysis_frame()
    base_variant = RuleVariant(
        variant_id="test.lower_high_rollover",
        family_id="lower_high_rollover",
        direction="negative",
        detector="lower_high_rollover",
        params={
            "lookback": 5,
            "recent_window": 3,
            "min_prior_high": 1.0,
            "min_lower_high_gap": 0.1,
            "require_below_viscosity": False,
            "max_relative_slope": 1.0,
            "timeframe": "1d",
        },
    )
    base_mask = detect_variant_events(frame, base_variant)
    event_index = base_mask[base_mask].index[0]
    frame["grammar_fast_slow_pressure_gap"] = -1.0
    frame["grammar_pressure_area_balance_20"] = 10.0
    frame["grammar_pressure_distance"] = 0.0
    frame["grammar_time_above_viscosity_5"] = 5.0
    frame["grammar_time_above_viscosity_10"] = 10.0
    frame.loc[event_index, "grammar_fast_slow_pressure_gap"] = 0.25
    frame.loc[event_index, "grammar_pressure_area_balance_20"] = 2.0
    frame.loc[event_index, "grammar_pressure_distance"] = -1.0
    frame.loc[event_index, "grammar_time_above_viscosity_5"] = 0.0
    frame.loc[event_index, "grammar_time_above_viscosity_10"] = 4.0

    filtered_variant = RuleVariant(
        variant_id="test.lower_high_rollover.filtered",
        family_id="lower_high_rollover",
        direction="negative",
        detector="lower_high_rollover",
        params={
            **base_variant.params,
            "min_fast_slow_pressure_gap": 0.0,
            "max_pressure_area_balance": 5.0,
            "max_pressure_distance": -0.5,
            "max_time_above_viscosity_5": 1.0,
            "max_time_above_viscosity_10": 5.0,
        },
    )
    filtered_mask = detect_variant_events(frame, filtered_variant)

    assert filtered_mask.loc[event_index]
    assert filtered_mask.sum() < base_mask.sum()


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


def test_grammar_search_meta_summaries_build_review_outputs(tmp_path) -> None:
    specs = load_rule_search_grid(_grid(tmp_path))
    variants = expand_rule_variants(specs, timeframes=["1d"])
    records = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "date": pd.Timestamp(f"2024-0{idx + 1}-10"),
                "timeframe": "1d",
                "benchmark": "MEME_BASKET",
                "variant_id": variants[0].variant_id,
                "family_id": variants[0].family_id,
                "detector": variants[0].detector,
                "direction": variants[0].direction,
                "params": "{}",
                "entry_lag_bars": 1,
                "entry_date": pd.Timestamp(f"2024-0{idx + 1}-11"),
                "cooldown_bars": 1,
                "event_cluster_id": f"2024-0{idx + 1}",
                "forward_return_3": 0.05,
                "forward_relative_return_3": 0.03,
                "forward_return_7": 0.08,
                "forward_relative_return_7": 0.05,
                "forward_return_14": 0.12,
                "forward_relative_return_14": 0.07,
                "forward_return_30": 0.15,
                "forward_relative_return_30": 0.09,
                "max_drawdown_30": -0.02,
            }
            for idx, symbol in enumerate(["AAA", "BBB", "CCC"])
        ]
    )
    summary = summarize_grammar_search_records(records, variants=variants, min_sample_size=3)

    robustness = family_timeframe_robustness(summary)
    duplicates = duplicate_outcome_clusters(pd.concat([summary, summary], ignore_index=True))
    mixed_records = records.copy()
    mixed_records.loc[mixed_records.index[0], "timeframe"] = "4h"
    mixed_records.loc[mixed_records.index[0], "forward_relative_return_180"] = 0.22
    queue = chart_review_queue(summary, mixed_records, top_variant_count=1)
    validation_records = pd.concat([records, records.assign(date=pd.Timestamp("2024-04-10"))], ignore_index=True)
    validation = time_split_validation(summary, validation_records, min_validation_sample=1)

    assert robustness.iloc[0]["family_id"] == "zone_reclaim_retest"
    assert "direction" in robustness.columns
    assert not duplicates.empty
    assert "review_outcome" in queue.columns
    assert queue.loc[queue["timeframe"] == "4h", "review_outcome_column"].iloc[0] == "forward_relative_return_180"
    assert "validation_status" in validation.columns


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


def test_strict_baseline_referee_builds_variant_evidence(tmp_path) -> None:
    summary, records, ranked, _family_summary, _variants = run_grammar_search(
        {"1d": {"AAA": _analysis_frame(), "BBB": _analysis_frame()}},
        grid_path=_grid(tmp_path),
        timeframes=["1d"],
        min_sample_size=1,
        cooldown_bars_by_timeframe={"1d": 1},
    )

    referee = strict_baseline_referee(
        ranked,
        records,
        {"1d": {"AAA": _analysis_frame(), "BBB": _analysis_frame()}},
        null_iterations=3,
        random_seed=1,
        min_validation_sample=1,
    )

    assert not summary.empty
    assert not referee.empty
    assert {
        "passes_both_baselines",
        "matched_null_p_value",
        "strict_survivor",
        "validation_status",
    }.issubset(referee.columns)


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
            "--strict-referee",
            "--strict-null-iterations",
            "3",
        ]
    )

    assert GRAMMAR_SEARCH_MODEL == "riskflow_grammar_search_v0"
    assert status == 0
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_ranked.csv").exists()
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_family_timeframe_robustness.csv").exists()
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_duplicate_clusters.csv").exists()
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_chart_review_queue.csv").exists()
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_time_split_validation.csv").exists()
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_strict_referee.csv").exists()
    assert (tmp_path / "reports" / "grammar_search" / "grammar_search_manifest.yaml").exists()
    assert (tmp_path / "obsidian" / "reports" / "latest_grammar_search.md").exists()
