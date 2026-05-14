from __future__ import annotations


def build_trade_plan(features: dict) -> dict:
    close = float(features["close"])
    breakout_level = float(features["breakout_level"] or close)
    atr = max(float(features.get("atr") or 0), close * 0.01)
    swing_low = float(features.get("swing_low_20d") or close - atr)

    already_triggered = bool(features.get("valid_breakout")) and close >= breakout_level
    if already_triggered:
        entry_price = close
        entry_type = "already_triggered"
    else:
        entry_price = max(breakout_level * 1.001, close)
        entry_type = "breakout_trigger"

    atr_stop = entry_price - (1.5 * atr)
    ema_20 = float(features.get("ema_20") or 0)
    ema_stop = ema_20 * 0.997 if ema_20 > 0 else 0
    swing_stop = swing_low * 0.998
    stop_candidates = [value for value in [swing_stop, atr_stop, ema_stop] if 0 < value < entry_price]
    stop_loss = max(stop_candidates) if stop_candidates else entry_price - (1.5 * atr)
    risk_per_share = max(entry_price - stop_loss, atr * 0.5)

    target_1 = entry_price + (2.0 * risk_per_share)
    target_2 = entry_price + (3.0 * risk_per_share)
    base_low = float(features.get("base_low") or swing_low)
    breakout_candle_low = float(features.get("breakout_candle_low") or close - atr)
    breakout_buy_stop = breakout_level * 1.0025
    breakout_retest_entry = breakout_level * 1.002
    breakout_target_1 = breakout_level + max(breakout_level - base_low, risk_per_share)
    breakout_target_2 = breakout_level + 2 * max(breakout_level - base_low, risk_per_share)
    breakout_base_stop = base_low * 0.997
    breakout_atr_stop = breakout_level - 1.5 * atr
    breakout_candle_stop = breakout_candle_low * 0.998
    risk_pct = risk_per_share / entry_price * 100 if entry_price else 0
    reward_risk = (target_1 - entry_price) / risk_per_share if risk_per_share else 0

    risk_grade = "low"
    if risk_pct > 5 or features.get("extension_from_20ema_pct", 0) > 8:
        risk_grade = "medium"
    if risk_pct > 8 or features.get("atr_pct", 0) > 6:
        risk_grade = "high"

    notes = []
    if not already_triggered:
        notes.append("Wait for price to trade above breakout trigger; avoid early entry.")
    if features.get("volume_vs_20d", 0) < 1.5:
        notes.append("Volume confirmation is below ideal breakout threshold.")
    if features.get("extension_from_20ema_pct", 0) > 8:
        notes.append("Price is extended from 20 EMA; avoid chasing a gap-up.")
    if risk_pct > 8:
        notes.append("Risk per share is wide; reduce position size or skip.")
    if not notes:
        notes.append("Use position sizing so loss at stop remains within planned account risk.")

    return {
        "entry_type": entry_type,
        "entry_price": round(entry_price, 2),
        "breakout_trigger": round(breakout_level, 2),
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "risk_per_share": round(risk_per_share, 2),
        "risk_pct": round(risk_pct, 2),
        "reward_risk": round(reward_risk, 2),
        "atr_stop": round(atr_stop, 2),
        "ema_stop": round(ema_stop, 2),
        "swing_stop": round(swing_stop, 2),
        "stop_method": "tightest_valid_stop",
        "atr_multiplier": 1.5,
        "target_rr": 2.0,
        "trail_stop_rule": "After +3% profit, move stop to breakeven. After T1, trail at 2x ATR below highest close.",
        "trail_stop_distance": round(2 * atr, 2),
        "breakout_buy_stop_entry": round(breakout_buy_stop, 2),
        "breakout_retest_entry": round(breakout_retest_entry, 2),
        "breakout_next_open_entry_rule": "Enter next-day open only if prior EOD close remains above resistance.",
        "breakout_target_1": round(breakout_target_1, 2),
        "breakout_target_2": round(breakout_target_2, 2),
        "breakout_base_stop": round(breakout_base_stop, 2),
        "breakout_atr_stop": round(breakout_atr_stop, 2),
        "breakout_candle_stop": round(breakout_candle_stop, 2),
        "breakout_stop_method": "base_low_primary",
        "breakout_exit_rule": "Exit immediately if price closes back below breakout level.",
        "breakout_trail_rule": "Once up 5%, raise stop to original breakout level. After T1, trail near 20 EMA.",
        "risk_grade": risk_grade,
        "notes": notes,
    }
