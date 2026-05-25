from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from riskflow.score_registry import OPPORTUNITY_SCORE_V0, get_score_spec
from riskflow.score_research import (
    BUCKET_SUMMARY_COLUMNS,
    IC_SUMMARY_COLUMNS,
    RECORD_COLUMNS,
    SCORE_SUMMARY_COLUMNS,
    run_score_research,
    summarize_rank_ic,
    summarize_score_buckets,
)


def _frame(score_offset: float, return_rate: float = 1.01, periods: int = 40) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    target = pd.Series(100.0 * np.cumprod(np.full(periods, return_rate)), index=dates)
    benchmark = pd.Series(100.0 * np.cumprod(np.full(periods, 1.004)), index=dates)
    base = np.linspace(10.0 + score_offset, 90.0 + score_offset, periods)
    return pd.DataFrame(
        {
            "target": target,
            "benchmark": benchmark,
            "opportunity_score_v0": base.clip(0.0, 100.0),
            "trader_score_v0": (base * 0.9).clip(0.0, 100.0),
            "leader_quality_score": (base + 5.0).clip(0.0, 100.0),
            "compression_quality_score": np.linspace(80.0, 20.0, periods),
            "relative_accumulation_score": base.clip(0.0, 100.0),
            "setup_readiness_score": np.linspace(0.0, 100.0, periods),
            "extension_risk_score": np.linspace(90.0 - score_offset, 10.0, periods).clip(0.0, 100.0),
            "data_quality_score": 100.0,
        },
        index=dates,
    )


def test_score_registry_accepts_known_ids_and_rejects_unknown_ids():
    assert get_score_spec(OPPORTUNITY_SCORE_V0).active is True
    with pytest.raises(KeyError):
        get_score_spec("unknown_score")


def test_score_research_outputs_required_columns_and_forward_returns():
    frames = {
        "AAA": _frame(0.0, return_rate=1.008),
        "BBB": _frame(5.0, return_rate=1.010),
        "CCC": _frame(10.0, return_rate=1.012),
        "DDD": _frame(15.0, return_rate=1.014),
        "EEE": _frame(20.0, return_rate=1.016),
    }

    score_summary, bucket_summary, ic_summary, records = run_score_research(
        frames,
        bucket_count=10,
        min_symbols_per_date=5,
        min_bucket_sample_size=1,
    )

    assert list(records.columns) == RECORD_COLUMNS
    assert list(bucket_summary.columns) == BUCKET_SUMMARY_COLUMNS
    assert list(ic_summary.columns) == IC_SUMMARY_COLUMNS
    assert list(score_summary.columns) == SCORE_SUMMARY_COLUMNS
    assert records["forward_relative_return_14"].notna().any()
    assert records["rank_percentile"].between(0.0, 1.0).all()
    assert records["bucket"].dropna().astype(int).between(1, 5).all()
    assert records["bucket_fallback"].all()


def test_bucket_assignment_is_datewise_and_extension_risk_is_inverted():
    frames = {
        "AAA": _frame(0.0),
        "BBB": _frame(20.0),
        "CCC": _frame(40.0),
    }
    _score_summary, _bucket_summary, _ic_summary, records = run_score_research(
        frames,
        bucket_count=3,
        min_symbols_per_date=3,
        min_bucket_sample_size=1,
    )
    first_date = records["date"].min()
    opportunity = records[
        (records["score_id"] == "opportunity_score_v0")
        & (records["date"] == first_date)
    ].sort_values("score_value")
    extension = records[
        (records["score_id"] == "extension_risk_score")
        & (records["date"] == first_date)
    ].sort_values("raw_score_value")

    assert list(opportunity["bucket"].astype(int)) == [1, 2, 3]
    assert list(extension["bucket"].astype(int)) == [3, 2, 1]


def test_rank_ic_handles_ties_missing_values_and_insufficient_symbols():
    records = pd.DataFrame(
        {
            "score_id": ["opportunity_score_v0"] * 6,
            "date": [pd.Timestamp("2024-01-01")] * 3 + [pd.Timestamp("2024-01-02")] * 3,
            "score_value": [1.0, 1.0, 3.0, 1.0, np.nan, 2.0],
            "forward_relative_return_3": [0.01, 0.01, 0.03, 0.02, 0.03, 0.04],
            "forward_relative_return_7": [0.01, 0.01, 0.03, 0.02, 0.03, 0.04],
            "forward_relative_return_14": [0.01, 0.01, 0.03, 0.02, 0.03, 0.04],
            "forward_relative_return_30": [0.01, 0.01, 0.03, 0.02, 0.03, 0.04],
        }
    )

    summary = summarize_rank_ic(records, min_symbols_per_date=3)
    row = summary[(summary["score_id"] == "opportunity_score_v0") & (summary["horizon"] == 14)].iloc[0]

    assert row["valid_dates"] == 1
    assert row["mean_rank_ic"] > 0.0
    assert row["classification"] == "inconclusive"


def test_bucket_summary_spread_and_concentration_diagnostics():
    records = pd.DataFrame(
        {
            "score_id": ["opportunity_score_v0"] * 6,
            "bucket": [1, 1, 1, 2, 2, 2],
            "symbol": ["AAA", "AAA", "AAA", "BBB", "CCC", "DDD"],
            "date": pd.date_range("2024-01-01", periods=6, freq="D"),
            "event_cluster_id": ["2024-01"] * 6,
            "bucket_fallback": False,
            "forward_relative_return_3": [-0.02, -0.01, 0.0, 0.02, 0.03, 0.04],
            "forward_relative_return_7": [-0.02, -0.01, 0.0, 0.02, 0.03, 0.04],
            "forward_relative_return_14": [-0.02, -0.01, 0.0, 0.02, 0.03, 0.04],
            "forward_relative_return_30": [-0.02, -0.01, 0.0, 0.02, 0.03, 0.04],
            "max_drawdown_14": [-0.05] * 6,
            "max_drawdown_30": [-0.08] * 6,
        }
    )

    summary = summarize_score_buckets(records, min_bucket_sample_size=1)
    low_bucket = summary[(summary["score_id"] == "opportunity_score_v0") & (summary["bucket"] == 1)].iloc[0]
    high_bucket = summary[(summary["score_id"] == "opportunity_score_v0") & (summary["bucket"] == 2)].iloc[0]

    assert high_bucket["top_minus_bottom_spread_14"] > 0.0
    assert low_bucket["classification"] == "fragile"
    assert low_bucket["max_symbol_share"] == 1.0


def test_low_bucket_sample_sizes_classify_as_inconclusive():
    frames = {"AAA": _frame(0.0, periods=10), "BBB": _frame(5.0, periods=10)}

    _score_summary, bucket_summary, _ic_summary, _records = run_score_research(
        frames,
        bucket_count=2,
        min_bucket_sample_size=999,
    )

    assert set(bucket_summary["classification"]) == {"inconclusive"}
