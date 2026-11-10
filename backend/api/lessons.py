from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_admin
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.learning_path_repo import LearningPathRepository
from backend.repositories.lessons_repo import LessonRepository
from backend.schemas.lessons_schema import LessonCreate, LessonResponse, LessonUpdate
from backend.schemas.page_schema import Page
from backend.services.learning_path_service import LearningPathService
from backend.services.lessons_service import LessonService

router = APIRouter(prefix="/lessons", tags=["Lessons"])


def get_lesson_service(session: AsyncSession = Depends(get_session)):
    repository = LessonRepository(session)
    return LessonService(repository)


def get_learning_path_service(session: AsyncSession = Depends(get_session)):
    return LearningPathService(LearningPathRepository(session))


@router.get("", response_model=list[LessonResponse])
async def get_lessons(
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.get_all()


@router.get("/paged", response_model=Page[LessonResponse])
async def get_lessons_paged(
    q: str | None = Query(default=None,max_length=100),
    limit: int = Query(default=20,ge=1,le=100),
    offset: int = Query(default=0,ge=0),
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)):
    items,total = await service.get_paged(q,limit,offset)
    return Page(items=items,total=total,limit=limit,offset=offset)


@router.get("/course/{course_id}", response_model=list[LessonResponse])
async def get_lessons_by_course(course_id: int,service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(get_current_user),
    access_service: LearningPathService = Depends(get_learning_path_service)):
    if current_user.role.value != "admin":
        await access_service.ensure_course_access(current_user.id,course_id)
    return await service.get_by_course(course_id)


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: int,service: LessonService = Depends(get_lesson_service),
          current_user: UserProfile = Depends(get_current_user),
          access_service: LearningPathService = Depends(get_learning_path_service)):
    if current_user.role.value != "admin":
        await access_service.ensure_lesson_access(current_user.id,lesson_id)
    lesson = await service.get_by_id(lesson_id)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.post("", response_model=LessonResponse)
async def create_lesson(data: LessonCreate,service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.create(data)


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(lesson_id: int,data: LessonUpdate,
    service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)):
    lesson = await service.update(lesson_id, data)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: int,service: LessonService = Depends(get_lesson_service),
    current_user: UserProfile = Depends(require_admin)):
    result = await service.delete(lesson_id)

    if not result:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"message": "Lesson deleted"}
