from datetime import date, datetime, timezone
from importlib import import_module, util


def _app_time_module():
    assert util.find_spec("backend.time") is not None, "backend.time must exist"
    return import_module("backend.time")


def test_utc_now_returns_an_aware_utc_instant():
    app_time = _app_time_module()
    utc_now = getattr(app_time, "utc_now", None)

    assert callable(utc_now)
    result = utc_now()
    assert result.tzinfo is not None
    assert result.utcoffset().total_seconds() == 0


def test_bishkek_date_stays_on_november_8_before_local_midnight():
    app_time = _app_time_module()
    bishkek_date = getattr(app_time, "bishkek_date", None)

    assert callable(bishkek_date)
    instant = datetime(2026, 11, 8, 17, 59, 59, tzinfo=timezone.utc)
    assert bishkek_date(instant) == date(2026, 11, 8)


def test_bishkek_date_rolls_over_at_18_utc():
    app_time = _app_time_module()
    bishkek_date = getattr(app_time, "bishkek_date", None)

    assert callable(bishkek_date)
    instant = datetime(2026, 11, 8, 18, 0, 0, tzinfo=timezone.utc)
    assert bishkek_date(instant) == date(2026, 11, 9)


def test_bishkek_date_treats_a_naive_input_as_utc():
    app_time = _app_time_module()
    bishkek_date = getattr(app_time, "bishkek_date", None)

    assert callable(bishkek_date)
    assert bishkek_date(datetime(2026, 11, 8, 18, 0, 0)) == date(2026, 11, 9)
