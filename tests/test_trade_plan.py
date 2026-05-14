from app.scanner.trade_plan import build_trade_plan


def test_trade_plan_has_entry_stop_and_targets() -> None:
    plan = build_trade_plan(
        {
            "close": 105.0,
            "breakout_level": 104.0,
            "valid_breakout": True,
            "atr": 3.0,
            "swing_low_20d": 100.0,
            "volume_vs_20d": 1.8,
            "extension_from_20ema_pct": 4.0,
            "atr_pct": 2.8,
        }
    )
    assert plan["entry_price"] == 105.0
    assert plan["stop_loss"] < plan["entry_price"]
    assert plan["target_1"] > plan["entry_price"]
    assert plan["target_2"] > plan["target_1"]

