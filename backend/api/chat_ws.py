from uuid import UUID

from fastapi import APIRouter,WebSocket,WebSocketDisconnect

from backend.database.db import SessionLocal
from backend.repositories.chat_repo import ChatRepository
from backend.schemas.chat_schema import MessageCreate
from backend.services.auth_ser import AuthService
from backend.services.chat_service import ChatService
from backend.services.redis_service import RedisService


websocket_router=APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)


class ConnectionManager:

    def __init__(self):
        self.active_connections:dict[UUID,dict[UUID,WebSocket]]={}

    async def connect(
        self,
        chat_id:UUID,
        user_id:UUID,
        websocket:WebSocket
    ):
        await websocket.accept()

        if chat_id not in self.active_connections:
            self.active_connections[chat_id]={}

        self.active_connections[chat_id][user_id]=websocket

        await RedisService.set_online(
            chat_id,
            user_id
        )

    async def disconnect(
        self,
        chat_id:UUID,
        user_id:UUID
    ):
        connections=self.active_connections.get(
            chat_id,
            {}
        )

        connections.pop(user_id,None)

        if not connections:
            self.active_connections.pop(
                chat_id,
                None
            )

        await RedisService.set_offline(
            chat_id,
            user_id
        )

        await RedisService.remove_typing(
            chat_id,
            user_id
        )

    async def broadcast(
        self,
        chat_id:UUID,
        data:dict
    ):
        connections=self.active_connections.get(
            chat_id,
            {}
        )

        disconnected_users=[]

        for user_id,websocket in connections.copy().items():
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected_users.append(user_id)

        for user_id in disconnected_users:
            await self.disconnect(
                chat_id,
                user_id
            )

    async def get_online_users(
        self,
        chat_id:UUID
    ):
        return await RedisService.get_online_users(chat_id)


manager=ConnectionManager()


@websocket_router.websocket("/chats/{chat_id}")
async def chat_websocket(
    websocket:WebSocket,
    chat_id:UUID,
    token:str=""
):
    auth_header=websocket.headers.get("authorization","")

    if auth_header.startswith("Bearer "):
        token=auth_header[7:]

    if not token:
        await websocket.close(
            code=1008,
            reason="Authentication required"
        )
        return

    async with SessionLocal() as session:

        auth_service=AuthService(session)
        payload=auth_service.decode_token(token)

        if not payload or payload.get("type")!="access":
            await websocket.close(
                code=1008,
                reason="Invalid token"
            )
            return

        try:
            user_id=UUID(str(payload.get("sub")))
        except (ValueError,TypeError):
            await websocket.close(
                code=1008,
                reason="Invalid token payload"
            )
            return

        repository=ChatRepository(session)
        service=ChatService(repository)

        chat=await service.get_chat(chat_id)

        if chat is None:
            await websocket.close(
                code=1008,
                reason="Chat not found"
            )
            return

        member=await service.get_member(
            chat_id,
            user_id
        )

        if member is None:
            await websocket.close(
                code=1008,
                reason="User is not a member of this chat"
            )
            return

        await manager.connect(
            chat_id,
            user_id,
            websocket
        )

        await websocket.send_json(
            {
                "type":"connection.established",
                "data":{
                    "chat_id":str(chat_id),
                    "user_id":str(user_id)
                }
            }
        )

        await manager.broadcast(
            chat_id,
            {
                "type":"user.online",
                "data":{
                    "user_id":str(user_id)
                }
            }
        )

        try:
            while True:

                data=await websocket.receive_json()
                event_type=data.get("type")

                if event_type=="message":

                    content=data.get("content")

                    if not content:
                        await websocket.send_json(
                            {
                                "type":"error",
                                "message":"Message content is required"
                            }
                        )
                        continue

                    content=content.strip()

                    if not content:
                        await websocket.send_json(
                            {
                                "type":"error",
                                "message":"Message content cannot be empty"
                            }
                        )
                        continue

                    message_data=MessageCreate(
                        content=content
                    )

                    message=await service.create_message(
                        chat_id=chat_id,
                        sender_id=user_id,
                        data=message_data
                    )

                    await manager.broadcast(
                        chat_id,
                        {
                            "type":"message.created",
                            "data":{
                                "id":str(message.id),
                                "chat_id":str(message.chat_id),
                                "sender_id":str(message.sender_id),
                                "content":message.content,
                                "created_at":message.created_at.isoformat(),
                                "is_read":message.is_read
                            }
                        }
                    )

                elif event_type=="typing.start":

                    await RedisService.set_typing(
                        chat_id,
                        user_id
                    )

                    await manager.broadcast(
                        chat_id,
                        {
                            "type":"typing.start",
                            "data":{
                                "user_id":str(user_id)
                            }
                        }
                    )

                elif event_type=="typing.stop":

                    await RedisService.remove_typing(
                        chat_id,
                        user_id
                    )

                    await manager.broadcast(
                        chat_id,
                        {
                            "type":"typing.stop",
                            "data":{
                                "user_id":str(user_id)
                            }
                        }
                    )

                else:

                    await websocket.send_json(
                        {
                            "type":"error",
                            "message":"Unknown event type"
                        }
                    )

        except WebSocketDisconnect:

            await manager.disconnect(
                chat_id,
                user_id
            )

            await manager.broadcast(
                chat_id,
                {
                    "type":"user.offline",
                    "data":{
                        "user_id":str(user_id)
                    }
                }
            )

        except Exception:

            await manager.disconnect(
                chat_id,
                user_id
            )

            try:
                await websocket.close(
                    code=1011,
                    reason="Internal server error"
                )
            except Exception:
                pass