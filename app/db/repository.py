from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import pandas as pd
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.instruments import InstrumentRecord
from app.db.models import Base, Candle, Instrument, ScanResult


def _sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    path_text = database_url.replace("sqlite:///", "", 1)
    if path_text.startswith("./"):
        return Path.cwd() / path_text[2:]
    return Path(path_text)


@lru_cache(maxsize=8)
def get_engine(database_url: str) -> Engine:
    sqlite_path = _sqlite_path(database_url)
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def init_db(database_url: str) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)


class BaseRepository:
    def __init__(self, database_url: str):
        self.engine = get_engine(database_url)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self.session_factory() as session:
            yield session


class InstrumentRepository(BaseRepository):
    def upsert_many(self, instruments: list[InstrumentRecord]) -> int:
        if not instruments:
            return 0
        rows = [
            {
                "instrument_token": item.instrument_token,
                "tradingsymbol": item.tradingsymbol,
                "name": item.name,
                "exchange": item.exchange,
                "segment": item.segment,
                "instrument_type": item.instrument_type,
                "tick_size": item.tick_size,
                "lot_size": item.lot_size,
            }
            for item in instruments
        ]
        with self.session() as session:
            for row in rows:
                stmt = sqlite_insert(Instrument).values(**row)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Instrument.tradingsymbol],
                    set_=row,
                )
                session.execute(stmt)
            session.commit()
        return len(rows)

    def get_by_symbols(self, symbols: list[str]) -> dict[str, InstrumentRecord]:
        wanted = [symbol.upper() for symbol in symbols]
        with self.session() as session:
            rows = session.execute(
                select(Instrument).where(Instrument.tradingsymbol.in_(wanted))
            ).scalars()
            return {
                row.tradingsymbol: InstrumentRecord(
                    instrument_token=row.instrument_token,
                    tradingsymbol=row.tradingsymbol,
                    name=row.name,
                    exchange=row.exchange,
                    segment=row.segment,
                    instrument_type=row.instrument_type,
                    tick_size=row.tick_size,
                    lot_size=row.lot_size,
                )
                for row in rows
            }

    def count(self) -> int:
        with self.session() as session:
            return int(session.execute(select(func.count()).select_from(Instrument)).scalar() or 0)


