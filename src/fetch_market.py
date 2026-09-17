"""yfinance-backed fetchers for market tickers (VIX, oil, equities, DXY, BDRY)."""
from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_ticker_history(ticker: str, existing_dates: set[pd.Timestamp]) -> pd.DataFrame:
    """Return a DataFrame[date, value] for a ticker.

    Backfills 5y of daily closes if we have no history for it yet; otherwise
    only pulls the last 40 days (buffer for weekends/holidays/late fills).
    """
    period = "5y" if not existing_dates else "40d"
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval="1d", auto_adjust=False)
        if hist.empty:
            raise ValueError(f"yfinance returned empty history for {ticker}")
        hist = hist.reset_index()
        hist["date"] = pd.to_datetime(hist["Date"]).dt.tz_localize(None).dt.normalize()
        out = hist[["date", "Close"]].rename(columns={"Close": "value"})
        out = out.dropna(subset=["value"])
        return out
    except Exception as e:  # noqa: BLE001 - one failing source must never break the run
        logger.warning("yfinance fetch failed for %s: %s", ticker, e)
        return pd.DataFrame(columns=["date", "value"])


def fetch_all_tickers(tickers: dict[str, str], existing_history: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Returns {indicator_key: DataFrame[date, value]} of NEW rows only (caller upserts)."""
    results: dict[str, pd.DataFrame] = {}
    for key, ticker in tickers.items():
        existing_dates = set(existing_history.loc[existing_history["indicator"] == key, "date"])
        df = fetch_ticker_history(ticker, existing_dates)
        results[key] = df
    return results
