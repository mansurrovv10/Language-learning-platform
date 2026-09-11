from uuid import UUID
from backend.database.redis import redis_client


class RedisService:

    @staticmethod
    async def set_online(chat_id:UUID,user_id:UUID):
        await redis_client.sadd(
            f"chat:{chat_id}:online",
            str(user_id)
        )

    @staticmethod
    async def set_offline(chat_id:UUID,user_id:UUID):
        await redis_client.srem(
            f"chat:{chat_id}:online",
            str(user_id)
        )

    @staticmethod
    async def get_online_users(chat_id:UUID):
        users=await redis_client.smembers(
            f"chat:{chat_id}:online"
        )
        return [UUID(user_id) for user_id in users]

    @staticmethod
    async def set_typing(chat_id:UUID,user_id:UUID):
        await redis_client.sadd(
            f"chat:{chat_id}:typing",
            str(user_id)
        )

    @staticmethod
    async def remove_typing(chat_id:UUID,user_id:UUID):
        await redis_client.srem(
            f"chat:{chat_id}:typing",
            str(user_id)
        )

    @staticmethod
    async def get_typing_users(chat_id:UUID):
        users=await redis_client.smembers(
            f"chat:{chat_id}:typing"
        )
        return [UUID(user_id) for user_id in users]

    @staticmethod
    async def clear_chat(chat_id:UUID):
        await redis_client.delete(
            f"chat:{chat_id}:online",
            f"chat:{chat_id}:typing"
        )

    @staticmethod
    async def close():
        await redis_client.aclose()