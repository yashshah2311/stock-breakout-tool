from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.repository import CandleRepository, init_db


def synthetic_breakout(symbol: str, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days = 310
    dates = pd.bdate_range(end=date.today(), periods=days).date
    base = 100 + np.cumsum(rng.normal(0.08, 0.9, size=days))
    base[-30:-5] = np.linspace(base[-30], base[-30] * 1.03, 25) + rng.normal(0, 0.35, 25)
    base[-1] = max(base[-50:-1]) * (1.01 + seed * 0.001)
    high = base * (1 + rng.uniform(0.003, 0.016, days))
    low = base * (1 - rng.uniform(0.003, 0.016, days))
    open_ = base * (1 + rng.normal(0, 0.004, days))
    volume = rng.integers(800_000, 1_600_000, days)
    volume[-1] = int(volume[-20:].mean() * (1.6 + seed * 0.05))
    return pd.DataFrame(
        {
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": base,
            "volume": volume,
        }
    )


def main() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    repo = CandleRepository(settings.database_url)
    total = 0
    for idx, symbol in enumerate(["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"], start=1):
        total += repo.upsert_candles(symbol, 1000 + idx, synthetic_breakout(symbol, idx))
    print(f"Seeded {total} sample candles.")


if __name__ == "__main__":
    main()
