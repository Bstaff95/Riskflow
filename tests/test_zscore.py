import numpy as np
import pandas as pd

from riskflow.features import rolling_zscore


def test_rolling_zscore_bootstraps_before_full_window():
    series = pd.Series([1.0, 2.0, 3.0])
    result = rolling_zscore(series, window=10)

    assert result.notna().all()
    assert result.iloc[0] == 0.0
    assert result.iloc[-1] > 0.0


def test_rolling_zscore_zero_std_returns_zero_for_valid_values():
    series = pd.Series([5.0, 5.0, 5.0, np.nan, 5.0])
    result = rolling_zscore(series, window=3)

    assert result.iloc[0] == 0.0
    assert result.iloc[1] == 0.0
    assert result.iloc[2] == 0.0
    assert np.isnan(result.iloc[3])
    assert result.iloc[4] == 0.0
