from backend.repositories.lesson import LessonRepository


class LessonService:
    def __init__(self, repository: LessonRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, lesson_id: int):
        return await self.repository.get_by_id(lesson_id)

    async def get_by_course(self, course_id: int):
        return await self.repository.get_by_course(course_id)

    async def create(self, data):
        return await self.repository.create(data)

    async def update(self, lesson_id: int, data):
        return await self.repository.update(lesson_id, data)

    async def delete(self, lesson_id: int):
        return await self.repository.delete(lesson_id)