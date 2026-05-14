from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.scanner.feature_builder import build_features, prepare_candles
from app.scanner.scoring import score_features
from app.scanner.strategy_engine import match_strategy_families
from app.scanner.trade_plan import build_trade_plan


@dataclass(frozen=True)
class BacktestConfig:
    strategy_id: str
    horizon_days: int = 10
    min_score: int = 55
    lookback_days: int = 320
    step_days: int = 5
    max_trades_per_symbol: int = 40
    risk_per_trade_pct: float = 1.0


def backtest_strategy(
    candles_by_symbol: dict[str, pd.DataFrame],
    config: BacktestConfig,
    min_avg_traded_value: float,
) -> dict:
    trades: list[dict] = []

    for symbol, raw in candles_by_symbol.items():
        if raw.empty:
            continue
        df = prepare_candles(raw)
        if len(df) < config.lookback_days + config.horizon_days + 1:
            continue

        symbol_trades = 0
        end_limit = len(df) - config.horizon_days - 1
        start_at = max(220, len(df) - config.lookback_days)
        for idx in range(start_at, end_limit, config.step_days):
            history = df.iloc[: idx + 1].copy()
            future = df.iloc[idx + 1 : idx + 1 + config.horizon_days].copy()
            try:
                features = build_features(symbol, history, min_avg_traded_value)
            except ValueError:
                continue

            features["relative_strength_score"] = 50
            score = score_features(features)
            if score.score < config.min_score:
                continue
            plan = build_trade_plan(features)
            matches = match_strategy_families(features, score.score, score.verdict, plan)
            if config.strategy_id not in matches:
                continue

            trade = _simulate_trade(symbol, history.iloc[-1], future, score.score, plan, config)
            if trade:
                trades.append(trade)
                symbol_trades += 1
            if symbol_trades >= config.max_trades_per_symbol:
                break

    return _summarize(trades, config)


def _simulate_trade(
    symbol: str,
    signal_row: pd.Series,
    future: pd.DataFrame,
    score: int,
    plan: dict,
    config: BacktestConfig,
) -> dict | None:
    if future.empty:
        return None
    entry = float(future.iloc[0]["open"])
    if entry <= 0:
        return None
    stop = min(float(plan.get("stop_loss") or 0), entry * 0.98)
    if stop <= 0:
        stop = entry * 0.96
    target = max(float(plan.get("target_1") or 0), entry + 2 * (entry - stop))
    if target <= entry:
        target = entry + 2 * (entry - stop)

    exit_price = float(future.iloc[-1]["close"])
    exit_date = future.iloc[-1]["date"]
    exit_reason = "time_exit"

    for _, row in future.iterrows():
        low = float(row["low"])
        high = float(row["high"])
        if low <= stop:
            exit_price = stop
            exit_date = row["date"]
            exit_reason = "stop"
            break
        if high >= target:
            exit_price = target
            exit_date = row["date"]
            exit_reason = "target"
            break

    return_pct = (exit_price - entry) / entry * 100
    risk_pct = max((entry - stop) / entry * 100, 0.01)
    r_multiple = return_pct / risk_pct
    return {
        "symbol": symbol,
        "signal_date": str(pd.to_datetime(signal_row["date"]).date()),
        "exit_date": str(pd.to_datetime(exit_date).date()),
        "entry": round(entry, 2),
        "exit": round(exit_price, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "score": score,
        "return_pct": round(return_pct, 2),
        "r_multiple": round(r_multiple, 2),
        "exit_reason": exit_reason,
    }


def _summarize(trades: list[dict], config: BacktestConfig) -> dict:
    if not trades:
        return {
            "strategy_id": config.strategy_id,
            "trades": [],
            "summary": {
                "sample_size": 0,
                "status": "insufficient_sample",
                "note": "No historical trades matched the requested filters.",
            },
        }

    returns = [float(item["return_pct"]) for item in trades]
    r_values = [float(item["r_multiple"]) for item in trades]
    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value <= 0]
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in r_values:
        equity += value * config.risk_per_trade_pct
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)

    sample_size = len(trades)
    expectancy_r = sum(r_values) / sample_size
    win_rate = len(wins) / sample_size * 100
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    status = "research_only"
    if sample_size >= 30 and expectancy_r > 0.15 and win_rate >= 42:
        status = "promising_needs_forward_test"
    elif sample_size >= 30 and expectancy_r <= 0:
        status = "not_robust"
    elif sample_size < 30:
        status = "insufficient_sample"

    return {
        "strategy_id": config.strategy_id,
        "summary": {
            "sample_size": sample_size,
            "win_rate_pct": round(win_rate, 2),
            "average_return_pct": round(sum(returns) / sample_size, 2),
            "average_win_pct": round(avg_win, 2),
            "average_loss_pct": round(avg_loss, 2),
            "expectancy_r": round(expectancy_r, 3),
            "max_drawdown_risk_pct": round(max_drawdown, 2),
            "target_hits": sum(1 for item in trades if item["exit_reason"] == "target"),
            "stop_hits": sum(1 for item in trades if item["exit_reason"] == "stop"),
            "time_exits": sum(1 for item in trades if item["exit_reason"] == "time_exit"),
            "status": status,
            "note": "Backtest uses next-day open entries on stored daily candles. It is research evidence, not a profit guarantee.",
        },
        "trades": trades[-100:],
    }
