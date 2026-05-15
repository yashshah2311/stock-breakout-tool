from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


DEFAULT_NIFTY50_SYMBOLS = [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BAJFINANCE",
    "BAJAJFINSV",
    "BEL",
    "BHARTIARTL",
    "CIPLA",
    "COALINDIA",
    "DRREDDY",
    "EICHERMOT",
    "GRASIM",
    "HCLTECH",
    "HDFCBANK",
    "HDFCLIFE",
    "HEROMOTOCO",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "ITC",
    "JIOFIN",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "M&M",
    "MARUTI",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "RELIANCE",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
    "SUNPHARMA",
    "TATACONSUM",
    "TATAMOTORS",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "TRENT",
    "ULTRACEMCO",
    "WIPRO",
]


DEFAULT_NIFTY100_SYMBOLS = list(
    dict.fromkeys(
        DEFAULT_NIFTY50_SYMBOLS
        + [
            "ABB",
            "ADANIENSOL",
            "ADANIGREEN",
            "ADANIPOWER",
            "AMBUJACEM",
            "BAJAJHLDNG",
            "BANKBARODA",
            "BHEL",
            "BOSCHLTD",
            "BPCL",
            "BRITANNIA",
            "CANBK",
            "CGPOWER",
            "CHOLAFIN",
            "DABUR",
            "DIVISLAB",
            "DLF",
            "DMART",
            "GAIL",
            "GODREJCP",
            "HAL",
            "HAVELLS",
            "ICICIGI",
            "ICICIPRULI",
            "INDIGO",
            "IOC",
            "IRFC",
            "JSWENERGY",
            "LICI",
            "LODHA",
            "LTIM",
            "MANKIND",
            "MAXHEALTH",
            "MOTHERSON",
            "NAUKRI",
            "PFC",
            "PIDILITIND",
            "PNB",
            "RECLTD",
            "SIEMENS",
            "TVSMOTOR",
            "UNIONBANK",
            "UNITDSPR",
            "VBL",
            "VEDL",
            "ZYDUSLIFE",
            "ETERNAL",
            "TORNTPHARM",
            "SHREECEM",
            "PERSISTENT",
            "POLYCAB",
            "INDHOTEL",
            "JINDALSTEL",
            "OIL",
            "NHPC",
            "ATGL",
            "TATAPOWER",
            "HINDPETRO",
            "MARICO",
            "COLPAL",
            "YESBANK",
        ]
    )
)[:100]


