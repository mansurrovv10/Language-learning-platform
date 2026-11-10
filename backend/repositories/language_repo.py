from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.language import Language
from backend.pagination import literal_search_pattern, normalize_page


class LanguageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, is_admin: bool = False):
        query = select(Language)

        if not is_admin:
            query = query.where(Language.is_active.is_(True))

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_paged(self, q=None, limit=20, offset=0, is_admin=False):
        q, limit, offset = normalize_page(q, limit, offset)
        filters = []
        if not is_admin:
            filters.append(Language.is_active.is_(True))
        if q:
            pattern = literal_search_pattern(q)
            filters.append(or_(
                Language.name.ilike(pattern,escape="\\"),
                Language.code.ilike(pattern,escape="\\"),
            ))
        total = int(await self.session.scalar(
            select(func.count()).select_from(Language).where(*filters)) or 0)
        items = list(await self.session.scalars(
            select(Language).where(*filters).order_by(Language.name, Language.id)
            .limit(limit).offset(offset)))
        return items, total

    async def get_by_id(self, language_id: int):
        result = await self.session.execute(
            select(Language).where(Language.id == language_id)
        )
        return result.scalar_one_or_none()


    async def create(self, data):
        language = Language(
            code=data.code,
            name=data.name,
            is_active=data.is_active
        )

        self.session.add(language)

        try:
            await self.session.commit()
            await self.session.refresh(language)
            return language
        except IntegrityError:
            await self.session.rollback()
            raise

    async def update(self, language_id: int, data):
        language = await self.get_by_id(language_id)

        if not language:
            return None

        if data.code is not None:
            language.code = data.code

        if data.name is not None:
            language.name = data.name

        if data.is_active is not None:
            language.is_active = data.is_active

        await self.session.commit()
        await self.session.refresh(language)
        return language

    async def delete(self, language_id: int):
        language = await self.get_by_id(language_id)

        if not language:
            return False

        language.is_active = False
        await self.session.commit()
        return True
