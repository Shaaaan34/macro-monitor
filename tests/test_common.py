import pandas as pd

from src.common import change_vs, change_vs_ytd, derive_pct_change_series, percentile_rank


def _series(values, start="2024-01-01"):
    dates = pd.date_range(start, periods=len(values), freq="D")
    return pd.DataFrame({"date": dates, "value": values})


def test_change_vs_basic():
    df = _series([100, 101, 102, 103, 110])
    latest_date = df["date"].iloc[-1]
    chg = change_vs(df, 110, latest_date, 1)
    assert round(chg, 2) == round((110 - 103) / 103 * 100, 2)


def test_percentile_rank_bounds():
    df = _series(list(range(1, 101)))
    latest_date = df["date"].iloc[-1]
    p = percentile_rank(df, 100, latest_date, 365)
    assert p == 100.0
    p_low = percentile_rank(df, 1, latest_date, 365)
    assert p_low == 1.0


def test_derive_yoy_from_monthly_level():
    dates = pd.date_range("2023-01-01", periods=25, freq="MS")
    values = [100 * (1.002 ** i) for i in range(25)]  # ~2.4% annualized growth
    df = pd.DataFrame({"date": dates, "value": values})
    yoy = derive_pct_change_series(df, days=365, tolerance_days=20)
    assert not yoy.empty
    last_yoy = yoy.sort_values("date").iloc[-1]["value"]
    assert 1.5 < last_yoy < 3.5


def test_change_vs_ytd_uses_jan1_anchor():
    df = _series([100] * 30 + [110], start="2024-12-01")
    latest_date = df["date"].iloc[-1]
    chg = change_vs_ytd(df, 110, latest_date)
    assert chg is not None
