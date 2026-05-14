from __future__ import annotations


STRATEGY_CATALOG = [
    {
        "id": "momentum_strategy",
        "number": 1,
        "label": "Strategy 1: Momentum",
        "status": "active",
        "basis": "Ride stocks in strong uptrends using EMA 20/50/200 alignment, RSI 55-72, MACD confirmation, ADX/+DI strength, stochastic trigger, ATR stop and 1:2 target.",
    },
    {
        "id": "breakout_strategy",
        "number": 2,
        "label": "Strategy 2: Breakout",
        "status": "active",
        "basis": "Daily EOD breakout above rolling 20-day resistance with buy-stop 0.25% above breakout level, measured-move targets, base-low stop, ATR fallback, candle-low tight stop, and failed-breakout exit.",
    },
    {
        "id": "swing_trading",
        "number": 3,
        "label": "Swing Trading",
        "status": "active",
        "basis": "3-10 session equity setups with trend, volume, resistance, risk, and candle context.",
    },
    {
        "id": "volatility_trading",
        "number": 4,
        "label": "Volatility Trading",
        "status": "active",
        "basis": "ATR expansion or volatility squeeze candidates where price is preparing for a larger move.",
    },
    {
        "id": "sp500_trading",
        "number": 5,
        "label": "S&P 500 Trading",
        "status": "external_market",
        "basis": "Not applicable to the current Nifty 100 equity universe.",
    },
    {
        "id": "overnight_trading",
        "number": 6,
        "label": "Overnight Trading",
        "status": "needs_backtest",
        "basis": "Requires close-to-next-open gap statistics and a separate overnight backtest.",
    },
    {
        "id": "day_trading",
        "number": 7,
        "label": "Day Trading",
        "status": "active_daily_proxy",
        "basis": "Daily high-liquidity, high-volume, high-range names that deserve intraday chart review.",
    },
    {
        "id": "mean_reversion",
        "number": 8,
        "label": "Mean Reversion",
        "status": "active",
        "basis": "Oversold or support-proximity stocks where RSI and trend extension suggest snapback potential.",
    },
    {
        "id": "nasdaq_trading",
        "number": 9,
        "label": "Nasdaq Trading",
        "status": "external_market",
        "basis": "Not applicable to the current Nifty 100 equity universe.",
    },
    {
        "id": "fixed_income",
        "number": 10,
        "label": "Fixed Income",
        "status": "external_asset",
        "basis": "Requires bond, treasury, yield, duration, and credit spread data.",
    },
    {
        "id": "candlestick_patterns",
        "number": 11,
        "label": "Candlestick Patterns",
        "status": "active",
        "basis": "Latest candle pattern such as hammer, engulfing, marubozu, inside bar, or doji.",
    },
    {
        "id": "treasuries_bonds",
        "number": 12,
        "label": "Treasuries & Bonds",
        "status": "external_asset",
        "basis": "Requires fixed-income market data, not Nifty stock candles.",
    },
    {
        "id": "technical_indicators",
        "number": 13,
        "label": "Technical Indicators",
        "status": "active",
        "basis": "EMA, RSI, ADX, ATR, volume, and breakout indicator alignment.",
    },
    {
        "id": "russell_2000",
        "number": 14,
        "label": "Russell 2000",
        "status": "external_market",
        "basis": "Not applicable to the current Nifty 100 equity universe.",
    },
    {
        "id": "seasonality_stocks",
        "number": 15,
        "label": "Stock Seasonality",
        "status": "needs_backtest",
        "basis": "Requires multi-year calendar-month/day studies before live classification.",
    },
    {
        "id": "stock_sector_rotation",
        "number": 16,
        "label": "Stock & Sector Rotation",
        "status": "active",
        "basis": "Relative strength leaders and stronger sector buckets inside Nifty 100.",
    },
    {
        "id": "momentum_trading",
        "number": 17,
        "label": "Momentum Trading",
        "status": "active",
        "basis": "3-6 month return strength, relative strength, and trend continuation.",
    },
    {
        "id": "trend_following",
        "number": 18,
        "label": "Trend Following",
        "status": "active",
        "basis": "Price above key EMAs with 20 EMA > 50 EMA and preferably 50 EMA > 200 EMA.",
    },
    {
        "id": "larry_connors",
        "number": 19,
        "label": "Larry Connors RSI",
        "status": "needs_backtest",
        "basis": "Needs a dedicated Connors/2-day RSI rule module and backtest.",
    },
    {
        "id": "trend_reversal",
        "number": 20,
        "label": "Trend Reversal",
        "status": "active",
        "basis": "Bullish reversal candles, oversold RSI, or support rejection after weakness.",
    },
    {
        "id": "sentiment_indicator",
        "number": 21,
        "label": "Sentiment Indicator",
        "status": "external_data",
        "basis": "Requires sentiment, news, put/call, FII/DII, or option positioning data.",
    },
    {
        "id": "moving_average",
        "number": 22,
        "label": "Moving Average",
        "status": "active",
        "basis": "20/50/200 EMA trend filter and moving-average alignment.",
    },
    {
        "id": "macro_economy",
        "number": 23,
        "label": "Macro Economy",
        "status": "external_data",
        "basis": "Requires rates, inflation, currency, GDP, and macro regime data.",
    },
    {
        "id": "bear_market",
        "number": 24,
        "label": "Bear Market",
        "status": "active",
        "basis": "Weak trend names or below-200 EMA candidates useful for defensive/short watchlists.",
    },
    {
        "id": "market_neutral",
        "number": 25,
        "label": "Market Neutral",
        "status": "needs_backtest",
        "basis": "Requires pair selection, hedge ratios, spread z-scores, and portfolio construction.",
    },
    {
        "id": "breakout_trading",
        "number": 26,
        "label": "Breakout Trading",
        "status": "active",
        "basis": "Close above 20/50-day resistance or within 2% of breakout level.",
    },
    {
        "id": "volatility_indicator",
        "number": 27,
        "label": "Volatility Indicator",
        "status": "active",
        "basis": "ATR percentage and range-contraction rules.",
    },
    {
        "id": "oscillator_indicator",
        "number": 28,
        "label": "Oscillator Indicator",
        "status": "active",
        "basis": "RSI overbought/oversold readings as a filter, not a standalone signal.",
    },
    {
        "id": "price_action",
        "number": 29,
        "label": "Price Action",
        "status": "active",
        "basis": "Inside bars, support/resistance proximity, tight bases, and breakout structure.",
    },
    {
        "id": "random_indicator",
        "number": 30,
        "label": "Mixed Indicator",
        "status": "active",
        "basis": "Multi-factor setups that do not fit a cleaner single family.",
    },
    {
        "id": "gold_trading",
        "number": 31,
        "label": "Gold Trading",
        "status": "external_asset",
        "basis": "Requires gold spot/futures/ETF data, not Nifty stock candles.",
    },
    {
        "id": "forex_trading",
        "number": 32,
        "label": "Forex Trading",
        "status": "external_asset",
        "basis": "Requires currency pair data, not Nifty stock candles.",
    },
]


