from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .lab_loop import BULLISH_POSITIVE_OBJECTIVE, utc_now_iso


OBSIDIAN_KG_MODEL = "riskflow_obsidian_kg_v0"
OBSIDIAN_QUEUE_MODEL = "riskflow_lab_loop_hypothesis_queue_v0"
DEFAULT_OBSIDIAN_DIR = Path("obsidian")
DEFAULT_KG_OUTPUT_DIR = Path("research/knowledge_graph")
DEFAULT_OBSIDIAN_QUEUE_PATH = Path("research/lab_loop/obsidian_candidate_queue.yaml")
DEFAULT_OBSIDIAN_GRID_DIR = Path("research/grammar/generated_from_obsidian")
GENERATED_START = "<!-- riskflow:generated:start -->"
GENERATED_END = "<!-- riskflow:generated:end -->"

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

NOTE_TYPE_BY_PART = {
    "cases": "case",
    "concepts": "concept",
    "setup_journeys": "setup_journey",
    "evidence": "evidence_summary",
    "maps": "map",
    "hypotheses": "hypothesis",
    "decisions": "decision",
    "postmortems": "postmortem",
}

NODE_ID_FIELDS = (
    "node_id",
    "journey_id",
    "concept_id",
    "evidence_id",
    "observation_id",
    "hypothesis_id",
    "decision_id",
    "postmortem_id",
)

SETUP_REQUIRED_FIELDS = (
    "journey_id",
    "direction",
    "setup_conditions",
    "entry_triggers",
    "confirmation",
    "invalidation",
    "required_controls",
    "source_cases",
)

EVIDENCE_REQUIRED_FIELDS = (
    "evidence_id",
    "journey_id",
    "hypothesis_id",
    "verdict",
)

EDGE_FIELD_TYPES = {
    "linked_concepts": "uses_concept",
    "concept_tags": "uses_concept",
    "canonical_primitives": "measures_primitive",
    "canonical_detectors": "uses_detector",
    "linked_journeys": "supports_journey",
    "source_cases": "derived_from_case",
    "supports": "supports",
    "invalidated_by": "invalidated_by",
    "requires_confirmation": "requires_confirmation",
    "permission_filters": "permission_filter",
    "setup_conditions": "setup_condition",
    "entry_triggers": "entry_trigger",
    "confirmation": "confirmation",
    "invalidation": "invalidation",
    "required_controls": "required_control",
    "blockers": "blocker",
    "duplicate_of": "duplicate_of",
}


@dataclass(frozen=True)
class KnowledgeNode:
    node_id: str
    title: str
    node_type: str
    path: Path
    frontmatter: dict[str, Any]
    wikilinks: tuple[str, ...]


@dataclass(frozen=True)
class KnowledgeEdge:
    source: str
    target: str
    edge_type: str
    source_path: Path
    target_resolved_id: str = ""


@dataclass(frozen=True)
class KnowledgeGraph:
    nodes: tuple[KnowledgeNode, ...]
    edges: tuple[KnowledgeEdge, ...]


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "node"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        return [value.strip()]
    return [str(value).strip()]


def _read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[text.find("\n", end + 1) + 1 :]
    frontmatter = yaml.safe_load(raw) if raw else {}
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    return frontmatter, body


