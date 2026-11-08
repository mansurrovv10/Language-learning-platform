import uuid
from datetime import datetime,timezone
from types import SimpleNamespace

import pytest

from backend.services.gamification_service import GamificationService


pytestmark = pytest.mark.asyncio(loop_scope="function")


class FakeGamificationRepository:
    def __init__(self):
        self.streak = None
        self.xp_calls = []

    async def get_streak(self,user_id):
        return self.streak

    async def create_streak(self,user_id,commit=True):
        self.streak = SimpleNamespace(
            user_id=user_id,current_streak=0,last_activity=None
        )
        return self.streak

    async def update_streak(self,streak,commit=True):
        self.streak = streak
        return streak

    async def add_xp(self,user_id,xp,reason):
        self.xp_calls.append((user_id,xp,reason))


async def test_streak_advances_once_per_bishkek_day():
    repository = FakeGamificationRepository()
    service = GamificationService(repository)
    user_id = uuid.uuid4()

    await service.advance_streak_for_learning(
        user_id,datetime(2026,11,8,17,59,59,tzinfo=timezone.utc)
    )
    await service.advance_streak_for_learning(
        user_id,datetime(2026,11,8,17,59,59,tzinfo=timezone.utc)
    )
    streak = await service.advance_streak_for_learning(
        user_id,datetime(2026,11,8,18,0,0,tzinfo=timezone.utc)
    )

    assert streak.current_streak == 2
    assert streak.last_activity.isoformat() == "2026-11-09"


async def test_streak_resets_after_missed_bishkek_day():
    repository = FakeGamificationRepository()
    service = GamificationService(repository)
    user_id = uuid.uuid4()

    await service.advance_streak_for_learning(
        user_id,datetime(2026,11,6,18,0,0,tzinfo=timezone.utc)
    )
    streak = await service.advance_streak_for_learning(
        user_id,datetime(2026,11,8,18,0,0,tzinfo=timezone.utc)
    )

    assert streak.current_streak == 1
    assert streak.last_activity.isoformat() == "2026-11-09"


async def test_achievement_xp_does_not_advance_streak():
    repository = FakeGamificationRepository()
    service = GamificationService(repository)
    user_id = uuid.uuid4()

    await service.add_xp(user_id,50,"achievement")

    assert repository.streak is None

