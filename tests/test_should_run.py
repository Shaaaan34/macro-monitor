import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from should_run import check  # noqa: E402


def test_within_window_on_a_trading_day():
    # 2026-09-16 is a Wednesday, a normal NYSE trading day. Close is 16:00 ET.
    now = pd.Timestamp("2026-09-16 16:05:00", tz="America/New_York")
    should_run, msg = check(now)
    assert should_run, msg


def test_before_close_is_skipped():
    now = pd.Timestamp("2026-09-16 15:00:00", tz="America/New_York")
    should_run, _ = check(now)
    assert not should_run


def test_long_after_close_is_skipped():
    now = pd.Timestamp("2026-09-16 18:00:00", tz="America/New_York")
    should_run, _ = check(now)
    assert not should_run


def test_weekend_is_skipped():
    # 2026-09-19 is a Saturday
    now = pd.Timestamp("2026-09-19 16:05:00", tz="America/New_York")
    should_run, msg = check(now)
    assert not should_run
    assert "not a NYSE trading day" in msg


def test_holiday_is_skipped():
    # 2026-01-01 New Year's Day
    now = pd.Timestamp("2026-01-01 16:05:00", tz="America/New_York")
    should_run, msg = check(now)
    assert not should_run
    assert "not a NYSE trading day" in msg
