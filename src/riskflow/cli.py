from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path

import pandas as pd

from .blocker_audit import run_blocker_audit
from .baskets import build_equal_weight_return_index_frame
from .compression import calculate_compression_features
from .config import UniverseConfig, load_universe_config
from .data_loader import load_universe_ohlcv
from .event_study import run_event_study
from .flow_graph import build_flow_graph_tables
from .flow_research import run_flow_research
from .grammar_search import (
    DEFAULT_GRAMMAR_SEARCH_GRID,
    GRAMMAR_SEARCH_MODEL,
    chart_review_queue,
    duplicate_outcome_clusters,
    family_timeframe_robustness,
    run_grammar_search,
    strict_baseline_referee,
    timeframe_cooldown,
    time_split_validation,
    write_grammar_review_packet,
)
from .indicator_behavior import (
    DEFAULT_CONCEPT_LIBRARY,
    DEFAULT_PRIMITIVE_REGISTRY,
    run_indicator_behavior_search,
)
from .indicator_engine import calculate_indicator
from .lab_director import (
    DEFAULT_DIRECTOR_GRID_DIR,
    DEFAULT_DIRECTOR_QUEUE_PATH,
    DEFAULT_DIRECTOR_REPORT_ROOT,
    LabDirectorOptions,
    append_queue_to_runtime,
    audit_director_plan,
    design_lane_recovery_experiments,
    run_director_inspect,
    run_director_plan_next,
)
from .lab_loop import (
    DEFAULT_CONCEPT_SCOREBOARD_PATH,
    DEFAULT_QUEUE_PATH,
    DEFAULT_REPORT_ROOT,
    DEFAULT_RUNTIME_QUEUE_PATH,
    DEFAULT_STATE_PATH,
    LAB_OBJECTIVES,
    LabLoopOptions,
    atomic_write_yaml,
    lab_loop_status,
    load_lab_queue,
    load_lab_state,
    load_yaml_file,
    run_lab_epoch,
    run_lab_loop,
    select_next_hypothesis,
    validate_lab_queue,
)
from .lab_supervisor import (
    DEFAULT_EVIDENCE_LEDGER_PATH,
    DEFAULT_SUPERVISOR_POLICY_PATH,
    SupervisorOptions,
    run_supervised_epochs,
    supervise_latest_epoch,
)
from .lab_ops import (
    LAB_OPS_REPORT_ROOT,
    LAB_OPS_RUNTIME_ROOT,
    LabOpsOptions,
    run_lab_ops_plan,
    run_lab_ops_report,
    run_lab_ops_run,
    run_lab_ops_status,
    run_lab_ops_stop,
)
from .ceo_ops import (
    CEO_REPORT_ROOT,
    _trace_grade_manual_data_import_required,
    run_ceo_action_board,
    run_ceo_artifact_coherence,
    run_ceo_approval_apply,
    run_ceo_approval_queue,
    run_ceo_approval_record,
    run_ceo_blocker_stack,
    run_ceo_capability_backlog,
    run_ceo_dispatch_receipt,
    run_ceo_heartbeat_status,
    CeoOpsOptions,
    run_ceo_champion_challenger,
    run_ceo_broaden_hypothesis_source,
    run_ceo_data_gate_brief,
    run_ceo_decision_quality,
    run_ceo_evidence_debt_register,
    run_ceo_execute_next,
    run_ceo_executive_kpis,
    run_ceo_eval_suite,
    run_ceo_eval_fixtures,
    run_ceo_fresh_withheld_validation_contract,
    run_ceo_withheld_split_manifest,
    run_ceo_fresh_withheld_snapshot_declare,
    run_ceo_fresh_withheld_snapshot_manifest,
    run_ceo_fresh_withheld_validation_executor,
    run_ceo_fresh_control_validation,
    run_ceo_fresh_data_preflight,
    run_ceo_flight_dashboard,
    run_ceo_frozen_candidate_validation,
    run_ceo_frozen_validation_executor,
    run_ceo_frozen_validation_rerun,
    run_ceo_guardrail_audit,
    run_ceo_heartbeat_journal,
    run_ceo_heartbeat_plan,
    run_ceo_lab_status_text,
    run_ceo_memory_delta,
    run_ceo_mission_score,
    run_ceo_org_progress_score,
    run_ceo_operating_dashboard,
    run_ceo_operating_incident_register,
    run_ceo_operator_brief,
    run_ceo_operator_step,
    run_ceo_patch_research_infra,
    run_ceo_plan,
    run_ceo_portfolio_allocator,
    run_ceo_preflight_gate,
    run_ceo_promotion_proposal,
    run_ceo_repair_apply,
    run_ceo_repair_plan,
    run_ceo_report,
    run_ceo_replay,
    run_ceo_resumption_brief,
    run_ceo_review,
    run_ceo_role_dispatch,
    run_ceo_role_queue,
    run_ceo_role_result,
    run_ceo_run_block,
    run_ceo_run_index,
    run_ceo_sidecar_evidence_brief,
    run_ceo_strategy_capital_dashboard,
    run_ceo_status,
    run_ceo_stop,
    run_ceo_heartbeat_tick,
    run_ceo_trace_grade,
)
from .meta_research import (
    DEFAULT_META_REPORT_ROOT,
    LabMetaOptions,
    read_latest_meta_status,
    run_lab_meta_inspect,
    run_lab_meta_plan,
)
from .reports import (
    export_event_study_reports,
    export_flow_graph_reports,
    export_flow_research_reports,
    export_grammar_search_reports,
    export_mtf_research_reports,
    export_scan_reports,
    export_score_research_reports,
    export_setup_research_reports,
    export_signal_research_reports,
    export_state_research_reports,
    export_transition_research_reports,
)
from .research_lane_router import run_lane_assignment
from .research_map import (
    DEFAULT_RESEARCH_MAP_PATH,
    DEFAULT_RESEARCH_MAP_REPORT_ROOT,
    run_research_map_update,
)
from .research_outcomes import HORIZONS
from .validation_governance import run_validation_governance
from .mtf import MTF_LEADERBOARD_COLUMNS, RESEARCH_MTF_PRESET, append_mtf_context, normalize_timeframe
from .mtf_research import run_mtf_research
from .obsidian_kg import (
    DEFAULT_KG_OUTPUT_DIR,
    DEFAULT_OBSIDIAN_DIR,
    DEFAULT_OBSIDIAN_GRID_DIR,
    DEFAULT_OBSIDIAN_QUEUE_PATH,
    DEFAULT_TARGETED_BULLISH_QUEUE_PATH,
    audit_knowledge_graph,
    build_knowledge_graph,
    compile_setup_journey_queue,
    compile_targeted_bullish_queue,
    export_evidence_summaries,
    load_obsidian_notes,
    validate_knowledge_graph,
    write_knowledge_audit_outputs,
    write_knowledge_graph_outputs,
)
from .observation_library import export_observation_library
from .resample import research_mtf_derivations, resample_universe
from .score_research import run_score_research
from .signal_grammar import calculate_signal_grammar_features, export_grammar_lab
from .signal_research import run_signal_research
from .setup_quality import calculate_setup_quality
from .setup_research import run_setup_research
from .state_research import run_state_research
from .states import classify_state_frame
from .transition_research import run_transition_research
from .visual_review import VisualReviewSettings, render_grammar_review_label_gallery, run_visual_review


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
    "grammar_model",
    "grammar_pressure_area_balance_20",
    "grammar_pressure_area_delta_5",
    "grammar_time_above_viscosity_20",
    "grammar_sustained_above_viscosity_10",
    "grammar_coil_under_viscosity",
    "grammar_relative_weakness_fails_to_accelerate",
    "grammar_minus_1_5_reclaim",
    "grammar_zero_reclaim",
    "grammar_bullish_divergence_20",
    "grammar_bearish_divergence_20",
    "grammar_clean_chop_quality",
    "grammar_chaotic_chop_quality",
    "grammar_reset_quality_watch",
    "grammar_constructive_reset_watch",
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
        analysis["volume"] = raw["volume"].reindex(analysis.index)
        state_details = classify_state_frame(analysis)
        analysis = analysis.join(state_details, how="left")
        setup_quality = calculate_setup_quality(analysis)
        analysis = analysis.join(setup_quality, how="left")
        grammar_features = calculate_signal_grammar_features(analysis)
        analysis = analysis.join(grammar_features, how="left")
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
            "grammar_model": latest.get("grammar_model"),
            "grammar_pressure_area_balance_20": latest.get("grammar_pressure_area_balance_20"),
            "grammar_pressure_area_delta_5": latest.get("grammar_pressure_area_delta_5"),
            "grammar_time_above_viscosity_20": latest.get("grammar_time_above_viscosity_20"),
            "grammar_sustained_above_viscosity_10": latest.get("grammar_sustained_above_viscosity_10"),
            "grammar_coil_under_viscosity": latest.get("grammar_coil_under_viscosity"),
            "grammar_relative_weakness_fails_to_accelerate": latest.get(
                "grammar_relative_weakness_fails_to_accelerate"
            ),
            "grammar_minus_1_5_reclaim": latest.get("grammar_minus_1_5_reclaim"),
            "grammar_zero_reclaim": latest.get("grammar_zero_reclaim"),
            "grammar_bullish_divergence_20": latest.get("grammar_bullish_divergence_20"),
            "grammar_bearish_divergence_20": latest.get("grammar_bearish_divergence_20"),
            "grammar_clean_chop_quality": latest.get("grammar_clean_chop_quality"),
            "grammar_chaotic_chop_quality": latest.get("grammar_chaotic_chop_quality"),
            "grammar_reset_quality_watch": latest.get("grammar_reset_quality_watch"),
            "grammar_constructive_reset_watch": latest.get("grammar_constructive_reset_watch"),
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


def obsidian_kg_command(args: argparse.Namespace) -> int:
    if args.obsidian_kg_action == "compile-targeted-bullish-queue":
        try:
            compiled = compile_targeted_bullish_queue(
                output_queue=args.output_queue,
                generated_grid_dir=args.generated_grid_dir,
            )
        except Exception as exc:
            print(f"Targeted bullish queue compile failed: {exc}")
            return 1
        queue = compiled["queue"]
        print(f"Wrote targeted bullish queue: {compiled['queue_path']}")
        print(f"Wrote generated grids under: {compiled['grid_dir']}")
        print(f"Hypotheses: {len(queue.get('queue', []))}")
        return 0

    try:
        nodes = load_obsidian_notes(args.obsidian_dir)
        graph = build_knowledge_graph(nodes)
    except Exception as exc:
        print(f"Obsidian KG load failed: {exc}")
        return 1

    if args.obsidian_kg_action == "validate":
        result = validate_knowledge_graph(graph)
        print(f"Obsidian KG nodes: {len(graph.nodes)}")
        print(f"Obsidian KG edges: {len(graph.edges)}")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"- {error}")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings[: args.warning_limit]:
                print(f"- {warning}")
            if len(result.warnings) > args.warning_limit:
                print(f"- ... {len(result.warnings) - args.warning_limit} more warnings")
        if result.errors:
            return 1
        print("Obsidian KG valid")
        return 0

    if args.obsidian_kg_action == "index":
        try:
            paths = write_knowledge_graph_outputs(graph, args.output_dir)
        except Exception as exc:
            print(f"Obsidian KG index failed: {exc}")
            return 1
        print(f"Wrote Obsidian KG nodes CSV: {paths['nodes_csv']}")
        print(f"Wrote Obsidian KG edges CSV: {paths['edges_csv']}")
        print(f"Wrote Obsidian KG JSON: {paths['graph_json']}")
        return 0

    if args.obsidian_kg_action == "audit":
        try:
            audit = audit_knowledge_graph(graph)
            paths = write_knowledge_audit_outputs(audit, args.output_dir)
        except Exception as exc:
            print(f"Obsidian KG audit failed: {exc}")
            return 1
        print(f"Wrote Obsidian KG audit YAML: {paths['audit_yaml']}")
        print(f"Wrote Obsidian KG audit report: {paths['audit_md']}")
        print(f"Status: {audit.get('status')}")
        print(f"Issues: {audit.get('issue_count')}")
        return 0

    if args.obsidian_kg_action == "compile-queue":
        result = validate_knowledge_graph(graph)
        if result.errors:
            print("Obsidian KG validation failed:")
            for error in result.errors:
                print(f"- {error}")
            return 1
        try:
            compiled = compile_setup_journey_queue(
                graph,
                direction=args.direction,
                output_queue=args.output_queue,
                generated_grid_dir=args.generated_grid_dir,
                min_source_cases=args.min_source_cases,
                include_research_grammar=args.include_research_grammar,
                research_grammar_dir=args.research_grammar_dir,
                max_research_families=args.max_research_families,
                max_family_variants=args.max_family_variants,
            )
        except Exception as exc:
            print(f"Obsidian KG queue compile failed: {exc}")
            return 1
        queue = compiled["queue"]
        print(f"Wrote Obsidian candidate queue: {compiled['queue_path']}")
        print(f"Wrote generated grids under: {compiled['grid_dir']}")
        print(f"Hypotheses: {len(queue.get('queue', []))}")
        if result.warnings:
            print(f"Warnings: {len(result.warnings)}")
        return 0

    if args.obsidian_kg_action == "export-evidence":
        try:
            paths = export_evidence_summaries(
                args.session_dir,
                obsidian_dir=args.obsidian_dir,
                include_failed=args.include_failed,
            )
        except Exception as exc:
            print(f"Obsidian KG evidence export failed: {exc}")
            return 1
        print(f"Wrote evidence summary notes: {len(paths)}")
        for path in paths[: args.path_limit]:
            print(f"Wrote: {path}")
        if len(paths) > args.path_limit:
            print(f"... {len(paths) - args.path_limit} more")
        return 0

    print(f"Unknown obsidian-kg action: {args.obsidian_kg_action}")
    return 1


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


