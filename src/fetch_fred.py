"""FRED API fetchers. Requires FRED_API_KEY. Never raises — returns empty df on failure."""
from __future__ import annotations

import logging
import os

import pandas as pd
import requests

logger = logging.getLogger(__name__)

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fred_series(series_id: str, api_key: str, start_date: str = "2015-01-01") -> pd.DataFrame:
    try:
        resp = requests.get(
            FRED_URL,
            params={
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start_date,
            },
            timeout=20,
        )
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        if not obs:
            raise ValueError(f"FRED returned no observations for {series_id}")
        df = pd.DataFrame(obs)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])[["date", "value"]]
        return df
    except Exception as e:  # noqa: BLE001 - one failing source must never break the run
        logger.warning("FRED fetch failed for %s: %s", series_id, e)
        return pd.DataFrame(columns=["date", "value"])


def fetch_all_fred(series_map: dict[str, str], existing_history: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Returns {indicator_key: DataFrame[date, value]}. Empty df + logged warning if
    FRED_API_KEY is missing or a given series fails — caller falls back to last good value."""
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    results: dict[str, pd.DataFrame] = {}
    if not api_key:
        logger.warning("FRED_API_KEY not set — skipping %d FRED-backed indicators, will show stale/last-known values", len(series_map))
        return {key: pd.DataFrame(columns=["date", "value"]) for key in series_map}

    for key, series_id in series_map.items():
        has_history = key in set(existing_history["indicator"])
        start = "2015-01-01" if not has_history else (pd.Timestamp.today() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
        results[key] = fetch_fred_series(series_id, api_key, start_date=start)
    return results
