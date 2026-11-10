import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace


def _run_immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("test coroutine unexpectedly required an event loop")


class _ReviewRepository:
    def __init__(self, box=0):
        self.item = SimpleNamespace(
            box=box,
            due_at=None,
            last_result=None,
            attempts=0,
            correct_streak=0,
        )
        self.commits = []

    async def get_or_create(self, user_id, exercise_id):
        return self.item

    async def save(self, item, commit):
        self.commits.append(commit)
        return item


def test_wrong_result_is_due_immediately_and_resets_box():
    """Catches a wrong answer retaining a future due date or advanced box."""
    from backend.services.review_service import ReviewService

    repository = _ReviewRepository(box=4)
    at = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    item = _run_immediate(
        ReviewService(repository).record_result(
            uuid.uuid4(), 1, False, at=at, commit=False
        )
    )

    assert item.box == 0
    assert item.due_at == at
    assert item.last_result is False
    assert item.attempts == 1
    assert item.correct_streak == 0
    assert repository.commits == [False]


def test_correct_results_follow_interval_ladder_and_cap():
    """Catches off-by-one interval progression or advancing beyond box five."""
    from backend.services.review_service import ReviewService

    at = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    expected_days = [1, 3, 7, 14, 30, 30]
    repository = _ReviewRepository(box=0)
    service = ReviewService(repository)

    for expected in expected_days:
        item = _run_immediate(
            service.record_result(uuid.uuid4(), 1, True, at=at, commit=False)
        )
        assert item.due_at == at + timedelta(days=expected)

    assert item.box == 5
    assert item.attempts == 6
    assert item.correct_streak == 6


def test_due_review_route_uses_authenticated_user_and_is_registered():
    """Catches due-review reads accepting another user id or missing from API."""
    from backend.api.reviews import get_due_reviews
    from main import duolingo

    class Service:
        def __init__(self):
            self.call = None

        async def get_due(self, user_id, limit, offset):
            self.call = (user_id, limit, offset)
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

    user = SimpleNamespace(id=uuid.uuid4())
    service = Service()
    result = _run_immediate(
        get_due_reviews(user, service, limit=5, offset=2)
    )

    assert service.call == (user.id, 5, 2)
    assert result["limit"] == 5
    assert "get" in duolingo.openapi()["paths"]["/reviews/due"]
