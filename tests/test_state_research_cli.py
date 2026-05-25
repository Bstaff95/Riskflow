from pathlib import Path

import pandas as pd

from riskflow.cli import main


def _write_csv(path: Path, start: float) -> None:
    dates = pd.date_range("2024-01-01", periods=45, freq="D")
    close = [start + idx * 0.5 for idx in range(45)]
    lines = ["date,open,high,low,close,volume"]
    for date, value in zip(dates, close):
        lines.append(f"{date.date()},{value},{value * 1.02},{value * 0.98},{value},1000")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_state_research_cli_creates_report_files(tmp_path: Path):
    config_path = tmp_path / "universe.yaml"
    data_dir = tmp_path / "raw"
    report_dir = tmp_path / "reports"
    obsidian_dir = tmp_path / "obsidian"
    data_dir.mkdir()
    _write_csv(data_dir / "AAA_1d.csv", 100.0)
    _write_csv(data_dir / "BBB_1d.csv", 50.0)
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
            "state-research",
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
        ]
    )

    assert exit_code == 0
    assert (report_dir / "state_research_summary.csv").exists()
    assert (report_dir / "state_research_summary.html").exists()
    assert (report_dir / "state_research_records.csv").exists()
    assert (report_dir / "state_transition_matrix.csv").exists()
    assert (obsidian_dir / "reports" / "latest_state_research.md").exists()
