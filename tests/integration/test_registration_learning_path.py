import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from backend.models.course import Course, LevelChoices
from backend.models.gamification import Hearts
from backend.models.language import Language
from backend.models.lesson import Lesson
from backend.models.user import UserProfile
from backend.repositories.learning_path_repo import LearningPathRepository
from backend.services.auth_ser import AuthService
from backend.services.learning_path_service import LearningPathService


pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_registration_creates_five_hearts(db_session):
    user = await AuthService(db_session).register(
        f"user-{uuid.uuid4().hex}@example.com",
        f"user_{uuid.uuid4().hex}",
        "password123",
    )
    hearts = await db_session.scalar(select(Hearts).where(Hearts.user_id == user.id))

    assert hearts is not None
    assert hearts.hearts == 5


async def test_registered_users_have_isolated_heart_rows(db_session):
    service = AuthService(db_session)
    first = await service.register(
        f"first-{uuid.uuid4().hex}@example.com",
        f"first_{uuid.uuid4().hex}",
        "password123",
    )
    second = await service.register(
        f"second-{uuid.uuid4().hex}@example.com",
        f"second_{uuid.uuid4().hex}",
        "password123",
    )
    hearts = (
        await db_session.execute(
            select(Hearts).where(Hearts.user_id.in_([first.id, second.id]))
        )
    ).scalars().all()

    assert len(hearts) == 2
    assert {item.user_id for item in hearts} == {first.id, second.id}


async def test_registration_returns_stable_duplicate_email_error(db_session):
    email = f"duplicate-{uuid.uuid4().hex}@example.com"
    service = AuthService(db_session)
    await service.register(email, f"first_{uuid.uuid4().hex}", "password123")

    with pytest.raises(HTTPException) as error:
        await service.register(email.upper(), f"second_{uuid.uuid4().hex}", "password123")

    assert error.value.status_code == 400
    assert error.value.detail == {
        "code": "EMAIL_EXISTS",
        "message": "Email already exists",
    }


async def test_start_language_rejects_inactive_language(db_session):
    user = UserProfile(
        email=f"inactive-{uuid.uuid4().hex}@example.com",
        username=f"inactive_{uuid.uuid4().hex}",
        password_hash="not-used",
    )
    language = Language(code=f"x-{uuid.uuid4().hex[:6]}", name=f"Inactive {uuid.uuid4().hex}")
    db_session.add_all([user, language])
    await db_session.commit()

    service = LearningPathService(LearningPathRepository(db_session))
    with pytest.raises(HTTPException) as error:
        await service.start_language(user.id, language.id)

    assert error.value.status_code == 409
    assert error.value.detail["code"] == "INACTIVE_LANGUAGE"


async def test_start_language_rejects_missing_language(db_session):
    user = UserProfile(
        email=f"missing-{uuid.uuid4().hex}@example.com",
        username=f"missing_{uuid.uuid4().hex}",
        password_hash="not-used",
    )
    db_session.add(user)
    await db_session.commit()

    service = LearningPathService(LearningPathRepository(db_session))
    with pytest.raises(HTTPException) as error:
        await service.start_language(user.id, 2_000_000_000)

    assert error.value.status_code == 404
    assert error.value.detail == {
        "code": "LANGUAGE_NOT_FOUND",
        "message": "Language not found",
    }


async def test_start_language_is_idempotent_for_active_language(db_session):
    user = UserProfile(
        email=f"active-{uuid.uuid4().hex}@example.com",
        username=f"active_{uuid.uuid4().hex}",
        password_hash="not-used",
    )
    language = Language(
        code=f"a-{uuid.uuid4().hex[:6]}",
        name=f"Active {uuid.uuid4().hex}",
        is_active=True,
    )
    db_session.add_all([user, language])
    await db_session.commit()

    service = LearningPathService(LearningPathRepository(db_session))
    first = await service.start_language(user.id, language.id)
    second = await service.start_language(user.id, language.id)
    count = await db_session.scalar(
        select(func.count()).select_from(type(first)).where(type(first).user_id == user.id)
    )

    assert first.id == second.id
    assert first.level == LevelChoices.A1
    assert count == 1


async def test_unstarted_language_does_not_grant_lesson_access(db_session):
    user = UserProfile(
        email=f"locked-{uuid.uuid4().hex}@example.com",
        username=f"locked_{uuid.uuid4().hex}",
        password_hash="not-used",
    )
    language = Language(
        code=f"l-{uuid.uuid4().hex[:6]}",
        name=f"Locked {uuid.uuid4().hex}",
        is_active=True,
    )
    db_session.add_all([user, language])
    await db_session.flush()
    course = Course(
        language_id=language.id,
        title="A1",
        description="A1 course",
        level=LevelChoices.A1,
        order=1,
    )
    db_session.add(course)
    await db_session.flush()
    lesson = Lesson(course_id=course.id, title="First lesson", order=1)
    db_session.add(lesson)
    await db_session.commit()

    service = LearningPathService(LearningPathRepository(db_session))
    with pytest.raises(HTTPException) as error:
        await service.ensure_lesson_access(user.id, lesson.id)

    assert error.value.status_code == 403
