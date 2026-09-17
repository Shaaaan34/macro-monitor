"""FRED fetcher tests. Requires FRED_API_KEY in the environment to hit the live
API; without it we assert the graceful no-key fallback instead of failing the run."""
import os

import pandas as pd
import pytest

from src.fetch_fred import fetch_fred_series

PLAUSIBLE_RANGES = {
    "DGS10": (0, 20),          # 10Y yield, %
    "CPIAUCSL": (50, 500),     # CPI index level
    "BAMLH0A0HYM2": (0, 30),  # HY OAS, %
}


@pytest.mark.skipif(not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set")
@pytest.mark.parametrize("series_id", list(PLAUSIBLE_RANGES.keys()))
def test_fred_series_returns_plausible_data(series_id):
    api_key = os.environ["FRED_API_KEY"]
    df = fetch_fred_series(series_id, api_key)
    assert not df.empty, f"FRED returned no data for {series_id}"
    latest = df.sort_values("date").iloc[-1]["value"]
    lo, hi = PLAUSIBLE_RANGES[series_id]
    assert lo <= latest <= hi, f"{series_id} latest value {latest} outside plausible range [{lo}, {hi}]"


def test_fred_bad_key_fails_gracefully():
    df = fetch_fred_series("DGS10", api_key="invalid-key-xyz")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
