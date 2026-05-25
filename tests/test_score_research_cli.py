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


def test_score_research_cli_creates_report_files(tmp_path: Path):
    config_path = tmp_path / "universe.yaml"
    data_dir = tmp_path / "raw"
    report_dir = tmp_path / "reports"
    obsidian_dir = tmp_path / "obsidian"
    data_dir.mkdir()
    for idx, symbol in enumerate(["AAA", "BBB", "CCC", "DDD", "EEE"]):
        _write_csv(data_dir / f"{symbol}_1d.csv", 50.0 + idx * 10.0, 0.4 + idx * 0.1)
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
  - symbol: CCC
    name: CCC
    sector: memes
    subgroup: test
  - symbol: DDD
    name: DDD
    sector: memes
    subgroup: test
  - symbol: EEE
    name: EEE
    sector: memes
    subgroup: test
""",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "score-research",
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
            "--bucket-count",
            "3",
            "--min-symbols-per-date",
            "3",
            "--min-bucket-sample-size",
            "1",
        ]
    )

    assert exit_code == 0
    assert (report_dir / "score_research_records.csv").exists()
    assert (report_dir / "score_research_bucket_summary.csv").exists()
    assert (report_dir / "score_research_ic_summary.csv").exists()
    assert (report_dir / "score_research_score_summary.csv").exists()
    assert (report_dir / "score_research_summary.html").exists()
    assert (obsidian_dir / "reports" / "latest_score_research.md").exists()
