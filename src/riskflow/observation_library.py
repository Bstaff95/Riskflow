from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


OBSERVATION_LIBRARY_MODEL = "riskflow_observation_library_v0"

TAG_GRAMMAR: dict[str, list[str]] = {
    "location": [
        "deep_negative",
        "lower_gate",
        "under_zero",
        "zero_zone",
        "above_zero",
        "upper_gate",
        "overheated",
    ],
    "structure": [
        "coil",
        "chop",
        "compression",
        "descending_wedge",
        "ascending_wedge",
        "symmetrical_triangle",
        "ascending_triangle",
        "descending_triangle",
        "oscillator_trendline_break",
        "oscillator_downtrend_resistance",
        "long_term_signal_downtrend_break",
        "steep_oscillator_downtrend",
        "wedge_breakout",
        "descending_channel",
        "channel_breakout",
        "tight_chop_above_lower_band",
        "basing_under_minus_one_point_five",
        "failed_first_trendline_break",
        "second_trendline_break",
        "impulse",
        "pullback",
        "pennant",
        "divergence",
        "bullish_divergence",
        "bearish_divergence",
        "bearish_divergence_after_pump",
        "hidden_bearish_divergence",
        "bullish_divergence_after_double_bottom",
        "higher_low",
        "rising_oscillator_lows",
        "lower_high",
        "price_double_bottom",
        "capitulatory_low",
        "failed_breakdown",
        "failed_breakout",
        "vertical_consolidation",
        "coil_under_viscosity",
        "tight_coil_below_viscosity",
        "double_bottom_required",
        "second_base_required",
        "failed_impulse_spike",
        "spike_retrace_reset_needed",
        "chaotic_oscillator_pa",
        "weak_viscosity_chop",
        "chop_around_viscosity",
        "unstructured_volatility",
        "weak_wedge",
        "wedge_without_confirmation",
        "rising_oscillator_highs",
        "unstable_strength",
        "signal_lower_high",
        "color_divergence",
        "weaker_second_color_push",
        "fading_gradient_quality",
        "gradient_momentum_divergence",
        "weakness_exhaustion",
        "price_lower_lows",
        "failed_reversal_watchlist",
    ],
    "trigger": [
        "viscosity_reclaim",
        "zero_reclaim",
        "level_reclaim",
        "minus_two_reclaim",
        "minus_one_point_five_reclaim",
        "support_retest",
        "resistance_reclaim",
        "trendline_break",
        "explosive_trendline_break",
        "relative_improvement",
        "color_shift_green_to_yellow",
        "weak_color_shift",
        "weak_colors",
        "fast_viscosity_reclaim",
        "reclaim_after_flush",
        "failed_breakout_reset_reclaim",
        "impulse_sold_off",
        "failed_strength_acceptance",
    ],
    "confirmation": [
        "viscosity_retest_hold",
        "zero_retest_hold",
        "flat_viscosity_before_break",
        "viscosity_breakout",
        "zero_line_support",
        "viscosity_support",
        "time_above_viscosity",
        "sustained_above_viscosity",
        "daily_uptrend_viscosity_acceptance",
        "viscosity_acceptance",
        "lower_band_support",
        "upper_band_support",
        "lower_band_retest_hold",
        "minus_two_retest_hold",
        "minus_one_point_five_retest_hold",
        "higher_low_hold",
        "acceleration",
        "low_in_before_price_confirmation",
        "relative_weakness_fails_to_accelerate",
    ],
    "failure": [
        "lost_viscosity",
        "zero_rejection",
        "failed_retest",
        "failed_viscosity_breakdown",
        "zero_reclaim_failure",
        "equilibrium_rejection",
        "zero_rejection",
        "upper_band_rejection",
        "lower_band_failure",
        "support_failure",
        "resistance_failure",
        "underside_support_rejection",
        "weak_breakout_response",
        "no_meaningful_bounce",
        "zero_line_not_reached",
        "zero_confirmation_missing",
        "failed_zero_reclaim",
        "no_compression",
        "failed_higher_highs",
        "not_ready",
        "price_needs_chop",
        "low_zone_viscosity_rejection",
        "failed_first_breakout",
        "weak_relative_followthrough",
        "overextended_rollover",
    ],
    "context": [
        "meme_basket_relative",
        "ex_target_benchmark",
        "tradingview_reference_needed",
        "human_review_needed",
        "multi_level_reclaim_confluence",
    ],
}

