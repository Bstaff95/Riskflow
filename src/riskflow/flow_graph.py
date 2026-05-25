from __future__ import annotations

import numpy as np
import pandas as pd

from .config import UniverseConfig


CAPITAL_FLOW_GRAPH_V0 = "capital_flow_graph_v0"

NODE_COLUMNS = [
    "graph_model",
    "node_id",
    "node_type",
    "symbol",
    "name",
    "sector",
    "subgroup",
    "timeframe",
    "state",
    "final_signal",
    "relative_component",
    "compression_score",
    "opportunity_score",
    "setup_readiness_score",
    "extension_risk_score",
    "mtf_leader_context",
    "data_quality_score",
    "notes",
]

EDGE_COLUMNS = [
    "graph_model",
    "edge_id",
    "source_node_id",
    "target_node_id",
    "edge_type",
    "timeframe",
    "benchmark",
    "relative_component",
    "edge_signal",
    "edge_slope",
    "edge_state",
    "edge_confidence",
    "evidence_notes",
]

CHAIN_COLUMNS = [
    "graph_model",
    "chain_id",
    "date",
    "timeframe",
    "chain_path",
    "asset_symbol",
    "parent_node",
    "grandparent_node",
    "chain_label",
    "chain_support_score",
    "chain_alignment_tags",
    "chain_conflict_tags",
    "chain_confidence",
    "chain_notes",
]

SUPPORTIVE_CHAIN_LABELS = {"Full Chain Support", "Partial Chain Support"}
NON_SUPPORTIVE_CHAIN_LABELS = {
    "Asset Leading Weak Parent",
    "Parent Strong / Asset Not Ready",
    "Conflicted Chain",
}


def node_id(node_type: str, key: str) -> str:
    return f"{node_type}:{str(key).strip().lower().replace(' ', '_')}"


def edge_id(source: str, target: str, edge_type: str) -> str:
    return f"{edge_type}:{source}->{target}"


def _latest_valid_row(frame: pd.DataFrame) -> tuple[pd.Timestamp | None, pd.Series | None]:
    if frame.empty or "target" not in frame.columns:
        return None, None
    latest_index = frame["target"].last_valid_index()
    if latest_index is None:
        return None, None
    return latest_index, frame.loc[latest_index]


def _float(value: object) -> float:
    try:
        if pd.isna(value):
            return np.nan
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _asset_ready(row: pd.Series) -> bool:
    state = str(row.get("state", ""))
    final_signal = _float(row.get("final_signal"))
    relative = _float(row.get("relative_component"))
    above_viscosity = bool(row.get("above_viscosity")) if pd.notna(row.get("above_viscosity")) else False
    return state in {"Relative Accumulation", "Emerging Leader", "Confirmed Leader"} or (
        final_signal > 0.0 and relative > 0.0 and above_viscosity
    )


def _parent_return(frame: pd.DataFrame, lookback: int = 20) -> pd.Series:
    benchmark = pd.to_numeric(frame.get("benchmark"), errors="coerce").astype(float)
    return benchmark / benchmark.shift(lookback) - 1.0


def _edge_state(relative_component: float, edge_slope: float) -> str:
    if pd.isna(relative_component):
        return "unknown"
    if relative_component > 0.0 and (pd.isna(edge_slope) or edge_slope >= 0.0):
        return "outperforming"
    if relative_component > 0.0 and edge_slope < 0.0:
        return "weakening"
    if relative_component <= 0.0 and edge_slope > 0.0:
        return "improving"
    return "breaking_down"


