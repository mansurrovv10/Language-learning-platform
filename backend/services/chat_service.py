from uuid import UUID
from backend.models.chat import Chat,ChatMember,ChatType
from backend.models.message import Message
from backend.repositories.chat_repo import ChatRepository
from backend.schemas.chat_schema import ChatCreate,MessageCreate


class ChatService:

    def __init__(self,repository: ChatRepository):
        self.repository = repository

    async def create_private_chat(self,data: ChatCreate,creator_id: UUID):
        participant = await self.repository.get_user_by_username(
            data.participant_username
        )
        if participant is None or not participant.is_active:
            raise ValueError("PARTICIPANT_NOT_FOUND")
        if participant.id == creator_id:
            raise ValueError("SELF_CHAT_NOT_ALLOWED")

        chat = Chat(
            creator_id=creator_id,
            type=ChatType.PRIVATE,
            language_id=data.language_id)
        return await self.repository.create_private_chat(
            chat,[creator_id,participant.id]
        )

    async def get_chat(self,chat_id: UUID):
        return await self.repository.get_by_id(chat_id)

    async def get_all_chats(self):
        return await self.repository.get_all()

    async def get_user_chats(self,user_id: UUID):
        return await self.repository.get_user_chats(user_id)

    async def get_user_by_username(self,username: str):
        return await self.repository.get_user_by_username(username)

    async def add_member(self,chat_id: UUID,user_id: UUID):
        member = ChatMember(
            chat_id=chat_id,
            user_id=user_id)
        return await self.repository.add_member(member)

    async def add_member_authorized(
        self,
        chat_id: UUID,
        username: str,
        actor_id: UUID,
        is_admin: bool,
    ):
        chat = await self.repository.get_by_id(chat_id)
        if chat is None:
            raise ValueError("CHAT_NOT_FOUND")
        if not is_admin and chat.creator_id != actor_id:
            raise PermissionError("CHAT_CREATOR_REQUIRED")

        user = await self.repository.get_user_by_username(username)
        if user is None or not user.is_active:
            raise ValueError("USER_NOT_FOUND")
        if await self.repository.get_member(chat_id,user.id):
            raise ValueError("ALREADY_MEMBER")
        if chat.type == ChatType.PRIVATE:
            raise ValueError("PRIVATE_CHAT_FULL")

        return await self.add_member(chat_id,user.id)

    async def get_member(self,chat_id: UUID,user_id: UUID):
        return await self.repository.get_member(chat_id,user_id)

    async def get_members(self,chat_id: UUID):
        return await self.repository.get_members(chat_id)

    async def remove_member(self,chat_id: UUID,user_id: UUID):
        return await self.repository.remove_member(chat_id,user_id)

    async def remove_member_authorized(
        self,
        chat_id: UUID,
        user_id: UUID,
        actor_id: UUID,
        is_admin: bool,
    ):
        chat = await self.repository.get_by_id(chat_id)
        if chat is None:
            raise ValueError("CHAT_NOT_FOUND")
        if await self.repository.get_member(chat_id,user_id) is None:
            raise ValueError("MEMBER_NOT_FOUND")
        if user_id != actor_id and not is_admin and chat.creator_id != actor_id:
            raise PermissionError("CHAT_CREATOR_REQUIRED")
        return await self.repository.remove_member(chat_id,user_id)

    async def create_message(
        self,chat_id: UUID,sender_id: UUID,data: MessageCreate):
        if await self.repository.get_member(chat_id,sender_id) is None:
            raise PermissionError("CHAT_MEMBER_REQUIRED")
        message = Message(
            chat_id=chat_id,
            sender_id=sender_id,
            content=data.content.strip())
        return await self.repository.create_message(message)

    async def get_messages(self,chat_id: UUID):
        return await self.repository.get_messages(chat_id)

    async def get_messages_authorized(
        self,chat_id: UUID,user_id: UUID,is_admin: bool = False
    ):
        if not is_admin and await self.repository.get_member(chat_id,user_id) is None:
            raise PermissionError("CHAT_MEMBER_REQUIRED")
        return await self.repository.get_messages(chat_id)

    async def get_message(self,message_id: UUID):
        return await self.repository.get_message(message_id)

    async def update_message(self,message_id: UUID,content: str):
        return await self.repository.update_message(message_id,content.strip())

    async def update_message_authorized(
        self,
        chat_id: UUID,
        message_id: UUID,
        actor_id: UUID,
        content: str,
        is_admin: bool = False,
    ):
        message = await self.repository.get_message(message_id)
        if message is None or message.chat_id != chat_id:
            raise ValueError("MESSAGE_NOT_FOUND")
        if not is_admin and await self.repository.get_member(chat_id,actor_id) is None:
            raise PermissionError("CHAT_MEMBER_REQUIRED")
        if not is_admin and message.sender_id != actor_id:
            raise PermissionError("MESSAGE_OWNER_REQUIRED")
        return await self.repository.update_message(message_id,content.strip())

    async def mark_message_as_read(self,message_id: UUID):
        return await self.repository.mark_message_as_read(message_id)

    async def delete_message(self,message_id: UUID):
        return await self.repository.delete_message(message_id)

    async def delete_message_authorized(
        self,
        chat_id: UUID,
        message_id: UUID,
        actor_id: UUID,
        is_admin: bool = False,
    ):
        message = await self.repository.get_message(message_id)
        if message is None or message.chat_id != chat_id:
            raise ValueError("MESSAGE_NOT_FOUND")
        if not is_admin and await self.repository.get_member(chat_id,actor_id) is None:
            raise PermissionError("CHAT_MEMBER_REQUIRED")
        if not is_admin and message.sender_id != actor_id:
            raise PermissionError("MESSAGE_OWNER_REQUIRED")
        return await self.repository.delete_message(message_id)
