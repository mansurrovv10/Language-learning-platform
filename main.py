from fastapi import FastAPI
import uvicorn
from backend.api.auth import auth_router
from backend.api.users import user_router
from backend.api.friends import friend_router
from backend.api.chats import router as chats_router
from backend.api.chat_ws import websocket_router
from backend.api.courses import router as courses_router
from backend.api.exercises import router as exercises_router
from backend.api.lessons import router as lessons_router
from backend.api.languages import router as languages_router
from backend.api.gamification import router as gamification_router
from backend.api.progress import router as progress_router
from backend.api.reviews import router as reviews_router


duolingo = FastAPI(title="Mini Duolingo")
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
duolingo.include_router(reviews_router)


if __name__ == '__main__':
    uvicorn.run(duolingo, host="127.0.0.1", port=8000)