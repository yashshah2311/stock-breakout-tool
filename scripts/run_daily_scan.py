import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.repository import CandleRepository, ScanRepository
from app.llm.openai_client import AnalystLLM
from app.reports.daily_report import build_markdown_report
from app.scanner.signal_engine import SignalEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run daily breakout scan.")
    parser.add_argument("--symbols", nargs="*", default=None)
    parser.add_argument("--min-score", type=int, default=60)
    parser.add_argument("--use-openai", action="store_true")
    parser.add_argument("--out", default=None, help="Optional markdown output file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    candle_repo = CandleRepository(settings.database_url)
    scan_repo = ScanRepository(settings.database_url)

    symbols = args.symbols or candle_repo.list_symbols()
    if not symbols:
        raise SystemExit("No stored candles found. Run scripts/fetch_history.py first.")

    engine = SignalEngine(candle_repo, min_avg_traded_value=settings.min_avg_traded_value)
    scan_result = engine.scan(symbols=symbols, min_score=args.min_score)

    llm_report = None
    if args.use_openai:
        llm_report = AnalystLLM(settings).explain_scan(
            scan_date=scan_result["scan_date"],
            market_context=scan_result["market_context"],
            candidates=scan_result["candidates"][: settings.max_openai_candidates],
        )
        scan_result["llm_report"] = llm_report

    scan_repo.save_scan(
        scan_date=date.fromisoformat(scan_result["scan_date"]),
        candidates=scan_result["candidates"],
        llm_report=llm_report,
        market_context=scan_result.get("market_context"),
    )

    markdown = build_markdown_report(scan_result, llm_report)
    output = Path(args.out) if args.out else Path("reports") / f"daily_scan_{scan_result['scan_date']}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    print(f"Candidates: {len(scan_result['candidates'])}")
    print(f"Report written: {output}")


if __name__ == "__main__":
    main()
