from app.scanner.strategy_engine import build_strategy_profile


def test_strategy_profile_for_breakout_candidate() -> None:
    features = {
        "valid_breakout": True,
        "volume_vs_20d": 1.9,
        "tight_base": True,
        "near_breakout": True,
        "range_contraction_10d": True,
        "highest_volume_10": True,
        "near_52w_high": True,
        "relative_strength_score": 84.0,
        "above_20ema": True,
        "above_50ema": True,
        "extension_from_20ema_pct": 2.4,
        "rsi_14": 63.0,
    }
    trade_plan = {
        "entry_type": "breakout_trigger",
        "stop_loss": 100.0,
        "breakout_trigger": 110.0,
        "risk_grade": "low",
    }

    result = build_strategy_profile(features, score=81, verdict="possible_breakout", trade_plan=trade_plan)

    assert result["primary_strategy"] == "breakout_momentum"
    assert result["prediction"]["bias"] == "bullish"
    assert result["prediction"]["confidence"] == "high"

