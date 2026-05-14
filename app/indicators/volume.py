import pandas as pd


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["avg_volume_20"] = result["volume"].rolling(20, min_periods=20).mean()
    result["volume_vs_20d"] = result["volume"] / result["avg_volume_20"]
    result["highest_volume_10"] = result["volume"] >= result["volume"].shift(1).rolling(10).max()
    result["avg_traded_value_20d"] = result["avg_volume_20"] * result["close"]
    return result

