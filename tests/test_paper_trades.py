from pathlib import Path

from app.paper.paper_trade_repository import PaperTradeRepository


def test_create_and_close_paper_trade(tmp_path: Path) -> None:
    repo = PaperTradeRepository(tmp_path / "paper_trades.csv")

    trade = repo.create_trade(
        symbol="RELIANCE",
        side="BUY",
        quantity=10,
        entry_price=2500,
        stop_loss=2440,
        target_1=2580,
        target_2=2620,
        strategy="Breakout Momentum",
        prediction_bias="bullish",
        prediction_confidence="medium",
        thesis="Test trade",
    )

    snapshot = repo.portfolio(latest_prices={"RELIANCE": 2550})
    assert snapshot.summary["open_positions"] == 1
    assert snapshot.open_positions[0]["unrealized_pnl"] == 500.0

    closed = repo.close_trade(trade["trade_id"], exit_price=2575, exit_reason="Target")
    assert closed["status"] == "CLOSED"

    snapshot = repo.portfolio(latest_prices={"RELIANCE": 2575})
    assert snapshot.summary["closed_positions"] == 1
    assert snapshot.summary["realized_pnl"] == 750.0
