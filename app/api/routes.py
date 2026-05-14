from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.data.fundamentals import FundamentalsClient
from app.data.historical_fetcher import fetch_and_store_history
from app.data.instruments import DEFAULT_NIFTY50_SYMBOLS, DEFAULT_NIFTY100_SYMBOLS, sector_for_symbol
from app.data.yahoo_client import YahooFinanceClient
from app.data.zerodha_client import ZerodhaClient
from app.db.repository import CandleRepository, InstrumentRepository, ScanRepository
from app.llm.openai_client import AnalystLLM
from app.paper.paper_trade_repository import PaperTradeRepository
from app.reports.daily_report import build_markdown_report
from app.scanner.backtest import BacktestConfig, backtest_strategy
from app.scanner.signal_engine import SignalEngine
from app.scanner.strategy_engine import strategy_catalog

router = APIRouter()


def _usable_openai_key(key: str | None) -> bool:
    if not key:
        return False
    normalized = key.strip()
    return not normalized.startswith("your_")


def _is_nse_market_open_now() -> bool:
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    if now.weekday() >= 5:
        return False
    return time(9, 15) <= now.time() <= time(15, 30)


class ScanRequest(BaseModel):
    symbols: list[str] | None = None
    universe: str = "nifty100"
    use_openai: bool = True
    fetch_latest: bool = True
    min_score: int = Field(default=0, ge=0, le=100)


class FetchCandlesRequest(BaseModel):
    symbols: list[str] | None = None
    years: int = Field(default=5, ge=1, le=10)


class LiveQuotesRequest(BaseModel):
    symbols: list[str] | None = None


class IntradayCandlesRequest(BaseModel):
    symbols: list[str] | None = None
    period: str = "1d"
    interval: str = "5m"


class BacktestRequest(BaseModel):
    strategy_id: str = "momentum_strategy"
    symbols: list[str] | None = None
    universe: str = "nifty100"
    horizon_days: int = Field(default=10, ge=2, le=30)
    min_score: int = Field(default=55, ge=0, le=100)
    lookback_days: int = Field(default=320, ge=260, le=1300)
    step_days: int = Field(default=15, ge=1, le=30)
    max_symbols: int = Field(default=20, ge=1, le=100)


class PaperTradeCreateRequest(BaseModel):
    symbol: str
    side: str = "BUY"
    quantity: int = Field(default=1, ge=1, le=100000)
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    target_1: float = Field(gt=0)
    target_2: float = Field(gt=0)
    strategy: str = "Manual"
    prediction_bias: str = "watch"
    prediction_confidence: str = "low"
    thesis: str = ""


class PaperTradeCloseRequest(BaseModel):
    exit_price: float = Field(gt=0)
    exit_reason: str = ""


def _candidate_for_symbol(symbol: str, latest_scan: dict | None) -> dict | None:
    if not latest_scan:
        return None
    symbol = symbol.upper()
    for candidate in latest_scan.get("candidates", []):
        if candidate.get("symbol") == symbol:
            return candidate
    return None


def _build_latest_from_stored_candles(settings) -> dict | None:
    candle_repo = CandleRepository(settings.database_url)
    stored_symbols = set(candle_repo.list_symbols())
    if not stored_symbols:
        return None

    scan_repo = ScanRepository(settings.database_url)
    engine = SignalEngine(
        candle_repo=candle_repo,
        min_avg_traded_value=settings.min_avg_traded_value,
    )
    scan_result = engine.scan(symbols=DEFAULT_NIFTY100_SYMBOLS, min_score=0)
    scan_result["llm_report"] = None
    scan_result["auto_built_from_stored_candles"] = True
    try:
        scan_repo.save_scan(
            scan_date=date.fromisoformat(scan_result["scan_date"]),
            candidates=scan_result["candidates"],
            llm_report=None,
            market_context=scan_result.get("market_context"),
        )
    except Exception as exc:
        scan_result["persistence_warning"] = str(exc)
    return scan_result


@router.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    settings = get_settings()
    return FileResponse(settings.project_root / "app" / "static" / "index.html")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/status")
