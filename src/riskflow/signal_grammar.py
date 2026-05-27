from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


SIGNAL_GRAMMAR_MODEL = "riskflow_signal_grammar_primitives_v0"

DEFAULT_TARGETS = {
    "clean_bullish_hits": 15,
    "bullish_false_positives": 10,
    "missed_breakouts": 10,
    "bearish_or_weakness_examples": 10,
    "noisy_or_ambiguous_edge_cases": 5,
}

SCENARIO_TAGS = {
    "clean_bullish_hits": {
        "fast_clean_hit",
        "slow_hit",
        "delayed_hit",
        "viscosity_reclaim",
        "viscosity_retest_hold",
        "minus_one_point_five_reclaim",
        "minus_two_reclaim",
    },
    "bullish_false_positives": {
        "false_positive",
        "failed_breakout",
        "failed_reversal_watchlist",
        "weak_breakout_response",
        "failed_strength_acceptance",
    },
    "missed_breakouts": {
        "missed_breakout",
        "low_in_before_price_confirmation",
        "price_needs_chop",
        "zero_confirmation_missing",
    },
    "bearish_or_weakness_examples": {
        "bearish_divergence",
        "hidden_bearish_divergence",
        "color_divergence",
        "gradient_momentum_divergence",
        "zero_rejection",
        "upper_band_rejection",
        "underside_support_rejection",
    },
    "noisy_or_ambiguous_edge_cases": {
        "mixed_or_flat",
        "chaotic_oscillator_pa",
        "unstructured_volatility",
        "unstable_strength",
        "constructive_wave_without_signal_confirmation",
    },
}


@dataclass(frozen=True)
class GrammarLabPaths:
    primitive_summary_csv: Path
    review_plan_md: Path
    obsidian_note_md: Path | None = None


def load_primitive_registry(path: str | Path = "research/grammar/primitive_registry.yaml") -> dict:
    registry_path = Path(path)
    with registry_path.open(encoding="utf-8") as file:
        registry = yaml.safe_load(file)
    if not isinstance(registry, dict):
        raise ValueError(f"Grammar registry {registry_path} must contain a mapping.")
    model = registry.get("model")
    if model != SIGNAL_GRAMMAR_MODEL:
        raise ValueError(f"Unknown grammar registry model: {model!r}")
    if not isinstance(registry.get("primitive_families"), dict):
        raise ValueError("Grammar registry must define primitive_families.")
    return registry


def _split_tags(value: object) -> set[str]:
    if value is None or pd.isna(value):
        return set()
    if isinstance(value, (list, tuple, set)):
        raw_tags = value
    else:
        raw_tags = str(value).replace("|", ",").split(",")
    return {str(tag).strip() for tag in raw_tags if str(tag).strip()}


def _load_observation_records(path: str | Path) -> pd.DataFrame:
    records_path = Path(path)
    if not records_path.exists():
        return pd.DataFrame()
    records = pd.read_csv(records_path)
    if "tags" not in records.columns:
        records["tags"] = ""
    return records


def _all_registry_primitives(registry: dict) -> set[str]:
    primitives: set[str] = set()
    for family in registry["primitive_families"].values():
        primitives.update(family.get("candidate_primitives", []) or [])
    return primitives


def build_primitive_summary(registry: dict, observations: pd.DataFrame | None = None) -> pd.DataFrame:
    observations = pd.DataFrame() if observations is None else observations.copy()
    observed_tags: list[set[str]] = [_split_tags(value) for value in observations.get("tags", [])]
    rows: list[dict[str, object]] = []

    for family_name, family in registry["primitive_families"].items():
        description = str(family.get("description", ""))
        first_tests = " | ".join(str(test) for test in family.get("first_tests", []) or [])
        for primitive in family.get("candidate_primitives", []) or []:
            observation_count = sum(primitive in tags for tags in observed_tags)
            rows.append(
                {
                    "grammar_model": registry["model"],
                    "family": family_name,
                    "primitive": primitive,
                    "description": description,
                    "observation_count": int(observation_count),
                    "evidence_status": "needs_observations" if observation_count == 0 else "observed_needs_testing",
                    "first_tests": first_tests,
                }
            )
    return pd.DataFrame(rows)


def _scenario_count(records: pd.DataFrame, scenario: str) -> int:
    if records.empty:
        return 0
    tags = SCENARIO_TAGS.get(scenario, set())
    count = 0
    for _, row in records.iterrows():
        row_tags = _split_tags(row.get("tags", ""))
        label = str(row.get("outcome_label", "")).strip()
        human_label = str(row.get("human_label", "")).strip()
        if row_tags.intersection(tags) or label in tags or human_label in tags:
            count += 1
    return count


