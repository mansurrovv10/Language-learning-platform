from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import require_admin
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.course_repo import CourseRepository
from backend.schemas.course_schema import CourseCreate, CourseResponse, CourseUpdate
from backend.schemas.page_schema import Page
from backend.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])


def get_course_service(session: AsyncSession = Depends(get_session)):
    repository = CourseRepository(session)
    return CourseService(repository)


@router.get("", response_model=list[CourseResponse])
async def get_courses(service: CourseService = Depends(get_course_service)):
    return await service.get_all()


@router.get("/paged", response_model=Page[CourseResponse])
async def get_courses_paged(
    q: str | None = Query(default=None,max_length=100),
    limit: int = Query(default=20,ge=1,le=100),
    offset: int = Query(default=0,ge=0),
    service: CourseService = Depends(get_course_service)):
    items,total = await service.get_paged(q,limit,offset)
    return Page(items=items,total=total,limit=limit,offset=offset)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int,service: CourseService = Depends(get_course_service)):
    course = await service.get_by_id(course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.get("/language/{language_id}", response_model=list[CourseResponse])
async def get_courses_by_language(language_id: int,service: CourseService = Depends(get_course_service)):
    return await service.get_by_language(language_id)


@router.post("", response_model=CourseResponse)
async def create_course(data: CourseCreate,service: CourseService = Depends(get_course_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.create(data)


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(course_id: int,data: CourseUpdate,
    service: CourseService = Depends(get_course_service),
    current_user: UserProfile = Depends(require_admin)):
    course = await service.update(course_id, data)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.delete("/{course_id}")
async def delete_course(course_id: int,service: CourseService = Depends(get_course_service),
    current_user: UserProfile = Depends(require_admin)):
    result = await service.delete(course_id)

    if not result:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"message": "Course deleted"}
