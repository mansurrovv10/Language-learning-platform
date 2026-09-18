import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_admin
from backend.database.db import get_session
from backend.models.course import LevelChoices
from backend.models.user import UserProfile
from backend.repositories.level_test_repo import LevelTestRepository
from backend.schemas.level_test_schema import (LevelTestCreate,LevelTestQuestionAdminResponse,
    LevelTestQuestionCreate,LevelTestQuestionResponse,LevelTestQuestionUpdate,LevelTestResponse,
    LevelTestResultResponse,LevelTestStartResponse,LevelTestSubmit,LevelTestUpdate)
from backend.services.level_test_service import LevelTestService


router = APIRouter(prefix="/level-tests",tags=["Level tests"])


def get_level_test_service(session: AsyncSession = Depends(get_session)):
    repository = LevelTestRepository(session)
    return LevelTestService(repository)


@router.get("",response_model=list[LevelTestResponse])
async def get_tests(language_id: int | None = None,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.get_tests(language_id)


@router.post("",response_model=LevelTestResponse)
async def create_test(data: LevelTestCreate,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.create_test(data)


@router.put("/{test_id}",response_model=LevelTestResponse)
async def update_test(test_id: uuid.UUID,data: LevelTestUpdate,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    test = await service.update_test(test_id,data)
    if not test:
        raise HTTPException(status_code=404,detail="Level test not found")
    return test


@router.delete("/{test_id}")
async def delete_test(test_id: uuid.UUID,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    if not await service.delete_test(test_id):
        raise HTTPException(status_code=404,detail="Level test not found")
    return {"message":"Level test deleted"}


@router.get("/{test_id}/questions",response_model=list[LevelTestQuestionAdminResponse])
async def get_questions(test_id: uuid.UUID,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    return await service.get_questions(test_id)


@router.post("/{test_id}/questions",response_model=LevelTestQuestionAdminResponse)
async def create_question(test_id: uuid.UUID,data: LevelTestQuestionCreate,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    question = await service.create_question(test_id,data)
    if not question:
        raise HTTPException(status_code=404,detail="Level test not found")
    return question


@router.put("/questions/{question_id}",response_model=LevelTestQuestionAdminResponse)
async def update_question(question_id: int,data: LevelTestQuestionUpdate,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    question = await service.update_question(question_id,data)
    if not question:
        raise HTTPException(status_code=404,detail="Level test question not found")
    return question


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(require_admin)):
    if not await service.delete_question(question_id):
        raise HTTPException(status_code=404,detail="Level test question not found")
    return {"message":"Level test question deleted"}


@router.post("/placement/{language_id}/start",response_model=LevelTestStartResponse)
async def start_placement(language_id: int,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(get_current_user)):
    attempt,test,questions = await service.start_placement(current_user.id,language_id)
    return {"attempt_id":attempt.id,"test_id":test.id,"is_placement":test.is_placement,
        "target_level":test.target_level,"questions":questions}


@router.post("/completion/{language_id}/{level}/start",response_model=LevelTestStartResponse)
async def start_completion(language_id: int,level: LevelChoices,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(get_current_user)):
    attempt,test,questions = await service.start_completion(current_user.id,language_id,level)
    return {"attempt_id":attempt.id,"test_id":test.id,"is_placement":test.is_placement,
        "target_level":test.target_level,"questions":questions}


@router.post("/attempts/{attempt_id}/submit",response_model=LevelTestResultResponse)
async def submit_attempt(attempt_id: uuid.UUID,data: LevelTestSubmit,
    service: LevelTestService = Depends(get_level_test_service),
    current_user: UserProfile = Depends(get_current_user)):
    attempt = await service.submit_attempt(current_user.id,attempt_id,data)
    return {"attempt_id":attempt.id,"score":attempt.score,"passed":attempt.passed,
        "result_level":attempt.result_level}
