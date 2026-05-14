from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from app.config import Settings
from app.data.instruments import InstrumentRecord, normalize_instruments


class ZerodhaClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._kite = None

    @property
    def kite(self):
        if self._kite is not None:
            return self._kite

        if not self.settings.kite_api_key or not self.settings.kite_access_token:
            raise ValueError("KITE_API_KEY and KITE_ACCESS_TOKEN are required.")

        try:
            from kiteconnect import KiteConnect
        except ImportError as exc:
            raise ImportError("Install kiteconnect with `pip install -r requirements.txt`.") from exc

        kite = KiteConnect(api_key=self.settings.kite_api_key)
        kite.set_access_token(self.settings.kite_access_token)
        self._kite = kite
        return kite

    def fetch_instruments(self, exchange: str = "NSE") -> list[InstrumentRecord]:
        raw = self.kite.instruments(exchange)
        return normalize_instruments(raw)

    def login_url(self) -> str:
        if not self.settings.kite_api_key:
            raise ValueError("KITE_API_KEY is required.")
        try:
            from kiteconnect import KiteConnect
        except ImportError as exc:
            raise ImportError("Install kiteconnect with `pip install -r requirements.txt`.") from exc
        return KiteConnect(api_key=self.settings.kite_api_key).login_url()

    def generate_access_token(self, request_token: str) -> dict:
        if not self.settings.kite_api_key or not self.settings.kite_api_secret:
            raise ValueError("KITE_API_KEY and KITE_API_SECRET are required.")
        try:
            from kiteconnect import KiteConnect
        except ImportError as exc:
            raise ImportError("Install kiteconnect with `pip install -r requirements.txt`.") from exc
        kite = KiteConnect(api_key=self.settings.kite_api_key)
        data = kite.generate_session(request_token, api_secret=self.settings.kite_api_secret)
        return {
            "access_token": data.get("access_token"),
            "public_token": data.get("public_token"),
            "user_id": data.get("user_id"),
            "user_name": data.get("user_name"),
            "login_time": str(data.get("login_time")),
        }

    def historical_daily(
        self,
        instrument_token: int,
        from_date: date,
        to_date: date,
    ) -> pd.DataFrame:
        raw = self.kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval="day",
            continuous=False,
            oi=False,
        )
        df = pd.DataFrame(raw)
        if df.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df[["date", "open", "high", "low", "close", "volume"]]

    def quote_ltp(self, exchange_symbol: str) -> float | None:
        quote = self.kite.ltp([exchange_symbol])
        value = quote.get(exchange_symbol)
        if not value:
            return None
        return float(value["last_price"])

    def quote_ltp_many(self, exchange_symbols: list[str]) -> dict[str, float | None]:
        if not exchange_symbols:
            return {}
        quote = self.kite.ltp(exchange_symbols)
        return {
            exchange_symbol: (
                float(value["last_price"])
                if (value := quote.get(exchange_symbol)) and value.get("last_price") is not None
                else None
            )
            for exchange_symbol in exchange_symbols
        }


def five_year_window(today: date | None = None) -> tuple[date, date]:
    end = today or datetime.now().date()
    start = subtract_years(end, 5)
    return start, end


def subtract_years(value: date, years: int) -> date:
    try:
        return date(value.year - years, value.month, value.day)
    except ValueError:
        return date(value.year - years, value.month, 28)
