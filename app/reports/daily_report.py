from __future__ import annotations


def build_markdown_report(scan_result: dict, llm_report: dict | None = None) -> str:
    report = llm_report or scan_result.get("llm_report") or {}
    lines = [
        f"# Daily Breakout Scan - {scan_result['scan_date']}",
        "",
        "Educational scanner output only; not investment advice.",
        "",
    ]

    market = scan_result.get("market_context", {})
    lines.extend(
        [
            "## Market Context",
            f"- Trend proxy: {market.get('nifty_trend', 'unknown')}",
            f"- Breadth: {market.get('breadth', 'unknown')}",
            f"- Note: {market.get('note', '')}",
            "",
        ]
    )

    if report:
        lines.extend(_pick_section("Top Breakout Watchlist", report.get("top_picks", [])))
        lines.extend(_pick_section("Near-Breakout Watchlist", report.get("near_breakouts", [])))
        lines.extend(_pick_section("Avoid / Do Not Chase", report.get("avoid_list", [])))
        if report.get("market_commentary"):
            lines.extend(["## Analyst Commentary", report["market_commentary"], ""])
    else:
        lines.extend(_candidate_section(scan_result.get("candidates", [])))

    return "\n".join(lines).strip() + "\n"


def _pick_section(title: str, picks: list[dict]) -> list[str]:
    lines = [f"## {title}"]
    if not picks:
        return lines + ["No stocks in this bucket.", ""]
    for pick in picks:
        lines.extend(
            [
                f"### {pick['symbol']} - {pick['confidence'].title()} Confidence",
                f"- Verdict: {pick['verdict']}",
                f"- Action level: {pick['action_level']}",
                f"- Invalidation: {pick['invalidation_level']}",
                f"- Why: {pick['summary']}",
                f"- Risk: {pick['risk_note']}",
                "",
            ]
        )
    return lines


def _candidate_section(candidates: list[dict]) -> list[str]:
    lines = ["## Scanner Candidates"]
    if not candidates:
        return lines + ["No candidates passed the threshold.", ""]
    for item in candidates:
        plan = item.get("trade_plan", {})
        strategy = item.get("strategy_profile", {})
        prediction = strategy.get("prediction", {})
        lines.extend(
            [
                f"### {item['symbol']} - Score {item['score']}",
                f"- Close: {item['close']}",
                f"- Strategy: {strategy.get('strategy_label', 'n/a')} ({strategy.get('setup_phase', 'n/a')})",
                f"- Outlook: {prediction.get('bias', 'n/a')} / {prediction.get('confidence', 'n/a')}",
                f"- Breakout level: {item['breakout_level']}",
                f"- Entry: {plan.get('entry_price', 'n/a')} ({plan.get('entry_type', 'n/a')})",
                f"- Stop loss: {plan.get('stop_loss', 'n/a')}",
                f"- Target 1 / Target 2: {plan.get('target_1', 'n/a')} / {plan.get('target_2', 'n/a')}",
                f"- Risk: {plan.get('risk_pct', 'n/a')}% per share, grade {plan.get('risk_grade', 'n/a')}",
                f"- Verdict: {item['verdict']}",
                f"- Reasons: {', '.join(item.get('reasons', [])) or 'None'}",
                f"- Risks: {', '.join(item.get('risk_flags', [])) or 'None'}",
                f"- Prediction note: {prediction.get('summary', 'None')}",
                f"- Plan notes: {', '.join(plan.get('notes', [])) or 'None'}",
                "",
            ]
        )
    return lines
