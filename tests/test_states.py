import pandas as pd
import pytest

from riskflow.state_registry import STATE_MODEL_V0, get_state_model_spec
from riskflow.states import (
    STATE_DETAIL_COLUMNS,
    VALID_STATES,
    classify_state,
    classify_state_details,
    classify_state_frame,
    classify_states,
)


def test_state_classification_returns_valid_state():
    row = pd.Series(
        {
            "final_signal": 0.8,
            "relative_component": 0.5,
            "viscosity": 0.2,
            "compression_score": 65.0,
            "signal_slope": 0.1,
            "gradient_slope": 0.1,
        }
    )

    assert classify_state(row) in VALID_STATES
    details = classify_state_details(row)
    assert details["state"] in VALID_STATES
    assert details["state_model"] == STATE_MODEL_V0
    assert 0.0 <= details["state_confidence"] <= 100.0
    assert "positive relative strength" in details["state_reason"]


def test_classify_states_vectorized_output_is_valid():
    frame = pd.DataFrame(
        {
            "final_signal": [-0.5, 0.2, 0.8],
            "relative_component": [-0.4, 0.2, 0.5],
            "viscosity": [0.0, 0.1, 0.3],
            "compression_score": [40.0, 80.0, 65.0],
            "signal_slope": [-0.1, 0.2, 0.3],
            "gradient_driver": [-0.6, 0.3, 0.9],
        }
    )

    result = classify_states(frame)

    assert set(result).issubset(VALID_STATES)


def test_classify_state_frame_outputs_layer5_contract():
    frame = pd.DataFrame(
        {
            "final_signal": [-0.2, 0.2, 0.8, 2.4],
            "relative_component": [-0.1, 0.2, 0.5, 1.0],
            "viscosity": [0.0, 0.1, 0.3, 1.1],
            "compression_score": [80.0, 85.0, 65.0, 20.0],
            "signal_slope": [-0.1, 0.4, 0.3, 0.2],
            "gradient_driver": [-0.3, 0.4, 0.9, 1.0],
        }
    )

    result = classify_state_frame(frame)

    assert list(result.columns) == STATE_DETAIL_COLUMNS
    assert result["state"].isin(VALID_STATES).all()
    assert (result["state_model"] == STATE_MODEL_V0).all()
    assert result["state_confidence"].between(0.0, 100.0).all()
    assert result["state_reason"].str.len().min() > 0
    assert "viscosity_reclaim" in result["state_tags"].iloc[1]


def test_obvious_state_examples_classify_as_expected():
    examples = [
        (
            {
                "final_signal": 2.5,
                "relative_component": 1.0,
                "viscosity": 1.2,
                "compression_score": 20.0,
            },
            "Overheated",
        ),
        (
            {
                "final_signal": -0.8,
                "relative_component": -0.6,
                "viscosity": 0.0,
                "compression_score": 35.0,
            },
            "Breakdown",
        ),
        (
            {
                "final_signal": 0.1,
                "relative_component": 0.4,
                "viscosity": -0.1,
                "compression_score": 75.0,
                "signal_slope": 0.2,
            },
            "Compression",
        ),
    ]

    for row, expected in examples:
        assert classify_state(pd.Series(row)) == expected


def test_state_registry_rejects_unknown_ids():
    assert get_state_model_spec(STATE_MODEL_V0).version == 0
    with pytest.raises(KeyError):
        get_state_model_spec("state_model_v99")
