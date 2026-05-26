from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AssetConfig:
    symbol: str
    name: str
    sector: str
    subgroup: str


@dataclass(frozen=True)
class BenchmarkConfig:
    type: str = "equal_weight_basket"
    name: str = "MEME_BASKET"
    role: str = "opportunity_cost"
    exclude_self: bool = False


@dataclass(frozen=True)
class WeightSettings:
    price_weight: float = 1.20
    relative_weight: float = 0.65
    risk_weight: float = 0.85


@dataclass(frozen=True)
class IndicatorSettings:
    z_len: int = 200
    component_z_clamp: float = 3.5
    use_risk: bool = False
    viscosity_lookback: int = 20
    viscosity_fast: int = 2
    viscosity_slow: int = 34
    viscosity_impulse_boost: float = 0.65
    viscosity_zero_zone_boost: float = 0.35
    velocity_weight: float = 0.55
    slope_weight: float = 0.25
    accel_weight: float = 0.08
    gradient_smooth_len: int = 3
    gradient_smooth_blend: float = 0.55


@dataclass(frozen=True)
class CompressionSettings:
    length: int = 20
    percentile_window: int = 252


@dataclass(frozen=True)
class UniverseConfig:
    name: str
    benchmark: BenchmarkConfig
    min_active_members: int
    assets: list[AssetConfig]
    weights: WeightSettings = field(default_factory=WeightSettings)
    indicator_settings: IndicatorSettings = field(default_factory=IndicatorSettings)
    compression_settings: CompressionSettings = field(default_factory=CompressionSettings)

    @property
    def asset_by_symbol(self) -> dict[str, AssetConfig]:
        return {asset.symbol: asset for asset in self.assets}


def _known_dataclass_kwargs(cls: type, values: dict[str, Any]) -> dict[str, Any]:
    field_names = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
    return {key: value for key, value in values.items() if key in field_names}


def load_universe_config(path: str | Path) -> UniverseConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    benchmark = BenchmarkConfig(**_known_dataclass_kwargs(BenchmarkConfig, raw.get("benchmark", {})))
    weights = WeightSettings(**_known_dataclass_kwargs(WeightSettings, raw.get("default_weights", {})))
    indicator_settings = IndicatorSettings(
        **_known_dataclass_kwargs(IndicatorSettings, raw.get("default_indicator_settings", {}))
    )
    compression_settings = CompressionSettings(
        **_known_dataclass_kwargs(CompressionSettings, raw.get("default_compression_settings", {}))
    )
    assets = [
        AssetConfig(
            symbol=str(asset["symbol"]).upper(),
            name=str(asset.get("name", asset["symbol"])),
            sector=str(asset.get("sector", "")),
            subgroup=str(asset.get("subgroup", "")),
        )
        for asset in raw.get("assets", [])
    ]

    if not assets:
        raise ValueError(f"No assets found in config: {config_path}")

    return UniverseConfig(
        name=str(raw.get("name", config_path.stem)),
        benchmark=benchmark,
        min_active_members=int(raw.get("min_active_members", 3)),
        assets=assets,
        weights=weights,
        indicator_settings=indicator_settings,
        compression_settings=compression_settings,
    )
