from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.database import get_session
from backend.repositories.language import LanguageRepository
from backend.schemas.language import LanguageCreate, LanguageUpdate, LanguageResponse
from backend.services.language import LanguageService


router = APIRouter(prefix="/languages", tags=["Languages"])


def get_language_service(session: AsyncSession = Depends(get_session)):
    repository = LanguageRepository(session)
    return LanguageService(repository)


@router.get("", response_model=list[LanguageResponse])
async def get_languages(
    service: LanguageService = Depends(get_language_service)
):
    return await service.get_all()


@router.get("/{language_id}", response_model=LanguageResponse)
async def get_language(
    language_id: int,
    service: LanguageService = Depends(get_language_service)
):
    language = await service.get_by_id(language_id)

    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    return language


@router.post("", response_model=LanguageResponse)
async def create_language(
    data: LanguageCreate,
    service: LanguageService = Depends(get_language_service)
):
    return await service.create(data)


@router.put("/{language_id}", response_model=LanguageResponse)
async def update_language(
    language_id: int,
    data: LanguageUpdate,
    service: LanguageService = Depends(get_language_service)
):
    language = await service.update(language_id, data)

    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    return language


@router.delete("/{language_id}")
async def delete_language(
    language_id: int,
    service: LanguageService = Depends(get_language_service)
):
    result = await service.delete(language_id)

    if not result:
        raise HTTPException(status_code=404, detail="Language not found")

    return {"message": "Language deleted"}