def status() -> dict:
    settings = get_settings()
    candle_repo = CandleRepository(settings.database_url)
    instrument_repo = InstrumentRepository(settings.database_url)
    paper_repo = PaperTradeRepository(Path(settings.paper_trades_csv))
    candle_stats = candle_repo.stats()
    missing_credentials = []
    if not settings.kite_api_key:
        missing_credentials.append("KITE_API_KEY")
    if not settings.kite_access_token:
        missing_credentials.append("KITE_ACCESS_TOKEN")
    return {
        "app": "stock-breakout-tool",
        "environment": settings.app_env,
        "data_provider": settings.data_provider,
        "database_url": settings.database_url,
        "zerodha_configured": bool(settings.kite_api_key and settings.kite_access_token),
        "zerodha_token_generation_ready": bool(settings.kite_api_key and settings.kite_api_secret),
        "missing_zerodha_credentials": missing_credentials,
        "openai_configured": _usable_openai_key(settings.openai_api_key),
        "openai_model": settings.openai_model,
        "instrument_count": instrument_repo.count(),
        "paper_trades_count": len(paper_repo.list_trades()),
        "candle_stats": candle_stats,
        "available_symbols": candle_repo.list_symbols(),
    }


@router.get("/symbols")
def symbols() -> dict[str, list[str]]:
    settings = get_settings()
    repo = CandleRepository(settings.database_url)
    return {"symbols": repo.list_symbols()}


@router.get("/universe/default")
def default_universe() -> dict[str, list[str]]:
    return {"nifty50": DEFAULT_NIFTY50_SYMBOLS, "nifty100": DEFAULT_NIFTY100_SYMBOLS}


@router.get("/sectors")
def sectors() -> dict:
    by_sector: dict[str, list[str]] = {}
    for symbol in DEFAULT_NIFTY100_SYMBOLS:
        by_sector.setdefault(sector_for_symbol(symbol), []).append(symbol)
    return {
        "sectors": [
            {"sector": sector, "symbols": symbols, "count": len(symbols)}
            for sector, symbols in sorted(by_sector.items())
        ]
    }


@router.get("/strategies")
def strategies() -> dict:
    catalog = strategy_catalog()
    return {
        "strategies": catalog,
        "note": (
            "Active tabs are classified from Nifty 100 OHLCV and fundamentals. "
            "External/needs_backtest tabs are shown for roadmap clarity and are not traded as signals yet."
        ),
    }


@router.post("/strategies/backtest")
def strategy_backtest(payload: BacktestRequest) -> dict:
    settings = get_settings()
    candle_repo = CandleRepository(settings.database_url)
    default_universe_symbols = DEFAULT_NIFTY100_SYMBOLS if payload.universe.lower() == "nifty100" else DEFAULT_NIFTY50_SYMBOLS
    symbols = payload.symbols or default_universe_symbols
    symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()][: payload.max_symbols]
    candles_by_symbol = {symbol: candle_repo.load_candles(symbol) for symbol in symbols}
    return backtest_strategy(
        candles_by_symbol=candles_by_symbol,
        config=BacktestConfig(
            strategy_id=payload.strategy_id,
            horizon_days=payload.horizon_days,
            min_score=payload.min_score,
            lookback_days=payload.lookback_days,
            step_days=payload.step_days,
        ),
        min_avg_traded_value=settings.min_avg_traded_value,
    )


@router.get("/kite/login", include_in_schema=False)
def kite_login() -> RedirectResponse:
    settings = get_settings()
    if not settings.kite_api_key:
        raise HTTPException(status_code=400, detail="KITE_API_KEY is required in .env.")
    return RedirectResponse(ZerodhaClient(settings).login_url())


