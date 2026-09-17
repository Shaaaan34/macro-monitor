"""Fetcher tests: returns data, and the value is in a plausible range.

These hit the live yfinance/FRED APIs (per the project's data-source design, we
verify real endpoints rather than mock them) — skipped automatically if offline.
"""
import pandas as pd
import pytest

from src.fetch_market import fetch_ticker_history

PLAUSIBLE_RANGES = {
    "^VIX": (5, 100),
    "CL=F": (-50, 250),   # WTI went briefly negative in 2020; keep the floor wide
    "BZ=F": (0, 250),
    "^GSPC": (1000, 15000),
    "DX-Y.NYB": (50, 150),
    "BDRY": (5, 200),
}


@pytest.mark.parametrize("ticker", list(PLAUSIBLE_RANGES.keys()))
def test_ticker_returns_plausible_data(ticker):
    df = fetch_ticker_history(ticker, existing_dates=set())
    if df.empty:
        pytest.skip(f"no network / yfinance unavailable for {ticker}")
    assert "date" in df.columns and "value" in df.columns
    assert len(df) > 0
    latest = df.sort_values("date").iloc[-1]["value"]
    lo, hi = PLAUSIBLE_RANGES[ticker]
    assert lo <= latest <= hi, f"{ticker} latest value {latest} outside plausible range [{lo}, {hi}]"


def test_bad_ticker_fails_gracefully():
    df = fetch_ticker_history("NOT-A-REAL-TICKER-XYZ", existing_dates=set())
    assert isinstance(df, pd.DataFrame)
    assert df.empty
