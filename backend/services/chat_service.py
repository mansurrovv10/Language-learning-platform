from datetime import datetime
from uuid import UUID

from backend.models.chat import Chat, ChatMember
from backend.models.message import Message
from backend.models.reaction import MessageReaction
from backend.repositories.chat_repo import ChatRepository
from backend.schemas.chat_schema import (
    ChatCreate,
    MessageCreate,
    ReactionCreate,
)


class ChatService:

    def __init__(self, repository: ChatRepository):
        self.repository = repository



    async def create_chat(self, data: ChatCreate):
        chat = Chat(
            type=data.type,
            language_id=data.language_id,
            created_at=datetime.now()
        )

        return await self.repository.create(chat)

    async def get_chat(self, chat_id: UUID):
        return await self.repository.get_by_id(chat_id)

    async def get_all_chats(self):
        return await self.repository.get_all()



    async def add_member(
        self,
        chat_id: UUID,
        user_id: UUID
    ):

        member = ChatMember(
            chat_id=chat_id,
            user_id=user_id,
            joined_at=datetime.now()
        )

        return await self.repository.add_member(member)

    async def get_member(
        self,
        chat_id: UUID,
        user_id: UUID
    ):

        return await self.repository.get_member(
            chat_id,
            user_id
        )

    async def get_members(
        self,
        chat_id: UUID
    ):

        return await self.repository.get_members(chat_id)

    async def remove_member(
        self,
        chat_id: UUID,
        user_id: UUID
    ) -> bool:

        return await self.repository.remove_member(
            chat_id,
            user_id
        )



    async def create_message(
        self,
        chat_id: UUID,
        sender_id: UUID,
        data: MessageCreate
    ):

        message = Message(
            chat_id=chat_id,
            sender_id=sender_id,
            content=data.content,
            created_at=datetime.now()
        )

        return await self.repository.create_message(message)

    async def get_messages(
        self,
        chat_id: UUID
    ):

        return await self.repository.get_messages(chat_id)

    async def get_message(
        self,
        message_id: UUID
    ):

        return await self.repository.get_message(message_id)

    async def update_message(
        self,
        message_id: UUID,
        content: str
    ):

        return await self.repository.update_message(
            message_id,
            content
        )

    async def mark_message_as_read(
        self,
        message_id: UUID
    ):

        return await self.repository.mark_message_as_read(
            message_id
        )

    async def delete_message(
        self,
        message_id: UUID
    ):

        return await self.repository.delete_message(message_id)



    async def create_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        data: ReactionCreate
    ):

        reaction = MessageReaction(
            message_id=message_id,
            user_id=user_id,
            reaction=data.reaction,
            created_at=datetime.now()
        )

        return await self.repository.create_reaction(
            reaction
        )

    async def get_reactions(
        self,
        message_id: UUID
    ):

        return await self.repository.get_reactions(
            message_id
        )

    async def get_reaction(
        self,
        message_id: UUID,
        user_id: UUID
    ):

        return await self.repository.get_reaction(
            message_id,
            user_id
        )

    async def delete_reaction(
        self,
        message_id: UUID,
        user_id: UUID
    ) -> bool:

        return await self.repository.delete_reaction(
            message_id,
            user_id
        )