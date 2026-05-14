from __future__ import annotations

import json
from typing import Any

from app.config import Settings
from app.llm.prompts import ANALYST_SYSTEM_PROMPT, build_user_payload
from app.llm.schemas import AnalystPick, DailyAnalysisReport


class AnalystLLM:
    def __init__(self, settings: Settings):
        self.settings = settings

    def explain_scan(self, scan_date: str, market_context: dict, candidates: list[dict]) -> dict:
        if not candidates:
            return self._empty_report("No candidates met the scanner threshold.")

        if not self._has_usable_api_key():
            return self._fallback_report(market_context, candidates, "OPENAI_API_KEY is not configured.")

        payload = build_user_payload(scan_date, market_context, candidates)
        try:
            from openai import OpenAI
        except ImportError:
            return self._fallback_report(market_context, candidates, "openai package is not installed.")

        client = OpenAI(api_key=self.settings.openai_api_key)
        try:
            response = client.responses.parse(
                model=self.settings.openai_model,
                input=[
                    {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, separators=(",", ":"))},
                ],
                text_format=DailyAnalysisReport,
            )
            parsed = response.output_parsed
            if parsed is None:
                return self._fallback_report(market_context, candidates, "OpenAI returned no parsed report.")
            return parsed.model_dump()
        except Exception as exc:
            return self._fallback_report(market_context, candidates, f"OpenAI summary failed: {exc}")

    def _has_usable_api_key(self) -> bool:
        key = (self.settings.openai_api_key or "").strip()
        return bool(key) and not key.startswith("your_")

    @staticmethod
    def _empty_report(message: str) -> dict:
        return DailyAnalysisReport(
            top_picks=[],
            near_breakouts=[],
            avoid_list=[],
            market_commentary=message,
            risk_disclaimer="Educational scanner output only; not investment advice.",
        ).model_dump()

    def _fallback_report(self, market_context: dict, candidates: list[dict], reason: str) -> dict:
        top_picks = []
        near_breakouts = []
        avoid_list = []

        for item in candidates:
            pick = self._pick_from_candidate(item)
            if item["verdict"] == "strong_watchlist":
                top_picks.append(pick)
            elif item["verdict"] in {"possible_breakout", "near_breakout"}:
                near_breakouts.append(pick)
            else:
                avoid_list.append(pick)

        report = DailyAnalysisReport(
            top_picks=top_picks[:5],
            near_breakouts=near_breakouts[:7],
            avoid_list=avoid_list[:7],
            market_commentary=(
                f"{market_context.get('nifty_trend', 'unknown').title()} market proxy with "
                f"{market_context.get('breadth', 'unknown')} breadth. LLM fallback used: {reason}"
            ),
            risk_disclaimer="Educational scanner output only; not investment advice.",
        )
        return report.model_dump()

    @staticmethod
    def _pick_from_candidate(item: dict[str, Any]) -> AnalystPick:
        features = item["features"]
        verdict_map = {
            "strong_watchlist": "watch for breakout",
            "possible_breakout": "watch for breakout",
            "near_breakout": "near breakout",
            "avoid": "avoid chasing",
            "reject": "reject",
        }
        confidence = "high" if item["score"] >= 80 else "medium" if item["score"] >= 65 else "low"
        risk_note = "; ".join(item["risk_flags"]) if item["risk_flags"] else "Use breakout level and swing low for risk control."
        summary = "; ".join(item["reasons"]) if item["reasons"] else "Setup needs more confirmation."
        return AnalystPick(
            symbol=item["symbol"],
            verdict=verdict_map.get(item["verdict"], "reject"),
            confidence=confidence,
            summary=summary,
            risk_note=risk_note,
            action_level=float(item["breakout_level"]),
            invalidation_level=float(features["swing_low_20d"]),
            ranking_reason=f"Scanner score {item['score']} with volume {features['volume_vs_20d']}x 20-day average.",
        )
