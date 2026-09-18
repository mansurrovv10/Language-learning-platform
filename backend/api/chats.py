from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import SessionLocal
from backend.api.auth import get_current_user
from backend.models.user import UserProfile
from backend.repositories.chat_repo import ChatRepository
from backend.schemas.chat_schema import (ChatCreate,ChatResponse,ChatMemberCreate,
    ChatMemberResponse,MessageCreate,MessageUpdate,MessageResponse)
from backend.services.chat_service import ChatService


router = APIRouter(prefix="/chats",tags=["Chats"])


async def get_session():
    async with SessionLocal() as session:
        yield session


def get_chat_service(
    session: AsyncSession = Depends(get_session)):
    repository = ChatRepository(session)
    return ChatService(repository)


@router.post("/", response_model=ChatResponse)
async def create_chat(data: ChatCreate,current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    chat = await service.create_chat(data,current_user.id)

    await service.add_member(chat_id=chat.id,user_id=current_user.id)
    return chat


@router.get("/", response_model=list[ChatResponse])
async def get_chats(current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    return await service.get_user_chats(current_user.id)


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: UUID,current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    chat = await service.get_chat(chat_id)

    if chat is None:
        raise HTTPException(status_code=404,detail="Chat not found")

    member = await service.get_member(chat_id,current_user.id)

    if member is None and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return chat


@router.post("/{chat_id}/members",response_model=ChatMemberResponse)
async def add_member(chat_id: UUID,data: ChatMemberCreate,
    current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    user = await service.get_user_by_username(data.username)

    if user is None:
        raise HTTPException(status_code=404,detail="User not found")

    existing_member = await service.get_member(chat_id,user.id)

    if existing_member is not None:
        raise HTTPException(status_code=400,detail="User is already a member")

    return await service.add_member(chat_id=chat_id,user_id=user.id)

@router.get("/{chat_id}/members",response_model=list[ChatMemberResponse])
async def get_members(chat_id: UUID,current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    chat = await service.get_chat(chat_id)

    if chat is None:
        raise HTTPException(status_code=404,detail="Chat not found")

    member = await service.get_member(chat_id,current_user.id)

    if member is None and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return await service.get_members(chat_id)


@router.delete("/{chat_id}/members/{user_id}")
async def remove_member(chat_id: UUID,user_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    chat = await service.get_chat(chat_id)

    if chat is None:
        raise HTTPException(status_code=404,detail="Chat not found")

    member = await service.get_member(chat_id,user_id)

    if member is None:
        raise HTTPException(status_code=404,detail="Member not found")

    current_member = await service.get_member(chat_id,current_user.id)

    if current_member is None and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    if user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="You can only remove yourself")

    await service.remove_member(chat_id,user_id)

    return {"message": "Member removed successfully"}


@router.post("/{chat_id}/messages",response_model=MessageResponse)
async def create_message(chat_id: UUID,data: MessageCreate,
    current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    chat = await service.get_chat(chat_id)

    if chat is None:
        raise HTTPException(status_code=404,detail="Chat not found")

    member = await service.get_member(chat_id,current_user.id)

    if member is None:
        raise HTTPException(status_code=403,detail="User is not a member of this chat")

    return await service.create_message(chat_id,current_user.id,data)


@router.get("/{chat_id}/messages",response_model=list[MessageResponse])
async def get_messages(chat_id: UUID,current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    chat = await service.get_chat(chat_id)

    if chat is None:
        raise HTTPException(status_code=404,detail="Chat not found")

    member = await service.get_member(chat_id,current_user.id)

    if member is None and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return await service.get_messages(chat_id)


@router.get("/{chat_id}/messages/{message_id}",response_model=MessageResponse)
async def get_message(chat_id: UUID,message_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    message = await service.get_message(message_id)

    if message is None or message.chat_id != chat_id:
        raise HTTPException(status_code=404,detail="Message not found")

    member = await service.get_member(chat_id,current_user.id)

    if member is None and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return message


@router.patch("/{chat_id}/messages/{message_id}",response_model=MessageResponse)
async def update_message(chat_id: UUID,message_id: UUID,data: MessageUpdate,
    current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    message = await service.get_message(message_id)

    if message is None or message.chat_id != chat_id:
        raise HTTPException(status_code=404,detail="Message not found")

    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403,detail="You can only update your own messages")

    return await service.update_message(message_id,data.content)


@router.patch("/{chat_id}/messages/{message_id}/read",response_model=MessageResponse)
async def mark_message_as_read(chat_id: UUID,message_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    message = await service.get_message(message_id)

    if message is None or message.chat_id != chat_id:
        raise HTTPException(status_code=404,detail="Message not found")

    member = await service.get_member(chat_id,current_user.id)

    if member is None and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return await service.mark_message_as_read(message_id)


@router.delete("/{chat_id}/messages/{message_id}")
async def delete_message(chat_id: UUID,message_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    message = await service.get_message(message_id)

    if message is None or message.chat_id != chat_id:
        raise HTTPException(status_code=404,detail="Message not found")

    if message.sender_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="You can only delete your own messages")

    await service.delete_message(message_id)

    return {"message": "Message deleted successfully"}