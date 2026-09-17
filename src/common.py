"""Shared utilities: config, history store, change/percentile math, status colors."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
HISTORY_COLUMNS = ["date", "indicator", "value", "as_of", "source", "is_stale", "fetched_at"]


def load_config() -> dict:
    with open(ROOT / "config" / "config.yaml") as f:
        return yaml.safe_load(f)


def history_path(cfg: dict) -> Path:
    return ROOT / cfg["history"]["path"]


def read_history(cfg: dict) -> pd.DataFrame:
    path = history_path(cfg)
    if not path.exists():
        return pd.DataFrame(columns=HISTORY_COLUMNS)
    df = pd.read_csv(path, parse_dates=["date", "as_of", "fetched_at"])
    return df


def write_history(cfg: dict, df: pd.DataFrame) -> None:
    path = history_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = df.sort_values(["indicator", "date"]).drop_duplicates(["indicator", "date"], keep="last")
    df.to_csv(path, index=False)


def upsert_history(cfg: dict, existing: pd.DataFrame, new_rows: pd.DataFrame) -> pd.DataFrame:
    if new_rows.empty:
        return existing
    combined = pd.concat([existing, new_rows], ignore_index=True)
    combined = combined.sort_values(["indicator", "date", "fetched_at"])
    combined = combined.drop_duplicates(["indicator", "date"], keep="last")
    write_history(cfg, combined)
    return combined


def latest_row(series_df: pd.DataFrame) -> pd.Series | None:
    if series_df.empty:
        return None
    return series_df.sort_values("date").iloc[-1]


def change_vs(series_df: pd.DataFrame, latest_value: float, latest_date: pd.Timestamp, days_back: int) -> float | None:
    """% change vs the closest observation at or before (latest_date - days_back)."""
    target = latest_date - pd.Timedelta(days=days_back)
    prior = series_df[series_df["date"] <= target]
    if prior.empty:
        return None
    prior_value = prior.sort_values("date").iloc[-1]["value"]
    if prior_value == 0:
        return None
    return (latest_value - prior_value) / abs(prior_value) * 100.0


def change_vs_ytd(series_df: pd.DataFrame, latest_value: float, latest_date: pd.Timestamp) -> float | None:
    jan1 = pd.Timestamp(year=latest_date.year, month=1, day=1)
    prior = series_df[series_df["date"] <= jan1]
    if prior.empty:
        prior = series_df[series_df["date"] >= jan1]
        if prior.empty:
            return None
        prior_value = prior.sort_values("date").iloc[0]["value"]
    else:
        prior_value = prior.sort_values("date").iloc[-1]["value"]
    if prior_value == 0:
        return None
    return (latest_value - prior_value) / abs(prior_value) * 100.0


def percentile_rank(series_df: pd.DataFrame, value: float, latest_date: pd.Timestamp, lookback_days: int) -> float | None:
    window_start = latest_date - pd.Timedelta(days=lookback_days)
    window = series_df[(series_df["date"] >= window_start) & (series_df["date"] <= latest_date)]
    if len(window) < 5:
        return None
    return (window["value"] <= value).mean() * 100.0


def sparkline_points(series_df: pd.DataFrame, latest_date: pd.Timestamp, lookback_days: int = 365) -> list[float]:
    window_start = latest_date - pd.Timedelta(days=lookback_days)
    window = series_df[(series_df["date"] >= window_start) & (series_df["date"] <= latest_date)].sort_values("date")
    return window["value"].tolist()


def now_utc() -> pd.Timestamp:
    return pd.Timestamp(dt.datetime.now(dt.timezone.utc))


def ordinal(n: float) -> str:
    n = int(round(n))
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def change_vs_ytd_abs(series_df: pd.DataFrame, latest_value: float, latest_date: pd.Timestamp) -> float | None:
    jan1 = pd.Timestamp(year=latest_date.year, month=1, day=1)
    prior = series_df[series_df["date"] <= jan1]
    if prior.empty:
        prior = series_df[series_df["date"] >= jan1]
        if prior.empty:
            return None
        prior_value = prior.sort_values("date").iloc[0]["value"]
    else:
        prior_value = prior.sort_values("date").iloc[-1]["value"]
    return latest_value - prior_value


def change_vs_abs(series_df: pd.DataFrame, latest_value: float, latest_date: pd.Timestamp, days_back: int) -> float | None:
    """Absolute (not %) change vs the closest observation at or before (latest_date - days_back).
    Use for rates/spreads/diffusion indices where percentage points or bp are the natural unit."""
    target = latest_date - pd.Timedelta(days=days_back)
    prior = series_df[series_df["date"] <= target]
    if prior.empty:
        return None
    prior_value = prior.sort_values("date").iloc[-1]["value"]
    return latest_value - prior_value


def derive_pct_change_series(level_df: pd.DataFrame, days: int, tolerance_days: int, annualize_periods: float | None = None) -> pd.DataFrame:
    """From a raw level series (e.g. CPI index), derive a %-change series (e.g. YoY inflation).

    For each observation at date t, finds the nearest prior observation at or before
    t - days (within tolerance_days, to tolerate monthly-data spacing) and computes the
    % change, optionally annualized (e.g. 3-month change annualized: annualize_periods=4).
    """
    if level_df.empty:
        return pd.DataFrame(columns=["date", "value"])
    lvl = level_df.sort_values("date").reset_index(drop=True)
    lvl["target_date"] = lvl["date"] - pd.Timedelta(days=days)
    merged = pd.merge_asof(
        lvl.sort_values("target_date"),
        lvl[["date", "value"]].rename(columns={"date": "prior_date", "value": "prior_value"}),
        left_on="target_date",
        right_on="prior_date",
        direction="backward",
        tolerance=pd.Timedelta(days=tolerance_days),
    )
    merged = merged.dropna(subset=["prior_value"])
    ratio = merged["value"] / merged["prior_value"]
    if annualize_periods:
        merged["value"] = (ratio ** annualize_periods - 1) * 100.0
    else:
        merged["value"] = (ratio - 1) * 100.0
    return merged.sort_values("date")[["date", "value"]].reset_index(drop=True)
