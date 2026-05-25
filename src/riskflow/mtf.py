from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


MTF_CONTEXT_MODEL_V0 = "mtf_context_v0"
RESEARCH_MTF_PRESET = ("1w", "3d", "12h", "4h")

TIMEFRAME_ROLES = {
    "1w": "regime",
    "3d": "swing",
    "1d": "primary/tactical",
    "12h": "confirmation",
    "4h": "timing/reset",
    "1h": "source/detail",
}

MTF_LEADERBOARD_COLUMNS = [
    "mtf_context_model",
    "mtf_context_available",
    "mtf_missing_timeframes",
    "mtf_data_quality",
    "mtf_leader_context",
    "mtf_trader_context",
    "mtf_alignment_tags",
    "mtf_conflict_tags",
    "mtf_notes",
    "mtf_1w_state",
    "mtf_1w_final_signal",
    "mtf_1w_relative_component",
    "mtf_1w_above_viscosity",
    "mtf_3d_state",
    "mtf_3d_final_signal",
    "mtf_3d_relative_component",
    "mtf_3d_above_viscosity",
    "mtf_12h_state",
    "mtf_12h_final_signal",
    "mtf_4h_state",
    "mtf_4h_final_signal",
    "mtf_4h_compression_score",
]

CONTEXT_VALUE_COLUMNS = [
    "state",
    "final_signal",
    "relative_component",
    "above_viscosity",
    "compression_score",
    "setup_readiness_score",
    "extension_risk_score",
    "signal_slope",
]


@dataclass(frozen=True)
class TimeframeSpec:
    timeframe: str
    role: str
    duration: pd.Timedelta


def normalize_timeframe(timeframe: str) -> str:
    return timeframe.strip().lower()


def timeframe_duration(timeframe: str) -> pd.Timedelta:
    normalized = normalize_timeframe(timeframe)
    if normalized.endswith("w"):
        return pd.Timedelta(weeks=int(normalized[:-1] or "1"))
    if normalized.endswith("d"):
        return pd.Timedelta(days=int(normalized[:-1] or "1"))
    if normalized.endswith("h"):
        return pd.Timedelta(hours=int(normalized[:-1] or "1"))
    raise ValueError(f"Unsupported timeframe '{timeframe}'")


def timeframe_spec(timeframe: str) -> TimeframeSpec:
    normalized = normalize_timeframe(timeframe)
    return TimeframeSpec(
        timeframe=normalized,
        role=TIMEFRAME_ROLES.get(normalized, "context"),
        duration=timeframe_duration(normalized),
    )


