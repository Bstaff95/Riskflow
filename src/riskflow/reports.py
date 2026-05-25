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
EVENT_RECORDS_CSV = "event_study_records.csv"
OBSIDIAN_EVENT_STUDY_MD = "latest_event_study.md"
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
MTF_RESEARCH_RECORDS_CSV = "mtf_research_records.csv"
MTF_RESEARCH_SUMMARY_CSV = "mtf_research_summary.csv"
MTF_RESEARCH_SUMMARY_HTML = "mtf_research_summary.html"
OBSIDIAN_MTF_RESEARCH_MD = "latest_mtf_research.md"
FLOW_GRAPH_NODES_CSV = "flow_graph_nodes.csv"
FLOW_GRAPH_EDGES_CSV = "flow_graph_edges.csv"
FLOW_GRAPH_CHAINS_CSV = "flow_graph_chains.csv"
FLOW_RESEARCH_RECORDS_CSV = "flow_research_records.csv"
FLOW_RESEARCH_SUMMARY_CSV = "flow_research_summary.csv"
FLOW_RESEARCH_SUMMARY_HTML = "flow_research_summary.html"
OBSIDIAN_FLOW_GRAPH_MD = "latest_flow_graph.md"
TRANSITION_RESEARCH_RECORDS_CSV = "transition_research_records.csv"
TRANSITION_RESEARCH_SUMMARY_CSV = "transition_research_summary.csv"
TRANSITION_MATRIX_UNCONDITIONAL_CSV = "transition_matrix_unconditional.csv"
TRANSITION_MATRIX_CONDITIONED_CSV = "transition_matrix_conditioned.csv"
TRANSITION_RESEARCH_SUMMARY_HTML = "transition_research_summary.html"
OBSIDIAN_TRANSITION_RESEARCH_MD = "latest_transition_research.md"


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
    mtf_columns = [
        "mtf_leader_context",
        "mtf_trader_context",
        "mtf_notes",
        "mtf_conflict_tags",
    ]
    columns.extend([column for column in mtf_columns if column in leaderboard.columns])
    obsidian_names = {
        "mtf_leader_context": "Leader Context",
        "mtf_trader_context": "Trader Context",
        "mtf_notes": "MTF Note",
        "mtf_conflict_tags": "Conflict Tags",
    }
    markdown_columns = [obsidian_names.get(column, column) for column in columns]
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
{dataframe_to_markdown(top_opportunities.rename(columns=obsidian_names), columns=markdown_columns, max_rows=10)}

## Strongest Relative Leaders
{dataframe_to_markdown(strongest.rename(columns=obsidian_names), columns=markdown_columns, max_rows=10)}

## Compressed Emerging Leaders
{dataframe_to_markdown(compressed_emerging.rename(columns=obsidian_names), columns=markdown_columns, max_rows=10)}

## Overheated Leaders
{dataframe_to_markdown(overheated.rename(columns=obsidian_names), columns=markdown_columns, max_rows=10)}

## Laggards
{dataframe_to_markdown(laggards.rename(columns=obsidian_names), columns=markdown_columns, max_rows=10)}

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


