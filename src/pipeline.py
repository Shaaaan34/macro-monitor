"""Fetch -> store history -> compute changes/status -> render dashboard. Entry point: run.py"""
from __future__ import annotations

import logging

import pandas as pd

from . import common, fetch_fred, fetch_market
from .indicators import INDICATOR_REGISTRY, forecast_text, status_for

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

TICKER_KEYS = {ind["key"] for ind in INDICATOR_REGISTRY if ind["category"] == "ticker_level"}
FRED_LEVEL_YOY_KEYS = {ind["key"]: {"cpi_headline": "cpi_headline", "cpi_core": "cpi_core"}[ind["key"]]
                       for ind in INDICATOR_REGISTRY if ind["category"] == "fred_level_yoy"}
FRED_RATE_KEYS = {ind["key"] for ind in INDICATOR_REGISTRY if ind["category"] == "fred_rate"}
FRED_DIFFUSION_KEYS = {ind["key"] for ind in INDICATOR_REGISTRY if ind["category"] == "fred_diffusion"}
FRED_DIRECT_KEYS = FRED_RATE_KEYS | FRED_DIFFUSION_KEYS  # stored directly, no derived transform


def run_pipeline() -> dict:
    cfg = common.load_config()
    thresholds = cfg["thresholds"]
    history = common.read_history(cfg)

    # --- fetch ---
    ticker_new = fetch_market.fetch_all_tickers(cfg["tickers"], history)

    fred_direct_series_map = {k: v for k, v in cfg["fred_series"].items() if k in FRED_DIRECT_KEYS}
    fred_yoy_series_map = {k: v for k, v in cfg["fred_series"].items() if k in FRED_LEVEL_YOY_KEYS}
    fred_new = fetch_fred.fetch_all_fred({**fred_direct_series_map, **fred_yoy_series_map}, history)

    # --- upsert raw fetched values into history (levels, as fetched) ---
    fetched_at = common.now_utc()
    new_rows = []
    for key, df in {**ticker_new, **fred_new}.items():
        if df.empty:
            continue
        df = df.copy()
        df["indicator"] = key
        df["as_of"] = df["date"]
        df["source"] = next((i["source"] for i in INDICATOR_REGISTRY if i["key"] == key), "unknown")
        df["is_stale"] = False
        df["fetched_at"] = fetched_at
        new_rows.append(df[list(common.HISTORY_COLUMNS)])

    if new_rows:
        history = common.upsert_history(cfg, history, pd.concat(new_rows, ignore_index=True))
    else:
        logger.warning("No new data fetched this run — dashboard will show last known values as stale")

    # --- build cards ---
    cards = []
    missing = []

    for ind in INDICATOR_REGISTRY:
        key = ind["key"]
        raw_series = history[history["indicator"] == key][["date", "value"]].sort_values("date")

        if raw_series.empty:
            missing.append(f"{ind['label']} ({ind['source']}): no data ever retrieved")
            cards.append(_stale_card(ind, "never retrieved"))
            continue

        if ind["category"] == "fred_level_yoy":
            series_df = common.derive_pct_change_series(raw_series, days=365, tolerance_days=20)
            extra_3m = common.derive_pct_change_series(raw_series, days=91, tolerance_days=15, annualize_periods=4)
            if series_df.empty:
                missing.append(f"{ind['label']}: not enough history yet to compute YoY")
                cards.append(_stale_card(ind, "insufficient history for YoY"))
                continue
        else:
            series_df = raw_series
            extra_3m = None

        latest = common.latest_row(series_df)
        latest_value = float(latest["value"])
        latest_date = latest["date"]

        raw_latest = common.latest_row(raw_series)
        as_of_date = raw_latest["date"]
        days_stale = (pd.Timestamp.now().normalize() - as_of_date.normalize()).days
        # daily/intraday series: stale if no new obs in 5+ days (only weekends/holidays
        # should cause gaps that big). Monthly releases are normal up to ~45 days old.
        stale_after = 5 if ind.get("cadence", "daily") == "daily" else 45
        is_stale = days_stale > stale_after

        change_unit = ind.get("change_unit", "pct")
        if change_unit == "pct":
            chg_1d = common.change_vs(series_df, latest_value, latest_date, 1)
            chg_1w = common.change_vs(series_df, latest_value, latest_date, 7)
            chg_1m = common.change_vs(series_df, latest_value, latest_date, 30)
            chg_ytd = common.change_vs_ytd(series_df, latest_value, latest_date)
        else:
            # "pp" (percentage points) or "pts" (index points): absolute change, not relative %
            chg_1d = common.change_vs_abs(series_df, latest_value, latest_date, 1)
            chg_1w = common.change_vs_abs(series_df, latest_value, latest_date, 7)
            chg_1m = common.change_vs_abs(series_df, latest_value, latest_date, 30)
            chg_ytd = common.change_vs_ytd_abs(series_df, latest_value, latest_date)

        pctile_1y = common.percentile_rank(series_df, latest_value, latest_date, 365)
        pctile_5y = common.percentile_rank(series_df, latest_value, latest_date, 365 * 5)
        spark = common.sparkline_points(series_df, latest_date, 365)

        # status color uses different bases per indicator type (see indicators.status_for)
        if key in ("sp500", "sp500_futures", "nasdaq100", "nasdaq_composite", "nasdaq_futures"):
            status_input = chg_1d
        elif key == "dgs10":
            status_input = common.change_vs_abs(series_df, latest_value, latest_date, 30)
            if status_input is not None:
                status_input = status_input * 100  # percentage points -> bp
        elif key in ("vix",):
            status_input = None  # vix uses raw level, not a change
        else:
            status_input = chg_1m

        color, reason = status_for(key, latest_value, status_input, thresholds)

        card = {
            **ind,
            "value": latest_value,
            "as_of_date": as_of_date,
            "days_stale": days_stale,
            "is_stale": is_stale,
            "chg_1d": chg_1d,
            "chg_1w": chg_1w,
            "chg_1m": chg_1m,
            "chg_ytd": chg_ytd,
            "change_unit": change_unit,
            "pctile_1y": pctile_1y,
            "pctile_5y": pctile_5y,
            "sparkline": spark,
            "color": color,
            "reason": reason,
            "extra_3m_annualized": (float(common.latest_row(extra_3m)["value"])
                                     if extra_3m is not None and not extra_3m.empty else None),
        }
        card["forecast"] = forecast_text(card)
        cards.append(card)

    if not missing:
        missing.append("Nothing — all configured indicators returned data this run.")

    tldr = build_tldr(cards)

    return {"cfg": cfg, "cards": cards, "missing": missing, "history": history,
            "generated_at": fetched_at, "tldr": tldr}


