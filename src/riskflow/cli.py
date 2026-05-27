from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .baskets import build_equal_weight_return_index_frame
from .compression import calculate_compression_features
from .config import UniverseConfig, load_universe_config
from .data_loader import load_universe_ohlcv
from .event_study import run_event_study
from .flow_graph import build_flow_graph_tables
from .flow_research import run_flow_research
from .indicator_engine import calculate_indicator
from .reports import (
    export_event_study_reports,
    export_flow_graph_reports,
    export_flow_research_reports,
    export_mtf_research_reports,
    export_scan_reports,
    export_score_research_reports,
    export_setup_research_reports,
    export_signal_research_reports,
    export_state_research_reports,
    export_transition_research_reports,
)
from .research_outcomes import HORIZONS
from .mtf import MTF_LEADERBOARD_COLUMNS, RESEARCH_MTF_PRESET, append_mtf_context, normalize_timeframe
from .mtf_research import run_mtf_research
from .observation_library import export_observation_library
from .resample import research_mtf_derivations, resample_universe
from .score_research import run_score_research
from .signal_grammar import export_grammar_lab
from .signal_research import run_signal_research
from .setup_quality import calculate_setup_quality
from .setup_research import run_setup_research
from .state_research import run_state_research
from .states import classify_state_frame
from .transition_research import run_transition_research
from .visual_review import VisualReviewSettings, run_visual_review


LEADERBOARD_COLUMNS = [
    "symbol",
    "name",
    "sector",
    "subgroup",
    "latest_close",
    "final_signal",
    "price_component",
    "relative_component",
    "benchmark_used",
    "benchmark_name",
    "benchmark_role",
    "benchmark_method",
    "benchmark_exclude_self",
    "benchmark_target_excluded",
    "benchmark_fallback_used",
    "benchmark_fallback_reason",
    "benchmark_active_members",
    "benchmark_missing_members",
    "benchmark_member_count",
    "benchmark_min_active_members",
    "benchmark_passed",
    "benchmark_confidence",
    "benchmark_notes",
    "viscosity",
    "above_viscosity",
    "gradient_driver",
    "compression_score",
    "compression_score_v0",
    "compression_duration",
    "compression_stability",
    "leader_quality_score",
    "compression_quality_score",
    "relative_accumulation_score",
    "setup_readiness_score",
    "extension_risk_score",
    "data_quality_score",
    "trader_score_v0",
    "trader_rank",
    "state",
    "state_model",
    "state_confidence",
    "state_reason",
    "state_tags",
    "setup_state_v0",
    "setup_tags",
    "opportunity_score",
    "opportunity_score_v0",
    "notes",
]


def _benchmark_confidence(
    diagnostics: pd.DataFrame,
    *,
    target_excluded: bool,
    fallback_used: bool,
) -> pd.Series:
    active = pd.to_numeric(diagnostics["benchmark_active_members"], errors="coerce")
    required = pd.to_numeric(diagnostics["benchmark_min_active_members"], errors="coerce")
    passed = diagnostics["benchmark_passed"].eq(True)
    confidence = pd.Series("unavailable", index=diagnostics.index, dtype=object)
    confidence.loc[passed & (active >= required + 2) & target_excluded & ~fallback_used] = "high"
    confidence.loc[passed & (confidence == "unavailable")] = "medium"
    confidence.loc[~passed & diagnostics["basket_index"].notna()] = "low"
    return confidence


def _benchmark_notes(
    diagnostics: pd.DataFrame,
    *,
    benchmark_name: str,
    target_symbol: str,
    target_excluded: bool,
    fallback_used: bool,
) -> pd.Series:
    active = pd.to_numeric(diagnostics["benchmark_active_members"], errors="coerce")
    required = pd.to_numeric(diagnostics["benchmark_min_active_members"], errors="coerce")
    notes: list[str] = []
    for date, passed in diagnostics["benchmark_passed"].items():
        row_notes: list[str] = [f"compared against {benchmark_name}"]
        row_notes.append(f"target {'excluded' if target_excluded else 'included'}")
        if fallback_used:
            row_notes.append(f"fallback to full basket; ex-target {target_symbol} had too few active members")
        if not bool(passed):
            active_value = active.loc[date]
            required_value = required.loc[date]
            active_text = "unknown" if pd.isna(active_value) else str(int(active_value))
            required_text = "unknown" if pd.isna(required_value) else str(int(required_value))
            row_notes.append(f"benchmark below active-member requirement {active_text}/{required_text}")
        notes.append("; ".join(row_notes))
    return pd.Series(notes, index=diagnostics.index, dtype=object)