def _title_from_body(path: Path, body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _infer_type(path: Path, frontmatter: dict[str, Any]) -> str:
    explicit = str(frontmatter.get("rf_type") or frontmatter.get("type") or "").strip()
    if explicit:
        return explicit
    if path.name.lower() == "readme.md":
        return "note"
    parts = set(path.parts)
    for part, node_type in NOTE_TYPE_BY_PART.items():
        if part in parts:
            return node_type
    return "note"


def _node_id(path: Path, title: str, frontmatter: dict[str, Any]) -> str:
    if path.name.lower() == "readme.md":
        return _slug("_".join(path.with_suffix("").parts[-3:]))
    stem_slug = _slug(path.stem)
    for field in NODE_ID_FIELDS:
        value = frontmatter.get(field)
        if value:
            value_slug = _slug(str(value))
            if field == "observation_id" and "human_review" in stem_slug and value_slug != stem_slug:
                return stem_slug
            return value_slug
    return _slug(path.stem or title)


def _wikilinks(body: str) -> tuple[str, ...]:
    links: list[str] = []
    seen: set[str] = set()
    for match in WIKILINK_RE.finditer(body):
        target = match.group(1).strip()
        if target and target not in seen:
            links.append(target)
            seen.add(target)
    return tuple(links)


def load_obsidian_notes(obsidian_dir: str | Path = DEFAULT_OBSIDIAN_DIR) -> list[KnowledgeNode]:
    root = Path(obsidian_dir)
    if not root.exists():
        return []
    nodes: list[KnowledgeNode] = []
    for path in sorted(root.rglob("*.md")):
        if ".obsidian" in path.parts or "reports" in path.parts:
            continue
        frontmatter, body = _read_markdown(path)
        title = _title_from_body(path, body)
        nodes.append(
            KnowledgeNode(
                node_id=_node_id(path, title, frontmatter),
                title=title,
                node_type=_infer_type(path, frontmatter),
                path=path,
                frontmatter=frontmatter,
                wikilinks=_wikilinks(body),
            )
        )
    return nodes


def _target_lookup(nodes: list[KnowledgeNode]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for node in nodes:
        lookup[_slug(node.node_id)] = node.node_id
        lookup[_slug(node.title)] = node.node_id
        lookup[_slug(node.path.stem)] = node.node_id
        for field in NODE_ID_FIELDS:
            if node.frontmatter.get(field):
                lookup[_slug(str(node.frontmatter[field]))] = node.node_id
    return lookup


def build_knowledge_graph(nodes: list[KnowledgeNode]) -> KnowledgeGraph:
    lookup = _target_lookup(nodes)
    edges: list[KnowledgeEdge] = []
    for node in nodes:
        for link in node.wikilinks:
            edges.append(
                KnowledgeEdge(
                    source=node.node_id,
                    target=link,
                    edge_type="wikilink",
                    source_path=node.path,
                    target_resolved_id=lookup.get(_slug(link), ""),
                )
            )
        for field, edge_type in EDGE_FIELD_TYPES.items():
            for target in _as_list(node.frontmatter.get(field)):
                edges.append(
                    KnowledgeEdge(
                        source=node.node_id,
                        target=target,
                        edge_type=edge_type,
                        source_path=node.path,
                        target_resolved_id=lookup.get(_slug(target), ""),
                    )
                )
    return KnowledgeGraph(nodes=tuple(nodes), edges=tuple(edges))


def validate_knowledge_graph(graph: KnowledgeGraph) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    by_id: dict[str, list[KnowledgeNode]] = {}
    for node in graph.nodes:
        by_id.setdefault(node.node_id, []).append(node)
    for node_id, duplicates in sorted(by_id.items()):
        if len(duplicates) > 1:
            paths = ", ".join(str(node.path) for node in duplicates)
            errors.append(f"duplicate node id {node_id}: {paths}")

    for node in graph.nodes:
        if node.node_type == "setup_journey":
            for field in SETUP_REQUIRED_FIELDS:
                if not _as_list(node.frontmatter.get(field)):
                    errors.append(f"{node.path}: setup_journey missing {field}")
            if str(node.frontmatter.get("direction", "")).lower() != "bullish":
                warnings.append(f"{node.path}: setup_journey direction is not bullish")
        elif node.node_type == "evidence_summary":
            for field in EVIDENCE_REQUIRED_FIELDS:
                if not node.frontmatter.get(field):
                    errors.append(f"{node.path}: evidence_summary missing {field}")
            if not any(node.frontmatter.get(field) for field in ("source_report", "source_csv", "source_yaml")):
                errors.append(f"{node.path}: evidence_summary missing source_report/source_csv/source_yaml")
        elif node.node_type == "concept" and node.frontmatter:
            if not node.frontmatter.get("concept_id"):
                warnings.append(f"{node.path}: concept frontmatter has no concept_id")

    for edge in graph.edges:
        if edge.edge_type == "wikilink" and not edge.target_resolved_id:
            warnings.append(f"{edge.source_path}: unresolved wikilink [[{edge.target}]]")

    return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))


