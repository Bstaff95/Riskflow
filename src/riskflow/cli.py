from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .baskets import build_equal_weight_return_index
from .compression import calculate_compression_features
from .config import UniverseConfig, load_universe_config
from .data_loader import load_universe_ohlcv
from .event_study import run_event_study
from .indicator_engine import calculate_indicator
from .reports import (
    export_event_study_reports,
    export_scan_reports,
    export_setup_research_reports,
    export_signal_research_reports,
    export_state_research_reports,
)
from .resample import research_mtf_derivations, resample_universe
from .signal_research import run_signal_research
from .setup_quality import calculate_setup_quality
from .setup_research import run_setup_research
from .state_research import run_state_research
from .states import classify_state_frame


LEADERBOARD_COLUMNS = [
    "symbol",
    "name",
    "sector",
    "subgroup",
    "latest_close",
    "final_signal",
    "price_component",
    "relative_component",
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


def build_analysis_frames(
    universe: UniverseConfig,
    raw_frames: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], pd.Series, list[str]]:
    warnings: list[str] = []
    closes = {symbol: frame["close"] for symbol, frame in raw_frames.items()}
    basket = build_equal_weight_return_index(
        closes,
        min_active_members=universe.min_active_members,
        name=universe.benchmark.name,
    )
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
        indicator = calculate_indicator(
            raw["close"],
            basket,
            settings=universe.indicator_settings,
            weights=universe.weights,
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


def build_leaderboard(universe: UniverseConfig, analysis_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
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
        rows.append(
            {
                "symbol": symbol,
                "name": asset.name,
                "sector": asset.sector,
                "subgroup": asset.subgroup,
                "latest_close": latest.get("target"),
                "final_signal": latest.get("final_signal"),
                "price_component": latest.get("price_component"),
                "relative_component": latest.get("relative_component"),
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
        )

    leaderboard = pd.DataFrame(rows)
    for column in LEADERBOARD_COLUMNS:
        if column not in leaderboard.columns:
            leaderboard[column] = pd.NA
    if "trader_score_v0" in leaderboard.columns:
        leaderboard["trader_rank"] = leaderboard["trader_score_v0"].rank(
            ascending=False,
            method="min",
            na_option="bottom",
        )
    leaderboard = leaderboard[LEADERBOARD_COLUMNS]
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


def scan_command(args: argparse.Namespace) -> int:
    try:
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


def event_study_command(args: argparse.Namespace) -> int:
    try:
        _universe, _leaderboard, analysis_frames, warnings = load_and_analyze(
            args.config,
            data_dir=args.data_dir,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        print(f"Event study failed: {exc}")
        return 1

    summary, _records = run_event_study(analysis_frames)
    paths = export_event_study_reports(summary, report_dir=args.report_dir)
    print(f"Wrote event study CSV: {paths['csv']}")
    print(f"Wrote event study HTML: {paths['html']}")
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
    scan.set_defaults(func=scan_command)

    event_study = subparsers.add_parser("event-study", help="Run simple signal event studies.")
    add_common_arguments(event_study)
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
