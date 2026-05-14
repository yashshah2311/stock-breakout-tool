from typing import Literal

from pydantic import BaseModel, ConfigDict


Confidence = Literal["high", "medium", "low"]
Verdict = Literal["watch for breakout", "near breakout", "avoid chasing", "reject"]


class AnalystPick(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    verdict: Verdict
    confidence: Confidence
    summary: str
    risk_note: str
    action_level: float
    invalidation_level: float
    ranking_reason: str


class DailyAnalysisReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_picks: list[AnalystPick]
    near_breakouts: list[AnalystPick]
    avoid_list: list[AnalystPick]
    market_commentary: str
    risk_disclaimer: str
