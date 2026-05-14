import pandas as pd

from app.indicators.candle_patterns import detect_latest_pattern


def test_bullish_engulfing_detected() -> None:
    df = pd.DataFrame(
        [
            {"open": 110, "high": 112, "low": 100, "close": 102},
            {"open": 101, "high": 116, "low": 99, "close": 114},
        ]
    )
    assert detect_latest_pattern(df) == "bullish_engulfing"


def test_inside_bar_detected() -> None:
    df = pd.DataFrame(
        [
            {"open": 100, "high": 112, "low": 96, "close": 108},
            {"open": 106, "high": 110, "low": 99, "close": 107},
        ]
    )
    assert detect_latest_pattern(df) == "inside_bar"

