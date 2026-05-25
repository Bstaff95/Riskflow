from __future__ import annotations

from dataclasses import dataclass


CORE_SIGNAL_V0 = "core_signal_v0"
CORE_SIGNAL_V0_FORMULA_VERSION = "riskflow_core_signal_v0_2026_05_24"
DEFAULT_SIGNAL_RESEARCH_COOLDOWN_BARS = 30
DEFAULT_SIGNAL_RESEARCH_ENTRY_LAG_BARS = 1


@dataclass(frozen=True)
class SignalSpec:
    signal_id: str
    role: str
    family: str
    version: int
    lookback: int | None
    trigger: float
    scale_type: str
    direction: str
    description: str
    allowed_downstream_use: tuple[str, ...] = ()


SIGNAL_REGISTRY: dict[str, SignalSpec] = {
    CORE_SIGNAL_V0: SignalSpec(
        signal_id=CORE_SIGNAL_V0,
        role="core",
        family="pine_style_weight_scaled_oscillator",
        version=0,
        lookback=None,
        trigger=0.0,
        scale_type="oscillator_z_like",
        direction="higher_is_stronger",
        description="Incumbent Pine-style price plus relative weight-scaled oscillator.",
        allowed_downstream_use=("scan", "states", "scoring", "event_study", "tradingview"),
    ),
    "relative_vol_adj_momentum_20": SignalSpec(
        signal_id="relative_vol_adj_momentum_20",
        role="challenger",
        family="relative_vol_adj_momentum",
        version=0,
        lookback=20,
        trigger=1.0,
        scale_type="vol_adjusted_relative_log_return",
        direction="higher_is_stronger",
        description="20-bar relative momentum divided by trailing relative realized volatility.",
    ),
    "relative_vol_adj_momentum_50": SignalSpec(
        signal_id="relative_vol_adj_momentum_50",
        role="challenger",
        family="relative_vol_adj_momentum",
        version=0,
        lookback=50,
        trigger=1.0,
        scale_type="vol_adjusted_relative_log_return",
        direction="higher_is_stronger",
        description="50-bar relative momentum divided by trailing relative realized volatility.",
    ),
    "relative_percentile_strength_50": SignalSpec(
        signal_id="relative_percentile_strength_50",
        role="challenger",
        family="relative_percentile_strength",
        version=0,
        lookback=50,
        trigger=70.0,
        scale_type="percentile_0_100",
        direction="higher_is_stronger",
        description="Percentile rank of the relative log ratio against its own 50-bar history.",
    ),
    "relative_percentile_strength_100": SignalSpec(
        signal_id="relative_percentile_strength_100",
        role="challenger",
        family="relative_percentile_strength",
        version=0,
        lookback=100,
        trigger=70.0,
        scale_type="percentile_0_100",
        direction="higher_is_stronger",
        description="Percentile rank of the relative log ratio against its own 100-bar history.",
    ),
    "cross_sectional_relative_rank_20": SignalSpec(
        signal_id="cross_sectional_relative_rank_20",
        role="challenger",
        family="cross_sectional_relative_rank",
        version=0,
        lookback=20,
        trigger=70.0,
        scale_type="cross_sectional_percentile_0_100",
        direction="higher_is_stronger",
        description="Percentile rank of 20-bar relative momentum across the peer universe.",
    ),
    "cross_sectional_relative_rank_50": SignalSpec(
        signal_id="cross_sectional_relative_rank_50",
        role="challenger",
        family="cross_sectional_relative_rank",
        version=0,
        lookback=50,
        trigger=70.0,
        scale_type="cross_sectional_percentile_0_100",
        direction="higher_is_stronger",
        description="Percentile rank of 50-bar relative momentum across the peer universe.",
    ),
    "baseline_raw_relative_return_20": SignalSpec(
        signal_id="baseline_raw_relative_return_20",
        role="baseline",
        family="raw_relative_return",
        version=0,
        lookback=20,
        trigger=0.0,
        scale_type="relative_return",
        direction="higher_is_stronger",
        description="Simple 20-bar asset-versus-benchmark relative return.",
    ),
    "baseline_raw_relative_return_50": SignalSpec(
        signal_id="baseline_raw_relative_return_50",
        role="baseline",
        family="raw_relative_return",
        version=0,
        lookback=50,
        trigger=0.0,
        scale_type="relative_return",
        direction="higher_is_stronger",
        description="Simple 50-bar asset-versus-benchmark relative return.",
    ),
    "baseline_simple_relative_momentum_rank_20": SignalSpec(
        signal_id="baseline_simple_relative_momentum_rank_20",
        role="baseline",
        family="simple_relative_momentum_rank",
        version=0,
        lookback=20,
        trigger=70.0,
        scale_type="cross_sectional_percentile_0_100",
        direction="higher_is_stronger",
        description="Simple cross-sectional rank of 20-bar relative momentum.",
    ),
    "baseline_simple_relative_momentum_rank_50": SignalSpec(
        signal_id="baseline_simple_relative_momentum_rank_50",
        role="baseline",
        family="simple_relative_momentum_rank",
        version=0,
        lookback=50,
        trigger=70.0,
        scale_type="cross_sectional_percentile_0_100",
        direction="higher_is_stronger",
        description="Simple cross-sectional rank of 50-bar relative momentum.",
    ),
    "baseline_ratio_trend_20": SignalSpec(
        signal_id="baseline_ratio_trend_20",
        role="baseline",
        family="ratio_trend",
        version=0,
        lookback=20,
        trigger=0.0,
        scale_type="relative_log_ratio_minus_mean",
        direction="higher_is_stronger",
        description="Relative log ratio above or below its 20-bar mean.",
    ),
    "baseline_ratio_trend_50": SignalSpec(
        signal_id="baseline_ratio_trend_50",
        role="baseline",
        family="ratio_trend",
        version=0,
        lookback=50,
        trigger=0.0,
        scale_type="relative_log_ratio_minus_mean",
        direction="higher_is_stronger",
        description="Relative log ratio above or below its 50-bar mean.",
    ),
    "baseline_buy_and_hold_relative": SignalSpec(
        signal_id="baseline_buy_and_hold_relative",
        role="baseline",
        family="buy_and_hold_relative",
        version=0,
        lookback=None,
        trigger=0.0,
        scale_type="relative_log_ratio_since_first_valid",
        direction="higher_is_stronger",
        description="Asset-versus-benchmark relative log ratio since first valid observation.",
    ),
}


def get_signal_spec(signal_id: str) -> SignalSpec:
    try:
        return SIGNAL_REGISTRY[signal_id]
    except KeyError as exc:
        raise KeyError(f"Unknown signal_id: {signal_id}") from exc


def signal_ids_by_role(role: str) -> tuple[str, ...]:
    return tuple(spec.signal_id for spec in SIGNAL_REGISTRY.values() if spec.role == role)
