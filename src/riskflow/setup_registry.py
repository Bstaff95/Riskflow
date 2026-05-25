from __future__ import annotations

from dataclasses import dataclass

from .state_registry import STATE_MODEL_V0

COMPRESSION_SCORE_V0 = "compression_score_v0"
SETUP_QUALITY_V0 = "setup_quality_v0"
OPPORTUNITY_SCORE_V0 = "opportunity_score_v0"
TRADER_SCORE_V0 = "trader_score_v0"


@dataclass(frozen=True)
class SetupSpec:
    setup_id: str
    role: str
    version: int
    scale_type: str
    direction: str
    description: str
    allowed_downstream_use: tuple[str, ...] = ()


SETUP_REGISTRY: dict[str, SetupSpec] = {
    COMPRESSION_SCORE_V0: SetupSpec(
        setup_id=COMPRESSION_SCORE_V0,
        role="compression",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_more_compressed",
        description="Asset-relative compression score derived from volatility/range percentiles.",
        allowed_downstream_use=("scan", "states", "scoring", "event_study", "reports"),
    ),
    STATE_MODEL_V0: SetupSpec(
        setup_id=STATE_MODEL_V0,
        role="state_model",
        version=0,
        scale_type="categorical",
        direction="not_ordered",
        description="Initial deterministic lifecycle state model.",
        allowed_downstream_use=("scan", "scoring", "event_study", "reports"),
    ),
    SETUP_QUALITY_V0: SetupSpec(
        setup_id=SETUP_QUALITY_V0,
        role="setup_quality",
        version=0,
        scale_type="bounded_0_100_components",
        direction="higher_is_better_setup_quality",
        description="Explainable setup-quality component scores for Trader Mode research.",
        allowed_downstream_use=("scan", "event_study", "reports"),
    ),
    OPPORTUNITY_SCORE_V0: SetupSpec(
        setup_id=OPPORTUNITY_SCORE_V0,
        role="opportunity_score",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_opportunity",
        description="Backward-compatible active opportunity score hypothesis.",
        allowed_downstream_use=("scan", "reports"),
    ),
    TRADER_SCORE_V0: SetupSpec(
        setup_id=TRADER_SCORE_V0,
        role="trader_score",
        version=0,
        scale_type="bounded_0_100",
        direction="higher_is_better_current_setup",
        description="Experimental Trader Mode ranking score; not the active default leaderboard sort.",
        allowed_downstream_use=("scan", "setup_research", "reports"),
    ),
}


def get_setup_spec(setup_id: str) -> SetupSpec:
    try:
        return SETUP_REGISTRY[setup_id]
    except KeyError as exc:
        raise KeyError(f"Unknown setup_id: {setup_id}") from exc
