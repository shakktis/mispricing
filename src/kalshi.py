from __future__ import annotations
import os, re, requests, datetime as dt
import pandas as pd
from calendar import month_name

# Optional: set KALSHI_API_TOKEN in env; we’ll send it as Bearer if present.
KALSHI_BASE = os.getenv("KALSHI_BASE_URL", "https://trading-api.kalshi.com/v1")

def _auth_headers(token: str | None) -> dict:
    tok = token or os.getenv("KALSHI_API_TOKEN")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

# Parse "5.25%" / "525 bps" → 525
_rate_pat = re.compile(r"(\d+)(?:[.\-](\d{1,2}))?")

def _parse_rate_bps(txt: str) -> int | None:
    s = txt.replace(",", "").replace("bp","").replace("bps","").replace("%","").strip()
    if s.isdigit() and int(s) > 50:
        return int(s)
    m = _rate_pat.search(s)
    if not m:
        return None
    whole = int(m.group(1))
    frac  = m.group(2)
    return whole*100 + (int(frac) if frac else 0)

def _event_search(query: str, token: str | None) -> dict:
    url = f"{KALSHI_BASE}/events?limit=50&search={requests.utils.quote(query)}"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()
    data = r.json()
    evts = data.get("events") or data.get("data") or []
    return evts[0] if evts else {}

def _get_markets_for_event(event_ticker: str, token: str | None) -> list[dict]:
    url = f"{KALSHI_BASE}/markets?event_ticker={event_ticker}&limit=200"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("markets") or data.get("data") or []

def _get_orderbook(market_ticker: str, token: str | None) -> dict:
    url = f"{KALSHI_BASE}/markets/{market_ticker}/orderbook"
    r = requests.get(url, headers=_auth_headers(token), timeout=20)
    r.raise_for_status()
    return r.json()

def _best_mid_cents(book: dict) -> float | None:
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    bb = float(bids[0]["price"]) if bids else None
    ba = float(asks[0]["price"]) if asks else None
    if bb is not None and ba is not None:
        return 0.5*(bb+ba)
    return bb if bb is not None else ba

def monthname_from_yyyy_mm(meeting_month: str) -> str:
    y, m = meeting_month.split("-")
    return f"{month_name[int(m)]} {y}"

def fetch_kalshi_distribution(meeting_month: str, token: str | None = None) -> pd.DataFrame:
    """
    Build a probability distribution over post-meeting target rates for the FOMC meeting in `meeting_month` (YYYY-MM).
    Returns DataFrame: [meeting_month, meeting_date, rate_bps, prob]
    """
    # Heuristic: search "FOMC <MonthName YYYY>"
    query = f"FOMC {monthname_from_yyyy_mm(meeting_month)}"
    evt = _event_search(query, token)
    if not evt:
        raise RuntimeError(f"No Kalshi event found for query: {query}")
    event_tkr = evt.get("ticker") or evt.get("event_ticker") or ""
    close_ts  = evt.get("close_time") or evt.get("end_time")  # ISO8601
    try:
        meeting_date = dt.datetime.fromisoformat((close_ts or "").replace("Z","")).date()
    except Exception:
        # fall back: mid-month guess if missing
        y, m = map(int, meeting_month.split("-"))
        meeting_date = dt.date(y, m, 15)

    markets = _get_markets_for_event(event_tkr, token)
    rows = []
    for mkt in markets:
        mtkr  = mkt.get("ticker") or mkt.get("market_ticker")
        title = (mkt.get("title") or mkt.get("name") or "").strip()
        rate  = _parse_rate_bps(title)
        if rate is None:
            continue
        # get orderbook mid, fallback to last price
        mid = None
        try:
            ob = _get_orderbook(mtkr, token)
            mid = _best_mid_cents(ob)
        except Exception:
            pass
        if mid is None:
            last_px = mkt.get("last_price") or mkt.get("last_trade_price")
            if last_px is not None:
                mid = float(last_px)
        if mid is None:
            continue
        prob = max(0.0, min(1.0, mid/100.0))
        rows.append({
            "meeting_month": meeting_month,
            "meeting_date": meeting_date,
            "rate_bps": int(rate),
            "prob": float(prob),
        })
    if not rows:
        raise RuntimeError("No priced outcome legs found for this event.")
    df = pd.DataFrame(rows)
    s = df["prob"].sum()
    if s > 0:
        df["prob"] = df["prob"] / s
    return df