def write_knowledge_graph_outputs(
    graph: KnowledgeGraph,
    output_dir: str | Path = DEFAULT_KG_OUTPUT_DIR,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    nodes_path = output / "obsidian_nodes.csv"
    edges_path = output / "obsidian_edges.csv"
    graph_path = output / "obsidian_graph.json"
    node_rows = [
        {
            "node_id": node.node_id,
            "title": node.title,
            "node_type": node.node_type,
            "path": str(node.path),
            "status": node.frontmatter.get("status", ""),
            "promotion_level": node.frontmatter.get("promotion_level", ""),
            "direction": node.frontmatter.get("direction", ""),
        }
        for node in graph.nodes
    ]
    edge_rows = [
        {
            "source": edge.source,
            "target": edge.target,
            "target_resolved_id": edge.target_resolved_id,
            "edge_type": edge.edge_type,
            "source_path": str(edge.source_path),
        }
        for edge in graph.edges
    ]
    pd.DataFrame(node_rows).to_csv(nodes_path, index=False)
    pd.DataFrame(edge_rows).to_csv(edges_path, index=False)
    graph_path.write_text(
        json.dumps({"model": OBSIDIAN_KG_MODEL, "nodes": node_rows, "edges": edge_rows}, indent=2),
        encoding="utf-8",
    )
    return {"nodes_csv": nodes_path, "edges_csv": edges_path, "graph_json": graph_path}


def _journey_primitives(frontmatter: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field in (
        "setup_conditions",
        "repair",
        "entry_triggers",
        "confirmation",
        "invalidation",
        "permission_filters",
        "canonical_primitives",
        "canonical_detectors",
    ):
        values.extend(_as_list(frontmatter.get(field)))
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        primitive = _slug(value)
        if primitive not in seen:
            result.append(primitive)
            seen.add(primitive)
    return result


def _journey_text(journey_id: str, frontmatter: dict[str, Any]) -> str:
    values = [
        journey_id,
        str(frontmatter.get("title", "")),
        str(frontmatter.get("setup_class", "")),
    ]
    for field in (
        "setup_conditions",
        "repair",
        "entry_triggers",
        "confirmation",
        "invalidation",
        "permission_filters",
        "canonical_primitives",
        "canonical_detectors",
    ):
        values.extend(_as_list(frontmatter.get(field)))
    return " ".join(values).lower()


def _detector_archetype(journey_id: str, frontmatter: dict[str, Any]) -> str:
    text = _journey_text(journey_id, frontmatter)
    if any(token in text for token in ("compression", "coil", "chop")):
        return "compression_expansion"
    if any(token in text for token in ("fresh", "leader", "relative_leads_price")):
        return "fresh_leadership"
    if any(token in text for token in ("second_base", "failed_first", "post_failed_break", "double_bottom")):
        return "second_base_reclaim"
    if any(token in text for token in ("zero", "acceptance", "regime")):
        return "acceptance_confirmation"
    if any(token in text for token in ("warning_cleared", "warning_refire", "cleared")):
        return "warning_cleared_recovery"
    if any(token in text for token in ("flush", "breakdown", "deep_reset", "weakness")):
        return "failed_breakdown_reclaim"
    return "rotation_reclaim"


def _journey_detector_families(journey_id: str, frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    title = str(frontmatter.get("title") or journey_id).replace("_", " ")
    family = _slug(journey_id)
    archetype = _detector_archetype(journey_id, frontmatter)
    if archetype == "compression_expansion":
        primary = [
            {
                "family_id": f"{family}_compression_reclaim",
                "direction": "positive",
                "detector": "compression_reclaim",
                "description": f"{title}: compression rebuild followed by reclaim.",
                "parameter_grid": {
                    "min_compression": [45.0, 60.0],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                },
            },
            {
                "family_id": f"{family}_low_zone_coil_reclaim",
                "direction": "positive",
                "detector": "low_zone_coil_reclaim",
                "description": f"{title}: low-zone coil resolving through reclaim.",
                "parameter_grid": {
                    "coil_window": [10, 14],
                    "range_max": [0.6, 0.8],
                    "std_max": [0.30, 0.40],
                    "zone_max": [-1.5, -1.0],
                    "recent_window": [8],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                },
            },
        ]
    elif archetype == "fresh_leadership":
        primary = [
            {
                "family_id": f"{family}_fresh_leader_ignition",
                "direction": "positive",
                "detector": "fresh_leader_ignition",
                "description": f"{title}: fresh relative leadership while price is not extended.",
                "parameter_grid": {
                    "relative_window": [5, 8],
                    "min_relative_slope": [0.02, 0.04],
                    "max_signal": [0.75, 1.0],
                    "min_gradient_slope": [0.0],
                    "price_lookback": [20],
                    "below_high_margin": [0.02],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "require_warning_absent": [True],
                },
            },
            {
                "family_id": f"{family}_relative_compression_breakout",
                "direction": "positive",
                "detector": "fresh_relative_compression_breakout",
                "description": f"{title}: relative leadership emerging from compression.",
                "parameter_grid": {
                    "relative_window": [5],
                    "gradient_window": [5],
                    "compression_window": [13, 20],
                    "price_lookback": [20],
                    "min_compression": [50.0, 60.0],
                    "min_relative_slope": [0.02, 0.04],
                    "min_gradient_slope": [0.0],
                    "min_signal": [-1.0],
                    "max_signal": [1.0],
                    "below_high_margin": [0.02],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "require_warning_absent": [True],
                },
            },
        ]
    elif archetype == "second_base_reclaim":
        primary = [
            {
                "family_id": f"{family}_second_base_reclaim",
                "direction": "positive",
                "detector": "rotation_reclaim_setup",
                "description": f"{title}: second-base/fresh-base reclaim after failed first break.",
                "parameter_grid": {
                    "setup_mode": ["fresh_base_reclaim"],
                    "lookback": [20],
                    "relative_window": [5],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "min_relative_slope": [0.0, 0.03],
                    "min_signal_slope": [0.0],
                    "min_gradient_slope": [-0.03, 0.0],
                    "max_prior_signal": [0.75, 1.0],
                    "max_signal": [0.75, 1.0],
                    "min_compression": [30.0, 45.0],
                },
            },
            {
                "family_id": f"{family}_retest_hold_confirmation",
                "direction": "positive",
                "detector": "zone_reclaim_retest",
                "description": f"{title}: reclaim plus retest/hold confirmation.",
                "parameter_grid": {
                    "level": [-1.5, 0.0],
                    "tolerance": [0.15, 0.30],
                    "hold_bars": [3, 5],
                    "mode": ["retest"],
                },
            },
        ]
    elif archetype == "acceptance_confirmation":
        primary = [
            {
                "family_id": f"{family}_regime_confirmed_reclaim",
                "direction": "positive",
                "detector": "regime_confirmed_reclaim",
                "description": f"{title}: reclaim confirmed by relative and benchmark regime.",
                "parameter_grid": {
                    "relative_window": [5, 8],
                    "benchmark_window": [5],
                    "min_relative_slope": [0.0, 0.03],
                    "min_benchmark_return": [-0.03, 0.0],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "require_warning_absent": [True],
                    "max_signal": [0.75, 1.25],
                    "min_compression": [30.0, 50.0],
                },
            },
            {
                "family_id": f"{family}_zero_retest_hold",
                "direction": "positive",
                "detector": "zone_reclaim_retest",
                "description": f"{title}: zero reclaim then retest hold.",
                "parameter_grid": {
                    "level": [0.0],
                    "tolerance": [0.10, 0.20],
                    "hold_bars": [3, 5],
                    "mode": ["retest"],
                },
            },
        ]
    elif archetype == "warning_cleared_recovery":
        primary = [
            {
                "family_id": f"{family}_warning_cleared_reclaim",
                "direction": "positive",
                "detector": "warning_cleared_reclaim",
                "description": f"{title}: warning clears, then reclaim occurs.",
                "parameter_grid": {
                    "warning_lookback": [20],
                    "warning_context_window": [8],
                    "clearance_window": [5, 8],
                    "relative_window": [5],
                    "min_relative_slope": [0.0, 0.03],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "max_signal": [1.0],
                    "min_recent_signal_low": [-1.5, -1.0],
                },
            },
            {
                "family_id": f"{family}_trend_pullback_warning_cleared",
                "direction": "positive",
                "detector": "trend_pullback_hold",
                "description": f"{title}: trend pullback holds after warning clears.",
                "parameter_grid": {
                    "lookback": [20],
                    "relative_window": [5],
                    "min_prior_signal": [0.75, 1.0],
                    "hold_tolerance": [0.15, 0.25],
                    "max_pressure_distance": [0.25, 0.35],
                    "min_relative_slope": [0.0],
                    "warning_mode": ["cleared"],
                },
            },
        ]
    elif archetype == "failed_breakdown_reclaim":
        primary = [
            {
                "family_id": f"{family}_failed_breakdown_reclaim",
                "direction": "positive",
                "detector": "failed_weakness_reclaim",
                "description": f"{title}: failed breakdown followed by reclaim.",
                "parameter_grid": {
                    "lookback": [13, 20],
                    "zone_max": [-2.0, -1.5],
                    "low_tolerance": [0.20, 0.35],
                    "min_slope": [0.0, 0.03],
                    "relative_slope_min": [-0.05, 0.0],
                    "recent_window": [8],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                },
            },
            {
                "family_id": f"{family}_warning_cleared_failed_breakdown",
                "direction": "positive",
                "detector": "warning_absent_bullish_setup",
                "description": f"{title}: failed breakdown only when warning is absent or cleared.",
                "parameter_grid": {
                    "setup": ["failed_weakness_reclaim"],
                    "lookback": [13, 20],
                    "zone_max": [-2.0, -1.5],
                    "low_tolerance": [0.25],
                    "min_slope": [0.0],
                    "relative_slope_min": [-0.05, 0.0],
                    "recent_window": [8],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "warning_mode": ["absent", "cleared"],
                    "warning_context_window": [8],
                    "warning_lookback": [20],
                },
            },
        ]
    else:
        primary = [
            {
                "family_id": f"{family}_rotation_reclaim",
                "direction": "positive",
                "detector": "rotation_reclaim_setup",
                "description": f"{title}: rotation reclaim after relative repair.",
                "parameter_grid": {
                    "setup_mode": ["post_underperformance", "relative_leads_price"],
                    "lookback": [20],
                    "relative_window": [5],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "min_relative_slope": [0.0, 0.03],
                    "min_signal_slope": [0.0],
                    "min_gradient_slope": [-0.03, 0.0],
                },
            },
            {
                "family_id": f"{family}_post_reset_reclaim",
                "direction": "positive",
                "detector": "post_reset_reclaim",
                "description": f"{title}: hot/reset reclaim candidate.",
                "parameter_grid": {
                    "prior_window": [20],
                    "hot_level": [1.0, 1.5],
                    "reset_level": [0.75, 1.0],
                    "reset_window": [8],
                    "require_below_viscosity": [True],
                    "trigger": ["viscosity_reclaim", "zero_reclaim"],
                    "relative_slope_min": [-0.05, 0.0],
                },
            },
        ]

    controls = [
        {
            "family_id": f"{family}_trigger_only_control",
            "direction": "positive",
            "detector": "failed_weakness_reclaim",
            "description": f"{title}: trigger-only failed-weakness control.",
            "parameter_grid": {
                "lookback": [13, 20],
                "zone_max": [-2.0, -1.5],
                "low_tolerance": [0.25],
                "min_slope": [0.0],
                "relative_slope_min": [-0.05, 0.0],
                "recent_window": [8],
                "trigger": ["viscosity_reclaim", "zero_reclaim"],
            },
        },
        {
            "family_id": f"{family}_blocker_present_counterfactual",
            "direction": "negative",
            "detector": "compression_warning_bullish_setup",
            "description": f"{title}: blocker-present counterfactual for long invalidation.",
            "parameter_grid": {
                "setup": ["failed_weakness_reclaim", "compression_reclaim", "zone_reclaim_retest"],
                "lookback": [20],
                "zone_max": [-2.0, -1.5],
                "low_tolerance": [0.25],
                "min_slope": [0.0],
                "relative_slope_min": [-0.05],
                "recent_window": [8],
                "trigger": ["viscosity_reclaim", "zero_reclaim"],
                "warning_mode": ["active"],
                "warning_context_window": [8],
                "warning_lookback": [20],
                "warning_min_compression": [70.0],
            },
        },
    ]
    return primary + controls


def _generated_grid_for_journey(journey_id: str, frontmatter: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": "riskflow_grammar_search_v0",
        "generated_from": "obsidian_kg",
        "journey_id": journey_id,
        "archetype": _detector_archetype(journey_id, frontmatter),
        "families": _journey_detector_families(journey_id, frontmatter),
    }


def compile_setup_journey_queue(
    graph: KnowledgeGraph,
    *,
    direction: str = "bullish",
    output_queue: str | Path = DEFAULT_OBSIDIAN_QUEUE_PATH,
    generated_grid_dir: str | Path = DEFAULT_OBSIDIAN_GRID_DIR,
    min_source_cases: int = 1,
) -> dict[str, Any]:
    queue_path = Path(output_queue)
    grid_dir = Path(generated_grid_dir)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    grid_dir.mkdir(parents=True, exist_ok=True)

    queue_items: list[dict[str, Any]] = []
    journeys = [
        node
        for node in graph.nodes
        if node.node_type == "setup_journey"
        and str(node.frontmatter.get("direction", "")).lower() == direction.lower()
        and str(node.frontmatter.get("status", "")).lower() not in {"archived", "rejected", "duplicate"}
    ]
    for index, node in enumerate(sorted(journeys, key=lambda item: item.node_id), start=1):
        frontmatter = node.frontmatter
        source_cases = _as_list(frontmatter.get("source_cases"))
        if len(source_cases) < min_source_cases:
            continue
        journey_id = _slug(str(frontmatter.get("journey_id") or node.node_id))
        grid = _generated_grid_for_journey(journey_id, {**frontmatter, "title": node.title})
        grid_path = grid_dir / f"{journey_id}.yaml"
        grid_path.write_text(yaml.safe_dump(grid, sort_keys=False), encoding="utf-8")
        primary_detector = ""
        if grid.get("families"):
            primary_detector = str(grid["families"][0].get("detector", ""))
        queue_items.append(
            {
                "id": f"obsidian_{journey_id}",
                "track": "bullish_setup",
                "status": "new",
                "promotion_level": str(frontmatter.get("promotion_level", "L0_registered")),
                "priority": index,
                "source": str(grid_path),
                "hypothesis": str(
                    frontmatter.get("hypothesis")
                    or f"Obsidian setup journey {node.title} should improve bullish trade path only when confirmation and blockers agree."
                ),
                "claim_type": str(frontmatter.get("claim_type", "bullish_entry")),
                "setup_class": str(frontmatter.get("setup_class", journey_id)),
                "discovery_mode": "new_family",
                "primary_detector": str(frontmatter.get("primary_detector") or primary_detector),
                "detector_archetype": str(grid.get("archetype", "")),
                "objective": BULLISH_POSITIVE_OBJECTIVE,
                "source_cases": source_cases,
                "stages": {
                    "stage_0_context": "; ".join(_as_list(frontmatter.get("setup_conditions"))),
                    "stage_1_repair": "; ".join(_as_list(frontmatter.get("repair"))),
                    "stage_2_trigger": "; ".join(_as_list(frontmatter.get("entry_triggers"))),
                    "stage_3_confirmation": "; ".join(_as_list(frontmatter.get("confirmation"))),
                    "stage_4_invalidation": "; ".join(_as_list(frontmatter.get("invalidation"))),
                },
                "measurable_primitives": _journey_primitives(frontmatter),
                "required_controls": _as_list(frontmatter.get("required_controls")),
                "novelty": {
                    "source": "obsidian_kg",
                    "archetype": str(grid.get("archetype", "")),
                    "expected_new_primitives": _journey_primitives(frontmatter),
                },
                "family_budget": frontmatter.get(
                    "family_budget",
                    {
                        "max_loops_without_contract": 3,
                        "max_generation_without_contract": 1,
                        "cooldown_epochs_on_fail": 5,
                    },
                ),
                "path_objective": frontmatter.get(
                    "path_objective",
                    {
                        "min_sample_size": 30,
                        "min_unique_symbols": 12,
                        "min_event_clusters": 12,
                        "min_mfe_mae_ratio": 1.25,
                    },
                ),
                "branch_budget": frontmatter.get("branch_budget", {"max_generation": 2}),
                "expected_outcome": "positive_trade_path_with_controlled_mae",
                "next_action": "Run through bullish-positive objective with full controls before promoting.",
            }
        )

    payload = {
        "model": OBSIDIAN_QUEUE_MODEL,
        "date": utc_now_iso().split("T", 1)[0],
        "generated_from": OBSIDIAN_KG_MODEL,
        "production_effect": "none",
        "default_timeframes": ["1d", "12h", "4h", "1h"],
        "default_outcome": "forward_relative_return_vs_basket",
        "strict_referee_required": True,
        "queue": queue_items,
    }
    queue_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return {"queue": payload, "queue_path": queue_path, "grid_dir": grid_dir}


def _evidence_hash(evidence: dict[str, Any]) -> str:
    raw = json.dumps(evidence, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _manual_tail(existing: str) -> str:
    if GENERATED_END not in existing:
        return ""
    return existing.split(GENERATED_END, 1)[1].lstrip("\n")


def _evidence_note_text(evidence: dict[str, Any], *, source_path: Path, existing: str = "") -> str:
    hypothesis_id = str(evidence.get("hypothesis_id", "unknown"))
    loop_id = source_path.parent.name
    evidence_id = _slug(f"{hypothesis_id}_{loop_id}")
    journey_id = _slug(hypothesis_id.replace("obsidian_", ""))
    frontmatter = {
        "rf_type": "evidence_summary",
        "evidence_id": evidence_id,
        "journey_id": journey_id,
        "hypothesis_id": hypothesis_id,
        "source_yaml": str(source_path),
        "promotion_level": "L3_strict_survivor" if evidence.get("passes_bullish_contract") else "L2_discovered",
        "verdict": "passed_bullish_contract" if evidence.get("passes_bullish_contract") else "watchlist_not_promoted",
        "evidence_hash": _evidence_hash(evidence),
        "created_from": "obsidian_kg_export_evidence",
    }
    generated = [
        f"# Evidence - {hypothesis_id} {loop_id}",
        "",
        GENERATED_START,
        "",
        f"- Source: `{source_path}`",
        f"- Contract: {'passed' if evidence.get('passes_bullish_contract') else 'failed'}",
        f"- Failure reason: {evidence.get('failure_reason', '')}",
        f"- Positive useful rows: {evidence.get('positive_useful_rows', 0)}",
        f"- Strict positive survivors: {evidence.get('strict_positive_survivors', 0)}",
        f"- Terminal median relative return: {evidence.get('terminal_median_relative_return', '')}",
        f"- Hit rate: {evidence.get('hit_rate', '')}",
        f"- MFE/MAE: {evidence.get('mfe_mae_ratio', '')}",
        "",
        GENERATED_END,
        "",
    ]
    tail = _manual_tail(existing)
    return (
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False).strip()
        + "\n---\n\n"
        + "\n".join(generated)
        + (tail if tail else "## Manual Notes\n\n")
    )


def export_evidence_summaries(
    session_dir: str | Path,
    *,
    obsidian_dir: str | Path = DEFAULT_OBSIDIAN_DIR,
    include_failed: bool = True,
) -> list[Path]:
    session = Path(session_dir)
    output_dir = Path(obsidian_dir) / "wiki" / "evidence"
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for evidence_path in sorted(session.glob("loop_*/bullish_evidence.yaml")):
        evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8")) or {}
        if not include_failed and not evidence.get("passes_bullish_contract"):
            continue
        hypothesis_id = str(evidence.get("hypothesis_id", evidence_path.parent.name))
        note_path = output_dir / f"{_slug(hypothesis_id)}_{evidence_path.parent.name}.md"
        existing = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
        note_path.write_text(_evidence_note_text(evidence, source_path=evidence_path, existing=existing), encoding="utf-8")
        written.append(note_path)
    return written
