# mispricing
# Kalshi ↔ Fed Funds Futures (ZQ) Dislocation Arb

Compares **Kalshi-implied post-FOMC rate distributions** with **Fed Funds Futures (CME ZQ)** to compute a mispricing signal Δ for each meeting month, then recommends aligned positions.

Quick start:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python examples/demo.py
