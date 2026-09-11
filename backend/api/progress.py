import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_admin
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.progress_repo import ProgressRepository
from backend.schemas.progress_schema import ProgressUpdate, ProgressResponse
from backend.services.progress_service import ProgressService


router = APIRouter(prefix="/progress",tags=["Progress"])


def get_progress_service(session: AsyncSession = Depends(get_session)):
    repository = ProgressRepository(session)
    return ProgressService(repository)


@router.get("",response_model=list[ProgressResponse])
async def get_progress(
    service: ProgressService = Depends(get_progress_service),
    current_user: UserProfile = Depends(require_admin)
):
    return await service.get_all()


@router.get("/user/{user_id}",response_model=list[ProgressResponse])
async def get_user_progress(
    user_id: uuid.UUID,
    service: ProgressService = Depends(get_progress_service),
    current_user: UserProfile = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return await service.get_by_user(user_id)


@router.get("/lesson/{lesson_id}",response_model=list[ProgressResponse])
async def get_lesson_progress(
    lesson_id: int,
    service: ProgressService = Depends(get_progress_service),
    current_user: UserProfile = Depends(require_admin)
):
    return await service.get_by_lesson(lesson_id)


@router.get("/{progress_id}",response_model=ProgressResponse)
async def get_progress_by_id(
    progress_id: int,
    service: ProgressService = Depends(get_progress_service),
    current_user: UserProfile = Depends(get_current_user)
):
    progress = await service.get_by_id(progress_id)

    if not progress:
        raise HTTPException(status_code=404,detail="Progress not found")

    if progress.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return progress


@router.put("/{progress_id}",response_model=ProgressResponse)
async def update_progress(
    progress_id: int,
    data: ProgressUpdate,
    service: ProgressService = Depends(get_progress_service),
    current_user: UserProfile = Depends(get_current_user)
):
    progress = await service.get_by_id(progress_id)

    if not progress:
        raise HTTPException(status_code=404,detail="Progress not found")

    if progress.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403,detail="Access denied")

    return await service.update(
        progress_id,
        data.completed,
        data.score
    )


@router.delete("/{progress_id}")
async def delete_progress(
    progress_id: int,
    service: ProgressService = Depends(get_progress_service),
    current_user: UserProfile = Depends(require_admin)
):
    result = await service.delete(progress_id)

    if not result:
        raise HTTPException(status_code=404,detail="Progress not found")

    return {"message":"Progress deleted"}