def grammar_search_command(args: argparse.Namespace) -> int:
    try:
        universe = load_universe_config(args.config)
        analysis_by_timeframe: dict[str, dict[str, pd.DataFrame]] = {}
        warnings: list[str] = []
        timeframes = [normalize_timeframe(timeframe) for timeframe in args.timeframes]
        for timeframe in timeframes:
            raw_frames, load_warnings = load_universe_ohlcv(
                universe,
                data_dir=args.data_dir,
                timeframe=timeframe,
            )
            warnings.extend(f"{timeframe}: {warning}" for warning in load_warnings)
            if not raw_frames:
                warnings.append(f"{timeframe}: no usable CSV files found in {Path(args.data_dir)}")
                analysis_by_timeframe[timeframe] = {}
                continue
            analysis_frames, _basket, analysis_warnings = build_analysis_frames(universe, raw_frames)
            warnings.extend(f"{timeframe}: {warning}" for warning in analysis_warnings)
            analysis_by_timeframe[timeframe] = analysis_frames

        cooldowns = {timeframe: args.cooldown_bars for timeframe in timeframes} if args.cooldown_bars else None
        summary, records, ranked, family_summary, variants = run_grammar_search(
            analysis_by_timeframe,
            grid_path=args.grid,
            timeframes=timeframes,
            benchmark_name=universe.benchmark.name,
            min_sample_size=args.min_sample_size,
            entry_lag_bars=args.entry_lag_bars,
            cooldown_bars_by_timeframe=cooldowns,
        )
        manifest = {
            "model": GRAMMAR_SEARCH_MODEL,
            "config": args.config,
            "data_dir": args.data_dir,
            "grid": args.grid,
            "timeframes": timeframes,
            "min_sample_size": args.min_sample_size,
            "entry_lag_bars": args.entry_lag_bars,
            "cooldown_bars_by_timeframe": cooldowns
            or {timeframe: timeframe_cooldown(timeframe) for timeframe in timeframes},
            "variant_count": len(variants),
            "record_count": int(len(records)),
        }
    except Exception as exc:
        print(f"Grammar search failed: {exc}")
        return 1

    paths = export_grammar_search_reports(
        summary,
        records,
        ranked,
        family_summary,
        manifest,
        universe,
        warnings=warnings,
        report_dir=args.report_dir,
        obsidian_dir=args.obsidian_dir,
    )
    if args.strict_referee:
        try:
            strict_referee = strict_baseline_referee(
                ranked,
                records,
                analysis_by_timeframe,
                entry_lag_bars=args.entry_lag_bars,
                null_iterations=args.strict_null_iterations,
                random_seed=args.strict_random_seed,
            )
            strict_referee_path = Path(args.report_dir) / "grammar_search_strict_referee.csv"
            strict_referee.to_csv(strict_referee_path, index=False)
            paths["strict_referee_csv"] = strict_referee_path
        except Exception as exc:
            print(f"Grammar search strict referee failed: {exc}")
            return 1
    print(f"Wrote grammar search records CSV: {paths['records_csv']}")
    print(f"Wrote grammar search summary CSV: {paths['summary_csv']}")
    print(f"Wrote grammar search ranked CSV: {paths['ranked_csv']}")
    print(f"Wrote grammar search family/timeframe CSV: {paths['family_timeframe_csv']}")
    print(f"Wrote grammar search family robustness CSV: {paths['family_robustness_csv']}")
    print(f"Wrote grammar search duplicate clusters CSV: {paths['duplicate_clusters_csv']}")
    print(f"Wrote grammar search chart review queue CSV: {paths['chart_review_queue_csv']}")
    print(f"Wrote grammar search time split validation CSV: {paths['time_split_validation_csv']}")
    if "strict_referee_csv" in paths:
        print(f"Wrote grammar search strict referee CSV: {paths['strict_referee_csv']}")
    print(f"Wrote grammar search manifest: {paths['manifest_yaml']}")
    print(f"Wrote grammar search HTML: {paths['summary_html']}")
    print(f"Wrote Obsidian grammar search report: {paths['obsidian']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def grammar_review_packet_command(args: argparse.Namespace) -> int:
    try:
        paths = write_grammar_review_packet(
            args.queue_csv,
            args.output_dir,
            title=args.title,
            max_cases=args.max_cases,
            max_cases_per_bucket=args.max_cases_per_bucket,
        )
    except Exception as exc:
        print(f"Grammar review packet failed: {exc}")
        return 1
    print(f"Wrote grammar review labels CSV: {paths['labels_csv']}")
    print(f"Wrote grammar review packet: {paths['packet_md']}")
    return 0


def grammar_review_gallery_command(args: argparse.Namespace) -> int:
    try:
        labels = pd.read_csv(args.labels_csv)
        if labels.empty:
            timeframes: list[str] = []
        else:
            timeframes = sorted({str(value).strip().lower() for value in labels["timeframe"].dropna() if str(value).strip()})
        universe = load_universe_config(args.config)
        raw_by_timeframe: dict[str, dict[str, pd.DataFrame]] = {}
        analysis_by_timeframe: dict[str, dict[str, pd.DataFrame]] = {}
        warnings: list[str] = []
        for timeframe in timeframes:
            raw_frames, load_warnings = load_universe_ohlcv(
                universe,
                data_dir=args.data_dir,
                timeframe=timeframe,
            )
            warnings.extend(f"{timeframe}: {warning}" for warning in load_warnings)
            analysis_frames, _basket, build_warnings = build_analysis_frames(universe, raw_frames)
            warnings.extend(f"{timeframe}: {warning}" for warning in build_warnings)
            raw_by_timeframe[timeframe] = raw_frames
            analysis_by_timeframe[timeframe] = analysis_frames
        records, paths = render_grammar_review_label_gallery(
            labels,
            raw_by_timeframe,
            analysis_by_timeframe,
            output_dir=args.output_dir,
            lookback_bars=args.lookback_bars,
            forward_bars=args.forward_bars,
            max_images=args.max_images,
        )
    except Exception as exc:
        print(f"Grammar review gallery failed: {exc}")
        return 1
    rendered = int((records["render_status"] == "rendered").sum()) if "render_status" in records else 0
    print(f"Wrote grammar review labels with images CSV: {paths['labels_with_images_csv']}")
    print(f"Wrote grammar review gallery: {paths['gallery_md']}")
    print(f"Rendered images: {rendered}/{len(records)}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def indicator_behavior_search_command(args: argparse.Namespace) -> int:
    try:
        universe = load_universe_config(args.config)
        analysis_by_timeframe: dict[str, dict[str, pd.DataFrame]] = {}
        warnings: list[str] = []
        timeframes = [normalize_timeframe(timeframe) for timeframe in args.timeframes]
        for timeframe in timeframes:
            raw_frames, load_warnings = load_universe_ohlcv(
                universe,
                data_dir=args.data_dir,
                timeframe=timeframe,
            )
            warnings.extend(f"{timeframe}: {warning}" for warning in load_warnings)
            if not raw_frames:
                warnings.append(f"{timeframe}: no usable CSV files found in {Path(args.data_dir)}")
                analysis_by_timeframe[timeframe] = {}
                continue
            analysis_frames, _basket, analysis_warnings = build_analysis_frames(universe, raw_frames)
            warnings.extend(f"{timeframe}: {warning}" for warning in analysis_warnings)
            analysis_by_timeframe[timeframe] = analysis_frames

        cooldowns = {timeframe: args.cooldown_bars for timeframe in timeframes} if args.cooldown_bars else None
        priority = None if args.priority == "all" else args.priority
        summary, records, ranked, family_summary, variants = run_indicator_behavior_search(
            analysis_by_timeframe,
            concept_library_path=args.concept_library,
            primitive_registry_path=args.primitive_registry,
            timeframes=timeframes,
            priority=priority,
            context_windows=args.context_windows,
            benchmark_name=universe.benchmark.name,
            min_sample_size=args.min_sample_size,
            entry_lag_bars=args.entry_lag_bars,
            cooldown_bars_by_timeframe=cooldowns,
        )

        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "records_csv": report_dir / "indicator_behavior_records.csv",
            "summary_csv": report_dir / "indicator_behavior_summary.csv",
            "ranked_csv": report_dir / "indicator_behavior_ranked.csv",
            "family_timeframe_csv": report_dir / "indicator_behavior_family_timeframe.csv",
            "robustness_csv": report_dir / "indicator_behavior_robustness.csv",
            "duplicate_clusters_csv": report_dir / "indicator_behavior_duplicate_clusters.csv",
            "chart_review_queue_csv": report_dir / "indicator_behavior_chart_review_queue.csv",
            "time_split_validation_csv": report_dir / "indicator_behavior_time_split_validation.csv",
            "manifest_json": report_dir / "indicator_behavior_manifest.json",
        }
        summary.to_csv(paths["summary_csv"], index=False)
        records.to_csv(paths["records_csv"], index=False)
        ranked.to_csv(paths["ranked_csv"], index=False)
        family_summary.to_csv(paths["family_timeframe_csv"], index=False)
        family_timeframe_robustness(summary).to_csv(paths["robustness_csv"], index=False)
        duplicate_outcome_clusters(summary).to_csv(paths["duplicate_clusters_csv"], index=False)
        chart_review_queue(ranked, records).to_csv(paths["chart_review_queue_csv"], index=False)
        time_split_validation(ranked, records).to_csv(paths["time_split_validation_csv"], index=False)

        if args.strict_referee:
            strict_referee = strict_baseline_referee(
                ranked,
                records,
                analysis_by_timeframe,
                entry_lag_bars=args.entry_lag_bars,
                null_iterations=args.strict_null_iterations,
                random_seed=args.strict_random_seed,
            )
            paths["strict_referee_csv"] = report_dir / "indicator_behavior_strict_referee.csv"
            strict_referee.to_csv(paths["strict_referee_csv"], index=False)

        manifest = {
            "model": "riskflow_indicator_behavior_search_v0",
            "config": args.config,
            "data_dir": args.data_dir,
            "concept_library": args.concept_library,
            "primitive_registry": args.primitive_registry,
            "timeframes": timeframes,
            "priority": args.priority,
            "context_windows": args.context_windows,
            "min_sample_size": args.min_sample_size,
            "entry_lag_bars": args.entry_lag_bars,
            "cooldown_bars_by_timeframe": cooldowns
            or {timeframe: timeframe_cooldown(timeframe) for timeframe in timeframes},
            "variant_count": len(variants),
            "record_count": int(len(records)),
            "warnings": warnings,
        }
        paths["manifest_json"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"Indicator behavior search failed: {exc}")
        return 1

    print(f"Wrote indicator behavior records CSV: {paths['records_csv']}")
    print(f"Wrote indicator behavior summary CSV: {paths['summary_csv']}")
    print(f"Wrote indicator behavior ranked CSV: {paths['ranked_csv']}")
    print(f"Wrote indicator behavior family/timeframe CSV: {paths['family_timeframe_csv']}")
    print(f"Wrote indicator behavior robustness CSV: {paths['robustness_csv']}")
    print(f"Wrote indicator behavior duplicate clusters CSV: {paths['duplicate_clusters_csv']}")
    print(f"Wrote indicator behavior chart review queue CSV: {paths['chart_review_queue_csv']}")
    print(f"Wrote indicator behavior time split validation CSV: {paths['time_split_validation_csv']}")
    if "strict_referee_csv" in paths:
        print(f"Wrote indicator behavior strict referee CSV: {paths['strict_referee_csv']}")
    print(f"Wrote indicator behavior manifest: {paths['manifest_json']}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
    return 0


def lab_loop_command(args: argparse.Namespace) -> int:
    action = args.lab_loop_action
    if action == "validate-queue":
        try:
            data = load_lab_queue(args.queue)
            max_source_variants = 500 if Path(args.queue).name == "runtime_queue.yaml" else None
            errors = validate_lab_queue(
                data,
                validate_sources=True,
                max_source_variants=max_source_variants,
            )
        except Exception as exc:
            print(f"Lab loop queue validation failed: {exc}")
            return 1
        if errors:
            print("Lab loop queue validation failed:")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"Lab loop queue valid: {args.queue}")
        print(f"Hypotheses: {len(data.get('queue', []))}")
        return 0

    if action == "status":
        print(lab_loop_status(args.state))
        return 0

    if action == "next":
        try:
            queue = load_lab_queue(args.runtime_queue if Path(args.runtime_queue).exists() else args.queue)
            state_path = Path(args.state)
            state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
            hypothesis = select_next_hypothesis(queue, state)
        except Exception as exc:
            print(f"Lab loop next failed: {exc}")
            return 1
        if hypothesis is None:
            print("No runnable lab-loop hypothesis found.")
            return 0
        print(f"Next hypothesis: {hypothesis.get('id')}")
        print(f"Track: {hypothesis.get('track')}")
        print(f"Status: {hypothesis.get('status')}")
        print(f"Priority: {hypothesis.get('priority')}")
        print(f"Source: {hypothesis.get('source', '')}")
        return 0

    if action == "supervise-epoch":
        options = SupervisorOptions(
            state_path=Path(args.state),
            runtime_queue_path=Path(args.runtime_queue),
            concept_scoreboard_path=Path(args.concept_scoreboard),
            evidence_ledger_path=Path(args.evidence_ledger),
            policy_path=Path(args.supervisor_policy),
            epoch_size=args.epoch_size,
            apply=not args.dry_run,
            max_generation=args.max_generation,
            max_same_root_per_epoch=args.max_same_root_per_epoch,
            min_bullish_share=args.min_bullish_share,
            validation_share=args.validation_share,
            min_new_bullish_roots=args.min_new_bullish_roots,
            max_same_setup_class_per_epoch=args.max_same_setup_class_per_epoch,
            weak_family_attempt_limit=args.weak_family_attempt_limit,
            weak_family_cooldown_loops=args.weak_family_cooldown_loops,
            max_non_contract_reseed_source_generation=args.max_non_contract_reseed_source_generation,
            max_primitive_overlap=args.max_primitive_overlap,
            reseed_when_empty=args.reseed_when_empty,
            max_reseed_per_epoch=args.max_reseed_per_epoch,
            max_reseeds_per_root=args.max_reseeds_per_root,
            max_reseed_signature_attempts=args.max_reseed_signature_attempts,
            objective=args.objective,
        )
        try:
            result = supervise_latest_epoch(options)
        except Exception as exc:
            print(f"Lab loop supervise-epoch failed: {exc}")
            return 1
        print(f"Meta-supervisor status: {'applied' if options.apply else 'dry-run'}")
        print(f"Epoch: {result['decision'].get('epoch')}")
        print(f"Next slots: {len(result['decision'].get('next_epoch_slots', []))}")
        print(f"Actions: {len(result.get('actions', []))}")
        print(f"Summary: {result['artifacts'].get('supervisor_summary')}")
        return 0

    if action in {"run", "run-epoch", "run-supervised"}:
        options = LabLoopOptions(
            queue_path=Path(args.queue),
            runtime_queue_path=Path(args.runtime_queue),
            state_path=Path(args.state),
            report_root=Path(args.report_root),
            concept_scoreboard_path=Path(args.concept_scoreboard),
            config_path=Path(args.config),
            data_dir=Path(args.data_dir),
            timeframes=tuple(args.timeframes),
            max_loops=args.max_loops if action == "run" else args.epoch_size,
            max_hours=args.max_hours,
            min_sample_size=args.min_sample_size,
            entry_lag_bars=args.entry_lag_bars,
            cooldown_bars=args.cooldown_bars,
            strict_referee=args.strict_referee,
            strict_null_iterations=args.strict_null_iterations,
            strict_random_seed=args.strict_random_seed,
            checkpoint_interval=args.checkpoint_interval,
            resume=args.resume,
            dry_run=args.dry_run,
            auto_refine=args.auto_refine if action == "run" else False,
            auto_gate_followups=args.auto_gate_followups,
            objective=args.objective,
        )
        try:
            if action == "run-supervised":
                state = run_supervised_epochs(
                    options,
                    SupervisorOptions(
                        state_path=Path(args.state),
                        runtime_queue_path=Path(args.runtime_queue),
                        concept_scoreboard_path=Path(args.concept_scoreboard),
                        evidence_ledger_path=Path(args.evidence_ledger),
                        policy_path=Path(args.supervisor_policy),
                        epoch_size=args.epoch_size,
                        apply=args.apply_supervisor,
                        max_generation=args.max_generation,
                        max_same_root_per_epoch=args.max_same_root_per_epoch,
                        min_bullish_share=args.min_bullish_share,
                        validation_share=args.validation_share,
                        min_new_bullish_roots=args.min_new_bullish_roots,
                        max_same_setup_class_per_epoch=args.max_same_setup_class_per_epoch,
                        weak_family_attempt_limit=args.weak_family_attempt_limit,
                        weak_family_cooldown_loops=args.weak_family_cooldown_loops,
                        max_non_contract_reseed_source_generation=args.max_non_contract_reseed_source_generation,
                        max_primitive_overlap=args.max_primitive_overlap,
                        reseed_when_empty=args.reseed_when_empty,
                        max_reseed_per_epoch=args.max_reseed_per_epoch,
                        max_reseeds_per_root=args.max_reseeds_per_root,
                        max_reseed_signature_attempts=args.max_reseed_signature_attempts,
                        generated_grid_dir=options.generated_grid_dir,
                        objective=args.objective,
                    ),
                    epochs=args.epochs,
                    epoch_size=args.epoch_size,
                )
            else:
                state = run_lab_epoch(options, epoch_size=args.epoch_size) if action == "run-epoch" else run_lab_loop(options)
        except Exception as exc:
            print(f"Lab loop {action} failed: {exc}")
            return 1
        print(f"Lab loop status: {state.get('status')}")
        print(f"Session: {state.get('session_id')}")
        print(f"Completed this run: {state.get('completed_this_run')}")
        print(f"Last completed loop: {state.get('last_completed_loop')}")
        if action in {"run-epoch", "run-supervised"}:
            print(f"Epoch summary: {state.get('last_epoch', {}).get('summary', '')}")
        print(f"Latest status: {Path(args.report_root) / 'latest_status.md'}")
        return 0

    if action == "epoch-summary":
        state_path = Path(args.state)
        if not state_path.exists():
            print(f"No lab-loop state found at {state_path}")
            return 1
        state = json.loads(state_path.read_text(encoding="utf-8"))
        summary_path = Path(state.get("last_epoch", {}).get("summary", ""))
        if not summary_path.exists():
            print("No lab-loop epoch summary found.")
            return 1
        print(summary_path.read_text(encoding="utf-8"))
        return 0

    if action == "concept-scoreboard":
        scoreboard_path = Path(args.concept_scoreboard)
        if not scoreboard_path.exists():
            print(f"No lab-loop concept scoreboard found at {scoreboard_path}")
            return 1
        print(scoreboard_path.read_text(encoding="utf-8"))
        return 0

    if action == "summarize":
        status_path = Path(args.report_root) / "latest_status.md"
        if not status_path.exists():
            print(f"No latest lab-loop status found at {status_path}")
            return 1
        print(status_path.read_text(encoding="utf-8"))
        return 0

    print(f"Unknown lab-loop action: {action}")
    return 1


def lab_director_command(args: argparse.Namespace) -> int:
    action = args.lab_director_action
    options = LabDirectorOptions(
        state_path=Path(args.state),
        runtime_queue_path=Path(args.runtime_queue),
        concept_scoreboard_path=Path(args.concept_scoreboard),
        evidence_ledger_path=Path(args.evidence_ledger),
        report_root=Path(args.report_root),
        director_report_root=Path(args.director_report_root),
        output_queue_path=Path(args.output_queue),
        generated_grid_dir=Path(args.generated_grid_dir),
        objective=args.objective,
        max_new_hypotheses=args.max_new_hypotheses,
        source_root=Path(args.source_root),
        apply=getattr(args, "apply", False),
        apply_to_runtime=getattr(args, "apply_to_runtime", False),
    )
    try:
        if action in {"inspect", "report"}:
            result = run_director_inspect(options)
            print(f"Evidence rows: {result['mart'].get('row_count')}")
            print(f"Beliefs: {result['belief_graph'].get('belief_count')}")
            print(f"Evidence mart: {result['paths']['evidence_mart_yaml']}")
            print(f"Belief graph: {result['paths']['belief_graph']}")
            print(f"Report: {result['paths']['report']}")
            return 0
        if action == "plan-next":
            result = run_director_plan_next(options)
            plan = result["plan"]
            audit = result["audit"]
            print(f"Research mode: {plan.get('research_mode')}")
            print(f"Generated experiments: {len(plan.get('experiments', []))}")
            print(f"Audit passed: {audit.get('passed')}")
            if audit.get("errors"):
                print("Audit errors:")
                for error in audit["errors"]:
                    print(f"- {error}")
            print(f"Plan: {result['paths']['plan']}")
            print(f"Proposed queue: {result['paths']['proposed_queue']}")
            if "applied_queue" in result["paths"]:
                print(f"Applied queue: {result['paths']['applied_queue']}")
            if result.get("runtime_added"):
                print(f"Runtime queue additions: {result['runtime_added']}")
            print(f"Report: {result['paths']['report']}")
            return 0 if audit.get("passed") or not options.apply else 1
        if action == "run":
            remaining = int(args.epochs)
            completed_blocks = 0
            last_state: dict[str, object] = {}
            last_director: dict[str, object] | None = None
            while remaining > 0:
                block_epochs = min(int(args.director_checkpoint_epochs), remaining)
                lab_options = LabLoopOptions(
                    queue_path=Path(args.queue),
                    runtime_queue_path=Path(args.runtime_queue),
                    state_path=Path(args.state),
                    report_root=Path(args.report_root),
                    concept_scoreboard_path=Path(args.concept_scoreboard),
                    config_path=Path(args.config),
                    data_dir=Path(args.data_dir),
                    timeframes=tuple(args.timeframes),
                    max_loops=args.epoch_size,
                    max_hours=args.max_hours,
                    min_sample_size=args.min_sample_size,
                    entry_lag_bars=args.entry_lag_bars,
                    cooldown_bars=args.cooldown_bars,
                    strict_referee=args.strict_referee,
                    strict_null_iterations=args.strict_null_iterations,
                    strict_random_seed=args.strict_random_seed,
                    checkpoint_interval=args.checkpoint_interval,
                    resume=args.resume or completed_blocks > 0,
                    dry_run=args.dry_run,
                    auto_refine=False,
                    auto_gate_followups=args.auto_gate_followups,
                    objective=args.objective,
                )
                supervisor_options = SupervisorOptions(
                    state_path=Path(args.state),
                    runtime_queue_path=Path(args.runtime_queue),
                    concept_scoreboard_path=Path(args.concept_scoreboard),
                    evidence_ledger_path=Path(args.evidence_ledger),
                    policy_path=Path(args.supervisor_policy),
                    epoch_size=args.epoch_size,
                    apply=True,
                    objective=args.objective,
                )
                last_state = run_supervised_epochs(
                    lab_options,
                    supervisor_options,
                    epochs=block_epochs,
                    epoch_size=args.epoch_size,
                )
                completed_blocks += 1
                remaining -= block_epochs
                last_director = run_director_plan_next(options)
                if options.apply and not last_director["audit"].get("passed"):
                    break
                if last_state.get("requires_new_candidate_queue") and not last_director.get("runtime_added"):
                    break
            print(f"Director blocks completed: {completed_blocks}")
            print(f"Lab loop status: {last_state.get('status')}")
            print(f"Last completed loop: {last_state.get('last_completed_loop')}")
            if last_director:
                print(f"Director mode: {last_director['plan'].get('research_mode')}")
                print(f"Director audit passed: {last_director['audit'].get('passed')}")
                print(f"Director report: {last_director['paths']['report']}")
            return 0
    except Exception as exc:
        print(f"Lab director {action} failed: {exc}")
        return 1

    print(f"Unknown lab-director action: {action}")
    return 1


def _lab_director_options_from_args(args: argparse.Namespace) -> LabDirectorOptions:
    return LabDirectorOptions(
        state_path=Path(args.state),
        runtime_queue_path=Path(args.runtime_queue),
        concept_scoreboard_path=Path(args.concept_scoreboard),
        evidence_ledger_path=Path(args.evidence_ledger),
        report_root=Path(args.report_root),
        director_report_root=Path(args.director_report_root),
        output_queue_path=Path(args.output_queue),
        generated_grid_dir=Path(args.generated_grid_dir),
        objective=args.objective,
        max_new_hypotheses=args.max_new_hypotheses,
        source_root=Path(args.source_root),
        apply=getattr(args, "apply", False),
        apply_to_runtime=getattr(args, "apply_to_runtime", False),
    )


def lab_meta_command(args: argparse.Namespace) -> int:
    action = args.lab_meta_action
    director_options = _lab_director_options_from_args(args)
    options = LabMetaOptions(
        director_options=director_options,
        meta_report_root=Path(args.meta_report_root),
        snapshot_path=Path(args.snapshot) if getattr(args, "snapshot", None) else None,
        session_id=getattr(args, "session_id", None),
    )
    try:
        if action in {"inspect", "evaluate"}:
            result = run_lab_meta_inspect(options)
            print(f"Process score: {result['scorecard'].get('overall_process_score')}/100")
            print(f"Failures: {', '.join(result['diagnosis'].get('failure_modes', [])) or 'none'}")
            print(f"Scorecard: {result['paths']['scorecard']}")
            print(f"Report: {result['paths']['report']}")
            return 0
        if action in {"plan", "recommend", "report", "replay"}:
            result = run_lab_meta_plan(options)
            intervention = result.get("intervention") or {}
            audit = result.get("audit") or {}
            print(f"Process score: {result['scorecard'].get('overall_process_score')}/100")
            print(f"Intervention: {intervention.get('intervention_type')}")
            print(f"Meta audit passed: {audit.get('passed')}")
            if audit.get("errors"):
                print("Meta audit errors:")
                for error in audit["errors"]:
                    print(f"- {error}")
            print(f"Scorecard: {result['paths']['scorecard']}")
            print(f"Intervention plan: {result['paths'].get('intervention')}")
            print(f"Report: {result['paths']['report']}")
            return 0 if audit.get("passed") else 1
        if action == "status":
            print(read_latest_meta_status(Path(args.meta_report_root)))
            return 0
    except Exception as exc:
        print(f"Lab meta {action} failed: {exc}")
        return 1
    print(f"Unknown lab-meta action: {action}")
    return 1


def _lab_ops_options_from_args(args: argparse.Namespace) -> LabOpsOptions:
    return LabOpsOptions(
        objective=getattr(args, "objective", "bullish-positive"),
        run_id=getattr(args, "run_id", None),
        queue_path=Path(getattr(args, "queue", DEFAULT_DIRECTOR_QUEUE_PATH)),
        config_path=Path(getattr(args, "config", "configs/meme_universe.yaml")),
        data_dir=Path(getattr(args, "data_dir", "data/raw")),
        timeframes=tuple(getattr(args, "timeframes", ["1d", "12h", "4h", "1h"])),
        max_epochs=getattr(args, "max_epochs", 50),
        epoch_size=getattr(args, "epoch_size", 5),
        director_checkpoint_epochs=getattr(args, "director_checkpoint_epochs", 2),
        max_hours=getattr(args, "max_hours", None),
        min_sample_size=getattr(args, "min_sample_size", 20),
        entry_lag_bars=getattr(args, "entry_lag_bars", 1),
        cooldown_bars=getattr(args, "cooldown_bars", None),
        strict_referee=getattr(args, "strict_referee", True),
        strict_null_iterations=getattr(args, "strict_null_iterations", 300),
        strict_random_seed=getattr(args, "strict_random_seed", 29),
        checkpoint_interval=getattr(args, "checkpoint_interval", 5),
        max_errors=getattr(args, "max_errors", 10),
        max_generated_artifact_mb=getattr(args, "max_generated_artifact_mb", 5000),
        apply=getattr(args, "apply", False),
        resume=getattr(args, "resume", False),
        dry_run=getattr(args, "dry_run", False),
        governed=getattr(args, "governed", False),
        source_root=Path(getattr(args, "source_root", ".")),
        report_root=Path(getattr(args, "ops_report_root", LAB_OPS_REPORT_ROOT)),
        runtime_root=Path(getattr(args, "ops_runtime_root", LAB_OPS_RUNTIME_ROOT)),
        supervisor_policy_path=Path(getattr(args, "supervisor_policy", DEFAULT_SUPERVISOR_POLICY_PATH)),
        max_new_hypotheses=getattr(args, "max_new_hypotheses", 30),
    )


def lab_ops_command(args: argparse.Namespace) -> int:
    action = args.lab_ops_action
    options = _lab_ops_options_from_args(args)
    try:
        if action in {"resume", "status", "report", "stop"} and not args.run_id:
            print(f"lab-ops {action} requires --run-id")
            return 1
        if action == "plan":
            result = run_lab_ops_plan(options)
            print(f"Run id: {result['run_id']}")
            print(f"Manifest: {result['paths']['manifest']}")
            print(f"Status: {result['paths']['status']}")
            return 0
        if action in {"run", "resume"}:
            options = LabOpsOptions(**{**options.__dict__, "resume": action == "resume" or options.resume})
            result = run_lab_ops_run(options)
            print(f"Run id: {result['run_id']}")
            print(f"Status: {result['status']}")
            print(f"Stop reason: {result['stop_reason']}")
            print(f"Completed epochs: {result['completed_epochs']}")
            print(f"Report: {result['paths']['report']}")
            return 0 if result["status"] in {"completed", "stopped"} else 1
        if action == "status":
            result = run_lab_ops_status(options, run_id=args.run_id)
            print(result["status_text"])
            return 0
        if action == "report":
            result = run_lab_ops_report(options, run_id=args.run_id)
            print(f"Report: {result['paths']['report']}")
            return 0
        if action == "stop":
            result = run_lab_ops_stop(options, run_id=args.run_id, reason=args.reason)
            print(f"Stop requested: {result['stop_request']}")
            return 0
    except Exception as exc:
        print(f"Lab ops {action} failed: {exc}")
        return 1
    print(f"Unknown lab-ops action: {action}")
    return 1


def _ceo_options_from_args(args: argparse.Namespace) -> CeoOpsOptions:
    return CeoOpsOptions(
        objective=getattr(args, "objective", "bullish-positive"),
        run_id=getattr(args, "run_id", None),
        lab_run_id=getattr(args, "lab_run_id", None),
        queue_path=Path(getattr(args, "queue", DEFAULT_DIRECTOR_QUEUE_PATH)),
        config_path=Path(getattr(args, "config", "configs/meme_universe.yaml")),
        data_dir=Path(getattr(args, "data_dir", "data/raw")),
        timeframes=tuple(getattr(args, "timeframes", ["1d", "12h", "4h", "1h"])),
        block_epochs=getattr(args, "block_epochs", 2),
        epoch_size=getattr(args, "epoch_size", 5),
        max_hours=getattr(args, "max_hours", None),
        min_sample_size=getattr(args, "min_sample_size", 20),
        entry_lag_bars=getattr(args, "entry_lag_bars", 1),
        cooldown_bars=getattr(args, "cooldown_bars", None),
        strict_referee=getattr(args, "strict_referee", True),
        strict_null_iterations=getattr(args, "strict_null_iterations", 300),
        strict_random_seed=getattr(args, "strict_random_seed", 29),
        checkpoint_interval=getattr(args, "checkpoint_interval", 5),
        apply=getattr(args, "apply", False),
        resume=getattr(args, "resume", False),
        dry_run=getattr(args, "dry_run", False),
        source_root=Path(getattr(args, "source_root", ".")),
        report_root=Path(getattr(args, "ceo_report_root", CEO_REPORT_ROOT)),
        lab_ops_report_root=Path(getattr(args, "ops_report_root", LAB_OPS_REPORT_ROOT)),
        lab_ops_runtime_root=Path(getattr(args, "ops_runtime_root", LAB_OPS_RUNTIME_ROOT)),
        max_new_hypotheses=getattr(args, "max_new_hypotheses", 30),
    )


def _print_ceo_preflight_trace_source(gate: dict[str, Any]) -> None:
    source_status = gate.get("source_status", {}) or {}
    print(f"Trace verdict: {source_status.get('trace_verdict') or 'none'}")
    print(f"Trace score: {source_status.get('trace_score') if source_status.get('trace_score') != '' else 'n/a'}")
    print(f"Trace recommended next action: {source_status.get('trace_recommended_next_action') or 'none'}")
    print(
        "Trace manual data import required: "
        f"{source_status.get('trace_manual_data_import_required') if source_status.get('trace_manual_data_import_required') != '' else 'n/a'}"
    )
    print(f"Trace issues: {source_status.get('trace_issues') or []}")


def _print_ceo_trace_summary(trace: dict[str, Any], *, verdict_key: str = "verdict") -> None:
    print(f"Trace verdict: {trace.get(verdict_key) or 'none'}")
    print(f"Trace score: {trace.get('score') if trace.get('score') != '' else 'n/a'}")
    print(f"Trace recommended next action: {trace.get('recommended_next_action') or 'none'}")
    print(
        "Trace manual data import required: "
        f"{trace.get('manual_data_import_required') if trace.get('manual_data_import_required') != '' else 'n/a'}"
    )
    print(f"Trace issues: {trace.get('issues') or []}")


def ceo_command(args: argparse.Namespace) -> int:
    action = args.ceo_action
    options = _ceo_options_from_args(args)
    try:
        if action in {
            "review",
            "report",
            "heartbeat-status",
            "heartbeat-plan",
            "heartbeat-tick",
            "heartbeat-journal",
            "stop",
            "trace-grade",
            "flight-dashboard",
            "operating-dashboard",
            "portfolio-allocator",
            "mission-score",
            "strategy-capital-dashboard",
            "decision-quality",
            "action-board",
            "operator-step",
            "operator-brief",
            "artifact-coherence",
            "resumption-brief",
            "dispatch-receipt",
            "blocker-stack",
            "incident-register",
            "promotion-proposal",
            "evidence-debt-register",
            "approval-queue",
            "approval-record",
            "executive-kpis",
            "sidecar-evidence-brief",
            "data-gate-brief",
            "role-queue",
            "role-dispatch",
            "role-result",
            "org-progress-score",
            "repair-apply",
            "capability-backlog",
            "fresh-data-preflight",
            "frozen-candidate-validation",
            "frozen-validation-executor",
            "frozen-validation-rerun",
            "fresh-withheld-validation-contract",
            "withheld-split-manifest",
            "fresh-withheld-snapshot-manifest",
            "fresh-withheld-snapshot-declare",
            "fresh-withheld-validation-executor",
            "fresh-control-validation",
            "patch-research-infra",
            "broaden-hypothesis-source",
        } and not args.run_id:
            print(f"ceo {action} requires --run-id")
            return 1
        guarded_direct_actions = {
            "run-block",
            "champion-challenger",
            "promotion-proposal",
            "evidence-debt-register",
            "fresh-control-validation",
            "fresh-data-preflight",
            "frozen-candidate-validation",
            "frozen-validation-executor",
            "frozen-validation-rerun",
            "fresh-withheld-validation-contract",
            "withheld-split-manifest",
            "fresh-withheld-snapshot-manifest",
            "fresh-withheld-snapshot-declare",
            "fresh-withheld-validation-executor",
        }
        if action in guarded_direct_actions:
            preflight_result = run_ceo_preflight_gate(options, enforce_memory_delta=True)
            preflight_gate = preflight_result["preflight_gate"]
            if preflight_gate.get("safe_to_execute") is False:
                print(f"Direct ceo {action} blocked by preflight gate: {preflight_result['paths']['preflight_gate']}")
                print(f"Preflight gate report: {preflight_result['paths']['preflight_gate_report']}")
                print(f"Status: {preflight_gate.get('status')}")
                print(f"Blockers: {[item.get('blocker') for item in preflight_gate.get('blockers', []) or []]}")
                _print_ceo_preflight_trace_source(preflight_gate)
                return 1
            options = replace(options, ceo_context="guarded_direct", ceo_authorized_action=action)
        authority_mutating_actions = {
            "withheld-split-manifest",
            "fresh-withheld-snapshot-manifest",
            "fresh-withheld-snapshot-declare",
        }
        if action in authority_mutating_actions and not getattr(args, "apply", False):
            print(f"ceo {action} requires --apply because it writes validation authority artifacts")
            return 1
        if action == "status":
            result = run_ceo_status(options)
            status = result["company_status"]
            lab_status = status.get("lab_status", {})
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Lab status: {lab_status.get('status')}")
            print(f"Stop reason: {lab_status.get('stop_reason')}")
            open_lanes = status.get("governance", {}).get("open_lanes", [])
            print(f"Open lanes: {', '.join(open_lanes) or 'none'}")
            print(f"True blocker: {status.get('true_blocker')}")
            print(f"Stop requested: {status.get('stop_requested')}")
            operating = status.get("operating_artifacts", {}) or {}
            if operating.get("runtime_authority_override"):
                print(f"Runtime authority override: {operating.get('runtime_authority_override')}")
            print(f"Blocker stack: {operating.get('blocker_stack_status')}")
            print(f"Top blocker: {operating.get('top_blocker') or 'none'}")
            print(f"Operating incidents: {operating.get('operating_incident_count', 0)}")
            print(f"Dispatch receipt: {operating.get('dispatch_receipt_status')}")
            print(f"Safe to dispatch: {operating.get('dispatch_safe_to_dispatch')}")
            print(f"Trace grade: {operating.get('trace_grade_status')}")
            if operating.get("trace_grade_score") != "":
                print(f"Trace score: {operating.get('trace_grade_score')}")
            if operating.get("trace_grade_recommended_next_action"):
                print(f"Trace recommended next action: {operating.get('trace_grade_recommended_next_action')}")
            if operating.get("trace_grade_manual_data_import_required") != "":
                print(f"Trace manual data import required: {operating.get('trace_grade_manual_data_import_required')}")
            if operating.get("trace_grade_issues"):
                print(f"Trace issues: {operating.get('trace_grade_issues')}")
            print(f"Replay: {operating.get('replay_status')}")
            print(f"Replay issues: {operating.get('replay_issue_count')}")
            if operating.get("replay_dispatch_receipt_status"):
                print(f"Replay dispatch receipts: {operating.get('replay_dispatch_receipt_status')}")
            print(f"Operator step: {operating.get('operator_step_status')}")
            if operating.get("operator_step_count") != "":
                print(f"Operator step count: {operating.get('operator_step_count')}")
            print(f"Eval suite: {operating.get('eval_suite_status')}")
            if operating.get("eval_suite_score") != "":
                print(f"Eval score: {operating.get('eval_suite_score')}")
            if operating.get("nine_nine_readiness"):
                print(f"9.9 readiness: {operating.get('nine_nine_readiness')}")
                print(f"9.9 blocking cases: {operating.get('nine_nine_blocking_case_count')}")
                print(f"9.9 advisory cases: {operating.get('nine_nine_advisory_case_count')}")
            print(f"Artifact coherence: {operating.get('artifact_coherence_status')}")
            if operating.get("artifact_coherence_issue_count") != "":
                print(f"Artifact coherence issues: {operating.get('artifact_coherence_issue_count')}")
            if operating.get("artifact_coherence_top_issue_artifact"):
                print(f"Artifact coherence top issue: {operating.get('artifact_coherence_top_issue_artifact')}")
                print(f"Artifact coherence top issue types: {operating.get('artifact_coherence_top_issue_types')}")
                print(f"Artifact coherence top issue severity: {operating.get('artifact_coherence_top_issue_severity') or 'unknown'}")
            print(f"Effective operator status: {operating.get('effective_operator_status')}")
            print(f"Manual gate active: {operating.get('manual_gate_active')}")
            print(f"Effective operator runtime blocked: {operating.get('effective_operator_runtime_blocked')}")
            if operating.get("effective_operator_runtime_block_reason"):
                print(f"Effective operator runtime block reason: {operating.get('effective_operator_runtime_block_reason')}")
            print(f"Resumption status: {operating.get('resumption_status')}")
            print(f"Default handoff command: {operating.get('default_handoff_command')}")
            if operating.get("blocker_next_command"):
                print(f"Next blocker command: {operating.get('blocker_next_command')}")
            print(f"Repair plan: {operating.get('repair_plan_status')}")
            print(f"Runnable repairs: {operating.get('runnable_repair_count', 0)}")
            print(f"Diagnostic refreshes: {operating.get('diagnostic_refresh_count', 0)}")
            print(f"Top repair: {operating.get('top_repair') or 'none'}")
            print(f"Top repair kind: {operating.get('top_repair_kind') or 'none'}")
            if operating.get("repair_next_command"):
                print(f"Repair next command: {operating.get('repair_next_command')}")
            print(f"Repair apply: {operating.get('repair_apply_status')}")
            if operating.get("repair_apply_key"):
                print(f"Repair apply key: {operating.get('repair_apply_key')}")
            if operating.get("repair_apply_executed") != "":
                print(f"Repair apply executed: {operating.get('repair_apply_executed')}")
            if operating.get("repair_apply_closed") != "":
                print(f"Repair apply closed: {operating.get('repair_apply_closed')}")
            print(f"Approval queue: {operating.get('approval_queue_status')}")
            if operating.get("approval_pending_count") != "":
                print(f"Approval pending: {operating.get('approval_pending_count')}")
            if operating.get("approval_top_pending_id"):
                print(f"Approval top id: {operating.get('approval_top_pending_id')}")
                print(f"Approval top kind: {operating.get('approval_top_pending_kind') or 'none'}")
                print(f"Approval top reason: {operating.get('approval_top_pending_reason') or 'none'}")
                print(f"Approval top source: {operating.get('approval_top_pending_source') or 'none'}")
                print(
                    "Approval required user decision: "
                    f"{operating.get('approval_top_pending_required_user_decision') or 'none'}"
                )
                print(f"Approval authority: {operating.get('approval_top_pending_authority') or 'none'}")
                print(f"Approval fingerprint: {operating.get('approval_top_pending_fingerprint') or 'none'}")
                print(f"Approval record command: {operating.get('approval_record_command') or 'none'}")
                print(f"Approval apply command: {operating.get('approval_apply_command') or 'none'}")
            print(f"Approval status: {operating.get('approval_status')}")
            print(f"Action board: {operating.get('action_board_status')}")
            print(f"Action board primary: {operating.get('action_board_primary_action') or 'none'}")
            print(f"Action board kind: {operating.get('action_board_primary_kind') or 'none'}")
            if operating.get("action_board_command"):
                print(f"Action board command: {operating.get('action_board_command')}")
            print(f"Decision quality: {operating.get('decision_quality_status')}")
            if (
                operating.get("decision_quality_status")
                or operating.get("decision_quality_effective_runtime_action")
                or operating.get("decision_quality_runtime_authority")
            ):
                print(f"Decision quality effective runtime action: {operating.get('decision_quality_effective_runtime_action') or 'none'}")
                print(
                    "Decision quality effective runtime command kind: "
                    f"{operating.get('decision_quality_effective_runtime_command_kind') or 'none'}"
                )
                print(
                    "Decision quality effective runtime can execute now: "
                    f"{operating.get('decision_quality_effective_runtime_can_execute_now')}"
                )
                print(f"Decision quality runtime blocked: {operating.get('decision_quality_runtime_blocked')}")
                print(f"Decision quality runtime block reason: {operating.get('decision_quality_runtime_block_reason') or 'none'}")
                print(f"Decision quality selected action: {operating.get('decision_quality_selected_action') or 'none'}")
                print(
                    "Decision quality selected strategic route advisory: "
                    f"{operating.get('decision_quality_selected_strategic_route_advisory') or 'none'}"
                )
                print(f"Decision quality confidence: {operating.get('decision_quality_confidence')}")
                print(f"Decision quality runtime authority: {operating.get('decision_quality_runtime_authority') or 'none'}")
                print(f"Decision quality executable next action: {operating.get('decision_quality_executable_next_action') or 'none'}")
                print(f"Decision quality executable command kind: {operating.get('decision_quality_executable_command_kind') or 'none'}")
                print(
                    "Decision quality runtime authorized strategic route: "
                    f"{operating.get('decision_quality_runtime_authorized_strategic_route') or 'none'}"
                )
                print(f"Decision quality can execute now: {operating.get('decision_quality_executable_can_execute_now')}")
                print(
                    "Decision quality selected action executable now: "
                    f"{operating.get('decision_quality_selected_action_is_executable_now')}"
                )
                print(f"Decision quality selected action blocked by: {operating.get('decision_quality_selected_action_blocked_by') or 'none'}")
            print(f"Operator brief: {operating.get('operator_brief_status')}")
            if operating.get("operator_brief_summary"):
                print(f"Operator brief summary: {operating.get('operator_brief_summary')}")
            if operating.get("operator_brief_next_action"):
                print(f"Operator brief next action: {operating.get('operator_brief_next_action')}")
            print(f"Sidecar evidence brief: {operating.get('sidecar_evidence_brief_status')}")
            if operating.get("sidecar_candidate_count") != "":
                print(f"Sidecar candidates: {operating.get('sidecar_candidate_count')}")
                print(f"Sidecar ready visual review: {operating.get('sidecar_ready_visual_review_count')}")
                print(f"Sidecar fresh-data blocked: {operating.get('sidecar_fresh_data_blocked_count')}")
                print(f"Sidecar review-only frozen specs: {operating.get('sidecar_review_only_frozen_spec_count')}")
                print(f"Sidecar official frozen plan exists: {operating.get('sidecar_official_frozen_plan_exists')}")
                print(f"Sidecar manual data gate active: {operating.get('sidecar_manual_data_gate_active')}")
                print(f"Sidecar safe to run fresh validation: {operating.get('sidecar_safe_to_run_fresh_validation')}")
            if operating.get("sidecar_next_action"):
                print(f"Sidecar next action: {operating.get('sidecar_next_action')}")
            if operating.get("sidecar_evidence_brief_report"):
                print(f"Sidecar evidence report: {operating.get('sidecar_evidence_brief_report')}")
            if operating.get("sidecar_evidence_candidate_table"):
                print(f"Sidecar candidate table: {operating.get('sidecar_evidence_candidate_table')}")
            if operating.get("sidecar_visual_review_handoff_table"):
                print(f"Sidecar visual-review handoff table: {operating.get('sidecar_visual_review_handoff_table')}")
            if operating.get("sidecar_visual_review_coverage"):
                print(f"Sidecar visual-review coverage: {operating.get('sidecar_visual_review_coverage')}")
                print(f"Sidecar visual-review coverage rows: {operating.get('sidecar_visual_review_coverage_row_count')}")
                print(
                    "Sidecar visual-review coverage ready/missing/empty-label: "
                    f"{operating.get('sidecar_visual_review_coverage_ready_count')}/"
                    f"{operating.get('sidecar_visual_review_coverage_missing_count')}/"
                    f"{operating.get('sidecar_visual_review_coverage_empty_label_count')}"
                )
                print(
                    "Sidecar visual-review human-review started/pending: "
                    f"{operating.get('sidecar_visual_review_human_review_started_count')}/"
                    f"{operating.get('sidecar_visual_review_human_review_pending_count')}"
                )
            if operating.get("sidecar_visual_review_coverage_report"):
                print(f"Sidecar visual-review coverage report: {operating.get('sidecar_visual_review_coverage_report')}")
            if operating.get("sidecar_visual_label_worklist"):
                print(f"Sidecar visual-label worklist: {operating.get('sidecar_visual_label_worklist')}")
                print(f"Sidecar visual-label worklist rows: {operating.get('sidecar_visual_label_worklist_row_count')}")
                print(f"Sidecar visual-label worklist candidates: {operating.get('sidecar_visual_label_worklist_candidate_count')}")
                print(
                    "Sidecar visual-label exact/family-timeframe/context rows: "
                    f"{operating.get('sidecar_visual_label_worklist_exact_variant_count')}/"
                    f"{operating.get('sidecar_visual_label_worklist_family_timeframe_count')}/"
                    f"{operating.get('sidecar_visual_label_worklist_family_context_count')}"
                )
            if operating.get("sidecar_visual_label_worklist_report"):
                print(f"Sidecar visual-label worklist report: {operating.get('sidecar_visual_label_worklist_report')}")
            if operating.get("sidecar_visual_label_review_batches"):
                print(f"Sidecar visual-label review batches: {operating.get('sidecar_visual_label_review_batches')}")
                print(f"Sidecar visual-label review batch rows: {operating.get('sidecar_visual_label_review_batch_row_count')}")
                print(f"Sidecar visual-label review batch count: {operating.get('sidecar_visual_label_review_batch_count')}")
                print(
                    "Sidecar visual-label review batch exact/family-timeframe/context rows: "
                    f"{operating.get('sidecar_visual_label_review_batch_exact_variant_count')}/"
                    f"{operating.get('sidecar_visual_label_review_batch_family_timeframe_count')}/"
                    f"{operating.get('sidecar_visual_label_review_batch_family_context_count')}"
                )
            if operating.get("sidecar_visual_label_review_batches_report"):
                print(
                    "Sidecar visual-label review batches report: "
                    f"{operating.get('sidecar_visual_label_review_batches_report')}"
                )
            if operating.get("sidecar_visual_label_progress"):
                print(f"Sidecar visual-label progress: {operating.get('sidecar_visual_label_progress')}")
                print(
                    "Sidecar visual-label progress matched/pending/completed rows: "
                    f"{operating.get('sidecar_visual_label_progress_matched_rows')}/"
                    f"{operating.get('sidecar_visual_label_progress_pending_rows')}/"
                    f"{operating.get('sidecar_visual_label_progress_completed_rows')}"
                )
                print(
                    "Sidecar visual-label progress not-started/incomplete/complete candidates: "
                    f"{operating.get('sidecar_visual_label_progress_not_started_candidates')}/"
                    f"{operating.get('sidecar_visual_label_progress_incomplete_candidates')}/"
                    f"{operating.get('sidecar_visual_label_progress_complete_candidates')}"
                )
                print(
                    "Sidecar visual-label progress next batch: "
                    f"{operating.get('sidecar_visual_label_progress_next_batch_id') or 'none'}"
                )
            if operating.get("sidecar_visual_label_progress_report"):
                print(
                    "Sidecar visual-label progress report: "
                    f"{operating.get('sidecar_visual_label_progress_report')}"
                )
            if operating.get("sidecar_visual_label_next_batch"):
                print(f"Sidecar visual-label next batch: {operating.get('sidecar_visual_label_next_batch')}")
                print(f"Sidecar visual-label next batch id: {operating.get('sidecar_visual_label_next_batch_id')}")
                print(f"Sidecar visual-label next batch rows: {operating.get('sidecar_visual_label_next_batch_row_count')}")
                print(
                    "Sidecar visual-label next batch exact/family-timeframe/context rows: "
                    f"{operating.get('sidecar_visual_label_next_batch_exact_variant_count')}/"
                    f"{operating.get('sidecar_visual_label_next_batch_family_timeframe_count')}/"
                    f"{operating.get('sidecar_visual_label_next_batch_family_context_count')}"
                )
            if operating.get("sidecar_visual_label_next_batch_report"):
                print(
                    "Sidecar visual-label next batch report: "
                    f"{operating.get('sidecar_visual_label_next_batch_report')}"
                )
            if operating.get("sidecar_visual_label_next_batch_gallery"):
                print(
                    "Sidecar visual-label next batch gallery: "
                    f"{operating.get('sidecar_visual_label_next_batch_gallery')}"
                )
            if operating.get("sidecar_visual_label_rubric"):
                print(f"Sidecar visual-label rubric: {operating.get('sidecar_visual_label_rubric')}")
                print(f"Sidecar visual-label rubric status: {operating.get('sidecar_visual_label_rubric_status')}")
                print(f"Sidecar visual-label rubric batch: {operating.get('sidecar_visual_label_rubric_batch_id')}")
                print(
                    "Sidecar visual-label rubric required fields: "
                    f"{operating.get('sidecar_visual_label_rubric_required_fields') or 'none'}"
                )
            if operating.get("sidecar_visual_label_rubric_report"):
                print(f"Sidecar visual-label rubric report: {operating.get('sidecar_visual_label_rubric_report')}")
            if operating.get("sidecar_visual_label_entry_sheet"):
                print(f"Sidecar visual-label entry sheet: {operating.get('sidecar_visual_label_entry_sheet')}")
                print(f"Sidecar visual-label entry sheet batch: {operating.get('sidecar_visual_label_entry_sheet_batch_id')}")
                print(f"Sidecar visual-label entry sheet rows: {operating.get('sidecar_visual_label_entry_sheet_row_count')}")
                print(
                    "Sidecar visual-label entry sheet required fields: "
                    f"{operating.get('sidecar_visual_label_entry_sheet_required_fields') or 'none'}"
                )
                print(
                    "Sidecar visual-label entry sheet missing required cells: "
                    f"{operating.get('sidecar_visual_label_entry_sheet_missing_required_cells')}"
                )
                print(
                    "Sidecar visual-label entry sheet source-file/source-row/image gaps: "
                    f"{operating.get('sidecar_visual_label_entry_sheet_missing_source_files')}/"
                    f"{operating.get('sidecar_visual_label_entry_sheet_missing_source_rows')}/"
                    f"{operating.get('sidecar_visual_label_entry_sheet_missing_images')}"
                )
            if operating.get("sidecar_visual_label_entry_sheet_report"):
                print(
                    "Sidecar visual-label entry sheet report: "
                    f"{operating.get('sidecar_visual_label_entry_sheet_report')}"
                )
            if operating.get("sidecar_visual_label_source_update_manifest"):
                print(
                    "Sidecar visual-label source update manifest: "
                    f"{operating.get('sidecar_visual_label_source_update_manifest')}"
                )
                print(
                    "Sidecar visual-label source update rows/pending/cells: "
                    f"{operating.get('sidecar_visual_label_source_update_manifest_row_count')}/"
                    f"{operating.get('sidecar_visual_label_source_update_manifest_pending_update_rows')}/"
                    f"{operating.get('sidecar_visual_label_source_update_manifest_required_update_cells')}"
                )
                print(
                    "Sidecar visual-label source update source-file/source-row/image gaps: "
                    f"{operating.get('sidecar_visual_label_source_update_manifest_missing_source_files')}/"
                    f"{operating.get('sidecar_visual_label_source_update_manifest_missing_source_rows')}/"
                    f"{operating.get('sidecar_visual_label_source_update_manifest_missing_images')}"
                )
            if operating.get("sidecar_visual_label_source_update_manifest_report"):
                print(
                    "Sidecar visual-label source update manifest report: "
                    f"{operating.get('sidecar_visual_label_source_update_manifest_report')}"
                )
            if operating.get("sidecar_visual_label_source_patch_plan"):
                print(
                    "Sidecar visual-label source patch plan: "
                    f"{operating.get('sidecar_visual_label_source_patch_plan')}"
                )
                print(
                    "Sidecar visual-label source patch cells/pending/blocked: "
                    f"{operating.get('sidecar_visual_label_source_patch_plan_cell_count')}/"
                    f"{operating.get('sidecar_visual_label_source_patch_plan_pending_cells')}/"
                    f"{operating.get('sidecar_visual_label_source_patch_plan_blocked_cells')}"
                )
                print(
                    "Sidecar visual-label source patch files/rows: "
                    f"{operating.get('sidecar_visual_label_source_patch_plan_source_files')}/"
                    f"{operating.get('sidecar_visual_label_source_patch_plan_source_rows')}"
                )
            if operating.get("sidecar_visual_label_source_patch_plan_report"):
                print(
                    "Sidecar visual-label source patch plan report: "
                    f"{operating.get('sidecar_visual_label_source_patch_plan_report')}"
                )
            if operating.get("sidecar_visual_label_completion_audit"):
                print(
                    "Sidecar visual-label completion audit: "
                    f"{operating.get('sidecar_visual_label_completion_audit')}"
                )
                print(
                    "Sidecar visual-label completion audit status: "
                    f"{operating.get('sidecar_visual_label_completion_audit_status')}"
                )
                print(
                    "Sidecar visual-label completion audit rows/completed/missing/invalid: "
                    f"{operating.get('sidecar_visual_label_completion_audit_rows')}/"
                    f"{operating.get('sidecar_visual_label_completion_audit_completed_rows')}/"
                    f"{operating.get('sidecar_visual_label_completion_audit_missing_rows')}/"
                    f"{operating.get('sidecar_visual_label_completion_audit_invalid_rows')}"
                )
            if operating.get("sidecar_visual_label_completion_audit_report"):
                print(
                    "Sidecar visual-label completion audit report: "
                    f"{operating.get('sidecar_visual_label_completion_audit_report')}"
                )
            if operating.get("sidecar_visual_review_top_candidate"):
                print(f"Sidecar visual-review top candidate: {operating.get('sidecar_visual_review_top_candidate')}")
                print(f"Sidecar visual-review top role: {operating.get('sidecar_visual_review_top_product_role') or 'none'}")
                print(f"Sidecar visual-review top focus: {operating.get('sidecar_visual_review_top_focus') or 'none'}")
                print(f"Sidecar visual-review top priority: {operating.get('sidecar_visual_review_top_priority')}")
                if operating.get("sidecar_visual_review_top_question"):
                    print(f"Sidecar visual-review top question: {operating.get('sidecar_visual_review_top_question')}")
                if operating.get("sidecar_visual_review_top_gallery"):
                    print(f"Sidecar visual-review top gallery: {operating.get('sidecar_visual_review_top_gallery')}")
                if operating.get("sidecar_visual_review_top_labels_with_images"):
                    print(f"Sidecar visual-review top labels: {operating.get('sidecar_visual_review_top_labels_with_images')}")
            if operating.get("sidecar_champion_challenger_evidence_table"):
                print(
                    "Sidecar champion/challenger evidence table: "
                    f"{operating.get('sidecar_champion_challenger_evidence_table')}"
                )
            if operating.get("sidecar_champion_challenger_quality_audit"):
                print(
                    "Sidecar champion/challenger quality audit: "
                    f"{operating.get('sidecar_champion_challenger_quality_audit')}"
                )
                print(
                    "Sidecar champion/challenger quality audit report: "
                    f"{operating.get('sidecar_champion_challenger_quality_audit_report')}"
                )
                print(
                    "Sidecar champion/challenger quality status: "
                    f"{operating.get('sidecar_champion_challenger_quality_status')}"
                )
                print(
                    "Sidecar champion/challenger quality issues: "
                    f"{operating.get('sidecar_champion_challenger_quality_issue_count')}"
                )
                print(
                    "Sidecar champion/challenger quality hard/advisory issues: "
                    f"{operating.get('sidecar_champion_challenger_quality_hard_issue_count')}/"
                    f"{operating.get('sidecar_champion_challenger_quality_advisory_issue_count')}"
                )
                if operating.get("sidecar_champion_challenger_quality_advisory_issue_summary"):
                    print(
                        "Sidecar champion/challenger quality advisory summary: "
                        f"{operating.get('sidecar_champion_challenger_quality_advisory_issue_summary')}"
                    )
                if operating.get("sidecar_champion_challenger_quality_hard_issue_summary"):
                    print(
                        "Sidecar champion/challenger quality hard summary: "
                        f"{operating.get('sidecar_champion_challenger_quality_hard_issue_summary')}"
                    )
            if operating.get("sidecar_quality_remediation_plan"):
                print(f"Sidecar quality remediation plan: {operating.get('sidecar_quality_remediation_plan')}")
            if operating.get("sidecar_quality_remediation_plan_report"):
                print(
                    "Sidecar quality remediation plan report: "
                    f"{operating.get('sidecar_quality_remediation_plan_report')}"
                )
            if operating.get("sidecar_quality_remediation_plan_status"):
                print(
                    "Sidecar quality remediation plan status: "
                    f"{operating.get('sidecar_quality_remediation_plan_status')}"
                )
                print(
                    "Sidecar quality remediation plan required action: "
                    f"{operating.get('sidecar_quality_remediation_plan_current_required_action') or 'none'}"
                )
                print(
                    "Sidecar quality remediation autonomous/human/diversity/archive: "
                    f"{operating.get('sidecar_quality_remediation_plan_autonomous_clearable_now_count')}/"
                    f"{operating.get('sidecar_quality_remediation_plan_human_visual_remediation_count')}/"
                    f"{operating.get('sidecar_quality_remediation_plan_diversity_control_remediation_count')}/"
                    f"{operating.get('sidecar_quality_remediation_plan_archive_only_count')}"
                )
            if operating.get("sidecar_evidence_gap_matrix"):
                print(f"Sidecar evidence gap matrix: {operating.get('sidecar_evidence_gap_matrix')}")
            if operating.get("sidecar_candidate_readiness_summary"):
                print(f"Sidecar candidate readiness summary: {operating.get('sidecar_candidate_readiness_summary')}")
            if operating.get("sidecar_candidate_readiness_summary_report"):
                print(
                    "Sidecar candidate readiness summary report: "
                    f"{operating.get('sidecar_candidate_readiness_summary_report')}"
                )
            if operating.get("sidecar_validation_queue"):
                print(f"Sidecar validation queue: {operating.get('sidecar_validation_queue')}")
            if operating.get("sidecar_validation_queue_report"):
                print(f"Sidecar validation queue report: {operating.get('sidecar_validation_queue_report')}")
            if operating.get("sidecar_champion_challenger_validation_design"):
                print(
                    "Sidecar champion/challenger validation design: "
                    f"{operating.get('sidecar_champion_challenger_validation_design')}"
                )
            if operating.get("sidecar_champion_challenger_validation_design_report"):
                print(
                    "Sidecar champion/challenger validation design report: "
                    f"{operating.get('sidecar_champion_challenger_validation_design_report')}"
                )
            if operating.get("sidecar_data_gate_unlock_matrix"):
                print(f"Sidecar data-gate unlock matrix: {operating.get('sidecar_data_gate_unlock_matrix')}")
            if operating.get("sidecar_data_gate_unlock_matrix_yaml"):
                print(f"Sidecar data-gate unlock matrix YAML: {operating.get('sidecar_data_gate_unlock_matrix_yaml')}")
            if operating.get("sidecar_data_gate_unlock_matrix_report"):
                print(f"Sidecar data-gate unlock matrix report: {operating.get('sidecar_data_gate_unlock_matrix_report')}")
            if operating.get("sidecar_evidence_consistency_audit"):
                print(f"Sidecar evidence consistency audit: {operating.get('sidecar_evidence_consistency_audit')}")
            if operating.get("sidecar_evidence_consistency_audit_report"):
                print(
                    "Sidecar evidence consistency audit report: "
                    f"{operating.get('sidecar_evidence_consistency_audit_report')}"
                )
            if operating.get("sidecar_evidence_consistency_audit_status"):
                print(
                    "Sidecar evidence consistency audit status: "
                    f"{operating.get('sidecar_evidence_consistency_audit_status')}"
                )
                print(
                    "Sidecar evidence consistency audit checks/issues: "
                    f"{operating.get('sidecar_evidence_consistency_audit_check_count')}/"
                    f"{operating.get('sidecar_evidence_consistency_audit_issue_count')}"
                )
            if operating.get("sidecar_evidence_packet_index"):
                print(f"Sidecar evidence packet index: {operating.get('sidecar_evidence_packet_index')}")
            if operating.get("sidecar_evidence_packet_index_report"):
                print(f"Sidecar evidence packet index report: {operating.get('sidecar_evidence_packet_index_report')}")
            if operating.get("sidecar_candidate_decision_cards"):
                print(f"Sidecar candidate decision cards: {operating.get('sidecar_candidate_decision_cards')}")
            if operating.get("sidecar_current_decision_packet"):
                print(f"Sidecar current decision packet: {operating.get('sidecar_current_decision_packet')}")
            if operating.get("sidecar_current_decision_packet_report"):
                print(
                    "Sidecar current decision packet report: "
                    f"{operating.get('sidecar_current_decision_packet_report')}"
                )
            if operating.get("sidecar_current_decision_packet_status"):
                print(
                    "Sidecar current decision packet status: "
                    f"{operating.get('sidecar_current_decision_packet_status')}"
                )
                print(
                    "Sidecar current decision packet decision: "
                    f"{operating.get('sidecar_current_decision_packet_decision') or 'none'}"
                )
                if operating.get("sidecar_current_decision_packet_quality_remediation_status"):
                    print(
                        "Sidecar current decision packet quality remediation status: "
                        f"{operating.get('sidecar_current_decision_packet_quality_remediation_status')}"
                    )
                    print(
                        "Sidecar current decision packet quality remediation required action: "
                        f"{operating.get('sidecar_current_decision_packet_quality_remediation_required_action')}"
                    )
                    print(
                        "Sidecar current decision packet quality remediation autonomous/human/diversity/archive: "
                        f"{operating.get('sidecar_current_decision_packet_quality_remediation_autonomous_clearable_now_count')}/"
                        f"{operating.get('sidecar_current_decision_packet_quality_remediation_human_visual_count')}/"
                        f"{operating.get('sidecar_current_decision_packet_quality_remediation_diversity_control_count')}/"
                        f"{operating.get('sidecar_current_decision_packet_quality_remediation_archive_only_count')}"
                    )
            if operating.get("sidecar_shadow_guardrail_report"):
                print(f"Sidecar shadow guardrail: {operating.get('sidecar_shadow_guardrail_status')}")
                print(f"Sidecar shadow guardrail violations: {operating.get('sidecar_shadow_guardrail_violation_count')}")
                print(f"Sidecar shadow guardrail report: {operating.get('sidecar_shadow_guardrail_report')}")
            if operating.get("sidecar_evidence_source_manifest"):
                print(f"Sidecar evidence source manifest: {operating.get('sidecar_evidence_source_manifest')}")
            if operating.get("sidecar_evidence_source_health"):
                print(f"Sidecar evidence source health: {operating.get('sidecar_evidence_source_health')}")
                print(f"Sidecar evidence source health YAML: {operating.get('sidecar_evidence_source_health_yaml')}")
                print(f"Sidecar evidence source health report: {operating.get('sidecar_evidence_source_health_report')}")
                print(f"Sidecar evidence source health status: {operating.get('sidecar_evidence_source_health_status')}")
                print(f"Sidecar evidence source health issues: {operating.get('sidecar_evidence_source_health_issue_count')}")
                print(
                    "Sidecar evidence source health missing required refs: "
                    f"{operating.get('sidecar_evidence_source_health_missing_required')}"
                )
                print(
                    "Sidecar evidence source health wrong-type required refs: "
                    f"{operating.get('sidecar_evidence_source_health_wrong_type_required')}"
                )
            if operating.get("sidecar_evidence_source_fingerprints"):
                print(
                    "Sidecar evidence source fingerprints: "
                    f"{operating.get('sidecar_evidence_source_fingerprints')}"
                )
                print(
                    "Sidecar evidence source fingerprints YAML: "
                    f"{operating.get('sidecar_evidence_source_fingerprints_yaml')}"
                )
                print(
                    "Sidecar evidence source fingerprints report: "
                    f"{operating.get('sidecar_evidence_source_fingerprints_report')}"
                )
                print(
                    "Sidecar evidence source fingerprints status: "
                    f"{operating.get('sidecar_evidence_source_fingerprints_status')}"
                )
                print(
                    "Sidecar evidence source fingerprints issues: "
                    f"{operating.get('sidecar_evidence_source_fingerprints_issue_count')}"
                )
                print(
                    "Sidecar evidence source fingerprints files: "
                    f"{operating.get('sidecar_evidence_source_fingerprints_fingerprinted_file_count')}/"
                    f"{operating.get('sidecar_evidence_source_fingerprints_file_count')}"
                )
                print(
                    "Sidecar evidence source fingerprints CSV row counts: "
                    f"{operating.get('sidecar_evidence_source_fingerprints_csv_row_count_recorded_count')}/"
                    f"{operating.get('sidecar_evidence_source_fingerprints_csv_count')}"
                )
            if operating.get("sidecar_candidate_learning_ledger"):
                print(f"Sidecar candidate learning ledger: {operating.get('sidecar_candidate_learning_ledger')}")
                print(
                    "Sidecar candidate learning ledger YAML: "
                    f"{operating.get('sidecar_candidate_learning_ledger_yaml')}"
                )
                print(
                    "Sidecar candidate learning ledger report: "
                    f"{operating.get('sidecar_candidate_learning_ledger_report')}"
                )
                print(f"Sidecar candidate learning ledger status: {operating.get('sidecar_candidate_learning_ledger_status')}")
                print(
                    "Sidecar candidate learning ledger lead/control/archive/review/blocked: "
                    f"{operating.get('sidecar_candidate_learning_ledger_lead_count')}/"
                    f"{operating.get('sidecar_candidate_learning_ledger_diversity_control_count')}/"
                    f"{operating.get('sidecar_candidate_learning_ledger_archive_count')}/"
                    f"{operating.get('sidecar_candidate_learning_ledger_review_only_count')}/"
                    f"{operating.get('sidecar_candidate_learning_ledger_quality_blocked_count')}"
                )
                if operating.get("sidecar_learning_lead_candidate"):
                    print(f"Sidecar learning lead candidate: {operating.get('sidecar_learning_lead_candidate')}")
                    print(f"Sidecar learning lead next required: {operating.get('sidecar_learning_lead_next_required_action') or 'none'}")
                    print(f"Sidecar learning lead authority: {operating.get('sidecar_learning_lead_validation_authority') or 'none'}")
                if operating.get("sidecar_learning_control_candidate"):
                    print(f"Sidecar learning control candidate: {operating.get('sidecar_learning_control_candidate')}")
                    print(f"Sidecar learning control reason: {operating.get('sidecar_learning_control_reason') or 'none'}")
                    print(f"Sidecar learning control next allowed: {operating.get('sidecar_learning_control_next_allowed_action') or 'none'}")
                if operating.get("sidecar_learning_archive_candidate"):
                    print(f"Sidecar learning archive candidate: {operating.get('sidecar_learning_archive_candidate')}")
                    print(f"Sidecar learning archive reason: {operating.get('sidecar_learning_archive_reason') or 'none'}")
                    print(f"Sidecar learning archive next allowed: {operating.get('sidecar_learning_archive_next_allowed_action') or 'none'}")
            if operating.get("sidecar_post_data_validation_playbook"):
                print(
                    "Sidecar post-data validation playbook: "
                    f"{operating.get('sidecar_post_data_validation_playbook')}"
                )
                print(
                    "Sidecar post-data playbook status: "
                    f"{operating.get('sidecar_post_data_validation_playbook_status') or 'none'}"
                )
                print(
                    "Sidecar post-data required action: "
                    f"{operating.get('sidecar_post_data_validation_playbook_current_required_action') or 'none'}"
                )
                print(
                    "Sidecar post-data visual-label status/gate: "
                    f"{operating.get('sidecar_post_data_validation_playbook_visual_label_completion_status') or 'none'}/"
                    f"{operating.get('sidecar_post_data_validation_playbook_visual_label_gate_passed')}"
                )
                print(
                    "Sidecar post-data blockers: "
                    f"{operating.get('sidecar_post_data_validation_playbook_pre_validation_blockers') or 'none'}"
                )
                print(
                    "Sidecar post-data can-execute candidates: "
                    f"{operating.get('sidecar_post_data_validation_playbook_can_execute_count')}"
                )
            if operating.get("sidecar_post_data_validation_playbook_report"):
                print(
                    "Sidecar post-data validation playbook report: "
                    f"{operating.get('sidecar_post_data_validation_playbook_report')}"
                )
            if operating.get("sidecar_current_handoff"):
                print(f"Sidecar current handoff: {operating.get('sidecar_current_handoff')}")
            if operating.get("sidecar_current_handoff_report"):
                print(f"Sidecar current handoff report: {operating.get('sidecar_current_handoff_report')}")
            if operating.get("sidecar_candidate_decision_matrix"):
                print(f"Sidecar candidate decision matrix: {operating.get('sidecar_candidate_decision_matrix')}")
                print(
                    "Sidecar candidate decision matrix rows: "
                    f"{operating.get('sidecar_candidate_decision_matrix_row_count')}"
                )
            if operating.get("sidecar_candidate_decision_matrix_report"):
                print(
                    "Sidecar candidate decision matrix report: "
                    f"{operating.get('sidecar_candidate_decision_matrix_report')}"
                )
            if operating.get("sidecar_frozen_spec_review_table"):
                print(f"Sidecar frozen-spec review table: {operating.get('sidecar_frozen_spec_review_table')}")
            if operating.get("evidence_debt_register_status"):
                print(f"Evidence debt register: {operating.get('evidence_debt_register_status')}")
                print(f"Evidence debt count: {operating.get('evidence_debt_count')}")
                print(
                    "Evidence debt candidate/global/archive: "
                    f"{operating.get('evidence_debt_candidate_count')}/"
                    f"{operating.get('evidence_debt_global_count')}/"
                    f"{operating.get('evidence_debt_archived_candidate_count')}"
                )
                if operating.get("evidence_debt_next_action"):
                    print(f"Evidence debt next action: {operating.get('evidence_debt_next_action')}")
                if operating.get("evidence_debt_current_runtime_handoff_action"):
                    print(
                        "Evidence debt current handoff: "
                        f"{operating.get('evidence_debt_current_runtime_handoff_action')}"
                    )
                    print(
                        "Evidence debt handoff status: "
                        f"{operating.get('evidence_debt_current_runtime_handoff_status')}"
                    )
                    print(
                        "Evidence debt strategic blocked by handoff: "
                        f"{operating.get('evidence_debt_strategic_blocked_by_current_handoff')}"
                    )
                if operating.get("evidence_debt_register_report"):
                    print(f"Evidence debt report: {operating.get('evidence_debt_register_report')}")
            print(f"Data gate brief: {operating.get('data_gate_brief_status')}")
            if operating.get("data_gate_preflight_status"):
                print(f"Data gate preflight: {operating.get('data_gate_preflight_status')}")
                print(f"Data gate safe fresh validation: {operating.get('data_gate_safe_to_run_fresh_validation')}")
                print(f"Data gate manual gate active: {operating.get('data_gate_manual_gate_active')}")
                print(f"Data gate required timeframes: {operating.get('data_gate_required_timeframes') or []}")
                print(f"Data gate CSV requirements: {operating.get('data_gate_csv_requirement_count')}")
                print(f"Data gate blocked candidates: {operating.get('data_gate_blocked_candidate_count')}")
                print(f"Data gate candidate unlocks: {operating.get('data_gate_candidate_unlock_count')}")
                print(f"Data gate role blockers: {operating.get('data_gate_role_blocker_count')}")
            if operating.get("data_gate_next_action"):
                print(f"Data gate next action: {operating.get('data_gate_next_action')}")
            if operating.get("data_gate_next_verification_command"):
                print(f"Data gate next verification: {operating.get('data_gate_next_verification_command')}")
            if operating.get("data_gate_brief_report"):
                print(f"Data gate report: {operating.get('data_gate_brief_report')}")
            if operating.get("data_gate_candidate_unlocks"):
                print(f"Data gate candidate unlock table: {operating.get('data_gate_candidate_unlocks')}")
            if operating.get("data_gate_import_plan"):
                print(f"Data gate import plan: {operating.get('data_gate_import_plan')}")
            if operating.get("data_gate_import_plan_report"):
                print(f"Data gate import plan report: {operating.get('data_gate_import_plan_report')}")
            if operating.get("data_gate_import_batches"):
                print(f"Data gate import batch table: {operating.get('data_gate_import_batches')}")
            if operating.get("data_gate_import_checklist"):
                print(f"Data gate import checklist: {operating.get('data_gate_import_checklist')}")
                print(
                    "Data gate import checklist rows/pending/ready: "
                    f"{operating.get('data_gate_import_checklist_row_count')}/"
                    f"{operating.get('data_gate_import_checklist_pending_imports')}/"
                    f"{operating.get('data_gate_import_checklist_complete_ready')}"
                )
                print(
                    "Data gate import checklist missing/stale: "
                    f"{operating.get('data_gate_import_checklist_missing_count')}/"
                    f"{operating.get('data_gate_import_checklist_stale_count')}"
                )
            if operating.get("data_gate_import_checklist_report"):
                print(f"Data gate import checklist report: {operating.get('data_gate_import_checklist_report')}")
            if operating.get("data_gate_handoff_audit"):
                print(f"Data gate handoff audit: {operating.get('data_gate_handoff_audit')}")
                print(f"Data gate handoff audit status: {operating.get('data_gate_handoff_audit_status')}")
                print(
                    "Data gate handoff audit checks/issues: "
                    f"{operating.get('data_gate_handoff_audit_check_count')}/"
                    f"{operating.get('data_gate_handoff_audit_issue_count')}"
                )
            if operating.get("data_gate_handoff_audit_report"):
                print(f"Data gate handoff audit report: {operating.get('data_gate_handoff_audit_report')}")
            if operating.get("data_gate_symbol_matrix"):
                print(f"Data gate symbol matrix: {operating.get('data_gate_symbol_matrix')}")
                print(f"Data gate symbol matrix rows: {operating.get('data_gate_symbol_matrix_row_count')}")
            if operating.get("data_gate_symbol_matrix_report"):
                print(f"Data gate symbol matrix report: {operating.get('data_gate_symbol_matrix_report')}")
            print(f"Role queue: {operating.get('role_queue_status')}")
            if operating.get("role_pending_task_count") != "":
                print(f"Role pending: {operating.get('role_pending_task_count')}")
                print(f"Role pending manual: {operating.get('role_pending_manual_task_count')}")
                print(f"Role pending autonomous: {operating.get('role_pending_autonomous_task_count')}")
                print(f"Role completed: {operating.get('role_completed_task_count')}")
                print(f"Role blocked: {operating.get('role_blocked_task_count')}")
            if operating.get("role_top_pending_task_id"):
                print(f"Role top pending task: {operating.get('role_top_pending_task_id')}")
                print(f"Role top pending role: {operating.get('role_top_pending_role_id')}")
                print(f"Role top pending packet: {operating.get('role_top_pending_packet_path')}")
                print(f"Role top pending result mode: {operating.get('role_top_pending_result_resolution_mode')}")
                print(f"Role top pending requires manual gate: {operating.get('role_top_pending_requires_manual_gate')}")
                print(f"Role top pending closure command: {operating.get('role_top_pending_closure_command')}")
                print(f"Role top autonomous task: {operating.get('role_top_autonomous_pending_task_id') or 'none'}")
                print(f"Role top autonomous packet: {operating.get('role_top_autonomous_pending_packet_path') or 'none'}")
                print(f"Role top autonomous result command: {operating.get('role_top_autonomous_next_result_command') or 'none'}")
                print(f"Role next result command: {operating.get('role_next_result_command')}")
            if operating.get("role_top_blocked_task_id"):
                print(f"Role top blocked task: {operating.get('role_top_blocked_task_id') or 'none'}")
                print(f"Role top blocked role: {operating.get('role_top_blocked_role_id') or 'none'}")
                print(f"Role top blocked packet: {operating.get('role_top_blocked_packet_path') or 'none'}")
                print(f"Role top blocked result mode: {operating.get('role_top_blocked_result_resolution_mode') or 'none'}")
                print(f"Role top blocked validation: {operating.get('role_top_blocked_validation_status') or 'none'}")
                print(f"Role top blocked closure command: {operating.get('role_top_blocked_closure_command') or 'none'}")
                print(f"Role top blocked review status: {operating.get('role_top_blocked_review_status') or 'none'}")
                print(f"Role top blocked result path: {operating.get('role_top_blocked_result_path') or 'none'}")
                print(f"Role top blocked next action: {operating.get('role_top_blocked_next_action') or 'none'}")
                print(f"Role top blocked finding: {operating.get('role_top_blocked_finding') or 'none'}")
            print(f"Role result validation: {operating.get('role_result_validation_status')}")
            if operating.get("role_result_validation_task"):
                print(f"Role result validation task: {operating.get('role_result_validation_task')}")
            if operating.get("role_result_validation_issues"):
                print(f"Role result validation issues: {operating.get('role_result_validation_issues')}")
            if getattr(args, "show_lab_status", False):
                print(run_ceo_lab_status_text(options))
            return 0
        if action == "plan":
            result = run_ceo_plan(options)
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Plan: {result['paths']['plan']}")
            print(f"Decision: {result['plan']['recommended_decision']['decision']}")
            return 0
        if action == "run-block":
            result = run_ceo_run_block(options)
            review = result["review"]
            lab_result = result["lab_result"]
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Lab status: {lab_result['status']}")
            print(f"Lab stop reason: {lab_result['stop_reason']}")
            print(f"CEO decision: {review['decision']['decision']}")
            print(f"Decision packet: {review['paths']['latest_decision_packet']}")
            return 0 if lab_result["status"] in {"completed", "stopped"} else 1
        if action == "execute-next":
            result = run_ceo_execute_next(options)
            action_result = result["action_result"]
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Decision: {action_result.get('decision')}")
            print(f"Action taken: {action_result.get('action_taken')}")
            print(f"Status: {action_result.get('status')}")
            paths = result.get("paths", {})
            if paths.get("binding_action_result"):
                print(f"Action result: {paths['binding_action_result']}")
            if paths.get("capability_gap"):
                print(f"Capability gap: {paths['capability_gap']}")
            return 0 if action_result.get("status") not in {"blocked"} else 1
        if action == "champion-challenger":
            result = run_ceo_champion_challenger(options, top_n=getattr(args, "top_n", None))
            action_result = result["action_result"]
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Status: {action_result.get('status')}")
            print(f"Results: {result['paths']['results']}")
            if result["paths"].get("capability_gap"):
                print(f"Capability gap: {result['paths']['capability_gap']}")
            return 0
        if action == "fresh-control-validation":
            result = run_ceo_fresh_control_validation(options)
            action_result = result["action_result"]
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Status: {action_result.get('status')}")
            print(f"Plan: {result['paths']['plan']}")
            print(f"Report: {result['paths']['report']}")
            return 0 if action_result.get("status") not in {"blocked_missing_champion_challenger_results"} else 1
        if action == "fresh-data-preflight":
            result = run_ceo_fresh_data_preflight(options)
            preflight = result["preflight"]
            print(f"Fresh data preflight: {result['paths']['preflight']}")
            print(f"Preflight report: {result['paths']['report']}")
            print(f"Overall status: {preflight.get('overall_status')}")
            print(f"Safe to run fresh validation: {preflight.get('safe_to_run_fresh_validation')}")
            print(f"Next action: {preflight.get('next_action')}")
            return 0 if preflight.get("safe_to_run_fresh_validation") else 1
        if action == "frozen-candidate-validation":
            result = run_ceo_frozen_candidate_validation(options)
            plan = result["plan"]
            print(f"Frozen candidate validation plan: {result['paths']['plan']}")
            print(f"Frozen candidate validation report: {result['paths']['report']}")
            print(f"Status: {plan.get('status')}")
            print(f"Ready specs: {plan.get('ready_spec_count')}/{plan.get('spec_count')}")
            print(f"Next action: {plan.get('next_action')}")
            return 0 if plan.get("safe_to_execute_specs") else 1
        if action == "frozen-validation-executor":
            result = run_ceo_frozen_validation_executor(options)
            execution = result["execution"]
            print(f"Frozen validation execution result: {result['paths']['result']}")
            print(f"Frozen validation execution report: {result['paths']['report']}")
            print(f"Frozen validation rerun grid: {result['paths']['rerun_grid']}")
            print(f"Status: {execution.get('status')}")
            print(f"Executed specs: {execution.get('executed_spec_count')}/{execution.get('spec_count')}")
            print(f"Validation result: {execution.get('validation_result')}")
            print(f"Next action: {execution.get('next_action')}")
            return 0 if execution.get("validation_completed") else 1
        if action == "frozen-validation-rerun":
            result = run_ceo_frozen_validation_rerun(options)
            rerun = result["rerun"]
            print(f"Frozen validation rerun result: {result['paths']['result']}")
            print(f"Frozen validation rerun report: {result['paths']['report']}")
            print(f"Frozen validation rerun output dir: {result['paths']['output_dir']}")
            print(f"Status: {rerun.get('status')}")
            print(f"Records: {rerun.get('record_rows')}")
            print(f"Strict referee rows: {rerun.get('strict_referee_rows')}")
            print(f"Next action: {rerun.get('next_action')}")
            return 0 if str(rerun.get("status", "")).startswith("adapter_rerun_") else 1
        if action == "fresh-withheld-validation-contract":
            result = run_ceo_fresh_withheld_validation_contract(options)
            contract = result["contract"]
            print(f"Fresh/withheld validation contract: {result['paths']['contract']}")
            print(f"Fresh/withheld validation report: {result['paths']['report']}")
            print(f"Status: {contract.get('status')}")
            print(f"Ready specs: {contract.get('ready_spec_count')}/{contract.get('candidate_spec_count')}")
            print(f"Next action: {contract.get('next_action')}")
            return 0 if contract.get("status") == "fresh_withheld_validation_contract_ready" else 1
        if action == "withheld-split-manifest":
            result = run_ceo_withheld_split_manifest(
                options,
                withheld_split_id=args.withheld_split_id,
                source_evidence_cutoff=args.source_evidence_cutoff,
                description=args.description,
            )
            manifest = result["manifest"]
            print(f"Withheld split manifest: {result['paths']['manifest']}")
            print(f"Withheld split manifest report: {result['paths']['report']}")
            print(f"Status: {manifest.get('status')}")
            print(f"Withheld split id: {manifest.get('withheld_split_id') or 'unset'}")
            print(f"Blocked reasons: {manifest.get('blocked_reasons') or []}")
            print(f"Next action: {result['action_result'].get('next_allowed_actions', [''])[0]}")
            return 0 if manifest.get("status") == "withheld_split_manifest_ready" else 1
        if action == "fresh-withheld-snapshot-manifest":
            result = run_ceo_fresh_withheld_snapshot_manifest(options)
            manifest = result["manifest"]
            print(f"Fresh/withheld snapshot manifest: {result['paths']['manifest']}")
            print(f"Fresh/withheld snapshot manifest report: {result['paths']['report']}")
            print(f"Status: {manifest.get('status')}")
            print(f"Snapshot type: {manifest.get('snapshot_type') or 'unset'}")
            print(f"Active assets: {manifest.get('active_asset_count')}")
            print(f"Next action: {manifest.get('next_action')}")
            return 0 if manifest.get("status") == "draft_requires_manual_snapshot_authority" else 1
        if action == "fresh-withheld-snapshot-declare":
            result = run_ceo_fresh_withheld_snapshot_declare(
                options,
                snapshot_type=args.snapshot_type,
                snapshot_cutoff=args.snapshot_cutoff,
                withheld_split_id=args.withheld_split_id,
                source_evidence_cutoff=args.source_evidence_cutoff,
                confirm_no_overlap=args.confirm_no_overlap,
            )
            manifest = result["manifest"]
            print(f"Fresh/withheld snapshot manifest: {result['paths']['manifest']}")
            print(f"Fresh/withheld snapshot manifest report: {result['paths']['report']}")
            print(f"Status: {manifest.get('status')}")
            print(f"Blocked reasons: {manifest.get('blocked_reasons') or []}")
            print(f"Next action: {manifest.get('next_action')}")
            return 0 if manifest.get("status") == "snapshot_authority_ready" else 1
        if action == "fresh-withheld-validation-executor":
            result = run_ceo_fresh_withheld_validation_executor(options)
            execution = result["execution"]
            print(f"Fresh/withheld validation execution result: {result['paths']['result']}")
            print(f"Fresh/withheld validation execution report: {result['paths']['report']}")
            print(f"Status: {execution.get('status')}")
            print(f"Validation completed: {execution.get('validation_completed')}")
            print(f"Validation result: {execution.get('validation_result')}")
            print(f"Next action: {execution.get('next_action')}")
            return 0 if execution.get("validation_completed") else 1
        if action == "patch-research-infra":
            result = run_ceo_patch_research_infra(options)
            action_result = result["action_result"]
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Status: {action_result.get('status')}")
            print(f"Plan: {result['paths']['plan']}")
            print(f"Report: {result['paths']['report']}")
            return 0 if action_result.get("status") not in {"blocked_missing_recovery_inputs", "blocked_recovery_audit_failed"} else 1
        if action == "broaden-hypothesis-source":
            result = run_ceo_broaden_hypothesis_source(options)
            action_result = result["action_result"]
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Status: {action_result.get('status')}")
            print(f"Plan: {result['paths']['plan']}")
            print(f"Report: {result['paths']['report']}")
            return 0 if action_result.get("status") != "no_broadening_sources" else 1
        if action == "heartbeat-status":
            result = run_ceo_heartbeat_status(options)
            status = result["status"]
            print(f"CEO run id: {result['run_id']}")
            print(f"Lab run id: {result['lab_run_id']}")
            print(f"Heartbeat status: {result['paths']['heartbeat_status']}")
            print(f"Last block: {status.get('last_block_number')}")
            print(f"Last decision: {status.get('last_decision')}")
            print(f"Continue recommended: {status.get('continue_recommended')}")
            print(f"Stop requested: {status.get('stop_requested')}")
            print(f"True blocker: {status.get('true_blocker')}")
            if status.get("manual_gate_active"):
                print(f"Manual gate active: {status.get('manual_gate_active')}")
                print(f"Runtime authority: {status.get('runtime_authority_status')}")
                print(f"Runtime block reason: {status.get('runtime_block_reason')}")
            if status.get("data_gate_status"):
                print(f"Data gate: {status.get('data_gate_status')}")
                print(f"Data gate preflight: {status.get('data_gate_preflight_status')}")
                print(f"Data gate safe fresh validation: {status.get('data_gate_safe_to_run_fresh_validation')}")
                print(f"Data gate required timeframes: {status.get('data_gate_required_timeframes') or []}")
                print(f"Data gate CSV requirements: {status.get('data_gate_csv_requirement_count')}")
                print(f"Data gate candidate unlocks: {status.get('data_gate_candidate_unlock_count')}")
                print(f"Data gate next action: {status.get('data_gate_next_action') or 'none'}")
                if status.get("data_gate_brief_report"):
                    print(f"Data gate report: {status.get('data_gate_brief_report')}")
                if status.get("data_gate_candidate_unlocks"):
                    print(f"Data gate candidate unlock table: {status.get('data_gate_candidate_unlocks')}")
                if status.get("data_gate_import_plan"):
                    print(f"Data gate import plan: {status.get('data_gate_import_plan')}")
                if status.get("data_gate_import_plan_report"):
                    print(f"Data gate import plan report: {status.get('data_gate_import_plan_report')}")
                if status.get("data_gate_import_batches"):
                    print(f"Data gate import batch table: {status.get('data_gate_import_batches')}")
                if status.get("data_gate_import_checklist"):
                    print(f"Data gate import checklist: {status.get('data_gate_import_checklist')}")
                    print(
                        "Data gate import checklist rows/pending/ready: "
                        f"{status.get('data_gate_import_checklist_row_count')}/"
                        f"{status.get('data_gate_import_checklist_pending_imports')}/"
                        f"{status.get('data_gate_import_checklist_complete_ready')}"
                    )
                    print(
                        "Data gate import checklist missing/stale: "
                        f"{status.get('data_gate_import_checklist_missing_count')}/"
                        f"{status.get('data_gate_import_checklist_stale_count')}"
                    )
                if status.get("data_gate_import_checklist_report"):
                    print(f"Data gate import checklist report: {status.get('data_gate_import_checklist_report')}")
                if status.get("data_gate_handoff_audit"):
                    print(f"Data gate handoff audit: {status.get('data_gate_handoff_audit')}")
                    print(f"Data gate handoff audit status: {status.get('data_gate_handoff_audit_status')}")
                    print(
                        "Data gate handoff audit checks/issues: "
                        f"{status.get('data_gate_handoff_audit_check_count')}/"
                        f"{status.get('data_gate_handoff_audit_issue_count')}"
                    )
                if status.get("data_gate_handoff_audit_report"):
                    print(f"Data gate handoff audit report: {status.get('data_gate_handoff_audit_report')}")
                if status.get("data_gate_symbol_matrix"):
                    print(f"Data gate symbol matrix: {status.get('data_gate_symbol_matrix')}")
                    print(f"Data gate symbol matrix rows: {status.get('data_gate_symbol_matrix_row_count')}")
                if status.get("data_gate_symbol_matrix_report"):
                    print(f"Data gate symbol matrix report: {status.get('data_gate_symbol_matrix_report')}")
            if status.get("sidecar_visual_review_top_candidate"):
                print(f"Sidecar visual-review top candidate: {status.get('sidecar_visual_review_top_candidate')}")
                print(f"Sidecar visual-review top role: {status.get('sidecar_visual_review_top_product_role') or 'none'}")
                print(f"Sidecar visual-review top focus: {status.get('sidecar_visual_review_top_focus') or 'none'}")
                print(f"Sidecar visual-review top priority: {status.get('sidecar_visual_review_top_priority')}")
                if status.get("sidecar_visual_review_top_question"):
                    print(f"Sidecar visual-review top question: {status.get('sidecar_visual_review_top_question')}")
                if status.get("sidecar_visual_review_top_gallery"):
                    print(f"Sidecar visual-review top gallery: {status.get('sidecar_visual_review_top_gallery')}")
                if status.get("sidecar_visual_review_top_labels_with_images"):
                    print(f"Sidecar visual-review top labels: {status.get('sidecar_visual_review_top_labels_with_images')}")
            if status.get("sidecar_visual_review_coverage"):
                print(f"Sidecar visual-review coverage: {status.get('sidecar_visual_review_coverage')}")
                print(f"Sidecar visual-review coverage rows: {status.get('sidecar_visual_review_coverage_row_count')}")
                print(
                    "Sidecar visual-review coverage ready/missing/empty-label: "
                    f"{status.get('sidecar_visual_review_coverage_ready_count')}/"
                    f"{status.get('sidecar_visual_review_coverage_missing_count')}/"
                    f"{status.get('sidecar_visual_review_coverage_empty_label_count')}"
                )
                print(
                    "Sidecar visual-review human-review started/pending: "
                    f"{status.get('sidecar_visual_review_human_review_started_count')}/"
                    f"{status.get('sidecar_visual_review_human_review_pending_count')}"
                )
            if status.get("sidecar_visual_review_coverage_report"):
                print(f"Sidecar visual-review coverage report: {status.get('sidecar_visual_review_coverage_report')}")
            if status.get("sidecar_visual_label_worklist"):
                print(f"Sidecar visual-label worklist: {status.get('sidecar_visual_label_worklist')}")
                print(f"Sidecar visual-label worklist rows: {status.get('sidecar_visual_label_worklist_row_count')}")
                print(f"Sidecar visual-label worklist candidates: {status.get('sidecar_visual_label_worklist_candidate_count')}")
                print(
                    "Sidecar visual-label exact/family-timeframe/context rows: "
                    f"{status.get('sidecar_visual_label_worklist_exact_variant_count')}/"
                    f"{status.get('sidecar_visual_label_worklist_family_timeframe_count')}/"
                    f"{status.get('sidecar_visual_label_worklist_family_context_count')}"
                )
            if status.get("sidecar_visual_label_worklist_report"):
                print(f"Sidecar visual-label worklist report: {status.get('sidecar_visual_label_worklist_report')}")
            if status.get("sidecar_visual_label_review_batches"):
                print(f"Sidecar visual-label review batches: {status.get('sidecar_visual_label_review_batches')}")
                print(f"Sidecar visual-label review batch rows: {status.get('sidecar_visual_label_review_batch_row_count')}")
                print(f"Sidecar visual-label review batch count: {status.get('sidecar_visual_label_review_batch_count')}")
                print(
                    "Sidecar visual-label review batch exact/family-timeframe/context rows: "
                    f"{status.get('sidecar_visual_label_review_batch_exact_variant_count')}/"
                    f"{status.get('sidecar_visual_label_review_batch_family_timeframe_count')}/"
                    f"{status.get('sidecar_visual_label_review_batch_family_context_count')}"
                )
            if status.get("sidecar_visual_label_review_batches_report"):
                print(
                    "Sidecar visual-label review batches report: "
                    f"{status.get('sidecar_visual_label_review_batches_report')}"
                )
            if status.get("sidecar_visual_label_progress"):
                print(f"Sidecar visual-label progress: {status.get('sidecar_visual_label_progress')}")
                print(
                    "Sidecar visual-label progress matched/pending/completed rows: "
                    f"{status.get('sidecar_visual_label_progress_matched_rows')}/"
                    f"{status.get('sidecar_visual_label_progress_pending_rows')}/"
                    f"{status.get('sidecar_visual_label_progress_completed_rows')}"
                )
                print(
                    "Sidecar visual-label progress not-started/incomplete/complete candidates: "
                    f"{status.get('sidecar_visual_label_progress_not_started_candidates')}/"
                    f"{status.get('sidecar_visual_label_progress_incomplete_candidates')}/"
                    f"{status.get('sidecar_visual_label_progress_complete_candidates')}"
                )
                print(
                    "Sidecar visual-label progress next batch: "
                    f"{status.get('sidecar_visual_label_progress_next_batch_id') or 'none'}"
                )
            if status.get("sidecar_visual_label_progress_report"):
                print(
                    "Sidecar visual-label progress report: "
                    f"{status.get('sidecar_visual_label_progress_report')}"
                )
            if status.get("sidecar_visual_label_next_batch"):
                print(f"Sidecar visual-label next batch: {status.get('sidecar_visual_label_next_batch')}")
                print(f"Sidecar visual-label next batch id: {status.get('sidecar_visual_label_next_batch_id')}")
                print(f"Sidecar visual-label next batch rows: {status.get('sidecar_visual_label_next_batch_row_count')}")
                print(
                    "Sidecar visual-label next batch exact/family-timeframe/context rows: "
                    f"{status.get('sidecar_visual_label_next_batch_exact_variant_count')}/"
                    f"{status.get('sidecar_visual_label_next_batch_family_timeframe_count')}/"
                    f"{status.get('sidecar_visual_label_next_batch_family_context_count')}"
                )
            if status.get("sidecar_visual_label_next_batch_report"):
                print(
                    "Sidecar visual-label next batch report: "
                    f"{status.get('sidecar_visual_label_next_batch_report')}"
                )
            if status.get("sidecar_visual_label_next_batch_gallery"):
                print(
                    "Sidecar visual-label next batch gallery: "
                    f"{status.get('sidecar_visual_label_next_batch_gallery')}"
                )
            if status.get("sidecar_visual_label_decision_context"):
                print(
                    "Sidecar visual-label decision context: "
                    f"{status.get('sidecar_visual_label_decision_context')}"
                )
                print(
                    "Sidecar visual-label decision context status/rows: "
                    f"{status.get('sidecar_visual_label_decision_context_status')}/"
                    f"{status.get('sidecar_visual_label_decision_context_row_count')}"
                )
                print(
                    "Sidecar visual-label decision context false/avoided probes: "
                    f"{status.get('sidecar_visual_label_decision_context_false_warning_probe_count')}/"
                    f"{status.get('sidecar_visual_label_decision_context_avoided_downside_probe_count')}"
                )
                print(
                    "Sidecar visual-label decision context pending/gaps: "
                    f"{status.get('sidecar_visual_label_decision_context_pending_entry_cells')}/"
                    f"{status.get('sidecar_visual_label_decision_context_entry_reference_gaps')}"
                )
            if status.get("sidecar_visual_label_decision_context_report"):
                print(
                    "Sidecar visual-label decision context report: "
                    f"{status.get('sidecar_visual_label_decision_context_report')}"
                )
            if status.get("sidecar_visual_label_rubric"):
                print(f"Sidecar visual-label rubric: {status.get('sidecar_visual_label_rubric')}")
                print(f"Sidecar visual-label rubric status: {status.get('sidecar_visual_label_rubric_status')}")
                print(f"Sidecar visual-label rubric batch: {status.get('sidecar_visual_label_rubric_batch_id')}")
                print(
                    "Sidecar visual-label rubric required fields: "
                    f"{status.get('sidecar_visual_label_rubric_required_fields') or 'none'}"
                )
            if status.get("sidecar_visual_label_rubric_report"):
                print(f"Sidecar visual-label rubric report: {status.get('sidecar_visual_label_rubric_report')}")
            if status.get("sidecar_visual_label_entry_sheet"):
                print(f"Sidecar visual-label entry sheet: {status.get('sidecar_visual_label_entry_sheet')}")
                print(f"Sidecar visual-label entry sheet batch: {status.get('sidecar_visual_label_entry_sheet_batch_id')}")
                print(f"Sidecar visual-label entry sheet rows: {status.get('sidecar_visual_label_entry_sheet_row_count')}")
                print(
                    "Sidecar visual-label entry sheet required fields: "
                    f"{status.get('sidecar_visual_label_entry_sheet_required_fields') or 'none'}"
                )
                print(
                    "Sidecar visual-label entry sheet missing required cells: "
                    f"{status.get('sidecar_visual_label_entry_sheet_missing_required_cells')}"
                )
                print(
                    "Sidecar visual-label entry sheet source-file/source-row/image gaps: "
                    f"{status.get('sidecar_visual_label_entry_sheet_missing_source_files')}/"
                    f"{status.get('sidecar_visual_label_entry_sheet_missing_source_rows')}/"
                    f"{status.get('sidecar_visual_label_entry_sheet_missing_images')}"
                )
            if status.get("sidecar_visual_label_entry_sheet_report"):
                print(
                    "Sidecar visual-label entry sheet report: "
                    f"{status.get('sidecar_visual_label_entry_sheet_report')}"
                )
            if status.get("sidecar_visual_label_source_update_manifest"):
                print(
                    "Sidecar visual-label source update manifest: "
                    f"{status.get('sidecar_visual_label_source_update_manifest')}"
                )
                print(
                    "Sidecar visual-label source update rows/pending/cells: "
                    f"{status.get('sidecar_visual_label_source_update_manifest_row_count')}/"
                    f"{status.get('sidecar_visual_label_source_update_manifest_pending_update_rows')}/"
                    f"{status.get('sidecar_visual_label_source_update_manifest_required_update_cells')}"
                )
                print(
                    "Sidecar visual-label source update source-file/source-row/image gaps: "
                    f"{status.get('sidecar_visual_label_source_update_manifest_missing_source_files')}/"
                    f"{status.get('sidecar_visual_label_source_update_manifest_missing_source_rows')}/"
                    f"{status.get('sidecar_visual_label_source_update_manifest_missing_images')}"
                )
            if status.get("sidecar_visual_label_source_update_manifest_report"):
                print(
                    "Sidecar visual-label source update manifest report: "
                    f"{status.get('sidecar_visual_label_source_update_manifest_report')}"
                )
            if status.get("sidecar_visual_label_source_patch_plan"):
                print(
                    "Sidecar visual-label source patch plan: "
                    f"{status.get('sidecar_visual_label_source_patch_plan')}"
                )
                print(
                    "Sidecar visual-label source patch cells/pending/blocked: "
                    f"{status.get('sidecar_visual_label_source_patch_plan_cell_count')}/"
                    f"{status.get('sidecar_visual_label_source_patch_plan_pending_cells')}/"
                    f"{status.get('sidecar_visual_label_source_patch_plan_blocked_cells')}"
                )
                print(
                    "Sidecar visual-label source patch files/rows: "
                    f"{status.get('sidecar_visual_label_source_patch_plan_source_files')}/"
                    f"{status.get('sidecar_visual_label_source_patch_plan_source_rows')}"
                )
            if status.get("sidecar_visual_label_source_patch_plan_report"):
                print(
                    "Sidecar visual-label source patch plan report: "
                    f"{status.get('sidecar_visual_label_source_patch_plan_report')}"
                )
            if status.get("sidecar_visual_label_completion_audit"):
                print(f"Sidecar visual-label completion audit: {status.get('sidecar_visual_label_completion_audit')}")
                print(
                    "Sidecar visual-label completion audit status: "
                    f"{status.get('sidecar_visual_label_completion_audit_status')}"
                )
                print(
                    "Sidecar visual-label completion audit rows/completed/missing/invalid: "
                    f"{status.get('sidecar_visual_label_completion_audit_rows')}/"
                    f"{status.get('sidecar_visual_label_completion_audit_completed_rows')}/"
                    f"{status.get('sidecar_visual_label_completion_audit_missing_rows')}/"
                    f"{status.get('sidecar_visual_label_completion_audit_invalid_rows')}"
                )
            if status.get("sidecar_visual_label_completion_audit_report"):
                print(
                    "Sidecar visual-label completion audit report: "
                    f"{status.get('sidecar_visual_label_completion_audit_report')}"
                )
            if status.get("sidecar_learning_status"):
                print(f"Sidecar learning ledger: {status.get('sidecar_learning_status')}")
                print(f"Sidecar learning candidates: {status.get('sidecar_learning_candidate_count')}")
                print(
                    "Sidecar learning lead/control/archive/review/blocked: "
                    f"{status.get('sidecar_learning_lead_count')}/"
                    f"{status.get('sidecar_learning_control_count')}/"
                    f"{status.get('sidecar_learning_archive_count')}/"
                    f"{status.get('sidecar_learning_review_count')}/"
                    f"{status.get('sidecar_learning_blocked_count')}"
                )
                if status.get("sidecar_learning_ledger_report"):
                    print(f"Sidecar learning report: {status.get('sidecar_learning_ledger_report')}")
                if status.get("sidecar_learning_lead_candidate"):
                    print(f"Sidecar learning lead candidate: {status.get('sidecar_learning_lead_candidate')}")
                    print(f"Sidecar learning lead next required: {status.get('sidecar_learning_lead_next_required_action') or 'none'}")
                    print(f"Sidecar learning lead authority: {status.get('sidecar_learning_lead_validation_authority') or 'none'}")
                if status.get("sidecar_learning_control_candidate"):
                    print(f"Sidecar learning control candidate: {status.get('sidecar_learning_control_candidate')}")
                    print(f"Sidecar learning control reason: {status.get('sidecar_learning_control_reason') or 'none'}")
                    print(f"Sidecar learning control next allowed: {status.get('sidecar_learning_control_next_allowed_action') or 'none'}")
                if status.get("sidecar_learning_archive_candidate"):
                    print(f"Sidecar learning archive candidate: {status.get('sidecar_learning_archive_candidate')}")
                    print(f"Sidecar learning archive reason: {status.get('sidecar_learning_archive_reason') or 'none'}")
                    print(f"Sidecar learning archive next allowed: {status.get('sidecar_learning_archive_next_allowed_action') or 'none'}")
            if status.get("sidecar_post_data_playbook"):
                print(f"Sidecar post-data playbook: {status.get('sidecar_post_data_playbook_status') or 'none'}")
                print(
                    "Sidecar post-data action: "
                    f"{status.get('sidecar_post_data_playbook_current_required_action') or 'none'}"
                )
                print(f"Sidecar post-data candidates: {status.get('sidecar_post_data_playbook_candidate_count')}")
                print(
                    "Sidecar post-data visual-label status/gate: "
                    f"{status.get('sidecar_post_data_playbook_visual_label_completion_status') or 'none'}/"
                    f"{status.get('sidecar_post_data_playbook_visual_label_gate_passed')}"
                )
                print(
                    "Sidecar post-data blockers: "
                    f"{status.get('sidecar_post_data_playbook_pre_validation_blockers') or 'none'}"
                )
                print(
                    "Sidecar post-data can-execute candidates: "
                    f"{status.get('sidecar_post_data_playbook_can_execute_count')}"
                )
                if status.get("sidecar_post_data_playbook_report"):
                    print(f"Sidecar post-data report: {status.get('sidecar_post_data_playbook_report')}")
            if status.get("sidecar_current_handoff"):
                print(f"Sidecar current handoff: {status.get('sidecar_current_handoff')}")
                if status.get("sidecar_current_handoff_report"):
                    print(f"Sidecar current handoff report: {status.get('sidecar_current_handoff_report')}")
                print(f"Sidecar current handoff status: {status.get('sidecar_current_handoff_status') or 'none'}")
                print(f"Sidecar current handoff candidates: {status.get('sidecar_current_handoff_candidate_count')}")
                print(
                    "Sidecar current handoff required action: "
                    f"{status.get('sidecar_current_handoff_required_action') or 'none'}"
                )
                print(
                    "Sidecar current handoff historical packet only: "
                    f"{status.get('sidecar_current_handoff_historical_only')}"
                )
                print(
                    "Sidecar current handoff stale product snapshot: "
                    f"{status.get('sidecar_current_handoff_stale_product_delta_snapshot_detected')}"
                )
                if status.get("sidecar_candidate_decision_matrix"):
                    print(f"Sidecar candidate decision matrix: {status.get('sidecar_candidate_decision_matrix')}")
                    print(
                        "Sidecar candidate decision matrix rows: "
                        f"{status.get('sidecar_candidate_decision_matrix_row_count')}"
                    )
                if status.get("sidecar_candidate_decision_matrix_report"):
                    print(
                        "Sidecar candidate decision matrix report: "
                        f"{status.get('sidecar_candidate_decision_matrix_report')}"
                    )
            if status.get("sidecar_current_decision_packet"):
                print(f"Sidecar current decision packet: {status.get('sidecar_current_decision_packet')}")
                if status.get("sidecar_current_decision_packet_report"):
                    print(
                        "Sidecar current decision packet report: "
                        f"{status.get('sidecar_current_decision_packet_report')}"
                    )
                print(
                    "Sidecar current decision packet status: "
                    f"{status.get('sidecar_current_decision_packet_status') or 'none'}"
                )
                print(
                    "Sidecar current decision packet decision: "
                    f"{status.get('sidecar_current_decision_packet_decision') or 'none'}"
                )
                if status.get("sidecar_current_decision_packet_quality_remediation_status"):
                    print(
                        "Sidecar current decision packet quality remediation status: "
                        f"{status.get('sidecar_current_decision_packet_quality_remediation_status')}"
                    )
                    print(
                        "Sidecar current decision packet quality remediation required action: "
                        f"{status.get('sidecar_current_decision_packet_quality_remediation_required_action')}"
                    )
                    print(
                        "Sidecar current decision packet quality remediation autonomous/human/diversity/archive: "
                        f"{status.get('sidecar_current_decision_packet_quality_remediation_autonomous_clearable_now_count')}/"
                        f"{status.get('sidecar_current_decision_packet_quality_remediation_human_visual_count')}/"
                        f"{status.get('sidecar_current_decision_packet_quality_remediation_diversity_control_count')}/"
                        f"{status.get('sidecar_current_decision_packet_quality_remediation_archive_only_count')}"
                    )
            if status.get("sidecar_evidence_consistency_audit"):
                print(f"Sidecar evidence consistency audit: {status.get('sidecar_evidence_consistency_audit')}")
                if status.get("sidecar_evidence_consistency_audit_report"):
                    print(
                        "Sidecar evidence consistency audit report: "
                        f"{status.get('sidecar_evidence_consistency_audit_report')}"
                    )
                print(
                    "Sidecar evidence consistency audit status: "
                    f"{status.get('sidecar_evidence_consistency_audit_status') or 'none'}"
                )
                print(
                    "Sidecar evidence consistency audit checks/issues: "
                    f"{status.get('sidecar_evidence_consistency_audit_check_count')}/"
                    f"{status.get('sidecar_evidence_consistency_audit_issue_count')}"
                )
            if status.get("sidecar_quality_status"):
                print(f"Sidecar quality status: {status.get('sidecar_quality_status')}")
                print(
                    "Sidecar quality hard/advisory issues: "
                    f"{status.get('sidecar_quality_hard_issue_count')}/"
                    f"{status.get('sidecar_quality_advisory_issue_count')}"
                )
                if status.get("sidecar_quality_advisory_issue_summary"):
                    print(f"Sidecar quality advisory summary: {status.get('sidecar_quality_advisory_issue_summary')}")
                if status.get("sidecar_quality_hard_issue_summary"):
                    print(f"Sidecar quality hard summary: {status.get('sidecar_quality_hard_issue_summary')}")
                if status.get("sidecar_quality_report"):
                    print(f"Sidecar quality report: {status.get('sidecar_quality_report')}")
            if status.get("sidecar_quality_remediation_plan"):
                print(f"Sidecar quality remediation plan: {status.get('sidecar_quality_remediation_plan')}")
                if status.get("sidecar_quality_remediation_plan_report"):
                    print(
                        "Sidecar quality remediation plan report: "
                        f"{status.get('sidecar_quality_remediation_plan_report')}"
                    )
                print(
                    "Sidecar quality remediation plan status: "
                    f"{status.get('sidecar_quality_remediation_plan_status') or 'none'}"
                )
                print(
                    "Sidecar quality remediation required action: "
                    f"{status.get('sidecar_quality_remediation_plan_current_required_action') or 'none'}"
                )
                print(
                    "Sidecar quality remediation autonomous/human/diversity/archive: "
                    f"{status.get('sidecar_quality_remediation_plan_autonomous_clearable_now_count')}/"
                    f"{status.get('sidecar_quality_remediation_plan_human_visual_remediation_count')}/"
                    f"{status.get('sidecar_quality_remediation_plan_diversity_control_remediation_count')}/"
                    f"{status.get('sidecar_quality_remediation_plan_archive_only_count')}"
                )
            if status.get("evidence_debt_status"):
                print(f"Evidence debt register: {status.get('evidence_debt_status')}")
                print(f"Evidence debt count: {status.get('evidence_debt_count')}")
                print(
                    "Evidence debt candidate/global/archive: "
                    f"{status.get('evidence_debt_candidate_count')}/"
                    f"{status.get('evidence_debt_global_count')}/"
                    f"{status.get('evidence_debt_archived_candidate_count')}"
                )
                if status.get("evidence_debt_next_action"):
                    print(f"Evidence debt next action: {status.get('evidence_debt_next_action')}")
                if status.get("evidence_debt_current_runtime_handoff_action"):
                    print(
                        "Evidence debt current handoff: "
                        f"{status.get('evidence_debt_current_runtime_handoff_action')}"
                    )
                    print(
                        "Evidence debt handoff status: "
                        f"{status.get('evidence_debt_current_runtime_handoff_status')}"
                    )
                    print(
                        "Evidence debt strategic blocked by handoff: "
                        f"{status.get('evidence_debt_strategic_blocked_by_current_handoff')}"
                    )
                if status.get("evidence_debt_register_report"):
                    print(f"Evidence debt report: {status.get('evidence_debt_register_report')}")
            print(f"Next action: {status.get('next_recommended_action')}")
            return 0
        if action == "heartbeat-plan":
            result = run_ceo_heartbeat_plan(
                options,
                interval_minutes=args.interval_minutes,
                max_hours=args.max_hours if args.max_hours is not None else 8.0,
            )
            print(f"Heartbeat plan: {result['paths']['heartbeat_plan']}")
            print(f"Heartbeat plan report: {result['paths']['heartbeat_plan_report']}")
            print(f"Tick command: {result['plan']['tick_command']}")
            return 0
        if action == "heartbeat-tick":
            result = run_ceo_heartbeat_tick(options)
            tick = result["tick"]
            print(f"Heartbeat state: {result['paths']['heartbeat_state']}")
            print(f"Heartbeat journal: {result['paths']['heartbeat_journal']}")
            print(f"Status: {tick.get('status')}")
            print(f"Blockers: {tick.get('blockers') or []}")
            print(f"Action: {tick.get('action_decision') or 'none'}")
            print(f"Next action: {tick.get('next_action')}")
            return 0 if tick.get("status") != "blocked_before_action" else 1
        if action == "heartbeat-journal":
            result = run_ceo_heartbeat_journal(options)
            print(f"Heartbeat journal: {result['paths']['heartbeat_journal']}")
            print(f"Heartbeat journal report: {result['paths']['heartbeat_journal_report']}")
            print(f"Ticks: {len(result['entries'])}")
            return 0
        if action == "stop":
            result = run_ceo_stop(options, reason=args.reason)
            print(f"CEO stop requested: {result['paths']['ceo_stop']}")
            print(f"Lab stop requested: {result['paths']['lab_stop']}")
            print(f"Reason: {result['reason']}")
            return 0
        if action == "review":
            result = run_ceo_review(options)
            print(f"CEO decision: {result['decision']['decision']}")
            print(f"Decision packet: {result['paths']['latest_decision_packet']}")
            return 0
        if action == "report":
            result = run_ceo_report(options)
            print(f"CEO report: {result['paths']['report']}")
            return 0
        if action == "trace-grade":
            result = run_ceo_trace_grade(options)
            grade = result["grade"]
            print(f"CEO trace grade: {result['paths']['trace_grade']}")
            print(f"Trace grade report: {result['paths']['trace_grade_report']}")
            print(f"Verdict: {grade.get('verdict')}")
            print(f"Score: {grade.get('score')}")
            print(f"Recommended next action: {grade.get('recommended_next_action')}")
            print(f"Manual data import required: {_trace_grade_manual_data_import_required(grade)}")
            print(f"Issues: {grade.get('issues') or []}")
            return 0 if grade.get("verdict") != "fail" else 1
        if action == "flight-dashboard":
            result = run_ceo_flight_dashboard(options)
            dashboard = result["dashboard"]
            print(f"CEO flight dashboard: {result['paths']['dashboard']}")
            print(f"Dashboard report: {result['paths']['dashboard_report']}")
            print(f"Safe to continue: {dashboard.get('safe_to_continue')}")
            print(f"Safety scope: {dashboard.get('safe_to_continue_scope') or 'flight_dashboard_only_not_dispatch_authority'}")
            print(f"Dispatch authority: {dashboard.get('dispatch_authority') or 'not_granted_by_flight_dashboard'}")
            print(f"Runtime authority note: {dashboard.get('runtime_authority_note') or 'check ceo status before dispatch'}")
            print(f"Blockers: {', '.join(dashboard.get('blockers', []) or []) or 'none'}")
            print(f"Next action: {dashboard.get('next_recommended_action')}")
            _print_ceo_trace_summary(dashboard.get("trace_grade", {}) or {})
            return 0
        if action == "operating-dashboard":
            result = run_ceo_operating_dashboard(options)
            dashboard = result["dashboard"]
            print(f"CEO operating dashboard: {result['paths']['dashboard']}")
            print(f"Dashboard report: {result['paths']['dashboard_report']}")
            print(f"Candidate portfolio: {dashboard.get('candidate_portfolio_count')}")
            print(f"Capability backlog: {dashboard.get('capability_backlog_count')}")
            print(f"Safety scope: {dashboard.get('safe_to_continue_scope') or 'flight_dashboard_only_not_dispatch_authority'}")
            print(f"Dispatch authority: {dashboard.get('dispatch_authority') or 'not_granted_by_operating_dashboard'}")
            print(f"Runtime authority note: {dashboard.get('runtime_authority_note') or 'check ceo status before dispatch'}")
            print(f"Next recommended action: {dashboard.get('next_recommended_action')}")
            _print_ceo_trace_summary(dashboard.get("trace", {}) or {})
            return 0
        if action == "portfolio-allocator":
            result = run_ceo_portfolio_allocator(options)
            allocator = result["allocator"]
            selected = allocator.get("selected_lane", {}) or {}
            print(f"Portfolio allocator: {result['paths']['portfolio_allocator']}")
            print(f"Portfolio allocator report: {result['paths']['portfolio_allocator_report']}")
            print(f"Selected lane: {selected.get('lane_id')}")
            print(f"Score: {selected.get('score')}")
            print(f"Attention next action: {selected.get('next_action')}")
            print(f"Action scope: {allocator.get('action_scope') or 'portfolio_attention_only'}")
            print(f"Dispatch authority: {allocator.get('dispatch_authority') or 'not_granted_by_portfolio_allocator'}")
            print(f"Runtime authority note: {allocator.get('runtime_authority_note') or 'check ceo status before dispatch'}")
            return 0
        if action == "mission-score":
            result = run_ceo_mission_score(options)
            score = result["mission_score"]
            print(f"Mission score: {result['paths']['mission_score']}")
            print(f"Mission score report: {result['paths']['mission_score_report']}")
            print(f"Status: {score.get('status')}")
            print(f"Overall mission score: {score.get('overall_mission_score')}")
            print(f"Lowest dimension: {score.get('lowest_dimension')}")
            print(f"Mission attention action: {score.get('next_best_mission_action')}")
            print(f"Action scope: {score.get('action_scope') or 'mission_strategy_only'}")
            print(f"Dispatch authority: {score.get('dispatch_authority') or 'not_granted_by_mission_score'}")
            print(f"Runtime authority note: {score.get('runtime_authority_note') or 'check ceo status before dispatch'}")
            return 0
        if action == "strategy-capital-dashboard":
            result = run_ceo_strategy_capital_dashboard(options)
            dashboard = result["dashboard"]
            print(f"Strategy capital dashboard: {result['paths']['strategy_capital_dashboard']}")
            print(f"Strategy capital dashboard report: {result['paths']['strategy_capital_dashboard_report']}")
            print(f"Safe to continue: {dashboard.get('safe_to_continue')}")
            print(f"Safety scope: {dashboard.get('safe_to_continue_scope') or 'strategy_attention_only_not_dispatch_authority'}")
            print(f"Dispatch authority: {dashboard.get('dispatch_authority') or 'not_granted_by_strategy_capital_dashboard'}")
            print(f"Runtime authority note: {dashboard.get('runtime_authority_note') or 'check ceo status before dispatch'}")
            print(f"Selected bucket: {dashboard.get('selected_capital_bucket')}")
            print(f"Selected strategy: {dashboard.get('selected_strategy')}")
            print(f"Capital points: {dashboard.get('total_points')}")
            return 0
        if action == "decision-quality":
            result = run_ceo_decision_quality(options)
            quality = result["decision_quality"]
            print(f"Decision quality: {result['paths']['decision_quality']}")
            print(f"Decision quality report: {result['paths']['decision_quality_report']}")
            print(f"Effective runtime action: {quality.get('effective_runtime_action') or 'none'}")
            print(f"Effective runtime command kind: {quality.get('effective_runtime_command_kind') or 'none'}")
            print(f"Effective runtime can execute now: {quality.get('effective_runtime_can_execute_now')}")
            print(f"Runtime blocked: {quality.get('runtime_blocked')}")
            print(f"Runtime block reason: {quality.get('runtime_block_reason') or 'none'}")
            print(f"Selected action: {quality.get('selected_action')}")
            print(f"Selected strategic route advisory: {quality.get('selected_strategic_route_advisory') or 'none'}")
            print(f"Selected score: {quality.get('selected_score')}")
            print(f"Runner-up action: {quality.get('runner_up_action') or 'none'}")
            print(f"Confidence: {quality.get('confidence')}")
            print(f"Expected artifact: {quality.get('expected_artifact')}")
            print(f"Runtime authority: {quality.get('runtime_authority_status')}")
            print(f"Executable next action: {quality.get('executable_next_action') or 'none'}")
            print(f"Executable command kind: {quality.get('executable_next_command_kind') or 'none'}")
            print(f"Runtime authorized strategic route: {quality.get('runtime_authorized_strategic_route') or 'none'}")
            print(f"Runtime authorized route source: {quality.get('runtime_authorized_route_source') or 'none'}")
            print(f"Can execute now: {quality.get('executable_can_execute_now')}")
            print(f"Selected action executable now: {quality.get('selected_action_is_executable_now')}")
            print(f"Selected action blocked by: {quality.get('selected_action_blocked_by') or 'none'}")
            print(f"Runtime note: {quality.get('selected_action_runtime_note') or ''}")
            return 0
        if action == "action-board":
            result = run_ceo_action_board(options)
            board = result["action_board"]
            primary = board.get("primary_action", {}) or {}
            print(f"CEO action board: {result['paths']['action_board']}")
            print(f"CEO action board report: {result['paths']['action_board_report']}")
            print(f"Status: {board.get('status')}")
            print(f"Autonomy mode: {board.get('autonomy_mode')}")
            print(f"Primary action: {primary.get('action_id') or 'none'}")
            print(f"Primary kind: {primary.get('command_kind') or 'none'}")
            print(f"Can execute now: {primary.get('can_execute_now')}")
            print(f"Command: {primary.get('command')}")
            counts = board.get("counts", {}) or {}
            print(f"Manual gates: {counts.get('manual_gates', 0)}")
            print(f"Runnable repairs: {counts.get('runnable_repairs', 0)}")
            print(f"Diagnostic refreshes: {counts.get('diagnostic_refreshes', 0)}")
            print(f"Implementation repairs: {counts.get('implementation_repairs', 0)}")
            return 0 if board.get("status") not in {"manual_gate_required", "implementation_repair_required"} else 1
        if action == "operator-step":
            result = run_ceo_operator_step(options)
            step = result["operator_step"]
            primary = step.get("primary_action", {}) or {}
            print(f"CEO operator step: {result['paths']['operator_step']}")
            print(f"CEO operator step report: {result['paths']['operator_step_report']}")
            print(f"Status: {step.get('status')}")
            print(f"Reason: {step.get('reason')}")
            print(f"Primary action: {primary.get('action_id') or 'none'}")
            print(f"Primary kind: {primary.get('command_kind') or 'none'}")
            print(f"Action attempted: {step.get('action_attempted')}")
            print(f"Action executed: {step.get('action_executed')}")
            print(f"Execution status: {step.get('execution_status') or 'n/a'}")
            print(f"After board: {step.get('after_board_status')}")
            return 0 if step.get("action_executed") else 1
        if action == "operator-brief":
            result = run_ceo_operator_brief(options)
            brief = result["operator_brief"]
            situation = brief.get("current_situation", {}) or {}
            print(f"CEO operator brief: {result['paths']['operator_brief']}")
            print(f"CEO operator brief report: {result['paths']['operator_brief_report']}")
            print(f"Manual gate clearance packet: {result['paths'].get('manual_gate_clearance_packet')}")
            print(f"Manual gate clearance report: {result['paths'].get('manual_gate_clearance_packet_report')}")
            print(f"Status: {brief.get('status')}")
            print(f"Summary: {brief.get('plain_english_summary')}")
            print(f"Effective operator status: {situation.get('effective_operator_status') or 'unknown_or_diagnostic'}")
            print(f"Manual gate active: {situation.get('manual_gate_active')}")
            print(f"Effective operator runtime blocked: {situation.get('effective_operator_runtime_blocked')}")
            print(f"Effective operator runtime block reason: {situation.get('effective_operator_runtime_block_reason') or 'none'}")
            print(f"Primary action: {situation.get('primary_action') or 'none'}")
            print(f"Primary kind: {situation.get('primary_kind') or 'none'}")
            print(f"Effective runtime action: {situation.get('decision_quality_effective_runtime_action') or 'none'}")
            print(f"Effective runtime command kind: {situation.get('decision_quality_effective_runtime_command_kind') or 'none'}")
            print(f"Effective runtime can execute now: {situation.get('decision_quality_effective_runtime_can_execute_now')}")
            print(f"Runtime blocked: {situation.get('decision_quality_runtime_blocked')}")
            print(f"Runtime block reason: {situation.get('decision_quality_runtime_block_reason') or 'none'}")
            print(f"Selected advisory route: {situation.get('decision_quality_selected_strategic_route_advisory') or 'none'}")
            trace = brief.get("trace_health", {}) or {}
            print(f"Trace status: {trace.get('status') or 'missing_trace_grade'}")
            print(f"Trace score: {trace.get('score') if trace.get('score') != '' else 'n/a'}")
            print(f"Trace recommended next action: {trace.get('recommended_next_action') or 'none'}")
            print(f"Trace manual data import required: {trace.get('manual_data_import_required') if trace.get('manual_data_import_required') != '' else 'n/a'}")
            print(f"Trace issues: {trace.get('issues') or []}")
            clearance = brief.get("manual_gate_clearance", {}) or {}
            if clearance:
                print(f"Manual gate clearance status: {clearance.get('status')}")
                print(
                    "Manual gate clearance can start post-data validation: "
                    f"{clearance.get('can_start_post_data_validation')}"
                )
                print(
                    "Manual gate clearance blocked gates/count: "
                    f"{clearance.get('blocked_gates') or 'none'}/"
                    f"{clearance.get('blocked_gate_count')}"
                )
                print(
                    "Manual gate clearance first blocker/action: "
                    f"{clearance.get('first_blocking_gate') or 'none'}/"
                    f"{clearance.get('first_blocking_required_action') or 'none'}"
                )
                print(
                    "Manual gate clearance data/visual/can-execute: "
                    f"{clearance.get('pending_data_imports')}/"
                    f"{clearance.get('pending_visual_label_cells')}/"
                    f"{clearance.get('post_data_can_execute_count')}"
                )
            approval = brief.get("approval_work", {}) or {}
            print(f"Approval status: {approval.get('status') or 'none'}")
            print(f"Approval pending: {approval.get('pending_count') if approval.get('pending_count') != '' else 'n/a'}")
            print(f"Approval top id: {approval.get('top_pending_approval_id') or 'none'}")
            print(f"Approval record command: {approval.get('approval_record_command') or 'none'}")
            print(f"Approval apply command: {approval.get('approval_apply_command') or 'none'}")
            sidecar = brief.get("sidecar_current_decision", {}) or {}
            print(f"Sidecar current decision status: {sidecar.get('status') or 'missing_sidecar_current_decision_packet'}")
            print(f"Sidecar current decision: {sidecar.get('decision') or 'none'}")
            print(f"Sidecar current required action: {sidecar.get('required_action') or 'none'}")
            print(f"Sidecar current candidates: {sidecar.get('candidate_count') if sidecar.get('candidate_count') != '' else 'n/a'}")
            print(
                "Sidecar quality remediation status: "
                f"{sidecar.get('quality_remediation_status') or 'none'}"
            )
            print(
                "Sidecar quality remediation required action: "
                f"{sidecar.get('quality_remediation_required_action') or 'none'}"
            )
            print(
                "Sidecar quality remediation autonomous/human/diversity/archive: "
                f"{sidecar.get('quality_remediation_autonomous_clearable_now_count')}/"
                f"{sidecar.get('quality_remediation_human_visual_count')}/"
                f"{sidecar.get('quality_remediation_diversity_control_count')}/"
                f"{sidecar.get('quality_remediation_archive_only_count')}"
            )
            data_gate = brief.get("data_gate_work", {}) or {}
            if data_gate:
                data_gate_paths = data_gate.get("paths", {}) or {}
                print(f"Data gate work status: {data_gate.get('status') or 'none'}")
                print(f"Data gate universe: {data_gate.get('universe') or 'none'}")
                print(f"Data gate preflight status: {data_gate.get('preflight_status') or 'none'}")
                print(f"Data gate safe fresh validation: {data_gate.get('safe_to_run_fresh_validation')}")
                print(f"Data gate required timeframes: {data_gate.get('required_timeframes') or 'none'}")
                print(f"Data gate timeframe statuses: {data_gate.get('timeframe_statuses') or 'none'}")
                print(f"Data gate required CSVs: {data_gate.get('required_csv_count')}")
                print(f"Data gate required batches: {data_gate.get('required_batch_count')}")
                print(f"Data gate import batch rows: {data_gate.get('import_batch_row_count')}")
                print(
                    "Data gate import checklist rows/pending/ready: "
                    f"{data_gate.get('import_checklist_row_count')}/"
                    f"{data_gate.get('import_checklist_pending_imports')}/"
                    f"{data_gate.get('import_checklist_complete_ready')}"
                )
                print(
                    "Data gate import checklist missing/stale: "
                    f"{data_gate.get('import_checklist_missing_count')}/"
                    f"{data_gate.get('import_checklist_stale_count')}"
                )
                print(
                    "Data gate handoff audit status/checks/issues: "
                    f"{data_gate.get('handoff_audit_status') or 'none'}/"
                    f"{data_gate.get('handoff_audit_check_count')}/"
                    f"{data_gate.get('handoff_audit_issue_count')}"
                )
                print(f"Data gate symbol matrix rows: {data_gate.get('symbol_matrix_row_count')}")
                print(f"Data gate candidate unlocks: {data_gate.get('candidate_unlock_count')}")
                print(f"Data gate CSV requirement rows: {data_gate.get('csv_requirement_row_count')}")
                print(f"Data gate next verification command: {data_gate.get('next_verification_command') or 'none'}")
                print(f"Data gate import plan: {data_gate_paths.get('import_plan') or 'none'}")
                print(f"Data gate import batches: {data_gate_paths.get('import_batches') or 'none'}")
                print(f"Data gate import checklist: {data_gate_paths.get('import_checklist') or 'none'}")
                print(f"Data gate import checklist report: {data_gate_paths.get('import_checklist_report') or 'none'}")
                print(f"Data gate handoff audit: {data_gate_paths.get('handoff_audit') or 'none'}")
                print(f"Data gate handoff audit report: {data_gate_paths.get('handoff_audit_report') or 'none'}")
                print(f"Data gate symbol matrix: {data_gate_paths.get('symbol_matrix') or 'none'}")
                print(f"Data gate candidate unlocks file: {data_gate_paths.get('candidate_unlocks') or 'none'}")
                print(f"Data gate CSV requirements: {data_gate_paths.get('csv_requirements') or 'none'}")
                print(f"Data gate fresh preflight: {data_gate_paths.get('fresh_data_preflight') or 'none'}")
            visual_labels = brief.get("sidecar_visual_label_work", {}) or {}
            if visual_labels:
                visual_paths = visual_labels.get("paths", {}) or {}
                print(f"Sidecar visual-label work status: {visual_labels.get('status') or 'none'}")
                print(f"Sidecar visual-label next batch: {visual_labels.get('next_batch_id') or 'none'}")
                print(f"Sidecar visual-label required fields: {visual_labels.get('required_fields') or 'none'}")
                print(
                    "Sidecar visual-label progress matched/pending/completed rows: "
                    f"{visual_labels.get('progress_matched_rows')}/"
                    f"{visual_labels.get('progress_pending_rows')}/"
                    f"{visual_labels.get('progress_completed_rows')}"
                )
                print(f"Sidecar visual-label next batch rows: {visual_labels.get('next_batch_row_count')}")
                print(
                    "Sidecar visual-label entry sheet rows/missing cells: "
                    f"{visual_labels.get('entry_sheet_row_count')}/"
                    f"{visual_labels.get('entry_sheet_missing_required_cells')}"
                )
                print(
                    "Sidecar visual-label source update rows/pending/cells: "
                    f"{visual_labels.get('source_update_row_count')}/"
                    f"{visual_labels.get('source_update_pending_rows')}/"
                    f"{visual_labels.get('source_update_required_cells')}"
                )
                print(
                    "Sidecar visual-label source patch cells/pending/blocked: "
                    f"{visual_labels.get('source_patch_plan_cell_count')}/"
                    f"{visual_labels.get('source_patch_plan_pending_cells')}/"
                    f"{visual_labels.get('source_patch_plan_blocked_cells')}"
                )
                print(
                    "Sidecar visual-label source patch files/rows: "
                    f"{visual_labels.get('source_patch_plan_source_files')}/"
                    f"{visual_labels.get('source_patch_plan_source_rows')}"
                )
                print(
                    "Sidecar visual-label completion audit rows/completed/missing/invalid: "
                    f"{visual_labels.get('completion_audit_rows')}/"
                    f"{visual_labels.get('completion_audit_completed_rows')}/"
                    f"{visual_labels.get('completion_audit_missing_rows')}/"
                    f"{visual_labels.get('completion_audit_invalid_rows')}"
                )
                print(f"Sidecar visual-label next batch file: {visual_paths.get('next_batch') or 'none'}")
                print(f"Sidecar visual-label next batch gallery: {visual_paths.get('next_batch_gallery') or 'none'}")
                print(f"Sidecar visual-label entry sheet: {visual_paths.get('entry_sheet') or 'none'}")
                print(
                    "Sidecar visual-label source update manifest: "
                    f"{visual_paths.get('source_update_manifest') or 'none'}"
                )
                print(
                    "Sidecar visual-label source patch plan: "
                    f"{visual_paths.get('source_patch_plan') or 'none'}"
                )
                print(f"Sidecar visual-label rubric: {visual_paths.get('rubric') or 'none'}")
                print(
                    "Sidecar visual-label completion audit: "
                    f"{visual_paths.get('completion_audit_yaml') or visual_paths.get('completion_audit') or 'none'}"
                )
            post_data = brief.get("sidecar_post_data_work", {}) or {}
            if post_data:
                post_data_paths = post_data.get("paths", {}) or {}
                print(f"Sidecar post-data playbook status: {post_data.get('status') or 'none'}")
                print(
                    "Sidecar post-data required action: "
                    f"{post_data.get('current_required_action') or 'none'}"
                )
                print(f"Sidecar post-data candidates: {post_data.get('candidate_count')}")
                print(
                    "Sidecar post-data visual-label status/gate: "
                    f"{post_data.get('visual_label_completion_status') or 'none'}/"
                    f"{post_data.get('visual_label_gate_passed')}"
                )
                print(f"Sidecar post-data blockers: {post_data.get('pre_validation_blockers') or 'none'}")
                print(f"Sidecar post-data can-execute candidates: {post_data.get('can_execute_count')}")
                print(f"Sidecar post-data playbook: {post_data_paths.get('playbook') or 'none'}")
                print(f"Sidecar post-data playbook report: {post_data_paths.get('playbook_report') or 'none'}")
            specialist = brief.get("specialist_work", {}) or {}
            print(f"Specialist status: {specialist.get('status') or 'none'}")
            print(f"Specialist pending: {specialist.get('pending_task_count') if specialist.get('pending_task_count') != '' else 'n/a'}")
            print(f"Specialist completed: {specialist.get('completed_task_count') if specialist.get('completed_task_count') != '' else 'n/a'}")
            print(f"Specialist blocked: {specialist.get('blocked_task_count') if specialist.get('blocked_task_count') != '' else 'n/a'}")
            print(f"Specialist top task: {specialist.get('top_pending_task_id') or 'none'}")
            print(f"Specialist top packet: {specialist.get('top_pending_packet_path') or 'none'}")
            print(f"Specialist top result mode: {specialist.get('top_pending_result_resolution_mode') or 'none'}")
            print(f"Specialist top requires manual gate: {specialist.get('top_pending_requires_manual_gate')}")
            print(f"Specialist top closure command: {specialist.get('top_pending_closure_command') or 'none'}")
            print(f"Specialist top autonomous task: {specialist.get('top_autonomous_pending_task_id') or 'none'}")
            print(f"Specialist top autonomous packet: {specialist.get('top_autonomous_pending_packet_path') or 'none'}")
            print(f"Specialist top autonomous result command: {specialist.get('top_autonomous_next_role_result_command') or 'none'}")
            print(f"Specialist top blocked task: {specialist.get('top_blocked_task_id') or 'none'}")
            print(f"Specialist top blocked packet: {specialist.get('top_blocked_packet_path') or 'none'}")
            print(f"Specialist top blocked validation: {specialist.get('top_blocked_validation_status') or 'none'}")
            print(f"Specialist top blocked closure command: {specialist.get('top_blocked_closure_command') or 'none'}")
            print(f"Specialist top blocked review status: {specialist.get('top_blocked_review_status') or 'none'}")
            print(f"Specialist top blocked result path: {specialist.get('top_blocked_result_path') or 'none'}")
            print(f"Specialist top blocked next action: {specialist.get('top_blocked_next_action') or 'none'}")
            print(f"Specialist top blocked finding: {specialist.get('top_blocked_finding') or 'none'}")
            print(f"Specialist next result command: {specialist.get('next_role_result_command') or 'none'}")
            print(f"Recommended next action: {brief.get('recommended_next_action')}")
            return 0
        if action == "memory-delta":
            result = run_ceo_memory_delta(options)
            delta = result["memory_delta"]
            print(f"Memory delta: {result['paths']['memory_delta']}")
            print(f"Memory delta report: {result['paths']['memory_delta_report']}")
            if "memory_delta_note" in result["paths"]:
                print(f"Memory delta note: {result['paths']['memory_delta_note']}")
            print(f"Status: {delta.get('status')}")
            print(f"Required: {delta.get('memory_delta_required')}")
            print(f"Reasons: {delta.get('reasons') or []}")
            return 0
        if action == "guardrail-audit":
            result = run_ceo_guardrail_audit(options)
            audit = result["guardrail_audit"]
            print(f"Guardrail audit: {result['paths']['guardrail_audit']}")
            print(f"Guardrail audit report: {result['paths']['guardrail_audit_report']}")
            print(f"Status: {audit.get('status')}")
            print(f"Violations: {audit.get('violation_count')}")
            return 0 if audit.get("status") == "pass" else 1
        if action == "preflight-gate":
            result = run_ceo_preflight_gate(options, enforce_memory_delta=args.enforce_memory_delta)
            gate = result["preflight_gate"]
            print(f"Preflight gate: {result['paths']['preflight_gate']}")
            print(f"Preflight gate report: {result['paths']['preflight_gate_report']}")
            print(f"Status: {gate.get('status')}")
            print(f"Safe to execute: {gate.get('safe_to_execute')}")
            print(f"Blockers: {[item.get('blocker') for item in gate.get('blockers', []) or []]}")
            _print_ceo_preflight_trace_source(gate)
            return 0 if gate.get("safe_to_execute") else 1
        if action == "promotion-proposal":
            result = run_ceo_promotion_proposal(options)
            proposal = result["proposal"]
            print(f"Promotion proposal: {result['paths']['proposal']}")
            print(f"Proposal report: {result['paths']['proposal_report']}")
            print(f"Status: {proposal.get('status')}")
            print(f"Missing evidence: {proposal.get('missing_evidence') or []}")
            print(f"Approval required: {proposal.get('approval_required')}")
            return 0 if proposal.get("status") == "ready_for_user_approval" else 1
        if action == "evidence-debt-register":
            result = run_ceo_evidence_debt_register(options)
            register = result["register"]
            print(f"Evidence debt register: {result['paths']['register']}")
            print(f"Evidence debt report: {result['paths']['register_report']}")
            print(f"Status: {register.get('status')}")
            print(f"Debts: {register.get('debt_count')}")
            print(f"Next action: {register.get('next_action')}")
            return 0
        if action == "sidecar-evidence-brief":
            result = run_ceo_sidecar_evidence_brief(options)
            brief = result["brief"]
            print(f"Sidecar evidence brief: {result['paths']['sidecar_evidence_brief']}")
            print(f"Sidecar evidence report: {result['paths']['sidecar_evidence_brief_report']}")
            print(f"Sidecar candidate table: {result['paths']['sidecar_evidence_candidates']}")
            print(f"Sidecar visual-review handoff table: {result['paths']['sidecar_visual_review_handoff']}")
            print(f"Sidecar visual-review coverage: {result['paths']['sidecar_visual_review_coverage']}")
            print(f"Sidecar visual-review coverage report: {result['paths']['sidecar_visual_review_coverage_report']}")
            print(f"Sidecar visual-label worklist: {result['paths']['sidecar_visual_label_worklist']}")
            print(f"Sidecar visual-label worklist report: {result['paths']['sidecar_visual_label_worklist_report']}")
            print(f"Sidecar visual-label review batches: {result['paths']['sidecar_visual_label_review_batches']}")
            print(
                "Sidecar visual-label review batches report: "
                f"{result['paths']['sidecar_visual_label_review_batches_report']}"
            )
            print(f"Sidecar visual-label progress: {result['paths']['sidecar_visual_label_progress']}")
            print(f"Sidecar visual-label progress report: {result['paths']['sidecar_visual_label_progress_report']}")
            print(f"Sidecar visual-label next batch: {result['paths']['sidecar_visual_label_next_batch']}")
            print(
                "Sidecar visual-label next batch report: "
                f"{result['paths']['sidecar_visual_label_next_batch_report']}"
            )
            print(
                "Sidecar visual-label next batch gallery: "
                f"{result['paths']['sidecar_visual_label_next_batch_gallery']}"
            )
            print(
                "Sidecar visual-label decision context: "
                f"{result['paths']['sidecar_visual_label_decision_context']}"
            )
            print(
                "Sidecar visual-label decision context report: "
                f"{result['paths']['sidecar_visual_label_decision_context_report']}"
            )
            decision_context = result.get("visual_label_decision_context", {}) or {}
            print(
                "Sidecar visual-label decision context status/rows: "
                f"{decision_context.get('status')}/"
                f"{decision_context.get('row_count')}"
            )
            print(
                "Sidecar visual-label decision context false/avoided probes: "
                f"{decision_context.get('missed_upside_false_warning_probe_count')}/"
                f"{decision_context.get('avoided_downside_warning_probe_count')}"
            )
            print(f"Sidecar visual-label rubric: {result['paths']['sidecar_visual_label_rubric']}")
            print(f"Sidecar visual-label rubric report: {result['paths']['sidecar_visual_label_rubric_report']}")
            print(f"Sidecar visual-label entry sheet: {result['paths']['sidecar_visual_label_entry_sheet']}")
            print(
                "Sidecar visual-label entry sheet report: "
                f"{result['paths']['sidecar_visual_label_entry_sheet_report']}"
            )
            print(
                "Sidecar visual-label source update manifest: "
                f"{result['paths']['sidecar_visual_label_source_update_manifest']}"
            )
            print(
                "Sidecar visual-label source update manifest report: "
                f"{result['paths']['sidecar_visual_label_source_update_manifest_report']}"
            )
            print(
                "Sidecar visual-label source patch plan: "
                f"{result['paths']['sidecar_visual_label_source_patch_plan']}"
            )
            print(
                "Sidecar visual-label source patch plan YAML: "
                f"{result['paths']['sidecar_visual_label_source_patch_plan_yaml']}"
            )
            print(
                "Sidecar visual-label source patch plan report: "
                f"{result['paths']['sidecar_visual_label_source_patch_plan_report']}"
            )
            source_patch_plan = result.get("visual_label_source_patch_plan", {}) or {}
            print(
                "Sidecar visual-label source patch cells/pending/blocked: "
                f"{source_patch_plan.get('source_patch_cell_count')}/"
                f"{source_patch_plan.get('pending_source_patch_cell_count')}/"
                f"{source_patch_plan.get('blocked_source_patch_cell_count')}"
            )
            print(
                "Sidecar visual-label source patch files/rows: "
                f"{source_patch_plan.get('source_file_count')}/"
                f"{source_patch_plan.get('source_row_count')}"
            )
            print(
                "Sidecar visual-label completion audit: "
                f"{result['paths']['sidecar_visual_label_completion_audit']}"
            )
            print(
                "Sidecar visual-label completion audit YAML: "
                f"{result['paths']['sidecar_visual_label_completion_audit_yaml']}"
            )
            print(
                "Sidecar visual-label completion audit report: "
                f"{result['paths']['sidecar_visual_label_completion_audit_report']}"
            )
            print(
                "Sidecar champion/challenger evidence table: "
                f"{result['paths']['sidecar_champion_challenger_evidence']}"
            )
            print(
                "Sidecar champion/challenger quality audit: "
                f"{result['paths']['sidecar_champion_challenger_quality_audit']}"
            )
            print(
                "Sidecar champion/challenger quality audit report: "
                f"{result['paths']['sidecar_champion_challenger_quality_audit_report']}"
            )
            print(f"Sidecar quality remediation plan: {result['paths']['sidecar_quality_remediation_plan']}")
            print(
                "Sidecar quality remediation plan report: "
                f"{result['paths']['sidecar_quality_remediation_plan_report']}"
            )
            print(f"Sidecar evidence gap matrix: {result['paths']['sidecar_evidence_gap_matrix']}")
            print(f"Sidecar candidate readiness summary: {result['paths']['sidecar_candidate_readiness_summary']}")
            print(
                "Sidecar candidate readiness summary report: "
                f"{result['paths']['sidecar_candidate_readiness_summary_report']}"
            )
            print(f"Sidecar validation queue: {result['paths']['sidecar_validation_queue']}")
            print(f"Sidecar validation queue report: {result['paths']['sidecar_validation_queue_report']}")
            print(
                "Sidecar champion/challenger validation design: "
                f"{result['paths']['sidecar_champion_challenger_validation_design']}"
            )
            print(
                "Sidecar champion/challenger validation design report: "
                f"{result['paths']['sidecar_champion_challenger_validation_design_report']}"
            )
            print(f"Sidecar data-gate unlock matrix: {result['paths']['sidecar_data_gate_unlock_matrix']}")
            print(f"Sidecar data-gate unlock matrix YAML: {result['paths']['sidecar_data_gate_unlock_matrix_yaml']}")
            print(f"Sidecar data-gate unlock matrix report: {result['paths']['sidecar_data_gate_unlock_matrix_report']}")
            print(f"Sidecar evidence consistency audit: {result['paths']['sidecar_evidence_consistency_audit']}")
            print(
                "Sidecar evidence consistency audit report: "
                f"{result['paths']['sidecar_evidence_consistency_audit_report']}"
            )
            print(f"Sidecar evidence consistency audit status: {result['consistency_audit'].get('status')}")
            print(
                "Sidecar evidence consistency audit checks/issues: "
                f"{result['consistency_audit'].get('check_count')}/"
                f"{result['consistency_audit'].get('issue_count')}"
            )
            print(f"Sidecar evidence packet index: {result['paths']['sidecar_evidence_packet_index']}")
            print(f"Sidecar evidence packet index report: {result['paths']['sidecar_evidence_packet_index_report']}")
            print(f"Sidecar candidate decision cards: {result['paths']['sidecar_candidate_decision_cards']}")
            print(f"Sidecar current decision packet: {result['paths']['sidecar_current_decision_packet']}")
            print(
                "Sidecar current decision packet report: "
                f"{result['paths']['sidecar_current_decision_packet_report']}"
            )
            print(f"Sidecar shadow guardrail audit: {result['paths']['sidecar_shadow_guardrail_audit']}")
            print(f"Sidecar shadow guardrail report: {result['paths']['sidecar_shadow_guardrail_audit_report']}")
            print(f"Sidecar evidence source manifest: {result['paths']['sidecar_evidence_source_manifest']}")
            print(f"Sidecar evidence source health: {result['paths']['sidecar_evidence_source_health']}")
            print(f"Sidecar evidence source health YAML: {result['paths']['sidecar_evidence_source_health_yaml']}")
            print(f"Sidecar evidence source health report: {result['paths']['sidecar_evidence_source_health_report']}")
            print(f"Sidecar evidence source fingerprints: {result['paths']['sidecar_evidence_source_fingerprints']}")
            print(
                "Sidecar evidence source fingerprints YAML: "
                f"{result['paths']['sidecar_evidence_source_fingerprints_yaml']}"
            )
            print(
                "Sidecar evidence source fingerprints report: "
                f"{result['paths']['sidecar_evidence_source_fingerprints_report']}"
            )
            print(f"Sidecar candidate learning ledger: {result['paths']['sidecar_candidate_learning_ledger']}")
            print(
                "Sidecar candidate learning ledger YAML: "
                f"{result['paths']['sidecar_candidate_learning_ledger_yaml']}"
            )
            print(
                "Sidecar candidate learning ledger report: "
                f"{result['paths']['sidecar_candidate_learning_ledger_report']}"
            )
            print(
                "Sidecar post-data validation playbook: "
                f"{result['paths']['sidecar_post_data_validation_playbook']}"
            )
            print(
                "Sidecar post-data validation playbook report: "
                f"{result['paths']['sidecar_post_data_validation_playbook_report']}"
            )
            post_data_playbook = result.get("post_data_playbook", {}) or {}
            print(f"Sidecar post-data playbook status: {post_data_playbook.get('status')}")
            print(
                "Sidecar post-data required action: "
                f"{post_data_playbook.get('current_required_action') or 'none'}"
            )
            print(
                "Sidecar post-data visual-label status/gate: "
                f"{post_data_playbook.get('visual_label_completion_status') or 'none'}/"
                f"{post_data_playbook.get('visual_label_gate_passed')}"
            )
            print(
                "Sidecar post-data blockers: "
                f"{'|'.join(str(item) for item in post_data_playbook.get('pre_validation_blockers', []) or []) or 'none'}"
            )
            print(
                "Sidecar post-data can-execute candidates: "
                f"{sum(1 for candidate in post_data_playbook.get('candidates', []) or [] if candidate.get('can_execute_now') is True)}"
            )
            print(f"Sidecar current handoff: {result['paths']['sidecar_current_handoff']}")
            print(f"Sidecar current handoff report: {result['paths']['sidecar_current_handoff_report']}")
            print(f"Sidecar candidate decision matrix: {result['paths']['sidecar_candidate_decision_matrix']}")
            print(
                "Sidecar candidate decision matrix report: "
                f"{result['paths']['sidecar_candidate_decision_matrix_report']}"
            )
            print(f"Sidecar frozen-spec review table: {result['paths']['sidecar_frozen_spec_review']}")
            guardrail = result["guardrail_audit"]
            quality = result["champion_challenger_quality"]
            source_health = result["source_health"]
            source_fingerprints = result["source_fingerprints"]
            candidate_learning_ledger = result["candidate_learning_ledger"]
            print(f"Status: {brief.get('status')}")
            print(f"Guardrail status: {guardrail.get('status')}")
            print(f"Guardrail violations: {guardrail.get('violation_count')}")
            print(f"Champion/challenger quality status: {quality.get('status')}")
            print(f"Champion/challenger quality issues: {quality.get('issue_count')}")
            print(f"Source health status: {source_health.get('status')}")
            print(f"Source health issues: {source_health.get('issue_count')}")
            print(f"Source fingerprints status: {source_fingerprints.get('status')}")
            print(f"Source fingerprints issues: {source_fingerprints.get('issue_count')}")
            print(f"Candidate learning ledger status: {candidate_learning_ledger.get('status')}")
            print(
                "Candidate learning ledger lead/control/archive/review/blocked: "
                f"{candidate_learning_ledger.get('lead_post_data_candidate_count')}/"
                f"{candidate_learning_ledger.get('diversity_control_only_count')}/"
                f"{candidate_learning_ledger.get('archive_failure_mode_count')}/"
                f"{candidate_learning_ledger.get('review_only_candidate_count')}/"
                f"{candidate_learning_ledger.get('quality_blocked_review_only_count')}"
            )
            print(f"Candidate count: {brief.get('candidate_count')}")
            print(f"Ready visual review: {brief.get('ready_visual_review_count')}")
            print(f"Fresh-data blocked: {brief.get('fresh_data_blocked_count')}")
            print(f"Review-only frozen specs: {brief.get('review_only_frozen_spec_count')}")
            print(f"Official frozen plan exists: {brief.get('official_frozen_candidate_validation_plan_exists')}")
            print(f"Manual data gate active: {brief.get('manual_data_gate_active')}")
            print(f"Next action: {brief.get('next_action')}")
            return 0
        if action == "data-gate-brief":
            result = run_ceo_data_gate_brief(options)
            brief = result["brief"]
            print(f"Data gate brief: {result['paths']['data_gate_brief']}")
            print(f"Data gate report: {result['paths']['data_gate_brief_report']}")
            print(f"CSV requirement table: {result['paths']['data_gate_csv_requirements']}")
            print(f"Candidate unlock table: {result['paths']['data_gate_candidate_unlocks']}")
            print(f"Import plan: {result['paths']['data_gate_import_plan']}")
            print(f"Import plan report: {result['paths']['data_gate_import_plan_report']}")
            print(f"Import batch table: {result['paths']['data_gate_import_batches']}")
            print(f"Import checklist: {result['paths']['data_gate_import_checklist']}")
            print(f"Import checklist YAML: {result['paths']['data_gate_import_checklist_yaml']}")
            print(f"Import checklist report: {result['paths']['data_gate_import_checklist_report']}")
            print(f"Symbol matrix: {result['paths']['data_gate_symbol_matrix']}")
            print(f"Symbol matrix report: {result['paths']['data_gate_symbol_matrix_report']}")
            print(f"Handoff audit: {result['paths']['data_gate_handoff_audit']}")
            print(f"Handoff audit report: {result['paths']['data_gate_handoff_audit_report']}")
            print(f"Status: {brief.get('status')}")
            print(f"Preflight status: {brief.get('preflight_status')}")
            print(f"Safe to run fresh validation: {brief.get('safe_to_run_fresh_validation')}")
            print(f"Manual data gate active: {brief.get('manual_data_gate_active')}")
            print(f"Required timeframes: {brief.get('required_timeframes') or []}")
            print(f"CSV requirements: {brief.get('csv_requirement_count')}")
            print(f"Import batches: {result['import_plan'].get('required_batch_count')}")
            print(
                "Import checklist rows/pending/ready: "
                f"{result['import_checklist'].get('checklist_row_count')}/"
                f"{result['import_checklist'].get('pending_import_count')}/"
                f"{result['import_checklist'].get('complete_ready_count')}"
            )
            print(f"Handoff audit status: {result['handoff_audit'].get('status')}")
            print(
                "Handoff audit checks/issues: "
                f"{result['handoff_audit'].get('check_count')}/"
                f"{result['handoff_audit'].get('issue_count')}"
            )
            print(f"Symbol matrix rows: {result['symbol_matrix'].get('symbol_count')}")
            print(f"Blocked candidates: {brief.get('blocked_candidate_count')}")
            print(f"Candidate unlocks: {brief.get('candidate_unlock_count')}")
            print(f"Sidecar learning ledger: {brief.get('sidecar_learning_status')}")
            print(
                "Sidecar learning lead/control/archive/review/blocked: "
                f"{brief.get('sidecar_learning_lead_count')}/"
                f"{brief.get('sidecar_learning_control_count')}/"
                f"{brief.get('sidecar_learning_archive_count')}/"
                f"{brief.get('sidecar_learning_review_count')}/"
                f"{brief.get('sidecar_learning_blocked_count')}"
            )
            print(f"Fresh-data role blockers: {brief.get('fresh_data_role_blocker_count')}")
            print(f"Next action: {brief.get('next_action')}")
            print(f"Next verification command: {brief.get('next_verification_command')}")
            return 0
        if action == "approval-queue":
            result = run_ceo_approval_queue(options)
            queue = result["queue"]
            print(f"Approval queue: {result['paths']['queue']}")
            print(f"Approval queue report: {result['paths']['queue_report']}")
            print(f"Approval status: {result['paths']['approval_status']}")
            print(f"Status: {queue.get('status')}")
            print(f"Pending approvals: {queue.get('pending_count')}")
            print(f"Top pending approval: {queue.get('top_pending_approval_id') or 'none'}")
            print(f"Approval record command: {queue.get('top_pending_approval_record_command') or 'none'}")
            print(f"Approval apply command: {queue.get('top_pending_approval_apply_command') or 'none'}")
            print(f"Next action: {queue.get('next_action')}")
            return 0
        if action == "approval-record":
            result = run_ceo_approval_record(
                options,
                approval_id=args.approval_id,
                decision=args.decision,
                user_confirmed=args.user_confirmed,
            )
            print(f"Approval decision ledger: {result['paths']['approval_decision_ledger']}")
            print(f"Approval queue: {result['paths']['approval_queue']}")
            print(f"Approval status: {result['paths']['approval_status']}")
            print(f"Decision: {result['decision']['decision']}")
            return 0
        if action == "approval-apply":
            preflight_result = run_ceo_preflight_gate(options, enforce_memory_delta=True)
            preflight_gate = preflight_result["preflight_gate"]
            blockers = {str(item.get("blocker", "")) for item in preflight_gate.get("blockers", []) or []}
            allowed_blockers_by_approval = {
                "promotion_proposal": {"pending_user_approval"},
                "clear_stop_request": {"pending_user_approval", "stop_requested"},
            }
            allowed_blockers = allowed_blockers_by_approval.get(str(args.approval_id), set())
            unexpected_blockers = sorted(blockers - allowed_blockers)
            if unexpected_blockers:
                print(f"Approval apply blocked by unrelated preflight blockers: {preflight_result['paths']['preflight_gate']}")
                print(f"Preflight gate report: {preflight_result['paths']['preflight_gate_report']}")
                print(f"Status: {preflight_gate.get('status')}")
                print(f"Unexpected blockers: {unexpected_blockers}")
                _print_ceo_preflight_trace_source(preflight_gate)
                return 1
            result = run_ceo_approval_apply(
                replace(options, ceo_context="guarded_direct", ceo_authorized_action="approval-apply"),
                approval_id=args.approval_id,
                user_confirmed=args.user_confirmed,
            )
            approval_apply = result["approval_apply"]
            print(f"Approval apply: {result['paths']['approval_apply']}")
            print(f"Approval apply report: {result['paths']['approval_apply_report']}")
            print(f"Status: {approval_apply.get('status')}")
            print(f"Action taken: {approval_apply.get('action_taken')}")
            return 0 if not str(approval_apply.get("status", "")).startswith("blocked") else 1
        if action == "executive-kpis":
            result = run_ceo_executive_kpis(options)
            kpis = result["kpis"]
            values = kpis.get("kpis", {}) or {}
            print(f"Executive KPIs: {result['paths']['executive_kpis']}")
            print(f"Executive KPI report: {result['paths']['executive_kpis_report']}")
            print(f"Status: {kpis.get('status')}")
            print(f"Attention next action: {kpis.get('next_action')}")
            print(f"Next action scope: {kpis.get('next_action_scope') or 'executive_health_diagnostic_only'}")
            print(f"Dispatch authority: {kpis.get('dispatch_authority') or 'not_granted_by_executive_kpis'}")
            print(f"Runtime authority note: {kpis.get('runtime_authority_note') or 'check ceo status before dispatch'}")
            print(f"Open approvals: {values.get('open_approval_count')}")
            print(f"Evidence debt: {values.get('evidence_debt_count')}")
            print(f"Candidates: {values.get('candidate_count')}")
            print(
                "Sidecar learning ledger: "
                f"{values.get('sidecar_learning_status') or 'missing_sidecar_candidate_learning_ledger'}"
            )
            if values.get("sidecar_learning_status") and values.get(
                "sidecar_learning_status"
            ) != "missing_sidecar_candidate_learning_ledger":
                print(f"Sidecar learning candidates: {values.get('sidecar_learning_candidate_count')}")
                print(
                    "Sidecar learning lead/control/archive/review/blocked: "
                    f"{values.get('sidecar_learning_lead_count')}/"
                    f"{values.get('sidecar_learning_control_count')}/"
                    f"{values.get('sidecar_learning_archive_count')}/"
                    f"{values.get('sidecar_learning_review_count')}/"
                    f"{values.get('sidecar_learning_blocked_count')}"
                )
            print(f"Trace verdict: {values.get('trace_verdict') or 'none'}")
            print(f"Trace score: {values.get('trace_score') if values.get('trace_score') != '' else 'n/a'}")
            print(f"Trace recommended next action: {values.get('trace_recommended_next_action') or 'none'}")
            print(
                "Trace manual data import required: "
                f"{values.get('trace_manual_data_import_required') if values.get('trace_manual_data_import_required') != '' else 'n/a'}"
            )
            print(f"Trace issues: {values.get('trace_issues') or []}")
            print(f"Top blocker: {values.get('top_blocker') or 'none'}")
            print(f"Repair plan status: {values.get('repair_plan_status') or 'none'}")
            print(f"Top repair: {values.get('top_repair') or 'none'}")
            print(f"Top repair kind: {values.get('top_repair_kind') or 'none'}")
            print(f"Repair next command: {values.get('repair_next_command') or 'none'}")
            print(f"Role queue: {values.get('role_queue_status') or 'none'}")
            print(f"Role pending: {values.get('role_pending_count', 0)}")
            print(f"Role blocked: {values.get('role_blocked_count', 0)}")
            print(f"Role top blocked task: {values.get('role_top_blocked_task') or 'none'}")
            print(f"Role top blocked review: {values.get('role_top_blocked_review_status') or 'none'}")
            if values.get("role_top_blocked_next_action"):
                print(f"Role top blocked next action: {values.get('role_top_blocked_next_action')}")
            if values.get("role_top_blocked_finding"):
                print(f"Role top blocked finding: {values.get('role_top_blocked_finding')}")
            if values.get("role_next_action"):
                print(f"Role next action: {values.get('role_next_action')}")
            return 0
        if action == "role-queue":
            result = run_ceo_role_queue(options)
            queue = result["queue"]
            print(f"Role registry: {result['paths']['role_registry']}")
            print(f"Role task queue: {result['paths']['role_task_queue']}")
            print(f"Role task queue report: {result['paths']['role_task_queue_report']}")
            print(f"Status: {queue.get('status')}")
            print(f"Tasks: {queue.get('task_count')}")
            print(f"Pending: {queue.get('pending_task_count')}")
            print(f"Pending manual: {queue.get('pending_manual_task_count')}")
            print(f"Pending autonomous: {queue.get('pending_autonomous_task_count')}")
            print(f"Completed: {queue.get('completed_task_count')}")
            print(f"Blocked: {queue.get('blocked_task_count')}")
            print(f"Top pending task: {queue.get('top_pending_task_id') or 'none'}")
            print(f"Top pending role: {queue.get('top_pending_role_id') or 'none'}")
            print(f"Top pending packet: {queue.get('top_pending_packet_path') or 'none'}")
            print(f"Top pending result mode: {queue.get('top_pending_result_resolution_mode') or 'none'}")
            print(f"Top pending requires manual gate: {queue.get('top_pending_requires_manual_gate')}")
            print(f"Top pending closure command: {queue.get('top_pending_closure_command') or 'none'}")
            print(f"Top autonomous task: {queue.get('top_autonomous_pending_task_id') or 'none'}")
            print(f"Top autonomous packet: {queue.get('top_autonomous_pending_packet_path') or 'none'}")
            print(f"Top autonomous result command: {queue.get('top_autonomous_next_role_result_command') or 'none'}")
            print(f"Top blocked task: {queue.get('top_blocked_task_id') or 'none'}")
            print(f"Top blocked role: {queue.get('top_blocked_role_id') or 'none'}")
            print(f"Top blocked packet: {queue.get('top_blocked_packet_path') or 'none'}")
            print(f"Top blocked validation: {queue.get('top_blocked_validation_status') or 'none'}")
            print(f"Top blocked closure command: {queue.get('top_blocked_closure_command') or 'none'}")
            print(f"Top blocked review status: {queue.get('top_blocked_review_status') or 'none'}")
            print(f"Top blocked result path: {queue.get('top_blocked_result_path') or 'none'}")
            print(f"Top blocked next action: {queue.get('top_blocked_next_action') or 'none'}")
            print(f"Top blocked finding: {queue.get('top_blocked_finding') or 'none'}")
            print(f"Next role dispatch command: {queue.get('next_role_dispatch_command') or 'none'}")
            print(f"Next role result command: {queue.get('next_role_result_command') or 'none'}")
            print(f"Next action: {queue.get('next_action')}")
            return 0
        if action == "role-dispatch":
            result = run_ceo_role_dispatch(options)
            dispatch = result["role_dispatch"]
            print(f"Role dispatch: {result['paths']['role_dispatch']}")
            print(f"Role dispatch report: {result['paths']['role_dispatch_report']}")
            print(f"Packet dir: {result['paths']['packet_dir']}")
            print(f"Status: {dispatch.get('status')}")
            print(f"Packets: {dispatch.get('packet_count')}")
            print(f"Top task: {dispatch.get('top_task_id') or 'none'}")
            print(f"Top role: {dispatch.get('top_role_id') or 'none'}")
            print(f"Top packet: {dispatch.get('top_packet_path') or 'none'}")
            print(f"Top result mode: {dispatch.get('top_result_resolution_mode') or 'none'}")
            print(f"Top requires manual gate: {dispatch.get('top_requires_manual_gate')}")
            print(f"Top closure command: {dispatch.get('top_closure_command') or 'none'}")
            print(f"Top autonomous task: {dispatch.get('top_autonomous_task_id') or 'none'}")
            print(f"Top autonomous packet: {dispatch.get('top_autonomous_packet_path') or 'none'}")
            print(f"Top autonomous result command: {dispatch.get('top_autonomous_next_role_result_command') or 'none'}")
            print(f"Next role result command: {dispatch.get('next_role_result_command') or 'none'}")
            return 0
        if action == "role-result":
            result = run_ceo_role_result(
                options,
                task_id=args.task_id,
                status=args.status,
                result_path=args.result_path,
            )
            print(f"Role task ledger: {result['paths']['role_task_ledger']}")
            print(f"Role result validation: {result['paths']['role_result_validation']}")
            print(f"Task: {result['result']['task_id']}")
            print(f"Status: {result['result']['status']}")
            print(f"Validation: {result['result'].get('validation_status')}")
            return 0
        if action == "org-progress-score":
            result = run_ceo_org_progress_score(options)
            scorecard = result["org_progress_score"]
            print(f"Org progress score: {result['paths']['org_progress_score']}")
            print(f"Org progress score report: {result['paths']['org_progress_score_report']}")
            print(f"Status: {scorecard.get('status')}")
            print(f"Score: {scorecard.get('org_progress_score')}")
            print(f"Action scope: {scorecard.get('action_scope') or 'org_progress_diagnostic_only'}")
            print(f"Dispatch authority: {scorecard.get('dispatch_authority') or 'not_granted_by_org_progress_score'}")
            print(f"Pending: {scorecard.get('pending_task_count')}")
            print(f"Blocked: {scorecard.get('blocked_task_count')}")
            print(f"Completed: {scorecard.get('completed_task_count')}")
            print(f"Accepted completed: {scorecard.get('accepted_completed_count')}")
            print(f"Merge receipts: {scorecard.get('merge_receipt_count')}")
            print(f"Completed without merge: {scorecard.get('completed_without_merge_count')}")
            print(f"Decision deltas: {scorecard.get('decision_delta_count')}")
            print(f"Fake progress flags: {scorecard.get('fake_progress_flags') or []}")
            print(f"Top blocked task: {scorecard.get('top_blocked_task_id') or 'none'}")
            print(f"Top blocked next action: {scorecard.get('top_blocked_next_action') or 'none'}")
            print(f"Next action: {scorecard.get('next_action')}")
            return 0
        if action == "capability-backlog":
            result = run_ceo_capability_backlog(options)
            backlog = result["backlog"]
            print(f"Capability backlog: {result['paths']['backlog']}")
            print(f"Backlog report: {result['paths']['backlog_report']}")
            print(f"Status: {backlog.get('status')}")
            print(f"Items: {backlog.get('backlog_count')}")
            return 0
        if action == "replay":
            result = run_ceo_replay(options)
            replay = result["replay"]
            print(f"CEO replay: {result['paths']['replay']}")
            print(f"CEO replay report: {result['paths']['replay_report']}")
            print(f"Status: {replay.get('status')}")
            print(f"Actions: {replay.get('action_count')}")
            print(f"Issues: {replay.get('issues') or []}")
            return 0 if replay.get("status") == "replayable" else 1
        if action == "resumption-brief":
            result = run_ceo_resumption_brief(options)
            brief = result["brief"]
            print(f"CEO resumption brief: {result['paths']['resumption_brief']}")
            print(f"CEO resumption brief report: {result['paths']['resumption_brief_report']}")
            print(f"Resume status: {brief.get('resume_status')}")
            print(f"Next command: {brief.get('next_command')}")
            print(f"Preflight blockers: {brief.get('preflight_blockers') or []}")
            print(f"Trace grade: {brief.get('trace_grade_status') or 'none'}")
            print(f"Trace score: {brief.get('trace_grade_score') if brief.get('trace_grade_score') != '' else 'n/a'}")
            print(f"Trace recommended next action: {brief.get('trace_grade_recommended_next_action') or 'none'}")
            print(
                "Trace manual data import required: "
                f"{brief.get('trace_grade_manual_data_import_required') if brief.get('trace_grade_manual_data_import_required') != '' else 'n/a'}"
            )
            print(f"Trace issues: {brief.get('trace_grade_issues') or []}")
            return 0 if brief.get("resume_status") in {"safe_for_one_bound_action", "diagnostic_advisory_before_extended_autonomy"} else 1
        if action == "artifact-coherence":
            result = run_ceo_artifact_coherence(options)
            coherence = result["coherence"]
            print(f"CEO artifact coherence: {result['paths']['artifact_coherence']}")
            print(f"CEO artifact coherence report: {result['paths']['artifact_coherence_report']}")
            print(f"Status: {coherence.get('status')}")
            print(f"Issues: {coherence.get('issue_count')}")
            print(f"Hard issues: {coherence.get('hard_issue_count', 0)}")
            print(f"Advisory issues: {coherence.get('advisory_issue_count', 0)}")
            return 0 if coherence.get("status") != "fail" else 1
        if action == "run-index":
            result = run_ceo_run_index(options, limit=args.limit)
            index = result["run_index"]
            print(f"CEO run index: {result['paths']['run_index']}")
            print(f"CEO run index report: {result['paths']['run_index_report']}")
            print(f"Status: {index.get('status')}")
            print(f"Run count: {index.get('run_count')}")
            print(f"Status counts: {index.get('status_counts')}")
            latest = (index.get("runs", []) or [{}])[0]
            if latest:
                print(f"Latest run: {latest.get('run_id')}")
                print(f"Latest status: {latest.get('status')}")
                print(f"Latest trace grade: {latest.get('trace_grade_status') or 'missing_trace_grade'}")
                print(f"Latest trace score: {latest.get('trace_grade_score') if latest.get('trace_grade_score') != '' else 'n/a'}")
                print(f"Latest trace recommended next action: {latest.get('trace_grade_recommended_next_action') or 'none'}")
                print(
                    "Latest trace manual data import required: "
                    f"{latest.get('trace_grade_manual_data_import_required') if latest.get('trace_grade_manual_data_import_required') != '' else 'n/a'}"
                )
                if latest.get("trace_grade_issues"):
                    print(f"Latest trace issues: {latest.get('trace_grade_issues')}")
                print(f"Latest artifact coherence: {latest.get('artifact_coherence_status') or 'none'}")
                print(f"Latest artifact coherence top issue: {latest.get('artifact_coherence_top_issue') or 'none'}")
                print(
                    "Latest artifact coherence top issue severity: "
                    f"{latest.get('artifact_coherence_top_issue_severity') or 'unknown'}"
                )
                print(f"Latest data gate: {latest.get('data_gate_brief_status') or 'missing_data_gate_brief'}")
                if latest.get("data_gate_brief_status") and latest.get("data_gate_brief_status") != "missing_data_gate_brief":
                    print(f"Latest data gate safe fresh validation: {latest.get('data_gate_safe_to_run_fresh_validation')}")
                    print(f"Latest data gate CSV requirements: {latest.get('data_gate_csv_requirement_count')}")
                    print(f"Latest data gate blocked candidates: {latest.get('data_gate_blocked_candidate_count')}")
                    print(f"Latest data gate role blockers: {latest.get('data_gate_role_blocker_count')}")
                    print(f"Latest data gate next action: {latest.get('data_gate_next_action') or 'none'}")
                    print(f"Latest data gate next verification: {latest.get('data_gate_next_verification_command') or 'none'}")
                print(
                    "Latest sidecar learning ledger: "
                    f"{latest.get('sidecar_learning_status') or 'missing_sidecar_candidate_learning_ledger'}"
                )
                if latest.get("sidecar_learning_status") and latest.get(
                    "sidecar_learning_status"
                ) != "missing_sidecar_candidate_learning_ledger":
                    print(f"Latest sidecar learning candidates: {latest.get('sidecar_learning_candidate_count')}")
                    print(
                        "Latest sidecar learning lead/control/archive/review/blocked: "
                        f"{latest.get('sidecar_learning_lead_count')}/"
                        f"{latest.get('sidecar_learning_control_count')}/"
                        f"{latest.get('sidecar_learning_archive_count')}/"
                        f"{latest.get('sidecar_learning_review_count')}/"
                        f"{latest.get('sidecar_learning_blocked_count')}"
                    )
                    if latest.get("sidecar_learning_lead_candidate"):
                        print(f"Latest sidecar learning lead candidate: {latest.get('sidecar_learning_lead_candidate')}")
                        print(f"Latest sidecar learning lead next required: {latest.get('sidecar_learning_lead_next_required_action') or 'none'}")
                        print(f"Latest sidecar learning lead authority: {latest.get('sidecar_learning_lead_validation_authority') or 'none'}")
                    if latest.get("sidecar_learning_control_candidate"):
                        print(f"Latest sidecar learning control candidate: {latest.get('sidecar_learning_control_candidate')}")
                        print(f"Latest sidecar learning control reason: {latest.get('sidecar_learning_control_reason') or 'none'}")
                        print(f"Latest sidecar learning control next allowed: {latest.get('sidecar_learning_control_next_allowed_action') or 'none'}")
                    if latest.get("sidecar_learning_archive_candidate"):
                        print(f"Latest sidecar learning archive candidate: {latest.get('sidecar_learning_archive_candidate')}")
                        print(f"Latest sidecar learning archive reason: {latest.get('sidecar_learning_archive_reason') or 'none'}")
                        print(f"Latest sidecar learning archive next allowed: {latest.get('sidecar_learning_archive_next_allowed_action') or 'none'}")
                if latest.get("sidecar_post_data_playbook_status"):
                    print(f"Latest sidecar post-data playbook: {latest.get('sidecar_post_data_playbook_status')}")
                    print(
                        "Latest sidecar post-data action: "
                        f"{latest.get('sidecar_post_data_playbook_current_required_action') or 'none'}"
                    )
                    print(
                        "Latest sidecar post-data candidates: "
                        f"{latest.get('sidecar_post_data_playbook_candidate_count') if latest.get('sidecar_post_data_playbook_candidate_count') != '' else 'n/a'}"
                    )
                    print(
                        "Latest sidecar post-data visual-label status/gate: "
                        f"{latest.get('sidecar_post_data_playbook_visual_label_completion_status') or 'none'}/"
                        f"{latest.get('sidecar_post_data_playbook_visual_label_gate_passed')}"
                    )
                    print(
                        "Latest sidecar post-data blockers: "
                        f"{latest.get('sidecar_post_data_playbook_pre_validation_blockers') or 'none'}"
                    )
                    print(
                        "Latest sidecar post-data can-execute candidates: "
                        f"{latest.get('sidecar_post_data_playbook_can_execute_count')}"
                    )
                    if latest.get("sidecar_post_data_playbook"):
                        print(f"Latest sidecar post-data playbook path: {latest.get('sidecar_post_data_playbook')}")
                    if latest.get("sidecar_post_data_playbook_report"):
                        print(
                            "Latest sidecar post-data playbook report: "
                            f"{latest.get('sidecar_post_data_playbook_report')}"
                        )
                if latest.get("sidecar_visual_review_top_candidate"):
                    print(f"Latest sidecar visual-review top candidate: {latest.get('sidecar_visual_review_top_candidate')}")
                    print(f"Latest sidecar visual-review top role: {latest.get('sidecar_visual_review_top_product_role') or 'none'}")
                    print(f"Latest sidecar visual-review top focus: {latest.get('sidecar_visual_review_top_focus') or 'none'}")
                    print(f"Latest sidecar visual-review top priority: {latest.get('sidecar_visual_review_top_priority')}")
                    if latest.get("sidecar_visual_review_top_gallery"):
                        print(f"Latest sidecar visual-review top gallery: {latest.get('sidecar_visual_review_top_gallery')}")
                    if latest.get("sidecar_visual_review_top_labels_with_images"):
                        print(f"Latest sidecar visual-review top labels: {latest.get('sidecar_visual_review_top_labels_with_images')}")
                if latest.get("sidecar_quality_status"):
                    print(f"Latest sidecar quality status: {latest.get('sidecar_quality_status')}")
                    print(
                        "Latest sidecar quality hard/advisory issues: "
                        f"{latest.get('sidecar_quality_hard_issue_count')}/"
                        f"{latest.get('sidecar_quality_advisory_issue_count')}"
                    )
                    if latest.get("sidecar_quality_advisory_issue_summary"):
                        print(
                            "Latest sidecar quality advisory summary: "
                            f"{latest.get('sidecar_quality_advisory_issue_summary')}"
                        )
                print(
                    "Latest evidence debt register: "
                    f"{latest.get('evidence_debt_status') or 'missing_evidence_debt_register'}"
                )
                if latest.get("evidence_debt_status") and latest.get("evidence_debt_status") != "missing_evidence_debt_register":
                    print(f"Latest evidence debt count: {latest.get('evidence_debt_count')}")
                    print(
                        "Latest evidence debt candidate/global/archive: "
                        f"{latest.get('evidence_debt_candidate_count')}/"
                        f"{latest.get('evidence_debt_global_count')}/"
                        f"{latest.get('evidence_debt_archived_candidate_count')}"
                    )
                    print(f"Latest evidence debt next action: {latest.get('evidence_debt_next_action') or 'none'}")
                    print(
                        "Latest evidence debt current handoff: "
                        f"{latest.get('evidence_debt_current_runtime_handoff_action') or 'none'}"
                    )
                    print(
                        "Latest evidence debt handoff status: "
                        f"{latest.get('evidence_debt_current_runtime_handoff_status') or 'none'}"
                    )
                print(f"Latest effective operator status: {latest.get('effective_operator_status') or 'unknown_or_diagnostic'}")
                print(f"Latest manual gate active: {latest.get('manual_gate_active')}")
                print(f"Latest effective runtime action: {latest.get('decision_quality_effective_runtime_action') or 'none'}")
                print(f"Latest runtime blocked: {latest.get('decision_quality_runtime_blocked')}")
                print(f"Latest runtime block reason: {latest.get('decision_quality_runtime_block_reason') or 'none'}")
                print(f"Latest decision: {latest.get('decision_quality_selected_action') or 'none'}")
                print(f"Latest decision advisory route: {latest.get('decision_quality_selected_strategic_route_advisory') or 'none'}")
                print(f"Latest decision authority: {latest.get('decision_quality_runtime_authority') or 'none'}")
                print(f"Latest decision can execute: {latest.get('decision_quality_executable_can_execute_now')}")
                print(f"Latest decision blocked by: {latest.get('decision_quality_selected_action_blocked_by') or 'none'}")
                if latest.get("approval_top_pending_id"):
                    print(f"Latest top approval: {latest.get('approval_top_pending_id')}")
                    print(f"Latest top approval kind: {latest.get('approval_top_pending_kind') or 'none'}")
                    print(f"Latest top approval reason: {latest.get('approval_top_pending_reason') or 'none'}")
                    print(f"Latest top approval source: {latest.get('approval_top_pending_source') or 'none'}")
                    print(
                        "Latest top approval required user decision: "
                        f"{latest.get('approval_top_pending_required_user_decision') or 'none'}"
                    )
                    print(f"Latest top approval authority: {latest.get('approval_top_pending_authority') or 'none'}")
                    print(f"Latest top approval fingerprint: {latest.get('approval_top_pending_fingerprint') or 'none'}")
                if latest.get("role_top_blocked_task_id"):
                    print(f"Latest top blocked role task: {latest.get('role_top_blocked_task_id')}")
                    print(f"Latest top blocked role: {latest.get('role_top_blocked_role_id') or 'none'}")
                    print(f"Latest top blocked role mode: {latest.get('role_top_blocked_result_resolution_mode') or 'none'}")
                    print(f"Latest top blocked role validation: {latest.get('role_top_blocked_validation_status') or 'none'}")
                    print(f"Latest top blocked role closure: {latest.get('role_top_blocked_closure_command') or 'none'}")
                    print(f"Latest top blocked role review: {latest.get('role_top_blocked_review_status') or 'none'}")
                    print(f"Latest top blocked role result: {latest.get('role_top_blocked_result_path') or 'none'}")
                    print(f"Latest top blocked role next action: {latest.get('role_top_blocked_next_action') or 'none'}")
                    print(f"Latest top blocked role finding: {latest.get('role_top_blocked_finding') or 'none'}")
                print(f"Latest next command: {latest.get('next_command')}")
            return 0
        if action == "dispatch-receipt":
            result = run_ceo_dispatch_receipt(options)
            receipt = result["receipt"]
            print(f"CEO dispatch receipt: {result['paths']['dispatch_receipt']}")
            print(f"CEO dispatch receipt report: {result['paths']['dispatch_receipt_report']}")
            print(f"Status: {receipt.get('status')}")
            print(f"Safe to dispatch: {receipt.get('safe_to_dispatch')}")
            print(f"Reason: {receipt.get('reason')}")
            return 0 if receipt.get("safe_to_dispatch") else 1
        if action == "blocker-stack":
            result = run_ceo_blocker_stack(options)
            stack = result["stack"]
            print(f"CEO blocker stack: {result['paths']['blocker_stack']}")
            print(f"CEO blocker stack report: {result['paths']['blocker_stack_report']}")
            print(f"Status: {stack.get('status')}")
            print(f"Top blocker: {stack.get('top_blocker') or 'none'}")
            print(f"Top blocker evidence: {stack.get('top_blocker_evidence') or 'none'}")
            print(f"Next command: {stack.get('next_command')}")
            return 0 if stack.get("status") == "clear_for_one_bound_action" else 1
        if action == "incident-register":
            result = run_ceo_operating_incident_register(options)
            register = result["register"]
            print(f"CEO incident register: {result['paths']['incident_register']}")
            print(f"CEO incident register report: {result['paths']['incident_register_report']}")
            print(f"Status: {register.get('status')}")
            print(f"Incidents: {register.get('incident_count')}")
            return 0
        if action == "repair-plan":
            result = run_ceo_repair_plan(options)
            plan = result["repair_plan"]
            print(f"CEO repair plan: {result['paths']['repair_plan']}")
            print(f"CEO repair plan report: {result['paths']['repair_plan_report']}")
            print(f"Status: {plan.get('status')}")
            print(f"Repairs: {plan.get('repair_count')}")
            print(f"Runnable repairs: {plan.get('runnable_repair_count', plan.get('autonomous_repair_count'))}")
            print(f"Diagnostic refreshes: {plan.get('diagnostic_refresh_count', 0)}")
            print(f"Top repair: {plan.get('top_repair') or 'none'}")
            print(f"Top repair kind: {plan.get('top_repair_kind') or 'none'}")
            print(f"Next command: {plan.get('next_command')}")
            return 0
        if action == "repair-apply":
            result = run_ceo_repair_apply(options, repair_key=args.repair_key)
            apply_result = result["repair_apply"]
            print(f"CEO repair apply: {result['paths']['repair_apply']}")
            print(f"CEO repair apply report: {result['paths']['repair_apply_report']}")
            print(f"Status: {apply_result.get('status')}")
            print(f"Repair key: {apply_result.get('repair_key')}")
            print(f"Command kind: {apply_result.get('command_kind') or 'n/a'}")
            print(f"Action attempted: {apply_result.get('action_attempted')}")
            print(f"Action executed: {apply_result.get('action_executed')}")
            print(f"Repair closed: {apply_result.get('repair_closed')}")
            print(f"Reason: {apply_result.get('reason')}")
            return 0 if apply_result.get("action_executed") else 1
        if action == "eval-suite":
            result = run_ceo_eval_suite(options)
            eval_suite = result["eval_suite"]
            print(f"CEO eval suite: {result['paths']['eval_suite']}")
            print(f"CEO eval suite report: {result['paths']['eval_suite_report']}")
            print(f"Replay: {result['paths']['replay']}")
            print(f"Eval fixtures: {result['paths']['eval_fixtures']}")
            print(f"Status: {eval_suite.get('status')}")
            print(f"Score: {eval_suite.get('score')}")
            readiness = (eval_suite.get("nine_nine_readiness", {}) or {})
            print(f"9.9 readiness: {readiness.get('status')}")
            print(f"9.9 blocking cases: {readiness.get('blocking_case_ids') or []}")
            print(f"9.9 advisory cases: {readiness.get('advisory_case_ids') or []}")
            failed_cases = [item for item in eval_suite.get("cases", []) or [] if item.get("status") != "pass"]
            for item in failed_cases:
                print(
                    "Failed case: "
                    f"{item.get('case_id')} severity={item.get('severity')} "
                    f"next={item.get('next_action')} evidence={item.get('evidence')}"
                )
            return 0 if eval_suite.get("status") != "fail" else 1
        if action == "eval-fixtures":
            result = run_ceo_eval_fixtures(options)
            fixtures = result["fixtures"]
            print(f"CEO eval fixtures: {result['paths']['eval_fixtures']}")
            print(f"CEO eval fixtures report: {result['paths']['eval_fixtures_report']}")
            print(f"Status: {fixtures.get('status')}")
            print(f"Cases: {fixtures.get('case_count')}")
            print(f"Failed: {fixtures.get('failed_case_count')}")
            return 0 if fixtures.get("status") == "pass" else 1
    except Exception as exc:
        print(f"CEO {action} failed: {exc}")
        return 1
    print(f"Unknown ceo action: {action}")
    return 1


def _latest_director_snapshot(args: argparse.Namespace) -> tuple[Path, Path]:
    evidence_mart = getattr(args, "evidence_mart", None)
    belief_graph = getattr(args, "belief_graph", None)
    if evidence_mart and belief_graph:
        return Path(evidence_mart), Path(belief_graph)

    candidate_roots: list[Path] = []
    run_id = getattr(args, "run_id", None)
    if run_id:
        candidate_roots.append(Path(getattr(args, "ops_report_root", LAB_OPS_REPORT_ROOT)) / run_id / "director")
    candidate_roots.append(Path(getattr(args, "director_report_root", DEFAULT_DIRECTOR_REPORT_ROOT)))

    candidates: list[Path] = []
    for root in candidate_roots:
        if root.exists():
            candidates.extend(root.glob("**/evidence_mart.yaml"))
    if not candidates:
        raise FileNotFoundError("No evidence_mart.yaml found. Pass --evidence-mart and --belief-graph explicitly.")
    mart_path = sorted(candidates, key=lambda path: path.stat().st_mtime)[-1]
    graph_path = mart_path.parent / "belief_graph.yaml"
    if not graph_path.exists():
        raise FileNotFoundError(f"No belief_graph.yaml next to {mart_path}")
    return mart_path, graph_path


def _governance_output_dir(args: argparse.Namespace, default_name: str) -> Path:
    output_dir = getattr(args, "output_dir", None)
    if output_dir:
        return Path(output_dir)
    run_id = getattr(args, "run_id", None)
    if run_id:
        return Path(getattr(args, "ops_report_root", LAB_OPS_REPORT_ROOT)) / run_id / "governance" / "manual"
    return Path("reports") / default_name


def _latest_lane_assignment_path(args: argparse.Namespace) -> Path:
    run_id = getattr(args, "run_id", None)
    candidates: list[Path] = []
    if run_id:
        root = Path(getattr(args, "ops_report_root", LAB_OPS_REPORT_ROOT)) / run_id / "governance"
        if root.exists():
            candidates.extend(root.glob("block_*/lane_assignment.yaml"))
    candidates.extend(Path("reports/lab_ops").glob("*/governance/block_*/lane_assignment.yaml"))
    if not candidates:
        raise FileNotFoundError("No lane_assignment.yaml found. Pass --lane-assignment explicitly.")
    return sorted(candidates, key=lambda path: path.stat().st_mtime)[-1]


def _runtime_queue_for_recovery_cli(args: argparse.Namespace) -> Path:
    if getattr(args, "runtime_queue", None):
        return Path(args.runtime_queue)
    run_id = getattr(args, "run_id", None)
    if run_id:
        return Path(getattr(args, "ops_runtime_root", LAB_OPS_RUNTIME_ROOT)) / run_id / "runtime_queue.yaml"
    raise ValueError("--apply requires --run-id or --runtime-queue")


def _default_recovery_grid_dir(args: argparse.Namespace, output_dir: Path) -> Path:
    if getattr(args, "generated_grid_dir", None):
        return Path(args.generated_grid_dir)
    run_id = getattr(args, "run_id", None)
    if run_id:
        return Path(getattr(args, "ops_runtime_root", LAB_OPS_RUNTIME_ROOT)) / run_id / "generated_grids" / "recovery"
    return output_dir / "generated_grids"


def _existing_ids_for_recovery_cli(args: argparse.Namespace) -> set[str]:
    existing: set[str] = set()
    runtime_queue = None
    try:
        runtime_queue = _runtime_queue_for_recovery_cli(args)
    except ValueError:
        runtime_queue = None
    if runtime_queue and runtime_queue.exists():
        try:
            payload = load_lab_queue(runtime_queue)
        except Exception:
            payload = {"queue": []}
        existing.update(str(item.get("id", "")) for item in payload.get("queue", []))
    state_path = None
    if getattr(args, "state", None):
        state_path = Path(args.state)
    elif getattr(args, "run_id", None):
        state_path = Path(getattr(args, "ops_runtime_root", LAB_OPS_RUNTIME_ROOT)) / args.run_id / "lab_state.json"
    if state_path and state_path.exists():
        try:
            state = load_lab_state(state_path)
        except Exception:
            state = {}
        existing.update(str(item) for item in state.get("completed_hypothesis_ids", []))
    return existing


def blocker_audit_command(args: argparse.Namespace) -> int:
    try:
        evidence_mart, belief_graph = _latest_director_snapshot(args)
        result = run_blocker_audit(
            evidence_mart_path=evidence_mart,
            belief_graph_path=belief_graph,
            output_dir=_governance_output_dir(args, "blocker_audit"),
        )
        audit = result["audit"]
        print(f"Audited blocker candidates: {audit.get('audited_count')}")
        print(f"Decisions: {audit.get('decision_counts')}")
        print(f"Blocker audit: {result['paths']['audit']}")
        return 0
    except Exception as exc:
        print(f"Blocker audit failed: {exc}")
        return 1


def lane_router_command(args: argparse.Namespace) -> int:
    try:
        _evidence_mart, belief_graph = _latest_director_snapshot(args)
        result = run_lane_assignment(
            belief_graph_path=belief_graph,
            output_dir=_governance_output_dir(args, "lane_router"),
            blocker_audit_path=Path(args.blocker_audit) if getattr(args, "blocker_audit", None) else None,
            meta_scorecard_path=Path(args.meta_scorecard) if getattr(args, "meta_scorecard", None) else None,
        )
        assignment = result["assignment"]
        print(f"Assignments: {assignment.get('assignment_count')}")
        print(f"Open lanes: {', '.join(assignment.get('open_lanes', [])) or 'none'}")
        print(f"Lane assignment: {result['paths']['assignment']}")
        return 0
    except Exception as exc:
        print(f"Lane router failed: {exc}")
        return 1


def lane_router_recover_command(args: argparse.Namespace) -> int:
    try:
        evidence_mart_path, belief_graph_path = _latest_director_snapshot(args)
        output_dir = _governance_output_dir(args, "lane_recovery")
        output_dir.mkdir(parents=True, exist_ok=True)
        lane_assignment_path = Path(args.lane_assignment) if getattr(args, "lane_assignment", None) else _latest_lane_assignment_path(args)
        mart = load_yaml_file(evidence_mart_path)
        belief_graph = load_yaml_file(belief_graph_path)
        lane_assignment = load_yaml_file(lane_assignment_path)
        output_queue = Path(args.output_queue) if getattr(args, "output_queue", None) else output_dir / "recovery_candidate_queue.yaml"
        generated_grid_dir = _default_recovery_grid_dir(args, output_dir)
        plan = design_lane_recovery_experiments(
            mart,
            belief_graph,
            lane_assignment,
            output_queue_path=output_queue,
            generated_grid_dir=generated_grid_dir,
            max_new_hypotheses=args.max_new_hypotheses,
            source_root=Path(args.source_root),
            existing_hypothesis_ids=_existing_ids_for_recovery_cli(args),
        )
        audit = audit_director_plan(plan, source_root=Path(args.source_root))
        plan_path = output_dir / "recovery_queue_plan.yaml"
        audit_path = output_dir / "recovery_audit.yaml"
        atomic_write_yaml(plan_path, plan)
        atomic_write_yaml(output_queue, plan.get("generated_queue", {}))
        atomic_write_yaml(audit_path, audit)
        runtime_added = 0
        if args.apply:
            if not audit.get("passed"):
                print(f"Recovery audit failed: {audit_path}")
                for error in audit.get("errors", []):
                    print(f"- {error}")
                return 1
            runtime_added = append_queue_to_runtime(_runtime_queue_for_recovery_cli(args), plan.get("generated_queue", {}))
        print(f"Generated recovery items: {plan.get('generated_count')}")
        print(f"Blocked lanes: {len(plan.get('blocked_lanes', []))}")
        print(f"Recovery audit passed: {audit.get('passed')}")
        if args.apply:
            print(f"Runtime queue additions: {runtime_added}")
        print(f"Recovery plan: {plan_path}")
        print(f"Recovery queue: {output_queue}")
        return 0 if audit.get("passed") else 1
    except Exception as exc:
        print(f"Lane recovery failed: {exc}")
        return 1


def validation_governance_command(args: argparse.Namespace) -> int:
    try:
        _evidence_mart, belief_graph = _latest_director_snapshot(args)
        result = run_validation_governance(
            belief_graph_path=belief_graph,
            output_dir=_governance_output_dir(args, "validation_governance"),
            lane_assignment_path=Path(args.lane_assignment) if getattr(args, "lane_assignment", None) else None,
            blocker_audit_path=Path(args.blocker_audit) if getattr(args, "blocker_audit", None) else None,
        )
        governance = result["governance"]
        print(f"Decision counts: {governance.get('decision_counts')}")
        print(f"Product change allowed: {governance.get('product_change_allowed')}")
        print(f"Validation decision: {result['paths']['governance']}")
        return 0
    except Exception as exc:
        print(f"Validation governance failed: {exc}")
        return 1


def research_map_command(args: argparse.Namespace) -> int:
    try:
        evidence_mart, belief_graph = _latest_director_snapshot(args)
        result = run_research_map_update(
            evidence_mart_path=evidence_mart,
            belief_graph_path=belief_graph,
            map_path=Path(args.map_path),
            report_root=Path(args.report_root),
            lane_assignment_path=Path(args.lane_assignment) if getattr(args, "lane_assignment", None) else None,
            blocker_audit_path=Path(args.blocker_audit) if getattr(args, "blocker_audit", None) else None,
            validation_governance_path=Path(args.validation_governance) if getattr(args, "validation_governance", None) else None,
        )
        research_map = result["research_map"]
        print(f"Nodes: {len(research_map.get('nodes', []))}")
        print(f"Edges: {len(research_map.get('edges', []))}")
        print(f"Research map: {result['paths']['map']}")
        print(f"Status: {result['paths']['status']}")
        return 0
    except Exception as exc:
        print(f"Research map update failed: {exc}")
        return 1


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

    obsidian_kg = subparsers.add_parser(
        "obsidian-kg",
        help="Validate, index, compile, or export the Obsidian research knowledge graph.",
    )
    obsidian_kg_subparsers = obsidian_kg.add_subparsers(dest="obsidian_kg_action", required=True)

    kg_validate = obsidian_kg_subparsers.add_parser("validate", help="Validate Obsidian KG notes and links.")
    kg_validate.add_argument("--obsidian-dir", default=str(DEFAULT_OBSIDIAN_DIR), help="Obsidian vault directory.")
    kg_validate.add_argument("--warning-limit", type=int, default=50, help="Maximum warnings to print.")
    kg_validate.set_defaults(func=obsidian_kg_command)

    kg_index = obsidian_kg_subparsers.add_parser("index", help="Export Obsidian KG node/edge tables.")
    kg_index.add_argument("--obsidian-dir", default=str(DEFAULT_OBSIDIAN_DIR), help="Obsidian vault directory.")
    kg_index.add_argument("--output-dir", default=str(DEFAULT_KG_OUTPUT_DIR), help="Generated KG output directory.")
    kg_index.set_defaults(func=obsidian_kg_command)

    kg_audit = obsidian_kg_subparsers.add_parser("audit", help="Write an Obsidian KG memory-quality audit report.")
    kg_audit.add_argument("--obsidian-dir", default=str(DEFAULT_OBSIDIAN_DIR), help="Obsidian vault directory.")
    kg_audit.add_argument("--output-dir", default=str(DEFAULT_KG_OUTPUT_DIR), help="Generated KG output directory.")
    kg_audit.set_defaults(func=obsidian_kg_command)

    kg_compile = obsidian_kg_subparsers.add_parser(
        "compile-queue",
        help="Compile setup-journey notes into a lab-loop hypothesis queue.",
    )
    kg_compile.add_argument("--obsidian-dir", default=str(DEFAULT_OBSIDIAN_DIR), help="Obsidian vault directory.")
    kg_compile.add_argument("--direction", default="bullish", choices=["bullish"], help="Setup direction to compile.")
    kg_compile.add_argument(
        "--output-queue",
        default=str(DEFAULT_OBSIDIAN_QUEUE_PATH),
        help="Generated lab-loop queue YAML path.",
    )
    kg_compile.add_argument(
        "--generated-grid-dir",
        default=str(DEFAULT_OBSIDIAN_GRID_DIR),
        help="Directory for generated grammar grids.",
    )
    kg_compile.add_argument(
        "--min-source-cases",
        type=int,
        default=1,
        help="Minimum linked source cases required before compiling a setup journey.",
    )
    kg_compile.add_argument(
        "--include-research-grammar",
        action="store_true",
        help="Also compile compact bullish candidates from existing research/grammar grids.",
    )
    kg_compile.add_argument(
        "--research-grammar-dir",
        default="research/grammar",
        help="Directory of prior grammar-search grid YAMLs used by --include-research-grammar.",
    )
    kg_compile.add_argument(
        "--max-research-families",
        type=int,
        default=80,
        help="Maximum positive research-memory families to append to the generated queue.",
    )
    kg_compile.add_argument(
        "--max-family-variants",
        type=int,
        default=32,
        help="Maximum compact parameter variants per generated research-memory family before timeframe expansion.",
    )
    kg_compile.set_defaults(func=obsidian_kg_command)

    kg_compile_targeted = obsidian_kg_subparsers.add_parser(
        "compile-targeted-bullish-queue",
        help="Compile the focused bullish setup queue from recent lab findings.",
    )
    kg_compile_targeted.add_argument(
        "--output-queue",
        default=str(DEFAULT_TARGETED_BULLISH_QUEUE_PATH),
        help="Generated targeted bullish lab-loop queue YAML path.",
    )
    kg_compile_targeted.add_argument(
        "--generated-grid-dir",
        default=str(DEFAULT_OBSIDIAN_GRID_DIR),
        help="Directory for generated targeted bullish grammar grids.",
    )
    kg_compile_targeted.set_defaults(func=obsidian_kg_command)

    kg_export = obsidian_kg_subparsers.add_parser(
        "export-evidence",
        help="Export compact lab-loop bullish evidence summaries into Obsidian.",
    )
    kg_export.add_argument("session_dir", help="Lab-loop report session directory containing loop_* outputs.")
    kg_export.add_argument("--obsidian-dir", default=str(DEFAULT_OBSIDIAN_DIR), help="Obsidian vault directory.")
    kg_export.add_argument(
        "--promoted-only",
        dest="include_failed",
        action="store_false",
        help="Only export evidence summaries that passed the bullish contract.",
    )
    kg_export.add_argument("--path-limit", type=int, default=20, help="Maximum written paths to print.")
    kg_export.set_defaults(include_failed=True)
    kg_export.set_defaults(func=obsidian_kg_command)

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

    grammar_search = subparsers.add_parser(
        "grammar-search",
        help="Run automated Signal Grammar Lab parameter search across timeframes.",
    )
    grammar_search.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
    grammar_search.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
    grammar_search.add_argument(
        "--report-dir",
        default="reports/grammar_search",
        help="Directory for grammar-search CSV, HTML, and manifest outputs.",
    )
    grammar_search.add_argument("--obsidian-dir", default="obsidian", help="Obsidian vault directory for markdown reports.")
    grammar_search.add_argument(
        "--grid",
        default=DEFAULT_GRAMMAR_SEARCH_GRID,
        help="Grammar search rule grid YAML.",
    )
    grammar_search.add_argument(
        "--timeframes",
        nargs="+",
        default=["1d", "12h", "4h", "1h"],
        help="Timeframe suffixes to search independently.",
    )
    grammar_search.add_argument(
        "--min-sample-size",
        type=int,
        default=20,
        help="Minimum independent event count before a variant can classify beyond inconclusive.",
    )
    grammar_search.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the candidate event before forward-return measurement starts.",
    )
    grammar_search.add_argument(
        "--cooldown-bars",
        type=int,
        default=None,
        help="Optional shared cooldown bars for all timeframes. Defaults to timeframe-scaled values.",
    )
    grammar_search.add_argument(
        "--strict-referee",
        action="store_true",
        help="Also write strict baseline/null validation for grammar-search variants.",
    )
    grammar_search.add_argument(
        "--strict-null-iterations",
        type=int,
        default=300,
        help="Matched random-null iterations for --strict-referee.",
    )
    grammar_search.add_argument(
        "--strict-random-seed",
        type=int,
        default=29,
        help="Random seed for --strict-referee matched-null sampling.",
    )
    grammar_search.set_defaults(func=grammar_search_command)

    grammar_review_packet = subparsers.add_parser(
        "grammar-review-packet",
        help="Build a human-review label sheet and packet from grammar-search queue or record rows.",
    )
    grammar_review_packet.add_argument(
        "--queue-csv",
        default="reports/grammar_search/grammar_search_chart_review_queue.csv",
        help="Input grammar_search_chart_review_queue.csv or grammar_search_variant_records.csv path.",
    )
    grammar_review_packet.add_argument(
        "--output-dir",
        default="reports/grammar_search/review_packet",
        help="Directory for human_review_labels.csv and human_review_packet.md.",
    )
    grammar_review_packet.add_argument(
        "--title",
        default="Grammar Search Review Packet",
        help="Markdown title for the generated review packet.",
    )
    grammar_review_packet.add_argument(
        "--max-cases",
        type=int,
        default=48,
        help="Maximum total cases to include in the review packet.",
    )
    grammar_review_packet.add_argument(
        "--max-cases-per-bucket",
        type=int,
        default=8,
        help="Maximum cases to include from each review bucket.",
    )
    grammar_review_packet.set_defaults(func=grammar_review_packet_command)

    grammar_review_gallery = subparsers.add_parser(
        "grammar-review-gallery",
        help="Render chart images and a gallery from a grammar-review label sheet.",
    )
    grammar_review_gallery.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
    grammar_review_gallery.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
    grammar_review_gallery.add_argument(
        "--labels-csv",
        default="reports/grammar_search/review_packet/human_review_labels.csv",
        help="Input human_review_labels.csv path from grammar-review-packet.",
    )
    grammar_review_gallery.add_argument(
        "--output-dir",
        default="reports/grammar_search/review_packet",
        help="Directory for human_review_labels_with_images.csv, gallery.md, and images/.",
    )
    grammar_review_gallery.add_argument(
        "--lookback-bars",
        type=int,
        default=80,
        help="Bars to show before each reviewed grammar event.",
    )
    grammar_review_gallery.add_argument(
        "--forward-bars",
        type=int,
        default=0,
        help="Bars to show after each reviewed grammar event. Use 0 to match each row's review horizon.",
    )
    grammar_review_gallery.add_argument(
        "--max-images",
        type=int,
        default=48,
        help="Maximum label rows to render into images.",
    )
    grammar_review_gallery.set_defaults(func=grammar_review_gallery_command)

    indicator_behavior_search = subparsers.add_parser(
        "indicator-behavior-search",
        help="Run encoded indicator-behavior concept search across timeframes.",
    )
    indicator_behavior_search.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
    indicator_behavior_search.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
    indicator_behavior_search.add_argument(
        "--report-dir",
        default="reports/indicator_behavior/search",
        help="Directory for indicator-behavior search outputs.",
    )
    indicator_behavior_search.add_argument(
        "--concept-library",
        default=DEFAULT_CONCEPT_LIBRARY,
        help="Indicator behavior concept library YAML.",
    )
    indicator_behavior_search.add_argument(
        "--primitive-registry",
        default=DEFAULT_PRIMITIVE_REGISTRY,
        help="Indicator behavior primitive registry YAML.",
    )
    indicator_behavior_search.add_argument(
        "--timeframes",
        nargs="+",
        default=["1d", "12h", "4h", "1h"],
        help="Timeframe suffixes to search independently.",
    )
    indicator_behavior_search.add_argument(
        "--priority",
        choices=["first_batch", "backlog", "all"],
        default="first_batch",
        help="Concept priority bucket to run.",
    )
    indicator_behavior_search.add_argument(
        "--context-windows",
        nargs="+",
        type=int,
        default=[10],
        help="Primitive context windows, in bars.",
    )
    indicator_behavior_search.add_argument(
        "--min-sample-size",
        type=int,
        default=20,
        help="Minimum independent event count before a variant can classify beyond inconclusive.",
    )
    indicator_behavior_search.add_argument(
        "--entry-lag-bars",
        type=int,
        default=1,
        help="Bars after the candidate event before forward-return measurement starts.",
    )
    indicator_behavior_search.add_argument(
        "--cooldown-bars",
        type=int,
        default=None,
        help="Optional shared cooldown bars for all timeframes. Defaults to timeframe-scaled values.",
    )
    indicator_behavior_search.add_argument(
        "--strict-referee",
        action="store_true",
        help="Also write strict baseline/null validation for indicator-behavior variants.",
    )
    indicator_behavior_search.add_argument(
        "--strict-null-iterations",
        type=int,
        default=300,
        help="Matched random-null iterations for --strict-referee.",
    )
    indicator_behavior_search.add_argument(
        "--strict-random-seed",
        type=int,
        default=29,
        help="Random seed for --strict-referee matched-null sampling.",
    )
    indicator_behavior_search.set_defaults(func=indicator_behavior_search_command)

    lab_loop = subparsers.add_parser(
        "lab-loop",
        help="Run or inspect the autonomous Riskflow lab-loop runner.",
    )
    lab_subparsers = lab_loop.add_subparsers(dest="lab_loop_action", required=True)

    def add_lab_loop_common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--queue", default=str(DEFAULT_QUEUE_PATH), help="Seed hypothesis queue YAML.")
        command.add_argument(
            "--runtime-queue",
            default=str(DEFAULT_RUNTIME_QUEUE_PATH),
            help="Runtime queue YAML updated during autonomous runs.",
        )
        command.add_argument("--state", default=str(DEFAULT_STATE_PATH), help="Lab-loop state JSON path.")
        command.add_argument("--report-root", default=str(DEFAULT_REPORT_ROOT), help="Lab-loop report root.")
        command.add_argument(
            "--concept-scoreboard",
            default=str(DEFAULT_CONCEPT_SCOREBOARD_PATH),
            help="Durable concept scoreboard YAML.",
        )
        command.add_argument(
            "--objective",
            choices=sorted(LAB_OBJECTIVES),
            default="general",
            help="Lab research objective. Use bullish-positive to require true positive setup evidence.",
        )

    def add_lab_loop_supervisor_args(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--evidence-ledger",
            default=str(DEFAULT_EVIDENCE_LEDGER_PATH),
            help="Durable meta-supervisor evidence ledger YAML.",
        )
        command.add_argument(
            "--supervisor-policy",
            default=str(DEFAULT_SUPERVISOR_POLICY_PATH),
            help="Optional meta-supervisor policy YAML path.",
        )
        command.add_argument(
            "--max-generation",
            type=int,
            default=3,
            help="Cool non-validation hypotheses deeper than this lineage generation.",
        )
        command.add_argument(
            "--max-same-root-per-epoch",
            type=int,
            default=2,
            help="Maximum planned next-epoch slots from one concept root.",
        )
        command.add_argument(
            "--min-bullish-share",
            type=float,
            default=0.35,
            help="Minimum next-epoch slot share for bullish setup tests when eligible.",
        )
        command.add_argument(
            "--validation-share",
            type=float,
            default=0.30,
            help="Minimum next-epoch slot share reserved for validation gates.",
        )
        command.add_argument(
            "--min-new-bullish-roots",
            type=int,
            default=3,
            help="Bullish-positive mode: minimum distinct new bullish roots to prefer per epoch when available.",
        )
        command.add_argument(
            "--max-same-setup-class-per-epoch",
            type=int,
            default=1,
            help="Bullish-positive mode: cap planned slots from one setup_class per epoch.",
        )
        command.add_argument(
            "--weak-family-attempt-limit",
            type=int,
            default=3,
            help="Bullish-positive mode: attempts without a contract pass before cooling a family.",
        )
        command.add_argument(
            "--weak-family-cooldown-loops",
            type=int,
            default=25,
            help="Bullish-positive mode: loop cooldown applied to weak families.",
        )
        command.add_argument(
            "--max-non-contract-reseed-source-generation",
            type=int,
            default=0,
            help="Bullish-positive mode: deepest non-contract generation allowed as a reseed source.",
        )
        command.add_argument(
            "--max-primitive-overlap",
            type=float,
            default=0.70,
            help="Bullish-positive mode: avoid adding discovery slots above this primitive Jaccard overlap.",
        )
        command.add_argument(
            "--max-reseed-per-epoch",
            type=int,
            default=5,
            help="Maximum runnable hypotheses the supervisor can create when the queue is exhausted.",
        )
        command.add_argument(
            "--max-reseeds-per-root",
            type=int,
            default=2,
            help="Bullish-positive mode: maximum meta-supervisor reseeds allowed from one canonical root.",
        )
        command.add_argument(
            "--max-reseed-signature-attempts",
            type=int,
            default=1,
            help="Maximum reseeds allowed for the same root/family/params signature.",
        )
        command.add_argument(
            "--no-reseed",
            dest="reseed_when_empty",
            action="store_false",
            help="Do not create bounded supervisor reseeds when the runnable queue is exhausted.",
        )
        command.set_defaults(reseed_when_empty=True)

    def add_lab_loop_execution_args(command: argparse.ArgumentParser) -> None:
        command.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
        command.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
        command.add_argument(
            "--timeframes",
            nargs="+",
            default=["1d", "12h", "4h", "1h"],
            help="Timeframes to run each executable hypothesis across.",
        )
        command.add_argument("--max-hours", type=float, default=None, help="Optional wall-clock hour cap.")
        command.add_argument("--min-sample-size", type=int, default=20, help="Minimum sample size for search classification.")
        command.add_argument("--entry-lag-bars", type=int, default=1, help="Bars after event before measuring outcomes.")
        command.add_argument("--cooldown-bars", type=int, default=None, help="Optional shared cooldown across timeframes.")
        command.add_argument("--strict-referee", action="store_true", help="Run strict baseline/null validation.")
        command.add_argument("--strict-null-iterations", type=int, default=300, help="Strict referee null iterations.")
        command.add_argument("--strict-random-seed", type=int, default=29, help="Strict referee random seed.")
        command.add_argument(
            "--checkpoint-interval",
            type=int,
            default=5,
            help="Write a process-quality checkpoint and adjust queue priorities every N completed loops.",
        )
        command.add_argument("--resume", action="store_true", help="Resume from existing runtime queue and state.")
        command.add_argument("--dry-run", action="store_true", help="Create loop state/report without executing searches.")
        command.add_argument(
            "--no-auto-gates",
            dest="auto_gate_followups",
            action="store_false",
            help="Do not append attribution/validation gate follow-ups after strict survivor promotions.",
        )
        command.set_defaults(auto_gate_followups=True)

    lab_run = lab_subparsers.add_parser("run", help="Run autonomous lab-loop iterations.")
    add_lab_loop_common(lab_run)
    add_lab_loop_execution_args(lab_run)
    lab_run.add_argument("--max-loops", type=int, default=1, help="Maximum loop iterations to run.")
    lab_run.add_argument(
        "--no-auto-refine",
        dest="auto_refine",
        action="store_false",
        help="Do not automatically append child refinement hypotheses after each loop.",
    )
    lab_run.set_defaults(auto_refine=True)
    lab_run.set_defaults(func=lab_loop_command)

    lab_epoch = lab_subparsers.add_parser("run-epoch", help="Run a supervised 3-10 loop research epoch.")
    add_lab_loop_common(lab_epoch)
    add_lab_loop_execution_args(lab_epoch)
    lab_epoch.add_argument("--epoch-size", type=int, default=5, help="Completed loops in this supervised epoch.")
    lab_epoch.set_defaults(func=lab_loop_command)

    lab_supervise = lab_subparsers.add_parser("supervise-epoch", help="Run the meta-supervisor on the latest epoch.")
    add_lab_loop_common(lab_supervise)
    add_lab_loop_supervisor_args(lab_supervise)
    lab_supervise.add_argument("--epoch-size", type=int, default=5, help="Planned next epoch size.")
    lab_supervise.add_argument("--dry-run", action="store_true", help="Write supervisor artifacts without mutating queue.")
    lab_supervise.set_defaults(func=lab_loop_command)

    lab_run_supervised = lab_subparsers.add_parser(
        "run-supervised",
        help="Run repeated epochs and apply the deterministic meta-supervisor after each epoch.",
    )
    add_lab_loop_common(lab_run_supervised)
    add_lab_loop_execution_args(lab_run_supervised)
    add_lab_loop_supervisor_args(lab_run_supervised)
    lab_run_supervised.add_argument("--epochs", type=int, default=1, help="Number of epochs to run.")
    lab_run_supervised.add_argument("--epoch-size", type=int, default=5, help="Completed loops per epoch.")
    lab_run_supervised.add_argument(
        "--no-apply-supervisor",
        dest="apply_supervisor",
        action="store_false",
        help="Write supervisor artifacts but do not mutate the runtime queue.",
    )
    lab_run_supervised.set_defaults(apply_supervisor=True)
    lab_run_supervised.set_defaults(func=lab_loop_command)

    lab_status = lab_subparsers.add_parser("status", help="Print latest lab-loop state.")
    add_lab_loop_common(lab_status)
    lab_status.set_defaults(func=lab_loop_command)

    lab_next = lab_subparsers.add_parser("next", help="Print the next runnable hypothesis.")
    add_lab_loop_common(lab_next)
    lab_next.set_defaults(func=lab_loop_command)

    lab_validate = lab_subparsers.add_parser("validate-queue", help="Validate the lab-loop queue schema.")
    add_lab_loop_common(lab_validate)
    lab_validate.set_defaults(func=lab_loop_command)

    lab_summarize = lab_subparsers.add_parser("summarize", help="Print reports/lab_loop/latest_status.md.")
    add_lab_loop_common(lab_summarize)
    lab_summarize.set_defaults(func=lab_loop_command)

    lab_epoch_summary = lab_subparsers.add_parser("epoch-summary", help="Print the latest lab-loop epoch summary.")
    add_lab_loop_common(lab_epoch_summary)
    lab_epoch_summary.set_defaults(func=lab_loop_command)

    lab_scoreboard = lab_subparsers.add_parser("concept-scoreboard", help="Print the lab-loop concept scoreboard.")
    add_lab_loop_common(lab_scoreboard)
    lab_scoreboard.set_defaults(func=lab_loop_command)

    lab_director = subparsers.add_parser(
        "lab-director",
        help="Inspect lab evidence, maintain research beliefs, and design the next experiment queue.",
    )
    lab_director_subparsers = lab_director.add_subparsers(dest="lab_director_action", required=True)

    def add_lab_director_common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--state", default=str(DEFAULT_STATE_PATH), help="Lab-loop state JSON path.")
        command.add_argument(
            "--runtime-queue",
            default=str(DEFAULT_RUNTIME_QUEUE_PATH),
            help="Runtime queue YAML used by supervised lab runs.",
        )
        command.add_argument(
            "--concept-scoreboard",
            default=str(DEFAULT_CONCEPT_SCOREBOARD_PATH),
            help="Durable concept scoreboard YAML.",
        )
        command.add_argument(
            "--evidence-ledger",
            default=str(DEFAULT_EVIDENCE_LEDGER_PATH),
            help="Durable meta-supervisor evidence ledger YAML.",
        )
        command.add_argument("--report-root", default=str(DEFAULT_REPORT_ROOT), help="Lab-loop report root.")
        command.add_argument(
            "--director-report-root",
            default=str(DEFAULT_DIRECTOR_REPORT_ROOT),
            help="Directory for generated lab-director artifacts.",
        )
        command.add_argument(
            "--output-queue",
            default=str(DEFAULT_DIRECTOR_QUEUE_PATH),
            help="Applied director queue path used when --apply is set.",
        )
        command.add_argument(
            "--generated-grid-dir",
            default=str(DEFAULT_DIRECTOR_GRID_DIR),
            help="Generated grammar grid directory used when --apply is set.",
        )
        command.add_argument(
            "--objective",
            choices=sorted(LAB_OBJECTIVES),
            default="bullish-positive",
            help="Research objective for director planning.",
        )
        command.add_argument(
            "--max-new-hypotheses",
            type=int,
            default=30,
            help="Maximum hypotheses to emit in a director-designed queue.",
        )
        command.add_argument(
            "--source-root",
            default=".",
            help="Root used to resolve relative report/source paths during audit.",
        )

    director_inspect = lab_director_subparsers.add_parser(
        "inspect",
        help="Build evidence mart, belief graph, and a director report without applying a queue.",
    )
    add_lab_director_common(director_inspect)
    director_inspect.set_defaults(func=lab_director_command)

    director_report = lab_director_subparsers.add_parser(
        "report",
        help="Alias for inspect; writes the latest lab-director report.",
    )
    add_lab_director_common(director_report)
    director_report.set_defaults(func=lab_director_command)

    director_plan = lab_director_subparsers.add_parser(
        "plan-next",
        help="Design and audit the next experiment queue from current evidence.",
    )
    add_lab_director_common(director_plan)
    director_plan.add_argument(
        "--apply",
        action="store_true",
        help="Write the audited director queue to --output-queue.",
    )
    director_plan.add_argument(
        "--apply-to-runtime",
        action="store_true",
        help="Append audited director queue items to --runtime-queue. Requires --apply.",
    )
    director_plan.set_defaults(func=lab_director_command)

    director_run = lab_director_subparsers.add_parser(
        "run",
        help="Run supervised epoch blocks and invoke the lab director after each block.",
    )
    add_lab_director_common(director_run)
    director_run.add_argument("--queue", default=str(DEFAULT_DIRECTOR_QUEUE_PATH), help="Seed queue for the run.")
    director_run.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
    director_run.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
    director_run.add_argument(
        "--timeframes",
        nargs="+",
        default=["1d", "12h", "4h", "1h"],
        help="Timeframes to run each executable hypothesis across.",
    )
    director_run.add_argument("--epochs", type=int, default=1, help="Maximum supervised epochs to run.")
    director_run.add_argument("--epoch-size", type=int, default=5, help="Completed loops per supervised epoch.")
    director_run.add_argument(
        "--director-checkpoint-epochs",
        type=int,
        default=2,
        help="Invoke the director after this many supervised epochs.",
    )
    director_run.add_argument("--max-hours", type=float, default=None, help="Optional wall-clock hour cap per block.")
    director_run.add_argument("--min-sample-size", type=int, default=20, help="Minimum sample size for search classification.")
    director_run.add_argument("--entry-lag-bars", type=int, default=1, help="Bars after event before measuring outcomes.")
    director_run.add_argument("--cooldown-bars", type=int, default=None, help="Optional shared cooldown across timeframes.")
    director_run.add_argument("--strict-referee", action="store_true", help="Run strict baseline/null validation.")
    director_run.add_argument("--strict-null-iterations", type=int, default=300, help="Strict referee null iterations.")
    director_run.add_argument("--strict-random-seed", type=int, default=29, help="Strict referee random seed.")
    director_run.add_argument(
        "--checkpoint-interval",
        type=int,
        default=5,
        help="Write a process-quality checkpoint every N completed loops.",
    )
    director_run.add_argument("--resume", action="store_true", help="Resume from existing runtime queue and state.")
    director_run.add_argument("--dry-run", action="store_true", help="Create loop state/report without executing searches.")
    director_run.add_argument(
        "--no-auto-gates",
        dest="auto_gate_followups",
        action="store_false",
        help="Do not append attribution/validation gate follow-ups after strict survivor promotions.",
    )
    director_run.set_defaults(auto_gate_followups=True)
    director_run.add_argument(
        "--supervisor-policy",
        default=str(DEFAULT_SUPERVISOR_POLICY_PATH),
        help="Optional meta-supervisor policy YAML path.",
    )
    director_run.add_argument(
        "--apply",
        action="store_true",
        help="Write director queues and append audited queue items to the runtime queue.",
    )
    director_run.set_defaults(apply_to_runtime=True)
    director_run.set_defaults(func=lab_director_command)

    lab_meta = subparsers.add_parser(
        "lab-meta",
        help="Score whether the research process is learning and recommend the next intervention.",
    )
    lab_meta_subparsers = lab_meta.add_subparsers(dest="lab_meta_action", required=True)

    def add_lab_meta_common(command: argparse.ArgumentParser) -> None:
        add_lab_director_common(command)
        command.add_argument(
            "--meta-report-root",
            default=str(DEFAULT_META_REPORT_ROOT),
            help="Directory for generated lab-meta artifacts.",
        )
        command.add_argument(
            "--session-id",
            default=None,
            help="Optional lab-meta output session id override.",
        )

    for action_name, help_text in (
        ("inspect", "Build a process scorecard without choosing an intervention."),
        ("evaluate", "Alias for inspect."),
        ("plan", "Build a scorecard and audited process intervention plan."),
        ("recommend", "Alias for plan."),
        ("report", "Write a plain-English meta-research report."),
    ):
        command = lab_meta_subparsers.add_parser(action_name, help=help_text)
        add_lab_meta_common(command)
        command.add_argument("--snapshot", default=None, help="Optional existing lab-director snapshot directory.")
        command.set_defaults(func=lab_meta_command)

    meta_replay = lab_meta_subparsers.add_parser(
        "replay",
        help="Run the meta evaluator against an existing lab-director artifact snapshot.",
    )
    add_lab_meta_common(meta_replay)
    meta_replay.add_argument("--snapshot", required=True, help="Lab-director artifact directory to replay.")
    meta_replay.set_defaults(func=lab_meta_command)

    meta_status = lab_meta_subparsers.add_parser("status", help="Print the latest lab-meta status.")
    add_lab_meta_common(meta_status)
    meta_status.add_argument("--snapshot", default=None, help=argparse.SUPPRESS)
    meta_status.set_defaults(func=lab_meta_command)

    def add_governance_snapshot_args(command: argparse.ArgumentParser) -> None:
        command.add_argument("--run-id", default=None, help="Lab-ops run id to inspect.")
        command.add_argument("--evidence-mart", default=None, help="Explicit evidence_mart.yaml path.")
        command.add_argument("--belief-graph", default=None, help="Explicit belief_graph.yaml path.")
        command.add_argument(
            "--director-report-root",
            default=str(DEFAULT_DIRECTOR_REPORT_ROOT),
            help="Fallback director report root when --run-id is not provided.",
        )
        command.add_argument(
            "--ops-report-root",
            default=str(LAB_OPS_REPORT_ROOT),
            help="Lab-ops report root used with --run-id.",
        )
        command.add_argument("--output-dir", default=None, help="Directory for generated governance artifacts.")

    blocker_audit = subparsers.add_parser("blocker-audit", help="Audit whether blocker-like beliefs avoid harm.")
    blocker_audit_subparsers = blocker_audit.add_subparsers(dest="blocker_audit_action", required=True)
    blocker_inspect = blocker_audit_subparsers.add_parser("inspect", help="Write a blocker audit from director artifacts.")
    add_governance_snapshot_args(blocker_inspect)
    blocker_inspect.set_defaults(func=blocker_audit_command)

    lane_router = subparsers.add_parser("lane-router", help="Assign director beliefs to research lanes.")
    lane_router_subparsers = lane_router.add_subparsers(dest="lane_router_action", required=True)
    lane_assign = lane_router_subparsers.add_parser("assign", help="Write lane assignments from a belief graph.")
    add_governance_snapshot_args(lane_assign)
    lane_assign.add_argument("--blocker-audit", default=None, help="Optional blocker_audit.yaml path.")
    lane_assign.add_argument("--meta-scorecard", default=None, help="Optional process_scorecard.yaml path.")
    lane_assign.set_defaults(func=lane_router_command)

    lane_recover = lane_router_subparsers.add_parser(
        "recover",
        help="Generate a governed lane-recovery queue when open lanes have no runnable director work.",
    )
    add_governance_snapshot_args(lane_recover)
    lane_recover.add_argument("--lane-assignment", default=None, help="Optional lane_assignment.yaml path.")
    lane_recover.add_argument("--runtime-queue", default=None, help="Runtime queue to append to when --apply is set.")
    lane_recover.add_argument("--state", default=None, help="Lab state JSON used to skip completed hypotheses.")
    lane_recover.add_argument("--output-queue", default=None, help="Recovery queue YAML path.")
    lane_recover.add_argument("--generated-grid-dir", default=None, help="Directory for generated recovery grids.")
    lane_recover.add_argument("--ops-runtime-root", default=str(LAB_OPS_RUNTIME_ROOT), help="Lab-ops runtime root.")
    lane_recover.add_argument("--source-root", default=".", help="Root used to resolve relative source paths.")
    lane_recover.add_argument("--max-new-hypotheses", type=int, default=30, help="Maximum recovery hypotheses.")
    lane_recover.add_argument("--apply", action="store_true", help="Append audited recovery items to the runtime queue.")
    lane_recover.set_defaults(func=lane_router_recover_command)

    validation_governance = subparsers.add_parser(
        "validation-governance",
        help="Review whether beliefs may advance through validation gates.",
    )
    validation_subparsers = validation_governance.add_subparsers(dest="validation_governance_action", required=True)
    validation_review = validation_subparsers.add_parser("review", help="Write validation governance decisions.")
    add_governance_snapshot_args(validation_review)
    validation_review.add_argument("--lane-assignment", default=None, help="Optional lane_assignment.yaml path.")
    validation_review.add_argument("--blocker-audit", default=None, help="Optional blocker_audit.yaml path.")
    validation_review.set_defaults(func=validation_governance_command)

    research_map = subparsers.add_parser("research-map", help="Update or report the durable Riskflow research map.")
    research_map_subparsers = research_map.add_subparsers(dest="research_map_action", required=True)
    research_map_update = research_map_subparsers.add_parser("update", help="Update the research map from director artifacts.")
    add_governance_snapshot_args(research_map_update)
    research_map_update.add_argument("--lane-assignment", default=None, help="Optional lane_assignment.yaml path.")
    research_map_update.add_argument("--blocker-audit", default=None, help="Optional blocker_audit.yaml path.")
    research_map_update.add_argument("--validation-governance", default=None, help="Optional validation_decision.yaml path.")
    research_map_update.add_argument("--map-path", default=str(DEFAULT_RESEARCH_MAP_PATH), help="Durable research map YAML.")
    research_map_update.add_argument(
        "--report-root",
        default=str(DEFAULT_RESEARCH_MAP_REPORT_ROOT),
        help="Generated research map status report root.",
    )
    research_map_update.set_defaults(func=research_map_command)

    ceo = subparsers.add_parser(
        "ceo",
        help="Operate the Riskflow CEO autopilot layer for bounded executive-supervised improvement blocks.",
    )
    ceo_subparsers = ceo.add_subparsers(dest="ceo_action", required=True)

    def add_ceo_common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--objective", choices=sorted(LAB_OBJECTIVES), default="bullish-positive")
        command.add_argument("--run-id", default=None, help="CEO run id.")
        command.add_argument("--lab-run-id", default=None, help="Underlying lab-ops run id.")
        command.add_argument("--queue", default=str(DEFAULT_DIRECTOR_QUEUE_PATH), help="Seed queue YAML.")
        command.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
        command.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
        command.add_argument(
            "--timeframes",
            nargs="+",
            default=["1d", "12h", "4h", "1h"],
            help="Timeframes to run each executable hypothesis across.",
        )
        command.add_argument("--block-epochs", type=int, default=2, help="Supervised epochs per CEO block.")
        command.add_argument("--epoch-size", type=int, default=5, help="Completed loops per supervised epoch.")
        command.add_argument("--max-hours", type=float, default=None, help="Optional wall-clock hour cap.")
        command.add_argument("--min-sample-size", type=int, default=20, help="Minimum sample size for search classification.")
        command.add_argument("--entry-lag-bars", type=int, default=1, help="Bars after event before measuring outcomes.")
        command.add_argument("--cooldown-bars", type=int, default=None, help="Optional shared cooldown across timeframes.")
        command.add_argument("--strict-referee", dest="strict_referee", action="store_true", default=True)
        command.add_argument("--no-strict-referee", dest="strict_referee", action="store_false")
        command.add_argument("--strict-null-iterations", type=int, default=300, help="Strict referee null iterations.")
        command.add_argument("--strict-random-seed", type=int, default=29, help="Strict referee random seed.")
        command.add_argument("--checkpoint-interval", type=int, default=5, help="Lab-loop checkpoint interval.")
        command.add_argument("--dry-run", action="store_true", help="Create loop state/report without executing searches.")
        command.add_argument("--resume", action="store_true", help="Resume the underlying run-scoped lab state.")
        command.add_argument("--source-root", default=".", help="Root used to resolve relative source paths.")
        command.add_argument("--ceo-report-root", default=str(CEO_REPORT_ROOT), help="Directory for CEO reports.")
        command.add_argument("--ops-report-root", default=str(LAB_OPS_REPORT_ROOT), help="Directory for lab-ops reports.")
        command.add_argument("--ops-runtime-root", default=str(LAB_OPS_RUNTIME_ROOT), help="Directory for lab-ops runtime state.")
        command.add_argument("--max-new-hypotheses", type=int, default=30, help="Maximum director hypotheses per checkpoint.")

    ceo_status = ceo_subparsers.add_parser("status", help="Print CEO-level company status.")
    add_ceo_common(ceo_status)
    ceo_status.add_argument("--show-lab-status", action="store_true", help="Also print underlying lab-ops status text.")
    ceo_status.set_defaults(func=ceo_command)

    ceo_plan = ceo_subparsers.add_parser("plan", help="Write a CEO plan without running a block.")
    add_ceo_common(ceo_plan)
    ceo_plan.set_defaults(func=ceo_command)

    ceo_run_block = ceo_subparsers.add_parser("run-block", help="Run one bounded governed CEO research block.")
    add_ceo_common(ceo_run_block)
    ceo_run_block.add_argument("--apply", action="store_true", help="Allow run-scoped lab queue/state mutations.")
    ceo_run_block.set_defaults(func=ceo_command)

    ceo_execute_next = ceo_subparsers.add_parser(
        "execute-next",
        help="Execute the latest CEO decision through the binding dispatcher.",
    )
    add_ceo_common(ceo_execute_next)
    ceo_execute_next.add_argument("--apply", action="store_true", help="Allow the selected CEO action to write run artifacts.")
    ceo_execute_next.set_defaults(func=ceo_command)

    ceo_champion_challenger = ceo_subparsers.add_parser(
        "champion-challenger",
        help="Run CEO product-delta champion/challenger preparation for shadow candidates.",
    )
    add_ceo_common(ceo_champion_challenger)
    ceo_champion_challenger.add_argument("--apply", action="store_true", help="Allow champion/challenger artifacts to be written.")
    ceo_champion_challenger.add_argument("--top-n", type=int, default=None, help="Limit comparison work items.")
    ceo_champion_challenger.set_defaults(func=ceo_command)

    ceo_fresh_control_validation = ceo_subparsers.add_parser(
        "fresh-control-validation",
        help="Plan fresh or control validation for promising champion/challenger shadow candidates.",
    )
    add_ceo_common(ceo_fresh_control_validation)
    ceo_fresh_control_validation.add_argument(
        "--apply",
        action="store_true",
        help="Allow fresh/control validation plan artifacts to be written.",
    )
    ceo_fresh_control_validation.set_defaults(func=ceo_command)

    ceo_fresh_data_preflight = ceo_subparsers.add_parser(
        "fresh-data-preflight",
        help="Check local OHLCV coverage/freshness before fresh/control validation.",
    )
    add_ceo_common(ceo_fresh_data_preflight)
    ceo_fresh_data_preflight.set_defaults(func=ceo_command)

    ceo_frozen_candidate_validation = ceo_subparsers.add_parser(
        "frozen-candidate-validation",
        help="Compile frozen validation specs from a fresh/control plan and data preflight.",
    )
    add_ceo_common(ceo_frozen_candidate_validation)
    ceo_frozen_candidate_validation.set_defaults(func=ceo_command)

    ceo_frozen_validation_executor = ceo_subparsers.add_parser(
        "frozen-validation-executor",
        help="Replay frozen validation specs against existing source artifacts without promotion authority.",
    )
    add_ceo_common(ceo_frozen_validation_executor)
    ceo_frozen_validation_executor.set_defaults(func=ceo_command)

    ceo_frozen_validation_rerun = ceo_subparsers.add_parser(
        "frozen-validation-rerun",
        help="Run the frozen validation adapter rerun grid on local data without promotion authority.",
    )
    add_ceo_common(ceo_frozen_validation_rerun)
    ceo_frozen_validation_rerun.set_defaults(func=ceo_command)

    ceo_fresh_withheld_validation_contract = ceo_subparsers.add_parser(
        "fresh-withheld-validation-contract",
        help="Freeze fresh/withheld validation snapshot rules and pass/fail gates without executing validation.",
    )
    add_ceo_common(ceo_fresh_withheld_validation_contract)
    ceo_fresh_withheld_validation_contract.set_defaults(func=ceo_command)

    ceo_withheld_split_manifest = ceo_subparsers.add_parser(
        "withheld-split-manifest",
        help="Write withheld split authority metadata without executing validation.",
    )
    add_ceo_common(ceo_withheld_split_manifest)
    ceo_withheld_split_manifest.add_argument(
        "--apply",
        action="store_true",
        help="Allow withheld split authority artifacts to be written.",
    )
    ceo_withheld_split_manifest.add_argument("--withheld-split-id", required=True)
    ceo_withheld_split_manifest.add_argument("--source-evidence-cutoff", required=True)
    ceo_withheld_split_manifest.add_argument("--description", default="")
    ceo_withheld_split_manifest.set_defaults(func=ceo_command)

    ceo_fresh_withheld_snapshot_manifest = ceo_subparsers.add_parser(
        "fresh-withheld-snapshot-manifest",
        help="Write a fresh/withheld snapshot authority manifest draft without executing validation.",
    )
    add_ceo_common(ceo_fresh_withheld_snapshot_manifest)
    ceo_fresh_withheld_snapshot_manifest.add_argument(
        "--apply",
        action="store_true",
        help="Allow snapshot authority manifest artifacts to be written.",
    )
    ceo_fresh_withheld_snapshot_manifest.set_defaults(func=ceo_command)

    ceo_fresh_withheld_snapshot_declare = ceo_subparsers.add_parser(
        "fresh-withheld-snapshot-declare",
        help="Declare fresh/withheld snapshot authority from explicit cutoff or split inputs without executing validation.",
    )
    add_ceo_common(ceo_fresh_withheld_snapshot_declare)
    ceo_fresh_withheld_snapshot_declare.add_argument(
        "--apply",
        action="store_true",
        help="Allow snapshot authority declaration artifacts to be written.",
    )
    ceo_fresh_withheld_snapshot_declare.add_argument("--snapshot-type", required=True, choices=("fresh", "withheld"))
    ceo_fresh_withheld_snapshot_declare.add_argument("--snapshot-cutoff", default="")
    ceo_fresh_withheld_snapshot_declare.add_argument("--withheld-split-id", default="")
    ceo_fresh_withheld_snapshot_declare.add_argument("--source-evidence-cutoff", required=True)
    ceo_fresh_withheld_snapshot_declare.add_argument("--confirm-no-overlap", action="store_true")
    ceo_fresh_withheld_snapshot_declare.set_defaults(func=ceo_command)

    ceo_fresh_withheld_validation_executor = ceo_subparsers.add_parser(
        "fresh-withheld-validation-executor",
        help="Run the manifest-gated fresh/withheld validation executor without promotion authority.",
    )
    add_ceo_common(ceo_fresh_withheld_validation_executor)
    ceo_fresh_withheld_validation_executor.set_defaults(func=ceo_command)

    ceo_patch_research_infra = ceo_subparsers.add_parser(
        "patch-research-infra",
        help="Plan/apply governed lane-recovery queue items for a CEO research-infra gap.",
    )
    add_ceo_common(ceo_patch_research_infra)
    ceo_patch_research_infra.add_argument(
        "--apply",
        action="store_true",
        help="Allow recovery plan artifacts and runtime queue additions to be written.",
    )
    ceo_patch_research_infra.set_defaults(func=ceo_command)

    ceo_broaden_hypothesis_source = ceo_subparsers.add_parser(
        "broaden-hypothesis-source",
        help="Compile Obsidian/research source hypotheses into the lab runtime queue.",
    )
    add_ceo_common(ceo_broaden_hypothesis_source)
    ceo_broaden_hypothesis_source.add_argument(
        "--apply",
        action="store_true",
        help="Allow broadening artifacts and runtime queue additions to be written.",
    )
    ceo_broaden_hypothesis_source.set_defaults(func=ceo_command)

    ceo_heartbeat_status = ceo_subparsers.add_parser(
        "heartbeat-status",
        help="Read the latest CEO heartbeat status without writing a new decision packet.",
    )
    add_ceo_common(ceo_heartbeat_status)
    ceo_heartbeat_status.set_defaults(func=ceo_command)

    ceo_heartbeat_plan = ceo_subparsers.add_parser(
        "heartbeat-plan",
        help="Write a bounded CEO heartbeat plan for external scheduler or Codex cadence.",
    )
    add_ceo_common(ceo_heartbeat_plan)
    ceo_heartbeat_plan.add_argument("--interval-minutes", type=int, default=15)
    ceo_heartbeat_plan.set_defaults(func=ceo_command)

    ceo_heartbeat_tick = ceo_subparsers.add_parser(
        "heartbeat-tick",
        help="Run one persisted CEO heartbeat tick: inspect gates, optionally execute one bound action, and append the journal.",
    )
    add_ceo_common(ceo_heartbeat_tick)
    ceo_heartbeat_tick.add_argument("--apply", action="store_true", help="Required to write heartbeat state and run one bound action.")
    ceo_heartbeat_tick.set_defaults(func=ceo_command)

    ceo_heartbeat_journal = ceo_subparsers.add_parser(
        "heartbeat-journal",
        help="Render the persisted CEO heartbeat journal for a run.",
    )
    add_ceo_common(ceo_heartbeat_journal)
    ceo_heartbeat_journal.set_defaults(func=ceo_command)

    ceo_stop = ceo_subparsers.add_parser("stop", help="Request a graceful stop for a CEO-supervised run.")
    add_ceo_common(ceo_stop)
    ceo_stop.add_argument("--reason", default="user_requested", help="Stop reason to write into stop.request files.")
    ceo_stop.set_defaults(func=ceo_command)

    ceo_review = ceo_subparsers.add_parser("review", help="Write a CEO decision packet from latest lab artifacts.")
    add_ceo_common(ceo_review)
    ceo_review.set_defaults(func=ceo_command)

    ceo_report = ceo_subparsers.add_parser("report", help="Write the final CEO report.")
    add_ceo_common(ceo_report)
    ceo_report.set_defaults(func=ceo_command)

    ceo_trace_grade = ceo_subparsers.add_parser(
        "trace-grade",
        help="Grade CEO heartbeat trace artifacts for no-progress, safety, and next-action support.",
    )
    add_ceo_common(ceo_trace_grade)
    ceo_trace_grade.set_defaults(func=ceo_command)

    ceo_flight_dashboard = ceo_subparsers.add_parser(
        "flight-dashboard",
        help="Write a plain-English CEO state dashboard for long supervised runs.",
    )
    add_ceo_common(ceo_flight_dashboard)
    ceo_flight_dashboard.set_defaults(func=ceo_command)

    ceo_operating_dashboard = ceo_subparsers.add_parser(
        "operating-dashboard",
        help="Write a CEO operating portfolio dashboard across candidates, capabilities, data gates, and risk.",
    )
    add_ceo_common(ceo_operating_dashboard)
    ceo_operating_dashboard.set_defaults(func=ceo_command)

    ceo_portfolio_allocator = ceo_subparsers.add_parser(
        "portfolio-allocator",
        help="Score CEO operating lanes and select the highest-value bottleneck to address next.",
    )
    add_ceo_common(ceo_portfolio_allocator)
    ceo_portfolio_allocator.set_defaults(func=ceo_command)

    ceo_mission_score = ceo_subparsers.add_parser(
        "mission-score",
        help="Score Riskflow mission coverage across permission, warning, invalidation, reset, gradient, path, regime, and archive dimensions.",
    )
    add_ceo_common(ceo_mission_score)
    ceo_mission_score.set_defaults(func=ceo_command)

    ceo_strategy_capital_dashboard = ceo_subparsers.add_parser(
        "strategy-capital-dashboard",
        help="Allocate CEO attention points across safety, validation, translation, mission gaps, and memory work.",
    )
    add_ceo_common(ceo_strategy_capital_dashboard)
    ceo_strategy_capital_dashboard.set_defaults(func=ceo_command)

    ceo_decision_quality = ceo_subparsers.add_parser(
        "decision-quality",
        help="Write an explainable CEO decision-quality card with alternatives, confidence, and expected artifacts.",
    )
    add_ceo_common(ceo_decision_quality)
    ceo_decision_quality.set_defaults(func=ceo_command)

    ceo_action_board = ceo_subparsers.add_parser(
        "action-board",
        help="Write the CEO operator action board with the primary safe next action and non-actions.",
    )
    add_ceo_common(ceo_action_board)
    ceo_action_board.set_defaults(func=ceo_command)

    ceo_operator_step = ceo_subparsers.add_parser(
        "operator-step",
        help="Run one audited CEO operator transaction from the action board when bounded dispatch is safe.",
    )
    add_ceo_common(ceo_operator_step)
    ceo_operator_step.add_argument("--apply", action="store_true", help="Required to write the operator step and run one safe bounded dispatch.")
    ceo_operator_step.set_defaults(func=ceo_command)

    ceo_operator_brief = ceo_subparsers.add_parser(
        "operator-brief",
        help="Write a plain-English CEO operator brief from status, action-board, and decision-quality artifacts.",
    )
    add_ceo_common(ceo_operator_brief)
    ceo_operator_brief.set_defaults(func=ceo_command)

    ceo_memory_delta = ceo_subparsers.add_parser(
        "memory-delta",
        help="Write a governed CEO memory-delta artifact and optionally a curated Obsidian handoff note.",
    )
    add_ceo_common(ceo_memory_delta)
    ceo_memory_delta.add_argument("--apply", action="store_true", help="Write the curated Obsidian memory-delta note when required.")
    ceo_memory_delta.set_defaults(func=ceo_command)

    ceo_guardrail_audit = ceo_subparsers.add_parser(
        "guardrail-audit",
        help="Scan CEO run artifacts for production-effect and product-language guardrail violations.",
    )
    add_ceo_common(ceo_guardrail_audit)
    ceo_guardrail_audit.set_defaults(func=ceo_command)

    ceo_preflight_gate = ceo_subparsers.add_parser(
        "preflight-gate",
        help="Build the unified CEO dispatch preflight gate from trace, replay, eval, approval, memory, and budget artifacts.",
    )
    add_ceo_common(ceo_preflight_gate)
    ceo_preflight_gate.add_argument("--enforce-memory-delta", action="store_true")
    ceo_preflight_gate.set_defaults(func=ceo_command)

    ceo_promotion_proposal = ceo_subparsers.add_parser(
        "promotion-proposal",
        help="Write a guarded promotion proposal for user review without applying product changes.",
    )
    add_ceo_common(ceo_promotion_proposal)
    ceo_promotion_proposal.set_defaults(func=ceo_command)

    ceo_evidence_debt_register = ceo_subparsers.add_parser(
        "evidence-debt-register",
        help="Write a CEO register of candidate evidence debts blocking product-language or promotion gates.",
    )
    add_ceo_common(ceo_evidence_debt_register)
    ceo_evidence_debt_register.set_defaults(func=ceo_command)

    ceo_sidecar_evidence_brief = ceo_subparsers.add_parser(
        "sidecar-evidence-brief",
        help="Write a compact warning/reset sidecar evidence brief from existing CEO sprint artifacts.",
    )
    add_ceo_common(ceo_sidecar_evidence_brief)
    ceo_sidecar_evidence_brief.set_defaults(func=ceo_command)

    ceo_data_gate_brief = ceo_subparsers.add_parser(
        "data-gate-brief",
        help="Write a diagnostic brief for OHLCV data readiness blocking sidecar validation.",
    )
    add_ceo_common(ceo_data_gate_brief)
    ceo_data_gate_brief.set_defaults(func=ceo_command)

    ceo_approval_queue = ceo_subparsers.add_parser(
        "approval-queue",
        help="Write a CEO queue of red-authority decisions waiting for explicit user approval.",
    )
    add_ceo_common(ceo_approval_queue)
    ceo_approval_queue.set_defaults(func=ceo_command)

    ceo_approval_record = ceo_subparsers.add_parser(
        "approval-record",
        help="Append an explicit user-confirmed approval or rejection decision to the CEO approval ledger.",
    )
    add_ceo_common(ceo_approval_record)
    ceo_approval_record.add_argument("--approval-id", required=True, help="Approval id from approval_queue.yaml.")
    ceo_approval_record.add_argument("--decision", required=True, choices=("approved", "rejected"))
    ceo_approval_record.add_argument("--user-confirmed", action="store_true", help="Required explicit confirmation flag.")
    ceo_approval_record.set_defaults(func=ceo_command)

    ceo_approval_apply = ceo_subparsers.add_parser(
        "approval-apply",
        help="Apply a recorded CEO approval through a second explicit guarded step.",
    )
    add_ceo_common(ceo_approval_apply)
    ceo_approval_apply.add_argument("--approval-id", required=True, help="Approval id from approval_queue.yaml.")
    ceo_approval_apply.add_argument("--user-confirmed", action="store_true", help="Required explicit confirmation flag.")
    ceo_approval_apply.add_argument("--apply", action="store_true", help="Required to apply the recorded approval closure.")
    ceo_approval_apply.set_defaults(func=ceo_command)

    ceo_executive_kpis = ceo_subparsers.add_parser(
        "executive-kpis",
        help="Write compact CEO operating KPIs for approvals, evidence debt, candidates, validation, and trace health.",
    )
    add_ceo_common(ceo_executive_kpis)
    ceo_executive_kpis.set_defaults(func=ceo_command)

    ceo_role_queue = ceo_subparsers.add_parser(
        "role-queue",
        help="Write specialist CEO role registry and task queue from approvals, evidence debt, and capability backlog.",
    )
    add_ceo_common(ceo_role_queue)
    ceo_role_queue.set_defaults(func=ceo_command)

    ceo_role_dispatch = ceo_subparsers.add_parser(
        "role-dispatch",
        help="Write specialist role dispatch packets with exact questions, refs, authority, and result schema.",
    )
    add_ceo_common(ceo_role_dispatch)
    ceo_role_dispatch.set_defaults(func=ceo_command)

    ceo_role_result = ceo_subparsers.add_parser(
        "role-result",
        help="Append a specialist role task result to the CEO role task ledger.",
    )
    add_ceo_common(ceo_role_result)
    ceo_role_result.add_argument("--task-id", required=True)
    ceo_role_result.add_argument("--status", required=True, choices=("complete", "blocked"))
    ceo_role_result.add_argument("--result-path", default="")
    ceo_role_result.set_defaults(func=ceo_command)

    ceo_org_progress_score = ceo_subparsers.add_parser(
        "org-progress-score",
        help="Score whether role/specialist work changed decisions or only produced activity.",
    )
    add_ceo_common(ceo_org_progress_score)
    ceo_org_progress_score.set_defaults(func=ceo_command)

    ceo_capability_backlog = ceo_subparsers.add_parser(
        "capability-backlog",
        help="Write a standalone CEO research-infrastructure capability backlog.",
    )
    add_ceo_common(ceo_capability_backlog)
    ceo_capability_backlog.set_defaults(func=ceo_command)

    ceo_replay = ceo_subparsers.add_parser(
        "replay",
        help="Reconstruct a CEO run from append-only ledgers and key artifacts.",
    )
    add_ceo_common(ceo_replay)
    ceo_replay.set_defaults(func=ceo_command)

    ceo_resumption_brief = ceo_subparsers.add_parser(
        "resumption-brief",
        help="Write a compact fresh-session brief that says whether a CEO run can resume, wait, repair, or stop.",
    )
    add_ceo_common(ceo_resumption_brief)
    ceo_resumption_brief.set_defaults(func=ceo_command)

    ceo_artifact_coherence = ceo_subparsers.add_parser(
        "artifact-coherence",
        help="Check whether CEO handoff artifacts are current and internally consistent.",
    )
    add_ceo_common(ceo_artifact_coherence)
    ceo_artifact_coherence.set_defaults(func=ceo_command)

    ceo_run_index = ceo_subparsers.add_parser(
        "run-index",
        help="Write a diagnostic index of CEO runs and the safest next command for each.",
    )
    add_ceo_common(ceo_run_index)
    ceo_run_index.add_argument("--limit", type=int, default=25, help="Maximum number of recent CEO runs to include.")
    ceo_run_index.set_defaults(func=ceo_command)

    ceo_dispatch_receipt = ceo_subparsers.add_parser(
        "dispatch-receipt",
        help="Write a diagnostic receipt of the trust artifacts that would allow or block execute-next dispatch.",
    )
    add_ceo_common(ceo_dispatch_receipt)
    ceo_dispatch_receipt.set_defaults(func=ceo_command)

    ceo_blocker_stack = ceo_subparsers.add_parser(
        "blocker-stack",
        help="Write an ordered CEO blocker stack with authority, evidence, and the safest next command.",
    )
    add_ceo_common(ceo_blocker_stack)
    ceo_blocker_stack.set_defaults(func=ceo_command)

    ceo_incident_register = ceo_subparsers.add_parser(
        "incident-register",
        help="Write a diagnostic CEO operating incident register from blocked dispatch, replay, eval, guardrail, and coherence artifacts.",
    )
    add_ceo_common(ceo_incident_register)
    ceo_incident_register.set_defaults(func=ceo_command)

    ceo_repair_plan = ceo_subparsers.add_parser(
        "repair-plan",
        help="Write a ranked CEO repair plan from the blocker stack and operating incident register.",
    )
    add_ceo_common(ceo_repair_plan)
    ceo_repair_plan.set_defaults(func=ceo_command)

    ceo_repair_apply = ceo_subparsers.add_parser(
        "repair-apply",
        help="Execute one allowlisted CEO repair-plan item and write before/after closure evidence.",
    )
    add_ceo_common(ceo_repair_apply)
    ceo_repair_apply.add_argument("--repair-key", required=True)
    ceo_repair_apply.add_argument("--apply", action="store_true", help="Required to execute one allowlisted repair-plan item.")
    ceo_repair_apply.set_defaults(func=ceo_command)

    ceo_eval_suite = ceo_subparsers.add_parser(
        "eval-suite",
        help="Grade CEO-mode replayability, guardrails, approval gates, validation authority, and role closure.",
    )
    add_ceo_common(ceo_eval_suite)
    ceo_eval_suite.set_defaults(func=ceo_command)

    ceo_eval_fixtures = ceo_subparsers.add_parser(
        "eval-fixtures",
        help="Run deterministic CEO policy fixtures for transition and approval-routing rules.",
    )
    add_ceo_common(ceo_eval_fixtures)
    ceo_eval_fixtures.set_defaults(func=ceo_command)

    lab_ops = subparsers.add_parser(
        "lab-ops",
        help="Plan, run, resume, and report autonomous Riskflow lab runs.",
    )
    lab_ops_subparsers = lab_ops.add_subparsers(dest="lab_ops_action", required=True)

    def add_lab_ops_common(command: argparse.ArgumentParser) -> None:
        command.add_argument("--objective", choices=sorted(LAB_OBJECTIVES), default="bullish-positive")
        command.add_argument("--run-id", default=None, help="Autonomous run id.")
        command.add_argument("--queue", default=str(DEFAULT_DIRECTOR_QUEUE_PATH), help="Seed queue YAML.")
        command.add_argument("--config", default="configs/meme_universe.yaml", help="Universe YAML config path.")
        command.add_argument("--data-dir", default="data/raw", help="Directory containing OHLCV CSV files.")
        command.add_argument(
            "--timeframes",
            nargs="+",
            default=["1d", "12h", "4h", "1h"],
            help="Timeframes to run each executable hypothesis across.",
        )
        command.add_argument("--max-epochs", type=int, default=50, help="Maximum supervised epochs to run.")
        command.add_argument("--epoch-size", type=int, default=5, help="Completed loops per supervised epoch.")
        command.add_argument(
            "--director-checkpoint-epochs",
            type=int,
            default=2,
            help="Run the director/meta checkpoint after this many supervised epochs.",
        )
        command.add_argument("--max-hours", type=float, default=None, help="Optional wall-clock hour cap.")
        command.add_argument("--min-sample-size", type=int, default=20, help="Minimum sample size for search classification.")
        command.add_argument("--entry-lag-bars", type=int, default=1, help="Bars after event before measuring outcomes.")
        command.add_argument("--cooldown-bars", type=int, default=None, help="Optional shared cooldown across timeframes.")
        command.add_argument("--strict-referee", dest="strict_referee", action="store_true", default=True)
        command.add_argument("--no-strict-referee", dest="strict_referee", action="store_false")
        command.add_argument("--strict-null-iterations", type=int, default=300, help="Strict referee null iterations.")
        command.add_argument("--strict-random-seed", type=int, default=29, help="Strict referee random seed.")
        command.add_argument("--checkpoint-interval", type=int, default=5, help="Lab-loop checkpoint interval.")
        command.add_argument("--max-errors", type=int, default=10, help="Maximum block-level errors before failing.")
        command.add_argument(
            "--max-generated-artifact-mb",
            type=int,
            default=5000,
            help="Generated artifact megabyte cap before stopping.",
        )
        command.add_argument("--dry-run", action="store_true", help="Create loop state/report without executing searches.")
        command.add_argument("--governed", action="store_true", help="Write governance artifacts at each lab-ops checkpoint.")
        command.add_argument("--source-root", default=".", help="Root used to resolve relative source paths.")
        command.add_argument(
            "--ops-report-root",
            default=str(LAB_OPS_REPORT_ROOT),
            help="Directory for lab-ops generated reports.",
        )
        command.add_argument(
            "--ops-runtime-root",
            default=str(LAB_OPS_RUNTIME_ROOT),
            help="Directory for lab-ops generated runtime state.",
        )
        command.add_argument(
            "--supervisor-policy",
            default=str(DEFAULT_SUPERVISOR_POLICY_PATH),
            help="Optional meta-supervisor policy YAML path.",
        )
        command.add_argument("--max-new-hypotheses", type=int, default=30, help="Maximum director hypotheses per checkpoint.")

    ops_plan = lab_ops_subparsers.add_parser("plan", help="Plan an autonomous run without mutating runtime queues.")
    add_lab_ops_common(ops_plan)
    ops_plan.set_defaults(func=lab_ops_command)

    ops_run = lab_ops_subparsers.add_parser("run", help="Run an autonomous lab session.")
    add_lab_ops_common(ops_run)
    ops_run.add_argument("--apply", action="store_true", help="Allow run-scoped runtime queue/state mutations.")
    ops_run.set_defaults(func=lab_ops_command)

    ops_resume = lab_ops_subparsers.add_parser("resume", help="Resume an existing autonomous lab session.")
    add_lab_ops_common(ops_resume)
    ops_resume.add_argument("--apply", action="store_true", help="Allow run-scoped runtime queue/state mutations.")
    ops_resume.add_argument("--resume", action="store_true", default=True, help=argparse.SUPPRESS)
    ops_resume.set_defaults(func=lab_ops_command)

    ops_status = lab_ops_subparsers.add_parser("status", help="Print autonomous run status.")
    add_lab_ops_common(ops_status)
    ops_status.add_argument("--apply", action="store_true", default=False, help=argparse.SUPPRESS)
    ops_status.set_defaults(func=lab_ops_command)

    ops_report = lab_ops_subparsers.add_parser("report", help="Write/read autonomous run final report.")
    add_lab_ops_common(ops_report)
    ops_report.add_argument("--apply", action="store_true", default=False, help=argparse.SUPPRESS)
    ops_report.set_defaults(func=lab_ops_command)

    ops_stop = lab_ops_subparsers.add_parser("stop", help="Request a graceful stop for an autonomous run.")
    add_lab_ops_common(ops_stop)
    ops_stop.add_argument("--reason", default="user_requested", help="Stop reason to write into stop.request.")
    ops_stop.add_argument("--apply", action="store_true", default=False, help=argparse.SUPPRESS)
    ops_stop.set_defaults(func=lab_ops_command)

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