def build_review_plan(
    registry: dict,
    observations: pd.DataFrame | None = None,
    *,
    title: str = "Signal Grammar Lab Review Plan",
) -> str:
    observations = pd.DataFrame() if observations is None else observations.copy()
    targets = registry.get("review_targets", {}) or {}
    target_counts = {key: int(targets.get(key, DEFAULT_TARGETS[key])) for key in DEFAULT_TARGETS}
    primitive_summary = build_primitive_summary(registry, observations)
    observed_primitives = primitive_summary[primitive_summary["observation_count"] > 0]
    missing_primitives = primitive_summary[primitive_summary["observation_count"] == 0]
    total_observations = len(observations)

    progress_rows = []
    for scenario, target in target_counts.items():
        current = _scenario_count(observations, scenario)
        remaining = max(target - current, 0)
        progress_rows.append((scenario, current, target, remaining))

    progress_table = "\n".join(
        f"| `{scenario}` | {current} | {target} | {remaining} |"
        for scenario, current, target, remaining in progress_rows
    )
    family_counts = (
        primitive_summary.groupby("family")["observation_count"].sum().sort_values(ascending=False).to_dict()
        if not primitive_summary.empty
        else {}
    )
    family_lines = "\n".join(f"- `{family}`: {count}" for family, count in family_counts.items())
    missing_lines = "\n".join(f"- `{row.primitive}` ({row.family})" for row in missing_primitives.itertuples(index=False))
    observed_lines = "\n".join(
        f"- `{row.primitive}` ({row.family}): {row.observation_count}"
        for row in observed_primitives.sort_values("observation_count", ascending=False).itertuples(index=False)
    )

    return f"""# {title}

Model: `{registry['model']}`

## Verdict

The grammar lab is a research queue, not a production signal. The base oscillator should remain frozen until repeated observations and Layer 7 evidence identify which primitives matter.

## Observation Progress

Total structured observations loaded: `{total_observations}`

| Scenario | Current | Target | Remaining |
|---|---:|---:|---:|
{progress_table}

## Primitive Family Coverage

{family_lines or '_No primitive observations yet._'}

## Observed Primitives

{observed_lines or '_No primitives observed yet._'}

## Missing Primitive Coverage

{missing_lines or '_All registered primitives have at least one observation._'}

## Next Review Batch

Prioritize the largest remaining scenario gaps first. Include both `4h` and `1d`, avoid one date cluster, and include failed/bearish examples alongside clean winners.

## Promotion Reminder

A primitive graduates only after it is measurable, appears across multiple symbols/date clusters, improves forward relative-return evidence, and remains readable on a TradingView-style chart.
"""


def unknown_observation_tags(registry: dict, observations: pd.DataFrame) -> set[str]:
    known = _all_registry_primitives(registry)
    known.update(SCENARIO_TAGS.keys())
    known.update(tag for tags in SCENARIO_TAGS.values() for tag in tags)
    unknown: set[str] = set()
    for value in observations.get("tags", []):
        unknown.update(_split_tags(value) - known)
    return unknown


def export_grammar_lab(
    *,
    registry_path: str | Path = "research/grammar/primitive_registry.yaml",
    observations_csv: str | Path = "research/observations/observation_records.csv",
    output_dir: str | Path = "reports/grammar_lab",
    obsidian_dir: str | Path | None = "obsidian",
) -> GrammarLabPaths:
    registry = load_primitive_registry(registry_path)
    observations = _load_observation_records(observations_csv)
    primitive_summary = build_primitive_summary(registry, observations)
    review_plan = build_review_plan(registry, observations)

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    primitive_summary_csv = output_root / "primitive_summary.csv"
    review_plan_md = output_root / "review_plan.md"
    primitive_summary.to_csv(primitive_summary_csv, index=False)
    review_plan_md.write_text(review_plan, encoding="utf-8")

    obsidian_note: Path | None = None
    if obsidian_dir:
        obsidian_note = Path(obsidian_dir) / "wiki" / "maps" / "Signal Grammar Lab.md"
        obsidian_note.parent.mkdir(parents=True, exist_ok=True)
        obsidian_note.write_text(review_plan, encoding="utf-8")

    return GrammarLabPaths(
        primitive_summary_csv=primitive_summary_csv,
        review_plan_md=review_plan_md,
        obsidian_note_md=obsidian_note,
    )
