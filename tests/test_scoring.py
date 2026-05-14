from app.scanner.scoring import score_features


def base_features() -> dict:
    return {
        "above_20ema": True,
        "ema_20_gt_50": True,
        "above_50ema": True,
        "ema_50_gt_200": True,
        "volume_vs_20d": 1.8,
        "highest_volume_10": True,
        "close_above_50d_high": True,
        "close_above_20d_high": True,
        "near_breakout": False,
        "tight_base": True,
        "range_contraction_10d": True,
        "near_52w_high": True,
        "candle_pattern": "bullish_engulfing",
        "relative_strength_score": 85,
        "liquidity_ok": True,
        "atr_pct": 2.5,
        "extension_from_20ema_pct": 4.0,
        "candle_body_atr_ratio": 1.1,
        "valid_breakout": True,
    }


def test_strong_watchlist_score() -> None:
    result = score_features(base_features())
    assert result.score >= 80
    assert result.verdict == "strong_watchlist"


def test_illiquid_setup_is_penalized() -> None:
    features = base_features()
    features["liquidity_ok"] = False
    result = score_features(features)
    assert "average traded value is below liquidity threshold" in result.risk_flags
    assert result.score < 90