class CandleRepository(BaseRepository):
    def delete_symbol(self, symbol: str) -> int:
        with self.session() as session:
            result = session.execute(delete(Candle).where(Candle.symbol == symbol.upper()))
            session.commit()
            return int(result.rowcount or 0)

    def upsert_candles(self, symbol: str, instrument_token: int, candles: pd.DataFrame) -> int:
        if candles.empty:
            return 0

        rows = []
        for record in candles.to_dict("records"):
            rows.append(
                {
                    "instrument_token": instrument_token,
                    "symbol": symbol.upper(),
                    "date": pd.to_datetime(record["date"]).date(),
                    "open": float(record["open"]),
                    "high": float(record["high"]),
                    "low": float(record["low"]),
                    "close": float(record["close"]),
                    "volume": float(record["volume"]),
                }
            )

        with self.session() as session:
            for row in rows:
                stmt = sqlite_insert(Candle).values(**row)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Candle.symbol, Candle.date],
                    set_=row,
                )
                session.execute(stmt)
            session.commit()
        return len(rows)

    def load_candles(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> pd.DataFrame:
        with self.session() as session:
            stmt = select(Candle).where(Candle.symbol == symbol.upper()).order_by(Candle.date)
            if start:
                stmt = stmt.where(Candle.date >= start)
            if end:
                stmt = stmt.where(Candle.date <= end)
            rows = session.execute(stmt).scalars().all()

        data = [
            {
                "date": row.date,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for row in rows
        ]
        return pd.DataFrame(data, columns=["date", "open", "high", "low", "close", "volume"])

    def list_symbols(self) -> list[str]:
        with self.session() as session:
            rows = session.execute(select(Candle.symbol).distinct().order_by(Candle.symbol)).all()
        return [row[0] for row in rows]

    def stats(self) -> dict:
        with self.session() as session:
            total = session.execute(select(func.count()).select_from(Candle)).scalar() or 0
            symbols = session.execute(select(func.count(func.distinct(Candle.symbol)))).scalar() or 0
            latest_date = session.execute(select(func.max(Candle.date))).scalar()
        return {
            "candles": int(total),
            "symbols": int(symbols),
            "latest_candle_date": latest_date.isoformat() if latest_date else None,
        }

    def latest_closes(self, symbols: list[str]) -> list[dict]:
        wanted = [symbol.upper() for symbol in symbols]
        if not wanted:
            return []
        with self.session() as session:
            latest_dates = (
                select(Candle.symbol, func.max(Candle.date).label("latest_date"))
                .where(Candle.symbol.in_(wanted))
                .group_by(Candle.symbol)
                .subquery()
            )
            rows = session.execute(
                select(Candle)
                .join(
                    latest_dates,
                    (Candle.symbol == latest_dates.c.symbol)
                    & (Candle.date == latest_dates.c.latest_date),
                )
                .order_by(Candle.symbol)
            ).scalars()
            return [
                {
                    "symbol": row.symbol,
                    "date": row.date.isoformat(),
                    "close": row.close,
                }
                for row in rows
            ]


class ScanRepository(BaseRepository):
    def save_scan(
        self,
        scan_date: date,
        candidates: list[dict],
        llm_report: dict | None,
        market_context: dict | None = None,
    ) -> int:
        with self.session() as session:
            session.execute(delete(ScanResult).where(ScanResult.scan_date == scan_date))
            for candidate in candidates:
                features = dict(candidate.get("features", {}))
                features["sector"] = candidate.get("sector")
                features["reasons"] = candidate.get("reasons", [])
                features["risk_flags"] = candidate.get("risk_flags", [])
                features["trade_plan"] = candidate.get("trade_plan", {})
                features["strategy_profile"] = candidate.get("strategy_profile", {})
                features["strategy_matches"] = candidate.get("strategy_matches", [])
                features["_market_context"] = market_context or {}
                session.add(
                    ScanResult(
                        scan_date=scan_date,
                        symbol=candidate["symbol"],
                        close=float(candidate["close"]),
                        breakout_level=float(candidate.get("breakout_level") or 0),
                        score=int(candidate["score"]),
                        verdict=candidate["verdict"],
                        features=features,
                        llm_report=llm_report,
                    )
                )
            session.commit()
        return len(candidates)

    def latest_scan(self) -> dict | None:
        with self.session() as session:
            latest_date = session.execute(
                select(ScanResult.scan_date).order_by(ScanResult.scan_date.desc()).limit(1)
            ).scalar_one_or_none()
            if latest_date is None:
                return None
            rows = session.execute(
                select(ScanResult)
                .where(ScanResult.scan_date == latest_date)
                .order_by(ScanResult.score.desc())
            ).scalars()

            candidates = []
            llm_report = None
            market_context = {}
            for row in rows:
                llm_report = row.llm_report or llm_report
                market_context = row.features.get("_market_context") or market_context
                candidates.append(
                    {
                        "symbol": row.symbol,
                        "sector": row.features.get("sector", "Other"),
                        "close": row.close,
                        "breakout_level": row.breakout_level,
                        "score": row.score,
                        "verdict": row.verdict,
                        "reasons": row.features.get("reasons", []),
                        "risk_flags": row.features.get("risk_flags", []),
                        "trade_plan": row.features.get("trade_plan", {}),
                        "strategy_profile": row.features.get("strategy_profile", {}),
                        "strategy_matches": row.features.get("strategy_matches", []),
                        "features": row.features,
                    }
                )
            return {
                "scan_date": latest_date.isoformat(),
                "market_context": market_context,
                "candidates": candidates,
                "llm_report": llm_report,
            }
