from __future__ import annotations

from functools import lru_cache

import pandas as pd


DHAN_SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"


@lru_cache(maxsize=1)
def bse_equity_symbols() -> list[str]:
    """Return BSE equity symbols in Yahoo-compatible `.BO` form.

    Dhan publishes a free scrip master covering BSE/NSE instruments. We only keep
    BSE equity shares (`ES`) with a trading symbol, then suffix `.BO` for Yahoo.
    Many small BSE symbols still may not have Yahoo historical data.
    """
    df = pd.read_csv(DHAN_SCRIP_MASTER_URL, dtype=str)
    required = {
        "SEM_EXM_EXCH_ID",
        "SEM_SEGMENT",
        "SEM_EXCH_INSTRUMENT_TYPE",
        "SEM_TRADING_SYMBOL",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dhan scrip master missing columns: {', '.join(sorted(missing))}")

    equities = df[
        (df["SEM_EXM_EXCH_ID"] == "BSE")
        & (df["SEM_SEGMENT"] == "E")
        & (df["SEM_EXCH_INSTRUMENT_TYPE"] == "ES")
    ].copy()
    symbols = []
    for raw in equities["SEM_TRADING_SYMBOL"].dropna().astype(str):
        symbol = raw.strip().upper()
        if not symbol or symbol == "NAN":
            continue
        symbols.append(f"{symbol}.BO")
    return sorted(dict.fromkeys(symbols))