def _chain_context_for_asset(
    symbol: str,
    sector: str,
    subgroup: str,
    frame: pd.DataFrame,
    *,
    timeframe: str,
    benchmark_name: str,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=CHAIN_COLUMNS)

    parent_return_20 = _parent_return(frame, lookback=20)
    rows: list[dict[str, object]] = []
    for date, row in frame.iterrows():
        selected_benchmark = str(row.get("benchmark_used", benchmark_name))
        benchmark_value = row.get("benchmark")
        parent_available = pd.notna(benchmark_value) and pd.notna(parent_return_20.loc[date])
        parent_supportive = bool(parent_return_20.loc[date] > 0.0) if parent_available else False
        asset_ready = _asset_ready(row)
        relative = _float(row.get("relative_component"))
        final_signal = _float(row.get("final_signal"))
        setup_readiness = _float(row.get("setup_readiness_score"))
        extension_risk = _float(row.get("extension_risk_score"))
        mtf_context = str(row.get("mtf_leader_context", ""))

        if not parent_available:
            label = "Incomplete Chain"
        elif parent_supportive and asset_ready:
            label = "Partial Chain Support"
        elif asset_ready and not parent_supportive:
            label = "Asset Leading Weak Parent"
        elif parent_supportive and not asset_ready:
            label = "Parent Strong / Asset Not Ready"
        elif relative < 0.0 and final_signal < 0.0:
            label = "Conflicted Chain"
        else:
            label = "Incomplete Chain"

        score = 0.0
        if relative > 0.0:
            score += 25.0
        if final_signal > 0.0:
            score += 15.0
        if parent_supportive:
            score += 30.0
        if setup_readiness >= 70.0:
            score += 20.0
        if mtf_context in {"Aligned Leader", "Early HTF Turn"}:
            score += 10.0
        if extension_risk >= 70.0:
            score -= 15.0
        if label == "Incomplete Chain":
            score = min(score, 40.0)
        score = float(np.clip(score, 0.0, 100.0))

        alignment_tags: list[str] = []
        conflict_tags: list[str] = []
        notes = ["subgroup/sector parent is structural until subgroup baskets exist"]
        if parent_supportive:
            alignment_tags.append("benchmark_parent_supportive")
        if asset_ready:
            alignment_tags.append("asset_ready")
        if relative > 0.0:
            alignment_tags.append("asset_outperforming_benchmark")
        if not parent_available:
            conflict_tags.append("missing_parent_context")
            notes.append("benchmark parent return unavailable")
        if not parent_supportive and parent_available:
            conflict_tags.append("benchmark_parent_not_supportive")
        if extension_risk >= 70.0:
            conflict_tags.append("extension_risk")

        rows.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "chain_id": f"chain:{selected_benchmark.lower()}->{subgroup.lower()}->{symbol.lower()}",
                "date": date,
                "timeframe": timeframe,
                "chain_path": f"{selected_benchmark} -> {subgroup} -> {symbol}",
                "asset_symbol": symbol,
                "parent_node": node_id("subgroup", f"{sector}:{subgroup}"),
                "grandparent_node": node_id("basket", benchmark_name),
                "chain_label": label,
                "chain_support_score": score,
                "chain_alignment_tags": "|".join(alignment_tags),
                "chain_conflict_tags": "|".join(conflict_tags),
                "chain_confidence": "provisional" if parent_available else "incomplete",
                "chain_notes": "; ".join(notes),
            }
        )
    return pd.DataFrame.from_records(rows, columns=CHAIN_COLUMNS)


def chain_context_frames(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
) -> dict[str, pd.DataFrame]:
    output: dict[str, pd.DataFrame] = {}
    for asset in universe.assets:
        frame = analysis_frames.get(asset.symbol)
        if frame is None or frame.empty:
            continue
        output[asset.symbol] = _chain_context_for_asset(
            asset.symbol,
            asset.sector,
            asset.subgroup,
            frame,
            timeframe=timeframe,
            benchmark_name=universe.benchmark.name,
        )
    return output


def append_chain_context(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
) -> dict[str, pd.DataFrame]:
    chain_frames = chain_context_frames(universe, analysis_frames, timeframe=timeframe)
    output: dict[str, pd.DataFrame] = {}
    chain_columns = [
        "chain_label",
        "chain_support_score",
        "chain_alignment_tags",
        "chain_conflict_tags",
        "chain_confidence",
        "chain_notes",
    ]
    for symbol, frame in analysis_frames.items():
        chain_frame = chain_frames.get(symbol)
        if chain_frame is None or chain_frame.empty:
            output[symbol] = frame.copy()
            continue
        indexed = chain_frame.set_index("date")
        output[symbol] = frame.join(indexed[chain_columns], how="left")
    return output


