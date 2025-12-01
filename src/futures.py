from __future__ import annotations
import pandas as pd

def zq_price_to_implied_avg_rate(price: float) -> float:
    """Convert ZQ price (e.g., 94.70) → implied monthly avg rate (decimal, e.g., 0.0530)."""
    return (100.0 - float(price)) / 100.0

def implied_from_prices(df_zq: pd.DataFrame) -> pd.DataFrame:
    """Given columns [date, price, meeting_month], compute implied_bps for each row."""
    df = df_zq.copy()
    df["implied_rate"] = df["price"].apply(zq_price_to_implied_avg_rate)  # decimal
    df["implied_bps"]  = (df["implied_rate"] * 10000).round(3)
    return df
