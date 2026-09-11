import asyncio
from datetime import date
from types import SimpleNamespace

from backend.schemas.challenge_schema import ChallengeCreate
from backend.services.challenge_service import ChallengeService


class FakeRepository:
    def __init__(self):
        self.created = []
        self.existing = None

    async def get_by_date(self,challenge_date):
        return self.existing

    async def get_by_id(self,challenge_id):
        return None

    async def get_all(self):
        return []

    async def create(self,challenge):
        self.created.append(challenge)
        return challenge

    async def update(self,challenge):
        return challenge

    async def delete(self,challenge):
        pass


def make_data():
    return ChallengeCreate(
        title="Practice",
        description="Do 10 exercises",
        xp_reward=10,
        challenge_date=date.today()
    )


def test_create_new_challenge():
    repo = FakeRepository()
    service = ChallengeService(repo)

    result = asyncio.run(service.create(make_data()))

    assert result is not None
    assert repo.created == [result]
    assert result.title == "Practice"
    assert result.xp_reward == 10


def test_create_duplicate_challenge_returns_none():
    repo = FakeRepository()
    repo.existing = SimpleNamespace()

    service = ChallengeService(repo)

    result = asyncio.run(service.create(make_data()))

    assert result is None
    assert repo.created == []


def test_get_today_uses_current_date():
    repo = FakeRepository()
    service = ChallengeService(repo)

    result = asyncio.run(service.get_today())

    assert result is None