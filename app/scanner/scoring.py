from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    score: int
    verdict: str
    reasons: list[str]
    risk_flags: list[str]


PATTERN_POINTS = {
    "bullish_engulfing": 10,
    "bullish_marubozu": 8,
    "inside_bar": 7,
    "hammer": 5,
    "doji": 1,
    "none": 0,
}


def score_features(features: dict) -> ScoreResult:
    reasons: list[str] = []
    risk_flags: list[str] = []

    trend = 0
    if features["above_20ema"]:
        trend += 6
    if features["ema_20_gt_50"]:
        trend += 6
    if features["above_50ema"]:
        trend += 4
    if features["ema_50_gt_200"]:
        trend += 4
    if trend >= 16:
        reasons.append("trend alignment is positive")

    volume = 0
    volume_multiple = features["volume_vs_20d"]
    if volume_multiple >= 2.0:
        volume += 20
        reasons.append("volume is at least 2x the 20-day average")
    elif volume_multiple >= 1.5:
        volume += 15
        reasons.append("volume is above 1.5x the 20-day average")
    elif volume_multiple >= 1.2:
        volume += 8
    if features["highest_volume_10"]:
        volume = min(20, volume + 5)
    volume = min(volume, 20)

    breakout = 0
    if features["close_above_50d_high"]:
        breakout += 14
        reasons.append("close cleared 50-day resistance")
    elif features["close_above_20d_high"]:
        breakout += 10
        reasons.append("close cleared 20-day high")
    elif features["near_breakout"]:
        breakout += 8
        reasons.append("price is within breakout range")
    if features["tight_base"]:
        breakout += 5
        reasons.append("recent base is tight")
    elif features["range_contraction_10d"]:
        breakout += 3
    if features["near_52w_high"]:
        breakout += 3
    breakout = min(breakout, 25)

    candle = PATTERN_POINTS.get(features["candle_pattern"], 0)
    if candle >= 7:
        reasons.append(f"latest candle pattern is {features['candle_pattern']}")

    relative_strength_score = float(features.get("relative_strength_score", 50))
    relative_strength = min(15, max(0, round(relative_strength_score / 100 * 15)))
    if relative_strength_score >= 70:
        reasons.append("relative strength is better than most scanned names")

    risk = 0
    if features["liquidity_ok"]:
        risk += 3
    else:
        risk_flags.append("average traded value is below liquidity threshold")
    if 1.0 <= features["atr_pct"] <= 5.5:
        risk += 3
    else:
        risk_flags.append("ATR profile is outside preferred swing range")
    if features["extension_from_20ema_pct"] <= 8:
        risk += 2
    else:
        risk_flags.append("price is extended from 20 EMA")
    if features["candle_body_atr_ratio"] <= 1.7:
        risk += 2
    else:
        risk_flags.append("breakout candle is oversized versus ATR")

    score = trend + volume + breakout + candle + relative_strength + risk

    if features["extension_from_20ema_pct"] > 12:
        score -= 8
    if features["atr_pct"] > 8:
        score -= 6
    if not features["liquidity_ok"]:
        score -= 10
    if features["volume_vs_20d"] < 0.8 and features["valid_breakout"]:
        score -= 8
        risk_flags.append("breakout attempt has weak volume")

    score = int(max(0, min(100, round(score))))

    if score >= 80 and features["valid_breakout"]:
        verdict = "strong_watchlist"
    elif score >= 65 and (features["valid_breakout"] or features["near_breakout"]):
        verdict = "possible_breakout"
    elif features["near_breakout"] and score >= 55:
        verdict = "near_breakout"
    elif score >= 55:
        verdict = "avoid"
        risk_flags.append("setup is interesting but incomplete")
    else:
        verdict = "reject"

    return ScoreResult(score=score, verdict=verdict, reasons=reasons, risk_flags=risk_flags)

