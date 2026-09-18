from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.achievement_repo import AchievementRepository
from backend.database.db import get_session
from backend.repositories.exercise_repo import ExerciseRepository
from backend.repositories.progress_repo import ProgressRepository
from backend.repositories.gamification_repo import GamificationRepository
from backend.repositories.exercise_progress_repo import ExerciseProgressRepository
from backend.schemas.exercise_schema import (ExerciseCreate,ExerciseUpdate,ExerciseResponse,
                                             ExerciseSubmit,ExerciseResult)
from backend.services.exercise_service import ExerciseService
from backend.api.auth import get_current_user,require_admin
from backend.models.user import UserProfile
from backend.repositories.learning_path_repo import LearningPathRepository
from backend.services.learning_path_service import LearningPathService


router = APIRouter(prefix="/exercises",tags=["Exercises"])


def get_exercise_service(session: AsyncSession = Depends(get_session)):
    exercise_repository = ExerciseRepository(session)
    progress_repository = ProgressRepository(session)
    exercise_progress_repository = ExerciseProgressRepository(session)
    gamification_repository = GamificationRepository(session)
    achievement_repository = AchievementRepository(session)

    return ExerciseService(exercise_repository,progress_repository,exercise_progress_repository,
        gamification_repository,achievement_repository)


def get_learning_path_service(session: AsyncSession = Depends(get_session)):
    return LearningPathService(LearningPathRepository(session))


@router.get("",response_model=list[ExerciseResponse])
async def get_exercises(service: ExerciseService = Depends(get_exercise_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.get_all()


@router.get("/lesson/{lesson_id}",response_model=list[ExerciseResponse])
async def get_exercises_by_lesson(lesson_id: int,service: ExerciseService = Depends(get_exercise_service),
    current_user: UserProfile = Depends(get_current_user),
    access_service: LearningPathService = Depends(get_learning_path_service)):
    if current_user.role.value != "admin":
        await access_service.ensure_lesson_access(current_user.id,lesson_id)
    return await service.get_by_lesson(lesson_id)


@router.get("/{exercise_id}",response_model=ExerciseResponse)
async def get_exercise(exercise_id: int,service: ExerciseService = Depends(get_exercise_service),
        current_user: UserProfile = Depends(get_current_user),
        access_service: LearningPathService = Depends(get_learning_path_service)):
    exercise = await service.get_by_id(exercise_id)

    if not exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")

    if current_user.role.value != "admin":
        await access_service.ensure_lesson_access(current_user.id,exercise.lesson_id)

    return exercise


@router.post("",response_model=ExerciseResponse)
async def create_exercise(data: ExerciseCreate,service: ExerciseService = Depends(get_exercise_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.create(data)


@router.put("/{exercise_id}",response_model=ExerciseResponse)
async def update_exercise(exercise_id: int,data: ExerciseUpdate,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: UserProfile = Depends(require_admin)):
    exercise = await service.update(exercise_id,data)

    if not exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")

    return exercise


@router.delete("/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: UserProfile = Depends(require_admin)):
    result = await service.delete(exercise_id)

    if not result:
        raise HTTPException(status_code=404,detail="Exercise not found")

    return {"message":"Exercise deleted"}


@router.post("/{exercise_id}/submit",response_model=ExerciseResult)
async def submit_exercise(
    exercise_id: int,
    data: ExerciseSubmit,
    service: ExerciseService = Depends(get_exercise_service),
    current_user: UserProfile = Depends(get_current_user),
    access_service: LearningPathService = Depends(get_learning_path_service)
):
    exercise = await service.get_by_id(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")
    if current_user.role.value != "admin":
        await access_service.ensure_lesson_access(current_user.id,exercise.lesson_id)
    result = await service.submit_exercise(
        exercise_id,
        data,
        current_user.id
    )

    if result is None:
        raise HTTPException(status_code=404,detail="Exercise not found")

    return result
