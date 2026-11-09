import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import backend.api.chat_ws as chat_ws
from backend.repositories.chat_repo import ChatRepository
from backend.schemas.chat_schema import ChatCreate,MessageCreate
from backend.services.auth_ser import AuthService
from backend.services.chat_service import ChatService


pytestmark = pytest.mark.integration


class FakeSession:
    def __init__(self,is_active=True):
        self.is_active = is_active

    async def get(self,model,user_id):
        return SimpleNamespace(id=user_id,is_active=self.is_active)


class FakeSessionContext:
    def __init__(self,is_active=True):
        self.is_active = is_active

    async def __aenter__(self):
        return FakeSession(self.is_active)

    async def __aexit__(self,exc_type,exc,tb):
        return False


def test_websocket_authenticates_after_single_accept(monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setattr(chat_ws,"SessionLocal",lambda: FakeSessionContext())
    monkeypatch.setattr(
        chat_ws.AuthService,
        "decode_token",
        lambda self,token:{"type":"access","sub":str(user_id)},
    )
    app = FastAPI()
    app.include_router(chat_ws.websocket_router)

    with TestClient(app).websocket_connect("/ws/chats") as websocket:
        websocket.send_json({"type":"auth","access_token":"valid"})
        assert websocket.receive_json() == {"type":"auth.ok"}


def test_websocket_rejects_invalid_token_with_4401(monkeypatch):
    monkeypatch.setattr(chat_ws,"SessionLocal",lambda: FakeSessionContext())
    monkeypatch.setattr(
        chat_ws.AuthService,"decode_token",lambda self,token:None
    )
    app = FastAPI()
    app.include_router(chat_ws.websocket_router)

    with TestClient(app).websocket_connect("/ws/chats") as websocket:
        websocket.send_json({"type":"auth","access_token":"invalid"})
        assert websocket.receive_json()["code"] == "UNAUTHORIZED"
        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_json()

    assert error.value.code == 4401


def test_websocket_rejects_inactive_user_with_4403(monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setattr(
        chat_ws,"SessionLocal",lambda: FakeSessionContext(is_active=False)
    )
    monkeypatch.setattr(
        chat_ws.AuthService,
        "decode_token",
        lambda self,token:{"type":"access","sub":str(user_id)},
    )
    app = FastAPI()
    app.include_router(chat_ws.websocket_router)

    with TestClient(app).websocket_connect("/ws/chats") as websocket:
        websocket.send_json({"type":"auth","access_token":"valid"})
        assert websocket.receive_json()["code"] == "FORBIDDEN"
        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_json()

    assert error.value.code == 4403


@pytest.mark.asyncio(loop_scope="session")
async def test_private_chat_membership_and_messages_are_enforced(db_session):
    auth = AuthService(db_session)
    creator = await auth.register(
        f"chat-creator-{uuid.uuid4().hex}@example.com",
        f"chat_creator_{uuid.uuid4().hex}",
        "password123",
    )
    participant = await auth.register(
        f"chat-participant-{uuid.uuid4().hex}@example.com",
        f"chat_participant_{uuid.uuid4().hex}",
        "password123",
    )
    outsider = await auth.register(
        f"chat-outsider-{uuid.uuid4().hex}@example.com",
        f"chat_outsider_{uuid.uuid4().hex}",
        "password123",
    )
    service = ChatService(ChatRepository(db_session))
    chat = await service.create_private_chat(
        ChatCreate(participant_username=participant.username),creator.id
    )

    members = await service.get_members(chat.id)
    assert {member.user_id for member in members} == {creator.id,participant.id}

    with pytest.raises(ValueError,match="PRIVATE_CHAT_FULL"):
        await service.add_member_authorized(
            chat.id,outsider.username,creator.id,is_admin=False
        )
    with pytest.raises(PermissionError,match="CHAT_MEMBER_REQUIRED"):
        await service.create_message(
            chat.id,outsider.id,MessageCreate(content="not allowed")
        )
    with pytest.raises(PermissionError,match="CHAT_MEMBER_REQUIRED"):
        await service.get_messages_authorized(chat.id,outsider.id)

    message = await service.create_message(
        chat.id,creator.id,MessageCreate(content="  hello  ")
    )
    assert message.content == "hello"
    assert message.created_at.tzinfo is not None

