from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.learning_path_repo import LearningPathRepository
from backend.schemas.learning_path_schema import LearningPathResponse
from backend.services.learning_path_service import LearningPathService


router = APIRouter(prefix="/learning-path",tags=["Learning path"])


def get_learning_path_service(session: AsyncSession = Depends(get_session)):
    return LearningPathService(LearningPathRepository(session))


@router.get("/{language_id}",response_model=LearningPathResponse)
async def get_learning_path(language_id: int,
    service: LearningPathService = Depends(get_learning_path_service),
    current_user: UserProfile = Depends(get_current_user)):
    return await service.get_path(current_user.id,language_id)
