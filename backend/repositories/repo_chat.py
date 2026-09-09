from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.chat import Chat, ChatMember


class ChatRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, chat: Chat):
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)

        return chat

    async def get_by_id(self, chat_id: UUID):
        result = await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )

        return result.scalar_one_or_none()

    async def get_all(self) -> list[Chat]:
        result = await self.session.execute(
            select(Chat)
        )

        return list(result.scalars().all())

    async def add_member(self, member: ChatMember):
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)

        return member

    async def get_member(
        self,
        chat_id: UUID,
        user_id: UUID
    ) -> ChatMember | None:
        result = await self.session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id
            )
        )

        return result.scalar_one_or_none()