@router.get("/kite/callback", include_in_schema=False)
def kite_callback(request_token: str | None = None, status: str | None = None) -> HTMLResponse:
    settings = get_settings()
    if status and status != "success":
        return HTMLResponse(f"<h1>Kite login failed</h1><p>Status: {status}</p>", status_code=400)
    if not request_token:
        return HTMLResponse("<h1>Missing request_token</h1><p>Kite did not return a request_token.</p>", status_code=400)
    try:
        data = ZerodhaClient(settings).generate_access_token(request_token)
    except Exception as exc:
        return HTMLResponse(
            f"""
            <h1>Could not generate access token</h1>
            <p>{exc}</p>
            <p>Check that KITE_API_KEY and KITE_API_SECRET in .env belong to the same Kite Connect app.</p>
            """,
            status_code=502,
        )

    token = data.get("access_token") or ""
    return HTMLResponse(
        f"""
        <!doctype html>
        <html>
          <head>
            <title>Kite access token</title>
            <style>
              body {{ font-family: system-ui, sans-serif; margin: 40px; max-width: 900px; }}
              code, pre {{ background: #f3f5f7; padding: 12px; border-radius: 6px; display: block; }}
              .warn {{ color: #9a3412; font-weight: 700; }}
            </style>
          </head>
          <body>
            <h1>Kite access token generated</h1>
            <p class="warn">Keep this private. It is valid for your Kite session/trading day.</p>
            <p>User: {data.get("user_id") or ""} {data.get("user_name") or ""}</p>
            <p>Put this in <code>C:\\react\\stock-breakout-tool\\.env</code>:</p>
            <pre>KITE_ACCESS_TOKEN={token}</pre>
            <p>Then restart the Stock Breakout Tool app.</p>
          </body>
        </html>
        """
    )


@router.post("/quotes/live")
def live_quotes(payload: LiveQuotesRequest) -> dict:
    settings = get_settings()
    candle_repo = CandleRepository(settings.database_url)
    symbols = payload.symbols or sorted(set(DEFAULT_NIFTY100_SYMBOLS + candle_repo.list_symbols()))
    symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]

    if settings.data_provider.lower() == "yahoo":
        client = YahooFinanceClient()
        quotes = client.latest_quotes(symbols)
        latest_by_symbol = {
            row["symbol"]: row
            for row in candle_repo.latest_closes(symbols)
        }
        for quote in quotes:
            if quote.get("last_price") is not None:
                quote["source"] = "yahoo_intraday"
                continue
            fallback = latest_by_symbol.get(quote["symbol"])
            if fallback:
                quote["last_price"] = round(float(fallback["close"]), 2)
                quote["last_time"] = fallback["date"]
                quote["source"] = "stored_daily_fallback"
            else:
                quote["source"] = "unavailable"
        priced = sum(1 for quote in quotes if quote.get("last_price") is not None)
        return {
            "mode": "free_delayed",
            "provider": "yahoo",
            "note": (
                f"Loaded {priced}/{len(quotes)} prices from Yahoo/yfinance. "
                "Missing intraday ticks fall back to the latest stored daily close."
            ),
            "market_open": _is_nse_market_open_now(),
            "quotes": quotes,
        }

    if not settings.kite_api_key or not settings.kite_access_token:
        raise HTTPException(
            status_code=400,
            detail="Live Zerodha mode needs KITE_API_KEY and today's KITE_ACCESS_TOKEN in .env.",
        )

    exchange_symbols = [f"{settings.kite_exchange}:{symbol}" for symbol in symbols]

    try:
        raw_quotes = ZerodhaClient(settings).quote_ltp_many(exchange_symbols)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Zerodha live quote request failed: {exc}") from exc

    quotes = []
    for symbol, exchange_symbol in zip(symbols, exchange_symbols, strict=True):
        quotes.append(
            {
                "symbol": symbol,
                "exchange_symbol": exchange_symbol,
                "last_price": raw_quotes.get(exchange_symbol),
            }
        )
    return {"mode": "live", "exchange": settings.kite_exchange, "quotes": quotes}