def with_available_at(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    output = frame.copy()
    output["available_at"] = pd.to_datetime(output.index) + timeframe_duration(timeframe)
    return output


def _prefixed_context_frame(frame: pd.DataFrame, context_timeframe: str) -> pd.DataFrame:
    prefix = f"mtf_{normalize_timeframe(context_timeframe)}_"
    selected = frame[[column for column in CONTEXT_VALUE_COLUMNS if column in frame.columns]].copy()
    selected["context_bar_start"] = frame.index
    selected["context_available_at"] = frame["available_at"]
    return selected.rename(columns={column: f"{prefix}{column}" for column in selected.columns})


def asof_join_completed_context(
    primary: pd.DataFrame,
    context: pd.DataFrame,
    *,
    primary_timeframe: str,
    context_timeframe: str,
) -> pd.DataFrame:
    if primary.empty:
        return primary.copy()
    if context.empty:
        return primary.copy()

    primary_working = with_available_at(primary, primary_timeframe).reset_index(names="primary_bar_start")
    context_working = with_available_at(context, context_timeframe)
    context_prefixed = _prefixed_context_frame(context_working, context_timeframe).reset_index(drop=True)

    merged = pd.merge_asof(
        primary_working.sort_values("available_at"),
        context_prefixed.sort_values(f"mtf_{normalize_timeframe(context_timeframe)}_context_available_at"),
        left_on="available_at",
        right_on=f"mtf_{normalize_timeframe(context_timeframe)}_context_available_at",
        direction="backward",
        allow_exact_matches=True,
    )
    merged = merged.sort_values("primary_bar_start").set_index("primary_bar_start")
    merged.index.name = primary.index.name
    return merged.drop(columns=["available_at"])


def _is_supportive(row: pd.Series, prefix: str) -> bool:
    state = str(row.get(f"{prefix}state", ""))
    final_signal = _float(row.get(f"{prefix}final_signal"))
    relative = _float(row.get(f"{prefix}relative_component"))
    above_viscosity = bool(row.get(f"{prefix}above_viscosity")) if pd.notna(row.get(f"{prefix}above_viscosity")) else False
    if state in {"Relative Accumulation", "Emerging Leader", "Confirmed Leader"}:
        return True
    return final_signal > 0.0 and relative > 0.0 and above_viscosity


def _is_weak(row: pd.Series, prefix: str) -> bool:
    state = str(row.get(f"{prefix}state", ""))
    final_signal = _float(row.get(f"{prefix}final_signal"))
    relative = _float(row.get(f"{prefix}relative_component"))
    if state in {"Weak", "Breakdown", "Dead Money"}:
        return True
    return final_signal < 0.0 and relative < 0.0


def _is_improving(row: pd.Series, prefix: str) -> bool:
    slope = _float(row.get(f"{prefix}signal_slope"))
    relative = _float(row.get(f"{prefix}relative_component"))
    final_signal = _float(row.get(f"{prefix}final_signal"))
    return slope > 0.0 and (relative > -0.25 or final_signal > -0.5)


def _float(value: object) -> float:
    try:
        if pd.isna(value):
            return np.nan
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _format_tags(tags: list[str]) -> str:
    return "|".join(dict.fromkeys(tag for tag in tags if tag))


def _context_prefix(timeframe: str) -> str:
    return f"mtf_{normalize_timeframe(timeframe)}_"


def _is_context_missing_or_stale(
    row: pd.Series,
    context_timeframe: str,
    primary_timeframe: str,
) -> tuple[bool, bool]:
    prefix = _context_prefix(context_timeframe)
    available = row.get(f"{prefix}context_available_at")
    if pd.isna(available):
        return True, False
    age = pd.Timestamp(row["primary_available_at"]) - pd.Timestamp(available)
    stale_after = timeframe_duration(context_timeframe) + timeframe_duration(primary_timeframe)
    return False, bool(age > stale_after)


def classify_mtf_context_row(
    row: pd.Series,
    *,
    primary_timeframe: str = "1d",
    context_timeframes: tuple[str, ...] = RESEARCH_MTF_PRESET,
) -> dict[str, object]:
    missing: list[str] = []
    stale: list[str] = []
    for timeframe in context_timeframes:
        is_missing, is_stale = _is_context_missing_or_stale(row, timeframe, primary_timeframe)
        if is_missing:
            missing.append(timeframe)
        elif is_stale:
            stale.append(timeframe)

    required = [timeframe for timeframe in ("1w", "3d") if timeframe in context_timeframes]
    required_missing = [timeframe for timeframe in required if timeframe in missing or timeframe in stale]
    incomplete = bool(required_missing) or not required

    htf_prefixes = [_context_prefix(timeframe) for timeframe in required if timeframe not in missing and timeframe not in stale]
    htf_supportive = any(_is_supportive(row, prefix) for prefix in htf_prefixes)
    htf_weak = any(_is_weak(row, prefix) for prefix in htf_prefixes)
    htf_improving = any(_is_improving(row, prefix) or _is_supportive(row, prefix) for prefix in htf_prefixes)

    state = str(row.get("state", ""))
    final_signal = _float(row.get("final_signal"))
    relative = _float(row.get("relative_component"))
    above_viscosity = bool(row.get("above_viscosity")) if pd.notna(row.get("above_viscosity")) else False
    setup_readiness = _float(row.get("setup_readiness_score"))
    extension_risk = _float(row.get("extension_risk_score"))

    primary_accumulating = state in {"Relative Accumulation", "Emerging Leader", "Confirmed Leader"}
    primary_confirmed = state in {"Emerging Leader", "Confirmed Leader"} or (
        final_signal > 0.0 and relative > 0.0 and above_viscosity
    )
    primary_tactical = primary_accumulating or (relative > 0.0 and above_viscosity)
    lower_reset = _lower_timeframe_reset(row, context_timeframes)
    lower_extended = _lower_timeframe_extended(row, context_timeframes)

    alignment_tags: list[str] = []
    conflict_tags: list[str] = []
    if htf_supportive:
        alignment_tags.append("htf_supportive")
    if htf_improving:
        alignment_tags.append("htf_improving")
    if lower_reset:
        alignment_tags.append("ltf_reset_or_compression")
    if htf_weak:
        conflict_tags.append("htf_weak")
    if lower_extended:
        conflict_tags.append("ltf_extended")
    if extension_risk >= 70.0:
        conflict_tags.append("primary_extension_risk")
    if stale:
        conflict_tags.append("stale_context")

    if incomplete:
        leader_context = "Incomplete Data"
    elif primary_tactical and htf_weak:
        leader_context = "Conflicted Leader"
    elif primary_tactical and htf_supportive:
        leader_context = "Aligned Leader"
    elif primary_tactical:
        leader_context = "Tactical Leader"
    elif htf_improving and not primary_confirmed:
        leader_context = "Early HTF Turn"
    else:
        leader_context = "Unconfirmed"

    if incomplete:
        trader_context = "No Trade Context"
    elif extension_risk >= 70.0 or lower_extended:
        trader_context = "Chase Risk"
    elif primary_tactical and htf_weak:
        trader_context = "HTF Conflict"
    elif htf_supportive and lower_reset and setup_readiness < 70.0:
        trader_context = "Reset Forming"
    elif htf_supportive and setup_readiness >= 70.0 and extension_risk < 70.0:
        trader_context = "Setup Ready"
    elif htf_improving:
        trader_context = "Wait For Confirmation"
    else:
        trader_context = "No Trade Context"

    if incomplete:
        data_quality = "missing" if missing else "stale"
    elif stale:
        data_quality = "stale"
    elif missing:
        data_quality = "partial"
    else:
        data_quality = "complete"

    notes = []
    if missing:
        notes.append(f"missing: {','.join(missing)}")
    if stale:
        notes.append(f"stale: {','.join(stale)}")
    if htf_supportive:
        notes.append("higher timeframe supportive")
    if htf_weak:
        notes.append("higher timeframe conflict")
    if lower_reset:
        notes.append("lower timeframe reset/compression visible")

    return {
        "mtf_context_model": MTF_CONTEXT_MODEL_V0,
        "mtf_context_available": not incomplete,
        "mtf_missing_timeframes": ",".join([*missing, *(f"{timeframe}:stale" for timeframe in stale)]),
        "mtf_data_quality": data_quality,
        "mtf_leader_context": leader_context,
        "mtf_trader_context": trader_context,
        "mtf_alignment_tags": _format_tags(alignment_tags),
        "mtf_conflict_tags": _format_tags(conflict_tags),
        "mtf_notes": "; ".join(notes),
    }


def _lower_timeframe_reset(row: pd.Series, context_timeframes: tuple[str, ...]) -> bool:
    for timeframe in ("4h", "12h"):
        if timeframe not in context_timeframes:
            continue
        prefix = _context_prefix(timeframe)
        state = str(row.get(f"{prefix}state", ""))
        compression = _float(row.get(f"{prefix}compression_score"))
        if state in {"Compression", "Relative Accumulation"} or compression >= 70.0:
            return True
    return False


def _lower_timeframe_extended(row: pd.Series, context_timeframes: tuple[str, ...]) -> bool:
    for timeframe in ("4h", "12h"):
        if timeframe not in context_timeframes:
            continue
        prefix = _context_prefix(timeframe)
        final_signal = _float(row.get(f"{prefix}final_signal"))
        compression = _float(row.get(f"{prefix}compression_score"))
        if final_signal > 2.0 and compression < 35.0:
            return True
    return False


def append_mtf_context(
    primary_frames: dict[str, pd.DataFrame],
    context_frames_by_timeframe: dict[str, dict[str, pd.DataFrame]],
    *,
    primary_timeframe: str = "1d",
    context_timeframes: list[str] | tuple[str, ...] = RESEARCH_MTF_PRESET,
) -> dict[str, pd.DataFrame]:
    normalized_timeframes = tuple(normalize_timeframe(timeframe) for timeframe in context_timeframes)
    output: dict[str, pd.DataFrame] = {}
    for symbol, primary in primary_frames.items():
        enriched = primary.copy()
        enriched["primary_available_at"] = pd.to_datetime(enriched.index) + timeframe_duration(primary_timeframe)
        for context_timeframe in normalized_timeframes:
            context = context_frames_by_timeframe.get(context_timeframe, {}).get(symbol)
            if context is None or context.empty:
                continue
            enriched = asof_join_completed_context(
                enriched,
                context,
                primary_timeframe=primary_timeframe,
                context_timeframe=context_timeframe,
            )
            if "primary_available_at" not in enriched.columns:
                enriched["primary_available_at"] = pd.to_datetime(enriched.index) + timeframe_duration(primary_timeframe)

        context_rows = [
            classify_mtf_context_row(
                row,
                primary_timeframe=primary_timeframe,
                context_timeframes=normalized_timeframes,
            )
            for _date, row in enriched.iterrows()
        ]
        context_frame = pd.DataFrame(context_rows, index=enriched.index)
        output[symbol] = enriched.join(context_frame, how="left")

    return output
