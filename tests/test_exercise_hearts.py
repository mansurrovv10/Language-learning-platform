import asyncio
import uuid
from datetime import date

import pytest

from backend.models.exercise import ExerciseType
from backend.schemas.exercise_schema import ExerciseSubmit
from backend.services.exercise_service import ExerciseService,NotEnoughHeartsError


class FakeExercise:
    def __init__(self,correct_answer,exercise_id: int = 1,lesson_id: int = 1):
        self.id = exercise_id
        self.lesson_id = lesson_id
        self.type = ExerciseType.CHOICE
        self.correct_answer = correct_answer


class FakeHearts:
    def __init__(self,hearts: int):
        self.hearts = hearts


class FakeStreak:
    def __init__(self):
        self.current_streak = 1
        self.last_activity = date.today()


class FakeProgress:
    def __init__(self,completed: bool):
        self.completed = completed


class FakeGamificationRepository:
    def __init__(self,hearts: int):
        self.hearts = FakeHearts(hearts)
        self.lose_heart_calls = 0

    async def get_current_hearts(self,user_id):
        return self.hearts

    def seconds_to_next_heart(self,hearts):
        return 900

    async def lose_heart(self,user_id):
        self.lose_heart_calls += 1
        self.hearts.hearts -= 1
        return self.hearts.hearts

    async def add_xp(self,user_id,xp,reason):
        return None

    async def get_streak(self,user_id):
        return FakeStreak()

    async def get_xp_history(self,user_id):
        return []


class FakeExerciseRepository:
    def __init__(self,exercise):
        self.exercise = exercise

    async def get_by_id(self,exercise_id):
        return self.exercise


class FakeExerciseProgressRepository:
    def __init__(self,completed: bool):
        self.completed = completed

    async def get_by_user_and_exercise(self,user_id,exercise_id):
        return FakeProgress(self.completed) if self.completed else None

    async def save_result(self,user_id,exercise_id,completed,score):
        return None

    async def are_lesson_exercises_completed(self,user_id,lesson_id):
        return False


class FakeProgressRepository:
    async def get_by_user_and_lesson(self,user_id,lesson_id):
        return None

    async def create(self,**kwargs):
        return None

    async def update(self,progress_id,**kwargs):
        return None


class FakeAchievementRepository:
    async def get_all(self):
        return []


def build_service(correct_answer,hearts: int = 5,completed: bool = False):
    gamification = FakeGamificationRepository(hearts)

    service = ExerciseService(
        FakeExerciseRepository(FakeExercise(correct_answer)),
        FakeProgressRepository(),
        FakeExerciseProgressRepository(completed),
        gamification,
        FakeAchievementRepository())

    return service,gamification


def submit(service,answer):
    return asyncio.run(service.submit_exercise(1,ExerciseSubmit(answer=answer),uuid.uuid4()))


def test_correct_answer_keeps_hearts_intact():
    service,gamification = build_service("hello")

    result = submit(service,"  HELLO ")

    assert result.correct is True
    assert result.hearts_left == 5
    assert gamification.lose_heart_calls == 0


def test_wrong_answer_loses_exactly_one_heart():
    service,gamification = build_service("hello")

    result = submit(service,"bonjour")

    assert result.correct is False
    assert result.hearts_left == 4
    assert gamification.lose_heart_calls == 1


def test_wrong_answer_on_completed_exercise_keeps_hearts():
    service,gamification = build_service("hello",completed=True)

    result = submit(service,"bonjour")

    assert result.correct is False
    assert result.hearts_left == 5
    assert gamification.lose_heart_calls == 0


def test_zero_hearts_blocks_submission():
    service,gamification = build_service("hello",hearts=0)

    with pytest.raises(NotEnoughHeartsError) as error:
        submit(service,"hello")

    assert error.value.seconds_to_next_heart == 900
    assert gamification.lose_heart_calls == 0


@pytest.mark.parametrize("expected,answer",[
    ({"answer":"hello"},"hello"),
    ("1",1),
    (1,"1"),
    (1.0,"1"),
    ("  Hello  ","hello"),
    ({"a":"1","b":"2"},[["a",1],["b",2]]),
    ("да",  "ДА "),
])
def test_answer_matching_ignores_formatting(expected,answer):
    service,_ = build_service(expected)

    assert service._check_answer(FakeExercise(expected),answer) is True


@pytest.mark.parametrize("expected,answer",[
    ("hello","bonjour"),
    (["a","b"],["a","c"]),
    ({"a":"1","b":"2"},{"a":"1","b":"3"}),
    ("1",2),
    ("hello",None),
    (True,False),
])
def test_answer_matching_rejects_wrong_answers(expected,answer):
    service,_ = build_service(expected)

    assert service._check_answer(FakeExercise(expected),answer) is False
