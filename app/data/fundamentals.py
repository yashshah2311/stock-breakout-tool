from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

from app.data.yahoo_client import YahooFinanceClient


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return round(result, 4)


def _safe_int(value: Any) -> int | None:
    number = _safe_float(value)
    return int(number) if number is not None else None


def _pct(value: Any) -> float | None:
    number = _safe_float(value)
    return round(number * 100, 2) if number is not None else None


def _statement_value(df: pd.DataFrame, aliases: list[str], column_index: int) -> float | None:
    if df is None or df.empty or len(df.columns) <= column_index:
        return None
    for alias in aliases:
        if alias in df.index:
            return _safe_float(df.iloc[df.index.get_loc(alias), column_index])
    return None


def _growth(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in {None, 0}:
        return None
    return round(((current - previous) / abs(previous)) * 100, 2)


def _cagr(current: float | None, past: float | None, years: int = 3) -> float | None:
    if current is None or past is None or current <= 0 or past <= 0:
        return None
    return round(((current / past) ** (1 / years) - 1) * 100, 2)


def _ratio(numerator: float | None, denominator: float | None, multiplier: float = 1.0) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return round(numerator / denominator * multiplier, 2)


def _signal(value: float | None, excellent: float, good: float, higher_is_better: bool = True) -> str:
    if value is None:
        return "Unavailable"
    if higher_is_better:
        if value >= excellent:
            return "Excellent"
        if value >= good:
            return "Good"
        return "Weak"
    if value <= excellent:
        return "Excellent"
    if value <= good:
        return "Good"
    return "Weak"


def _statement_series(df: pd.DataFrame, aliases: list[str], limit: int = 4) -> list[float | None]:
    if df is None or df.empty:
        return []
    for alias in aliases:
        if alias in df.index:
            return [_safe_float(value) for value in list(df.loc[alias].iloc[:limit])]
    return []


def _series_value(values: list[float | None], index: int) -> float | None:
    if len(values) <= index:
        return None
    return values[index]


def _trend_label(current: float | None, past: float | None, falling_good: bool) -> str:
    if current is None or past is None:
        return "Unavailable"
    falling = current < past
    if falling_good:
        return "Good" if falling else "Risk"
    return "Good" if not falling else "Risk"


class FundamentalsClient:
    def __init__(self):
        self.yahoo = YahooFinanceClient()

    def fundamentals(self, symbol: str) -> dict:
        return _fetch_fundamentals(self.yahoo.yahoo_symbol(symbol), symbol.strip().upper())


@lru_cache(maxsize=256)
def _fetch_fundamentals(provider_symbol: str, symbol: str) -> dict:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("Install yfinance with `pip install -r requirements.txt`.") from exc

    ticker = yf.Ticker(provider_symbol)
    try:
        info = ticker.get_info()
    except Exception:
        info = {}

    try:
        quarterly_financials = ticker.quarterly_financials
    except Exception:
        quarterly_financials = pd.DataFrame()
    try:
        annual_financials = ticker.financials
    except Exception:
        annual_financials = pd.DataFrame()
    try:
        annual_balance_sheet = ticker.balance_sheet
    except Exception:
        annual_balance_sheet = pd.DataFrame()
    try:
        annual_cashflow = ticker.cashflow
    except Exception:
        annual_cashflow = pd.DataFrame()

    revenue_aliases = ["Total Revenue", "Operating Revenue"]
    income_aliases = ["Net Income", "Net Income Common Stockholders"]

    latest_revenue = _statement_value(quarterly_financials, revenue_aliases, 0)
    previous_revenue = _statement_value(quarterly_financials, revenue_aliases, 1)
    year_ago_revenue = _statement_value(quarterly_financials, revenue_aliases, 4)
    latest_net_income = _statement_value(quarterly_financials, income_aliases, 0)
    previous_net_income = _statement_value(quarterly_financials, income_aliases, 1)
    year_ago_net_income = _statement_value(quarterly_financials, income_aliases, 4)

    quarters = []
    if quarterly_financials is not None and not quarterly_financials.empty:
        for idx, column in enumerate(list(quarterly_financials.columns)[:4]):
            quarters.append(
                {
                    "period": str(column.date() if hasattr(column, "date") else column),
                    "revenue": _statement_value(quarterly_financials, revenue_aliases, idx),
                    "net_income": _statement_value(quarterly_financials, income_aliases, idx),
                }
            )

    fundamentals = {
        "symbol": symbol,
        "provider_symbol": provider_symbol,
        "company_name": info.get("longName") or info.get("shortName") or symbol,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": _safe_int(info.get("marketCap")),
        "trailing_pe": _safe_float(info.get("trailingPE")),
        "forward_pe": _safe_float(info.get("forwardPE")),
        "price_to_book": _safe_float(info.get("priceToBook")),
        "eps_ttm": _safe_float(info.get("trailingEps")),
        "return_on_equity_pct": _pct(info.get("returnOnEquity")),
        "profit_margin_pct": _pct(info.get("profitMargins")),
        "revenue_growth_pct": _pct(info.get("revenueGrowth")),
        "earnings_growth_pct": _pct(info.get("earningsGrowth")),
        "debt_to_equity": _safe_float(info.get("debtToEquity")),
        "dividend_yield_pct": _pct(info.get("dividendYield")),
        "quarterly": {
            "latest_revenue": latest_revenue,
            "latest_net_income": latest_net_income,
            "revenue_qoq_pct": _growth(latest_revenue, previous_revenue),
            "revenue_yoy_pct": _growth(latest_revenue, year_ago_revenue),
            "net_income_qoq_pct": _growth(latest_net_income, previous_net_income),
            "net_income_yoy_pct": _growth(latest_net_income, year_ago_net_income),
            "recent_quarters": quarters,
        },
    }
    fundamentals["long_term_research"] = _long_term_research(
        fundamentals=fundamentals,
        annual_financials=annual_financials,
        annual_balance_sheet=annual_balance_sheet,
        annual_cashflow=annual_cashflow,
        info=info,
    )
    fundamentals["quality_score"] = _quality_score(fundamentals)
    fundamentals["valuation_note"] = _valuation_note(fundamentals)
    return fundamentals


def _long_term_research(
    fundamentals: dict,
    annual_financials: pd.DataFrame,
    annual_balance_sheet: pd.DataFrame,
    annual_cashflow: pd.DataFrame,
    info: dict,
) -> dict:
    revenue = _statement_series(annual_financials, ["Total Revenue", "Operating Revenue"], 4)
    pat = _statement_series(annual_financials, ["Net Income", "Net Income Common Stockholders"], 4)
    ebit = _statement_series(annual_financials, ["EBIT", "Operating Income"], 4)
    ebitda = _statement_series(annual_financials, ["EBITDA", "Normalized EBITDA"], 4)
    operating_income = _statement_series(annual_financials, ["Operating Income", "EBIT"], 4)
    interest_expense = _statement_series(annual_financials, ["Interest Expense", "Interest Expense Non Operating"], 4)
    other_income = _statement_series(annual_financials, ["Other Income Expense", "Other Non Operating Income Expenses"], 4)
    operating_cashflow = _statement_series(annual_cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"], 4)
    capital_expenditure = _statement_series(annual_cashflow, ["Capital Expenditure", "Capital Expenditures"], 4)
    total_debt = _statement_series(annual_balance_sheet, ["Total Debt", "Net Debt"], 4)
    equity = _statement_series(annual_balance_sheet, ["Stockholders Equity", "Total Equity Gross Minority Interest"], 4)
    receivables = _statement_series(annual_balance_sheet, ["Accounts Receivable", "Net Receivables"], 4)
    inventory = _statement_series(annual_balance_sheet, ["Inventory"], 4)
    payables = _statement_series(annual_balance_sheet, ["Accounts Payable", "Payables"], 4)
    capital_employed = _statement_series(
        annual_balance_sheet,
        ["Invested Capital", "Total Capitalization", "Total Assets"],
        4,
    )
    shares = _statement_series(annual_balance_sheet, ["Ordinary Shares Number", "Share Issued"], 4)

    sales_cagr = _cagr(_series_value(revenue, 0), _series_value(revenue, 3))
    pat_cagr = _cagr(_series_value(pat, 0), _series_value(pat, 3))
    eps_growth_pct = fundamentals.get("earnings_growth_pct")
    eps_cagr = eps_growth_pct if eps_growth_pct is not None else None
    ebitda_growth = _growth(_series_value(ebitda, 0), _series_value(ebitda, 1))
    sales_growth = _growth(_series_value(revenue, 0), _series_value(revenue, 1))
    opm_current = _ratio(_series_value(operating_income, 0), _series_value(revenue, 0), 100)
    opm_3y_avg_values = [
        _ratio(_series_value(operating_income, index), _series_value(revenue, index), 100)
        for index in range(1, 4)
    ]
    opm_3y_avg_values = [value for value in opm_3y_avg_values if value is not None]
    opm_3y_avg = round(sum(opm_3y_avg_values) / len(opm_3y_avg_values), 2) if opm_3y_avg_values else None
    opm_change = None if opm_current is None or opm_3y_avg is None else round(opm_current - opm_3y_avg, 2)
    cfo_pat = _ratio(_series_value(operating_cashflow, 0), _series_value(pat, 0))
    other_income_pat = _ratio(abs(_series_value(other_income, 0) or 0), abs(_series_value(pat, 0) or 0), 100)
    roce = _ratio(_series_value(ebit, 0), _series_value(capital_employed, 0), 100)
    incremental_roce = _ratio(
        (_series_value(ebit, 0) or 0) - (_series_value(ebit, 1) or 0),
        (_series_value(capital_employed, 0) or 0) - (_series_value(capital_employed, 1) or 0),
        100,
    )
    receivable_days = _ratio(_series_value(receivables, 0), _series_value(revenue, 0), 365)
    receivable_days_old = _ratio(_series_value(receivables, 2), _series_value(revenue, 2), 365)
    inventory_days = _ratio(_series_value(inventory, 0), _series_value(revenue, 0), 365)
    payable_days = _ratio(_series_value(payables, 0), _series_value(revenue, 0), 365)
    wc_days = None
    if receivable_days is not None or inventory_days is not None or payable_days is not None:
        wc_days = round((receivable_days or 0) + (inventory_days or 0) - (payable_days or 0), 2)
    wc_days_old = None
    old_receivable = _ratio(_series_value(receivables, 2), _series_value(revenue, 2), 365)
    old_inventory = _ratio(_series_value(inventory, 2), _series_value(revenue, 2), 365)
    old_payable = _ratio(_series_value(payables, 2), _series_value(revenue, 2), 365)
    if old_receivable is not None or old_inventory is not None or old_payable is not None:
        wc_days_old = round((old_receivable or 0) + (old_inventory or 0) - (old_payable or 0), 2)
    debt_ebitda = _ratio(_series_value(total_debt, 0), _series_value(ebitda, 0))
    interest_coverage = _ratio(_series_value(ebit, 0), abs(_series_value(interest_expense, 0) or 0))
    equity_dilution = _growth(_series_value(shares, 0), _series_value(shares, 3))
    eps_pat_gap = None if eps_cagr is None or pat_cagr is None else round(eps_cagr - pat_cagr, 2)
    pe = fundamentals.get("trailing_pe")
    peg = _ratio(pe, eps_cagr)
    ebitda_vs_sales_growth = None if ebitda_growth is None or sales_growth is None else round(ebitda_growth - sales_growth, 2)

    sections = [
        {
            "id": "growth",
            "title": "A. Growth Quality Parameters",
            "metrics": [
                _metric("Sales CAGR", sales_cagr, "%", "((Current Sales / 3Y Ago Sales)^(1/3))-1", _signal(sales_cagr, 20, 12)),
                _metric("PAT CAGR", pat_cagr, "%", "Same CAGR formula", _signal(pat_cagr, 20, 12)),
                _metric("EPS CAGR", eps_cagr, "%", "EPS growth/CAGR", _signal(eps_cagr, 18, 12)),
            ],
        },
        {
            "id": "dilution",
            "title": "B. Dilution Parameters",
            "metrics": [
                _metric("Equity Dilution %", equity_dilution, "%", "((Current Equity Shares / Old Equity Shares)-1)*100", _dilution_signal(equity_dilution)),
                _metric("EPS vs PAT Gap", eps_pat_gap, "pp", "EPS CAGR - PAT CAGR", _eps_pat_signal(eps_pat_gap)),
            ],
        },
        {
            "id": "quality",
            "title": "C. Earnings Quality Parameters",
            "metrics": [
                _metric("CFO / PAT Ratio", cfo_pat, "x", "Operating Cash Flow / PAT", _cfo_pat_signal(cfo_pat)),
                _metric("Other Income Dependency", other_income_pat, "%", "Other Income / PAT", _other_income_signal(other_income_pat)),
            ],
        },
        {
            "id": "margin",
            "title": "D. Margin Parameters",
            "metrics": [
                _metric("OPM Trend", opm_change, "pp", "Current OPM - 3Y Avg OPM", "Expansion" if opm_change and opm_change > 0 else "Compression" if opm_change is not None else "Unavailable"),
                _metric("EBITDA vs Sales Growth", ebitda_vs_sales_growth, "pp", "EBITDA Growth - Sales Growth", "Operating leverage" if ebitda_vs_sales_growth and ebitda_vs_sales_growth > 0 else "Margin pressure" if ebitda_vs_sales_growth is not None else "Unavailable"),
            ],
        },
        {
            "id": "capital_efficiency",
            "title": "E. Capital Efficiency Parameters",
            "metrics": [
                _metric("ROCE", roce, "%", "EBIT / Capital Employed", _signal(roce, 20, 15)),
                _metric("Incremental ROCE", incremental_roce, "%", "Change in EBIT / Change in Capital Employed", _signal(incremental_roce, 25, 15)),
            ],
        },
        {
            "id": "working_capital",
            "title": "F. Working Capital Parameters",
            "metrics": [
                _metric("Receivable Days", receivable_days, "days", "Receivables / Revenue * 365", _trend_label(receivable_days, receivable_days_old, True)),
                _metric("Inventory Days", inventory_days, "days", "Inventory / Revenue * 365", "Lower is better"),
                _metric("Working Capital Days", wc_days, "days", "Receivable + Inventory - Payable", _trend_label(wc_days, wc_days_old, True)),
            ],
        },
        {
            "id": "balance_sheet",
            "title": "G. Balance Sheet Parameters",
            "metrics": [
                _metric("Debt / EBITDA", debt_ebitda, "x", "Total Debt / EBITDA", _debt_ebitda_signal(debt_ebitda)),
                _metric("Interest Coverage", interest_coverage, "x", "EBIT / Interest Expense", _interest_coverage_signal(interest_coverage)),
            ],
        },
        {
            "id": "rerating",
            "title": "H. Rerating Parameters",
            "metrics": [
                _metric("PEG Ratio", peg, "x", "PE / EPS Growth", _peg_signal(peg)),
                _metric("Order Book / Revenue", None, "x", "Order Book / Annual Revenue", "Unavailable in Yahoo free data"),
            ],
        },
        {
            "id": "sector_cycle",
            "title": "I. Sector Cycle Parameters",
            "metrics": [
                _metric("Sector PE vs historical PE", None, "", "Sector PE vs historical PE", "Needs sector history dataset"),
                _metric("Industry growth %", fundamentals.get("revenue_growth_pct"), "%", "Industry/stock growth proxy", _signal(fundamentals.get("revenue_growth_pct"), 15, 8)),
                _metric("Capacity utilization", None, "", "Capacity utilization", "Needs industry dataset"),
            ],
        },
    ]
    matrix = _master_matrix(sections)
    score = round(sum(item["points"] for item in matrix) / max(len(matrix), 1))
    verdict = "Long-term compounder candidate" if score >= 70 else "Good but needs review" if score >= 50 else "Weak long-term quality"
    dashboard = _dashboard_payload(
        fundamentals=fundamentals,
        score=score,
        verdict=verdict,
        sections=sections,
        revenue=revenue,
        pat=pat,
        equity=equity,
        operating_income=operating_income,
        capital_employed=capital_employed,
        total_debt=total_debt,
        other_income=other_income,
        operating_cashflow=operating_cashflow,
        capital_expenditure=capital_expenditure,
        receivable_days=receivable_days,
        wc_days=wc_days,
        annual_financials=annual_financials,
    )
    return {"score": score, "verdict": verdict, "sections": sections, "master_matrix": matrix, "dashboard": dashboard}


def _metric(name: str, value: float | None, unit: str, formula: str, signal: str) -> dict:
    return {"name": name, "value": value, "unit": unit, "formula": formula, "signal": signal}


def _points(signal: str) -> int:
    positive = {"Excellent", "Strong", "Good", "Expansion", "Operating leverage", "Clean", "Safe", "Healthy", "Undervalued growth", "Efficient"}
    neutral = {"Acceptable", "Okay", "Fair", "Moderate", "Manageable", "Lower is better"}
    if signal in positive:
        return 100
    if signal in neutral:
        return 60
    if signal == "Unavailable" or signal.startswith("Needs"):
        return 0
    return 20


def _master_matrix(sections: list[dict]) -> list[dict]:
    rows = []
    for section in sections:
        for metric in section["metrics"]:
            rows.append(
                {
                    "category": section["title"].split(". ", 1)[-1],
                    "parameter": metric["name"],
                    "formula": metric["formula"],
                    "threshold": metric["signal"],
                    "points": _points(metric["signal"]),
                }
            )
    return rows


def _dilution_signal(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if value < 3:
        return "Safe"
    if value <= 8:
        return "Watch"
    return "Dilution Risk"


def _eps_pat_signal(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if abs(value) <= 3:
        return "Healthy"
    if value < 0:
        return "Dilution"
    return "Buybacks/high efficiency"


def _cfo_pat_signal(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if value > 1:
        return "Excellent"
    if value >= 0.8:
        return "Acceptable"
    return "Weak"


def _other_income_signal(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if value < 10:
        return "Clean"
    if value <= 20:
        return "Moderate"
    return "Risky"


def _debt_ebitda_signal(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if value < 1:
        return "Strong"
    if value <= 2:
        return "Manageable"
    return "Dangerous"


def _interest_coverage_signal(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if value > 5:
        return "Strong"
    if value >= 2:
        return "Okay"
    return "Weak"


def _peg_signal(value: float | None) -> str:
    if value is None:
        return "Unavailable"
    if value < 1:
        return "Undervalued growth"
    if value <= 2:
        return "Fair"
    return "Expensive"


def _dashboard_payload(
    fundamentals: dict,
    score: int,
    verdict: str,
    sections: list[dict],
    revenue: list[float | None],
    pat: list[float | None],
    equity: list[float | None],
    operating_income: list[float | None],
    capital_employed: list[float | None],
    total_debt: list[float | None],
    other_income: list[float | None],
    operating_cashflow: list[float | None],
    capital_expenditure: list[float | None],
    receivable_days: float | None,
    wc_days: float | None,
    annual_financials: pd.DataFrame,
) -> dict:
    def metric(name: str) -> dict | None:
        for section in sections:
            for item in section["metrics"]:
                if item["name"] == name:
                    return item
        return None

    def card(label: str, value: float | int | None, suffix: str, signal: str, previous: float | None = None) -> dict:
        return {"label": label, "value": value, "suffix": suffix, "signal": signal, "previous": previous}

    sales_growth = metric("Sales CAGR") or {}
    pat_growth = metric("PAT CAGR") or {}
    eps_growth = metric("EPS CAGR") or {}
    eps_pat_gap = metric("EPS vs PAT Gap") or {}
    opm_trend = metric("OPM Trend") or {}
    roce_metric = metric("ROCE") or {}
    dilution = metric("Equity Dilution %") or {}
    other_income_pat = metric("Other Income Dependency") or {}
    wc_metric = metric("Working Capital Days") or {}
    cfo_pat = metric("CFO / PAT Ratio") or {}

    latest_revenue = _series_value(revenue, 0)
    latest_pat = _series_value(pat, 0)
    latest_operating_income = _series_value(operating_income, 0)
    latest_capex = abs(_series_value(capital_expenditure, 0) or 0)
    latest_cfo = _series_value(operating_cashflow, 0)
    fcf = None if latest_cfo is None else round(latest_cfo - latest_capex, 2)
    debt = _series_value(total_debt, 0)
    debt_equity = _ratio(debt, _series_value(equity, 0))
    market_cap_cr = _crore(fundamentals.get("market_cap"))
    current_price = fundamentals.get("eps_ttm")

    cards = [
        card("Sales Growth (3Y)", sales_growth.get("value"), "%", sales_growth.get("signal", "Unavailable")),
        card("PAT Growth (3Y)", pat_growth.get("value"), "%", pat_growth.get("signal", "Unavailable")),
        card("EPS Growth (YoY)", eps_growth.get("value"), "%", eps_growth.get("signal", "Unavailable")),
        card("EPS vs PAT Gap", eps_pat_gap.get("value"), "pp", eps_pat_gap.get("signal", "Unavailable")),
        card("OPM Change", opm_trend.get("value"), "pp", opm_trend.get("signal", "Unavailable")),
        card("ROCE", roce_metric.get("value"), "%", roce_metric.get("signal", "Unavailable")),
        card("Market Cap", market_cap_cr, " Cr", "Info"),
        card("PE (TTM)", fundamentals.get("trailing_pe"), "x", fundamentals.get("valuation_note", "Info")),
        card("Debt / Equity", debt_equity, "x", "Strong" if debt_equity is not None and debt_equity < 1 else "Watch"),
        card("ROE", fundamentals.get("return_on_equity_pct"), "%", _signal(fundamentals.get("return_on_equity_pct"), 18, 12)),
        card("Equity Dilution (3Y)", dilution.get("value"), "%", dilution.get("signal", "Unavailable")),
        card("Other Income / PAT", other_income_pat.get("value"), "%", other_income_pat.get("signal", "Unavailable")),
        card("Working Capital Days", wc_metric.get("value"), " days", wc_metric.get("signal", "Unavailable")),
        card("FCF", _crore(fcf), " Cr", "Positive" if fcf and fcf > 0 else "Negative" if fcf is not None else "Unavailable"),
        card("Capex", _crore(latest_capex), " Cr", "Moderate"),
        card("Quality Score", score / 10, " / 10", verdict),
    ]

    year_labels = _year_labels(annual_financials, 4)
    opm_series = [
        _ratio(_series_value(operating_income, idx), _series_value(revenue, idx), 100)
        for idx in range(4)
    ]
    roce_series = [
        _ratio(_statement_value(annual_financials, ["EBIT", "Operating Income"], idx), _series_value(capital_employed, idx), 100)
        for idx in range(4)
    ]
    debt_equity_series = [_ratio(_series_value(total_debt, idx), _series_value(equity, idx)) for idx in range(4)]
    fcf_series = []
    capex_series = []
    for idx in range(4):
        cfo = _series_value(operating_cashflow, idx)
        capex = abs(_series_value(capital_expenditure, idx) or 0)
        fcf_series.append(None if cfo is None else _crore(cfo - capex))
        capex_series.append(_crore(capex))
    sales_growth_series = _growth_series(revenue)
    pat_growth_series = _growth_series(pat)
    eps_proxy_series = _growth_series(pat)

    trends = [
        _trend("Sales", [_crore(value) for value in revenue], year_labels, "Cr"),
        _trend("PAT", [_crore(value) for value in pat], year_labels, "Cr"),
        _trend("Sales Growth", sales_growth_series, year_labels[1:], "%"),
        _trend("PAT Growth", pat_growth_series, year_labels[1:], "%"),
        _trend("EPS Proxy", eps_proxy_series, year_labels[1:], "%"),
        _trend("OPM", opm_series, year_labels, "%"),
        _trend("ROCE", roce_series, year_labels, "%"),
        _trend("Debt / Equity", debt_equity_series, year_labels, "x"),
        _trend("Equity", [_crore(value) for value in equity], year_labels, "Cr"),
        _trend("Other Income", [_crore(value) for value in other_income], year_labels, "Cr"),
        _trend("FCF", fcf_series, year_labels, "Cr"),
        _trend("Capex", capex_series, year_labels, "Cr"),
    ]

    return {
        "cards": cards,
        "trends": trends,
        "summary_tables": {
            "financial_summary": [
                {"label": "Sales", "value": _crore(latest_revenue), "unit": "Cr"},
                {"label": "PAT", "value": _crore(latest_pat), "unit": "Cr"},
                {"label": "Operating Income", "value": _crore(latest_operating_income), "unit": "Cr"},
                {"label": "FCF", "value": _crore(fcf), "unit": "Cr"},
                {"label": "Total Debt", "value": _crore(debt), "unit": "Cr"},
            ],
            "quality_checks": [
                {"metric": "EPS vs PAT Growth", "status": eps_pat_gap.get("signal", "Unavailable")},
                {"metric": "Dilution (3Y)", "status": dilution.get("signal", "Unavailable")},
                {"metric": "Other Income / PAT", "status": other_income_pat.get("signal", "Unavailable")},
                {"metric": "CFO / PAT", "status": cfo_pat.get("signal", "Unavailable")},
                {"metric": "Earnings Quality", "status": verdict},
            ],
        },
    }


def _crore(value: float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value) / 10_000_000, 2)


def _year_labels(df: pd.DataFrame, limit: int) -> list[str]:
    if df is None or df.empty:
        return []
    labels = []
    for column in list(df.columns)[:limit]:
        if hasattr(column, "year"):
            labels.append(str(column.year))
        else:
            labels.append(str(column)[:4])
    return labels


def _growth_series(values: list[float | None]) -> list[float | None]:
    result = []
    for idx in range(len(values) - 1):
        result.append(_growth(_series_value(values, idx), _series_value(values, idx + 1)))
    return result


def _trend(name: str, values: list[float | None], labels: list[str], unit: str = "") -> dict:
    pairs = [
        {"label": label, "value": value}
        for label, value in zip(labels, values, strict=False)
        if value is not None
    ]
    pairs.reverse()
    return {
        "name": name,
        "unit": unit,
        "labels": [item["label"] for item in pairs],
        "values": [item["value"] for item in pairs],
    }


def _quality_score(fundamentals: dict) -> int:
    score = 0
    if (fundamentals.get("profit_margin_pct") or 0) >= 10:
        score += 20
    if (fundamentals.get("return_on_equity_pct") or 0) >= 12:
        score += 20
    if (fundamentals.get("revenue_growth_pct") or 0) > 0:
        score += 15
    if (fundamentals.get("earnings_growth_pct") or 0) > 0:
        score += 15
    pe = fundamentals.get("trailing_pe")
    if pe is not None and pe <= 40:
        score += 15
    debt = fundamentals.get("debt_to_equity")
    if debt is None or debt <= 150:
        score += 15
    return max(0, min(100, score))


def _valuation_note(fundamentals: dict) -> str:
    pe = fundamentals.get("trailing_pe")
    earnings_growth = fundamentals.get("earnings_growth_pct")
    if pe is None:
        return "P/E not available from Yahoo for this stock."
    if pe > 70:
        return "High P/E; breakout needs strong earnings support."
    if pe > 40:
        return "Premium valuation; avoid chasing extended moves."
    if earnings_growth is not None and earnings_growth > 0:
        return "Valuation is more acceptable if earnings growth continues."
    return "Check earnings trend before relying on valuation."
