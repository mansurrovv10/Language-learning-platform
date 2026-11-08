import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport,AsyncClient
from sqlalchemy import select

from backend.api.auth import get_current_user
from backend.api.progress import get_progress_service,router
from backend.models.leaderboard import Leaderboard
from backend.models.user import UserRole
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.leaderboard_repo import LeaderboardRepository
from backend.services.auth_ser import AuthService


pytestmark = [pytest.mark.integration,pytest.mark.asyncio(loop_scope="session")]


class FakeProgressService:
    def __init__(self,user_id):
        self.user_id = user_id

    async def get_by_id(self,progress_id):
        return SimpleNamespace(
            id=progress_id,
            user_id=self.user_id,
            lesson_id=1,
            completed=False,
            score=0,
            completed_at=None,
        )

    async def update(self,progress_id,completed,score):
        return {
            "id":progress_id,
            "user_id":self.user_id,
            "lesson_id":1,
            "completed":bool(completed),
            "score":score or 0,
            "completed_at":None,
        }


def progress_app(user):
    app = FastAPI()
    app.include_router(router)
    service = FakeProgressService(user.id)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_progress_service] = lambda: service
    return app


async def test_ordinary_user_cannot_mutate_own_progress():
    user = SimpleNamespace(id=uuid.uuid4(),role=UserRole.USER)
    async with AsyncClient(
        transport=ASGITransport(app=progress_app(user)),base_url="http://test"
    ) as client:
        response = await client.put(
            "/progress/1",json={"completed":True,"score":100}
        )

    assert response.status_code == 403


async def test_admin_can_maintain_progress():
    admin = SimpleNamespace(id=uuid.uuid4(),role=UserRole.ADMIN)
    async with AsyncClient(
        transport=ASGITransport(app=progress_app(admin)),base_url="http://test"
    ) as client:
        response = await client.put(
            "/progress/1",json={"completed":True,"score":100}
        )

    assert response.status_code == 200
    assert response.json()["completed"] is True


async def test_new_xp_recomputes_affected_leaderboard_ranks(db_session):
    first = await AuthService(db_session).register(
        f"rank-first-{uuid.uuid4().hex}@example.com",
        f"rank_first_{uuid.uuid4().hex}",
        "password123",
    )
    second = await AuthService(db_session).register(
        f"rank-second-{uuid.uuid4().hex}@example.com",
        f"rank_second_{uuid.uuid4().hex}",
        "password123",
    )
    repository = GamificationRepository(db_session)

    await repository.add_xp(first.id,10,"exercise_completed")
    await repository.add_xp(second.id,20,"exercise_completed")
    entries = list((await db_session.scalars(
        select(Leaderboard).where(Leaderboard.user_id.in_([first.id,second.id]))
    )).all())
    ranks = {entry.user_id:entry.rank for entry in entries}
    leaderboard = LeaderboardRepository(db_session)

    assert ranks[first.id] == await leaderboard.get_user_rank(first.id)
    assert ranks[second.id] == await leaderboard.get_user_rank(second.id)
    assert ranks[second.id] < ranks[first.id]
