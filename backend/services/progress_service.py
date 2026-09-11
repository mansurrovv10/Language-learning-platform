import uuid

from backend.repositories.progress_repo import ProgressRepository


class ProgressService:
    def __init__(self,repository: ProgressRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self,progress_id: int):
        return await self.repository.get_by_id(progress_id)

    async def get_by_user(self,user_id: uuid.UUID):
        return await self.repository.get_by_user(user_id)

    async def get_by_lesson(self,lesson_id: int):
        return await self.repository.get_by_lesson(lesson_id)

    async def get_by_user_and_lesson(self,user_id: uuid.UUID,lesson_id: int):
        return await self.repository.get_by_user_and_lesson(
            user_id,
            lesson_id
        )

    async def update(self,progress_id: int,completed: bool | None = None,score: int | None = None):
        return await self.repository.update(
            progress_id,
            completed,
            score
        )

    async def delete(self,progress_id: int):
        return await self.repository.delete(progress_id)