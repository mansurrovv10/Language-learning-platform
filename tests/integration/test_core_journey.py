import uuid

import pytest
from sqlalchemy import func,select

from backend.models.course import Course,LevelChoices
from backend.models.exercise import Exercise,ExerciseType
from backend.models.gamification import Hearts,Streak,XPHistory
from backend.models.language import Language
from backend.models.lesson import Lesson
from backend.models.progress import UserProgress
from backend.repositories.achievement_repo import AchievementRepository
from backend.repositories.chat_repo import ChatRepository
from backend.repositories.exercise_progress_repo import ExerciseProgressRepository
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.exercise_submission_repo import ExerciseSubmissionRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.learning_path_repo import LearningPathRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.schemas.chat_schema import ChatCreate,MessageCreate
from backend.schemas.exercise_schema import ExerciseSubmit
from backend.services.auth_ser import AuthService
from backend.services.chat_service import ChatService
from backend.services.exercise_service import ExerciseService
from backend.services.learning_path_service import LearningPathService


pytestmark = [pytest.mark.integration,pytest.mark.asyncio(loop_scope="session")]


async def test_registration_to_chat_core_journey(db_session):
    auth = AuthService(db_session)
    first = await auth.register(
        f"journey-first-{uuid.uuid4().hex}@example.com",
        f"journey_first_{uuid.uuid4().hex}",
        "password123",
    )
    second = await auth.register(
        f"journey-second-{uuid.uuid4().hex}@example.com",
        f"journey_second_{uuid.uuid4().hex}",
        "password123",
    )
    language = Language(
        code=f"j-{uuid.uuid4().hex[:6]}",
        name=f"Journey {uuid.uuid4().hex}",
        is_active=True,
    )
    db_session.add(language)
    await db_session.flush()
    course = Course(
        language_id=language.id,
        title="Journey A1",
        description="Core journey",
        level=LevelChoices.A1,
        order=1,
    )
    db_session.add(course)
    await db_session.flush()
    lesson = Lesson(course_id=course.id,title="First lesson",order=1)
    db_session.add(lesson)
    await db_session.flush()
    exercise = Exercise(
        lesson_id=lesson.id,
        type=ExerciseType.CHOICE,
        question="Say hello",
        options={"items":["hello","bye"]},
        correct_answer="hello",
    )
    db_session.add(exercise)
    await db_session.commit()

    learning = LearningPathService(LearningPathRepository(db_session))
    await learning.start_language(first.id,language.id)
    await learning.ensure_lesson_access(first.id,lesson.id)

    exercises = ExerciseService(
        ExerciseRepository(db_session),
        ProgressRepository(db_session),
        ExerciseProgressRepository(db_session),
        GamificationRepository(db_session),
        AchievementRepository(db_session),
        ExerciseSubmissionRepository(db_session),
    )
    wrong = await exercises.submit_exercise(
        exercise.id,ExerciseSubmit(answer="bye"),first.id,"journey-wrong"
    )
    correct = await exercises.submit_exercise(
        exercise.id,ExerciseSubmit(answer="hello"),first.id,"journey-correct"
    )

    first_hearts = await db_session.scalar(
        select(Hearts.hearts).where(Hearts.user_id == first.id)
    )
    second_hearts = await db_session.scalar(
        select(Hearts.hearts).where(Hearts.user_id == second.id)
    )
    xp = await db_session.scalar(
        select(func.coalesce(func.sum(XPHistory.xp),0)).where(
            XPHistory.user_id == first.id
        )
    )
    streak = await db_session.scalar(
        select(Streak).where(Streak.user_id == first.id)
    )
    progress = await db_session.scalar(
        select(UserProgress).where(
            UserProgress.user_id == first.id,
            UserProgress.lesson_id == lesson.id,
        )
    )

    assert wrong.correct is False
    assert correct.correct is True
    assert first_hearts == 4
    assert second_hearts == 5
    assert xp == 10
    assert streak.current_streak == 1
    assert progress.completed is True

    chats = ChatService(ChatRepository(db_session))
    chat = await chats.create_private_chat(
        ChatCreate(participant_username=second.username),first.id
    )
    message = await chats.create_message(
        chat.id,first.id,MessageCreate(content="Hello from the lesson")
    )
    members = await chats.get_members(chat.id)

    assert {member.user_id for member in members} == {first.id,second.id}
    assert message.content == "Hello from the lesson"
    assert message.created_at.tzinfo is not None
