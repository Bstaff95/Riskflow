from __future__ import annotations

import pandas as pd
import pytest

from riskflow.indicator_behavior import (
    IndicatorBehaviorVariant,
    detect_indicator_behavior_events,
    first_batch_indicator_behavior_concepts,
    indicator_behavior_primitive_ids,
    load_indicator_behavior_concepts,
    load_indicator_behavior_primitive_registry,
    run_indicator_behavior_search,
    summarize_indicator_behavior_concepts,
)


def test_indicator_behavior_library_registers_all_researched_concepts() -> None:
    concepts = load_indicator_behavior_concepts()
    summary = summarize_indicator_behavior_concepts(concepts)

    assert summary["concept_count"] == 99
    assert summary["priority_counts"] == {"backlog": 69, "first_batch": 30}
    assert summary["direction_counts"] == {"positive": 44, "negative": 44, "regime": 11}
    assert summary["implementation_status_counts"] == {
        "directly_derivable": 23,
        "existing_sidecar_column": 25,
        "needs_sidecar": 39,
        "needs_multi_timeframe_join": 7,
        "needs_peer_basket_context": 5,
    }


def test_first_batch_includes_riskflow_native_warning_and_repair_concepts() -> None:
    first_batch = first_batch_indicator_behavior_concepts(load_indicator_behavior_concepts())
    first_batch_ids = {concept.concept_id for concept in first_batch}

    assert len(first_batch_ids) == 30
    assert "relative_lower_high_warning" in first_batch_ids
    assert "failed_price_breakout_signal_confirm" in first_batch_ids
    assert "deep_below_baseline_repair" in first_batch_ids
    assert "hidden_relative_bull_divergence" in first_batch_ids


def test_indicator_behavior_primitives_are_registered() -> None:
    registry = load_indicator_behavior_primitive_registry()
    primitive_ids = indicator_behavior_primitive_ids(registry)

    assert len(primitive_ids) == 64
    assert "signal_lower_high" in primitive_ids
    assert "viscosity_reclaim" in primitive_ids
    assert "gradient_positive_fading" in primitive_ids
    assert "relative_failed_breakout" in primitive_ids


def test_concept_loader_rejects_unknown_primitives(tmp_path) -> None:
    registry_path = tmp_path / "primitive_registry.yaml"
    registry_path.write_text(
        """
model: riskflow_indicator_behavior_primitives_v0
primitive_families:
  demo:
    primitives:
      known_primitive:
        definition: known
        parameters: {}
        status: directly_derivable
""",
        encoding="utf-8",
    )
    concept_path = tmp_path / "concept_library.yaml"
    concept_path.write_text(
        """
model: riskflow_indicator_behavior_concept_library_v0
concepts:
  - id: bad_concept
    family: demo
    direction: positive
    priority: backlog
    primitives: [unknown_primitive]
    riskflow_inputs: [final_signal]
    implementation_status: directly_derivable
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown indicator behavior primitives"):
        load_indicator_behavior_concepts(concept_path, primitive_registry_path=registry_path)


def test_indicator_behavior_detector_returns_aligned_mask() -> None:
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    signal = pd.Series(
        [-0.8, -0.7, -0.6, -0.4, -0.2, 0.1, 0.4, 0.8, 1.3, 1.8, 1.7, 1.4, 1.2, 0.9, 0.7]
        + [0.5, 0.4, 0.3, 0.1, -0.1] * 5,
        index=dates,
        dtype=float,
    ).iloc[:40]
    frame = pd.DataFrame(
        {
            "target": pd.Series(range(100, 140), index=dates, dtype=float),
            "benchmark": pd.Series(range(100, 140), index=dates, dtype=float),
            "final_signal": signal,
            "viscosity": signal.ewm(span=5, adjust=False).mean(),
            "relative_component": signal.diff().fillna(0.0),
            "gradient_driver": signal,
            "compression_score": 80.0,
            "volume": 1000.0,
        },
        index=dates,
    )
    variant = IndicatorBehaviorVariant(
        variant_id="test.extended_above_baseline_exhaustion",
        family_id="extended_above_baseline_exhaustion",
        direction="negative",
        detector="primitive_context_all",
        params={
            "timeframe": "1d",
            "context_window": 10,
            "primitives": ["time_above_viscosity", "signal_above_high_band", "gradient_positive_fading"],
        },
    )

    mask = detect_indicator_behavior_events(frame, variant)

    assert mask.index.equals(frame.index)
    assert mask.dtype == bool
    assert mask.any()


def test_run_indicator_behavior_search_first_batch_smoke() -> None:
    dates = pd.date_range("2024-01-01", periods=90, freq="D")
    signal = pd.Series(([1.8, 1.6, 1.4, 1.2, 0.9, 0.5, 0.1, -0.2, -0.4, -0.1] * 9), index=dates)
    frame = pd.DataFrame(
        {
            "target": pd.Series([100.0 + idx for idx in range(90)], index=dates),
            "benchmark": pd.Series([100.0 + idx * 0.5 for idx in range(90)], index=dates),
            "benchmark_used": "MEME_BASKET",
            "final_signal": signal,
            "viscosity": signal.ewm(span=5, adjust=False).mean(),
            "relative_component": signal.diff().fillna(0.0),
            "gradient_driver": signal,
            "compression_score": 80.0,
            "volume": 1000.0,
        },
        index=dates,
    )

    summary, records, ranked, family_summary, variants = run_indicator_behavior_search(
        {"1d": {"TEST": frame}},
        timeframes=["1d"],
        priority="first_batch",
        context_windows=[10],
        min_sample_size=1,
    )

    assert len(variants) == 30
    assert set(summary["variant_id"]) == {variant.variant_id for variant in variants}
    assert {"variant_id", "sample_size", "classification"}.issubset(summary.columns)
    assert {"variant_id", "family_id", "timeframe"}.issubset(ranked.columns)
    assert {"family_id", "timeframe"}.issubset(family_summary.columns)
    assert records.empty or {"variant_id", "symbol", "date"}.issubset(records.columns)
