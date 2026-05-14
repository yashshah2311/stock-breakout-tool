import argparse
import sys
from datetime import date
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.data.historical_fetcher import fetch_and_store_history
from app.data.instruments import DEFAULT_NIFTY50_SYMBOLS
from app.db.repository import CandleRepository, ScanRepository
from app.llm.openai_client import AnalystLLM
from app.reports.daily_report import build_markdown_report
from app.scanner.signal_engine import SignalEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the stock scanner every market day evening.")
    parser.add_argument("--hour", type=int, default=18)
    parser.add_argument("--minute", type=int, default=15)
    parser.add_argument("--timezone", default="Asia/Kolkata")
    parser.add_argument("--fetch-latest", action="store_true")
    parser.add_argument("--use-openai", action="store_true")
    parser.add_argument("--min-score", type=int, default=60)
    return parser.parse_args()


def run_job(fetch_latest: bool, use_openai: bool, min_score: int) -> None:
    settings = get_settings()
    candle_repo = CandleRepository(settings.database_url)
    scan_repo = ScanRepository(settings.database_url)

    symbols = candle_repo.list_symbols() or DEFAULT_NIFTY50_SYMBOLS
    if fetch_latest:
        fetch_and_store_history(symbols=symbols, years=5, settings=settings)

    engine = SignalEngine(candle_repo, min_avg_traded_value=settings.min_avg_traded_value)
    scan_result = engine.scan(symbols=symbols, min_score=min_score)

    llm_report = None
    if use_openai:
        llm_report = AnalystLLM(settings).explain_scan(
            scan_date=scan_result["scan_date"],
            market_context=scan_result["market_context"],
            candidates=scan_result["candidates"][: settings.max_openai_candidates],
        )

    scan_repo.save_scan(
        scan_date=date.fromisoformat(scan_result["scan_date"]),
        candidates=scan_result["candidates"],
        llm_report=llm_report,
        market_context=scan_result.get("market_context"),
    )

    markdown = build_markdown_report(scan_result, llm_report)
    output = Path("reports") / f"daily_scan_{scan_result['scan_date']}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(f"[{scan_result['scan_date']}] candidates={len(scan_result['candidates'])} report={output}")


def main() -> None:
    args = parse_args()
    scheduler = BlockingScheduler(timezone=args.timezone)
    scheduler.add_job(
        run_job,
        CronTrigger(day_of_week="mon-fri", hour=args.hour, minute=args.minute),
        kwargs={
            "fetch_latest": args.fetch_latest,
            "use_openai": args.use_openai,
            "min_score": args.min_score,
        },
        id="daily_breakout_scan",
        replace_existing=True,
    )
    print(f"Daily scan scheduled at {args.hour:02d}:{args.minute:02d} {args.timezone}.")
    scheduler.start()


if __name__ == "__main__":
    main()
