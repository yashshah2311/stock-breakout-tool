from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd


CSV_COLUMNS = [
    "trade_id",
    "created_at",
    "symbol",
    "side",
    "quantity",
    "entry_price",
    "stop_loss",
    "target_1",
    "target_2",
    "strategy",
    "prediction_bias",
    "prediction_confidence",
    "thesis",
    "status",
    "exit_price",
    "exit_at",
    "exit_reason",
]


@dataclass(frozen=True)
class PortfolioSnapshot:
    summary: dict
    open_positions: list[dict]
    closed_positions: list[dict]


class PaperTradeRepository:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self) -> None:
        if self.csv_path.exists():
            return
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()

    def _load_df(self) -> pd.DataFrame:
        self._ensure_file()
        df = pd.read_csv(self.csv_path)
        if df.empty:
            return pd.DataFrame(columns=CSV_COLUMNS)
        return df.fillna("")

    def _save_df(self, df: pd.DataFrame) -> None:
        ordered = df.reindex(columns=CSV_COLUMNS)
        ordered.to_csv(self.csv_path, index=False)

    def create_trade(
        self,
        *,
        symbol: str,
        side: str,
        quantity: int,
        entry_price: float,
        stop_loss: float,
        target_1: float,
        target_2: float,
        strategy: str,
        prediction_bias: str,
        prediction_confidence: str,
        thesis: str,
    ) -> dict:
        df = self._load_df()
        trade = {
            "trade_id": uuid4().hex[:10],
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "symbol": symbol.upper(),
            "side": side.upper(),
            "quantity": int(quantity),
            "entry_price": round(float(entry_price), 2),
            "stop_loss": round(float(stop_loss), 2),
            "target_1": round(float(target_1), 2),
            "target_2": round(float(target_2), 2),
            "strategy": strategy,
            "prediction_bias": prediction_bias,
            "prediction_confidence": prediction_confidence,
            "thesis": thesis,
            "status": "OPEN",
            "exit_price": "",
            "exit_at": "",
            "exit_reason": "",
        }
        df = pd.concat([df, pd.DataFrame([trade])], ignore_index=True)
        self._save_df(df)
        return trade

    def close_trade(self, trade_id: str, exit_price: float, exit_reason: str = "") -> dict:
        df = self._load_df()
        mask = df["trade_id"].astype(str) == str(trade_id)
        if not mask.any():
            raise KeyError(f"Trade {trade_id} not found.")
        idx = df.index[mask][0]
        df.at[idx, "status"] = "CLOSED"
        df.at[idx, "exit_price"] = round(float(exit_price), 2)
        df.at[idx, "exit_at"] = datetime.now().isoformat(timespec="seconds")
        df.at[idx, "exit_reason"] = exit_reason
        self._save_df(df)
        return self._row_to_trade(df.loc[idx].to_dict())

    def list_trades(self) -> list[dict]:
        df = self._load_df()
        if df.empty:
            return []
        trades = [self._row_to_trade(row) for row in df.to_dict("records")]
        trades.sort(key=lambda item: item["created_at"], reverse=True)
        return trades

    def portfolio(self, latest_prices: dict[str, float] | None = None) -> PortfolioSnapshot:
        latest_prices = latest_prices or {}
        trades = self.list_trades()
        open_positions = [self._enrich_trade(item, latest_prices) for item in trades if item["status"] == "OPEN"]
        closed_positions = [self._enrich_trade(item, latest_prices) for item in trades if item["status"] == "CLOSED"]

        realized = round(sum(item.get("realized_pnl", 0.0) for item in closed_positions), 2)
        unrealized = round(sum(item.get("unrealized_pnl", 0.0) for item in open_positions), 2)
        wins = sum(1 for item in closed_positions if item.get("realized_pnl", 0.0) > 0)
        losses = sum(1 for item in closed_positions if item.get("realized_pnl", 0.0) < 0)
        closed_count = len(closed_positions)

        summary = {
            "open_positions": len(open_positions),
            "closed_positions": closed_count,
            "wins": wins,
            "losses": losses,
            "win_rate": round((wins / closed_count) * 100, 1) if closed_count else 0.0,
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "net_pnl": round(realized + unrealized, 2),
            "gross_exposure": round(sum(item["entry_price"] * item["quantity"] for item in open_positions), 2),
        }
        return PortfolioSnapshot(summary=summary, open_positions=open_positions, closed_positions=closed_positions)

    @staticmethod
    def _row_to_trade(row: dict) -> dict:
        trade = dict(row)
        numeric_fields = ["quantity", "entry_price", "stop_loss", "target_1", "target_2", "exit_price"]
        for field in numeric_fields:
            value = trade.get(field, "")
            if value in {"", None}:
                trade[field] = None if field != "quantity" else 0
            elif field == "quantity":
                trade[field] = int(float(value))
            else:
                trade[field] = round(float(value), 2)
        trade["status"] = str(trade.get("status") or "OPEN").upper()
        trade["side"] = str(trade.get("side") or "BUY").upper()
        return trade

    @staticmethod
    def _enrich_trade(trade: dict, latest_prices: dict[str, float]) -> dict:
        result = dict(trade)
        qty = int(result.get("quantity") or 0)
        entry = float(result.get("entry_price") or 0)
        side = result.get("side", "BUY")
        current_price = None
        if result["status"] == "OPEN":
            current_price = latest_prices.get(result["symbol"])
        elif result.get("exit_price") is not None:
            current_price = float(result["exit_price"])

        pnl = 0.0
        if current_price is not None:
            if side == "SELL":
                pnl = (entry - float(current_price)) * qty
            else:
                pnl = (float(current_price) - entry) * qty

        result["current_price"] = round(float(current_price), 2) if current_price is not None else None
        result["unrealized_pnl"] = round(pnl, 2) if result["status"] == "OPEN" else 0.0
        result["realized_pnl"] = round(pnl, 2) if result["status"] == "CLOSED" else 0.0
        result["return_pct"] = round((pnl / (entry * qty)) * 100, 2) if entry and qty else 0.0
        return result