def build_tldr(cards: list[dict]) -> dict:
    """Plain-English top-of-page summary. Purely a mechanical readout of the
    cards already computed above (status colors + recent trend) — not a
    prediction and not investment advice."""
    scored = [c for c in cards if c["value"] is not None and not c.get("context_only")]
    reds = [c for c in scored if c["color"] == "red"]
    ambers = [c for c in scored if c["color"] == "amber"]
    greens = [c for c in scored if c["color"] == "green"]

    if len(reds) >= 2:
        headline = "Risk-off tilt: multiple indicators are outside normal ranges and flashing stress."
    elif len(reds) == 1:
        headline = f"Mostly calm, but {reds[0]['label']} is flashing stress — worth watching."
    elif scored and len(ambers) >= len(scored) / 2:
        headline = "Mixed backdrop: several indicators are elevated, but none are at stress levels."
    elif scored:
        headline = "Calm backdrop: most indicators are within normal ranges today."
    else:
        headline = "No scored data available this run."

    flagged = sorted(reds + ambers, key=lambda c: abs(c["chg_1m"]) if c["chg_1m"] is not None else 0, reverse=True)
    bullets = [
        f"{c['label']} ({c['area']}): {c['plain_english']} Right now: {c['reason']}."
        for c in flagged[:4]
    ]

    caveats = []
    stale = [c for c in cards if c["is_stale"]]
    proxies = [c for c in cards if c.get("proxy")]
    if stale:
        caveats.append("Stale/last-known data: " + ", ".join(c["label"] for c in stale))
    if proxies:
        caveats.append("Proxies in use (no free official source exists): " + ", ".join(c["label"] for c in proxies))

    return {
        "headline": headline,
        "bullets": bullets,
        "caveats": caveats,
        "counts": {"red": len(reds), "amber": len(ambers), "green": len(greens)},
    }


def _stale_card(ind: dict, reason: str) -> dict:
    return {
        **ind, "value": None, "as_of_date": None, "days_stale": None, "is_stale": True,
        "chg_1d": None, "chg_1w": None, "chg_1m": None, "chg_ytd": None,
        "change_unit": ind.get("change_unit", "pct"),
        "pctile_1y": None, "pctile_5y": None, "sparkline": [], "color": "grey",
        "reason": f"source failed — {reason}", "extra_3m_annualized": None, "forecast": "No data",
    }
