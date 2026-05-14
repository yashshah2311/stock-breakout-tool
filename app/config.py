from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    data_provider: str = Field(default="yahoo", alias="DATA_PROVIDER")

    kite_api_key: str | None = Field(default=None, alias="KITE_API_KEY")
    kite_api_secret: str | None = Field(default=None, alias="KITE_API_SECRET")
    kite_access_token: str | None = Field(default=None, alias="KITE_ACCESS_TOKEN")
    kite_exchange: str = Field(default="NSE", alias="KITE_EXCHANGE")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    database_url: str = Field(default="sqlite:///./data/stock_breakout.sqlite3", alias="DATABASE_URL")
    paper_trades_csv: str = Field(default="./data/paper_trades.csv", alias="PAPER_TRADES_CSV")
    min_avg_traded_value: float = Field(default=50_000_000, alias="MIN_AVG_TRADED_VALUE")
    max_openai_candidates: int = Field(default=12, alias="MAX_OPENAI_CANDIDATES")
    app_env: str = Field(default="local", alias="APP_ENV")

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.database_url.startswith("sqlite:///./"):
        relative_path = settings.database_url.replace("sqlite:///./", "", 1)
        absolute_path = settings.project_root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        settings.database_url = f"sqlite:///{absolute_path.as_posix()}"
    if settings.paper_trades_csv.startswith("./"):
        absolute_csv = settings.project_root / settings.paper_trades_csv[2:]
        absolute_csv.parent.mkdir(parents=True, exist_ok=True)
        settings.paper_trades_csv = str(absolute_csv)
    return settings
