from __future__ import annotations

from dataclasses import dataclass


OPPORTUNITY_SCORE_V0 = "opportunity_score_v0"
TRADER_SCORE_V0 = "trader_score_v0"
LEADER_QUALITY_SCORE = "leader_quality_score"
COMPRESSION_QUALITY_SCORE = "compression_quality_score"
RELATIVE_ACCUMULATION_SCORE = "relative_accumulation_score"
SETUP_READINESS_SCORE = "setup_readiness_score"
EXTENSION_RISK_SCORE = "extension_risk_score"
DATA_QUALITY_SCORE = "data_quality_score"
OPPORTUNITY_SCORE_V1_CANDIDATE = "opportunity_score_v1_candidate"


@dataclass(frozen=True)
class ScoreSpec:
    score_id: str
    source_column: str
    role: str
    version: int
    scale_type: str
    direction: str
    active: bool
    description: str


SCORE_REGISTRY: dict[str, ScoreSpec] = {
    OPPORTUNITY_SCORE_V0: ScoreSpec(
        score_id=OPPORTUNITY_SCORE_V0,
        source_column=OPPORTUNITY_SCORE_V0,
        role="opportunity",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_attention",
        active=True,
        description="Active backward-compatible opportunity score used by the default leaderboard.",
    ),
    TRADER_SCORE_V0: ScoreSpec(
        score_id=TRADER_SCORE_V0,
        source_column=TRADER_SCORE_V0,
        role="trader",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_actionability",
        active=False,
        description="Experimental Trader Mode score for compressed actionable setups.",
    ),
    LEADER_QUALITY_SCORE: ScoreSpec(
        score_id=LEADER_QUALITY_SCORE,
        source_column=LEADER_QUALITY_SCORE,
        role="leader_component",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_stronger_leadership",
        active=False,
        description="Layer 4 component measuring relative leadership quality.",
    ),
    COMPRESSION_QUALITY_SCORE: ScoreSpec(
        score_id=COMPRESSION_QUALITY_SCORE,
        source_column=COMPRESSION_QUALITY_SCORE,
        role="setup_component",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_compression_quality",
        active=False,
        description="Layer 4 component measuring compression quality after data/staleness guardrails.",
    ),
    RELATIVE_ACCUMULATION_SCORE: ScoreSpec(
        score_id=RELATIVE_ACCUMULATION_SCORE,
        source_column=RELATIVE_ACCUMULATION_SCORE,
        role="setup_component",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_relative_accumulation",
        active=False,
        description="Layer 4 component measuring relative improvement during compression.",
    ),
    SETUP_READINESS_SCORE: ScoreSpec(
        score_id=SETUP_READINESS_SCORE,
        source_column=SETUP_READINESS_SCORE,
        role="setup_component",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_setup_readiness",
        active=False,
        description="Layer 4 component measuring reclaim and confirmation behavior.",
    ),
    EXTENSION_RISK_SCORE: ScoreSpec(
        score_id=EXTENSION_RISK_SCORE,
        source_column=EXTENSION_RISK_SCORE,
        role="risk_component",
        version=0,
        scale_type="bounded_0_100",
        direction="lower_is_better_attention",
        active=False,
        description="Layer 4 component measuring extension and rollover risk; inverted in score research.",
    ),
    DATA_QUALITY_SCORE: ScoreSpec(
        score_id=DATA_QUALITY_SCORE,
        source_column=DATA_QUALITY_SCORE,
        role="quality_component",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_data_quality",
        active=False,
        description="Layer 4 component measuring data/feed quality guardrails.",
    ),
    OPPORTUNITY_SCORE_V1_CANDIDATE: ScoreSpec(
        score_id=OPPORTUNITY_SCORE_V1_CANDIDATE,
        source_column=OPPORTUNITY_SCORE_V1_CANDIDATE,
        role="opportunity_candidate",
        version=1,
        scale_type="bounded_0_100",
        direction="higher_is_better_attention",
        active=False,
        description="Documented future opportunity score candidate; not produced or active yet.",
    ),
}


RESEARCH_SCORE_IDS = (
    OPPORTUNITY_SCORE_V0,
    TRADER_SCORE_V0,
    LEADER_QUALITY_SCORE,
    COMPRESSION_QUALITY_SCORE,
    RELATIVE_ACCUMULATION_SCORE,
    SETUP_READINESS_SCORE,
    EXTENSION_RISK_SCORE,
    DATA_QUALITY_SCORE,
)


def get_score_spec(score_id: str) -> ScoreSpec:
    try:
        return SCORE_REGISTRY[score_id]
    except KeyError as exc:
        raise KeyError(f"Unknown score_id: {score_id}") from exc
