"""Indicator registry for phase 1's core 10 areas, and status-color logic."""
from __future__ import annotations

# category values: "ticker_level", "fred_level_yoy", "fred_rate", "fred_diffusion"
# cadence: "daily" (stale if >5 days without a new obs) or "monthly" (stale if >45 days)
# change_unit: "pct" = relative % change (appropriate for price levels);
#              "pp" = absolute percentage-point change (rates/spreads/YoY%);
#              "pts" = absolute index-point change (diffusion indices)
INDICATOR_REGISTRY = [
    {"key": "vix", "label": "VIX", "area": "Market fear", "category": "ticker_level",
     "unit": "", "decimals": 1, "source": "yfinance ^VIX", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "Wall Street's “fear gauge.” Rises when investors expect bigger price swings ahead."},

    {"key": "wti", "label": "WTI crude", "area": "Oil", "category": "ticker_level",
     "unit": "$", "decimals": 2, "source": "yfinance CL=F", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "US oil price. Feeds into gas prices, shipping costs, and inflation."},
    {"key": "brent", "label": "Brent crude", "area": "Oil", "category": "ticker_level",
     "unit": "$", "decimals": 2, "source": "yfinance BZ=F", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "Global oil benchmark price — same effects as WTI, more international."},

    {"key": "philly_fed", "label": "Philly Fed general activity", "area": "Economic growth (PMI proxy)",
     "category": "fred_diffusion", "unit": "", "decimals": 1, "source": "FRED GACDFSA066MSFRBPHI",
     "proxy": True, "proxy_note": "Proxy for ISM Manufacturing PMI — no free official ISM API",
     "cadence": "monthly", "change_unit": "pts",
     "plain_english": "Survey of Philadelphia-area factory bosses — more are seeing growth (positive) or shrinking business (negative)?"},
    {"key": "empire_state", "label": "Empire State general business conditions", "area": "Economic growth (PMI proxy)",
     "category": "fred_diffusion", "unit": "", "decimals": 1, "source": "FRED GACDISA066MSFRBNY",
     "proxy": True, "proxy_note": "Proxy for ISM Manufacturing PMI — no free official ISM API",
     "cadence": "monthly", "change_unit": "pts",
     "plain_english": "Same idea, for New York-area manufacturers."},

    {"key": "hy_oas", "label": "US HY credit spread (OAS)", "area": "Recession risk", "category": "fred_rate",
     "unit": "%", "decimals": 2, "source": "FRED BAMLH0A0HYM2", "proxy": False,
     "cadence": "daily", "change_unit": "pp",
     "plain_english": "Extra interest investors demand to lend to riskier (“junk-rated”) companies vs. the US government. Widens when investors get nervous about defaults."},
    {"key": "ig_oas", "label": "US IG credit spread (OAS)", "area": "Recession risk", "category": "fred_rate",
     "unit": "%", "decimals": 2, "source": "FRED BAMLC0A0CM", "proxy": False, "context_only": True,
     "cadence": "daily", "change_unit": "pp",
     "plain_english": "Same idea, for safer investment-grade companies. Shown for context only."},

    {"key": "sp500", "label": "S&P 500", "area": "US stocks", "category": "ticker_level",
     "unit": "", "decimals": 2, "source": "yfinance ^GSPC", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "The 500 largest US public companies — the most-watched US stock market gauge."},
    {"key": "sp500_futures", "label": "S&P 500 futures", "area": "US stocks", "category": "ticker_level",
     "unit": "", "decimals": 2, "source": "yfinance ES=F", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "Where S&P 500 traders expect the market to open, based on overnight bets."},

    {"key": "nasdaq100", "label": "Nasdaq 100", "area": "Tech", "category": "ticker_level",
     "unit": "", "decimals": 2, "source": "yfinance ^NDX", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "The 100 largest non-financial companies on the Nasdaq — tech-heavy."},
    {"key": "nasdaq_composite", "label": "Nasdaq Composite", "area": "Tech", "category": "ticker_level",
     "unit": "", "decimals": 2, "source": "yfinance ^IXIC", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "All Nasdaq-listed stocks — broader tech-market gauge."},
    {"key": "nasdaq_futures", "label": "Nasdaq futures", "area": "Tech", "category": "ticker_level",
     "unit": "", "decimals": 2, "source": "yfinance NQ=F", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "Where Nasdaq traders expect the market to open."},

    {"key": "cpi_headline", "label": "CPI headline (YoY)", "area": "US inflation", "category": "fred_level_yoy",
     "unit": "%", "decimals": 2, "source": "FRED CPIAUCSL", "proxy": False,
     "cadence": "monthly", "change_unit": "pp",
     "plain_english": "Official US inflation rate — how much pricier a typical basket of goods is than a year ago."},
    {"key": "cpi_core", "label": "CPI core (YoY)", "area": "US inflation", "category": "fred_level_yoy",
     "unit": "%", "decimals": 2, "source": "FRED CPILFESL", "proxy": False,
     "cadence": "monthly", "change_unit": "pp",
     "plain_english": "Same as headline CPI, excluding volatile food and energy prices."},

    {"key": "dgs10", "label": "10-Year Treasury yield", "area": "US rates", "category": "fred_rate",
     "unit": "%", "decimals": 2, "source": "FRED DGS10", "proxy": False,
     "cadence": "daily", "change_unit": "pp",
     "plain_english": "What the US government pays to borrow for 10 years. Moves the price of mortgages and company borrowing everywhere."},

    {"key": "dxy", "label": "US Dollar Index (DXY)", "area": "US dollar", "category": "ticker_level",
     "unit": "", "decimals": 2, "source": "yfinance DX-Y.NYB", "proxy": False,
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "Strength of the US dollar against a basket of other major currencies."},

    {"key": "baltic_dry_proxy", "label": "Baltic Dry Index (proxy)", "area": "Global trade", "category": "ticker_level",
     "unit": "$", "decimals": 2, "source": "yfinance BDRY", "proxy": True,
     "proxy_note": "BDRY ETF used as proxy — no free official Baltic Dry Index API",
     "cadence": "daily", "change_unit": "pct",
     "plain_english": "Proxy for global shipping demand — more goods moving around the world tends to push this up."},
]


