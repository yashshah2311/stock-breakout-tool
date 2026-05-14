import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.data.historical_fetcher import fetch_and_store_history
from app.data.instruments import DEFAULT_NIFTY50_SYMBOLS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Zerodha daily candles into SQLite.")
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--symbols", nargs="*", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    symbols = args.symbols or DEFAULT_NIFTY50_SYMBOLS
    result = fetch_and_store_history(symbols=symbols, years=args.years, settings=settings)
    print(result)


if __name__ == "__main__":
    main()
