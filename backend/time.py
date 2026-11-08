from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


BISHKEK = ZoneInfo("Asia/Bishkek")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def bishkek_date(at: datetime | None = None) -> date:
    instant = utc_now() if at is None else as_utc(at)
    return instant.astimezone(BISHKEK).date()
