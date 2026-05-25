from __future__ import annotations

from dataclasses import dataclass


STATE_MODEL_V0 = "state_model_v0"
STATE_MODEL_V1_CANDIDATE = "state_model_v1_candidate"

STATE_TAGS_V0 = {
    "above_viscosity",
    "below_viscosity",
    "compressed",
    "dead_money",
    "expanded",
    "gradient_rising",
    "near_zero",
    "overheated",
    "relative_negative",
    "relative_positive",
    "rolling_over",
    "signal_negative",
    "signal_positive",
    "signal_slope_falling",
    "signal_slope_rising",
    "viscosity_reclaim",
    "zero_reclaim",
}


@dataclass(frozen=True)
class StateModelSpec:
    state_model_id: str
    version: int
    states: tuple[str, ...]
    tags: tuple[str, ...]
    description: str
    required_columns: tuple[str, ...]
    output_columns: tuple[str, ...]


STATE_MODEL_REGISTRY: dict[str, StateModelSpec] = {
    STATE_MODEL_V0: StateModelSpec(
        state_model_id=STATE_MODEL_V0,
        version=0,
        states=(
            "Dead Money",
            "Weak",
            "Compression",
            "Relative Accumulation",
            "Emerging Leader",
            "Confirmed Leader",
            "Overheated",
            "Distribution",
            "Breakdown",
            "Unknown",
        ),
        tags=tuple(sorted(STATE_TAGS_V0)),
        description="Initial deterministic lifecycle state model for Riskflow meme MVP.",
        required_columns=("final_signal", "relative_component", "viscosity"),
        output_columns=("state", "state_model", "state_confidence", "state_reason", "state_tags"),
    ),
    STATE_MODEL_V1_CANDIDATE: StateModelSpec(
        state_model_id=STATE_MODEL_V1_CANDIDATE,
        version=1,
        states=(
            "Dead Money",
            "Weak",
            "Compression",
            "Relative Accumulation",
            "Emerging Leader",
            "Confirmed Leader",
            "Overheated",
            "Distribution",
            "Breakdown",
            "Unknown",
        ),
        tags=tuple(sorted(STATE_TAGS_V0)),
        description="Planned evidence-weighted candidate state model; not active in production scans.",
        required_columns=(
            "final_signal",
            "relative_component",
            "viscosity",
            "compression_score",
            "signal_slope",
            "extension_risk_score",
        ),
        output_columns=(
            "state_v1_candidate",
            "state_v1_confidence",
            "state_v1_alternate",
            "state_v1_scores",
            "state_v1_reason",
        ),
    ),
}


def get_state_model_spec(state_model_id: str) -> StateModelSpec:
    try:
        return STATE_MODEL_REGISTRY[state_model_id]
    except KeyError as exc:
        raise KeyError(f"Unknown state_model_id: {state_model_id}") from exc
