from __future__ import annotations

from dataclasses import dataclass


TRANSITION_RESEARCH_V0 = "transition_research_v0"


@dataclass(frozen=True)
class TransitionResearchSpec:
    transition_model_id: str
    version: int
    description: str
    language_rule: str
    output_columns: tuple[str, ...]


TRANSITION_RESEARCH_REGISTRY: dict[str, TransitionResearchSpec] = {
    TRANSITION_RESEARCH_V0: TransitionResearchSpec(
        transition_model_id=TRANSITION_RESEARCH_V0,
        version=0,
        description=(
            "Research-only transition evidence model based on completed state runs, "
            "forward relative returns, concentration diagnostics, and optional chain/MTF context."
        ),
        language_rule=(
            "Report observed historical transition rates and uncertainty, not true probabilities, "
            "predictions, odds, or trade forecasts."
        ),
        output_columns=(
            "transition_model",
            "state_model",
            "from_state",
            "to_state",
            "observed_transition_rate",
            "classification",
        ),
    ),
}


def get_transition_research_spec(transition_model_id: str) -> TransitionResearchSpec:
    try:
        return TRANSITION_RESEARCH_REGISTRY[transition_model_id]
    except KeyError as exc:
        raise KeyError(f"Unknown transition_model_id: {transition_model_id}") from exc
