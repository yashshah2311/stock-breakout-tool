from __future__ import annotations

from datetime import date

from app.config import Settings
from app.data.yahoo_client import YahooFinanceClient
from app.data.zerodha_client import ZerodhaClient, five_year_window, subtract_years
from app.db.repository import CandleRepository, InstrumentRepository


def fetch_and_store_history(
    symbols: list[str],
    years: int,
    settings: Settings,
    end_date: date | None = None,
) -> dict[str, int | list[str]]:
    if years < 1:
        raise ValueError("years must be at least 1.")

    if settings.data_provider.lower() == "yahoo":
        return fetch_and_store_yahoo_history(symbols=symbols, years=years, settings=settings, end_date=end_date)

    end = end_date or date.today()
    start = subtract_years(end, years)

    instrument_repo = InstrumentRepository(settings.database_url)
    candle_repo = CandleRepository(settings.database_url)
    client = ZerodhaClient(settings)

    requested = [symbol.upper() for symbol in symbols]
    instruments = instrument_repo.get_by_symbols(requested)
    missing = sorted(set(requested) - set(instruments.keys()))
    if missing:
        fetched = client.fetch_instruments(settings.kite_exchange)
        instrument_repo.upsert_many(fetched)
        instruments = instrument_repo.get_by_symbols(requested)
        missing = sorted(set(requested) - set(instruments.keys()))

    if missing:
        raise ValueError(f"Missing instrument tokens for: {', '.join(missing)}")

    stored = 0
    failed: list[str] = []
    for symbol in requested:
        instrument = instruments[symbol]
        try:
            candles = client.historical_daily(instrument.instrument_token, start, end)
        except Exception:
            failed.append(symbol)
            continue
        stored += candle_repo.upsert_candles(symbol=symbol, instrument_token=instrument.instrument_token, candles=candles)

    return {"stored_candles": stored, "failed": failed}


def fetch_and_store_yahoo_history(
    symbols: list[str],
    years: int,
    settings: Settings,
    end_date: date | None = None,
) -> dict[str, int | list[str] | str]:
    candle_repo = CandleRepository(settings.database_url)
    client = YahooFinanceClient()

    stored = 0
    failed: list[str] = []
    requested = [symbol.upper() for symbol in symbols]
    for idx, symbol in enumerate(requested, start=1):
        try:
            candles = client.historical_daily(symbol=symbol, years=years, end_date=end_date)
        except Exception:
            failed.append(symbol)
            continue
        if candles.empty:
            failed.append(symbol)
            continue
        candle_repo.delete_symbol(symbol)
        stored += candle_repo.upsert_candles(symbol=symbol, instrument_token=idx, candles=candles)

    return {"provider": "yahoo", "stored_candles": stored, "failed": failed}


def default_five_year_window() -> tuple[date, date]:
    return five_year_window()
