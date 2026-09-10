from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.database import get_session
from backend.repositories.course import CourseRepository
from backend.schemas.course import CourseCreate, CourseUpdate, CourseResponse
from backend.services.course import CourseService


router = APIRouter(prefix="/courses", tags=["Courses"])


def get_course_service(session: AsyncSession = Depends(get_session)):
    repository = CourseRepository(session)
    return CourseService(repository)


@router.get("", response_model=list[CourseResponse])
async def get_courses(service: CourseService = Depends(get_course_service)):
    return await service.get_all()


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    service: CourseService = Depends(get_course_service)
):
    course = await service.get_by_id(course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.get("/language/{language_id}", response_model=list[CourseResponse])
async def get_courses_by_language(
    language_id: int,
    service: CourseService = Depends(get_course_service)
):
    return await service.get_by_language(language_id)


@router.post("", response_model=CourseResponse)
async def create_course(
    data: CourseCreate,
    service: CourseService = Depends(get_course_service)
):
    return await service.create(data)


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    service: CourseService = Depends(get_course_service)
):
    course = await service.update(course_id, data)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    service: CourseService = Depends(get_course_service)
):
    result = await service.delete(course_id)

    if not result:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"message": "Course deleted"}