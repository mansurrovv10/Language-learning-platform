from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import SessionLocal
from backend.repositories.repo_chat import ChatRepository
from backend.schemas.chat_schema import ChatCreate, ChatResponse
from backend.services.chat_service import ChatService


router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
)


async def get_session():
    async with SessionLocal() as session:
        yield session


def get_chat_service(
    session: AsyncSession = Depends(get_session)
) -> ChatService:
    repository = ChatRepository(session)

    return ChatService(repository)


@router.post("/", response_model=ChatResponse)
async def create_chat(
    data: ChatCreate,
    service: ChatService = Depends(get_chat_service)
):
    return await service.create_chat(data)


@router.get("/", response_model=list[ChatResponse])
async def get_chats(
    service: ChatService = Depends(get_chat_service)
):
    return await service.get_all_chats()


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    service: ChatService = Depends(get_chat_service)
):
    chat = await service.get_chat(chat_id)

    if chat is None:
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )

    return chat