def build_obsidian_event_study_report(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    columns = [
        "event",
        "classification",
        "sample_size",
        "unique_symbols",
        "unique_event_clusters",
        "median_forward_relative_return_14",
        "median_forward_relative_return_30",
        "hit_rate_forward_relative_return_14",
        "median_max_drawdown_30",
        "max_symbol_event_share",
        "max_cluster_event_share",
        "notes",
    ]
    useful = summary[summary["classification"].isin(["useful", "watchlist"])].sort_values(
        ["classification", "median_forward_relative_return_30"],
        ascending=[True, False],
    )
    fragile = summary[summary["classification"].isin(["fragile", "inconclusive"])].sort_values(
        ["classification", "sample_size"],
        ascending=[True, False],
    )
    concentrated = summary[
        (summary["max_symbol_event_share"] > 0.55)
        | (summary["max_cluster_event_share"] > 0.60)
    ].sort_values("sample_size", ascending=False)

    verdict = "No events passed useful/watchlist gates yet."
    if not useful.empty:
        verdict = f"{len(useful)} events reached useful/watchlist evidence gates. Treat as research evidence, not trading advice."

    promotion = "No event should be promoted without side-by-side evidence against its incumbent, concentration checks, and a written promotion note."
    if not summary[summary["classification"] == "useful"].empty:
        promotion = "Some events are useful candidates, but promotion still requires baseline comparison and reviewer approval."

    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    return f"""# Latest Event Study

Generated: {generated}
Universe: {universe.name}
Benchmark: {universe.benchmark.name}
Records: {len(records)}

## Verdict
{verdict}

## Useful / Watchlist Events
{dataframe_to_markdown(useful, columns=columns, max_rows=20)}

## Fragile / Inconclusive Events
{dataframe_to_markdown(fragile, columns=columns, max_rows=20)}

## Concentration Risks
{dataframe_to_markdown(concentrated, columns=columns, max_rows=20)}

## Promotion Eligibility
{promotion}

## Next Research Questions
- Rerun with ex-target baskets once Layer 2 benchmark hardening exists.
- Compare useful events against simple baselines before promotion.
- Preserve versioned event ids before changing any trigger threshold.

## Warnings
{warning_section}

## Concept Links
- [[Opportunity Score]]
- [[Relative Accumulation]]
- [[Compression Before Repricing]]
- [[Capital Flow Graph]]
- [[Riskflow]]
"""


def export_event_study_reports(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
    report_dir: str | Path = "reports",
    obsidian_dir: str | Path = "obsidian",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    obsidian_report_path = Path(obsidian_dir) / "reports"
    report_path.mkdir(parents=True, exist_ok=True)
    obsidian_report_path.mkdir(parents=True, exist_ok=True)
    csv_path = report_path / EVENT_SUMMARY_CSV
    records_path = report_path / EVENT_RECORDS_CSV
    html_path = report_path / EVENT_SUMMARY_HTML
    obsidian_path = obsidian_report_path / OBSIDIAN_EVENT_STUDY_MD
    summary.to_csv(csv_path, index=False)
    records.to_csv(records_path, index=False)
    write_html_report(summary, html_path, "Meme Event Study Summary", warnings=warnings)
    obsidian_path.write_text(
        build_obsidian_event_study_report(summary, records, universe, warnings),
        encoding="utf-8",
    )
    return {
        "csv": csv_path,
        "records_csv": records_path,
        "html": html_path,
        "obsidian": obsidian_path,
    }


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


def build_obsidian_mtf_research_report(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    columns = [
        "mtf_event",
        "classification",
        "aligned_sample_size",
        "non_aligned_sample_size",
        "aligned_minus_non_aligned_spread_14",
        "aligned_minus_non_aligned_spread_30",
        "aligned_hit_rate_forward_relative_return_14",
        "non_aligned_hit_rate_forward_relative_return_14",
        "aligned_median_max_drawdown_30",
        "non_aligned_median_max_drawdown_30",
        "notes",
    ]
    useful = summary[summary["classification"].isin(["useful", "watchlist"])].sort_values(
        ["classification", "aligned_minus_non_aligned_spread_30"],
        ascending=[True, False],
    )
    fragile = summary[summary["classification"].isin(["fragile", "inconclusive"])].sort_values(
        ["classification", "sample_size"],
        ascending=[True, False],
    )
    concentrated = summary[
        (summary["max_symbol_share"] > 0.55)
        | (summary["max_cluster_share"] > 0.60)
    ].sort_values("sample_size", ascending=False)

    verdict = "No MTF context event has enough useful/watchlist evidence yet."
    if not useful.empty:
        verdict = f"{len(useful)} MTF comparisons reached useful/watchlist evidence gates. Treat as context evidence, not a ranking change."

    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    return f"""# Latest Multi-Timeframe Research

Generated: {generated}
Universe: {universe.name}
Benchmark: {universe.benchmark.name}
Records: {len(records)}

## Verdict
{verdict}

## Useful / Watchlist MTF Comparisons
{dataframe_to_markdown(useful, columns=columns, max_rows=20)}

## Fragile / Inconclusive MTF Comparisons
{dataframe_to_markdown(fragile, columns=columns, max_rows=20)}

## Concentration Risks
{dataframe_to_markdown(concentrated, columns=columns, max_rows=20)}

## Promotion Eligibility
MTF context cannot change production ranking until aligned groups beat matching non-aligned baselines on forward relative return, hit rate, drawdown, and concentration checks.

## Next Research Questions
- Rerun after ex-target baskets exist.
- Compare daily setup events with and without completed 3D/1W support.
- Check whether 4H reset context improves Trader Mode timing without worsening drawdown.

## Warnings
{warning_section}

## Concept Links
- [[Multi-Timeframe Context]]
- [[Event Studies]]
- [[Opportunity Score]]
- [[Riskflow]]
"""


def export_mtf_research_reports(
    summary: pd.DataFrame,
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

    records_csv_path = report_path / MTF_RESEARCH_RECORDS_CSV
    summary_csv_path = report_path / MTF_RESEARCH_SUMMARY_CSV
    summary_html_path = report_path / MTF_RESEARCH_SUMMARY_HTML
    obsidian_path = obsidian_report_path / OBSIDIAN_MTF_RESEARCH_MD

    records.to_csv(records_csv_path, index=False)
    summary.to_csv(summary_csv_path, index=False)
    write_html_report(summary, summary_html_path, "Layer 8 Multi-Timeframe Research Summary", warnings=warnings)
    obsidian_path.write_text(
        build_obsidian_mtf_research_report(summary, records, universe, warnings),
        encoding="utf-8",
    )
    return {
        "records_csv": records_csv_path,
        "summary_csv": summary_csv_path,
        "summary_html": summary_html_path,
        "obsidian": obsidian_path,
    }


def build_obsidian_flow_graph_report(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    chains: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    node_columns = ["node_id", "node_type", "symbol", "name", "sector", "subgroup", "state", "notes"]
    edge_columns = ["edge_id", "edge_type", "source_node_id", "target_node_id", "edge_state", "edge_confidence", "evidence_notes"]
    chain_columns = [
        "asset_symbol",
        "chain_label",
        "chain_support_score",
        "chain_path",
        "chain_alignment_tags",
        "chain_conflict_tags",
        "chain_confidence",
        "chain_notes",
    ]
    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    verdict = "Graph v0 is a structural/evidence sidecar. It infers relative leadership context, not literal capital flows."
    if not chains.empty:
        complete_chains = chains[chains["chain_label"] != "Incomplete Chain"]
        verdict = f"{len(complete_chains)} of {len(chains)} chains have measurable benchmark-parent context. Subgroup/sector parent support remains provisional."

    return f"""# Latest Flow Graph

Generated: {generated}
Universe: {universe.name}
Graph Model: capital_flow_graph_v0

## Verdict
{verdict}

## Chain Context
{dataframe_to_markdown(chains.sort_values("chain_support_score", ascending=False), columns=chain_columns, max_rows=30)}

## Nodes
{dataframe_to_markdown(nodes, columns=node_columns, max_rows=40)}

## Edges
{dataframe_to_markdown(edges, columns=edge_columns, max_rows=60)}

## Warnings
{warning_section}

## Notes
- This graph is table-based and local; no graph database is used.
- Current subgroup and sector nodes are structural placeholders until Layer 2 adds independent subgroup/sector baskets.
- Do not read graph labels as probabilities or literal fund-flow proof.

## Concept Links
- [[Capital Flow Graph]]
- [[Relative Accumulation]]
- [[Compression Before Repricing]]
- [[Riskflow]]
"""


def export_flow_graph_reports(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    chains: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str],
    report_dir: str | Path = "reports",
    obsidian_dir: str | Path = "obsidian",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    obsidian_report_path = Path(obsidian_dir) / "reports"
    report_path.mkdir(parents=True, exist_ok=True)
    obsidian_report_path.mkdir(parents=True, exist_ok=True)

    nodes_csv_path = report_path / FLOW_GRAPH_NODES_CSV
    edges_csv_path = report_path / FLOW_GRAPH_EDGES_CSV
    chains_csv_path = report_path / FLOW_GRAPH_CHAINS_CSV
    obsidian_path = obsidian_report_path / OBSIDIAN_FLOW_GRAPH_MD

    nodes.to_csv(nodes_csv_path, index=False)
    edges.to_csv(edges_csv_path, index=False)
    chains.to_csv(chains_csv_path, index=False)
    obsidian_path.write_text(
        build_obsidian_flow_graph_report(nodes, edges, chains, universe, warnings),
        encoding="utf-8",
    )
    return {
        "nodes_csv": nodes_csv_path,
        "edges_csv": edges_csv_path,
        "chains_csv": chains_csv_path,
        "obsidian": obsidian_path,
    }


def build_obsidian_flow_research_report(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    columns = [
        "flow_event",
        "classification",
        "supportive_sample_size",
        "non_supportive_sample_size",
        "supportive_minus_non_supportive_spread_14",
        "supportive_minus_non_supportive_spread_30",
        "supportive_hit_rate_forward_relative_return_14",
        "non_supportive_hit_rate_forward_relative_return_14",
        "supportive_median_max_drawdown_30",
        "non_supportive_median_max_drawdown_30",
        "notes",
    ]
    useful = summary[summary["classification"].isin(["useful", "watchlist"])].sort_values(
        ["classification", "supportive_minus_non_supportive_spread_30"],
        ascending=[True, False],
    )
    fragile = summary[summary["classification"].isin(["fragile", "inconclusive"])].sort_values(
        ["classification", "sample_size"],
        ascending=[True, False],
    )
    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    verdict = "No flow-chain event has enough useful/watchlist evidence yet."
    if not useful.empty:
        verdict = f"{len(useful)} flow-chain comparisons reached useful/watchlist evidence gates. Treat as research evidence, not ranking logic."

    return f"""# Latest Flow Research

Generated: {generated}
Universe: {universe.name}
Graph Model: capital_flow_graph_v0
Records: {len(records)}

## Verdict
{verdict}

## Useful / Watchlist Flow Comparisons
{dataframe_to_markdown(useful, columns=columns, max_rows=20)}

## Fragile / Inconclusive Flow Comparisons
{dataframe_to_markdown(fragile, columns=columns, max_rows=20)}

## Promotion Eligibility
Flow-chain context cannot affect production ranking until supportive chains beat matched non-supportive baselines under Layer 7 evidence rules.

## Warnings
{warning_section}

## Concept Links
- [[Capital Flow Graph]]
- [[Event Studies]]
- [[Opportunity Score]]
- [[Riskflow]]
"""


def export_flow_research_reports(
    summary: pd.DataFrame,
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

    records_csv_path = report_path / FLOW_RESEARCH_RECORDS_CSV
    summary_csv_path = report_path / FLOW_RESEARCH_SUMMARY_CSV
    summary_html_path = report_path / FLOW_RESEARCH_SUMMARY_HTML
    obsidian_path = obsidian_report_path / OBSIDIAN_FLOW_GRAPH_MD

    records.to_csv(records_csv_path, index=False)
    summary.to_csv(summary_csv_path, index=False)
    write_html_report(summary, summary_html_path, "Layer 9 Flow Research Summary", warnings=warnings)
    obsidian_path.write_text(
        build_obsidian_flow_research_report(summary, records, universe, warnings),
        encoding="utf-8",
    )
    return {
        "records_csv": records_csv_path,
        "summary_csv": summary_csv_path,
        "summary_html": summary_html_path,
        "obsidian": obsidian_path,
    }


def build_obsidian_transition_research_report(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    unconditional: pd.DataFrame,
    conditioned: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str] | None = None,
) -> str:
    generated = datetime.now().isoformat(timespec="seconds")
    columns = [
        "from_state",
        "to_state",
        "classification",
        "sample_size",
        "observed_transition_rate",
        "wilson_80_lower",
        "wilson_80_upper",
        "median_duration_before_transition",
        "median_forward_relative_return_14",
        "median_forward_relative_return_30",
        "hit_rate_forward_relative_return_14",
        "median_max_drawdown_30",
        "notes",
    ]
    conditioned_columns = [
        "condition_type",
        "condition_group",
        "from_state",
        "to_state",
        "sample_size",
        "observed_transition_rate",
        "median_forward_relative_return_30",
        "classification",
        "notes",
    ]
    useful = summary[summary["classification"].isin(["useful", "watchlist"])].sort_values(
        ["classification", "median_forward_relative_return_30"],
        ascending=[True, False],
    )
    fragile = summary[summary["classification"].isin(["fragile", "inconclusive"])].sort_values(
        ["classification", "sample_size"],
        ascending=[True, False],
    )
    concentrated = summary[
        (summary["max_symbol_transition_share"] > 0.55)
        | (summary["max_cluster_transition_share"] > 0.60)
    ].sort_values("sample_size", ascending=False)
    top_conditioned = conditioned[conditioned["sample_size"] > 0].sort_values(
        ["classification", "sample_size"],
        ascending=[True, False],
    )

    verdict = "No transition pair has enough useful/watchlist evidence yet."
    if not useful.empty:
        verdict = f"{len(useful)} transition pairs reached useful/watchlist evidence gates. Treat as observed historical tendencies, not forecasts."

    warning_section = "_None._"
    if warnings:
        warning_section = "\n".join(f"- {warning}" for warning in warnings)

    return f"""# Latest Transition Research

Generated: {generated}
Universe: {universe.name}
Benchmark: {universe.benchmark.name}
Transition Model: transition_research_v0
Records: {len(records)}

## Verdict
{verdict}

## Useful / Watchlist Transitions
{dataframe_to_markdown(useful, columns=columns, max_rows=30)}

## Fragile / Inconclusive Transitions
{dataframe_to_markdown(fragile, columns=columns, max_rows=30)}

## Concentration Risks
{dataframe_to_markdown(concentrated, columns=columns, max_rows=20)}

## Conditioned Transition Evidence
{dataframe_to_markdown(top_conditioned, columns=conditioned_columns, max_rows=30)}

## Promotion Eligibility
Transition evidence cannot become product probability language until it survives sample-size, uncertainty, concentration, and out-of-sample stability checks.

## Warnings
{warning_section}

## Notes
- Observed transition rates are historical frequencies, not true probabilities or forecasts.
- Same-state persistence is handled as duration evidence, not as a state transition.
- Chain and MTF context are sidecar conditions only.

## Concept Links
- [[Lifecycle States]]
- [[Capital Flow Graph]]
- [[Event Studies]]
- [[Riskflow]]
"""


def export_transition_research_reports(
    summary: pd.DataFrame,
    records: pd.DataFrame,
    unconditional: pd.DataFrame,
    conditioned: pd.DataFrame,
    universe: UniverseConfig,
    warnings: list[str],
    report_dir: str | Path = "reports",
    obsidian_dir: str | Path = "obsidian",
) -> dict[str, Path]:
    report_path = Path(report_dir)
    obsidian_report_path = Path(obsidian_dir) / "reports"
    report_path.mkdir(parents=True, exist_ok=True)
    obsidian_report_path.mkdir(parents=True, exist_ok=True)

    records_csv_path = report_path / TRANSITION_RESEARCH_RECORDS_CSV
    summary_csv_path = report_path / TRANSITION_RESEARCH_SUMMARY_CSV
    unconditional_csv_path = report_path / TRANSITION_MATRIX_UNCONDITIONAL_CSV
    conditioned_csv_path = report_path / TRANSITION_MATRIX_CONDITIONED_CSV
    summary_html_path = report_path / TRANSITION_RESEARCH_SUMMARY_HTML
    obsidian_path = obsidian_report_path / OBSIDIAN_TRANSITION_RESEARCH_MD

    records.to_csv(records_csv_path, index=False)
    summary.to_csv(summary_csv_path, index=False)
    unconditional.to_csv(unconditional_csv_path, index=False)
    conditioned.to_csv(conditioned_csv_path, index=False)
    write_html_report(summary, summary_html_path, "Layer 10 Transition Research Summary", warnings=warnings)
    obsidian_path.write_text(
        build_obsidian_transition_research_report(summary, records, unconditional, conditioned, universe, warnings),
        encoding="utf-8",
    )
    return {
        "records_csv": records_csv_path,
        "summary_csv": summary_csv_path,
        "unconditional_csv": unconditional_csv_path,
        "conditioned_csv": conditioned_csv_path,
        "summary_html": summary_html_path,
        "obsidian": obsidian_path,
    }
