from uuid import UUID
from datetime import datetime, timezone

from backend.models.chat import Chat, ChatMember
from backend.repositories.repo_chat import ChatRepository
from backend.schemas.chat import ChatCreate


class ChatService:

    def __init__(self, repository: ChatRepository):
        self.repository = repository

    async def create_chat(self, data: ChatCreate) -> Chat:
        chat = Chat(
            type=data.type,
            language_id=data.language_id,
            created_at=datetime.now(timezone.utc)
        )

        return await self.repository.create(chat)

    async def get_chat(self, chat_id: UUID) -> Chat | None:
        return await self.repository.get_by_id(chat_id)

    async def get_all_chats(self) -> list[Chat]:
        return await self.repository.get_all()

    async def add_member(
        self,
        chat_id: UUID,
        user_id: UUID
    ) -> ChatMember:

        member = ChatMember(
            chat_id=chat_id,
            user_id=user_id,
            joined_at=datetime.now(timezone.utc)
        )

        return await self.repository.add_member(member)