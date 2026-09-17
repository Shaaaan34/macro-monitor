# Daily Pre-Market Macro Monitor

A one-glance, self-contained HTML dashboard for the macro layer of a top-down
(macro → industry → market → company) investing process. Fetches data, stores
history, computes changes/percentiles/status colors, and writes `docs/index.html`.

**Status: Phase 1 complete + TL;DR/forecast layer + GitHub Actions workflow
written** — core 10 indicator areas, 5-year history backfill, local
one-command run, plain-English top-of-page summary. The workflow file exists
(`.github/workflows/market-close.yml`) but the repo isn't pushed to GitHub
yet — see **Publishing (GitHub Actions + Pages)** below to finish that in
~5 minutes. Phase 2/4 (extended indicators + full regime scoring, calendar,
theme-tape, AI summary) are not yet built.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your FRED_API_KEY
python run.py
open docs/index.html        # or: python -m http.server 8743 --directory docs
```

Re-run `python run.py` any time — it backfills 5 years of history the first
time it sees an indicator, then only fetches new data on later runs.

### Getting a FRED API key

Free, instant signup: https://fred.stlouisfed.org/docs/api/api_key.html
Without it, the 7 FRED-backed indicators (PMI proxies, credit spreads, CPI,
10Y yield) show `UNVERIFIED` and are listed under "What I could not verify" —
the yfinance-backed indicators still work.

## Editing thresholds

All status-color (green/amber/red) thresholds live in [`config/config.yaml`](config/config.yaml),
each with a rationale comment. Edit and re-run — no code changes needed.

## Editing tickers / FRED series

Also in `config/config.yaml`, under `tickers:` (yfinance) and `fred_series:`
(FRED). If you add a new indicator, also add an entry to `INDICATOR_REGISTRY`
in [`src/indicators.py`](src/indicators.py) with its area, category, and display
formatting, and a status rule in `status_for()` if it needs one.

## Indicators (Phase 1 — core 10 areas)

| Area | Indicator | Source | Update frequency | Typical lag |
|---|---|---|---|---|
| Market fear | VIX | yfinance `^VIX` | Intraday | ~15-20 min delayed |
| Oil | WTI crude | yfinance `CL=F` | Intraday (futures) | ~10-20 min delayed |
| Oil | Brent crude | yfinance `BZ=F` | Intraday (futures) | ~10-20 min delayed |
| Economic growth (PMI proxy) | Philly Fed general activity | FRED `GACDFSA066MSFRBPHI` | Monthly (3rd Thu) | Same-day release |
| Economic growth (PMI proxy) | Empire State general business conditions | FRED `GACDISA066MSFRBNY` | Monthly (mid-month) | Same-day release |
| Recession risk | US HY credit spread (OAS) | FRED `BAMLH0A0HYM2` | Daily | ~1 day |
| Recession risk | US IG credit spread (OAS), context only | FRED `BAMLC0A0CM` | Daily | ~1 day |
| US stocks | S&P 500 | yfinance `^GSPC` | Intraday | ~15-20 min delayed |
| US stocks | S&P 500 futures | yfinance `ES=F` | Intraday (futures) | ~10-20 min delayed |
| Tech | Nasdaq 100 | yfinance `^NDX` | Intraday | ~15-20 min delayed |
| Tech | Nasdaq Composite | yfinance `^IXIC` | Intraday | ~15-20 min delayed |
| Tech | Nasdaq futures | yfinance `NQ=F` | Intraday (futures) | ~10-20 min delayed |
| US inflation | CPI headline (YoY, derived) | FRED `CPIAUCSL` | Monthly | ~2 weeks after month-end |
| US inflation | CPI core (YoY, derived) | FRED `CPILFESL` | Monthly | ~2 weeks after month-end |
| US rates | 10-Year Treasury yield | FRED `DGS10` | Daily | ~1 day |
| US dollar | US Dollar Index (DXY) | yfinance `DX-Y.NYB` | Intraday | ~15-20 min delayed |
| Global trade | Baltic Dry Index **(proxy: BDRY ETF)** | yfinance `BDRY` | Daily | ~15-20 min delayed |

**Proxies, clearly labeled in the dashboard with a `PROXY` badge:**
- ISM Manufacturing/Services PMI has no free API → Philly Fed + Empire State
  regional Fed diffusion indices are shown instead.
- Baltic Dry Index has no free official API → the BDRY ETF (a basket of dry-bulk
  shipping futures) is shown as a proxy, not the index itself.

## What each card shows

Latest value + as-of date, 1d/1w/1m/YTD change, percentile vs trailing 1y and 5y,
a 1-year sparkline, and a status color with a one-line reason referencing the
exact threshold crossed (see `config/config.yaml`).

## History storage

Long-format CSV at `data/history.csv` (`date, indicator, value, as_of, source,
is_stale, fetched_at`), chosen over SQLite so each day's diff is readable in
git and there's no binary merge-conflict risk when GitHub Actions commits it.

## One source failing never breaks the run

Each fetcher is wrapped so a failure logs a warning and falls back to the last
known value from history (or `UNVERIFIED` if there's no history yet). Every run
prints and renders a "What I could not verify" list — check it after every run.

## Tests

```bash
python -m pytest tests/ -q
```

Fetcher tests hit the live yfinance/FRED APIs and check (a) data comes back and
(b) the latest value is in a plausible range — FRED tests skip automatically if
`FRED_API_KEY` isn't set.

## Publishing (GitHub Actions + Pages) — runs automatically at market close

The workflow is already written; this repo just isn't pushed to GitHub yet.
I can't do this part myself (no GitHub auth in this environment) — it's ~5
minutes of copy-paste:

1. **Create an empty public repo** at https://github.com/new (any name, e.g.
   `macro-monitor`). Don't initialize it with a README/license — this repo
   already has commits.

2. **Commit and push this repo to it:**
   ```bash
   cd /Users/tharusha/Downloads/files/macro-monitor
   git add -A
   git commit -m "Phase 1: core 10 indicators, TL;DR summary, market-close workflow"
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git branch -M main
   git push -u origin main
   ```

3. **Add your FRED key as a repo secret** (GitHub needs its own copy — it
   can't read your local `.env`): repo → **Settings → Secrets and variables →
   Actions → New repository secret** → name `FRED_API_KEY`, value = your key.

4. **Enable Pages**: repo → **Settings → Pages** → Source: **Deploy from a
   branch** → Branch: `main`, folder: `/docs` → Save. Your dashboard will be
   live at `https://<your-username>.github.io/<repo-name>/`.

That's it — `.github/workflows/market-close.yml` will then:
- Fire twice daily on weekdays (20:15 and 21:15 UTC, covering both EDT and
  EST) and run [`scripts/should_run.py`](scripts/should_run.py) as a guard,
  which checks the real NYSE calendar (handles half-days and DST) and only
  lets the run through the one time that's actually within 20 minutes of
  today's real market close. The other scheduled trigger exits harmlessly.
  It also skips entirely on weekends/holidays.
- Fetch fresh data, update `data/history.csv`, and regenerate `docs/index.html`,
  committing both back to the repo — so Pages always serves the latest close.
- Also runs on-demand any time from the repo's **Actions** tab → this
  workflow → **Run workflow** (bypasses the close-time guard).

## Not yet built (see prompt's Build phases 2-4)

- Extended indicators (yield curve, breakevens, GDPNow, NFCI, labour, CFTC
  positioning, AAII/put-call, valuations) + full 5-pillar regime scoring +
  "what changed since yesterday" (a lightweight TL;DR + per-card forecast
  already exist, see above)
- Economic calendar, theme-tape ETF panel, optional AI "morning macro read"
  summary layer
