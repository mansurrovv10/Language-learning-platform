import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.achievement import router as achievement_router
from backend.api.ai import router as ai_router
from backend.api.auth import auth_router
from backend.api.challange import router as challange_router
from backend.api.chat_ws import websocket_router
from backend.api.chats import router as chats_router
from backend.api.courses import router as courses_router
from backend.api.daily_goals import router as daily_goals_router
from backend.api.exercises import router as exercises_router
from backend.api.friends import friend_router
from backend.api.gamification import router as gamification_router
from backend.api.languages import router as languages_router
from backend.api.leaderboard import router as leaderboard_router
from backend.api.learning_path import router as learning_path_router
from backend.api.lessons import router as lessons_router
from backend.api.level_tests import router as level_tests_router
from backend.api.practice import router as practice_router
from backend.api.progress import router as progress_router
from backend.api.reviews import router as reviews_router
from backend.api.users import user_router
from backend.config import settings
from backend.database.health import collect_readiness
from backend.logging_conf import setup_logging
from backend.middleware import LoggingMiddleware, RateLimitMiddleware
from backend.services.chat_event_broker import chat_event_broker

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    subscriber=(asyncio.create_task(chat_event_broker.run_forever())
                if chat_event_broker.enabled else None)
    if subscriber is not None:
        await asyncio.sleep(0)
    try:
        yield
    finally:
        if subscriber is not None:
            subscriber.cancel()
            with suppress(asyncio.CancelledError):
                await subscriber


duolingo = FastAPI(title="Mini Duolingo",lifespan=lifespan)

# uploads папкасы жок болсо сервер жыгылбасы үчүн
Path("uploads").mkdir(parents=True,exist_ok=True)
duolingo.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

duolingo.add_middleware(RateLimitMiddleware)
duolingo.add_middleware(LoggingMiddleware)

duolingo.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=r"https://[\w-]+\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"])


duolingo.include_router(chats_router)
duolingo.include_router(websocket_router)
duolingo.include_router(auth_router)
duolingo.include_router(user_router)
duolingo.include_router(friend_router)
duolingo.include_router(courses_router)
duolingo.include_router(exercises_router)
duolingo.include_router(lessons_router)
duolingo.include_router(languages_router)
duolingo.include_router(gamification_router)
duolingo.include_router(progress_router)
duolingo.include_router(achievement_router)
duolingo.include_router(challange_router)
duolingo.include_router(leaderboard_router)
duolingo.include_router(level_tests_router)
duolingo.include_router(learning_path_router)
duolingo.include_router(daily_goals_router)
duolingo.include_router(reviews_router)
duolingo.include_router(practice_router)
duolingo.include_router(ai_router)


@duolingo.get("/health")
async def health():
    return {"status": "ok"}


@duolingo.get("/ready")
async def ready():
    is_ready,dependencies = await collect_readiness()
    content = {
        "status":"ready" if is_ready else "not ready",
        "dependencies":dependencies,
    }
    if not is_ready:
        return JSONResponse(status_code=503,content=content)
    return content

if __name__ == '__main__':
    uvicorn.run(duolingo, host=settings.HOST, port=settings.PORT)
