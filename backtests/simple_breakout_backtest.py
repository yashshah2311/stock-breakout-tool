from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.repository import CandleRepository
from app.scanner.feature_builder import build_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple sanity backtest for breakout candidates.")
    parser.add_argument("symbol")
    parser.add_argument("--hold-days", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    repo = CandleRepository(settings.database_url)
    candles = repo.load_candles(args.symbol)
    if len(candles) < 260:
        raise SystemExit("Need at least 260 candles.")

    wins = 0
    losses = 0
    returns = []
    for idx in range(220, len(candles) - args.hold_days):
        window = candles.iloc[: idx + 1]
        features = build_features(args.symbol, window, settings.min_avg_traded_value)
        if not features["valid_breakout"] or features["volume_vs_20d"] < 1.5:
            continue
        entry = candles.iloc[idx + 1]["open"]
        exit_ = candles.iloc[idx + args.hold_days]["close"]
        pct = (exit_ / entry - 1) * 100
        returns.append(pct)
        if pct > 0:
            wins += 1
        else:
            losses += 1

    if not returns:
        print("No historical signals.")
        return

    avg_return = sum(returns) / len(returns)
    print(
        {
            "symbol": args.symbol.upper(),
            "signals": len(returns),
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / len(returns) * 100, 2),
            "avg_return_pct": round(avg_return, 2),
        }
    )


if __name__ == "__main__":
    main()
