#!/usr/bin/env python3
"""Exit 0 iff we're currently within the market-close run window (ET).

Used by the GitHub Actions schedule (which fires at two fixed UTC times to
cover both EDT and EST) so only the one that actually lands after today's
NYSE close proceeds to run the pipeline — the other exits 1 and is skipped.
Also correctly skips entirely on weekends/holidays and market half-days.

Window is intentionally wide (60 min): GitHub's own scheduler is documented
to run late, and observed delays here have been 20-27 minutes — a tighter
window caused every scheduled run to be silently skipped. If both the EDT
and EST crons land inside the window on the same day, that's harmless: the
pipeline just re-fetches the same latest close and the workflow's own
`git diff --cached --quiet` check skips the commit when nothing changed.
"""
import sys

import pandas as pd
import pandas_market_calendars as mcal

WINDOW_MINUTES_AFTER_CLOSE = 60


def check(now_et: pd.Timestamp) -> tuple[bool, str]:
    """Returns (should_run, message)."""
    nyse = mcal.get_calendar("NYSE")
    today = now_et.normalize().tz_localize(None)

    schedule = nyse.schedule(start_date=today, end_date=today)
    if schedule.empty:
        return False, f"{today.date()} is not a NYSE trading day — skipping"

    close_time = schedule.loc[today, "market_close"].tz_convert("America/New_York")
    window_end = close_time + pd.Timedelta(minutes=WINDOW_MINUTES_AFTER_CLOSE)

    if close_time <= now_et <= window_end:
        return True, f"within market-close window (close={close_time}, now={now_et})"
    return False, f"outside market-close window (close={close_time}, now={now_et}) — skipping"


def main() -> int:
    should_run, message = check(pd.Timestamp.now(tz="America/New_York"))
    print(message)
    return 0 if should_run else 1


if __name__ == "__main__":
    sys.exit(main())
