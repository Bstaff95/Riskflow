from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from .config import UniverseConfig
from .research_outcomes import (
    HORIZONS,
    apply_event_cooldown,
    benchmark_label_at,
    event_cluster_id,
    forward_relative_return,
)


VISUAL_REVIEW_MODEL = "visual_breakout_review_v0"

VISUAL_REVIEW_COLUMNS = [
    "symbol",
    "name",
    "date",
    "timeframe",
    "benchmark",
    "visual_review_model",
    "event_name",
    "event_cluster_id",
    "forward_relative_return_3",
    "forward_relative_return_7",
    "forward_relative_return_14",
    "forward_relative_return_30",
    "final_signal",
    "viscosity",
    "relative_component",
    "price_component",
    "compression_score",
    "state",
    "setup_tags",
    "pattern_score",
    "signal_above_viscosity",
    "recent_viscosity_reclaim",
    "pre_event_signal_band_share",
    "signal_zone",
    "image_path",
    "notes",
]


@dataclass(frozen=True)
class VisualReviewSettings:
    event_mode: str = "breakout"
    timeframe: str = "1d"
    horizon: int = 30
    min_forward_relative_return: float = 0.30
    entry_lag_bars: int = 1
    cooldown_bars: int = 30
    min_history_bars: int = 40
    min_signal_std: float = 0.02
    lookback_bars: int = 80
    forward_bars: int = 30
    max_events: int = 40
    max_events_per_symbol: int = 3


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(np.nan, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _recent_cross_above(signal: pd.Series, baseline: pd.Series, lookback: int = 10) -> pd.Series:
    crossed = (signal > baseline) & (signal.shift(1) <= baseline.shift(1))
    return crossed.rolling(lookback, min_periods=1).max().fillna(0.0).astype(bool)


def _signal_band_share(signal: pd.Series, lookback: int = 20, low: float = -2.25, high: float = -0.75) -> pd.Series:
    in_band = signal.between(low, high)
    return in_band.rolling(lookback, min_periods=1).mean()


def _signal_zone(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    numeric = float(value)
    if numeric <= -2.0:
        return "deep_negative"
    if numeric <= -1.0:
        return "negative_chop_band"
    if numeric < 0.0:
        return "below_zero"
    if numeric < 1.5:
        return "constructive"
    if numeric < 2.0:
        return "extended"
    return "overheated"


def _compression_impulse_retest(
    frame: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    signal = _numeric(frame, "final_signal")
    viscosity = _numeric(frame, "viscosity")
    relative = _numeric(frame, "relative_component")
    compression = _numeric(frame, "compression_score")

    band_share = _signal_band_share(signal, lookback=60, low=-2.35, high=-0.65)
    compression_support = compression.rolling(60, min_periods=10).median() >= 55.0
    coiled = (band_share >= 0.30) | compression_support

    prior_low = signal.rolling(60, min_periods=10).min()
    recent_high = signal.rolling(24, min_periods=5).max()
    impulse_range = recent_high - prior_low
    impulse_seen = (recent_high >= 1.25) & (impulse_range >= 2.0)

    distance = signal - viscosity
    rested_to_viscosity = distance.between(-0.30, 0.45) & signal.gt(-0.35)
    pulled_back_from_impulse = (recent_high - signal) >= 0.60

    relative_improving = relative.gt(-0.25) | (relative - relative.shift(10)).gt(0.45)
    coiled_ready = coiled.shift(5)
    coiled_ready = coiled_ready.where(coiled_ready.notna(), False).astype(bool)
    mask = coiled_ready & impulse_seen & rested_to_viscosity & pulled_back_from_impulse & relative_improving

    retest_quality = (1.0 - (distance.abs() / 0.45)).clip(lower=0.0, upper=1.0)
    score = (
        band_share.fillna(0.0) * 35.0
        + impulse_range.clip(lower=0.0, upper=4.0).fillna(0.0) * 8.0
        + retest_quality.fillna(0.0) * 20.0
        + compression.fillna(0.0).clip(lower=0.0, upper=100.0) * 0.15
        + (relative - relative.shift(10)).clip(lower=0.0, upper=2.0).fillna(0.0) * 8.0
    )
    return mask.fillna(False), score


def _coil_viscosity_reclaim(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    signal = _numeric(frame, "final_signal")
    viscosity = _numeric(frame, "viscosity")
    relative = _numeric(frame, "relative_component")
    compression = _numeric(frame, "compression_score")

    band_share = _signal_band_share(signal, lookback=60, low=-2.35, high=-0.65)
    prior_low = signal.rolling(60, min_periods=10).min()
    prior_high = signal.rolling(20, min_periods=5).max()
    prior_compression = compression.rolling(40, min_periods=10).median()
    relative_improvement = relative - relative.shift(12)
    signal_improvement = signal - signal.shift(12)

    coiled_in_lower_zone = (band_share >= 0.25) & (prior_low <= -1.45)
    compressed_or_tight = prior_compression.ge(40.0) | band_share.ge(0.40)
    reclaim = (signal > viscosity) & (signal.shift(1) <= viscosity.shift(1))

    early_enough = signal.between(-1.60, 0.85)
    not_recently_overheated = prior_high.lt(1.50)
    improving = relative_improvement.gt(0.20) | signal_improvement.gt(0.35) | relative.gt(-0.50)

    mask = (
        coiled_in_lower_zone
        & compressed_or_tight
        & reclaim
        & early_enough
        & not_recently_overheated
        & improving
    )

    reclaim_distance = (signal - viscosity).clip(lower=0.0, upper=0.75) / 0.75
    early_zone_quality = (1.0 - (signal.abs() / 1.75)).clip(lower=0.0, upper=1.0)
    score = (
        band_share.fillna(0.0) * 35.0
        + reclaim_distance.fillna(0.0) * 20.0
        + early_zone_quality.fillna(0.0) * 15.0
        + relative_improvement.clip(lower=0.0, upper=2.0).fillna(0.0) * 8.0
        + signal_improvement.clip(lower=0.0, upper=2.0).fillna(0.0) * 5.0
        + compression.fillna(0.0).clip(lower=0.0, upper=100.0) * 0.10
    )
    return mask.fillna(False), score


def _event_candidates_for_symbol(
    symbol: str,
    name: str,
    frame: pd.DataFrame,
    *,
    settings: VisualReviewSettings,
) -> pd.DataFrame:
    target = _numeric(frame, "target")
    benchmark = _numeric(frame, "benchmark")
    final_signal = _numeric(frame, "final_signal")
    viscosity = _numeric(frame, "viscosity")
    relative_component = _numeric(frame, "relative_component")
    price_component = _numeric(frame, "price_component")
    compression_score = _numeric(frame, "compression_score")

    metrics = pd.DataFrame(index=frame.index)
    for horizon in HORIZONS:
        metrics[f"forward_relative_return_{horizon}"] = forward_relative_return(
            target,
            benchmark,
            horizon=horizon,
            entry_lag_bars=settings.entry_lag_bars,
        )

    horizon_column = f"forward_relative_return_{settings.horizon}"
    if horizon_column not in metrics.columns:
        raise ValueError(f"Unsupported visual review horizon: {settings.horizon}")

    history_ready = pd.Series(np.arange(len(frame)), index=frame.index) >= settings.min_history_bars
    signal_activity = final_signal.rolling(20, min_periods=5).std().fillna(0.0) >= settings.min_signal_std
    if settings.event_mode == "impulse-retest":
        mask, pattern_score = _compression_impulse_retest(frame)
        event_name = "compression_impulse_viscosity_retest_v0"
        event_note = "selected by indicator pattern: compression, impulse, viscosity retest"
        sort_series = pattern_score
    elif settings.event_mode == "coil-reclaim":
        mask, pattern_score = _coil_viscosity_reclaim(frame)
        event_name = "coil_viscosity_reclaim_v0"
        event_note = "selected by early indicator pattern: lower-zone coil, viscosity reclaim, relative improvement"
        sort_series = pattern_score
    elif settings.event_mode == "breakout":
        mask = metrics[horizon_column] >= settings.min_forward_relative_return
        pattern_score = pd.Series(np.nan, index=frame.index, dtype=float)
        event_name = "strong_forward_relative_breakout"
        event_note = "selected because forward relative return exceeded threshold"
        sort_series = pd.to_numeric(metrics[horizon_column], errors="coerce")
    elif settings.event_mode == "missed-breakout":
        horizon_return = pd.to_numeric(metrics[horizon_column], errors="coerce")
        recent_reclaim = _recent_cross_above(final_signal, viscosity, lookback=12)
        weak_visual_confirmation = (final_signal <= viscosity) | final_signal.lt(0.0)
        not_obvious_momentum = final_signal.lt(0.85) & relative_component.lt(0.75)
        mask = (
            horizon_return.ge(settings.min_forward_relative_return)
            & weak_visual_confirmation
            & not_obvious_momentum
            & ~recent_reclaim
        )
        pattern_score = (
            horizon_return.fillna(0.0) * 100.0
            + (0.85 - final_signal).clip(lower=0.0, upper=3.0).fillna(0.0) * 8.0
            + (viscosity - final_signal).clip(lower=0.0, upper=2.0).fillna(0.0) * 8.0
        )
        event_name = "missed_breakout_review_v0"
        event_note = "selected as a strong forward relative winner without obvious signal/viscosity confirmation"
        sort_series = pattern_score
    elif settings.event_mode == "bearish-weakness":
        horizon_return = pd.to_numeric(metrics[horizon_column], errors="coerce")
        prior_strength = final_signal.rolling(20, min_periods=5).max().shift(1)
        cross_below_viscosity = (final_signal < viscosity) & (final_signal.shift(1) >= viscosity.shift(1))
        zero_rejection_zone = prior_strength.gt(-0.20) & final_signal.lt(0.15)
        weakening_relative = relative_component.lt(0.0) | relative_component.diff(10).lt(-0.35)
        mask = (
            horizon_return.le(-0.12)
            & (cross_below_viscosity | zero_rejection_zone)
            & final_signal.lt(viscosity)
            & weakening_relative
        )
        pattern_score = (
            (-horizon_return).clip(lower=0.0, upper=1.5).fillna(0.0) * 70.0
            + (viscosity - final_signal).clip(lower=0.0, upper=2.5).fillna(0.0) * 10.0
            + prior_strength.clip(lower=0.0, upper=3.0).fillna(0.0) * 5.0
        )
        event_name = "bearish_weakness_review_v0"
        event_note = "selected as bearish/weakness grammar: loss of viscosity or zero rejection with poor forward relative return"
        sort_series = pattern_score
    elif settings.event_mode == "noisy-false-positive":
        horizon_return = pd.to_numeric(metrics[horizon_column], errors="coerce")
        signal_std = final_signal.rolling(20, min_periods=5).std()
        recent_signal_high = final_signal.rolling(20, min_periods=5).max()
        recent_viscosity_reclaim = _recent_cross_above(final_signal, viscosity, lookback=12)
        no_followthrough = horizon_return.le(0.08)
        poor_compression = compression_score.lt(45.0)
        choppy = signal_std.gt(0.70) & recent_signal_high.gt(0.25)
        mask = choppy & recent_viscosity_reclaim & no_followthrough & poor_compression
        pattern_score = (
            signal_std.clip(lower=0.0, upper=2.5).fillna(0.0) * 25.0
            + recent_signal_high.clip(lower=0.0, upper=3.0).fillna(0.0) * 10.0
            + (-horizon_return).clip(lower=0.0, upper=1.0).fillna(0.0) * 35.0
            + (45.0 - compression_score).clip(lower=0.0, upper=45.0).fillna(0.0)
        )
        event_name = "noisy_false_positive_review_v0"
        event_note = "selected as noisy false-positive grammar: volatile impulse/reclaim behavior without forward follow-through"
        sort_series = pattern_score
    else:
        raise ValueError(f"Unsupported visual review event mode: {settings.event_mode}")
    mask &= target.notna() & benchmark.notna() & final_signal.notna()
    mask &= history_ready & signal_activity
    mask = apply_event_cooldown(mask, settings.cooldown_bars)

    recent_reclaim = _recent_cross_above(final_signal, viscosity)
    band_share = _signal_band_share(final_signal)
    rows: list[dict[str, object]] = []
    for position, date in enumerate(frame.index):
        if not bool(mask.loc[date]):
            continue
        benchmark_label = benchmark_label_at(frame, date, default="benchmark")
        row = {
            "symbol": symbol,
            "name": name,
            "date": date,
            "timeframe": settings.timeframe,
            "benchmark": benchmark_label,
            "visual_review_model": VISUAL_REVIEW_MODEL,
            "event_name": event_name,
            "event_cluster_id": event_cluster_id(date),
            "final_signal": final_signal.loc[date],
            "viscosity": viscosity.loc[date],
            "relative_component": relative_component.loc[date],
            "price_component": price_component.loc[date],
            "compression_score": compression_score.loc[date],
            "state": frame["state"].loc[date] if "state" in frame.columns else pd.NA,
            "setup_tags": frame["setup_tags"].loc[date] if "setup_tags" in frame.columns else pd.NA,
            "pattern_score": pattern_score.loc[date],
            "signal_above_viscosity": bool(final_signal.loc[date] > viscosity.loc[date]),
            "recent_viscosity_reclaim": bool(recent_reclaim.loc[date]),
            "pre_event_signal_band_share": band_share.loc[date],
            "signal_zone": _signal_zone(final_signal.loc[date]),
            "image_path": "",
            "notes": event_note,
        }
        for horizon in HORIZONS:
            row[f"forward_relative_return_{horizon}"] = metrics.loc[date, f"forward_relative_return_{horizon}"]
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=VISUAL_REVIEW_COLUMNS)

    records = pd.DataFrame(rows)
    records["_sort_value"] = pd.to_numeric(sort_series.reindex(records["date"]).to_numpy(), errors="coerce")
    records["_position"] = [frame.index.get_loc(date) for date in records["date"]]
    records = records.sort_values("_sort_value", ascending=False)
    records = records.head(settings.max_events_per_symbol)
    return records


def build_visual_review_records(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    settings: VisualReviewSettings,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    assets = universe.asset_by_symbol
    for symbol, frame in analysis_frames.items():
        asset = assets.get(symbol)
        name = asset.name if asset is not None else symbol
        symbol_records = _event_candidates_for_symbol(symbol, name, frame, settings=settings)
        if not symbol_records.empty:
            rows.append(symbol_records)

    if not rows:
        return pd.DataFrame(columns=[*VISUAL_REVIEW_COLUMNS, "_sort_value", "_position"])

    records = pd.concat(rows, ignore_index=True)
    records = records.sort_values("_sort_value", ascending=False).head(settings.max_events)
    for column in VISUAL_REVIEW_COLUMNS:
        if column not in records.columns:
            records[column] = pd.NA
    return records[[*VISUAL_REVIEW_COLUMNS, "_sort_value", "_position"]]


def _style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor("#101418")
    ax.grid(True, color="#2a2f35", linewidth=0.7, alpha=0.8)
    ax.tick_params(colors="#b8c1cc", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#30363d")


def _plot_price_panel(ax: plt.Axes, raw: pd.DataFrame, symbol: str, x: np.ndarray) -> None:
    _style_axis(ax)
    open_ = pd.to_numeric(raw["open"], errors="coerce").to_numpy(dtype=float)
    high = pd.to_numeric(raw["high"], errors="coerce").to_numpy(dtype=float)
    low = pd.to_numeric(raw["low"], errors="coerce").to_numpy(dtype=float)
    close = pd.to_numeric(raw["close"], errors="coerce").to_numpy(dtype=float)
    width = 0.62

    for xpos, open_value, high_value, low_value, close_value in zip(x, open_, high, low, close):
        if np.isnan([open_value, high_value, low_value, close_value]).any():
            continue
        color = "#26a69a" if close_value >= open_value else "#ef5350"
        ax.vlines(xpos, low_value, high_value, color=color, linewidth=1.0, alpha=0.95)
        body_low = min(open_value, close_value)
        body_height = max(abs(close_value - open_value), max(abs(close_value) * 0.001, 1e-12))
        ax.add_patch(
            Rectangle(
                (xpos - width / 2.0, body_low),
                width,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.6,
                alpha=0.95,
            )
        )

    ax.set_title(f"{symbol} price", color="#e6edf3", loc="left", fontsize=11)
    ax.set_ylabel("Price", color="#b8c1cc")


def _plot_volume_panel(ax: plt.Axes, raw: pd.DataFrame, x: np.ndarray) -> None:
    _style_axis(ax)
    open_ = pd.to_numeric(raw["open"], errors="coerce")
    close = pd.to_numeric(raw["close"], errors="coerce")
    volume = pd.to_numeric(raw["volume"], errors="coerce").fillna(0.0)
    colors = np.where(close.to_numpy(dtype=float) >= open_.to_numpy(dtype=float), "#26a69a", "#ef5350")
    ax.bar(x, volume.to_numpy(dtype=float), color=colors, alpha=0.55, width=0.72)
    ax.set_ylabel("Vol", color="#b8c1cc")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))


def _plot_signal_panel(ax: plt.Axes, frame: pd.DataFrame, x: np.ndarray) -> None:
    _style_axis(ax)
    signal = _numeric(frame, "final_signal")
    viscosity = _numeric(frame, "viscosity")
    ax.plot(x, signal, color="#f5d547", linewidth=1.45, label="final_signal")
    ax.plot(x, viscosity, color="#e6edf3", linewidth=1.0, linestyle="--", label="viscosity")
    ax.fill_between(x, -2.25, -0.75, color="#2ea043", alpha=0.08, linewidth=0)
    for level, color in [(-2.0, "#2ea043"), (-1.5, "#56d364"), (-1.0, "#8b949e"), (0.0, "#c9d1d9"), (1.5, "#f0883e"), (2.0, "#ff7b72")]:
        ax.axhline(level, color=color, linewidth=0.8, alpha=0.55)
    ax.set_ylabel("Riskflow", color="#b8c1cc")
    legend = ax.legend(loc="upper left", fontsize=8, facecolor="#161b22", edgecolor="#30363d")
    for text in legend.get_texts():
        text.set_color("#c9d1d9")


def _plot_context_panel(ax: plt.Axes, frame: pd.DataFrame, x: np.ndarray) -> None:
    _style_axis(ax)
    relative = _numeric(frame, "relative_component")
    compression = _numeric(frame, "compression_score")
    ax.plot(x, relative, color="#a371f7", linewidth=1.35, label="relative_component")
    ax.axhline(0.0, color="#c9d1d9", linewidth=0.8, alpha=0.45)
    ax.set_ylabel("Relative", color="#b8c1cc")
    twin = ax.twinx()
    twin.set_facecolor("#101418")
    twin.tick_params(colors="#b8c1cc", labelsize=8)
    for spine in twin.spines.values():
        spine.set_color("#30363d")
    twin.plot(x, compression, color="#3fb950", linewidth=1.0, alpha=0.9, label="compression_score")
    twin.set_ylim(0, 100)
    twin.set_ylabel("Compression", color="#b8c1cc")
    lines, labels = ax.get_legend_handles_labels()
    twin_lines, twin_labels = twin.get_legend_handles_labels()
    legend = ax.legend(lines + twin_lines, labels + twin_labels, loc="upper left", fontsize=8, facecolor="#161b22", edgecolor="#30363d")
    for text in legend.get_texts():
        text.set_color("#c9d1d9")


def render_visual_review_image(
    symbol: str,
    date: object,
    raw_frame: pd.DataFrame,
    analysis_frame: pd.DataFrame,
    output_path: Path,
    *,
    lookback_bars: int,
    forward_bars: int,
) -> None:
    position = analysis_frame.index.get_loc(date)
    if not isinstance(position, int):
        position = int(position.start)
    start = max(0, position - lookback_bars)
    end = min(len(analysis_frame), position + forward_bars + 1)
    analysis_window = analysis_frame.iloc[start:end]
    raw_window = raw_frame.reindex(analysis_frame.index).iloc[start:end]
    x = np.arange(len(analysis_window), dtype=float)
    event_x = float(position - start)

    fig, axes = plt.subplots(
        4,
        1,
        figsize=(14, 9),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 0.55, 1.25, 1.0]},
    )
    fig.patch.set_facecolor("#0d1117")
    _plot_price_panel(axes[0], raw_window, symbol, x)
    _plot_volume_panel(axes[1], raw_window, x)
    _plot_signal_panel(axes[2], analysis_window, x)
    _plot_context_panel(axes[3], analysis_window, x)

    event_timestamp = pd.Timestamp(date)
    for ax in axes:
        ax.axvline(event_x, color="#58a6ff", linewidth=1.2, alpha=0.95)
        ax.axvspan(event_x, len(analysis_window) - 1, color="#58a6ff", alpha=0.06)

    tick_count = min(8, len(analysis_window))
    tick_positions = np.linspace(0, len(analysis_window) - 1, tick_count, dtype=int)
    tick_labels = [pd.Timestamp(analysis_window.index[pos]).strftime("%Y-%m-%d") for pos in tick_positions]
    axes[-1].set_xticks(tick_positions)
    axes[-1].set_xticklabels(tick_labels, rotation=0, ha="center", color="#b8c1cc")

    fig.suptitle(f"{symbol} visual review event: {event_timestamp.date()}", fontsize=13, color="#e6edf3")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _write_gallery(records: pd.DataFrame, output_path: Path, *, report_root: Path) -> None:
    lines = [
        "# Riskflow Visual Review Gallery",
        "",
        "This gallery connects numeric forward-relative-return events to chart snapshots. It is for visual research, not formula promotion.",
        "",
    ]
    if records.empty:
        lines.extend(["No visual review events matched the current thresholds.", ""])
    for _, row in records.iterrows():
        image_path = Path(str(row["image_path"]))
        try:
            image_ref = image_path.relative_to(report_root)
        except ValueError:
            image_ref = image_path
        lines.extend(
            [
                f"## {row['symbol']} - {pd.Timestamp(row['date']).date()}",
                "",
                f"- Forward relative return 30 bars: {float(row['forward_relative_return_30']):.2%}",
                f"- Event: `{row['event_name']}`",
                f"- Pattern score: {float(row['pattern_score']):.1f}" if pd.notna(row["pattern_score"]) else "- Pattern score: n/a",
                f"- Signal / viscosity: {float(row['final_signal']):.2f} / {float(row['viscosity']):.2f}",
                f"- Relative component: {float(row['relative_component']):.2f}",
                f"- Compression score: {float(row['compression_score']):.1f}",
                f"- State: {row['state']}",
                f"- Visual tags: zone `{row['signal_zone']}`, recent viscosity reclaim `{row['recent_viscosity_reclaim']}`, -2/-1 band share `{float(row['pre_event_signal_band_share']):.2f}`",
                "",
                f"![{row['symbol']} visual review]({image_ref.as_posix()})",
                "",
            ]
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_visual_review(
    universe: UniverseConfig,
    raw_frames: dict[str, pd.DataFrame],
    analysis_frames: dict[str, pd.DataFrame],
    *,
    report_dir: str | Path = "reports",
    settings: VisualReviewSettings | None = None,
) -> tuple[pd.DataFrame, dict[str, Path]]:
    settings = settings or VisualReviewSettings()
    report_root = Path(report_dir)
    review_dir = report_root / "visual_review"
    image_dir = review_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for old_image in image_dir.glob("*.png"):
        old_image.unlink()

    records = build_visual_review_records(universe, analysis_frames, settings=settings)
    if not records.empty:
        image_paths: list[str] = []
        for sequence, (_, row) in enumerate(records.iterrows(), start=1):
            symbol = str(row["symbol"])
            date = row["date"]
            raw_frame = raw_frames.get(symbol)
            analysis_frame = analysis_frames.get(symbol)
            if raw_frame is None or analysis_frame is None:
                image_paths.append("")
                continue
            safe_date = pd.Timestamp(date).strftime("%Y%m%d_%H%M")
            output_path = image_dir / f"{sequence:02d}_{symbol}_{safe_date}.png"
            render_visual_review_image(
                symbol,
                date,
                raw_frame,
                analysis_frame,
                output_path,
                lookback_bars=settings.lookback_bars,
                forward_bars=settings.forward_bars,
            )
            image_paths.append(str(output_path))
        records["image_path"] = image_paths

    public_records = records.drop(columns=[column for column in ("_sort_value", "_position") if column in records.columns])
    events_csv = review_dir / "events.csv"
    gallery_md = review_dir / "gallery.md"
    review_dir.mkdir(parents=True, exist_ok=True)
    public_records.to_csv(events_csv, index=False)
    _write_gallery(public_records, gallery_md, report_root=review_dir)
    return public_records, {"events_csv": events_csv, "gallery_md": gallery_md, "image_dir": image_dir}
