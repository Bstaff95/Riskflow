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
    columns = ["symbol", "name", "state", "opportunity_score", "final_signal", "relative_component", "compression_score"]
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
