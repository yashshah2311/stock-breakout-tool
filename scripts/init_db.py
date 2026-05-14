import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.db.repository import init_db


def main() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    print(f"Database ready: {settings.database_url}")


if __name__ == "__main__":
    main()
