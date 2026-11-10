import json
import uuid

import pytest

pytestmark = [pytest.mark.integration,pytest.mark.asyncio(loop_scope="function")]


class RecordingManager:
    def __init__(self):
        self.deliveries=[]

    async def send_to_users(self,user_ids,payload):
        self.deliveries.append((list(user_ids),payload))


class RecordingRedis:
    def __init__(self,broken=False):
        self.broken=broken
        self.messages=[]

    async def publish(self,channel,message):
        if self.broken:
            raise ConnectionError("redis unavailable")
        self.messages.append((channel,message))


async def test_local_delivery_and_fail_open_publish():
    """Catches Redis failure suppressing the local committed chat event."""
    from backend.services.chat_event_broker import ChatEventBroker

    manager=RecordingManager()
    broker=ChatEventBroker(RecordingRedis(broken=True),manager,instance_id="one")
    user_id=uuid.uuid4()
    await broker.deliver_and_publish([user_id],{"type":"message.created"})

    assert manager.deliveries == [([user_id],{"type":"message.created"})]


async def test_remote_event_is_forwarded_once_and_own_event_is_suppressed():
    """Catches self-echo duplication or duplicate remote forwarding."""
    from backend.services.chat_event_broker import ChatEventBroker

    manager=RecordingManager()
    redis=RecordingRedis()
    broker=ChatEventBroker(redis,manager,instance_id="one")
    user_id=uuid.uuid4()
    own={"event_id":"own","instance_id":"one","target_user_ids":[str(user_id)],
         "payload":{"type":"message.created"}}
    remote={**own,"event_id":"remote","instance_id":"two"}

    await broker.process_message(json.dumps(own))
    await broker.process_message(json.dumps(remote))
    await broker.process_message(json.dumps(remote))

    assert manager.deliveries == [([user_id],{"type":"message.created"})]


async def test_published_envelope_has_instance_event_and_targets():
    """Catches an envelope that remote instances cannot route safely."""
    from backend.services.chat_event_broker import ChatEventBroker

    redis=RecordingRedis()
    broker=ChatEventBroker(redis,RecordingManager(),instance_id="one")
    target=uuid.uuid4()
    await broker.deliver_and_publish([target],{"type":"chat.updated"})
    envelope=json.loads(redis.messages[0][1])

    assert envelope["instance_id"] == "one"
    assert uuid.UUID(envelope["event_id"])
    assert envelope["target_user_ids"] == [str(target)]
    assert envelope["payload"] == {"type":"chat.updated"}