def build_flow_graph_tables(
    universe: UniverseConfig,
    analysis_frames: dict[str, pd.DataFrame],
    *,
    timeframe: str = "1d",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    chains: list[pd.DataFrame] = []

    universe_node = node_id("universe", universe.name)
    basket_node = node_id("basket", universe.benchmark.name)
    nodes.append(
        {
            "graph_model": CAPITAL_FLOW_GRAPH_V0,
            "node_id": universe_node,
            "node_type": "universe",
            "symbol": universe.name,
            "name": universe.name,
            "timeframe": timeframe,
            "notes": "structural universe node",
        }
    )
    nodes.append(
        {
            "graph_model": CAPITAL_FLOW_GRAPH_V0,
            "node_id": basket_node,
            "node_type": "basket",
            "symbol": universe.benchmark.name,
            "name": universe.benchmark.name,
            "timeframe": timeframe,
            "notes": "current benchmark basket; first parent context",
        }
    )
    edges.append(
        {
            "graph_model": CAPITAL_FLOW_GRAPH_V0,
            "edge_id": edge_id(universe_node, basket_node, "contains"),
            "source_node_id": universe_node,
            "target_node_id": basket_node,
            "edge_type": "contains",
            "timeframe": timeframe,
            "benchmark": universe.benchmark.name,
            "edge_state": "structural",
            "edge_confidence": "structural",
            "evidence_notes": "universe contains active benchmark basket",
        }
    )

    sectors = sorted({asset.sector for asset in universe.assets if asset.sector})
    subgroups = sorted({(asset.sector, asset.subgroup) for asset in universe.assets if asset.subgroup})
    for sector in sectors:
        sector_node = node_id("sector", sector)
        nodes.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "node_id": sector_node,
                "node_type": "sector",
                "symbol": sector,
                "name": sector,
                "sector": sector,
                "timeframe": timeframe,
                "notes": "structural sector node; independent sector basket deferred",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(basket_node, sector_node, "contains"),
                "source_node_id": basket_node,
                "target_node_id": sector_node,
                "edge_type": "contains",
                "timeframe": timeframe,
                "benchmark": universe.benchmark.name,
                "edge_state": "structural",
                "edge_confidence": "provisional",
                "evidence_notes": "sector parent is structural until sector baskets exist",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(sector_node, basket_node, "belongs_to"),
                "source_node_id": sector_node,
                "target_node_id": basket_node,
                "edge_type": "belongs_to",
                "timeframe": timeframe,
                "benchmark": universe.benchmark.name,
                "edge_state": "structural",
                "edge_confidence": "provisional",
                "evidence_notes": "sector belongs to benchmark basket structurally in v0",
            }
        )

    for sector, subgroup in subgroups:
        sector_node = node_id("sector", sector)
        subgroup_node = node_id("subgroup", f"{sector}:{subgroup}")
        nodes.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "node_id": subgroup_node,
                "node_type": "subgroup",
                "symbol": subgroup,
                "name": subgroup,
                "sector": sector,
                "subgroup": subgroup,
                "timeframe": timeframe,
                "notes": "structural subgroup node; independent subgroup basket deferred",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(sector_node, subgroup_node, "contains"),
                "source_node_id": sector_node,
                "target_node_id": subgroup_node,
                "edge_type": "contains",
                "timeframe": timeframe,
                "benchmark": universe.benchmark.name,
                "edge_state": "structural",
                "edge_confidence": "provisional",
                "evidence_notes": "subgroup parent is structural until subgroup baskets exist",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(subgroup_node, sector_node, "belongs_to"),
                "source_node_id": subgroup_node,
                "target_node_id": sector_node,
                "edge_type": "belongs_to",
                "timeframe": timeframe,
                "benchmark": universe.benchmark.name,
                "edge_state": "structural",
                "edge_confidence": "provisional",
                "evidence_notes": "subgroup belongs to sector structurally in v0",
            }
        )

    for asset in universe.assets:
        frame = analysis_frames.get(asset.symbol)
        latest_date, latest = _latest_valid_row(frame) if frame is not None else (None, None)
        asset_node = node_id("asset", asset.symbol)
        subgroup_node = node_id("subgroup", f"{asset.sector}:{asset.subgroup}")
        edge_signal = _float(latest.get("relative_component")) if latest is not None else np.nan
        edge_slope = _float(latest.get("signal_slope")) if latest is not None else np.nan
        edge_state = _edge_state(edge_signal, edge_slope)
        selected_benchmark = latest.get("benchmark_used") if latest is not None and pd.notna(latest.get("benchmark_used")) else universe.benchmark.name
        benchmark_confidence = latest.get("benchmark_confidence") if latest is not None and pd.notna(latest.get("benchmark_confidence")) else "unknown"
        benchmark_notes = latest.get("benchmark_notes") if latest is not None and pd.notna(latest.get("benchmark_notes")) else ""
        nodes.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "node_id": asset_node,
                "node_type": "asset",
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": asset.sector,
                "subgroup": asset.subgroup,
                "timeframe": timeframe,
                "state": latest.get("state") if latest is not None else pd.NA,
                "final_signal": latest.get("final_signal") if latest is not None else np.nan,
                "relative_component": latest.get("relative_component") if latest is not None else np.nan,
                "compression_score": latest.get("compression_score") if latest is not None else np.nan,
                "opportunity_score": latest.get("opportunity_score") if latest is not None else np.nan,
                "setup_readiness_score": latest.get("setup_readiness_score") if latest is not None else np.nan,
                "extension_risk_score": latest.get("extension_risk_score") if latest is not None else np.nan,
                "mtf_leader_context": latest.get("mtf_leader_context") if latest is not None else pd.NA,
                "data_quality_score": latest.get("data_quality_score") if latest is not None else np.nan,
                "notes": "asset observation node" if latest_date is not None else "no valid asset observation",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(subgroup_node, asset_node, "contains"),
                "source_node_id": subgroup_node,
                "target_node_id": asset_node,
                "edge_type": "contains",
                "timeframe": timeframe,
                "benchmark": universe.benchmark.name,
                "edge_state": "structural",
                "edge_confidence": "structural",
                "evidence_notes": "subgroup contains asset by config",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(asset_node, subgroup_node, "belongs_to"),
                "source_node_id": asset_node,
                "target_node_id": subgroup_node,
                "edge_type": "belongs_to",
                "timeframe": timeframe,
                "benchmark": universe.benchmark.name,
                "edge_state": "structural",
                "edge_confidence": "structural",
                "evidence_notes": "asset belongs to subgroup by config",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(asset_node, basket_node, "benchmarked_against"),
                "source_node_id": asset_node,
                "target_node_id": basket_node,
                "edge_type": "benchmarked_against",
                "timeframe": timeframe,
                "benchmark": selected_benchmark,
                "relative_component": edge_signal,
                "edge_signal": edge_signal,
                "edge_slope": edge_slope,
                "edge_state": edge_state,
                "edge_confidence": "provisional",
                "evidence_notes": f"asset relative to selected benchmark; benchmark_confidence={benchmark_confidence}; {benchmark_notes}",
            }
        )
        edges.append(
            {
                "graph_model": CAPITAL_FLOW_GRAPH_V0,
                "edge_id": edge_id(asset_node, basket_node, "child_vs_parent"),
                "source_node_id": asset_node,
                "target_node_id": basket_node,
                "edge_type": "child_vs_parent",
                "timeframe": timeframe,
                "benchmark": selected_benchmark,
                "relative_component": edge_signal,
                "edge_signal": edge_signal,
                "edge_slope": edge_slope,
                "edge_state": edge_state,
                "edge_confidence": "provisional",
                "evidence_notes": f"measurable v0 relationship is asset versus selected benchmark; benchmark_confidence={benchmark_confidence}",
            }
        )
        if frame is not None and not frame.empty:
            chain_frame = _chain_context_for_asset(
                asset.symbol,
                asset.sector,
                asset.subgroup,
                frame,
                timeframe=timeframe,
                benchmark_name=universe.benchmark.name,
            )
            if not chain_frame.empty:
                latest_chain = chain_frame.tail(1)
                chains.append(latest_chain)

    node_frame = pd.DataFrame.from_records(nodes)
    edge_frame = pd.DataFrame.from_records(edges)
    chain_frame = pd.concat(chains, ignore_index=True) if chains else pd.DataFrame(columns=CHAIN_COLUMNS)
    for frame, columns in ((node_frame, NODE_COLUMNS), (edge_frame, EDGE_COLUMNS), (chain_frame, CHAIN_COLUMNS)):
        for column in columns:
            if column not in frame.columns:
                frame[column] = pd.NA
    return node_frame[NODE_COLUMNS], edge_frame[EDGE_COLUMNS], chain_frame[CHAIN_COLUMNS]
