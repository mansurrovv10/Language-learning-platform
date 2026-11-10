from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_admin
from backend.database.db import get_session
from backend.models.user import UserProfile, UserRole
from backend.repositories.language_repo import LanguageRepository
from backend.schemas.language_schema import (
    LanguageCreate,
    LanguageResponse,
    LanguageUpdate,
)
from backend.schemas.page_schema import Page
from backend.services.language_service import LanguageService

router = APIRouter(prefix="/languages", tags=["Languages"])


def get_language_service(session: AsyncSession = Depends(get_session)):
    repository = LanguageRepository(session)
    return LanguageService(repository)


@router.get("", response_model=list[LanguageResponse])
async def get_languages(
    service: LanguageService = Depends(get_language_service),
    current_user: UserProfile = Depends(get_current_user)
):
    is_admin = current_user.role == UserRole.ADMIN
    return await service.get_all(is_admin)


@router.get("/paged", response_model=Page[LanguageResponse])
async def get_languages_paged(
    q: str | None = Query(default=None,max_length=100),
    limit: int = Query(default=20,ge=1,le=100),
    offset: int = Query(default=0,ge=0),
    service: LanguageService = Depends(get_language_service),
    current_user: UserProfile = Depends(get_current_user)):
    items,total = await service.get_paged(
        q,limit,offset,current_user.role == UserRole.ADMIN)
    return Page(items=items,total=total,limit=limit,offset=offset)


@router.get("/{language_id}", response_model=LanguageResponse)
async def get_language(language_id: int,service: LanguageService = Depends(get_language_service)):
    language = await service.get_by_id(language_id)

    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    return language


@router.post("", response_model=LanguageResponse)
async def create_language(data: LanguageCreate,service: LanguageService = Depends(get_language_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.create(data)


@router.put("/{language_id}", response_model=LanguageResponse)
async def update_language(language_id: int,data: LanguageUpdate,
    service: LanguageService = Depends(get_language_service),
    current_user: UserProfile = Depends(require_admin)):
    language = await service.update(language_id, data)

    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    return language


@router.delete("/{language_id}")
async def delete_language(language_id: int,service: LanguageService = Depends(get_language_service),
    current_user: UserProfile = Depends(require_admin)):
    result = await service.delete(language_id)

    if not result:
        raise HTTPException(status_code=404, detail="Language not found")

    return {"message": "Language deleted"}