def strategy_catalog() -> list[dict]:
    return STRATEGY_CATALOG


def match_strategy_families(features: dict, score: int, verdict: str, trade_plan: dict) -> list[str]:
    if features.get("data_missing"):
        return []

    matches: list[str] = []

    def add(strategy_id: str, condition: bool) -> None:
        if condition and strategy_id not in matches:
            matches.append(strategy_id)

    rsi = float(features.get("rsi_14") or 0)
    atr_pct = float(features.get("atr_pct") or 0)
    volume_vs_20d = float(features.get("volume_vs_20d") or 0)
    rs_score = float(features.get("relative_strength_score") or 50)
    returns_63d = float(features.get("returns_63d") or 0)
    returns_126d = float(features.get("returns_126d") or 0)
    extension = float(features.get("extension_from_20ema_pct") or 0)
    pattern = features.get("candle_pattern") or "none"
    bullish_pattern = pattern in {"hammer", "bullish_engulfing", "bullish_marubozu"}
    actionable = verdict in {"strong_watchlist", "possible_breakout", "near_breakout", "avoid"}
    momentum_entry_score = _momentum_entry_score(features)

    add("momentum_strategy", momentum_entry_score >= 6 and features.get("liquidity_ok", False))
    add("breakout_strategy", _breakout_strategy_score(features) >= 6 and features.get("liquidity_ok", False))
    add("swing_trading", actionable and score >= 55)
    add("volatility_trading", features.get("range_contraction_10d") or atr_pct >= 4.0)
    add("day_trading", volume_vs_20d >= 1.8 and atr_pct >= 1.2 and features.get("liquidity_ok", False))
    add(
        "mean_reversion",
        (rsi <= 35 and features.get("liquidity_ok", False)) or (rsi <= 42 and extension < -2),
    )
    add("candlestick_patterns", pattern != "none")
    add("technical_indicators", score >= 50)
    add("stock_sector_rotation", rs_score >= 70)
    add("momentum_trading", (returns_63d >= 0.08 or returns_126d >= 0.14) and rs_score >= 65)
    add(
        "trend_following",
        bool(features.get("above_20ema") and features.get("above_50ema") and features.get("ema_20_gt_50")),
    )
    add("trend_reversal", bullish_pattern and (rsi <= 50 or extension <= 1.5))
    add("moving_average", bool(features.get("above_20ema") and features.get("ema_20_gt_50")))
    add("bear_market", not features.get("above_200ema", True) and rsi < 48)
    add("breakout_trading", bool(features.get("valid_breakout") or features.get("near_breakout")))
    add("volatility_indicator", 1.0 <= atr_pct <= 5.5 or features.get("range_contraction_10d"))
    add("oscillator_indicator", rsi <= 35 or rsi >= 70)
    add(
        "price_action",
        pattern in {"inside_bar", "hammer", "bullish_engulfing", "bullish_marubozu"}
        or bool(features.get("tight_base") or features.get("valid_breakout")),
    )

    active_specific = {
        "swing_trading",
        "volatility_trading",
        "day_trading",
        "mean_reversion",
        "candlestick_patterns",
        "technical_indicators",
        "stock_sector_rotation",
        "momentum_trading",
        "trend_following",
        "trend_reversal",
        "moving_average",
        "bear_market",
        "breakout_trading",
        "volatility_indicator",
        "oscillator_indicator",
        "price_action",
        "momentum_strategy",
        "breakout_strategy",
    }
    if score >= 60 and not any(strategy_id in active_specific for strategy_id in matches):
        add("random_indicator", True)

    return matches


