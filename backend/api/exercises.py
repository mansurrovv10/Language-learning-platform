from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.database import get_session
from backend.repositories.exercise import ExerciseRepository
from backend.schemas.exercise import ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseSubmit, ExerciseResult
from backend.services.exercise import ExerciseService


router = APIRouter(prefix="/exercises", tags=["Exercises"])


def get_exercise_service(session: AsyncSession = Depends(get_session)):
    repository = ExerciseRepository(session)
    return ExerciseService(repository)


@router.get("", response_model=list[ExerciseResponse])
async def get_exercises(service: ExerciseService = Depends(get_exercise_service)):
    return await service.get_all()


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    service: ExerciseService = Depends(get_exercise_service)
):
    exercise = await service.get_by_id(exercise_id)

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return exercise


@router.get("/lesson/{lesson_id}", response_model=list[ExerciseResponse])
async def get_exercises_by_lesson(
    lesson_id: int,
    service: ExerciseService = Depends(get_exercise_service)
):
    return await service.get_by_lesson(lesson_id)


@router.post("", response_model=ExerciseResponse)
async def create_exercise(
    data: ExerciseCreate,
    service: ExerciseService = Depends(get_exercise_service)
):
    return await service.create(data)


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    service: ExerciseService = Depends(get_exercise_service)
):
    exercise = await service.update(exercise_id, data)

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return exercise


@router.delete("/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    service: ExerciseService = Depends(get_exercise_service)
):
    result = await service.delete(exercise_id)

    if not result:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return {"message": "Exercise deleted"}


@router.post("/{exercise_id}/submit", response_model=ExerciseResult)
async def submit_exercise(
    exercise_id: int,
    data: ExerciseSubmit,
    service: ExerciseService = Depends(get_exercise_service)
):
    result = await service.submit_exercise(exercise_id, data)

    if not result:
        raise HTTPException(status_code=404, detail="Exercise not found")

    return result