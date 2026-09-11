import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.reaction import MessageReaction


class ReactionRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_by_message(self,message_id: uuid.UUID) -> list[MessageReaction]:
        result = await self.session.execute(
            select(MessageReaction)
            .where(MessageReaction.message_id == message_id)
            .order_by(MessageReaction.created_at)
        )
        return list(result.scalars().all())

    async def get_one(
        self,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        reaction: str
    ) -> MessageReaction | None:
        result = await self.session.execute(
            select(MessageReaction).where(
                MessageReaction.message_id == message_id,
                MessageReaction.user_id == user_id,
                MessageReaction.reaction == reaction
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        reaction: str
    ) -> MessageReaction:
        existing = await self.get_one(message_id,user_id,reaction)

        if existing:
            return existing

        item = MessageReaction(
            message_id=message_id,
            user_id=user_id,
            reaction=reaction,
            created_at=datetime.utcnow()
        )

        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)

        return item

    async def remove(
        self,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        reaction: str
    ) -> bool:
        item = await self.get_one(message_id,user_id,reaction)

        if not item:
            return False

        await self.session.delete(item)
        await self.session.commit()

        return True