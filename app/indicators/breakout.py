import pandas as pd


def add_breakout_levels(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["high_20_prev"] = result["high"].shift(1).rolling(20, min_periods=20).max()
    result["high_50_prev"] = result["high"].shift(1).rolling(50, min_periods=50).max()
    result["low_20_prev"] = result["low"].shift(1).rolling(20, min_periods=20).min()
    result["low_50_prev"] = result["low"].shift(1).rolling(50, min_periods=50).min()
    result["high_252_prev"] = result["high"].shift(1).rolling(252, min_periods=120).max()
    result["low_252_prev"] = result["low"].shift(1).rolling(252, min_periods=120).min()
    result["breakout_level"] = result[["high_20_prev", "high_50_prev"]].max(axis=1)
    result["close_above_20d_high"] = result["close"] > result["high_20_prev"]
    result["close_above_50d_high"] = result["close"] > result["high_50_prev"]
    result["distance_to_breakout_pct"] = (
        (result["breakout_level"] - result["close"]) / result["close"] * 100
    )
    result["near_52w_high"] = result["close"] >= result["high_252_prev"] * 0.9
    return result


def add_volatility_contraction(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    daily_range_pct = (result["high"] - result["low"]) / result["close"] * 100
    recent = daily_range_pct.rolling(10, min_periods=10).mean()
    previous = daily_range_pct.shift(10).rolling(20, min_periods=20).mean()
    result["range_contraction_10d"] = recent < previous * 0.75
    result["close_std_10_pct"] = result["close"].rolling(10, min_periods=10).std() / result["close"] * 100
    result["tight_base"] = (result["close_std_10_pct"] <= 3.5) & result["range_contraction_10d"]
    return result