SECTOR_BY_SYMBOL = {
    "ABB": "Capital Goods",
    "ADANIENSOL": "Power & Utilities",
    "ADANIENT": "Metals & Mining",
    "ADANIGREEN": "Power & Utilities",
    "ADANIPORTS": "Infrastructure",
    "ADANIPOWER": "Power & Utilities",
    "AMBUJACEM": "Cement",
    "APOLLOHOSP": "Healthcare",
    "ASIANPAINT": "Consumer",
    "AXISBANK": "Banks",
    "BAJAJ-AUTO": "Auto",
    "BAJAJFINSV": "Financial Services",
    "BAJAJHLDNG": "Financial Services",
    "BAJFINANCE": "Financial Services",
    "BANKBARODA": "Banks",
    "BEL": "Defence",
    "BHARTIARTL": "Telecom",
    "BHEL": "Capital Goods",
    "BOSCHLTD": "Auto",
    "BPCL": "Oil & Gas",
    "BRITANNIA": "Consumer",
    "CANBK": "Banks",
    "CGPOWER": "Capital Goods",
    "CHOLAFIN": "Financial Services",
    "CIPLA": "Pharma",
    "COALINDIA": "Metals & Mining",
    "DABUR": "Consumer",
    "DIVISLAB": "Pharma",
    "DLF": "Real Estate",
    "DMART": "Retail",
    "DRREDDY": "Pharma",
    "EICHERMOT": "Auto",
    "ETERNAL": "Internet",
    "GAIL": "Oil & Gas",
    "GODREJCP": "Consumer",
    "GRASIM": "Diversified",
    "HAL": "Defence",
    "HAVELLS": "Consumer Durables",
    "HCLTECH": "IT",
    "HDFCBANK": "Banks",
    "HDFCLIFE": "Insurance",
    "HEROMOTOCO": "Auto",
    "HINDALCO": "Metals & Mining",
    "HINDUNILVR": "Consumer",
    "ICICIBANK": "Banks",
    "ICICIGI": "Insurance",
    "ICICIPRULI": "Insurance",
    "INDIGO": "Aviation",
    "INDUSINDBK": "Banks",
    "INFY": "IT",
    "IOC": "Oil & Gas",
    "IRFC": "Financial Services",
    "ITC": "Consumer",
    "JIOFIN": "Financial Services",
    "JSWENERGY": "Power & Utilities",
    "JSWSTEEL": "Metals & Mining",
    "KOTAKBANK": "Banks",
    "LICI": "Insurance",
    "LODHA": "Real Estate",
    "LT": "Infrastructure",
    "LTIM": "IT",
    "M&M": "Auto",
    "MANKIND": "Pharma",
    "MARUTI": "Auto",
    "MAXHEALTH": "Healthcare",
    "MOTHERSON": "Auto",
    "NAUKRI": "Internet",
    "NESTLEIND": "Consumer",
    "NTPC": "Power & Utilities",
    "ONGC": "Oil & Gas",
    "PERSISTENT": "IT",
    "PFC": "Financial Services",
    "PIDILITIND": "Consumer",
    "PNB": "Banks",
    "POLYCAB": "Capital Goods",
    "POWERGRID": "Power & Utilities",
    "RECLTD": "Financial Services",
    "RELIANCE": "Oil & Gas",
    "SBILIFE": "Insurance",
    "SBIN": "Banks",
    "SHREECEM": "Cement",
    "SHRIRAMFIN": "Financial Services",
    "SIEMENS": "Capital Goods",
    "SUNPHARMA": "Pharma",
    "TATACONSUM": "Consumer",
    "TATAMOTORS": "Auto",
    "TATASTEEL": "Metals & Mining",
    "TCS": "IT",
    "TECHM": "IT",
    "TITAN": "Consumer",
    "TORNTPHARM": "Pharma",
    "TRENT": "Retail",
    "TVSMOTOR": "Auto",
    "ULTRACEMCO": "Cement",
    "UNIONBANK": "Banks",
    "UNITDSPR": "Consumer",
    "VBL": "Consumer",
    "VEDL": "Metals & Mining",
    "WIPRO": "IT",
    "ZYDUSLIFE": "Pharma",
}


def sector_for_symbol(symbol: str) -> str:
    clean = symbol.upper().removesuffix(".BO").removesuffix(".NS")
    return SECTOR_BY_SYMBOL.get(clean, "Other")


@dataclass(frozen=True)
class InstrumentRecord:
    instrument_token: int
    tradingsymbol: str
    name: str | None
    exchange: str
    segment: str | None
    instrument_type: str | None
    tick_size: float | None
    lot_size: int | None


def normalize_instruments(raw: Iterable[dict]) -> list[InstrumentRecord]:
    normalized: list[InstrumentRecord] = []
    for row in raw:
        symbol = str(row.get("tradingsymbol") or "").strip().upper()
        token = row.get("instrument_token")
        if not symbol or token is None:
            continue

        normalized.append(
            InstrumentRecord(
                instrument_token=int(token),
                tradingsymbol=symbol,
                name=row.get("name"),
                exchange=str(row.get("exchange") or "NSE"),
                segment=row.get("segment"),
                instrument_type=row.get("instrument_type"),
                tick_size=float(row["tick_size"]) if row.get("tick_size") is not None else None,
                lot_size=int(row["lot_size"]) if row.get("lot_size") is not None else None,
            )
        )
    return normalized


def filter_equity_symbols(instruments: Iterable[InstrumentRecord], symbols: Iterable[str]) -> list[InstrumentRecord]:
    wanted = {symbol.upper() for symbol in symbols}
    filtered = []
    for instrument in instruments:
        if instrument.tradingsymbol not in wanted:
            continue
        if instrument.exchange != "NSE":
            continue
        if instrument.instrument_type and instrument.instrument_type != "EQ":
            continue
        filtered.append(instrument)
    return filtered