def _attach_benchmark_diagnostics(
    frame: pd.DataFrame,
    diagnostics: pd.DataFrame,
    *,
    benchmark_name: str,
    benchmark_base_name: str,
    benchmark_role: str,
    benchmark_exclude_self: bool,
    target_symbol: str,
    target_excluded: bool,
    fallback_used: bool,
    fallback_reason: str = "",
) -> pd.DataFrame:
    aligned = diagnostics.reindex(frame.index)
    frame["benchmark_used"] = benchmark_name
    frame["benchmark_name"] = benchmark_name
    frame["benchmark_base_name"] = benchmark_base_name
    frame["benchmark_role"] = benchmark_role
    frame["benchmark_method"] = "equal_weight_return_index"
    frame["benchmark_exclude_self"] = bool(benchmark_exclude_self)
    frame["benchmark_target_excluded"] = bool(target_excluded)
    frame["benchmark_fallback_used"] = bool(fallback_used)
    frame["benchmark_fallback_reason"] = fallback_reason
    frame["benchmark_active_members"] = aligned["benchmark_active_members"]
    frame["benchmark_missing_members"] = aligned["benchmark_missing_members"]
    frame["benchmark_member_count"] = aligned["benchmark_member_count"]
    frame["benchmark_min_active_members"] = aligned["benchmark_min_active_members"]
    frame["benchmark_passed"] = aligned["benchmark_passed"]
    frame["benchmark_confidence"] = _benchmark_confidence(
        aligned,
        target_excluded=target_excluded,
        fallback_used=fallback_used,
    )
    frame["benchmark_notes"] = _benchmark_notes(
        aligned,
        benchmark_name=benchmark_name,
        target_symbol=target_symbol,
        target_excluded=target_excluded,
        fallback_used=fallback_used,
    )
    return frame


def build_analysis_frames(
    universe: UniverseConfig,
    raw_frames: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], pd.Series, list[str]]:
    warnings: list[str] = []
    closes = {symbol: frame["close"] for symbol, frame in raw_frames.items()}
    basket_frame = build_equal_weight_return_index_frame(
        closes,
        min_active_members=universe.min_active_members,
        name=universe.benchmark.name,
    )
    basket = basket_frame["basket_index"].rename(universe.benchmark.name)
    if basket.dropna().empty:
        warnings.append(
            f"Benchmark {universe.benchmark.name} has no valid values. "
            f"Check min_active_members={universe.min_active_members} and CSV overlap."
        )

    analysis_frames: dict[str, pd.DataFrame] = {}
    for asset in universe.assets:
        raw = raw_frames.get(asset.symbol)
        if raw is None:
            continue
        ex_target_closes = {symbol: close for symbol, close in closes.items() if symbol != asset.symbol}
        use_ex_target = universe.benchmark.exclude_self and len(ex_target_closes) >= universe.min_active_members
        fallback_used = False
        fallback_reason = ""
        benchmark_name = universe.benchmark.name
        benchmark_frame = basket_frame
        if universe.benchmark.exclude_self and use_ex_target:
            ex_name = f"{universe.benchmark.name}_EX_{asset.symbol}"
            ex_frame = build_equal_weight_return_index_frame(
                ex_target_closes,
                min_active_members=universe.min_active_members,
                name=ex_name,
            )
            if ex_frame["basket_index"].dropna().empty:
                fallback_used = True
                fallback_reason = "ex_target_unavailable"
                warnings.append(
                    f"{asset.symbol}: ex-target benchmark {ex_name} unavailable; "
                    f"falling back to {universe.benchmark.name}."
                )
            else:
                benchmark_name = ex_name
                benchmark_frame = ex_frame
        elif universe.benchmark.exclude_self:
            fallback_used = True
            fallback_reason = "too_few_members_for_ex_target"
            warnings.append(
                f"{asset.symbol}: not enough members to build ex-target benchmark; "
                f"falling back to {universe.benchmark.name}."
            )
        indicator = calculate_indicator(
            raw["close"],
            benchmark_frame["basket_index"].rename(benchmark_name),
            settings=universe.indicator_settings,
            weights=universe.weights,
        )
        indicator = _attach_benchmark_diagnostics(
            indicator,
            benchmark_frame,
            benchmark_name=benchmark_name,
            benchmark_base_name=universe.benchmark.name,
            benchmark_role=universe.benchmark.role,
            benchmark_exclude_self=universe.benchmark.exclude_self,
            target_symbol=asset.symbol,
            target_excluded=not fallback_used and benchmark_name != universe.benchmark.name,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )
        compression = calculate_compression_features(raw, settings=universe.compression_settings)
        analysis = indicator.join(compression, how="left")
        state_details = classify_state_frame(analysis)
        analysis = analysis.join(state_details, how="left")
        setup_quality = calculate_setup_quality(analysis)
        analysis = analysis.join(setup_quality, how="left")
        analysis["opportunity_score"] = analysis["opportunity_score_v0"]
        analysis_frames[asset.symbol] = analysis

    return analysis_frames, basket, warnings


def _latest_notes(row: pd.Series) -> str:
    notes: list[str] = []
    if pd.isna(row.get("benchmark")):
        notes.append("benchmark unavailable")
    benchmark_notes = row.get("benchmark_notes")
    if pd.notna(benchmark_notes) and str(benchmark_notes):
        notes.append(str(benchmark_notes))
    if pd.isna(row.get("relative_component")):
        notes.append("relative unavailable")
    if pd.isna(row.get("compression_score")):
        notes.append("compression unavailable")
    setup_notes = row.get("setup_notes")
    if pd.notna(setup_notes) and str(setup_notes):
        notes.append(str(setup_notes))
    if row.get("state") == "Unknown":
        notes.append("insufficient or mixed signal")
    return "; ".join(notes)


