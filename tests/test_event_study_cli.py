from pathlib import Path

import pandas as pd

from riskflow.cli import main


def _write_csv(path: Path, start: float, step: float) -> None:
    dates = pd.date_range("2024-01-01", periods=55, freq="D")
    close = [start + idx * step for idx in range(55)]
    lines = ["date,open,high,low,close,volume"]
    for date, value in zip(dates, close):
        lines.append(f"{date.date()},{value},{value * 1.02},{value * 0.98},{value},1000")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_event_study_cli_creates_summary_records_html_and_obsidian(tmp_path: Path):
    config_path = tmp_path / "universe.yaml"
    data_dir = tmp_path / "raw"
    report_dir = tmp_path / "reports"
    obsidian_dir = tmp_path / "obsidian"
    data_dir.mkdir()
    _write_csv(data_dir / "AAA_1d.csv", 100.0, 0.5)
    _write_csv(data_dir / "BBB_1d.csv", 50.0, 0.7)
    config_path.write_text(
        """
name: test_meme_universe
benchmark:
  type: equal_weight_basket
  name: MEME_BASKET
min_active_members: 1
assets:
  - symbol: AAA
    name: AAA
    sector: memes
    subgroup: test
  - symbol: BBB
    name: BBB
    sector: memes
    subgroup: test
""",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "event-study",
            "--config",
            str(config_path),
            "--data-dir",
            str(data_dir),
            "--report-dir",
            str(report_dir),
            "--obsidian-dir",
            str(obsidian_dir),
            "--timeframe",
            "1d",
            "--min-sample-size",
            "1",
            "--cooldown-bars",
            "0",
        ]
    )

    assert exit_code == 0
    assert (report_dir / "event_study_summary.csv").exists()
    assert (report_dir / "event_study_records.csv").exists()
    assert (report_dir / "event_study_summary.html").exists()
    assert (obsidian_dir / "reports" / "latest_event_study.md").exists()
