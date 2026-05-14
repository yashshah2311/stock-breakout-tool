from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_token: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    tradingsymbol: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exchange: Mapped[str] = mapped_column(String(16), default="NSE")
    segment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    instrument_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tick_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_candle_symbol_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_token: Mapped[int] = mapped_column(Integer, index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_date: Mapped[date] = mapped_column(Date, index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    close: Mapped[float] = mapped_column(Float)
    breakout_level: Mapped[float] = mapped_column(Float)
    score: Mapped[int] = mapped_column(Integer)
    verdict: Mapped[str] = mapped_column(String(64))
    features: Mapped[dict] = mapped_column(JSON)
    llm_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
