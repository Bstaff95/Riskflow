from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import UniverseConfig
from .data_loader import find_symbol_csv, load_ohlcv_csv


TIMEFRAME_RULES = {
    "1w": {"rule": "W-MON", "origin": "start_day"},
    "3d": {"rule": "3D", "origin": pd.Timestamp("2000-01-01")},
    "12h": {"rule": "12h", "origin": "start_day"},
    "4h": {"rule": "4h", "origin": "start_day"},
}

RESEARCH_MTF_DERIVATIONS = {
    "1d": ("1w", "3d"),
    "1h": ("12h", "4h"),
}


def normalize_timeframe(timeframe: str) -> str:
    return timeframe.strip().lower()


def resample_ohlcv(frame: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
    timeframe = normalize_timeframe(target_timeframe)
    if timeframe not in TIMEFRAME_RULES:
        supported = ", ".join(sorted(TIMEFRAME_RULES))
        raise ValueError(f"Unsupported resample timeframe '{target_timeframe}'. Supported: {supported}")

    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("resample_ohlcv requires a DatetimeIndex")

    source = frame.sort_index()
    rule_config = TIMEFRAME_RULES[timeframe]
    grouped = source.resample(
        rule_config["rule"],
        label="left",
        closed="left",
        origin=rule_config["origin"],
    )
    output = pd.DataFrame(
        {
            "open": grouped["open"].first(),
            "high": grouped["high"].max(),
            "low": grouped["low"].min(),
            "close": grouped["close"].last(),
            "volume": grouped["volume"].sum(min_count=1),
        }
    )
    output["volume"] = output["volume"].fillna(0.0)
    output = output.dropna(subset=["open", "high", "low", "close"])
    return output


def write_ohlcv_csv(frame: pd.DataFrame, path: str | Path) -> None:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    output = frame.reset_index().rename(columns={frame.index.name or "index": "date"})
    if output.columns[0] != "date":
        output = output.rename(columns={output.columns[0]: "date"})
    output.to_csv(csv_path, index=False)


def resample_universe(
    universe: UniverseConfig,
    data_dir: str | Path,
    from_timeframe: str,
    to_timeframes: list[str] | tuple[str, ...],
) -> tuple[list[Path], list[str]]:
    directory = Path(data_dir)
    source_timeframe = normalize_timeframe(from_timeframe)
    target_timeframes = [normalize_timeframe(timeframe) for timeframe in to_timeframes]
    written: list[Path] = []
    warnings: list[str] = []

    for asset in universe.assets:
        source_path = find_symbol_csv(asset.symbol, directory, timeframe=source_timeframe)
        if source_path is None:
            warnings.append(f"Missing source CSV for {asset.symbol}_{source_timeframe} in {directory}")
            continue

        try:
            source = load_ohlcv_csv(source_path)
        except Exception as exc:
            warnings.append(f"Failed to load {asset.symbol} from {source_path}: {exc}")
            continue

        for target_timeframe in target_timeframes:
            try:
                resampled = resample_ohlcv(source, target_timeframe)
            except Exception as exc:
                warnings.append(f"Failed to resample {asset.symbol} to {target_timeframe}: {exc}")
                continue

            output_path = directory / f"{asset.symbol.upper()}_{target_timeframe}.csv"
            write_ohlcv_csv(resampled, output_path)
            written.append(output_path)

    return written, warnings


def research_mtf_derivations() -> list[tuple[str, tuple[str, ...]]]:
    return list(RESEARCH_MTF_DERIVATIONS.items())
