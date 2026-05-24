from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import UniverseConfig


REQUIRED_OHLCV_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def find_symbol_csv(symbol: str, data_dir: str | Path, timeframe: str = "1d") -> Path | None:
    directory = Path(data_dir)
    symbol_upper = symbol.upper()
    candidates = [
        directory / f"{symbol_upper}_{timeframe}.csv",
        directory / f"{symbol_upper}.csv",
        directory / f"{symbol_upper.lower()}_{timeframe}.csv",
        directory / f"{symbol_upper.lower()}.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    if not directory.exists():
        return None

    for candidate in directory.glob("*.csv"):
        stem = candidate.stem.upper()
        if stem == symbol_upper or stem == f"{symbol_upper}_{timeframe.upper()}":
            return candidate
    return None


def load_ohlcv_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    frame = pd.read_csv(csv_path)
    frame.columns = [str(column).strip().lower() for column in frame.columns]

    missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{csv_path} missing required columns: {missing}")

    frame["date"] = pd.to_datetime(frame["date"], utc=False)
    frame = frame.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    frame = frame.set_index("date")

    for column in REQUIRED_OHLCV_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame[list(REQUIRED_OHLCV_COLUMNS[1:])]


def load_universe_ohlcv(
    universe: UniverseConfig,
    data_dir: str | Path = "data/raw",
    timeframe: str = "1d",
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    frames: dict[str, pd.DataFrame] = {}
    warnings: list[str] = []

    for asset in universe.assets:
        csv_path = find_symbol_csv(asset.symbol, data_dir=data_dir, timeframe=timeframe)
        if csv_path is None:
            warnings.append(f"Missing CSV for {asset.symbol} in {Path(data_dir)}")
            continue
        try:
            frames[asset.symbol] = load_ohlcv_csv(csv_path)
        except Exception as exc:  # pragma: no cover - message is exercised through CLI paths.
            warnings.append(f"Failed to load {asset.symbol} from {csv_path}: {exc}")

    return frames, warnings

