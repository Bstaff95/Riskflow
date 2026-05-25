from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import UniverseConfig


LEADERBOARD_CSV = "latest_meme_leaderboard.csv"
LEADERBOARD_HTML = "latest_meme_leaderboard.html"
OBSIDIAN_SCAN_MD = "latest_meme_scan.md"
EVENT_SUMMARY_CSV = "event_study_summary.csv"
EVENT_SUMMARY_HTML = "event_study_summary.html"
SIGNAL_RESEARCH_SUMMARY_CSV = "signal_research_summary.csv"
SIGNAL_RESEARCH_SUMMARY_HTML = "signal_research_summary.html"
SIGNAL_RESEARCH_RECORDS_CSV = "signal_research_records.csv"
SETUP_RESEARCH_SUMMARY_CSV = "setup_research_summary.csv"
SETUP_RESEARCH_SUMMARY_HTML = "setup_research_summary.html"
SETUP_RESEARCH_RECORDS_CSV = "setup_research_records.csv"
STATE_RESEARCH_SUMMARY_CSV = "state_research_summary.csv"
STATE_RESEARCH_SUMMARY_HTML = "state_research_summary.html"
STATE_RESEARCH_RECORDS_CSV = "state_research_records.csv"
STATE_TRANSITION_MATRIX_CSV = "state_transition_matrix.csv"
OBSIDIAN_STATE_RESEARCH_MD = "latest_state_research.md"
SCORE_RESEARCH_RECORDS_CSV = "score_research_records.csv"
SCORE_RESEARCH_BUCKET_SUMMARY_CSV = "score_research_bucket_summary.csv"
SCORE_RESEARCH_IC_SUMMARY_CSV = "score_research_ic_summary.csv"
SCORE_RESEARCH_SCORE_SUMMARY_CSV = "score_research_score_summary.csv"
SCORE_RESEARCH_SUMMARY_HTML = "score_research_summary.html"
OBSIDIAN_SCORE_RESEARCH_MD = "latest_score_research.md"


def _format_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def dataframe_to_markdown(frame: pd.DataFrame, columns: list[str] | None = None, max_rows: int = 10) -> str:
    if columns is None:
        columns = list(frame.columns)
    if frame.empty:
        return "_None._"

    visible = frame.loc[:, [column for column in columns if column in frame.columns]].head(max_rows)
    header = "| " + " | ".join(visible.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(visible.columns)) + " |"
    rows = [
        "| " + " | ".join(_format_value(value) for value in row) + " |"
        for row in visible.to_numpy()
    ]
    return "\n".join([header, separator, *rows])


