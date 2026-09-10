import uuid

from backend.repositories.review_repo import ReviewRepository


class ReviewService:
    def __init__(self, repository: ReviewRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, review_id: int):
        return await self.repository.get_by_id(review_id)

    async def get_by_user(self, user_id: uuid.UUID):
        return await self.repository.get_by_user(user_id)

    async def create(self, data):
        return await self.repository.create(data)

    async def update(self, review_id: int, data):
        return await self.repository.update(review_id, data)

    async def delete(self, review_id: int):
        return await self.repository.delete(review_id)