import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.config import settings
from backend.database.db import get_session
from backend.models.exercise import Exercise
from backend.models.language import Language
from backend.models.user import UserProfile
from backend.models.user_language import UserLanguage
from backend.providers.openai_provider import OpenAIResponsesProvider
from backend.repositories.ai_usage_repo import AIUsageRepository
from backend.repositories.learning_path_repo import LearningPathRepository
from backend.repositories.review_repo import ReviewRepository
from backend.schemas.ai_schema import (
    AIChatRequest,
    EvaluationResponse,
    EvaluationRequest,
    ExamplesRequest,
    ExamplesResponse,
    ExplanationResponse,
    ExerciseAnswerRequest,
    ExerciseRequest,
    HintResponse,
    ReplyResponse,
    ReviewResponse,
)
from backend.services.ai_service import AIError, AIService
from backend.services.learning_path_service import LearningPathService
from backend.services.review_service import ReviewService

router=APIRouter(prefix="/ai",tags=["AI assistance"])
SessionDep=Annotated[AsyncSession,Depends(get_session)]
CurrentUser=Annotated[UserProfile,Depends(get_current_user)]


def get_ai_service(session: SessionDep) -> AIService:
    provider = None
    if settings.OPENAI_API_KEY:
        provider=OpenAIResponsesProvider(settings.OPENAI_API_KEY,settings.OPENAI_MODEL,
                                         settings.AI_TIMEOUT_SECONDS)
    return AIService(provider,AIUsageRepository(session))


ServiceDep=Annotated[AIService,Depends(get_ai_service)]


def get_learning_path_service(session: SessionDep) -> LearningPathService:
    return LearningPathService(LearningPathRepository(session))


AccessDep=Annotated[LearningPathService,Depends(get_learning_path_service)]


def _error(error: AIError):
    code=str(error)
    status={"AI_UNAVAILABLE":503,"AI_PROVIDER_ERROR":502,
            "AI_QUOTA_EXCEEDED":429,"AI_UNSAFE_INPUT":400,
            "AI_UNSAFE_OUTPUT":502}.get(code,502)
    return HTTPException(status_code=status,detail={
        "code":code,"message":code.replace("_"," ").title()})


async def _exercise(session,exercise_id,current_user,access_service):
    exercise=await session.get(Exercise,exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404,detail={
            "code":"EXERCISE_NOT_FOUND","message":"Exercise not found"})
    if current_user.role.value != "admin":
        await access_service.ensure_lesson_access(
            current_user.id,exercise.lesson_id
        )
    return exercise


async def _generate(service,user_id,kind,instructions,input_text,**kwargs):
    try:
        return await service.generate(user_id,kind,instructions,input_text,**kwargs)
    except AIError as error:
        raise _error(error)


@router.post("/explain",response_model=ExplanationResponse)
async def explain(data: ExerciseAnswerRequest,current_user: CurrentUser,
                  service: ServiceDep,session: SessionDep,
                  access_service: AccessDep):
    exercise=await _exercise(
        session,data.exercise_id,current_user,access_service
    )
    prompt=json.dumps({"question":exercise.question,"user_answer":data.answer,
                       "expected":exercise.correct_answer},ensure_ascii=False)
    text=await _generate(service,current_user.id,"explain",
        "Explain briefly why the answer is wrong or right. Do not change game state.",prompt)
    return ExplanationResponse(explanation=text)


@router.post("/hint",response_model=HintResponse)
async def hint(data: ExerciseRequest,current_user: CurrentUser,
               service: ServiceDep,session: SessionDep,
               access_service: AccessDep):
    exercise=await _exercise(
        session,data.exercise_id,current_user,access_service
    )
    prompt=json.dumps({"question":exercise.question,"options":exercise.options},
                      ensure_ascii=False)
    text=await _generate(service,current_user.id,"hint",
        "Give one useful hint without revealing or quoting the answer.",prompt,max_output_tokens=120)
    return HintResponse(hint=text)


@router.post("/examples",response_model=ExamplesResponse)
async def examples(data: ExamplesRequest,current_user: CurrentUser,
                   service: ServiceDep,session: SessionDep,
                   access_service: AccessDep):
    exercise=await _exercise(
        session,data.exercise_id,current_user,access_service
    )
    text=await _generate(service,current_user.id,"examples",
        f"Return exactly {data.count} short examples, one per line.",exercise.question)
    return ExamplesResponse(examples=[line.strip(" -") for line in text.splitlines()
                                      if line.strip()][:data.count])


@router.post("/chat",response_model=ReplyResponse)
async def level_chat(data: AIChatRequest,current_user: CurrentUser,
                     service: ServiceDep,session: SessionDep):
    row=(await session.execute(select(UserLanguage,Language)
        .join(Language,Language.id == UserLanguage.language_id)
        .where(UserLanguage.user_id == current_user.id)
        .order_by(UserLanguage.id).limit(1))).first()
    context={"language":row[1].name if row else "selected language",
             "level":row[0].level.value if row and row[0].level else "A1",
             "history":[turn.model_dump() for turn in data.history],
             "message":data.message}
    text=await _generate(service,current_user.id,"chat",
        "Chat in the learner's selected language and level. Be concise.",
        json.dumps(context,ensure_ascii=False),max_output_tokens=300)
    return ReplyResponse(reply=text)


@router.post("/review",response_model=ReviewResponse)
async def personalized_review(current_user: CurrentUser,service: ServiceDep,
                              session: SessionDep):
    due=await ReviewService(ReviewRepository(session)).get_due(current_user.id,limit=5)
    prompt=json.dumps([{"question":item.question,"options":item.options}
                       for item in due.items],ensure_ascii=False)
    text=await _generate(service,current_user.id,"review",
        "Create up to five short review tasks from this server-selected material.",prompt)
    return ReviewResponse(tasks=[line.strip(" -") for line in text.splitlines()
                                 if line.strip()][:5])


@router.post("/evaluate",response_model=EvaluationResponse)
async def evaluate(data: EvaluationRequest,current_user: CurrentUser,
                   service: ServiceDep,session: SessionDep,
                   access_service: AccessDep):
    exercise=await _exercise(
        session,data.exercise_id,current_user,access_service
    )
    prompt=json.dumps({"question":exercise.question,"answer":data.answer,
                       "reference":exercise.correct_answer},ensure_ascii=False)
    text=await _generate(service,current_user.id,"evaluate",
        "Return JSON with accepted boolean, score 0..1, and concise feedback. Advisory only.",
        prompt,structured=True,max_output_tokens=200)
    try:
        return EvaluationResponse.model_validate_json(text)
    except ValueError as error:
        raise _error(AIError("AI_PROVIDER_ERROR")) from error
