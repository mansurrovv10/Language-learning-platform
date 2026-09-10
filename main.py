from fastapi import FastAPI
import uvicorn
from backend.api.chats import router as chats_router
from backend.api.chat_ws import websocket_router

duolingo = FastAPI(title="Mini Duolingo")
duolingo.include_router(chats_router)
duolingo.include_router(websocket_router)



if __name__ == '__main__':
    uvicorn.run(duolingo, host="127.0.0.1", port=8000)