PATTERN_PRINCIPLES: dict[str, str] = {
    "coil_viscosity_reclaim_v0": (
        "A lower-zone oscillator coil can become actionable when signal reclaims the adaptive "
        "viscosity baseline before the move is already overheated."
    ),
    "compression_impulse_viscosity_retest_v0": (
        "A prior coil followed by impulse and a held viscosity retest can mark trend transition, "
        "but may fire late if the impulse is already mature."
    ),
    "strong_forward_relative_breakout": (
        "Hindsight breakout examples are useful for archeology, but cannot prove a predictive "
        "signal without a pre-event pattern definition."
    ),
}

CONCEPT_DESCRIPTIONS: dict[str, str] = {
    "Viscosity Reclaim": "Signal crosses back above the adaptive viscosity baseline.",
    "Viscosity Reclaim Without Retest": "Signal crosses above viscosity and continues without a clean pullback to the baseline.",
    "Viscosity Retest Hold": "Signal pulls back toward viscosity after reclaiming it and does not fail below it.",
    "Viscosity Support": "Signal uses the adaptive viscosity baseline as support.",
    "Zero Line Reclaim": "Signal crosses above oscillator equilibrium.",
    "Zero Line Support": "Signal holds the zero line as support after reclaiming or during continuation.",
    "Zero Line Retest Hold": "Signal returns to the zero line after reclaiming it and holds.",
    "Under Zero Coil": "Signal compresses or chops below zero before a possible expansion attempt.",
    "Descending Wedge": "Signal forms a tightening downward-sloping structure before breaking upward.",
    "Ascending Wedge": "Signal forms a tightening upward-sloping structure, often requiring exhaustion/failure review.",
    "Symmetrical Triangle": "Signal forms converging highs and lows before resolving.",
    "Ascending Triangle": "Signal presses into a horizontal resistance while making higher lows.",
    "Descending Triangle": "Signal presses into horizontal support while making lower highs.",
    "Oscillator Trendline Break": "A trendline drawn on the oscillator breaks before price fully confirms.",
    "Oscillator Downtrend Resistance": "A larger downtrend line on the oscillator acts as resistance before a breakout attempt.",
    "Long Term Signal Downtrend Break": "A major longer-term oscillator downtrend breaks, often marking a larger reversal attempt.",
    "Steep Oscillator Downtrend": "Signal is controlled by an unusually steep downtrend, raising the bar for a valid reversal.",
    "Wedge Breakout": "Signal breaks out of a tightening wedge structure.",
    "Descending Channel": "Signal moves inside a downward-sloping channel before a break attempt.",
    "Channel Breakout": "Signal breaks out of a channel structure.",
    "Tight Chop Above Lower Band": "Signal chops tightly above the lower reference band after an initial break.",
    "Basing Under Minus One Point Five": "Signal builds a base below the -1.5 lower gate before attempting reversal.",
    "Failed First Trendline Break": "An initial oscillator trendline break fails to produce durable follow-through.",
    "Second Trendline Break": "A later oscillator trendline break occurs after an earlier failed break and reset.",
    "Bullish Divergence": "Price makes a lower low while the oscillator makes a higher low.",
    "Bearish Divergence": "Price makes a higher high while the oscillator makes a lower high.",
    "Bearish Divergence After Pump": "Price pushes higher after a strong move while the oscillator makes a lower high.",
    "Hidden Bearish Divergence": "Oscillator makes higher highs while price makes lower highs, warning that relative pressure is not translating into price strength.",
    "Bullish Divergence After Double Bottom": "Price double bottoms while the oscillator makes higher lows before another leg up.",
    "Higher Low": "The oscillator forms a higher low, suggesting improving internal pressure.",
    "Rising Oscillator Lows": "Oscillator lows curl upward over time, suggesting pressure improvement before a clean impulse.",
    "Lower High": "The oscillator forms a lower high, suggesting fading internal pressure.",
    "Failed Breakdown": "The oscillator breaks or probes lower but quickly reclaims the prior support zone.",
    "Failed Breakout": "The oscillator breaks higher but quickly loses the breakout zone.",
    "Vertical Consolidation": "Signal spends time consolidating around a zone or baseline without needing to impulse higher.",
    "Coil Under Viscosity": "Signal coils below viscosity instead of accelerating lower.",
    "Tight Coil Below Viscosity": "Signal rejects under viscosity but compresses tightly without making much lower lows.",
    "Double Bottom Required": "A first constructive structure fails and the oscillator needs a second bottom before expansion.",
    "Second Base Required": "A setup needs another basing structure before it becomes actionable.",
    "Failed Impulse Spike": "Signal spikes sharply but immediately retraces, showing unstable or unconfirmed momentum.",
    "Spike Retrace Reset Needed": "A prior spike and immediate retrace suggest the next setup may need extra reset or confirmation.",
    "Chaotic Oscillator Pa": "Oscillator price action is too volatile and disorderly to show clean accumulation.",
    "Weak Viscosity Chop": "Signal chops around viscosity without clean acceptance, impulse, or support behavior.",
    "Chop Around Viscosity": "Signal repeatedly crosses above and below viscosity without clear directional control.",
    "Unstructured Volatility": "Signal is volatile but does not form a readable compression or accumulation structure.",
    "Weak Wedge": "A wedge exists visually, but supporting momentum/color/level behavior is weak.",
    "Wedge Without Confirmation": "A wedge breaks or forms, but other confirmation features are missing.",
    "Rising Oscillator Highs": "Oscillator highs rise over time, suggesting pressure attempts but not necessarily clean structure.",
    "Unstable Strength": "Strength appears but cannot sustain cleanly above levels or baseline support.",
    "Signal Lower High": "Signal makes a lower high on a later push, warning that pressure is fading.",
    "Color Divergence": "Price or signal attempts another push while oscillator color/gradient quality weakens.",
    "Weaker Second Color Push": "A later push shows weaker colors than an earlier push, suggesting fading pressure.",
    "Fading Gradient Quality": "Color/gradient behavior weakens over time even if price or signal still attempts to rise.",
    "Gradient Momentum Divergence": "The oscillator's color or gradient weakens while the chart attempts another push.",
    "Weakness Exhaustion": "Relative weakness stops accelerating even while the signal remains in a deeply negative zone.",
    "Price Lower Lows": "Price continues to make lower lows while the oscillator attempts to improve.",
    "Failed Reversal Watchlist": "A reversal clue appears, but later confirmation never arrives.",
    "Price Double Bottom": "Price retests a prior low area while oscillator structure may improve.",
    "Capitulatory Low": "Price makes a sharp exhaustion low before a reflex or reversal attempt.",
    "Support Retest": "Signal retests a prior support level and holds.",
    "Resistance Reclaim": "Signal reclaims a prior resistance level.",
    "Explosive Trendline Break": "Signal breaks a trendline with an unusually strong impulse.",
    "Minus Two Reclaim": "Signal reclaims the -2 lower extreme after trading below it.",
    "Minus One Point Five Reclaim": "Signal reclaims the -1.5 lower gate.",
    "Flat Viscosity Before Break": "Viscosity is flat or compressed before the signal breaks away from it.",
    "Viscosity Breakout": "Signal breaks decisively above a flat or resistant viscosity baseline.",
    "Time Above Viscosity": "Signal spends a sustained share of bars above viscosity.",
    "Sustained Above Viscosity": "Signal remains above viscosity for an extended period with few failed dips.",
    "Daily Uptrend Viscosity Acceptance": "A daily uptrend often shows the signal staying above viscosity most of the time.",
    "Viscosity Acceptance": "Signal accepts viscosity as support over time, even if momentum is not yet impulsing.",
    "Failed Viscosity Breakdown": "Signal loses viscosity briefly but the breakdown does not hold.",
    "Fast Viscosity Reclaim": "Signal quickly reclaims viscosity after losing it.",
    "Reclaim After Flush": "Signal flushes below support or viscosity, then rapidly recovers.",
    "Impulse Sold Off": "Signal impulses higher but is immediately sold back down.",
    "Failed Strength Acceptance": "Signal cannot sustain strength after reclaiming or impulsing above a level.",
    "Zero Reclaim Failure": "Signal fails to reclaim or hold the zero/equilibrium line.",
    "Equilibrium Rejection": "Signal rejects near the zero line instead of entering a positive regime.",
    "Zero Rejection": "Signal tests the zero/equilibrium line and rejects.",
    "Failed Breakout Reset Reclaim": "A failed first breakout resets lower, then reclaims structure after the reset.",
    "Color Shift Green To Yellow": "The oscillator color shifts from weak/green toward yellow quickly, suggesting momentum improvement.",
    "Weak Color Shift": "The oscillator color fails to improve much after a supposed setup trigger.",
    "Weak Colors": "The oscillator remains in weaker colors during a supposed setup, showing poor pressure quality.",
    "Multi Level Reclaim Confluence": "Several oscillator levels or structures are reclaimed in the same window.",
    "Lower Band Accumulation": "Signal spends time near the lower gates, often around -2 to -1.",
    "Lower Band Support": "Signal holds the lower reference band as support.",
    "Upper Band Support": "Signal holds the upper reference band during a strong continuation.",
    "Upper Band Rejection": "Signal rejects near the upper reference band, often warning of extension or rollover.",
    "Underside Support Rejection": "Signal breaks support, then repeatedly rejects from the underside of that former support.",
    "Weak Breakout Response": "A structure break produces little or no meaningful signal/price response.",
    "No Meaningful Bounce": "A would-be break or reclaim fails to generate a meaningful bounce.",
    "Zero Line Not Reached": "Signal fails to reach the zero/equilibrium line after a setup attempt.",
    "Zero Confirmation Missing": "A reversal or breakout attempt never confirms by reclaiming/holding the zero line.",
    "Failed Zero Reclaim": "Signal attempts to reclaim the zero line but cannot break or hold it.",
    "No Compression": "A setup lacks a calm/tight base before attempting to resolve.",
    "Failed Higher Highs": "Signal fails to make higher highs during a supposed constructive structure.",
    "Not Ready": "The structure may be interesting, but the oscillator lacks enough confirmation for a ready setup.",
    "Price Needs Chop": "The oscillator may have marked a low or reversal attempt, but price still needs consolidation before expansion.",
    "Low Zone Viscosity Rejection": "Signal rejects under viscosity while already deeply negative, useful only if weakness then fails to accelerate.",
    "Low In Before Price Confirmation": "The oscillator suggests the low may be in before price becomes ready to trend.",
    "Relative Weakness Fails To Accelerate": "The signal stops making meaningful lower lows while still below key lower levels.",
    "Failed First Breakout": "An initial breakout attempt fails and should not be treated as equivalent to later confirmed breaks.",
    "Minus Two Retest Hold": "Signal retests the -2 lower extreme and holds instead of continuing lower.",
    "Minus One Point Five Retest Hold": "Signal retests the -1.5 lower gate and holds.",
    "False Positive": "A setup-like observation that did not produce useful forward follow-through.",
}


