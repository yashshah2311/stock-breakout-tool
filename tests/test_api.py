from fastapi.testclient import TestClient


def test_dashboard_and_status(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from app.config import get_settings
    from app.db.repository import get_engine
    from app.main import create_app

    get_settings.cache_clear()
    get_engine.cache_clear()
    client = TestClient(create_app())

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "MarketLens Breakout Workstation" in dashboard.text

    status = client.get("/status")
    assert status.status_code == 200
    body = status.json()
    assert body["app"] == "stock-breakout-tool"
    assert body["candle_stats"]["candles"] == 0

    get_settings.cache_clear()
    get_engine.cache_clear()