@router.post("/candles/intraday")
def intraday_candles(payload: IntradayCandlesRequest) -> dict:
    settings = get_settings()
    candle_repo = CandleRepository(settings.database_url)
    symbols = payload.symbols or candle_repo.list_symbols() or DEFAULT_NIFTY50_SYMBOLS[:5]
    symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]

    if settings.data_provider.lower() != "yahoo":
        raise HTTPException(status_code=400, detail="Intraday free candles are available with DATA_PROVIDER=yahoo.")

    client = YahooFinanceClient()
    result = []
    failed = []
    for symbol in symbols[:25]:
        try:
            df = client.intraday(symbol=symbol, period=payload.period, interval=payload.interval)
        except Exception:
            failed.append(symbol)
            continue
        result.append(
            {
                "symbol": symbol,
                "provider_symbol": client.yahoo_symbol(symbol),
                "candles": [
                    {
                        "date": str(row["date"]),
                        "open": round(float(row["open"]), 2),
                        "high": round(float(row["high"]), 2),
                        "low": round(float(row["low"]), 2),
                        "close": round(float(row["close"]), 2),
                        "volume": int(row["volume"]),
                    }
                    for row in df.tail(80).to_dict("records")
                ],
            }
        )
    return {
        "provider": "yahoo",
        "mode": "free_delayed_intraday",
        "period": payload.period,
        "interval": payload.interval,
        "results": result,
        "failed": failed,
    }


@router.get("/stocks/{symbol}/chart")
def stock_chart(symbol: str, period: str = "1d", interval: str = "5m") -> dict:
    settings = get_settings()
    symbol = symbol.strip().upper()
    candle_repo = CandleRepository(settings.database_url)
    scan_repo = ScanRepository(settings.database_url)
    latest_scan = scan_repo.latest_scan()
    candidate = _candidate_for_symbol(symbol, latest_scan)

    candles = []
    mode = "stored_daily"
    provider = settings.data_provider
    if settings.data_provider.lower() == "yahoo":
        try:
            df = YahooFinanceClient().intraday(symbol=symbol, period=period, interval=interval)
        except Exception:
            df = None
        if df is not None and not df.empty:
            mode = "free_delayed_intraday"
            candles = [
                {
                    "date": str(row["date"]),
                    "open": round(float(row["open"]), 2),
                    "high": round(float(row["high"]), 2),
                    "low": round(float(row["low"]), 2),
                    "close": round(float(row["close"]), 2),
                    "volume": int(row["volume"]),
                }
                for row in df.tail(160).to_dict("records")
            ]

    if not candles:
        stored = candle_repo.load_candles(symbol)
        candles = [
            {
                "date": str(row["date"]),
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]),
            }
            for row in stored.tail(160).to_dict("records")
        ]

    if not candles:
        raise HTTPException(status_code=404, detail=f"No candle data available for {symbol}.")

    return {
        "symbol": symbol,
        "provider": provider,
        "mode": mode,
        "period": period,
        "interval": interval,
        "candles": candles,
        "candidate": candidate,
        "market_hours_note": "Yahoo/yfinance intraday data may be delayed. Broker-grade live pricing needs Zerodha live quotes.",
    }


