from pathlib import Path

import pandas as pd

from riskflow.data_loader import load_ohlcv_csv


def test_load_ohlcv_csv_accepts_tradingview_column_names(tmp_path: Path):
    csv_path = tmp_path / "DOGE_1d.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,Open,High,Low,Close,Volume",
                "2024-01-01,1,2,0.5,1.5,100",
                "2024-01-02,1.5,2.5,1,2,200",
            ]
        ),
        encoding="utf-8",
    )

    frame = load_ohlcv_csv(csv_path)

    assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert frame.index[0] == pd.Timestamp("2024-01-01")
    assert frame.loc[pd.Timestamp("2024-01-02"), "close"] == 2.0


def test_load_ohlcv_csv_defaults_missing_volume_to_zero(tmp_path: Path):
    csv_path = tmp_path / "BRETT_1d.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Date,Open,High,Low,Close",
                "2024-01-01,1,2,0.5,1.5",
            ]
        ),
        encoding="utf-8",
    )

    frame = load_ohlcv_csv(csv_path)

    assert frame.loc[pd.Timestamp("2024-01-01"), "volume"] == 0.0


def test_load_ohlcv_csv_defaults_blank_volume_to_zero(tmp_path: Path):
    csv_path = tmp_path / "SHIB_1d.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,Volume",
                "2024-01-01,1,2,0.5,1.5,",
            ]
        ),
        encoding="utf-8",
    )

    frame = load_ohlcv_csv(csv_path)

    assert frame.loc[pd.Timestamp("2024-01-01"), "volume"] == 0.0


def test_load_ohlcv_csv_accepts_tradingview_unix_timestamp(tmp_path: Path):
    csv_path = tmp_path / "PEPE_1d.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "1704067200,1,2,0.5,1.5,100",
                "1704153600,1.5,2.5,1,2,200",
            ]
        ),
        encoding="utf-8",
    )

    frame = load_ohlcv_csv(csv_path)

    assert frame.index[0] == pd.Timestamp("2024-01-01")
    assert frame.index[1] == pd.Timestamp("2024-01-02")
