"""Renders the single self-contained HTML dashboard from pipeline output."""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import pandas_market_calendars as mcal

from .common import ordinal

ROOT = Path(__file__).resolve().parent.parent

COLOR_HEX = {"green": "#2ecc71", "amber": "#f39c12", "red": "#e74c3c", "grey": "#7f8c8d"}


def _fmt(value, decimals, unit):
    if value is None:
        return "UNVERIFIED"
    sign = "" if unit != "$" else "$"
    return f"{sign}{value:,.{decimals}f}{'%' if unit == '%' else ''}"


def _fmt_change(value, unit="pct"):
    if value is None:
        return "—"
    if unit == "pp":
        return f"{value * 100:+.0f}bp" if abs(value) < 1 else f"{value:+.2f}pp"
    if unit == "pts":
        return f"{value:+.1f}pt"
    return f"{value:+.2f}%"


def _sparkline_svg(points: list[float], color: str, width=200, height=40) -> str:
    if len(points) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'
    lo, hi = min(points), max(points)
    span = (hi - lo) or 1.0
    n = len(points)
    coords = []
    for i, v in enumerate(points):
        x = (i / (n - 1)) * (width - 4) + 2
        y = height - 2 - ((v - lo) / span) * (height - 4)
        coords.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(coords)
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linejoin="round" stroke-linecap="round"/></svg>')


def _market_banner(local_tz: str) -> tuple[str, bool]:
    nyse = mcal.get_calendar("NYSE")
    now_et = pd.Timestamp.now(tz="America/New_York")
    today = now_et.normalize().tz_localize(None)
    schedule = nyse.schedule(start_date=today - pd.Timedelta(days=5), end_date=today + pd.Timedelta(days=1))
    is_trading_day = today in schedule.index
    if not is_trading_day:
        return "US market closed today (holiday/weekend)", False
    open_t = schedule.loc[today, "market_open"].tz_convert("America/New_York")
    close_t = schedule.loc[today, "market_close"].tz_convert("America/New_York")
    if now_et < open_t:
        mins = int((open_t - now_et).total_seconds() // 60)
        return f"Market opens in {mins} min ({open_t.strftime('%H:%M')} ET)", True
    if now_et > close_t:
        return "Market closed for the day", True
    return "Market open", True


def _card_html(card: dict) -> str:
    color = COLOR_HEX[card["color"]]
    label = html.escape(card["label"])
    proxy_badge = (f'<span class="badge proxy" title="{html.escape(card.get("proxy_note",""))}">PROXY</span>'
                   if card.get("proxy") else "")
    context_badge = '<span class="badge context">CONTEXT</span>' if card.get("context_only") else ""
    stale_badge = '<span class="badge stale">STALE</span>' if card["is_stale"] else ""

    plain_en = (f'<div class="plain">{html.escape(card["plain_english"])}</div>'
                if card.get("plain_english") else "")

    if card["value"] is None:
        return f"""
        <div class="card" style="border-left-color:{COLOR_HEX['grey']}">
          <div class="card-head"><span class="label">{label}</span>{proxy_badge}{context_badge}</div>
          {plain_en}
          <div class="value">UNVERIFIED</div>
          <div class="reason">{html.escape(card['reason'])}</div>
        </div>"""

    val_str = html.escape(_fmt(card["value"], card["decimals"], card["unit"]))
    as_of = card["as_of_date"].strftime("%Y-%m-%d") if card["as_of_date"] is not None else "?"
    spark = _sparkline_svg(card["sparkline"], color)
    p1y = f"{ordinal(card['pctile_1y'])} pct/1y" if card["pctile_1y"] is not None else "1y pct: n/a"
    p5y = f"{ordinal(card['pctile_5y'])} pct/5y" if card["pctile_5y"] is not None else "5y pct: n/a"
    extra3m = (f'<div class="extra">3m annualized: {card["extra_3m_annualized"]:+.2f}%</div>'
               if card.get("extra_3m_annualized") is not None else "")
    unit = card.get("change_unit", "pct")
    forecast = html.escape(card.get("forecast", "—"))

    return f"""
    <div class="card" style="border-left-color:{color}">
      <div class="card-head"><span class="label">{label}</span>{proxy_badge}{context_badge}{stale_badge}</div>
      {plain_en}
      <div class="value">{val_str}</div>
      <div class="asof">as of {as_of} ({card['source']})</div>
      <div class="changes">
        <span>1d {_fmt_change(card['chg_1d'], unit)}</span>
        <span>1w {_fmt_change(card['chg_1w'], unit)}</span>
        <span>1m {_fmt_change(card['chg_1m'], unit)}</span>
        <span>YTD {_fmt_change(card['chg_ytd'], unit)}</span>
      </div>
      <div class="pctile">{p1y} · {p5y}</div>
      {extra3m}
      {spark}
      <div class="reason" style="color:{color}">{html.escape(card['reason'])}</div>
      <div class="forecast"><span class="fc-label">Forecast</span> {forecast}</div>
    </div>"""


def _tldr_html(tldr: dict) -> str:
    if not tldr:
        return ""
    counts = tldr.get("counts", {})
    dot = lambda c, n: f'<span class="dot {c}"></span>{n}'  # noqa: E731
    counts_html = " ".join([
        dot("red", counts.get("red", 0)),
        dot("amber", counts.get("amber", 0)),
        dot("green", counts.get("green", 0)),
    ])
    bullets_html = "".join(f"<li>{html.escape(b)}</li>" for b in tldr.get("bullets", []))
    bullets_block = f"<ul>{bullets_html}</ul>" if bullets_html else "<p class='sub'>Nothing flagged — no indicators are outside their calm range.</p>"
    caveats_html = "".join(f"<li>{html.escape(c)}</li>" for c in tldr.get("caveats", []))
    caveats_block = f'<div class="tldr-caveats"><strong>Caveats:</strong><ul>{caveats_html}</ul></div>' if caveats_html else ""

    return f"""
    <section class="tldr">
      <h2>TL;DR</h2>
      <div class="tldr-headline">{html.escape(tldr.get('headline', ''))}</div>
      <div class="tldr-counts">{counts_html}</div>
      {bullets_block}
      {caveats_block}
      <div class="tldr-disclaimer">Mechanical summary of today's readings and recent trend — not a prediction, not investment advice.</div>
    </section>"""


def render(result: dict) -> str:
    cfg = result["cfg"]
    cards = result["cards"]
    missing = result["missing"]
    local_tz = cfg["meta"]["local_timezone"]

    now_et = pd.Timestamp.now(tz="America/New_York")
    banner_text, is_trading_day = _market_banner(local_tz)

    areas = []
    seen = set()
    for c in cards:
        if c["area"] not in seen:
            areas.append(c["area"])
            seen.add(c["area"])

    sections = []
    for area in areas:
        area_cards = [c for c in cards if c["area"] == area]
        cards_html = "\n".join(_card_html(c) for c in area_cards)
        sections.append(f'<section><h2>{html.escape(area)}</h2><div class="grid">{cards_html}</div></section>')

    missing_html = "".join(f"<li>{html.escape(m)}</li>" for m in missing)
    tldr_html = _tldr_html(result.get("tldr", {}))

    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(cfg['meta']['title'])}</title>