def _momentum_entry_score(features: dict) -> int:
    checks = [
        bool(features.get("above_20ema") and features.get("above_50ema")),
        bool(features.get("ema_20_slope_positive")),
        bool(features.get("ema_50_gt_200")),
        55 <= float(features.get("rsi_14") or 0) <= 72,
        float(features.get("macd_line") or 0) > float(features.get("macd_signal") or 0),
        float(features.get("macd_hist") or 0) > 0
        and float(features.get("macd_hist") or 0) > float(features.get("macd_hist_prev") or 0),
        float(features.get("adx_14") or 0) > 25
        and float(features.get("plus_di_14") or 0) > float(features.get("minus_di_14") or 0),
        float(features.get("stoch_k") or 0) > float(features.get("stoch_d") or 0)
        and float(features.get("stoch_k_prev") or 100) < 40,
    ]
    return sum(1 for item in checks if item)


def _breakout_strategy_score(features: dict) -> int:
    distance = float(features.get("distance_to_breakout_pct") or 99)
    checks = [
        bool(features.get("valid_breakout") or (-0.5 <= distance <= 1.5)),
        bool(features.get("tight_base") or features.get("range_contraction_10d")),
        float(features.get("volume_vs_20d") or 0) >= 1.5,
        bool(features.get("above_20ema") and features.get("above_50ema")),
        float(features.get("avg_traded_value_20d") or 0) > 0,
        bool(features.get("near_52w_high") or float(features.get("relative_strength_score") or 0) >= 60),
        1.0 <= float(features.get("atr_pct") or 0) <= 6.0,
    ]
    return sum(1 for item in checks if item)


