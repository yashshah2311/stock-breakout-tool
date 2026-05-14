from __future__ import annotations

from datetime import date, timedelta
from time import time

import pandas as pd

from app.data.zerodha_client import subtract_years


class YahooFinanceClient:
    """Free Yahoo Finance/yfinance data source for research use."""

    def yahoo_symbol(self, symbol: str) -> str:
        clean = symbol.strip().upper()
        if clean.startswith("^") or "." in clean:
            return clean
        return f"{clean}.NS"

    def historical_daily(self, symbol: str, years: int = 5, end_date: date | None = None) -> pd.DataFrame:
        end = end_date or date.today()
        start = subtract_years(end, years)
        return self._download(symbol=symbol, start=start, end=end + timedelta(days=1), interval="1d")

    def intraday(self, symbol: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame:
        return self._download(symbol=symbol, period=period, interval=interval)

    def latest_quotes(self, symbols: list[str]) -> list[dict]:
        clean_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        if not clean_symbols:
            return []

        results = {
            symbol: {
                "symbol": symbol,
                "exchange_symbol": self.yahoo_symbol(symbol),
                "last_price": None,
                "last_time": None,
            }
            for symbol in clean_symbols
        }

        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError("Install yfinance with `pip install -r requirements.txt`.") from exc

        chunk_size = 50
        for start in range(0, len(clean_symbols), chunk_size):
            chunk = clean_symbols[start : start + chunk_size]
            provider_symbols = [self.yahoo_symbol(symbol) for symbol in chunk]
            try:
                raw = yf.download(
                    tickers=" ".join(provider_symbols),
                    period="1d",
                    interval="1m",
                    auto_adjust=False,
                    progress=False,
                    threads=True,
                    group_by="ticker",
                )
            except Exception:
                continue
            if raw is None or raw.empty:
                continue

            for symbol, provider_symbol in zip(chunk, provider_symbols, strict=True):
                symbol_df = self._extract_downloaded_symbol(raw, provider_symbol)
                if symbol_df.empty or "Close" not in symbol_df.columns:
                    continue
                symbol_df = symbol_df.dropna(subset=["Close"])
                if symbol_df.empty:
                    continue
                row = symbol_df.iloc[-1]
                results[symbol]["last_price"] = round(float(row["Close"]), 2)
                results[symbol]["last_time"] = str(symbol_df.index[-1])

        return [results[symbol] for symbol in clean_symbols]

    def latest_quote(self, symbol: str) -> dict:
        quotes = self.latest_quotes([symbol])
        if quotes:
            return quotes[0]
        return {
            "symbol": symbol.strip().upper(),
            "exchange_symbol": self.yahoo_symbol(symbol),
            "last_price": None,
            "last_time": None,
        }

    def latest_news(self, symbol: str, limit: int = 8) -> dict:
        clean = symbol.strip().upper()
        provider_symbol = self.yahoo_symbol(clean)
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError("Install yfinance with `pip install -r requirements.txt`.") from exc

        raw_items = yf.Ticker(provider_symbol).news or []
        items = []
        for raw in raw_items[: max(1, limit)]:
            content = raw.get("content") if isinstance(raw.get("content"), dict) else raw
            title = content.get("title") or raw.get("title") or ""
            summary = content.get("summary") or content.get("description") or raw.get("summary") or ""
            provider = content.get("provider") or raw.get("publisher") or {}
            provider_name = provider.get("displayName") if isinstance(provider, dict) else provider
            clickthrough = content.get("clickThroughUrl") or content.get("canonicalUrl") or raw.get("link") or {}
            url = clickthrough.get("url") if isinstance(clickthrough, dict) else clickthrough
            published_at = (
                content.get("pubDate")
                or raw.get("providerPublishTime")
                or raw.get("provider_publish_time")
                or raw.get("published")
            )
            if isinstance(published_at, (int, float)):
                age_hours = max(0, round((time() - float(published_at)) / 3600, 1))
            else:
                age_hours = None
            text = f"{title} {summary}".lower()
            risk_words = [
                "probe",
                "fraud",
                "default",
                "downgrade",
                "resigns",
                "loss",
                "miss",
                "penalty",
                "regulator",
                "sebi",
                "rbi",
                "tax",
            ]
            catalyst_words = [
                "profit",
                "growth",
                "upgrade",
                "order",
                "deal",
                "approval",
                "beats",
                "record",
                "dividend",
                "buyback",
            ]
            risk_hits = [word for word in risk_words if word in text]
            catalyst_hits = [word for word in catalyst_words if word in text]
            sentiment = "risk" if risk_hits else "catalyst" if catalyst_hits else "neutral"
            if title:
                items.append(
                    {
                        "title": title,
                        "summary": summary,
                        "provider": provider_name or "Yahoo Finance",
                        "url": url,
                        "published_at": published_at,
                        "age_hours": age_hours,
                        "sentiment": sentiment,
                        "matched_terms": risk_hits or catalyst_hits,
                    }
                )

        risk_count = sum(1 for item in items if item["sentiment"] == "risk")
        catalyst_count = sum(1 for item in items if item["sentiment"] == "catalyst")
        if risk_count:
            news_risk = "headline_risk"
        elif catalyst_count:
            news_risk = "possible_catalyst"
        elif items:
            news_risk = "neutral"
        else:
            news_risk = "no_recent_news"
        return {
            "symbol": clean,
            "provider_symbol": provider_symbol,
            "provider": "yahoo",
            "news_risk": news_risk,
            "risk_count": risk_count,
            "catalyst_count": catalyst_count,
            "items": items,
        }

    @staticmethod
    def _extract_downloaded_symbol(df: pd.DataFrame, provider_symbol: str) -> pd.DataFrame:
        if not isinstance(df.columns, pd.MultiIndex):
            return df
        first_level = df.columns.get_level_values(0)
        second_level = df.columns.get_level_values(1)
        if provider_symbol in first_level:
            return df[provider_symbol]
        if provider_symbol in second_level:
            return df.xs(provider_symbol, axis=1, level=1)
        return pd.DataFrame()

    def _download(
        self,
        symbol: str,
        interval: str,
        start: date | None = None,
        end: date | None = None,
        period: str | None = None,
    ) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError("Install yfinance with `pip install -r requirements.txt`.") from exc

        kwargs = {
            "tickers": self.yahoo_symbol(symbol),
            "interval": interval,
            "auto_adjust": False,
            "progress": False,
            "threads": False,
        }
        if period:
            kwargs["period"] = period
        else:
            kwargs["start"] = start
            kwargs["end"] = end

        df = yf.download(**kwargs)
        if df is None or df.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df = df.reset_index()
        date_col = "Datetime" if "Datetime" in df.columns else "Date"
        renamed = df.rename(
            columns={
                date_col: "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        result = renamed[["date", "open", "high", "low", "close", "volume"]].copy()
        result = result.dropna(subset=["open", "high", "low", "close"])
        result["volume"] = result["volume"].fillna(0)
        return result
