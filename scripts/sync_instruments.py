import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.data.zerodha_client import ZerodhaClient
from app.db.repository import InstrumentRepository


def main() -> None:
    settings = get_settings()
    client = ZerodhaClient(settings)
    instruments = client.fetch_instruments(settings.kite_exchange)
    repo = InstrumentRepository(settings.database_url)
    count = repo.upsert_many(instruments)
    print(f"Stored {count} instruments.")


if __name__ == "__main__":
    main()
