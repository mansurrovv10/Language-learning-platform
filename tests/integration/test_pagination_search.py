import uuid

import pytest

from backend.models.course import Course, LevelChoices
from backend.models.exercise import Exercise, ExerciseType
from backend.models.language import Language
from backend.models.lesson import Lesson
from backend.repositories.chat_repo import ChatRepository
from backend.repositories.course_repo import CourseRepository
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.language_repo import LanguageRepository
from backend.repositories.lessons_repo import LessonRepository
from backend.repositories.user_repo import UserRepository
from backend.schemas.chat_schema import ChatCreate, MessageCreate
from backend.services.auth_ser import AuthService
from backend.services.chat_service import ChatService

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_content_and_user_search_is_case_insensitive_paged_and_stable(db_session):
    """Catches wrong totals, inactive language disclosure, or unstable page order."""
    auth = AuthService(db_session)
    first = await auth.register(
        f"alpha-{uuid.uuid4().hex}@example.com",
        f"AlphaUser_{uuid.uuid4().hex}",
        "password123",
    )
    await auth.register(
        f"beta-{uuid.uuid4().hex}@example.com",
        f"BetaUser_{uuid.uuid4().hex}",
        "password123",
    )
    active = Language(code=f"a-{uuid.uuid4().hex[:6]}",name="Alpha",is_active=True)
    inactive = Language(code=f"h-{uuid.uuid4().hex[:6]}",name="Alpha Hidden",is_active=False)
    literal = Language(code=f"p-{uuid.uuid4().hex[:6]}",name="Progress 100%",is_active=True)
    wildcard = Language(code=f"w-{uuid.uuid4().hex[:6]}",name="Progress 100x",is_active=True)
    db_session.add_all([active,inactive,literal,wildcard])
    await db_session.flush()
    courses = [
        Course(language_id=active.id,title="Alpha Basics",description="First",level=LevelChoices.A1,order=2),
        Course(language_id=active.id,title="Alpha Advanced",description="Second",level=LevelChoices.A2,order=1),
    ]
    db_session.add_all(courses)
    await db_session.flush()
    lessons = [Lesson(course_id=courses[0].id,title="Alpha lesson",order=2),Lesson(course_id=courses[0].id,title="Other",order=1)]
    db_session.add_all(lessons)
    await db_session.flush()
    exercises = [
        Exercise(lesson_id=lessons[0].id,type=ExerciseType.CHOICE,question="Find Alpha",options={},correct_answer="a"),
        Exercise(lesson_id=lessons[0].id,type=ExerciseType.CHOICE,question="Other",options={},correct_answer="a"),
    ]
    db_session.add_all(exercises)
    await db_session.commit()

    languages,total = await LanguageRepository(db_session).get_paged(" ALPHA ",1,0,False)
    assert total == 1 and [item.name for item in languages] == ["Alpha"]
    courses_page,courses_total = await CourseRepository(db_session).get_paged("alpha",1,0)
    assert courses_total == 2 and courses_page[0].order == 1
    lesson_page,lesson_total = await LessonRepository(db_session).get_paged("ALPHA",10,0)
    assert lesson_total == 1 and lesson_page[0].title == "Alpha lesson"
    exercise_page,exercise_total = await ExerciseRepository(db_session).get_paged("alpha",10,0)
    assert exercise_total == 1 and exercise_page[0].question == "Find Alpha"
    user_page,user_total = await UserRepository(db_session).get_paged(first.email.upper(),10,0)
    assert user_total == 1 and user_page[0].id == first.id
    literal_page,literal_total = await LanguageRepository(db_session).get_paged(
        "100%",10,0,False
    )
    assert literal_total == 1 and literal_page[0].id == literal.id


async def test_message_pagination_requires_membership_and_searches_content(db_session):
    """Catches message search leaking private chat data to outsiders."""
    auth = AuthService(db_session)
    creator = await auth.register(f"chat-page-{uuid.uuid4().hex}@example.com",f"chat_page_{uuid.uuid4().hex}","password123")
    member = await auth.register(f"chat-member-{uuid.uuid4().hex}@example.com",f"chat_member_{uuid.uuid4().hex}","password123")
    outsider = await auth.register(f"chat-out-{uuid.uuid4().hex}@example.com",f"chat_out_{uuid.uuid4().hex}","password123")
    service = ChatService(ChatRepository(db_session))
    chat = await service.create_private_chat(ChatCreate(participant_username=member.username),creator.id)
    await service.create_message(chat.id,creator.id,MessageCreate(content="Alpha first"))
    await service.create_message(chat.id,member.id,MessageCreate(content="other"))

    items,total = await service.get_messages_paged_authorized(chat.id,creator.id,"ALPHA",10,0)
    assert total == 1 and [message.content for message in items] == ["Alpha first"]
    with pytest.raises(PermissionError,match="CHAT_MEMBER_REQUIRED"):
        await service.get_messages_paged_authorized(chat.id,outsider.id,None,10,0)