@dataclass(frozen=True)
class ObservationLibraryPaths:
    records_jsonl: Path
    records_csv: Path
    schema_yaml: Path
    index_md: Path
    cases_dir: Path
    patterns_dir: Path
    concepts_dir: Path


def _slug(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def _float_or_none(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _string_or_empty(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _signal_location(final_signal: object) -> str:
    value = _float_or_none(final_signal)
    if value is None:
        return "unknown"
    if value <= -2.0:
        return "deep_negative"
    if value <= -1.0:
        return "lower_gate"
    if value < -0.15:
        return "under_zero"
    if value <= 0.35:
        return "zero_zone"
    if value < 1.5:
        return "above_zero"
    if value < 2.0:
        return "upper_gate"
    return "overheated"


def _outcome_label(row: pd.Series) -> str:
    rel_3 = _float_or_none(row.get("forward_relative_return_3"))
    rel_14 = _float_or_none(row.get("forward_relative_return_14"))
    rel_30 = _float_or_none(row.get("forward_relative_return_30"))
    best = max([value for value in [rel_3, rel_14, rel_30] if value is not None], default=None)
    if best is None:
        return "unknown_outcome"
    if best >= 0.20 and (rel_3 is not None and rel_3 >= 0.10):
        return "fast_clean_hit"
    if rel_14 is not None and rel_14 >= 0.08:
        return "delayed_hit"
    if rel_30 is not None and rel_30 >= 0.08:
        return "slow_hit"
    if rel_30 is not None and rel_30 <= -0.05:
        return "false_positive"
    return "mixed_or_flat"


def _tags_for_row(row: pd.Series) -> list[str]:
    tags = {_signal_location(row.get("final_signal")), "human_review_needed"}
    event_name = str(row.get("event_name", ""))
    signal_zone = row.get("signal_zone")
    if pd.notna(signal_zone):
        tags.add(str(signal_zone))
    if "coil" in event_name:
        tags.update({"coil", "compression", "viscosity_reclaim"})
    if "impulse" in event_name:
        tags.update({"impulse", "viscosity_retest_hold"})
    if bool(row.get("recent_viscosity_reclaim", False)):
        tags.add("viscosity_reclaim")
    if _float_or_none(row.get("relative_component")) is not None:
        tags.add("relative_component_observed")
    if _float_or_none(row.get("compression_score")) is not None:
        tags.add("compression_observed")
    if "EX_" in str(row.get("benchmark", "")):
        tags.add("ex_target_benchmark")
    tags.add(_outcome_label(row))
    return sorted(tag for tag in tags if tag and tag != "unknown")


def build_observation_records(events: pd.DataFrame, *, source_path: str | Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    source = str(source_path)
    generated = datetime.now().isoformat(timespec="seconds")

    for _, row in events.iterrows():
        symbol = str(row.get("symbol", "UNKNOWN")).upper()
        timeframe = str(row.get("timeframe", "unknown"))
        date = pd.Timestamp(row.get("date"))
        event_name = str(row.get("event_name", "unknown_event"))
        observation_id = f"{symbol}_{timeframe}_{date.strftime('%Y%m%d_%H%M')}_{_slug(event_name)}"
        tags = _tags_for_row(row)
        pattern_label = event_name
        principle = PATTERN_PRINCIPLES.get(pattern_label, "Unreviewed pattern principle.")

        rows.append(
            {
                "observation_id": observation_id,
                "observation_model": OBSERVATION_LIBRARY_MODEL,
                "created_at": generated,
                "source_path": source,
                "symbol": symbol,
                "name": _string_or_empty(row.get("name", symbol)) or symbol,
                "timeframe": timeframe,
                "date": date.isoformat(),
                "benchmark": _string_or_empty(row.get("benchmark", "")),
                "pattern_label": pattern_label,
                "principle": principle,
                "human_label": "unreviewed",
                "review_status": "needs_human_review",
                "tags": ",".join(tags),
                "location_tag": _signal_location(row.get("final_signal")),
                "outcome_label": _outcome_label(row),
                "final_signal": _float_or_none(row.get("final_signal")),
                "viscosity": _float_or_none(row.get("viscosity")),
                "relative_component": _float_or_none(row.get("relative_component")),
                "price_component": _float_or_none(row.get("price_component")),
                "compression_score": _float_or_none(row.get("compression_score")),
                "forward_relative_return_3": _float_or_none(row.get("forward_relative_return_3")),
                "forward_relative_return_7": _float_or_none(row.get("forward_relative_return_7")),
                "forward_relative_return_14": _float_or_none(row.get("forward_relative_return_14")),
                "forward_relative_return_30": _float_or_none(row.get("forward_relative_return_30")),
                "state": _string_or_empty(row.get("state", "")),
                "setup_tags": _string_or_empty(row.get("setup_tags", "")),
                "image_path": _string_or_empty(row.get("image_path", "")),
                "notes": _string_or_empty(row.get("notes", "")),
            }
        )

    return pd.DataFrame(rows)


def _write_jsonl(records: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records.to_dict(orient="records"):
            clean_record = {key: (None if pd.isna(value) else value) for key, value in record.items()}
            file.write(json.dumps(clean_record, ensure_ascii=True, allow_nan=False) + "\n")


def _write_schema(path: Path) -> None:
    schema = {
        "model": OBSERVATION_LIBRARY_MODEL,
        "purpose": "Structured observation records for Riskflow visual indicator learning.",
        "truth_policy": {
            "python_records": "machine-readable evidence source",
            "obsidian_wiki": "human synthesis and connected memory",
            "tradingview_screenshots": "visual frontend reference",
            "human_label": "required before promotion",
        },
        "required_columns": [
            "observation_id",
            "symbol",
            "timeframe",
            "date",
            "pattern_label",
            "human_label",
            "review_status",
            "tags",
            "forward_relative_return_14",
            "forward_relative_return_30",
        ],
        "tag_grammar": TAG_GRAMMAR,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")


def _wiki_link(label: object) -> str:
    return f"[[{label}]]"


def _pattern_title(pattern_label: str) -> str:
    return pattern_label.replace("_", " ").title().replace(" V0", " v0")


def _concept_links_for_tags(tags: Iterable[str]) -> list[str]:
    mapping = {
        "viscosity_reclaim": "Viscosity Reclaim",
        "viscosity_retest_hold": "Viscosity Retest Hold",
        "minus_two_retest_hold": "Minus Two Retest Hold",
        "minus_one_point_five_retest_hold": "Minus One Point Five Retest Hold",
        "descending_wedge": "Descending Wedge",
        "ascending_wedge": "Ascending Wedge",
        "symmetrical_triangle": "Symmetrical Triangle",
        "ascending_triangle": "Ascending Triangle",
        "descending_triangle": "Descending Triangle",
        "oscillator_trendline_break": "Oscillator Trendline Break",
        "oscillator_downtrend_resistance": "Oscillator Downtrend Resistance",
        "long_term_signal_downtrend_break": "Long Term Signal Downtrend Break",
        "steep_oscillator_downtrend": "Steep Oscillator Downtrend",
        "wedge_breakout": "Wedge Breakout",
        "descending_channel": "Descending Channel",
        "channel_breakout": "Channel Breakout",
        "tight_chop_above_lower_band": "Tight Chop Above Lower Band",
        "basing_under_minus_one_point_five": "Basing Under Minus One Point Five",
        "failed_first_trendline_break": "Failed First Trendline Break",
        "second_trendline_break": "Second Trendline Break",
        "bullish_divergence": "Bullish Divergence",
        "bearish_divergence": "Bearish Divergence",
        "bearish_divergence_after_pump": "Bearish Divergence After Pump",
        "hidden_bearish_divergence": "Hidden Bearish Divergence",
        "bullish_divergence_after_double_bottom": "Bullish Divergence After Double Bottom",
        "higher_low": "Higher Low",
        "rising_oscillator_lows": "Rising Oscillator Lows",
        "lower_high": "Lower High",
        "failed_breakdown": "Failed Breakdown",
        "failed_breakout": "Failed Breakout",
        "vertical_consolidation": "Vertical Consolidation",
        "coil_under_viscosity": "Coil Under Viscosity",
        "tight_coil_below_viscosity": "Tight Coil Below Viscosity",
        "double_bottom_required": "Double Bottom Required",
        "second_base_required": "Second Base Required",
        "failed_impulse_spike": "Failed Impulse Spike",
        "spike_retrace_reset_needed": "Spike Retrace Reset Needed",
        "chaotic_oscillator_pa": "Chaotic Oscillator Pa",
        "weak_viscosity_chop": "Weak Viscosity Chop",
        "chop_around_viscosity": "Chop Around Viscosity",
        "unstructured_volatility": "Unstructured Volatility",
        "weak_wedge": "Weak Wedge",
        "wedge_without_confirmation": "Wedge Without Confirmation",
        "rising_oscillator_highs": "Rising Oscillator Highs",
        "unstable_strength": "Unstable Strength",
        "signal_lower_high": "Signal Lower High",
        "color_divergence": "Color Divergence",
        "weaker_second_color_push": "Weaker Second Color Push",
        "fading_gradient_quality": "Fading Gradient Quality",
        "gradient_momentum_divergence": "Gradient Momentum Divergence",
        "weakness_exhaustion": "Weakness Exhaustion",
        "price_lower_lows": "Price Lower Lows",
        "failed_reversal_watchlist": "Failed Reversal Watchlist",
        "price_double_bottom": "Price Double Bottom",
        "capitulatory_low": "Capitulatory Low",
        "support_retest": "Support Retest",
        "resistance_reclaim": "Resistance Reclaim",
        "explosive_trendline_break": "Explosive Trendline Break",
        "minus_two_reclaim": "Minus Two Reclaim",
        "minus_one_point_five_reclaim": "Minus One Point Five Reclaim",
        "flat_viscosity_before_break": "Flat Viscosity Before Break",
        "viscosity_breakout": "Viscosity Breakout",
        "time_above_viscosity": "Time Above Viscosity",
        "sustained_above_viscosity": "Sustained Above Viscosity",
        "daily_uptrend_viscosity_acceptance": "Daily Uptrend Viscosity Acceptance",
        "viscosity_acceptance": "Viscosity Acceptance",
        "failed_viscosity_breakdown": "Failed Viscosity Breakdown",
        "fast_viscosity_reclaim": "Fast Viscosity Reclaim",
        "reclaim_after_flush": "Reclaim After Flush",
        "impulse_sold_off": "Impulse Sold Off",
        "failed_strength_acceptance": "Failed Strength Acceptance",
        "zero_reclaim_failure": "Zero Reclaim Failure",
        "equilibrium_rejection": "Equilibrium Rejection",
        "zero_rejection": "Zero Rejection",
        "failed_breakout_reset_reclaim": "Failed Breakout Reset Reclaim",
        "color_shift_green_to_yellow": "Color Shift Green To Yellow",
        "weak_color_shift": "Weak Color Shift",
        "weak_colors": "Weak Colors",
        "multi_level_reclaim_confluence": "Multi Level Reclaim Confluence",
        "zero_line_support": "Zero Line Support",
        "viscosity_support": "Viscosity Support",
        "lower_band_support": "Lower Band Support",
        "upper_band_support": "Upper Band Support",
        "upper_band_rejection": "Upper Band Rejection",
        "underside_support_rejection": "Underside Support Rejection",
        "weak_breakout_response": "Weak Breakout Response",
        "no_meaningful_bounce": "No Meaningful Bounce",
        "zero_line_not_reached": "Zero Line Not Reached",
        "zero_confirmation_missing": "Zero Confirmation Missing",
        "failed_zero_reclaim": "Failed Zero Reclaim",
        "no_compression": "No Compression",
        "failed_higher_highs": "Failed Higher Highs",
        "not_ready": "Not Ready",
        "price_needs_chop": "Price Needs Chop",
        "low_zone_viscosity_rejection": "Low Zone Viscosity Rejection",
        "low_in_before_price_confirmation": "Low In Before Price Confirmation",
        "relative_weakness_fails_to_accelerate": "Relative Weakness Fails To Accelerate",
        "failed_first_breakout": "Failed First Breakout",
        "zero_reclaim": "Zero Line Reclaim",
        "zero_retest_hold": "Zero Line Retest Hold",
        "under_zero": "Under Zero Coil",
        "lower_gate": "Lower Band Accumulation",
        "deep_negative": "Lower Band Accumulation",
        "false_positive": "False Positive",
    }
    concepts = [mapping[tag] for tag in tags if tag in mapping]
    return sorted(set(concepts))


def _write_case_note(record: pd.Series, path: Path) -> None:
    tags = [tag for tag in str(record.get("tags", "")).split(",") if tag]
    concepts = _concept_links_for_tags(tags)
    pattern_title = _pattern_title(str(record["pattern_label"]))
    image_path = str(record.get("image_path", ""))
    image_line = f"![Chart](/Users/Shared/Riskflow/{image_path})" if image_path else "_No chart image linked._"
    content = f"""---
observation_id: {record['observation_id']}
symbol: {record['symbol']}
timeframe: {record['timeframe']}
date: {record['date']}
pattern_label: {record['pattern_label']}
review_status: {record['review_status']}
human_label: {record['human_label']}
---

# {record['symbol']} {record['timeframe']} {pd.Timestamp(record['date']).strftime('%Y-%m-%d %H:%M')}

Pattern: [[{pattern_title}]]

Concepts: {", ".join(_wiki_link(concept) for concept in concepts) if concepts else "_Needs concept review._"}

## Chart

{image_line}

## Evidence

- Benchmark: `{record.get('benchmark', '')}`
- Final signal / viscosity: `{record.get('final_signal', '')}` / `{record.get('viscosity', '')}`
- Relative component: `{record.get('relative_component', '')}`
- Compression score: `{record.get('compression_score', '')}`
- 3/7/14/30 bar forward relative return: `{record.get('forward_relative_return_3', '')}` / `{record.get('forward_relative_return_7', '')}` / `{record.get('forward_relative_return_14', '')}` / `{record.get('forward_relative_return_30', '')}`
- Outcome label: `{record.get('outcome_label', '')}`

## Tags

{", ".join(f"`{tag}`" for tag in tags)}

## Human Review

- Label: `unreviewed`
- Notes:

## Source

- Source path: `{record.get('source_path', '')}`
- Image path: `{image_path}`
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_pattern_pages(records: pd.DataFrame, patterns_dir: Path) -> None:
    patterns_dir.mkdir(parents=True, exist_ok=True)
    for pattern_label, group in records.groupby("pattern_label"):
        title = _pattern_title(str(pattern_label))
        cases = "\n".join(
            f"- [[{row['observation_id']}]] `{row['outcome_label']}` "
            f"30-bar rel `{row['forward_relative_return_30']}`"
            for _, row in group.iterrows()
        )
        principle = PATTERN_PRINCIPLES.get(str(pattern_label), "Unreviewed pattern principle.")
        content = f"""# {title}

## Principle

{principle}

## Evidence Status

This page is a synthesis layer. Promotion requires structured evidence and human-reviewed cases.

## Linked Cases

{cases}
"""
        (patterns_dir / f"{title}.md").write_text(content, encoding="utf-8")


def _write_concept_pages(concepts_dir: Path) -> None:
    concepts_dir.mkdir(parents=True, exist_ok=True)
    for title, description in CONCEPT_DESCRIPTIONS.items():
        content = f"""# {title}

{description}

## Role In The Grammar

This is a reusable observation concept. It should link to case notes and pattern pages, but it is not proof by itself.

## Review Questions

- Does this concept appear before useful forward relative returns?
- Does it require context from another level or timeframe?
- What false positives does it create?
"""
        (concepts_dir / f"{title}.md").write_text(content, encoding="utf-8")


def _write_index(records: pd.DataFrame, path: Path) -> None:
    pattern_counts = records["pattern_label"].value_counts().to_dict() if not records.empty else {}
    outcome_counts = records["outcome_label"].value_counts().to_dict() if not records.empty else {}
    patterns = "\n".join(f"- [[{_pattern_title(pattern)}]]: {count}" for pattern, count in pattern_counts.items())
    outcomes = "\n".join(f"- `{outcome}`: {count}" for outcome, count in outcome_counts.items())
    cases = "\n".join(f"- [[{row['observation_id']}]]" for _, row in records.head(25).iterrows())
    content = f"""# Indicator Observation Library

Generated: {datetime.now().isoformat(timespec='seconds')}
Model: `{OBSERVATION_LIBRARY_MODEL}`

This is the Obsidian synthesis layer for Riskflow indicator learning. Structured records remain the evidence source.

## How To Use

1. Review case notes.
2. Set `human_label` in the note after visual inspection.
3. Add plain-language notes about what the indicator appeared to do.
4. Promote nothing until Riskflow evidence supports it.

## Pattern Counts

{patterns or '_None._'}

## Outcome Counts

{outcomes or '_None._'}

## Recent Cases

{cases or '_None._'}

## Core Maps

- [[Indicator Grammar]]
- [[False Positive Atlas]]
- [[Breakout Archetypes]]
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_map_pages(maps_dir: Path) -> None:
    maps_dir.mkdir(parents=True, exist_ok=True)
    grammar = "\n".join(
        [f"## {family.title()}\n" + "\n".join(f"- `{tag}`" for tag in tags) for family, tags in TAG_GRAMMAR.items()]
    )
    (maps_dir / "Indicator Grammar.md").write_text(
        f"# Indicator Grammar\n\n{grammar}\n\n## Principle\n\nPatterns are combinations of location, structure, trigger, confirmation, failure, and context tags.\n",
        encoding="utf-8",
    )
    (maps_dir / "False Positive Atlas.md").write_text(
        "# False Positive Atlas\n\nCollect failed setup notes here. Failures are first-class research data.\n",
        encoding="utf-8",
    )
    (maps_dir / "Breakout Archetypes.md").write_text(
        "# Breakout Archetypes\n\nCollect reusable expansion patterns here after they have multiple reviewed examples.\n",
        encoding="utf-8",
    )


def export_observation_library(
    events_csv: str | Path,
    *,
    output_dir: str | Path = "research/observations",
    obsidian_dir: str | Path = "obsidian",
    limit: int | None = None,
) -> ObservationLibraryPaths:
    source_path = Path(events_csv)
    events = pd.read_csv(source_path)
    if limit is not None:
        events = events.head(limit)
    records = build_observation_records(events, source_path=source_path)

    output_root = Path(output_dir)
    records_jsonl = output_root / "observation_records.jsonl"
    records_csv = output_root / "observation_records.csv"
    schema_yaml = output_root / "observation_schema.yaml"
    output_root.mkdir(parents=True, exist_ok=True)
    _write_jsonl(records, records_jsonl)
    records.to_csv(records_csv, index=False)
    _write_schema(schema_yaml)

    wiki_root = Path(obsidian_dir) / "wiki"
    cases_dir = wiki_root / "cases"
    patterns_dir = wiki_root / "patterns"
    concepts_dir = wiki_root / "concepts"
    maps_dir = wiki_root / "maps"
    index_md = wiki_root / "Indicator Observation Library.md"

    for _, record in records.iterrows():
        _write_case_note(record, cases_dir / f"{record['observation_id']}.md")
    _write_pattern_pages(records, patterns_dir)
    _write_concept_pages(concepts_dir)
    _write_map_pages(maps_dir)
    _write_index(records, index_md)

    return ObservationLibraryPaths(
        records_jsonl=records_jsonl,
        records_csv=records_csv,
        schema_yaml=schema_yaml,
        index_md=index_md,
        cases_dir=cases_dir,
        patterns_dir=patterns_dir,
        concepts_dir=concepts_dir,
    )
