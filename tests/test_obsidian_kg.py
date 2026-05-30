from __future__ import annotations

from pathlib import Path

import yaml

from riskflow.lab_loop import validate_lab_queue
from riskflow.obsidian_kg import (
    GENERATED_END,
    GENERATED_START,
    build_knowledge_graph,
    compile_setup_journey_queue,
    export_evidence_summaries,
    load_obsidian_notes,
    validate_knowledge_graph,
    write_knowledge_graph_outputs,
)


def _write_obsidian_fixture(tmp_path: Path) -> Path:
    obsidian = tmp_path / "obsidian"
    (obsidian / "wiki" / "cases").mkdir(parents=True)
    (obsidian / "wiki" / "concepts").mkdir(parents=True)
    (obsidian / "wiki" / "setup_journeys").mkdir(parents=True)
    (obsidian / "wiki" / "cases" / "CASE_A.md").write_text(
        """---
rf_type: case
observation_id: CASE_A
symbol: TEST
timeframe: 4h
date: 2026-01-01
review_status: human_reviewed
human_label: clean_hit_sequence
---

# Case A

Links to [[Viscosity Reclaim]].
""",
        encoding="utf-8",
    )
    (obsidian / "wiki" / "concepts" / "Viscosity Reclaim.md").write_text(
        """---
rf_type: concept
concept_id: viscosity_reclaim
track: bullish_setup
role: [entry_trigger]
measurable: true
canonical_primitives: [viscosity_reclaim]
canonical_detectors: [failed_weakness_reclaim]
status: defined
---

# Viscosity Reclaim
""",
        encoding="utf-8",
    )
    (obsidian / "wiki" / "setup_journeys" / "Test Journey.md").write_text(
        """---
rf_type: setup_journey
journey_id: test_journey
direction: bullish
status: candidate
promotion_level: L0_registered
claim_type: bullish_entry
setup_conditions: [deep_reset]
repair: [relative_repair]
entry_triggers: [viscosity_reclaim]
confirmation: [viscosity_retest_hold]
invalidation: [warning_refire]
permission_filters: [warning_absent_or_cleared]
required_controls: [trigger_only, permission_only, blocker_present, inverted_direction]
source_cases: [CASE_A]
---

# Test Journey

Uses [[Viscosity Reclaim]].
""",
        encoding="utf-8",
    )
    return obsidian


def test_obsidian_kg_loads_validates_and_indexes(tmp_path: Path) -> None:
    obsidian = _write_obsidian_fixture(tmp_path)

    graph = build_knowledge_graph(load_obsidian_notes(obsidian))
    result = validate_knowledge_graph(graph)
    paths = write_knowledge_graph_outputs(graph, tmp_path / "kg")

    assert result.errors == ()
    assert len(graph.nodes) == 3
    assert any(edge.edge_type == "wikilink" for edge in graph.edges)
    assert paths["nodes_csv"].exists()
    assert paths["edges_csv"].exists()
    assert paths["graph_json"].exists()


def test_compile_setup_journey_queue_writes_lab_compatible_queue(tmp_path: Path) -> None:
    obsidian = _write_obsidian_fixture(tmp_path)
    graph = build_knowledge_graph(load_obsidian_notes(obsidian))

    compiled = compile_setup_journey_queue(
        graph,
        output_queue=tmp_path / "obsidian_candidate_queue.yaml",
        generated_grid_dir=tmp_path / "generated_from_obsidian",
    )

    queue = compiled["queue"]
    errors = validate_lab_queue(queue, validate_sources=True)
    assert errors == []
    assert len(queue["queue"]) == 1
    item = queue["queue"][0]
    assert item["id"] == "obsidian_test_journey"
    assert item["track"] == "bullish_setup"
    assert item["claim_type"] == "bullish_entry"
    assert Path(item["source"]).exists()


def test_validate_rejects_incomplete_setup_journey(tmp_path: Path) -> None:
    obsidian = tmp_path / "obsidian"
    path = obsidian / "wiki" / "setup_journeys" / "Bad.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        """---
rf_type: setup_journey
journey_id: bad
direction: bullish
---

# Bad
""",
        encoding="utf-8",
    )

    graph = build_knowledge_graph(load_obsidian_notes(obsidian))
    result = validate_knowledge_graph(graph)

    assert any("setup_conditions" in error for error in result.errors)
    assert any("source_cases" in error for error in result.errors)


def test_export_evidence_summaries_preserves_manual_tail(tmp_path: Path) -> None:
    session = tmp_path / "reports" / "session_test"
    loop = session / "loop_0001"
    loop.mkdir(parents=True)
    evidence = {
        "hypothesis_id": "obsidian_test_journey",
        "passes_bullish_contract": False,
        "failure_reason": "positive rows exist but did not pass strict referee",
        "positive_useful_rows": 7,
        "strict_positive_survivors": 0,
        "terminal_median_relative_return": 0.04,
        "hit_rate": 0.48,
        "mfe_mae_ratio": 1.8,
    }
    (loop / "bullish_evidence.yaml").write_text(yaml.safe_dump(evidence), encoding="utf-8")
    obsidian = tmp_path / "obsidian"
    evidence_dir = obsidian / "wiki" / "evidence"
    evidence_dir.mkdir(parents=True)
    existing = evidence_dir / "obsidian_test_journey_loop_0001.md"
    existing.write_text(
        f"""# Old

{GENERATED_START}
old
{GENERATED_END}

## Manual Notes

Keep this review note.
""",
        encoding="utf-8",
    )

    paths = export_evidence_summaries(session, obsidian_dir=obsidian)

    assert paths == [existing]
    text = existing.read_text(encoding="utf-8")
    assert "positive rows exist but did not pass strict referee" in text
    assert "Keep this review note." in text
    assert "rf_type: evidence_summary" in text

