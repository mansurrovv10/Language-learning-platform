import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_session
from backend.repositories.progress_repo import ProgressRepository
from backend.schemas.progress_schema import ProgressCreate, ProgressUpdate, ProgressResponse
from backend.services.progress_service import ProgressService


router = APIRouter(prefix="/progress", tags=["Progress"])


def get_progress_service(session: AsyncSession = Depends(get_session)):
    repository = ProgressRepository(session)
    return ProgressService(repository)


@router.get("", response_model=list[ProgressResponse])
async def get_progress(
    service: ProgressService = Depends(get_progress_service)
):
    return await service.get_all()


@router.get("/{progress_id}", response_model=ProgressResponse)
async def get_progress_by_id(
    progress_id: int,
    service: ProgressService = Depends(get_progress_service)
):
    progress = await service.get_by_id(progress_id)

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return progress


@router.get("/user/{user_id}", response_model=list[ProgressResponse])
async def get_user_progress(
    user_id: uuid.UUID,
    service: ProgressService = Depends(get_progress_service)
):
    return await service.get_by_user(user_id)


@router.get("/lesson/{lesson_id}", response_model=list[ProgressResponse])
async def get_lesson_progress(
    lesson_id: int,
    service: ProgressService = Depends(get_progress_service)
):
    return await service.get_by_lesson(lesson_id)


@router.post("", response_model=ProgressResponse)
async def create_progress(
    data: ProgressCreate,
    service: ProgressService = Depends(get_progress_service)
):
    return await service.create(data)


@router.put("/{progress_id}", response_model=ProgressResponse)
async def update_progress(
    progress_id: int,
    data: ProgressUpdate,
    service: ProgressService = Depends(get_progress_service)
):
    progress = await service.update(progress_id, data)

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return progress


@router.delete("/{progress_id}")
async def delete_progress(
    progress_id: int,
    service: ProgressService = Depends(get_progress_service)
):
    result = await service.delete(progress_id)

    if not result:
        raise HTTPException(status_code=404, detail="Progress not found")

    return {"message": "Progress deleted"}