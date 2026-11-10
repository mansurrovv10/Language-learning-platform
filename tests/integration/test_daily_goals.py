import uuid
from datetime import datetime, timezone

import pytest

from backend.models.gamification import XPHistory
from backend.repositories.daily_goal_repo import DailyGoalRepository
from backend.services.auth_ser import AuthService
from backend.services.daily_goal_service import DailyGoalService

pytestmark = pytest.mark.integration


@pytest.mark.asyncio(loop_scope="session")
async def test_daily_goal_uses_bishkek_boundaries_and_isolates_users(db_session):
    """Catches XP leaking across a Bishkek day or between user accounts."""
    first = await AuthService(db_session).register(
        f"goal-first-{uuid.uuid4().hex}@example.com",
        f"goal_first_{uuid.uuid4().hex}",
        "password123",
    )
    second = await AuthService(db_session).register(
        f"goal-second-{uuid.uuid4().hex}@example.com",
        f"goal_second_{uuid.uuid4().hex}",
        "password123",
    )
    db_session.add_all(
        [
            XPHistory(
                user_id=first.id,
                xp=5,
                reason="before-boundary",
                created_at=datetime(2026, 1, 1, 17, 59, tzinfo=timezone.utc),
            ),
            XPHistory(
                user_id=first.id,
                xp=7,
                reason="after-boundary",
                created_at=datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc),
            ),
            XPHistory(
                user_id=second.id,
                xp=99,
                reason="other-user",
                created_at=datetime(2026, 1, 1, 18, 1, tzinfo=timezone.utc),
            ),
        ]
    )
    await db_session.commit()
    service = DailyGoalService(DailyGoalRepository(db_session))

    first_day = await service.get_status(
        first.id, datetime(2026, 1, 1, 17, 59, tzinfo=timezone.utc)
    )
    second_day = await service.get_status(
        first.id, datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)
    )

    assert first_day.earned_xp == 5
    assert second_day.earned_xp == 7


@pytest.mark.asyncio(loop_scope="session")
async def test_daily_goal_target_persists_without_editing_progress(db_session):
    """Catches target writes storing a client-provided progress value."""
    user = await AuthService(db_session).register(
        f"goal-target-{uuid.uuid4().hex}@example.com",
        f"goal_target_{uuid.uuid4().hex}",
        "password123",
    )
    service = DailyGoalService(DailyGoalRepository(db_session))

    updated = await service.set_target(
        user.id,
        35,
        datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    loaded = await service.get_status(
        user.id, datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    )

    assert updated.target_xp == 35
    assert loaded.target_xp == 35
    assert loaded.earned_xp == 0
