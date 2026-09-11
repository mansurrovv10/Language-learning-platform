from uuid import UUID

from sqlalchemy import delete,select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.chat import Chat,ChatMember
from backend.models.message import Message


class ChatRepository:

    def __init__(self,session: AsyncSession):
        self.session = session

    async def create(self,chat: Chat) -> Chat:
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def get_by_id(self,chat_id: UUID) -> Chat | None:
        result = await self.session.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Chat]:
        result = await self.session.execute(
            select(Chat)
        )
        return list(result.scalars().all())

    async def get_user_chats(self,user_id: UUID) -> list[Chat]:
        result = await self.session.execute(
            select(Chat)
            .join(ChatMember,Chat.id == ChatMember.chat_id)
            .where(ChatMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def add_member(self,member: ChatMember) -> ChatMember:
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def get_member(self,chat_id: UUID,user_id: UUID) -> ChatMember | None:
        result = await self.session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_members(self,chat_id: UUID) -> list[ChatMember]:
        result = await self.session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id
            )
        )
        return list(result.scalars().all())

    async def remove_member(self,chat_id: UUID,user_id: UUID) -> bool:
        result = await self.session.execute(
            delete(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id
            )
        )
        await self.session.commit()
        return result.rowcount > 0

    async def create_message(self,message: Message) -> Message:
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_messages(self,chat_id: UUID) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def get_message(self,message_id: UUID) -> Message | None:
        result = await self.session.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def update_message(self,message_id: UUID,content: str) -> Message | None:
        message = await self.get_message(message_id)

        if message is None:
            return None

        message.content = content

        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def mark_message_as_read(self,message_id: UUID) -> Message | None:
        message = await self.get_message(message_id)

        if message is None:
            return None

        message.is_read = True

        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def delete_message(self,message_id: UUID) -> bool:
        result = await self.session.execute(
            delete(Message).where(
                Message.id == message_id
            )
        )
        await self.session.commit()
        return result.rowcount > 0