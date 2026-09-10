from backend.models.course import Course
from backend.repositories.course_repo import CourseRepository
from backend.schemas.course_schema import CourseCreate, CourseUpdate


class CourseService:
    def __init__(self, repository: CourseRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, course_id: int):
        return await self.repository.get_by_id(course_id)

    async def get_by_language(self, language_id: int):
        return await self.repository.get_by_language(language_id)

    async def create(self, data: CourseCreate):
        course = Course(**data.model_dump())
        return await self.repository.create(course)

    async def update(self, course_id: int, data: CourseUpdate):
        course = await self.repository.get_by_id(course_id)

        if not course:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(course, key, value)

        return await self.repository.update(course)

    async def delete(self, course_id: int):
        course = await self.repository.get_by_id(course_id)

        if not course:
            return False

        await self.repository.delete(course)
        return True