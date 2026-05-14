ANALYST_SYSTEM_PROMPT = """You are a disciplined market analyst for an Indian equity swing-trading scanner.
You do not promise profits.
You only evaluate the provided computed features.
Reject weak or low-quality setups.
Focus on breakout quality, trend, volume, relative strength, and risk.
Do not invent prices or indicators that are not present in the payload.
Return strict JSON matching the schema."""


def build_user_payload(scan_date: str, market_context: dict, candidates: list[dict]) -> dict:
    compact = []
    for item in candidates:
        features = item["features"]
        compact.append(
            {
                "symbol": item["symbol"],
                "close": item["close"],
                "score": item["score"],
                "engine_verdict": item["verdict"],
                "breakout_level": item["breakout_level"],
                "distance_to_breakout_pct": features["distance_to_breakout_pct"],
                "volume_vs_20d": features["volume_vs_20d"],
                "above_20ema": features["above_20ema"],
                "above_50ema": features["above_50ema"],
                "above_200ema": features["above_200ema"],
                "ema_20_gt_50": features["ema_20_gt_50"],
                "near_52w_high": features["near_52w_high"],
                "range_contraction_10d": features["range_contraction_10d"],
                "tight_base": features["tight_base"],
                "candle_pattern": features["candle_pattern"],
                "atr_pct": features["atr_pct"],
                "extension_from_20ema_pct": features["extension_from_20ema_pct"],
                "relative_strength_score": features.get("relative_strength_score", 50),
                "liquidity_ok": features["liquidity_ok"],
                "reasons": item["reasons"],
                "risk_flags": item["risk_flags"],
                "swing_low_20d": features["swing_low_20d"],
            }
        )
    return {
        "scan_date": scan_date,
        "market_context": market_context,
        "stocks": compact,
        "instructions": {
            "top_picks": "Only include high-quality breakouts or clean near-breakouts.",
            "near_breakouts": "Include stocks within 0-2 percent of breakout with strong structure.",
            "avoid_list": "Include attractive-looking setups that fail volume, extension, liquidity, or risk filters.",
        },
    }