def _confidence_from(score: int, risk_grade: str) -> str:
    if score >= 80 and risk_grade == "low":
        return "high"
    if score >= 65 and risk_grade in {"low", "medium"}:
        return "medium"
    return "low"


def _bias_from(verdict: str, score: int) -> str:
    if verdict in {"strong_watchlist", "possible_breakout"} and score >= 65:
        return "bullish"
    if verdict == "near_breakout":
        return "watch"
    return "avoid"


def build_strategy_profile(features: dict, score: int, verdict: str, trade_plan: dict) -> dict:
    tags: list[str] = []

    if features.get("tight_base"):
        tags.append("tight-base")
    if features.get("range_contraction_10d"):
        tags.append("volatility-squeeze")
    if features.get("highest_volume_10") or features.get("volume_vs_20d", 0) >= 1.8:
        tags.append("volume-confirmed")
    if features.get("near_52w_high"):
        tags.append("near-52w-high")
    if features.get("relative_strength_score", 0) >= 80:
        tags.append("relative-strength-leader")

    primary_strategy = "watchlist_setup"
    strategy_label = "Watchlist Setup"

    if features.get("valid_breakout") and features.get("volume_vs_20d", 0) >= 1.5:
        primary_strategy = "breakout_momentum"
        strategy_label = "Breakout Momentum"
    elif features.get("tight_base") and features.get("near_breakout"):
        primary_strategy = "tight_base_breakout"
        strategy_label = "Tight Base Breakout"
    elif features.get("range_contraction_10d") and features.get("near_breakout"):
        primary_strategy = "squeeze_breakout_watch"
        strategy_label = "Squeeze Breakout Watch"
    elif (
        features.get("above_20ema")
        and features.get("above_50ema")
        and features.get("extension_from_20ema_pct", 0) <= 4
        and 50 <= features.get("rsi_14", 0) <= 68
    ):
        primary_strategy = "pullback_trend_continuation"
        strategy_label = "Pullback Trend Continuation"
    elif features.get("near_52w_high") and features.get("relative_strength_score", 0) >= 80:
        primary_strategy = "relative_strength_leader"
        strategy_label = "Relative Strength Leader"

    setup_phase = "coiling"
    if trade_plan.get("entry_type") == "already_triggered":
        setup_phase = "triggered"
    elif features.get("extension_from_20ema_pct", 0) > 8:
        setup_phase = "extended"
    elif not features.get("near_breakout"):
        setup_phase = "developing"

    bias = _bias_from(verdict, score)
    confidence = _confidence_from(score, trade_plan.get("risk_grade", "medium"))

    if bias == "bullish":
        summary = (
            f"{strategy_label} with score {score}. "
            f"Best if price respects {trade_plan.get('stop_loss')} and volume stays firm."
        )
    elif bias == "watch":
        summary = (
            f"Setup is close but not fully triggered. "
            f"Wait for a clean move above {trade_plan.get('breakout_trigger')} with volume."
        )
    else:
        summary = "Interesting structure, but risk/reward is not clean enough right now."

    return {
        "primary_strategy": primary_strategy,
        "strategy_label": strategy_label,
        "setup_phase": setup_phase,
        "tags": tags,
        "prediction": {
            "bias": bias,
            "confidence": confidence,
            "horizon": "3-10 sessions",
            "summary": summary,
            "trigger_condition": f"Watch {trade_plan.get('breakout_trigger')} for confirmation.",
        },
    }
