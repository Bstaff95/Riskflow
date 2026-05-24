import pandas as pd

from riskflow.states import VALID_STATES, classify_state, classify_states


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