<style>
  :root {{
    --bg: #0f1216; --card-bg: #171b21; --text: #e6e9ef; --muted: #8b93a1;
    --border: #262b33;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--text); margin: 0; padding: 16px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
  }}
  header {{ margin-bottom: 20px; }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  .sub {{ color: var(--muted); font-size: 13px; }}
  .banner {{
    display: inline-block; margin-top: 8px; padding: 4px 10px; border-radius: 6px;
    background: #1e2530; font-size: 13px;
  }}
  h2 {{ font-size: 15px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em;
       margin: 24px 0 10px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }}
  .card {{
    background: var(--card-bg); border: 1px solid var(--border); border-left: 3px solid;
    border-radius: 8px; padding: 12px;
  }}
  .card-head {{ display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }}
  .label {{ font-weight: 600; font-size: 13px; }}
  .badge {{ font-size: 9px; padding: 1px 5px; border-radius: 4px; letter-spacing: .03em; }}
  .badge.proxy {{ background: #4a3b1a; color: #f0c674; }}
  .badge.context {{ background: #2a3b4a; color: #7ec8e3; }}
  .badge.stale {{ background: #4a1a1a; color: #f08080; }}
  .value {{ font-size: 22px; font-weight: 700; margin: 4px 0 2px; }}
  .asof {{ color: var(--muted); font-size: 11px; margin-bottom: 6px; }}
  .changes {{ display: flex; gap: 10px; font-size: 11px; color: var(--muted); flex-wrap: wrap; }}
  .pctile {{ font-size: 11px; color: var(--muted); margin-top: 4px; }}
  .extra {{ font-size: 11px; color: var(--muted); }}
  .reason {{ font-size: 11.5px; margin-top: 6px; }}
  .plain {{ font-size: 11.5px; color: var(--muted); margin-bottom: 6px; line-height: 1.4; }}
  .forecast {{ font-size: 12px; margin-top: 6px; padding-top: 6px; border-top: 1px dashed var(--border); }}
  .fc-label {{ color: var(--muted); text-transform: uppercase; font-size: 9px; letter-spacing: .04em; margin-right: 4px; }}
  svg {{ display: block; margin: 6px 0; }}
  .tldr {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
          padding: 16px; margin-bottom: 8px; }}
  .tldr h2 {{ margin-top: 0; }}
  .tldr-headline {{ font-size: 16px; font-weight: 600; margin-bottom: 8px; }}
  .tldr-counts {{ display: flex; gap: 14px; font-size: 12.5px; color: var(--muted); margin-bottom: 10px; }}
  .dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }}
  .dot.red {{ background: #e74c3c; }}
  .dot.amber {{ background: #f39c12; }}
  .dot.green {{ background: #2ecc71; }}
  .tldr ul {{ margin: 6px 0; padding-left: 20px; font-size: 13px; line-height: 1.5; }}
  .tldr .sub {{ margin: 6px 0; }}
  .tldr-caveats {{ font-size: 11.5px; color: var(--muted); margin-top: 8px; }}
  .tldr-caveats ul {{ font-size: 11.5px; margin: 4px 0; }}
  .tldr-disclaimer {{ font-size: 10.5px; color: var(--muted); margin-top: 10px; font-style: italic; }}
  .missing {{ background: #171b21; border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px;
             margin-top: 24px; font-size: 12.5px; color: var(--muted); }}
  .missing h2 {{ margin-top: 0; }}
  @media (prefers-color-scheme: light) {{
    :root:not([data-theme="dark"]) {{ --bg:#f7f8fa; --card-bg:#fff; --text:#1a1d22; --muted:#6b7280; --border:#e2e5ea; }}
  }}
</style>
</head>
<body>
<header>
  <h1>{html.escape(cfg['meta']['title'])}</h1>
  <div class="sub">Generated {now_et.strftime('%Y-%m-%d %H:%M')} ET</div>
  <div class="banner">{html.escape(banner_text)}</div>
</header>
{tldr_html}
{''.join(sections)}
<div class="missing">
  <h2>What I could not verify</h2>
  <ul>{missing_html}</ul>
</div>
</body>
</html>"""


def write_dashboard(result: dict) -> Path:
    out_dir = ROOT / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(render(result))
    return out_path