def build_leaderboard(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    include_mtf: bool = False,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    assets = universe.asset_by_symbol

    for symbol, analysis in analysis_frames.items():
        asset = assets[symbol]
        latest_index = analysis["target"].last_valid_index()
        if latest_index is None:
            rows.append(
                {
                    "symbol": symbol,
                    "name": asset.name,
                    "sector": asset.sector,
                    "subgroup": asset.subgroup,
                    "notes": "no valid close data",
                }
            )
            continue

        latest = analysis.loc[latest_index]
        row = {
            "symbol": symbol,
            "name": asset.name,
            "sector": asset.sector,
            "subgroup": asset.subgroup,
            "latest_close": latest.get("target"),
            "final_signal": latest.get("final_signal"),
            "price_component": latest.get("price_component"),
            "relative_component": latest.get("relative_component"),
            "benchmark_used": latest.get("benchmark_used"),
            "benchmark_name": latest.get("benchmark_name"),
            "benchmark_role": latest.get("benchmark_role"),
            "benchmark_method": latest.get("benchmark_method"),
            "benchmark_exclude_self": latest.get("benchmark_exclude_self"),
            "benchmark_target_excluded": latest.get("benchmark_target_excluded"),
            "benchmark_fallback_used": latest.get("benchmark_fallback_used"),
            "benchmark_fallback_reason": latest.get("benchmark_fallback_reason"),
            "benchmark_active_members": latest.get("benchmark_active_members"),
            "benchmark_missing_members": latest.get("benchmark_missing_members"),
            "benchmark_member_count": latest.get("benchmark_member_count"),
            "benchmark_min_active_members": latest.get("benchmark_min_active_members"),
            "benchmark_passed": latest.get("benchmark_passed"),
            "benchmark_confidence": latest.get("benchmark_confidence"),
            "benchmark_notes": latest.get("benchmark_notes"),
            "viscosity": latest.get("viscosity"),
            "above_viscosity": bool(latest.get("above_viscosity")) if pd.notna(latest.get("above_viscosity")) else False,
            "gradient_driver": latest.get("gradient_driver"),
            "compression_score": latest.get("compression_score"),
            "compression_score_v0": latest.get("compression_score_v0"),
            "compression_duration": latest.get("compression_duration"),
            "compression_stability": latest.get("compression_stability"),
            "leader_quality_score": latest.get("leader_quality_score"),
            "compression_quality_score": latest.get("compression_quality_score"),
            "relative_accumulation_score": latest.get("relative_accumulation_score"),
            "setup_readiness_score": latest.get("setup_readiness_score"),
            "extension_risk_score": latest.get("extension_risk_score"),
            "data_quality_score": latest.get("data_quality_score"),
            "trader_score_v0": latest.get("trader_score_v0"),
            "state": latest.get("state"),
            "state_model": latest.get("state_model"),
            "state_confidence": latest.get("state_confidence"),
            "state_reason": latest.get("state_reason"),
            "state_tags": latest.get("state_tags"),
            "setup_state_v0": latest.get("setup_state_v0"),
            "setup_tags": latest.get("setup_tags"),
            "opportunity_score": latest.get("opportunity_score"),
            "opportunity_score_v0": latest.get("opportunity_score_v0"),
            "notes": _latest_notes(latest),
        }
        if include_mtf:
            for column in MTF_LEADERBOARD_COLUMNS:
                row[column] = latest.get(column)
        rows.append(row)

    leaderboard = pd.DataFrame(rows)
    columns = [*LEADERBOARD_COLUMNS, *MTF_LEADERBOARD_COLUMNS] if include_mtf else LEADERBOARD_COLUMNS
    for column in columns:
        if column not in leaderboard.columns:
            leaderboard[column] = pd.NA
    if "trader_score_v0" in leaderboard.columns:
        leaderboard["trader_rank"] = leaderboard["trader_score_v0"].rank(
            ascending=False,
            method="min",
            na_option="bottom",
        )
    leaderboard = leaderboard[columns]
    return leaderboard.sort_values(["opportunity_score", "final_signal"], ascending=[False, False], na_position="last")


def load_and_analyze(
    config_path: str | Path,
    data_dir: str | Path,
    timeframe: str,
) -> tuple[UniverseConfig, pd.DataFrame, dict[str, pd.DataFrame], list[str]]:
    universe = load_universe_config(config_path)
    raw_frames, load_warnings = load_universe_ohlcv(universe, data_dir=data_dir, timeframe=timeframe)
    if not raw_frames:
        raise RuntimeError(
            f"No usable CSV files found in {Path(data_dir)}. "
            "Expected files like DOGE.csv or DOGE_1d.csv with date, open, high, low, close, volume."
        )
    analysis_frames, _basket, analysis_warnings = build_analysis_frames(universe, raw_frames)
    leaderboard = build_leaderboard(universe, analysis_frames)
    return universe, leaderboard, analysis_frames, [*load_warnings, *analysis_warnings]


def resolve_context_timeframes(args: argparse.Namespace) -> list[str]:
    if getattr(args, "mtf_preset", None) == "research-mtf":
        return list(RESEARCH_MTF_PRESET)
    return [normalize_timeframe(timeframe) for timeframe in getattr(args, "context_timeframes", [])]


def load_context_analysis_frames(
    universe: UniverseConfig,
    *,
    data_dir: str | Path,
    context_timeframes: list[str],
) -> tuple[dict[str, dict[str, pd.DataFrame]], list[str]]:
    context_by_timeframe: dict[str, dict[str, pd.DataFrame]] = {}
    warnings: list[str] = []
    for timeframe in context_timeframes:
        raw_frames, load_warnings = load_universe_ohlcv(universe, data_dir=data_dir, timeframe=timeframe)
        warnings.extend(f"{timeframe}: {warning}" for warning in load_warnings)
        if not raw_frames:
            context_by_timeframe[timeframe] = {}
            continue
        analysis_frames, _basket, analysis_warnings = build_analysis_frames(universe, raw_frames)
        warnings.extend(f"{timeframe}: {warning}" for warning in analysis_warnings)
        context_by_timeframe[timeframe] = analysis_frames
    return context_by_timeframe, warnings


def load_and_analyze_with_mtf(
    config_path: str | Path,
    data_dir: str | Path,
    primary_timeframe: str,
    context_timeframes: list[str],
) -> tuple[UniverseConfig, pd.DataFrame, dict[str, pd.DataFrame], list[str]]:
    universe, _leaderboard, primary_frames, warnings = load_and_analyze(
        config_path,
        data_dir=data_dir,
        timeframe=primary_timeframe,
    )
    context_by_timeframe, context_warnings = load_context_analysis_frames(
        universe,
        data_dir=data_dir,
        context_timeframes=context_timeframes,
    )
    enriched_frames = append_mtf_context(
        primary_frames,
        context_by_timeframe,
        primary_timeframe=primary_timeframe,
        context_timeframes=context_timeframes,
    )
    leaderboard = build_leaderboard(universe, enriched_frames, include_mtf=True)
    return universe, leaderboard, enriched_frames, [*warnings, *context_warnings]


def scan_command(args: argparse.Namespace) -> int:
    try:
        context_timeframes = resolve_context_timeframes(args)
        if context_timeframes:
            universe, leaderboard, _analysis_frames, warnings = load_and_analyze_with_mtf(
                args.config,
                data_dir=args.data_dir,
                primary_timeframe=args.timeframe,
                context_timeframes=context_timeframes,
            )
        else:
            universe, leaderboard, _analysis_frames, warnings = load_and_analyze(
                args.config,
                data_dir=args.data_dir,
                timeframe=args.timeframe,
            )
    except Exception as exc:
        print(f"Scan failed: {exc}")
        return 1

    paths = export_scan_reports(
        leaderboard,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote leaderboard CSV: {paths['csv']}")
    print(f"Wrote leaderboard HTML: {paths['html']}")
    print(f"Wrote Obsidian report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def mtf_research_command(args: argparse.Namespace) -> int:
    try:
        context_timeframes = [normalize_timeframe(timeframe) for timeframe in args.context_timeframes]
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze_with_mtf(
            args.config,
            data_dir=args.data_dir,
            primary_timeframe=args.primary_timeframe,
            context_timeframes=context_timeframes,
        )
    except Exception as exc:
        print(f"MTF research failed: {exc}")
        return 1

    summary, records = run_mtf_research(
        analysis_frames,
        timeframe=args.primary_timeframe,
        benchmark_name=universe.benchmark.name,
        min_sample_size=args.min_sample_size,
        entry_lag_bars=args.entry_lag_bars,
        cooldown_bars=args.cooldown_bars,
    )
    paths = export_mtf_research_reports(
        summary,
        records,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote MTF research records CSV: {paths['records_csv']}")
    print(f"Wrote MTF research summary CSV: {paths['summary_csv']}")
    print(f"Wrote MTF research HTML: {paths['summary_html']}")
    print(f"Wrote Obsidian MTF research report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def flow_graph_command(args: argparse.Namespace) -> int:
    try:
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"Flow graph failed: {exc}")
        return 1

    nodes, edges, chains = build_flow_graph_tables(
        universe,
        analysis_frames,
        timeframe=args.timeframe,
    )
    paths = export_flow_graph_reports(
        nodes,
        edges,
        chains,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote flow graph nodes CSV: {paths['nodes_csv']}")
    print(f"Wrote flow graph edges CSV: {paths['edges_csv']}")
    print(f"Wrote flow graph chains CSV: {paths['chains_csv']}")
    print(f"Wrote Obsidian flow graph report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def flow_research_command(args: argparse.Namespace) -> int:
    try:
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"Flow research failed: {exc}")
        return 1

    summary, records = run_flow_research(
        universe,
        analysis_frames,
        timeframe=args.timeframe,
        min_sample_size=args.min_sample_size,
        entry_lag_bars=args.entry_lag_bars,
        cooldown_bars=args.cooldown_bars,
    )
    paths = export_flow_research_reports(
        summary,
        records,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote flow research records CSV: {paths['records_csv']}")
    print(f"Wrote flow research summary CSV: {paths['summary_csv']}")
    print(f"Wrote flow research HTML: {paths['summary_html']}")
    print(f"Wrote Obsidian flow research report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def transition_research_command(args: argparse.Namespace) -> int:
    try:
        context_timeframes = resolve_context_timeframes(args)
        if context_timeframes:
            universe, _leaderboard, analysis_frames, warnings = load_and_analyze_with_mtf(
                args.config,
                data_dir=args.data_dir,
                primary_timeframe=args.timeframe,
                context_timeframes=context_timeframes,
            )
        else:
            universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
                args.config,
                data_dir=args.data_dir,
                timeframe=args.timeframe,
            )
    except Exception as exc:
        print(f"Transition research failed: {exc}")
        return 1

    summary, records, unconditional, conditioned = run_transition_research(
        universe,
        analysis_frames,
        timeframe=args.timeframe,
        min_sample_size=args.min_sample_size,
        entry_lag_bars=args.entry_lag_bars,
    )
    paths = export_transition_research_reports(
        summary,
        records,
        unconditional,
        conditioned,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote transition research records CSV: {paths['records_csv']}")
    print(f"Wrote transition research summary CSV: {paths['summary_csv']}")
    print(f"Wrote unconditional transition matrix CSV: {paths['unconditional_csv']}")
    print(f"Wrote conditioned transition matrix CSV: {paths['conditioned_csv']}")
    print(f"Wrote transition research HTML: {paths['summary_html']}")
    print(f"Wrote Obsidian transition research report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def event_study_command(args: argparse.Namespace) -> int:
    try:
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"Event study failed: {exc}")
        return 1

    summary, records = run_event_study(
        analysis_frames,
        timeframe=args.timeframe,
        benchmark_name=universe.benchmark.name,
        min_sample_size=args.min_sample_size,
        entry_lag_bars=args.entry_lag_bars,
        cooldown_bars=args.cooldown_bars,
    )
    paths = export_event_study_reports(
        summary,
        records,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote event study CSV: {paths['csv']}")
    print(f"Wrote event study records CSV: {paths['records_csv']}")
    print(f"Wrote event study HTML: {paths['html']}")
    print(f"Wrote Obsidian event study report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def signal_research_command(args: argparse.Namespace) -> int:
    try:
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"Signal research failed: {exc}")
        return 1

    summary, records = run_signal_research(
        analysis_frames,
        timeframe=args.timeframe,
        benchmark_name=universe.benchmark.name,
        min_sample_size=args.min_sample_size,
        cooldown_bars=args.cooldown_bars,
        entry_lag_bars=args.entry_lag_bars,
    )
    paths = export_signal_research_reports(summary, records, report_dir=args.report_dir)
    print(f"Wrote signal research summary CSV: {paths['summary_csv']}")
    print(f"Wrote signal research summary HTML: {paths['summary_html']}")
    print(f"Wrote signal research event records CSV: {paths['records_csv']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def setup_research_command(args: argparse.Namespace) -> int:
    try:
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"Setup research failed: {exc}")
        return 1

    summary, records = run_setup_research(
        analysis_frames,
        timeframe=args.timeframe,
        benchmark_name=universe.benchmark.name,
        min_sample_size=args.min_sample_size,
        cooldown_bars=args.cooldown_bars,
        entry_lag_bars=args.entry_lag_bars,
    )
    paths = export_setup_research_reports(summary, records, report_dir=args.report_dir)
    print(f"Wrote setup research summary CSV: {paths['summary_csv']}")
    print(f"Wrote setup research summary HTML: {paths['summary_html']}")
    print(f"Wrote setup research event records CSV: {paths['records_csv']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def state_research_command(args: argparse.Namespace) -> int:
    try:
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"State research failed: {exc}")
        return 1

    summary, records, transition_matrix = run_state_research(
        analysis_frames,
        timeframe=args.timeframe,
        benchmark_name=universe.benchmark.name,
        min_sample_size=args.min_sample_size,
        entry_lag_bars=args.entry_lag_bars,
    )
    paths = export_state_research_reports(
        summary,
        records,
        transition_matrix,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote state research summary CSV: {paths['summary_csv']}")
    print(f"Wrote state research summary HTML: {paths['summary_html']}")
    print(f"Wrote state research records CSV: {paths['records_csv']}")
    print(f"Wrote state transition matrix CSV: {paths['transition_csv']}")
    print(f"Wrote Obsidian state research report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def score_research_command(args: argparse.Namespace) -> int:
    try:
        universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"Score research failed: {exc}")
        return 1

    score_summary, bucket_summary, ic_summary, records = run_score_research(
        analysis_frames,
        timeframe=args.timeframe,
        benchmark_name=universe.benchmark.name,
        bucket_count=args.bucket_count,
        min_symbols_per_date=args.min_symbols_per_date,
        min_bucket_sample_size=args.min_bucket_sample_size,
        entry_lag_bars=args.entry_lag_bars,
    )
    paths = export_score_research_reports(
        score_summary,
        bucket_summary,
        ic_summary,
        records,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    print(f"Wrote score research records CSV: {paths['records_csv']}")
    print(f"Wrote score bucket summary CSV: {paths['bucket_summary_csv']}")
    print(f"Wrote score IC summary CSV: {paths['ic_summary_csv']}")
    print(f"Wrote score summary CSV: {paths['score_summary_csv']}")
    print(f"Wrote score research HTML: {paths['summary_html']}")
    print(f"Wrote Obsidian score research report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def visual_review_command(args: argparse.Namespace) -> int:
    try:
        universe = load_universe_config(args.config)
        raw_frames, load_warnings = load_universe_ohlcv(
            universe,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
        if not raw_frames:
            raise RuntimeError(
                f"No usable CSV files found in {Path(args.data_dir)}. "
                "Expected files like DOGE.csv or DOGE_1d.csv with date, open, high, low, close, volume."
            )
        analysis_frames, _basket, analysis_warnings = build_analysis_frames(universe, raw_frames)
        settings = VisualReviewSettings(
            event_mode=args.event_mode,
            timeframe=args.timeframe,
            horizon=args.horizon,
            min_forward_relative_return=args.min_forward_relative_return,
            entry_lag_bars=args.entry_lag_bars,
            cooldown_bars=args.cooldown_bars,
            min_history_bars=args.min_history_bars,
            min_signal_std=args.min_signal_std,
            lookback_bars=args.lookback_bars,
            forward_bars=args.forward_bars,
            max_events=args.max_events,
            max_events_per_symbol=args.max_events_per_symbol,
        )
        _records, paths = run_visual_review(
            universe,
            raw_frames,
            analysis_frames,
            report_dir=args.report_dir,
            settings=settings,
        )
        warnings = [*load_warnings, *analysis_warnings]
    except Exception as exc:
        print(f"Visual review failed: {exc}")
        return 1

    print(f"Wrote visual review events CSV: {paths['events_csv']}")
    print(f"Wrote visual review gallery: {paths['gallery_md']}")
    print(f"Wrote visual review images directory: {paths['image_dir']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def observation_library_command(args: argparse.Namespace) -> int:
    try:
        paths = export_observation_library(
            args.events_csv,
            output_dir=args.output_dir,
            obsidian_dir=args.obsidian_dir,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"Observation library export failed: {exc}")
        return 1

    print(f"Wrote observation records JSONL: {paths.records_jsonl}")
    print(f"Wrote observation records CSV: {paths.records_csv}")
    print(f"Wrote observation schema: {paths.schema_yaml}")
    print(f"Wrote Obsidian index: {paths.index_md}")
    print(f"Wrote Obsidian cases directory: {paths.cases_dir}")
    return 0


def grammar_lab_command(args: argparse.Namespace) -> int:
    try:
        paths = export_grammar_lab(
            registry_path=args.registry,
            observations_csv=args.observations_csv,
            output_dir=args.output_dir,
            obsidian_dir=args.obsidian_dir,
        )
    except Exception as exc:
        print(f"Grammar lab export failed: {exc}")
        return 1

    print(f"Wrote grammar primitive summary: {paths.primitive_summary_csv}")
    print(f"Wrote grammar review plan: {paths.review_plan_md}")
    if paths.obsidian_note_md is not None:
        print(f"Wrote Obsidian grammar note: {paths.obsidian_note_md}")
    return 0


def resample_command(args: argparse.Namespace) -> int:
    try:
        universe = load_universe_config(args.config)
        derivations = (
            research_mtf_derivations()
            if args.preset == "research-mtf"
            else [(args.from_timeframe, tuple(args.to_timeframe))]
        )
        all_written: list[Path] = []
        all_warnings: list[str] = []
        for from_timeframe, to_timeframes in derivations:
            written, warnings = resample_universe(
                universe,
                data_dir=args.data_dir,
                from_timeframe=from_timeframe,
                to_timeframes=to_timeframes,
            )
            all_written.extend(written)
            all_warnings.extend(warnings)
    except Exception as exc:
        print(f"Resample failed: {exc}")
        return 1

    print(f"Wrote {len(all_written)} resampled CSV files.")
    for path in all_written:
        print(f"Wrote: {path}")
    if all_warnings:
        print(f"Warnings: {len(all_warnings)}")
        for warning in all_warnings:
            print(f"- {warning}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="riskflow", description="Riskflow meme leadership research CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
        subparser.add_argument("--timeframe", default="1d", help="Timeframe suffix for CSV lookup, e.g. 1d or 4h.")
        subparser.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
        subparser.add_argument("--report-dir", default="reports", help="Directory for CSV and HTML reports.")

    scan = subparsers.add_parser("scan", help="Build the latest meme leaderboard.")
    add_common_arguments(scan)
    scan.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    scan.add_argument(
        "--context-timeframes",
        nargs="+",
        default=[],
        help="Optional MTF sidecar timeframes to append, such as 1w 3d 12h 4h.",
    )
    scan.add_argument(
        "--mtf-preset",
        choices=["none", "research-mtf"],
        default="none",
        help="Use research-mtf to append 1w/3d/12h/4h context columns.",
    )
    scan.set_defaults(func=scan_command)

    event_study = subparsers.add_parser("event-study", help="Run Layer 7 event-study evidence reports.")
    add_common_arguments(event_study)
    event_study.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    event_study.add_argument(
        "--min-sample-size",
        type=int,
        default=20,
        help="Minimum event count before an event result can be classified beyond inconclusive.",
    )
    event_study.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the event before forward-return measurement starts.",
    )
    event_study.add_argument(
        "--cooldown-bars",
        type=int,
        default=30,
        help="Minimum bars before the same symbol/event can fire again.",
    )
    event_study.set_defaults(func=event_study_command)

    signal_research = subparsers.add_parser("signal-research", help="Run Layer 3 challenger-signal research.")
    add_common_arguments(signal_research)
    signal_research.add_argument(
        "--min-sample-size",
        type=int,
        default=5,
        help="Minimum event count before a signal result can be classified beyond inconclusive.",
    )
    signal_research.add_argument(
        "--cooldown-bars",
        type=int,
        default=30,
        help="Minimum bars before the same symbol/variant can fire another research event.",
    )
    signal_research.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the signal event before forward-return measurement starts.",
    )
    signal_research.set_defaults(func=signal_research_command)

    setup_research = subparsers.add_parser("setup-research", help="Run Layer 4 setup-quality research.")
    add_common_arguments(setup_research)
    setup_research.add_argument(
        "--min-sample-size",
        type=int,
        default=5,
        help="Minimum event count before a setup result can be classified beyond inconclusive.",
    )
    setup_research.add_argument(
        "--cooldown-bars",
        type=int,
        default=30,
        help="Minimum bars before the same symbol/setup event can fire again.",
    )
    setup_research.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the setup event before forward-return measurement starts.",
    )
    setup_research.set_defaults(func=setup_research_command)

    state_research = subparsers.add_parser("state-research", help="Run Layer 5 lifecycle-state research.")
    add_common_arguments(state_research)
    state_research.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    state_research.add_argument(
        "--min-sample-size",
        type=int,
        default=5,
        help="Minimum state observation count before a state result can be classified beyond inconclusive.",
    )
    state_research.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the state observation before forward-return measurement starts.",
    )
    state_research.set_defaults(func=state_research_command)

    score_research = subparsers.add_parser("score-research", help="Run Layer 6 score ranking research.")
    add_common_arguments(score_research)
    score_research.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    score_research.add_argument(
        "--bucket-count",
        type=int,
        default=10,
        help="Requested date-wise score bucket count.",
    )
    score_research.add_argument(
        "--min-symbols-per-date",
        type=int,
        default=5,
        help="Minimum valid symbols on a date before calculating rank IC.",
    )
    score_research.add_argument(
        "--min-bucket-sample-size",
        type=int,
        default=20,
        help="Minimum bucket observation count before a bucket result can be classified beyond inconclusive.",
    )
    score_research.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the score observation before forward-return measurement starts.",
    )
    score_research.set_defaults(func=score_research_command)

    visual_review = subparsers.add_parser(
        "visual-review",
        help="Generate chart snapshots for strong forward relative breakout events.",
    )
    add_common_arguments(visual_review)
    visual_review.add_argument(
        "--event-mode",
        choices=[
            "breakout",
            "impulse-retest",
            "coil-reclaim",
            "missed-breakout",
            "bearish-weakness",
            "noisy-false-positive",
        ],
        default="breakout",
        help=(
            "Use breakout for hindsight winners, impulse-retest for late confirmation, coil-reclaim for early lower-zone reclaim setups, "
            "or grammar-targeted modes for missed, bearish, and noisy review cases."
        ),
    )
    visual_review.add_argument(
        "--horizon",
        type=int,
        choices=list(HORIZONS),
        default=30,
        help="Forward relative-return horizon used to select visual review events.",
    )
    visual_review.add_argument(
        "--min-forward-relative-return",
        type=float,
        default=0.30,
        help="Minimum forward relative return required for a visual review event.",
    )
    visual_review.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the candidate date before forward-return measurement starts.",
    )
    visual_review.add_argument(
        "--cooldown-bars",
        type=int,
        default=30,
        help="Minimum bars before the same symbol can produce another visual review event. For 4H archeology, 12 can reveal nearby setup/follow-through cases.",
    )
    visual_review.add_argument(
        "--min-history-bars",
        type=int,
        default=40,
        help="Minimum prior bars required before a visual review event can be selected.",
    )
    visual_review.add_argument(
        "--min-signal-std",
        type=float,
        default=0.02,
        help="Minimum recent signal standard deviation required to avoid flat bootstrap artifacts.",
    )
    visual_review.add_argument(
        "--lookback-bars",
        type=int,
        default=80,
        help="Bars to show before the event in each snapshot.",
    )
    visual_review.add_argument(
        "--forward-bars",
        type=int,
        default=30,
        help="Bars to show after the event in each snapshot.",
    )
    visual_review.add_argument(
        "--max-events",
        type=int,
        default=40,
        help="Maximum total snapshots to render.",
    )
    visual_review.add_argument(
        "--max-events-per-symbol",
        type=int,
        default=3,
        help="Maximum snapshots to render per symbol.",
    )
    visual_review.set_defaults(func=visual_review_command)

    observation_library = subparsers.add_parser(
        "observation-library",
        help="Export visual-review events into structured observation records and Obsidian wiki notes.",
    )
    observation_library.add_argument(
        "--events-csv",
        default="reports/visual_review/events.csv",
        help="Visual-review events CSV to convert into observation records.",
    )
    observation_library.add_argument(
        "--output-dir",
        default="research/observations",
        help="Directory for machine-readable observation records and schema.",
    )
    observation_library.add_argument(
        "--obsidian-dir",
        default="obsidian",
        help="Existing Obsidian vault directory to receive wiki notes.",
    )
    observation_library.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of visual-review rows to export.",
    )
    observation_library.set_defaults(func=observation_library_command)

    grammar_lab = subparsers.add_parser(
        "grammar-lab",
        help="Summarize Signal Grammar Lab primitive coverage and next review targets.",
    )
    grammar_lab.add_argument(
        "--registry",
        default="research/grammar/primitive_registry.yaml",
        help="Signal grammar primitive registry YAML.",
    )
    grammar_lab.add_argument(
        "--observations-csv",
        default="research/observations/observation_records.csv",
        help="Structured observation records CSV to summarize if present.",
    )
    grammar_lab.add_argument(
        "--output-dir",
        default="reports/grammar_lab",
        help="Directory for grammar lab summary outputs.",
    )
    grammar_lab.add_argument(
        "--obsidian-dir",
        default="obsidian",
        help="Existing Obsidian vault directory to receive the grammar lab map.",
    )
    grammar_lab.set_defaults(func=grammar_lab_command)

    mtf_research = subparsers.add_parser("mtf-research", help="Run Layer 8 multi-timeframe context research.")
    mtf_research.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
    mtf_research.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
    mtf_research.add_argument("--report-dir", default="reports", help="Directory for CSV and HTML reports.")
    mtf_research.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    mtf_research.add_argument(
        "--primary-timeframe",
        default="1d",
        help="Primary timeframe suffix for the event side of MTF research.",
    )
    mtf_research.add_argument(
        "--context-timeframes",
        nargs="+",
        default=list(RESEARCH_MTF_PRESET),
        help="Completed context timeframes to join as a sidecar.",
    )
    mtf_research.add_argument(
        "--min-sample-size",
        type=int,
        default=20,
        help="Minimum aligned and non-aligned sample size before classification can move beyond inconclusive.",
    )
    mtf_research.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the primary event before forward-return measurement starts.",
    )
    mtf_research.add_argument(
        "--cooldown-bars",
        type=int,
        default=30,
        help="Minimum bars before the same symbol/MTF event can fire again.",
    )
    mtf_research.set_defaults(func=mtf_research_command)

    flow_graph = subparsers.add_parser("flow-graph", help="Export Layer 9 capital-flow graph tables.")
    add_common_arguments(flow_graph)
    flow_graph.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    flow_graph.set_defaults(func=flow_graph_command)

    flow_research = subparsers.add_parser("flow-research", help="Run Layer 9 capital-flow graph evidence reports.")
    add_common_arguments(flow_research)
    flow_research.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    flow_research.add_argument(
        "--min-sample-size",
        type=int,
        default=20,
        help="Minimum supportive and non-supportive sample size before classification can move beyond inconclusive.",
    )
    flow_research.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the primary event before forward-return measurement starts.",
    )
    flow_research.add_argument(
        "--cooldown-bars",
        type=int,
        default=30,
        help="Minimum bars before the same symbol/flow event can fire again.",
    )
    flow_research.set_defaults(func=flow_research_command)

    transition_research = subparsers.add_parser("transition-research", help="Run Layer 10 transition evidence reports.")
    add_common_arguments(transition_research)
    transition_research.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    transition_research.add_argument(
        "--min-sample-size",
        type=int,
        default=5,
        help="Minimum transition-pair sample size before classification can move beyond inconclusive.",
    )
    transition_research.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the transition event before forward-return measurement starts.",
    )
    transition_research.add_argument(
        "--context-timeframes",
        nargs="+",
        default=[],
        help="Optional MTF sidecar timeframes to condition transition evidence, such as 1w 3d 12h 4h.",
    )
    transition_research.add_argument(
        "--mtf-preset",
        choices=["none", "research-mtf"],
        default="none",
        help="Use research-mtf to condition transitions on 1w/3d/12h/4h context.",
    )
    transition_research.set_defaults(func=transition_research_command)

    resample = subparsers.add_parser("resample", help="Derive higher-timeframe OHLCV CSVs from lower-timeframe files.")
    resample.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
    resample.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
    resample.add_argument(
        "--from-timeframe",
        default="1d",
        help="Source timeframe suffix, such as 1d or 1h. Ignored when --preset research-mtf is used.",
    )
    resample.add_argument(
        "--to-timeframe",
        nargs="+",
        default=["1w", "3d"],
        help="Target timeframe suffixes to create, such as 1w 3d or 12h 4h.",
    )
    resample.add_argument(
        "--preset",
        choices=["custom", "research-mtf"],
        default="custom",
        help="Use research-mtf to derive 1w/3d from 1d and 12h/4h from 1h.",
    )
    resample.set_defaults(func=resample_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