def forecast_text(card: dict) -> str:
    """Mechanical, rule-based read of level + recent trend. Describes the current
    trajectory from already-observed data — it is not a prediction of future
    prices and carries no investment view."""
    if card.get("value") is None:
        return "No data"

    color_word = {"green": "Calm", "amber": "Elevated", "red": "Stressed", "grey": "Unclear"}[card["color"]]

    chg_1w, chg_1m = card.get("chg_1w"), card.get("chg_1m")
    if chg_1w is not None and chg_1m is not None:
        if chg_1w > 0 and chg_1m > 0:
            trend = "rising"
        elif chg_1w < 0 and chg_1m < 0:
            trend = "falling"
        else:
            trend = "mixed"
    elif chg_1m is not None:
        trend = "rising" if chg_1m > 0 else ("falling" if chg_1m < 0 else "flat")
    else:
        trend = "trend n/a"

    pctile_1y = card.get("pctile_1y")
    extremity = ""
    if pctile_1y is not None:
        if pctile_1y >= 90:
            extremity = "; near a 1y high"
        elif pctile_1y <= 10:
            extremity = "; near a 1y low"

    return f"{color_word}, {trend}{extremity}"


def status_for(key: str, value: float, one_month_change_pct: float | None, thresholds: dict) -> tuple[str, str]:
    """Returns (color, reason) where color in {green, amber, red, grey}."""
    t = thresholds

    if key == "vix":
        th = t["vix"]
        if value < th["green_below"]:
            return "green", f"VIX {value:.1f} < {th['green_below']} (calm)"
        if value > th["red_above"]:
            return "red", f"VIX {value:.1f} > {th['red_above']} (stressed)"
        return "amber", f"VIX {value:.1f} in elevated band ({th['green_below']}-{th['red_above']})"

    if key == "hy_oas":
        th = t["hy_oas_pct"]
        if value < th["green_below"]:
            return "green", f"HY OAS {value:.2f}% < {th['green_below']}% (calm credit)"
        if value > th["red_above"]:
            return "red", f"HY OAS {value:.2f}% > {th['red_above']}% (credit stress)"
        return "amber", f"HY OAS {value:.2f}% in elevated band"

    if key == "ig_oas":
        th = t["ig_oas_pct"]
        if value < th["green_below"]:
            return "green", f"IG OAS {value:.2f}% tight (context only)"
        if value > th["red_above"]:
            return "red", f"IG OAS {value:.2f}% wide (context only)"
        return "amber", f"IG OAS {value:.2f}% normal-to-wide (context only)"

    if key in ("cpi_headline", "cpi_core"):
        th = t["cpi_yoy_pct"]
        if value is None:
            return "grey", "YoY not computable yet"
        if value < th["green_below"]:
            return "green", f"CPI YoY {value:.2f}% near Fed target"
        if value > th["red_above"]:
            return "red", f"CPI YoY {value:.2f}% well above target"
        return "amber", f"CPI YoY {value:.2f}% above target"

    if key in ("wti", "brent"):
        th = t["oil_1m_change_pct"]
        if one_month_change_pct is None:
            return "grey", "1-month change not available yet"
        a = abs(one_month_change_pct)
        if a > th["red_abs"]:
            return "red", f"1m move {one_month_change_pct:+.1f}% (shock-level)"
        if a > th["amber_abs"]:
            return "amber", f"1m move {one_month_change_pct:+.1f}% (elevated)"
        return "green", f"1m move {one_month_change_pct:+.1f}% (calm)"

    if key in ("sp500", "sp500_futures", "nasdaq100", "nasdaq_composite", "nasdaq_futures"):
        # uses 1-day change, passed in as one_month_change_pct slot by caller convention below
        th = t["equity_futures_move_pct"]
        if one_month_change_pct is None:
            return "grey", "1-day change not available yet"
        a = abs(one_month_change_pct)
        if a > th["red_abs"]:
            return "red", f"1d move {one_month_change_pct:+.2f}% (large)"
        if a > th["amber_abs"]:
            return "amber", f"1d move {one_month_change_pct:+.2f}% (notable)"
        return "green", f"1d move {one_month_change_pct:+.2f}% (calm)"

    if key == "dxy":
        th = t["dxy_1m_change_pct"]
        if one_month_change_pct is None:
            return "grey", "1-month change not available yet"
        a = abs(one_month_change_pct)
        if a > th["red_abs"]:
            return "red", f"1m move {one_month_change_pct:+.1f}% (large FX move)"
        if a > th["amber_abs"]:
            return "amber", f"1m move {one_month_change_pct:+.1f}% (notable)"
        return "green", f"1m move {one_month_change_pct:+.1f}% (calm)"

    if key == "baltic_dry_proxy":
        th = t["baltic_dry_1m_change_pct"]
        if one_month_change_pct is None:
            return "grey", "1-month change not available yet"
        a = abs(one_month_change_pct)
        if a > th["red_abs"]:
            return "red", f"1m move {one_month_change_pct:+.1f}% (large shipping-demand shift)"
        if a > th["amber_abs"]:
            return "amber", f"1m move {one_month_change_pct:+.1f}% (notable)"
        return "green", f"1m move {one_month_change_pct:+.1f}% (calm)"

    if key == "dgs10":
        th = t["dgs10_1m_change_bp"]
        if one_month_change_pct is None:
            return "grey", "1-month change not available yet"
        bp = one_month_change_pct  # caller passes bp change directly for dgs10
        a = abs(bp)
        if a > th["red_abs"]:
            return "red", f"1m move {bp:+.0f}bp (large repricing)"
        if a > th["amber_abs"]:
            return "amber", f"1m move {bp:+.0f}bp (notable)"
        return "green", f"1m move {bp:+.0f}bp (calm)"

    if key in ("philly_fed", "empire_state"):
        th = t["pmi_proxy"]
        if value > th["green_above"]:
            return "green", f"{value:.1f} > 0 (expansion-leaning, proxy)"
        if value < th["red_below"]:
            return "red", f"{value:.1f} < {th['red_below']} (sharply contractionary, proxy)"
        return "amber", f"{value:.1f} contraction-leaning (proxy)"

    return "grey", "no status rule defined"
