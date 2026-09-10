from backend.repositories.language_repo import LanguageRepository


class LanguageService:
    def __init__(self, repository: LanguageRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, language_id: int):
        return await self.repository.get_by_id(language_id)

    async def create(self, data):
        return await self.repository.create(data)

    async def update(self, language_id: int, data):
        return await self.repository.update(language_id, data)

    async def delete(self, language_id: int):
        return await self.repository.delete(language_id)