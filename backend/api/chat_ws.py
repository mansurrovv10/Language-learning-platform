import asyncio
import json
from uuid import UUID
from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from backend.database.db import SessionLocal
from backend.models.user import UserProfile
from backend.services.auth_ser import AuthService


websocket_router=APIRouter(prefix="/ws",tags=["WebSocket"])


class ConnectionManager:

    def __init__(self):
        self.active_connections:dict[UUID,set[WebSocket]]={}

    async def connect(self,user_id:UUID,websocket:WebSocket):
        if user_id not in self.active_connections:
            self.active_connections[user_id]=set()

        self.active_connections[user_id].add(websocket)

    async def disconnect(self,user_id:UUID,websocket:WebSocket):
        connections=self.active_connections.get(user_id,set())

        connections.discard(websocket)

        if not connections:
            self.active_connections.pop(user_id,None)

    async def send_to_user(self,user_id:UUID,data:dict):
        connections=self.active_connections.get(user_id,set())

        disconnected=[]

        for websocket in connections.copy():
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            await self.disconnect(user_id,websocket)

    async def send_to_users(self,user_ids:list[UUID],data:dict):
        for user_id in set(user_ids):
            await self.send_to_user(user_id,data)


manager=ConnectionManager()


@websocket_router.websocket("/chats")
async def chat_websocket(websocket:WebSocket):
    user_id=None

    await websocket.accept()

    async with SessionLocal() as session:

        auth_service=AuthService(session)

        try:

            try:
                data=await asyncio.wait_for(
                    websocket.receive(),
                    timeout=5
                )
            except asyncio.TimeoutError:
                await websocket.close(code=4401)
                return

            if data.get("type")=="websocket.disconnect":
                return

            if data.get("bytes") is not None:
                await websocket.close(code=4401)
                return

            text=data.get("text")

            if not text or len(text)>16384:
                await websocket.close(code=4401)
                return

            try:
                auth_data=json.loads(text)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type":"error",
                        "code":"UNAUTHORIZED",
                        "message":"Authentication required"
                    }
                )
                await websocket.close(code=4401)
                return

            if not isinstance(auth_data,dict) or auth_data.get("type")!="auth":
                await websocket.send_json(
                    {
                        "type":"error",
                        "code":"UNAUTHORIZED",
                        "message":"Authentication required"
                    }
                )
                await websocket.close(code=4401)
                return

            token=auth_data.get("access_token")

            if not isinstance(token,str) or not token:
                await websocket.send_json(
                    {
                        "type":"error",
                        "code":"UNAUTHORIZED",
                        "message":"Authentication required"
                    }
                )
                await websocket.close(code=4401)
                return

            payload=auth_service.decode_token(token)

            if not payload or payload.get("type")!="access":
                await websocket.send_json(
                    {
                        "type":"error",
                        "code":"UNAUTHORIZED",
                        "message":"Authentication required"
                    }
                )
                await websocket.close(code=4401)
                return

            try:
                user_id=UUID(str(payload.get("sub")))
            except (ValueError,TypeError):
                await websocket.send_json(
                    {
                        "type":"error",
                        "code":"UNAUTHORIZED",
                        "message":"Authentication required"
                    }
                )
                await websocket.close(code=4401)
                return

            user=await session.get(UserProfile,user_id)

            if not user:
                await websocket.send_json(
                    {
                        "type":"error",
                        "code":"UNAUTHORIZED",
                        "message":"Authentication required"
                    }
                )
                await websocket.close(code=4401)
                return

            if not user.is_active:
                await websocket.send_json(
                    {
                        "type":"error",
                        "code":"FORBIDDEN",
                        "message":"User is inactive"
                    }
                )
                await websocket.close(code=4403)
                return

            await manager.connect(user_id,websocket)

            await websocket.send_json(
                {
                    "type":"auth.ok"
                }
            )

            while True:

                data=await websocket.receive()

                if data.get("type")=="websocket.disconnect":
                    break

                if data.get("bytes") is not None:
                    continue

                text=data.get("text")

                if not text or len(text)>16384:
                    continue

                try:
                    event=json.loads(text)
                except json.JSONDecodeError:
                    continue

                if not isinstance(event,dict):
                    continue

                if event.get("type")=="ping":
                    await websocket.send_json(
                        {
                            "type":"pong"
                        }
                    )

        except WebSocketDisconnect:
            pass

        except Exception:
            try:
                await websocket.close(code=1011)
            except Exception:
                pass

        finally:
            if user_id is not None:
                await manager.disconnect(user_id,websocket)
