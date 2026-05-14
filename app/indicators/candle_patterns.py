from __future__ import annotations

import pandas as pd


def detect_latest_pattern(df: pd.DataFrame) -> str:
    if len(df) < 2:
        return "none"

    current = df.iloc[-1]
    previous = df.iloc[-2]
    candle_range = max(float(current["high"] - current["low"]), 0.01)
    body = abs(float(current["close"] - current["open"]))
    upper_wick = float(current["high"] - max(current["open"], current["close"]))
    lower_wick = float(min(current["open"], current["close"]) - current["low"])

    bullish = current["close"] > current["open"]
    prev_bearish = previous["close"] < previous["open"]

    if (
        bullish
        and prev_bearish
        and current["open"] <= previous["close"]
        and current["close"] >= previous["open"]
    ):
        return "bullish_engulfing"

    if current["high"] < previous["high"] and current["low"] > previous["low"]:
        return "inside_bar"

    if bullish and body / candle_range >= 0.75:
        return "bullish_marubozu"

    if lower_wick >= body * 2 and upper_wick <= max(body, candle_range * 0.15):
        return "hammer"

    if body / candle_range <= 0.1:
        return "doji"

    return "none"


def candle_body_atr_ratio(df: pd.DataFrame) -> float:
    if df.empty or "atr_14" not in df.columns:
        return 0.0
    row = df.iloc[-1]
    atr = float(row.get("atr_14") or 0)
    if atr <= 0:
        return 0.0
    return abs(float(row["close"] - row["open"])) / atr

