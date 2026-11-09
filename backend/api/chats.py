from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import SessionLocal
from backend.api.auth import get_current_user
from backend.api.chat_ws import manager
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
    try:
        chat = await service.create_private_chat(data,current_user.id)
    except ValueError as error:
        code = str(error)
        status_code = 404 if code == "PARTICIPANT_NOT_FOUND" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"code":code,"message":code.replace("_"," ").title()},
        )

    members = await service.get_members(chat.id)
    await manager.send_to_users(
        [item.user_id for item in members],
        {
            "type":"chat.updated",
            "chat_id":str(chat.id)
        }
    )

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
    try:
        member = await service.add_member_authorized(
            chat_id,
            data.username,
            current_user.id,
            current_user.role.value == "admin",
        )
    except PermissionError as error:
        raise HTTPException(status_code=403,detail=str(error))
    except ValueError as error:
        code = str(error)
        status_code = 404 if code in {"CHAT_NOT_FOUND","USER_NOT_FOUND"} else 400
        raise HTTPException(status_code=status_code,detail=code)

    members = await service.get_members(chat_id)

    await manager.send_to_users(
        [item.user_id for item in members],
        {
            "type":"chat.updated",
            "chat_id":str(chat_id)
        }
    )

    return member


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
    try:
        await service.remove_member_authorized(
            chat_id,
            user_id,
            current_user.id,
            current_user.role.value == "admin",
        )
    except PermissionError as error:
        raise HTTPException(status_code=403,detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=404,detail=str(error))

    await manager.send_to_user(
        user_id,
        {
            "type":"chat.access_revoked",
            "chat_id":str(chat_id)
        }
    )

    members = await service.get_members(chat_id)

    await manager.send_to_users(
        [item.user_id for item in members],
        {
            "type":"chat.updated",
            "chat_id":str(chat_id)
        }
    )

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

    message = await service.create_message(chat_id,current_user.id,data)

    members = await service.get_members(chat_id)

    await manager.send_to_users(
        [item.user_id for item in members],
        {
            "type":"message.created",
            "chat_id":str(chat_id),
            "message_id":str(message.id)
        }
    )

    return message


@router.get("/{chat_id}/messages",response_model=list[MessageResponse])
async def get_messages(chat_id: UUID,current_user: UserProfile = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service)):
    chat = await service.get_chat(chat_id)

    if chat is None:
        raise HTTPException(status_code=404,detail="Chat not found")

    member = await service.get_member(chat_id,current_user.id)

    if member is None and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    try:
        return await service.get_messages_authorized(
            chat_id,current_user.id,current_user.role.value == "admin"
        )
    except PermissionError as error:
        raise HTTPException(status_code=403,detail=str(error))


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

    message = await service.update_message(message_id,data.content)

    members = await service.get_members(chat_id)

    await manager.send_to_users(
        [item.user_id for item in members],
        {
            "type":"message.updated",
            "chat_id":str(chat_id),
            "message_id":str(message_id)
        }
    )

    return message


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

    message = await service.mark_message_as_read(message_id)

    members = await service.get_members(chat_id)

    await manager.send_to_users(
        [item.user_id for item in members],
        {
            "type":"message.read",
            "chat_id":str(chat_id),
            "message_id":str(message_id)
        }
    )

    return message


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

    members = await service.get_members(chat_id)

    await manager.send_to_users(
        [item.user_id for item in members],
        {
            "type":"message.deleted",
            "chat_id":str(chat_id),
            "message_id":str(message_id)
        }
    )

    return {"message": "Message deleted successfully"}
