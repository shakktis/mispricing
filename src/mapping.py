from __future__ import annotations
import pandas as pd
from datetime import datetime
from .utils import split_pre_post_days

def kalshi_expected_month_avg_from_json(kalshi_obj: dict) -> pd.DataFrame:
    """
    kalshi_obj: dict with keys:
      meeting_month (YYYY-MM), meeting_date (YYYY-MM-DD), R0_bps (int),
      dist: list of {rate_bps:int, prob:float}
    Returns a DataFrame with one row for that meeting.
    """
    meeting_month = kalshi_obj["meeting_month"]
    meeting_date = datetime.fromisoformat(kalshi_obj["meeting_date"]).date()
    R0_bps = int(kalshi_obj.get("R0_bps", 525))

    Dm, d_pre, d_post = split_pre_post_days(meeting_date)

    # expected post-meeting rate in bps
    exp_post_bps = 0.0
    for leg in kalshi_obj["dist"]:
        exp_post_bps += float(leg["rate_bps"]) * float(leg["prob"])

    exp_month_bps = (d_pre / Dm) * R0_bps + (d_post / Dm) * exp_post_bps

    return pd.DataFrame([{
        "meeting_month": meeting_month,
        "meeting_date": meeting_date,
        "Dm": Dm, "d_pre": d_pre, "d_post": d_post,
        "exp_post_bps": exp_post_bps,
        "exp_month_bps": exp_month_bps,
        "R0_bps": R0_bps
    }])
