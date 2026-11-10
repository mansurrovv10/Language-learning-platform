import asyncio
import json
import logging
import uuid
from collections import deque

from backend.api.chat_ws import manager
from backend.database.redis import redis_client

logger=logging.getLogger(__name__)


class ChatEventBroker:
    def __init__(self,redis,connection_manager,*,instance_id=None,
                 channel="chat.events"):
        self.redis=redis
        self.manager=connection_manager
        self.instance_id=instance_id or str(uuid.uuid4())
        self.channel=channel
        self.enabled=redis is not None
        self._seen=deque(maxlen=1000)
        self._seen_set=set()

    def _remember(self,event_id):
        if event_id in self._seen_set:
            return False
        if len(self._seen) == self._seen.maxlen:
            self._seen_set.discard(self._seen[0])
        self._seen.append(event_id)
        self._seen_set.add(event_id)
        return True

    async def deliver_and_publish(self,target_user_ids,payload):
        targets=list(dict.fromkeys(target_user_ids))
        await self.manager.send_to_users(targets,payload)
        if not self.enabled:
            return
        await self._publish(targets,payload)

    async def revoke_user(self,user_id,code=4403):
        await self.manager.disconnect_user(user_id,code=code)
        if not self.enabled:
            return
        await self._publish(
            [user_id],{"type":"user.revoked","code":code}
        )

    async def _publish(self,targets,payload):
        envelope={"event_id":str(uuid.uuid4()),"instance_id":self.instance_id,
                  "target_user_ids":[str(item) for item in targets],"payload":payload}
        try:
            await self.redis.publish(self.channel,json.dumps(envelope,separators=(",",":")))
        except Exception:
            logger.warning("Redis chat event publish failed",exc_info=True)

    async def process_message(self,data):
        if isinstance(data,bytes):
            data=data.decode("utf-8")
        try:
            envelope=json.loads(data) if isinstance(data,str) else data
            if not isinstance(envelope,dict) or envelope.get("instance_id") == self.instance_id:
                return
            event_id=str(envelope["event_id"])
            targets=[uuid.UUID(item) for item in envelope["target_user_ids"]]
            payload=envelope["payload"]
            if not isinstance(payload,dict) or not self._remember(event_id):
                return
        except (KeyError,TypeError,ValueError,json.JSONDecodeError):
            logger.warning("Ignoring malformed Redis chat event")
            return
        if payload.get("type") == "user.revoked":
            code=payload.get("code",4403)
            for user_id in targets:
                await self.manager.disconnect_user(user_id,code=code)
            return
        await self.manager.send_to_users(targets,payload)

    async def _consume(self):
        pubsub=self.redis.pubsub()
        try:
            await pubsub.subscribe(self.channel)
            while True:
                message=await pubsub.get_message(ignore_subscribe_messages=True,timeout=1.0)
                if message is not None:
                    await self.process_message(message.get("data"))
                else:
                    await asyncio.sleep(0.05)
        finally:
            try:
                await pubsub.unsubscribe(self.channel)
                await pubsub.aclose()
            except Exception:
                pass

    async def run_forever(self):
        while True:
            try:
                await self._consume()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning("Redis chat subscriber unavailable",exc_info=True)
                await asyncio.sleep(1)


chat_event_broker=ChatEventBroker(redis_client,manager)
