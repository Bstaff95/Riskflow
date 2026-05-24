import pandas as pd

from riskflow.resample import resample_ohlcv


def test_resample_ohlcv_rolls_daily_to_3d():
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    frame = pd.DataFrame(
        {
            "open": [10, 11, 12, 13, 14, 15],
            "high": [12, 13, 14, 15, 16, 17],
            "low": [9, 8, 10, 12, 11, 13],
            "close": [11, 12, 13, 14, 15, 16],
            "volume": [1, 2, 3, 4, 5, 6],
        },
        index=dates,
    )

    output = resample_ohlcv(frame, "3d")

    assert list(output.index) == [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-04")]
    assert output.iloc[0].to_dict() == {
        "open": 10,
        "high": 14,
        "low": 8,
        "close": 13,
        "volume": 6,
    }
    assert output.iloc[1].to_dict() == {
        "open": 13,
        "high": 17,
        "low": 11,
        "close": 16,
        "volume": 15,
    }


def test_resample_ohlcv_uses_shared_3d_calendar_anchor():
    first = pd.DataFrame(
        {
            "open": [10, 11, 12],
            "high": [11, 12, 13],
            "low": [9, 10, 11],
            "close": [11, 12, 13],
            "volume": [1, 1, 1],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )
    second = pd.DataFrame(
        {
            "open": [20, 21, 22],
            "high": [21, 22, 23],
            "low": [19, 20, 21],
            "close": [21, 22, 23],
            "volume": [1, 1, 1],
        },
        index=pd.date_range("2024-01-02", periods=3, freq="D"),
    )

    first_output = resample_ohlcv(first, "3d")
    second_output = resample_ohlcv(second, "3d")

    assert pd.Timestamp("2024-01-01") in first_output.index
    assert pd.Timestamp("2024-01-01") in second_output.index


def test_resample_ohlcv_rolls_hourly_to_4h():
    dates = pd.date_range("2024-01-01", periods=8, freq="h")
    frame = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105, 106, 107],
            "high": [101, 104, 103, 105, 106, 108, 107, 109],
            "low": [99, 98, 100, 101, 103, 102, 105, 106],
            "close": [101, 102, 103, 104, 105, 106, 107, 108],
            "volume": [10, 20, 30, 40, 50, 60, 70, 80],
        },
        index=dates,
    )

    output = resample_ohlcv(frame, "4h")

    assert list(output.index) == [pd.Timestamp("2024-01-01 00:00"), pd.Timestamp("2024-01-01 04:00")]
    assert output.iloc[0].to_dict() == {
        "open": 100,
        "high": 105,
        "low": 98,
        "close": 104,
        "volume": 100,
    }
    assert output.iloc[1].to_dict() == {
        "open": 104,
        "high": 109,
        "low": 102,
        "close": 108,
        "volume": 260,
    }


def test_resample_ohlcv_rolls_daily_to_week_starting_monday():
    dates = pd.date_range("2024-01-01", periods=7, freq="D")
    frame = pd.DataFrame(
        {
            "open": [1, 2, 3, 4, 5, 6, 7],
            "high": [2, 3, 4, 5, 6, 7, 8],
            "low": [0, 1, 2, 3, 4, 5, 6],
            "close": [2, 3, 4, 5, 6, 7, 8],
            "volume": [1, 1, 1, 1, 1, 1, 1],
        },
        index=dates,
    )

    output = resample_ohlcv(frame, "1w")

    assert list(output.index) == [pd.Timestamp("2024-01-01")]
    assert output.iloc[0].to_dict() == {
        "open": 1,
        "high": 8,
        "low": 0,
        "close": 8,
        "volume": 7,
    }
