from __future__ import annotations

from datetime import date

import pandas as pd

from app.data.instruments import sector_for_symbol
from app.db.repository import CandleRepository
from app.scanner.feature_builder import build_features
from app.scanner.scoring import score_features
from app.scanner.strategy_engine import build_strategy_profile, match_strategy_families
from app.scanner.trade_plan import build_trade_plan


class SignalEngine:
    def __init__(self, candle_repo: CandleRepository, min_avg_traded_value: float):
        self.candle_repo = candle_repo
        self.min_avg_traded_value = min_avg_traded_value

    def scan(self, symbols: list[str], min_score: int = 0) -> dict:
        raw_features = []
        skipped = []

        for symbol in symbols:
            candles = self.candle_repo.load_candles(symbol)
            if candles.empty:
                skipped.append({"symbol": symbol, "reason": "no candles stored"})
                continue
            try:
                features = build_features(symbol, candles, self.min_avg_traded_value)
            except ValueError as exc:
                skipped.append({"symbol": symbol, "reason": str(exc)})
                continue
            raw_features.append(features)

        self._add_relative_strength(raw_features)

        candidates = []
        for features in raw_features:
            score_result = score_features(features)
            if score_result.score < min_score and score_result.verdict == "reject":
                continue
            trade_plan = build_trade_plan(features)
            strategy_profile = build_strategy_profile(features, score_result.score, score_result.verdict, trade_plan)
            strategy_matches = match_strategy_families(
                features,
                score_result.score,
                score_result.verdict,
                trade_plan,
            )
            candidates.append(
                {
                    "symbol": features["symbol"],
                    "sector": sector_for_symbol(features["symbol"]),
                    "close": features["close"],
                    "breakout_level": features["breakout_level"],
                    "score": score_result.score,
                    "verdict": score_result.verdict,
                    "reasons": score_result.reasons,
                    "risk_flags": score_result.risk_flags,
                    "trade_plan": trade_plan,
                    "strategy_profile": strategy_profile,
                    "strategy_matches": strategy_matches,
                    "features": features,
                }
            )

        candidates.sort(key=lambda item: item["score"], reverse=True)
        candidates.extend(self._missing_data_candidate(item) for item in skipped)
        scan_date = self._scan_date(raw_features)
        return {
            "scan_date": scan_date.isoformat(),
            "market_context": self._market_context(raw_features),
            "candidates": candidates,
            "skipped": skipped,
        }

    @staticmethod
    def _missing_data_candidate(skipped_item: dict) -> dict:
        symbol = skipped_item["symbol"].upper()
        reason = skipped_item["reason"]
        return {
            "symbol": symbol,
            "sector": sector_for_symbol(symbol),
            "close": 0,
            "breakout_level": 0,
            "score": 0,
            "verdict": "data_missing",
            "reasons": [],
            "risk_flags": [reason],
            "trade_plan": {},
            "strategy_matches": [],
            "strategy_profile": {
                "primary_strategy": "data_missing",
                "strategy_label": "Data Missing",
                "setup_phase": "unavailable",
                "tags": [],
                "prediction": {
                    "bias": "unavailable",
                    "confidence": "none",
                    "horizon": "n/a",
                    "summary": reason,
                    "trigger_condition": "Fetch or repair candle data before analysis.",
                },
            },
            "features": {"symbol": symbol, "data_missing": True, "missing_reason": reason},
        }

    @staticmethod
    def _add_relative_strength(features: list[dict]) -> None:
        if not features:
            return
        ranking_df = pd.DataFrame(
            {
                "symbol": [item["symbol"] for item in features],
                "momentum": [item["returns_63d"] * 0.65 + item["returns_126d"] * 0.35 for item in features],
            }
        )
        ranking_df["relative_strength_score"] = ranking_df["momentum"].rank(pct=True) * 100
        scores = dict(zip(ranking_df["symbol"], ranking_df["relative_strength_score"], strict=True))
        for item in features:
            item["relative_strength_score"] = round(float(scores[item["symbol"]]), 2)

    @staticmethod
    def _scan_date(features: list[dict]) -> date:
        if not features:
            return date.today()
        return date.fromisoformat(max(item["scan_date"] for item in features))

    @staticmethod
    def _market_context(features: list[dict]) -> dict:
        if not features:
            return {"nifty_trend": "unknown", "breadth": "unknown", "note": "No features available."}

        above_50 = sum(1 for item in features if item["above_50ema"])
        pct_above_50 = above_50 / len(features) * 100
        avg_rs = sum(item.get("relative_strength_score", 50) for item in features) / len(features)

        if pct_above_50 >= 65:
            trend = "bullish"
        elif pct_above_50 >= 45:
            trend = "neutral"
        else:
            trend = "weak"

        breadth = "positive" if pct_above_50 >= 55 else "mixed" if pct_above_50 >= 40 else "negative"
        return {
            "nifty_trend": trend,
            "breadth": breadth,
            "pct_above_50ema": round(pct_above_50, 1),
            "average_relative_strength": round(avg_rs, 1),
            "note": "Universe-derived proxy. Add NIFTY index candles for stronger market context.",
        }