def write_html_report(frame: pd.DataFrame, path: str | Path, title: str, warnings: list[str] | None = None) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    warning_html = ""
    if warnings:
        warning_items = "\n".join(f"<li>{warning}</li>" for warning in warnings)
        warning_html = f"<h2>Warnings</h2><ul>{warning_items}</ul>"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #171717; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: right; }}
    th {{ background: #f4f4f4; position: sticky; top: 0; }}
    td:first-child, th:first-child, td:nth-child(2), th:nth-child(2), td:nth-child(12), th:nth-child(12), td:last-child, th:last-child {{ text-align: left; }}
    .meta {{ color: #555; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="meta">Generated {datetime.now().isoformat(timespec="seconds")}</p>
  {warning_html}
  {frame.to_html(index=False, escape=True, border=0, float_format=lambda value: f"{value:.4f}")}
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def build_obsidian_scan_report(
    leaderboard: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    columns = [
        "symbol",
        "name",
        "state",
        "state_confidence",
        "state_reason",
        "setup_state_v0",
        "opportunity_score",
        "leader_quality_score",
        "compression_quality_score",
        "relative_accumulation_score",
        "setup_readiness_score",
        "extension_risk_score",
        "data_quality_score",
        "trader_score_v0",
        "trader_rank",
        "final_signal",
        "relative_component",
        "compression_score",
        "state_tags",
        "setup_tags",
    ]
    top_opportunities = leaderboard.sort_values("opportunity_score", ascending=False)
    strongest = leaderboard.sort_values("relative_component", ascending=False)
    compressed_emerging = leaderboard[
        (leaderboard["compression_score"] >= 70.0)
        & leaderboard["state"].isin(["Compression", "Relative Accumulation", "Emerging Leader"])
    ].sort_values("opportunity_score", ascending=False)
    overheated = leaderboard[leaderboard["state"] == "Overheated"].sort_values("final_signal", ascending=False)
    laggards = leaderboard.sort_values("final_signal", ascending=True)

    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    concept_links = "\n".join(
        [
            "- [[Relative Accumulation]]",
            "- [[Compression Before Repricing]]",
            "- [[Emerging Leader]]",
            "- [[Confirmed Leader]]",
            "- [[Meme Sector]]",
            "- [[Opportunity Score]]",
            "- [[Riskflow]]",
        ]
    )

    return f"""# Latest Meme Scan

Generated: {generated}
Universe: {universe.name}
Benchmark: {universe.benchmark.name}

## Top Opportunities
{dataframe_to_markdown(top_opportunities, columns=columns, max_rows=10)}

## Strongest Relative Leaders
{dataframe_to_markdown(strongest, columns=columns, max_rows=10)}

## Compressed Emerging Leaders
{dataframe_to_markdown(compressed_emerging, columns=columns, max_rows=10)}

## Overheated Leaders
{dataframe_to_markdown(overheated, columns=columns, max_rows=10)}

## Laggards
{dataframe_to_markdown(laggards, columns=columns, max_rows=10)}

## Warnings
{warning_section}

## Concept Links
{concept_links}
"""


def export_scan_reports(
    leaderboard: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str],
    report_dir: str | Path = "reports",
    obsidian_dir: str | Path = "obsidian",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    obsidian_report_path = Path(obsidian_dir) / "reports"
    report_path.mkdir(parents=True, exist_ok=True)
    obsidian_report_path.mkdir(parents=True, exist_ok=True)

    csv_path = report_path / LEADERBOARD_CSV
    html_path = report_path / LEADERBOARD_HTML
    markdown_path = obsidian_report_path / OBSIDIAN_SCAN_MD

    leaderboard.to_csv(csv_path, index=False)
    write_html_report(leaderboard, html_path, "Latest Meme Leaderboard", warnings=warnings)
    markdown_path.write_text(build_obsidian_scan_report(leaderboard, universe, warnings), encoding="utf-8")

    return {
        "csv": csv_path,
        "html": html_path,
        "obsidian": markdown_path,
    }


def export_event_study_reports(
    summary: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    csv_path = report_path / EVENT_SUMMARY_CSV
    html_path = report_path / EVENT_SUMMARY_HTML
    summary.to_csv(csv_path, index=False)
    write_html_report(summary, html_path, "Meme Event Study Summary")
    return {"csv": csv_path, "html": html_path}


def export_signal_research_reports(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    summary_csv_path = report_path / SIGNAL_RESEARCH_SUMMARY_CSV
    summary_html_path = report_path / SIGNAL_RESEARCH_SUMMARY_HTML
    records_csv_path = report_path / SIGNAL_RESEARCH_RECORDS_CSV

    summary.to_csv(summary_csv_path, index=False)
    records.to_csv(records_csv_path, index=False)
    write_html_report(summary, summary_html_path, "Layer 3 Signal Research Summary")
    return {
        "summary_csv": summary_csv_path,
        "summary_html": summary_html_path,
        "records_csv": records_csv_path,
    }


def export_setup_research_reports(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    summary_csv_path = report_path / SETUP_RESEARCH_SUMMARY_CSV
    summary_html_path = report_path / SETUP_RESEARCH_SUMMARY_HTML
    records_csv_path = report_path / SETUP_RESEARCH_RECORDS_CSV

    summary.to_csv(summary_csv_path, index=False)
    records.to_csv(records_csv_path, index=False)
    write_html_report(summary, summary_html_path, "Layer 4 Setup Research Summary")
    return {
        "summary_csv": summary_csv_path,
        "summary_html": summary_html_path,
        "records_csv": records_csv_path,
    }


def build_obsidian_state_research_report(
    summary: pd.DataFrame,
    transition_matrix: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    summary_columns = [
        "state",
        "sample_size",
        "classification",
        "median_forward_relative_return_14",
        "median_forward_relative_return_30",
        "hit_rate_forward_relative_return_14",
        "median_max_drawdown_30",
        "avg_state_duration",
        "most_common_next_state",
        "transition_to_emerging_leader_rate",
        "transition_to_breakdown_rate",
        "notes",
    ]
    transition_columns = [
        "from_state",
        "to_state",
        "transition_count",
        "transition_probability",
        "median_duration_before_transition",
    ]
    useful = summary[summary["classification"].isin(["useful", "watchlist"])].sort_values(
        ["classification", "median_forward_relative_return_30"],
        ascending=[True, False],
    )
    fragile = summary[summary["classification"].isin(["fragile", "inconclusive"])].sort_values(
        ["classification", "sample_size"],
        ascending=[True, False],
    )
    active_transitions = transition_matrix[transition_matrix["transition_count"] > 0].sort_values(
        ["transition_count", "transition_probability"],
        ascending=[False, False],
    )

    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    return f"""# Latest State Research

Generated: {generated}
Universe: {universe.name}
Benchmark: {universe.benchmark.name}
State Model: state_model_v0

## State Evidence Summary
{dataframe_to_markdown(summary, columns=summary_columns, max_rows=20)}

## Useful / Watchlist States
{dataframe_to_markdown(useful, columns=summary_columns, max_rows=20)}

## Fragile / Inconclusive States
{dataframe_to_markdown(fragile, columns=summary_columns, max_rows=20)}

## Most Common Transitions
{dataframe_to_markdown(active_transitions, columns=transition_columns, max_rows=20)}

## Warnings
{warning_section}

## Concept Links
- [[Relative Accumulation]]
- [[Emerging Leader]]
- [[Confirmed Leader]]
- [[Compression Before Repricing]]
- [[Capital Flow Graph]]
- [[Riskflow]]
"""


def export_state_research_reports(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    transition_matrix: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str],
    report_dir: str | Path = "reports",
    obsidian_dir: str | Path = "obsidian",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    obsidian_report_path = Path(obsidian_dir) / "reports"
    report_path.mkdir(parents=True, exist_ok=True)
    obsidian_report_path.mkdir(parents=True, exist_ok=True)

    summary_csv_path = report_path / STATE_RESEARCH_SUMMARY_CSV
    summary_html_path = report_path / STATE_RESEARCH_SUMMARY_HTML
    records_csv_path = report_path / STATE_RESEARCH_RECORDS_CSV
    transition_csv_path = report_path / STATE_TRANSITION_MATRIX_CSV
    obsidian_path = obsidian_report_path / OBSIDIAN_STATE_RESEARCH_MD

    summary.to_csv(summary_csv_path, index=False)
    records.to_csv(records_csv_path, index=False)
    transition_matrix.to_csv(transition_csv_path, index=False)
    write_html_report(summary, summary_html_path, "Layer 5 State Research Summary", warnings=warnings)
    obsidian_path.write_text(
        build_obsidian_state_research_report(summary, transition_matrix, universe, warnings),
        encoding="utf-8",
    )
    return {
        "summary_csv": summary_csv_path,
        "summary_html": summary_html_path,
        "records_csv": records_csv_path,
        "transition_csv": transition_csv_path,
        "obsidian": obsidian_path,
    }


def build_obsidian_score_research_report(
    score_summary: pd.DataFrame,
    bucket_summary: pd.DataFrame,
    ic_summary: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    score_columns = [
        "score_id",
        "classification",
        "top_bucket",
        "top_bucket_sample_size",
        "top_bucket_median_forward_relative_return_14",
        "top_bucket_median_forward_relative_return_30",
        "top_minus_bottom_spread_14",
        "top_minus_bottom_spread_30",
        "mean_rank_ic_14",
        "positive_rank_ic_share_14",
        "notes",
    ]
    bucket_columns = [
        "score_id",
        "bucket",
        "sample_size",
        "classification",
        "median_forward_relative_return_14",
        "median_forward_relative_return_30",
        "hit_rate_forward_relative_return_14",
        "top_minus_bottom_spread_30",
        "median_max_drawdown_30",
        "notes",
    ]
    ic_columns = [
        "score_id",
        "horizon",
        "valid_dates",
        "mean_rank_ic",
        "median_rank_ic",
        "positive_rank_ic_share",
        "icir",
        "classification",
    ]
    useful_scores = score_summary[score_summary["classification"].isin(["useful", "watchlist"])].sort_values(
        ["classification", "top_minus_bottom_spread_30"],
        ascending=[True, False],
    )
    fragile_scores = score_summary[score_summary["classification"].isin(["fragile", "inconclusive"])].sort_values(
        ["classification", "top_bucket_sample_size"],
        ascending=[True, False],
    )
    top_buckets = bucket_summary.sort_values(["score_id", "bucket"], ascending=[True, False]).groupby("score_id").head(1)

    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    return f"""# Latest Score Research

Generated: {generated}
Universe: {universe.name}
Benchmark: {universe.benchmark.name}

## Score Evidence Summary
{dataframe_to_markdown(score_summary, columns=score_columns, max_rows=20)}

## Useful / Watchlist Scores
{dataframe_to_markdown(useful_scores, columns=score_columns, max_rows=20)}

## Fragile / Inconclusive Scores
{dataframe_to_markdown(fragile_scores, columns=score_columns, max_rows=20)}

## Top Buckets
{dataframe_to_markdown(top_buckets, columns=bucket_columns, max_rows=20)}

## Rank IC
{dataframe_to_markdown(ic_summary, columns=ic_columns, max_rows=40)}

## Warnings
{warning_section}

## Concept Links
- [[Opportunity Score]]
- [[Relative Accumulation]]
- [[Compression Before Repricing]]
- [[Emerging Leader]]
- [[Riskflow]]
"""


def export_score_research_reports(
    score_summary: pd.DataFrame,
    bucket_summary: pd.DataFrame,
    ic_summary: pd.DataFrame,
    records: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str],
    report_dir: str | Path = "reports",
    obsidian_dir: str | Path = "obsidian",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    obsidian_report_path = Path(obsidian_dir) / "reports"
    report_path.mkdir(parents=True, exist_ok=True)
    obsidian_report_path.mkdir(parents=True, exist_ok=True)

    records_csv_path = report_path / SCORE_RESEARCH_RECORDS_CSV
    bucket_csv_path = report_path / SCORE_RESEARCH_BUCKET_SUMMARY_CSV
    ic_csv_path = report_path / SCORE_RESEARCH_IC_SUMMARY_CSV
    score_csv_path = report_path / SCORE_RESEARCH_SCORE_SUMMARY_CSV
    summary_html_path = report_path / SCORE_RESEARCH_SUMMARY_HTML
    obsidian_path = obsidian_report_path / OBSIDIAN_SCORE_RESEARCH_MD

    records.to_csv(records_csv_path, index=False)
    bucket_summary.to_csv(bucket_csv_path, index=False)
    ic_summary.to_csv(ic_csv_path, index=False)
    score_summary.to_csv(score_csv_path, index=False)
    write_html_report(score_summary, summary_html_path, "Layer 6 Score Research Summary", warnings=warnings)
    obsidian_path.write_text(
        build_obsidian_score_research_report(score_summary, bucket_summary, ic_summary, universe, warnings),
        encoding="utf-8",
    )
    return {
        "records_csv": records_csv_path,
        "bucket_summary_csv": bucket_csv_path,
        "ic_summary_csv": ic_csv_path,
        "score_summary_csv": score_csv_path,
        "summary_html": summary_html_path,
        "obsidian": obsidian_path,
    }
