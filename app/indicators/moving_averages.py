import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["ema_20"] = ema(result["close"], 20)
    result["ema_50"] = ema(result["close"], 50)
    result["ema_200"] = ema(result["close"], 200)
    result["sma_20"] = sma(result["close"], 20)
    result["sma_50"] = sma(result["close"], 50)
    return result

