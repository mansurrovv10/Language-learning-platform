import uuid

from backend.repositories.progress_repo import ProgressRepository


class ProgressService:
    def __init__(self, repository: ProgressRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, progress_id: int):
        return await self.repository.get_by_id(progress_id)

    async def get_by_user(self, user_id: uuid.UUID):
        return await self.repository.get_by_user(user_id)

    async def get_by_lesson(self, lesson_id: int):
        return await self.repository.get_by_lesson(lesson_id)

    async def create(self, data):
        return await self.repository.create(data)

    async def update(self, progress_id: int, data):
        return await self.repository.update(progress_id, data)

    async def delete(self, progress_id: int):
        return await self.repository.delete(progress_id)