@router.get("/stocks/{symbol}/fundamentals")
def stock_fundamentals(symbol: str) -> dict:
    symbol = symbol.strip().upper()
    try:
        fundamentals = FundamentalsClient().fundamentals(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Fundamentals request failed: {exc}") from exc
    return fundamentals


@router.get("/stocks/{symbol}/news")
def stock_news(symbol: str, limit: int = 8) -> dict:
    symbol = symbol.strip().upper()
    try:
        return YahooFinanceClient().latest_news(symbol, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"News request failed: {exc}") from exc


@router.post("/instruments/sync")
def sync_instruments() -> dict[str, int]:
    settings = get_settings()
    client = ZerodhaClient(settings)
    instruments = client.fetch_instruments(settings.kite_exchange)
    repo = InstrumentRepository(settings.database_url)
    count = repo.upsert_many(instruments)
    return {"stored": count}


@router.post("/candles/fetch")
def fetch_candles(payload: FetchCandlesRequest) -> dict[str, int | list[str]]:
    settings = get_settings()
    symbols = payload.symbols or DEFAULT_NIFTY50_SYMBOLS
    try:
        result = fetch_and_store_history(symbols=symbols, years=payload.years, settings=settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/scan")
def scan(payload: ScanRequest) -> dict:
    settings = get_settings()
    candle_repo = CandleRepository(settings.database_url)
    scan_repo = ScanRepository(settings.database_url)

    default_universe_symbols = DEFAULT_NIFTY100_SYMBOLS if payload.universe.lower() == "nifty100" else DEFAULT_NIFTY50_SYMBOLS
    symbols = payload.symbols or default_universe_symbols
    if not symbols:
        raise HTTPException(
            status_code=400,
            detail="No symbols requested and no candles are stored. Fetch history first.",
        )

    fetch_result = None
    if payload.fetch_latest:
        try:
            fetch_result = fetch_and_store_history(symbols=symbols, years=5, settings=settings)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    engine = SignalEngine(
        candle_repo=candle_repo,
        min_avg_traded_value=settings.min_avg_traded_value,
    )
    scan_result = engine.scan(symbols=symbols, min_score=payload.min_score)
    scan_result["fetch_result"] = fetch_result

    llm_report = None
    if payload.use_openai:
        llm = AnalystLLM(settings)
        llm_report = llm.explain_scan(
            scan_date=scan_result["scan_date"],
            market_context=scan_result["market_context"],
            candidates=scan_result["candidates"][: settings.max_openai_candidates],
        )
        scan_result["llm_report"] = llm_report

    try:
        scan_repo.save_scan(
            scan_date=date.fromisoformat(scan_result["scan_date"]),
            candidates=scan_result["candidates"],
            llm_report=llm_report,
            market_context=scan_result.get("market_context"),
        )
    except Exception as exc:
        scan_result["persistence_warning"] = str(exc)
    scan_result["markdown_report"] = build_markdown_report(scan_result, llm_report)
    return scan_result


@router.get("/results/latest")
def latest_results() -> dict:
    settings = get_settings()
    repo = ScanRepository(settings.database_url)
    latest = repo.latest_scan()
    if latest is None:
        latest = _build_latest_from_stored_candles(settings)
    if latest is None:
        raise HTTPException(status_code=404, detail="No scan results found. Run a scan after candles are loaded.")
    return latest


@router.get("/paper-trades")
def paper_trades() -> dict:
    settings = get_settings()
    repo = PaperTradeRepository(Path(settings.paper_trades_csv))
    return {"trades": repo.list_trades()}


@router.post("/paper-trades")
def create_paper_trade(payload: PaperTradeCreateRequest) -> dict:
    settings = get_settings()
    repo = PaperTradeRepository(Path(settings.paper_trades_csv))
    trade = repo.create_trade(
        symbol=payload.symbol,
        side=payload.side,
        quantity=payload.quantity,
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
        target_1=payload.target_1,
        target_2=payload.target_2,
        strategy=payload.strategy,
        prediction_bias=payload.prediction_bias,
        prediction_confidence=payload.prediction_confidence,
        thesis=payload.thesis,
    )
    return {"trade": trade}


@router.post("/paper-trades/{trade_id}/close")
def close_paper_trade(trade_id: str, payload: PaperTradeCloseRequest) -> dict:
    settings = get_settings()
    repo = PaperTradeRepository(Path(settings.paper_trades_csv))
    try:
        trade = repo.close_trade(trade_id=trade_id, exit_price=payload.exit_price, exit_reason=payload.exit_reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"trade": trade}


@router.get("/portfolio")
def portfolio() -> dict:
    settings = get_settings()
    repo = PaperTradeRepository(Path(settings.paper_trades_csv))
    trades = repo.list_trades()
    symbols = sorted({trade["symbol"] for trade in trades if trade["status"] == "OPEN"})
    latest_prices: dict[str, float] = {}
    if symbols and settings.data_provider.lower() == "yahoo":
        for quote in YahooFinanceClient().latest_quotes(symbols[:25]):
            if quote.get("last_price") is not None:
                latest_prices[quote["symbol"]] = float(quote["last_price"])
    snapshot = repo.portfolio(latest_prices=latest_prices)
    return {
        "summary": snapshot.summary,
        "open_positions": snapshot.open_positions,
        "closed_positions": snapshot.closed_positions,
    }


@router.get("/reports/latest", response_class=PlainTextResponse)
def latest_report() -> str:
    settings = get_settings()
    repo = ScanRepository(settings.database_url)
    latest = repo.latest_scan()
    if latest is None:
        latest = _build_latest_from_stored_candles(settings)
    if latest is None:
        raise HTTPException(status_code=404, detail="No scan results found. Run a scan after candles are loaded.")
    return build_markdown_report(latest, latest.get("llm_report"))
