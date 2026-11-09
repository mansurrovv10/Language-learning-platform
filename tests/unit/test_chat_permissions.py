import uuid
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.api.chat_ws import ConnectionManager
from backend.models.chat import ChatType
from backend.schemas.chat_schema import ChatCreate,MessageCreate,MessageUpdate
from backend.services.chat_service import ChatService


class FakeWebSocket:
    def __init__(self):
        self.accept_count = 0

    async def accept(self):
        self.accept_count += 1


class FakeChatRepository:
    def __init__(self,creator_id,participant):
        self.creator_id = creator_id
        self.participant = participant
        self.created = None

    async def get_user_by_username(self,username):
        return self.participant if username == self.participant.username else None

    async def create_private_chat(self,chat,user_ids):
        self.created = (chat,list(user_ids))
        return chat


class FakeMembershipRepository:
    def __init__(self,creator_id,actor_id,target):
        self.chat = SimpleNamespace(
            id=uuid.uuid4(),creator_id=creator_id,type=ChatType.PRIVATE
        )
        self.actor_id = actor_id
        self.target = target

    async def get_by_id(self,chat_id):
        return self.chat

    async def get_member(self,chat_id,user_id):
        if user_id in {self.creator_id,self.actor_id}:
            return SimpleNamespace(chat_id=chat_id,user_id=user_id)
        return None

    @property
    def creator_id(self):
        return self.chat.creator_id

    async def get_user_by_username(self,username):
        return self.target

    async def get_members(self,chat_id):
        return [
            SimpleNamespace(user_id=self.creator_id),
            SimpleNamespace(user_id=self.actor_id),
        ]



@pytest.mark.asyncio(loop_scope="function")
async def test_connection_manager_does_not_accept_twice():
    manager = ConnectionManager()
    websocket = FakeWebSocket()

    await manager.connect(uuid.uuid4(),websocket)

    assert websocket.accept_count == 0


@pytest.mark.parametrize("schema",[MessageCreate,MessageUpdate])
@pytest.mark.parametrize("content",["","   ","x" * 2001])
def test_message_content_is_bounded_and_nonblank(schema,content):
    with pytest.raises(ValidationError):
        schema(content=content)


@pytest.mark.asyncio(loop_scope="function")
async def test_private_chat_is_created_with_exactly_two_members():
    creator_id = uuid.uuid4()
    participant = SimpleNamespace(
        id=uuid.uuid4(),username="partner",is_active=True
    )
    repository = FakeChatRepository(creator_id,participant)

    chat = await ChatService(repository).create_private_chat(
        ChatCreate(participant_username="partner"),creator_id
    )

    assert chat.type == ChatType.PRIVATE
    assert repository.created[1] == [creator_id,participant.id]


@pytest.mark.asyncio(loop_scope="function")
async def test_private_chat_rejects_self_chat():
    creator_id = uuid.uuid4()
    participant = SimpleNamespace(
        id=creator_id,username="self",is_active=True
    )

    with pytest.raises(ValueError,match="SELF_CHAT_NOT_ALLOWED"):
        await ChatService(
            FakeChatRepository(creator_id,participant)
        ).create_private_chat(ChatCreate(participant_username="self"),creator_id)


def test_group_chat_creation_is_disabled():
    with pytest.raises(ValidationError):
        ChatCreate(type=ChatType.GROUP,participant_username="partner")


@pytest.mark.asyncio(loop_scope="function")
async def test_ordinary_member_cannot_add_user():
    creator_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    target = SimpleNamespace(id=uuid.uuid4(),username="third",is_active=True)
    service = ChatService(FakeMembershipRepository(creator_id,actor_id,target))

    with pytest.raises(PermissionError,match="CHAT_CREATOR_REQUIRED"):
        await service.add_member_authorized(
            service.repository.chat.id,"third",actor_id,is_admin=False
        )


@pytest.mark.asyncio(loop_scope="function")
async def test_private_chat_rejects_third_member_even_for_creator():
    creator_id = uuid.uuid4()
    target = SimpleNamespace(id=uuid.uuid4(),username="third",is_active=True)
    service = ChatService(
        FakeMembershipRepository(creator_id,uuid.uuid4(),target)
    )

    with pytest.raises(ValueError,match="PRIVATE_CHAT_FULL"):
        await service.add_member_authorized(
            service.repository.chat.id,"third",creator_id,is_admin=False
        )

