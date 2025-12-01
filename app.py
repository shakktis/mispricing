
---

### `app.py`
```python
import streamlit as st
import pandas as pd
import requests
from datetime import date

from src.mapping import kalshi_expected_month_avg_from_json
from src.futures import implied_from_prices
from src.signal import compute_signal, position_recommendation
from src.polygon import fetch_zq_prices_via_polygon

st.set_page_config(page_title="Kalshi ↔ Fed Funds Futures Gap", page_icon="📈", layout="centered")
st.title("Kalshi ↔ Fed Funds Futures (ZQ) Dislocation")
st.caption("Paste your Polygon key; load Kalshi from a public JSON URL or upload a file. Keys are used only in your session.")

# Inputs
poly_key = st.text_input("Polygon API Key", type="password")
meeting_month = st.text_input("Meeting month (YYYY-MM)", "2025-09")
colA, colB = st.columns(2)
start = colA.text_input("Start date (YYYY-MM-DD)", "2025-08-01")
end   = colB.text_input("End date (YYYY-MM-DD)", "2025-09-30")

st.subheader("Kalshi distribution source")
kalshi_url = st.text_input("Kalshi JSON URL (optional if uploading a file)", "")
uploaded = st.file_uploader("...or upload a Kalshi JSON file", type=["json"])

# R0 (pre-meeting policy rate, bps)
r0_bps = st.number_input("Pre-meeting policy rate (R0, bps)", min_value=0, max_value=10000, value=525)

def load_kalshi_obj():
    if kalshi_url:
        r = requests.get(kalshi_url, timeout=20)
        r.raise_for_status()
        data = r.json()
    elif uploaded is not None:
        import json
        data = json.loads(uploaded.read().decode("utf-8"))
    else:
        st.error("Provide a Kalshi JSON URL or upload a JSON file.")
        st.stop()

    # Accept either a single object or a list; pick the one matching meeting_month
    if isinstance(data, list):
        for obj in data:
            if obj.get("meeting_month") == meeting_month:
                return obj
        st.error(f"No entry for meeting_month={meeting_month} in the provided JSON.")
        st.stop()
    elif isinstance(data, dict):
        if data.get("meeting_month") != meeting_month:
            st.warning("Single JSON object provided; its meeting_month differs from input.")
        return data
    else:
        st.error("Kalshi JSON must be an object or a list of objects.")
        st.stop()

if st.button("Compute gap"):
    if not poly_key:
        st.error("Please paste your Polygon API key.")
        st.stop()

    kalshi_obj = load_kalshi_obj()
    # Ensure R0 is set from UI if not present
    kalshi_obj["R0_bps"] = int(r0_bps)

    # Kalshi → expected month average
    k_month = kalshi_expected_month_avg_from_json(kalshi_obj)
    st.write("Kalshi expectation (bps):", k_month[["meeting_month","meeting_date","exp_post_bps","exp_month_bps","R0_bps"]])

    # Polygon ZQ pulls
    zq = fetch_zq_prices_via_polygon(meeting_month, start, end, api_key=poly_key)
    if zq.empty:
        st.warning("No Polygon ZQ data returned for the selected range.")
        st.stop()
    zq_imp = implied_from_prices(zq)

    # Compute Δ
    signals = compute_signal(zq_imp, k_month)
    signals["recommendation"] = signals["delta_bps"].apply(lambda d: position_recommendation(d, 2.0))

    st.subheader("Signals")
    st.dataframe(signals)

    st.subheader("Gap (bps) over time")
    st.line_chart(signals.set_index("date")["delta_bps"])

    # Save CSV for download
    st.download_button("Download signals CSV", data=signals.to_csv(index=False), file_name="signals.csv", mime="text/csv")

    st.info("Rule of thumb: act only if |Δ| ≥ costs + safety buffer (e.g., ≥ 2 bps).")
