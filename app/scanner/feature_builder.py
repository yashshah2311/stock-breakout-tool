from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from app.indicators.breakout import add_breakout_levels, add_volatility_contraction
from app.indicators.candle_patterns import candle_body_atr_ratio, detect_latest_pattern
from app.indicators.moving_averages import add_moving_averages
from app.indicators.volume import add_volume_features


def _float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    result = df.copy()
    delta = result["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result[f"rsi_{window}"] = 100 - (100 / (1 + rs))
    return result


def add_atr(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    result = df.copy()
    high_low = result["high"] - result["low"]
    high_close = (result["high"] - result["close"].shift()).abs()
    low_close = (result["low"] - result["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    result[f"atr_{window}"] = true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    result[f"atr_{window}_pct"] = result[f"atr_{window}"] / result["close"] * 100
    return result


def add_adx(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    result = df.copy()
    up_move = result["high"].diff()
    down_move = -result["low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    high_low = result["high"] - result["low"]
    high_close = (result["high"] - result["close"].shift()).abs()
    low_close = (result["low"] - result["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()

    plus_di = 100 * pd.Series(plus_dm, index=result.index).ewm(alpha=1 / window, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=result.index).ewm(alpha=1 / window, adjust=False).mean() / atr
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    result[f"adx_{window}"] = dx.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    result[f"plus_di_{window}"] = plus_di
    result[f"minus_di_{window}"] = minus_di
    result[f"adx_{window}_slope"] = result[f"adx_{window}"].diff()
    return result


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    ema_12 = result["close"].ewm(span=12, adjust=False, min_periods=12).mean()
    ema_26 = result["close"].ewm(span=26, adjust=False, min_periods=26).mean()
    result["macd_line"] = ema_12 - ema_26
    result["macd_signal"] = result["macd_line"].ewm(span=9, adjust=False, min_periods=9).mean()
    result["macd_hist"] = result["macd_line"] - result["macd_signal"]
    result["macd_hist_prev"] = result["macd_hist"].shift()
    return result


def add_stochastic(df: pd.DataFrame, window: int = 14, smooth: int = 3) -> pd.DataFrame:
    result = df.copy()
    low_min = result["low"].rolling(window).min()
    high_max = result["high"].rolling(window).max()
    result["stoch_k"] = (result["close"] - low_min) / (high_max - low_min).replace(0, np.nan) * 100
    result["stoch_d"] = result["stoch_k"].rolling(smooth).mean()
    result["stoch_k_prev"] = result["stoch_k"].shift()
    result["stoch_d_prev"] = result["stoch_d"].shift()
    return result


def prepare_candles(df: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing candle columns: {', '.join(sorted(missing))}")

    result = df.copy()
    result["date"] = pd.to_datetime(result["date"])
    result = result.sort_values("date").drop_duplicates("date")
    numeric_cols = ["open", "high", "low", "close", "volume"]
    result[numeric_cols] = result[numeric_cols].apply(pd.to_numeric, errors="coerce")
    result = result.dropna(subset=numeric_cols)
    return result


def build_features(symbol: str, candles: pd.DataFrame, min_avg_traded_value: float) -> dict:
    df = prepare_candles(candles)
    if len(df) < 220:
        raise ValueError(f"{symbol} needs at least 220 candles for daily scan.")

    df = add_moving_averages(df)
    df = add_volume_features(df)
    df = add_breakout_levels(df)
    df = add_volatility_contraction(df)
    df = add_rsi(df)
    df = add_atr(df)
    df = add_adx(df)
    df = add_macd(df)
    df = add_stochastic(df)

    row = df.iloc[-1]
    close = _float(row["close"])
    ema_20 = _float(row["ema_20"])
    ema_50 = _float(row["ema_50"])
    ema_200 = _float(row["ema_200"])
    ema_20_prev = _float(df["ema_20"].iloc[-2])
    breakout_level = _float(row["breakout_level"], close)
    resistance_20d = _float(row["high_20_prev"], close)
    resistance_50d = _float(row["high_50_prev"], close)
    resistance_52w = _float(row["high_252_prev"], close)
    support_20d = _float(row["low_20_prev"], close)
    support_50d = _float(row["low_50_prev"], close)
    support_52w = _float(row["low_252_prev"], close)
    volume_vs_20d = _float(row["volume_vs_20d"])
    avg_traded_value = _float(row["avg_traded_value_20d"])
    atr = _float(row["atr_14"])
    atr_pct = _float(row["atr_14_pct"])

    returns_63d = _float(close / df["close"].iloc[-64] - 1) if len(df) >= 64 else 0.0
    returns_126d = _float(close / df["close"].iloc[-127] - 1) if len(df) >= 127 else 0.0

    distance = _float(row["distance_to_breakout_pct"])
    near_breakout = -0.5 <= distance <= 2.0
    valid_breakout = bool(row["close_above_20d_high"] or row["close_above_50d_high"])
    extension_from_20ema_pct = _float((close - ema_20) / ema_20 * 100) if ema_20 else 0.0

    features = {
        "symbol": symbol.upper(),
        "scan_date": row["date"].date().isoformat(),
        "close": round(close, 2),
        "volume": int(_float(row["volume"])),
        "avg_volume_20": int(_float(row["avg_volume_20"])),
        "volume_vs_20d": round(volume_vs_20d, 2),
        "highest_volume_10": bool(row["highest_volume_10"]),
        "avg_traded_value_20d": round(avg_traded_value, 2),
        "liquidity_ok": avg_traded_value >= min_avg_traded_value,
        "above_20ema": bool(close > ema_20),
        "above_50ema": bool(close > ema_50),
        "above_200ema": bool(close > ema_200),
        "ema_20_gt_50": bool(ema_20 > ema_50),
        "ema_50_gt_200": bool(ema_50 > ema_200),
        "ema_20": round(ema_20, 2),
        "ema_50": round(ema_50, 2),
        "ema_200": round(ema_200, 2),
        "ema_20_slope_positive": bool(ema_20 > ema_20_prev),
        "breakout_level": round(breakout_level, 2),
        "resistance_20d": round(resistance_20d, 2),
        "resistance_50d": round(resistance_50d, 2),
        "resistance_52w": round(resistance_52w, 2),
        "support_20d": round(support_20d, 2),
        "support_50d": round(support_50d, 2),
        "support_52w": round(support_52w, 2),
        "close_above_20d_high": bool(row["close_above_20d_high"]),
        "close_above_50d_high": bool(row["close_above_50d_high"]),
        "distance_to_breakout_pct": round(distance, 2),
        "near_breakout": near_breakout,
        "valid_breakout": valid_breakout,
        "range_contraction_10d": bool(row["range_contraction_10d"]),
        "tight_base": bool(row["tight_base"]),
        "near_52w_high": bool(row["near_52w_high"]),
        "rsi_14": round(_float(row["rsi_14"]), 2),
        "adx_14": round(_float(row["adx_14"]), 2),
        "plus_di_14": round(_float(row["plus_di_14"]), 2),
        "minus_di_14": round(_float(row["minus_di_14"]), 2),
        "adx_14_slope": round(_float(row["adx_14_slope"]), 2),
        "macd_line": round(_float(row["macd_line"]), 2),
        "macd_signal": round(_float(row["macd_signal"]), 2),
        "macd_hist": round(_float(row["macd_hist"]), 2),
        "macd_hist_prev": round(_float(row["macd_hist_prev"]), 2),
        "stoch_k": round(_float(row["stoch_k"]), 2),
        "stoch_d": round(_float(row["stoch_d"]), 2),
        "stoch_k_prev": round(_float(row["stoch_k_prev"]), 2),
        "stoch_d_prev": round(_float(row["stoch_d_prev"]), 2),
        "atr": round(atr, 2),
        "atr_pct": round(atr_pct, 2),
        "candle_pattern": detect_latest_pattern(df),
        "candle_body_atr_ratio": round(candle_body_atr_ratio(df), 2),
        "extension_from_20ema_pct": round(extension_from_20ema_pct, 2),
        "returns_63d": round(returns_63d, 4),
        "returns_126d": round(returns_126d, 4),
        "swing_low_20d": round(support_20d, 2),
        "base_low": round(support_20d, 2),
        "breakout_candle_low": round(_float(row["low"]), 2),
    }
    return features
