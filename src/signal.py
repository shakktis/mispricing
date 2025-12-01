from __future__ import annotations
import pandas as pd

def compute_signal(df_implied: pd.DataFrame, df_kalshi_month: pd.DataFrame) -> pd.DataFrame:
    """
    Join futures-implied monthly averages with Kalshi-based E[R̄_m] and compute Δ (bps).
    """
    k = df_kalshi_month[["meeting_month", "exp_month_bps"]].drop_duplicates()
    merged = df_implied.merge(k, on="meeting_month", how="left")
    merged = merged.rename(columns={
        "implied_bps": "futures_implied_bps",
        "exp_month_bps": "kalshi_exp_month_bps"
    })
    merged["delta_bps"] = merged["futures_implied_bps"] - merged["kalshi_exp_month_bps"]
    cols = ["meeting_month","date","futures_implied_bps","kalshi_exp_month_bps","delta_bps"]
    return merged[cols]

def position_recommendation(delta_bps: float, threshold_bps: float = 2.0) -> str:
    if abs(delta_bps) < threshold_bps:
        return "No trade (gap below threshold)"
    if delta_bps > 0:
        return "SHORT Fed Funds futures; BUY no-hike/cut legs on Kalshi"
    return "LONG Fed Funds futures; BUY hike legs on Kalshi"
