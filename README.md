# Stock Breakout Tool

A data-driven stock scanner for Indian equities. It can use free Yahoo Finance/yfinance data by default, or Zerodha/Kite for broker-grade historical/live data. Python rules do breakout detection, and the OpenAI Responses API can produce concise analyst-style explanations.

This is a scanner, not a prediction engine. It generates probability-based watchlists from computed features and never promises profit.

## What It Does

- Fetches NSE daily OHLCV candles through free Yahoo Finance/yfinance by default.
- Can fetch recent free intraday candles through yfinance for research.
- Still supports Zerodha Kite Connect if you set `DATA_PROVIDER=zerodha`.
- Stores candles in local SQLite.
- Computes trend, volume, candle, breakout, volatility, liquidity, and risk features.
- Scores candidates from 0 to 100.
- Sends only compact feature summaries to OpenAI, not raw 5-year candle dumps.
- Produces a daily watchlist, near-breakout list, avoid list, and market note.
- Serves a built-in dashboard at `/`.
- Can run manually or on a weekday evening scheduler.

## Quick Start

Use Python 3.11 or newer.

```powershell
cd C:\react\stock-breakout-tool
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your Zerodha and OpenAI keys.

For free data mode, keep:

```text
DATA_PROVIDER=yahoo
```

Free Yahoo/yfinance intraday data is not broker-grade live tick data. It is suitable for research and dashboards, but can be delayed, rate-limited, or occasionally missing.

Zerodha live mode needs both:

```text
KITE_API_KEY=...
KITE_API_SECRET=...
KITE_ACCESS_TOKEN=...
```

`KITE_ACCESS_TOKEN` is a daily token. Generate a fresh one after Zerodha login whenever it expires.

To generate it from the app:

1. Put `KITE_API_KEY` and `KITE_API_SECRET` in `.env`.
2. Restart the app.
3. Open `http://127.0.0.1:8000/kite/login`.
4. Log in to Zerodha.
5. Copy the generated `KITE_ACCESS_TOKEN` into `.env`.
6. Restart the app again.

Initialize the database:

```powershell
python scripts\init_db.py
```

Sync Zerodha instruments:

```powershell
python scripts\sync_instruments.py
```

Fetch five years of daily candles for the default Nifty 50 universe:

```powershell
python scripts\fetch_history.py --years 5
```

Run the daily scan:

```powershell
python scripts\run_daily_scan.py --use-openai
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`

## Free Deploy On Render

This repo includes `render.yaml`, so Render can create the free web service from the blueprint.

1. Push this folder to a GitHub repository.
2. Open [Render](https://render.com/), create an account, and choose **New > Blueprint**.
3. Connect your GitHub repository.
4. Select the detected `render.yaml`.
5. Create the service.

Render will use:

```text
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Default production env values in `render.yaml`:

```text
APP_ENV=production
DATA_PROVIDER=yahoo
DATABASE_URL=sqlite:////tmp/stock_breakout.sqlite3
PAPER_TRADES_CSV=/tmp/paper_trades.csv
```

Notes:

- Render free services can sleep after inactivity, so the first request may be slow.
- `/tmp` storage is ephemeral. Scan results and paper trades can reset after deploys/restarts.
- For a serious public version, move `DATABASE_URL` to a persistent Postgres database.
- Keep `OPENAI_API_KEY`, Zerodha keys, and other secrets out of Git. Add them only in Render's Environment settings.

For a local demo without live Zerodha data:

```powershell
python scripts\seed_sample_data.py
python scripts\run_daily_scan.py
uvicorn app.main:app --reload
```

Schedule the scanner for weekdays at 6:15 PM IST:

```powershell
python scripts\schedule_daily_scan.py --fetch-latest --use-openai
```

## Main API Endpoints

- `GET /health`
- `GET /status`
- `GET /symbols`
- `GET /universe/default`
- `POST /quotes/live`
- `POST /scan`
- `GET /results/latest`
- `GET /reports/latest`
- `POST /instruments/sync`
- `POST /candles/fetch`

## Scoring Model

- Trend strength: 20
- Volume confirmation: 20
- Breakout quality: 25
- Candle pattern: 10
- Relative strength: 15
- Risk quality: 10

General interpretation:

- `80+`: strong watchlist
- `65-79`: possible breakout
- below `65`: ignore unless it is very close to resistance and improving

## Important Trading Notes

- Use this as a research assistant, not financial advice.
- Backtest before live use.
- Avoid illiquid stocks, oversized gap-ups, and extended moves far above the 20 EMA.
- One candle pattern alone should never trigger a trade.
- Market and sector context matter.

## Folder Structure

```text
app/
  api/
  data/
  indicators/
  scanner/
  llm/
  reports/
  db/
backtests/
notebooks/
scripts/
tests/
```
