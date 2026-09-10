from fastapi import FastAPI
import uvicorn
from backend.api.auth import auth_router
from backend.api.users import user_router
from backend.api.friends import friend_router

duolingo = FastAPI(title="Mini Duolingo")


duolingo.include_router(auth_router)
duolingo.include_router(user_router)
duolingo.include_router(friend_router)


if __name__ == '__main__':
    uvicorn.run(duolingo, host="127.0.0.1", port=8000)