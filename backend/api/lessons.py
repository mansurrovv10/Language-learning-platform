from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.repositories.lessons_repo import LessonRepository
from backend.schemas.lessons_schema import LessonCreate, LessonUpdate, LessonResponse
from backend.services.lessons_service import LessonService
from backend.api.auth import get_current_user, require_admin
from backend.models.user import UserProfile


router = APIRouter(prefix="/lessons", tags=["Lessons"])


def get_lesson_service(session: AsyncSession = Depends(get_session)):
    repository = LessonRepository(session)
    return LessonService(repository)


@router.get("", response_model=list[LessonResponse])
async def get_lessons(
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.get_all()


@router.get("/course/{course_id}", response_model=list[LessonResponse])
async def get_lessons_by_course(
    course_id: int,
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.get_by_course(course_id)


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(get_current_user)
):
    lesson = await service.get_by_id(lesson_id)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return lesson


@router.post("", response_model=LessonResponse)
async def create_lesson(
    data: LessonCreate,
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)
):
    return await service.create(data)


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)
):
    lesson = await service.update(lesson_id, data)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return lesson


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)
):
    result = await service.delete(lesson_id)

    if not result:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"message": "Lesson deleted"}