import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace


def _run_immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("test coroutine unexpectedly required an event loop")


class _GoalRepository:
    def __init__(self, earned_xp=0):
        self.goal = SimpleNamespace(target_xp=20)
        self.earned_xp = earned_xp
        self.bounds = None

    async def get_or_create(self, user_id):
        return self.goal

    async def sum_xp(self, user_id, start_at, end_at):
        self.bounds = (start_at, end_at)
        return self.earned_xp

    async def set_target(self, user_id, target_xp):
        self.goal.target_xp = target_xp
        return self.goal


def test_bishkek_day_changes_at_1800_utc():
    """Catches daily XP using a UTC date instead of the Bishkek calendar."""
    from backend.services.daily_goal_service import bishkek_day_bounds

    before_start, before_end, before_day = bishkek_day_bounds(
        datetime(2026, 1, 1, 17, 59, tzinfo=timezone.utc)
    )
    after_start, after_end, after_day = bishkek_day_bounds(
        datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)
    )

    assert before_day == date(2026, 1, 1)
    assert before_start == datetime(2025, 12, 31, 18, 0, tzinfo=timezone.utc)
    assert before_end == datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)
    assert after_day == date(2026, 1, 2)
    assert after_start == before_end
    assert after_end == datetime(2026, 1, 2, 18, 0, tzinfo=timezone.utc)


def test_default_goal_and_progress_are_derived_server_side():
    """Catches a client-editable progress field or a wrong default target."""
    from backend.services.daily_goal_service import DailyGoalService

    repository = _GoalRepository(earned_xp=7)
    service = DailyGoalService(repository)
    user_id = uuid.uuid4()
    status = _run_immediate(
        service.get_status(
            user_id, datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        )
    )

    assert status.target_xp == 20
    assert status.earned_xp == 7
    assert status.remaining_xp == 13
    assert status.completed is False
    assert status.day == date(2026, 1, 1)
    assert repository.bounds == (
        datetime(2025, 12, 31, 18, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc),
    )


def test_setting_target_recomputes_status_from_existing_xp():
    """Catches target updates overwriting or trusting earned progress."""
    from backend.services.daily_goal_service import DailyGoalService

    repository = _GoalRepository(earned_xp=25)
    service = DailyGoalService(repository)
    status = _run_immediate(
        service.set_target(
            uuid.uuid4(),
            30,
            datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
    )

    assert status.target_xp == 30
    assert status.earned_xp == 25
    assert status.remaining_xp == 5
    assert status.completed is False


def test_daily_goal_routes_are_authenticated_and_use_current_user():
    """Catches goal routes accepting another user's id or disappearing from API."""
    from backend.api.daily_goals import get_daily_goal, update_daily_goal
    from backend.schemas.daily_goal_schema import DailyGoalUpdate
    from main import duolingo

    class Service:
        def __init__(self):
            self.calls = []

        async def get_status(self, user_id):
            self.calls.append(("get", user_id))
            return {"target_xp": 20}

        async def set_target(self, user_id, target_xp):
            self.calls.append(("set", user_id, target_xp))
            return {"target_xp": target_xp}

    service = Service()
    user = SimpleNamespace(id=uuid.uuid4())

    loaded = _run_immediate(get_daily_goal(current_user=user, service=service))
    updated = _run_immediate(
        update_daily_goal(
            DailyGoalUpdate(target_xp=40), current_user=user, service=service
        )
    )

    assert loaded == {"target_xp": 20}
    assert updated == {"target_xp": 40}
    assert service.calls == [("get", user.id), ("set", user.id, 40)]
    assert set(duolingo.openapi()["paths"]["/daily-goal"]) >= {"get", "put"}
