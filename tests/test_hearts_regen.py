from datetime import datetime,timedelta,timezone

from backend.config import HEART_REFILL_INTERVAL_SECONDS,HEART_REGEN_MINUTES,MAX_HEARTS
from backend.repositories.gamification_repo import GamificationRepository


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FakeHearts:
    def __init__(self,hearts: int,last_heart_lost_at=None):
        self.hearts = hearts
        self.last_heart_lost_at = last_heart_lost_at


def test_regen_is_capped_at_max_hearts():
    repository = GamificationRepository(None)
    hearts = FakeHearts(2,utcnow() - timedelta(hours=10))

    assert repository._apply_regen(hearts,utcnow()) is True
    assert hearts.hearts == 5
    assert hearts.last_heart_lost_at is None


def test_regen_advances_anchor_by_recovered_intervals():
    repository = GamificationRepository(None)
    anchor = utcnow() - timedelta(minutes=90)
    hearts = FakeHearts(2,anchor)

    assert repository._apply_regen(hearts,utcnow()) is True
    assert hearts.hearts == 5
    assert hearts.last_heart_lost_at is None


def test_regen_keeps_anchor_when_still_below_max():
    repository = GamificationRepository(None)
    anchor = utcnow() - timedelta(minutes=65)
    hearts = FakeHearts(2,anchor)

    assert repository._apply_regen(hearts,utcnow()) is True
    assert hearts.hearts == 4
    assert hearts.last_heart_lost_at == anchor + timedelta(minutes=60)


def test_regen_does_nothing_before_interval_elapses():
    repository = GamificationRepository(None)
    anchor = utcnow() - timedelta(minutes=29)
    hearts = FakeHearts(2,anchor)

    assert repository._apply_regen(hearts,utcnow()) is False
    assert hearts.hearts == 2
    assert hearts.last_heart_lost_at == anchor


def test_regen_clears_anchor_at_full_hearts():
    repository = GamificationRepository(None)
    hearts = FakeHearts(5,utcnow() - timedelta(hours=3))

    assert repository._apply_regen(hearts,utcnow()) is True
    assert hearts.hearts == 5
    assert hearts.last_heart_lost_at is None


def test_seconds_to_next_heart_counts_down_to_regen():
    repository = GamificationRepository(None)
    hearts = FakeHearts(2,utcnow() - timedelta(minutes=20))

    assert 595 < repository.seconds_to_next_heart(hearts) <= 600


def test_seconds_to_next_heart_is_zero_at_full_hearts():
    repository = GamificationRepository(None)

    assert repository.seconds_to_next_heart(FakeHearts(5)) == 0
    assert repository.seconds_to_next_heart(FakeHearts(3)) == 0


def test_next_heart_at_is_thirty_minutes_after_the_anchor():
    repository = GamificationRepository(None)
    anchor = datetime(2026,11,8,10,0,tzinfo=timezone.utc)
    hearts = FakeHearts(4,anchor)
    next_heart_at = getattr(repository,"next_heart_at",None)

    assert callable(next_heart_at)
    assert next_heart_at(hearts) == anchor + timedelta(minutes=30)


def test_next_heart_at_is_none_when_full():
    repository = GamificationRepository(None)
    next_heart_at = getattr(repository,"next_heart_at",None)

    assert callable(next_heart_at)
    assert next_heart_at(FakeHearts(5)) is None


def test_seconds_to_next_heart_never_goes_negative():
    repository = GamificationRepository(None)
    hearts = FakeHearts(2,utcnow() - timedelta(hours=4))

    assert repository.seconds_to_next_heart(hearts) == 0


def test_empty_hearts_arms_the_timer_instead_of_staying_locked():
    repository = GamificationRepository(None)
    now = utcnow()
    hearts = FakeHearts(0)

    assert repository._apply_regen(hearts,now) is True
    assert hearts.hearts == 0
    assert hearts.last_heart_lost_at == now
    assert 0 < repository.seconds_to_next_heart(hearts) <= 1800


def test_one_heart_returns_thirty_minutes_after_running_out():
    repository = GamificationRepository(None)
    anchor = utcnow() - timedelta(minutes=30)
    hearts = FakeHearts(0,anchor)

    assert repository._apply_regen(hearts,utcnow()) is True
    assert hearts.hearts == 1
    assert hearts.last_heart_lost_at == anchor + timedelta(minutes=30)


def test_refill_keeps_pace_one_heart_per_interval_when_empty():
    repository = GamificationRepository(None)
    anchor = utcnow() - timedelta(minutes=75)
    hearts = FakeHearts(0,anchor)

    assert repository._apply_regen(hearts,utcnow()) is True
    assert hearts.hearts == 2
    assert hearts.last_heart_lost_at == anchor + timedelta(minutes=60)


def test_refill_does_not_jump_ahead_of_elapsed_intervals():
    repository = GamificationRepository(None)
    anchor = utcnow() - timedelta(minutes=31)
    hearts = FakeHearts(0,anchor)

    assert repository._apply_regen(hearts,utcnow()) is True
    assert hearts.hearts == 1
    assert 0 < repository.seconds_to_next_heart(hearts) <= 1800


def test_running_out_rearms_the_countdown_from_the_last_loss():
    repository = GamificationRepository(None)
    anchor = utcnow() - timedelta(minutes=5)
    hearts = FakeHearts(2,anchor)

    assert repository._apply_regen(hearts,utcnow()) is False
    assert hearts.hearts == 2
    assert hearts.last_heart_lost_at == anchor


def test_background_pass_interval_is_shorter_than_the_regen_rate():
    assert 0 < HEART_REFILL_INTERVAL_SECONDS <= HEART_REGEN_MINUTES * 60


def test_max_hearts_leaves_room_to_lose_hearts():
    assert MAX_HEARTS > 1
    assert MAX_HEARTS == 5
