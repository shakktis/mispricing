from __future__ import annotations
import requests, datetime as dt
import pandas as pd

MONTH_CODE = {1:"F",2:"G",3:"H",4:"J",5:"K",6:"M",7:"N",8:"Q",9:"U",10:"V",11:"X",12:"Z"}

def zq_ticker_from_meeting_month(meeting_month: str, venue_prefix: str = "CME") -> str:
    year, month = meeting_month.split("-")
    y2 = year[-2:]
    code = MONTH_CODE[int(month)]
    core = f"ZQ{code}{y2}"
    return f"{venue_prefix}:{core}" if venue_prefix else core

def fetch_zq_prices_via_polygon(meeting_month: str, start_date: str, end_date: str, api_key: str) -> pd.DataFrame:
    """Fetch end-of-day aggregates for the ZQ contract via Polygon."""
    if not api_key:
        raise RuntimeError("Polygon API key is required.")
    ticker = zq_ticker_from_meeting_month(meeting_month)
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000, "apiKey": api_key}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    rows = []
    for rec in j.get("results", []):
        ts = int(rec["t"]) // 1000
        price = float(rec["c"])
        day = dt.datetime.utcfromtimestamp(ts).date().isoformat()
        rows.append({"meeting_month": meeting_month, "date": day, "price": price})
    return pd.DataFrame(rows)
