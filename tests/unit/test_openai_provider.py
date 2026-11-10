import json

import httpx
import pytest


@pytest.mark.asyncio(loop_scope="function")
async def test_provider_moderates_both_sides_and_sends_bounded_responses_payload():
    """Catches storage, missing moderation, or wrong Responses API parsing."""
    from backend.providers.openai_provider import OpenAIResponsesProvider

    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/v1/responses":
            payload = json.loads(request.content)
            assert payload["store"] is False
            assert payload["max_output_tokens"] == 80
            assert payload["safety_identifier"] == "a" * 64
            return httpx.Response(200,json={
                "output":[{"content":[{"type":"output_text","text":"Safe answer"}]}],
                "usage":{"input_tokens":4,"output_tokens":2}})
        return httpx.Response(200,json={"results":[{"flagged":False}]})

    provider=OpenAIResponsesProvider("key","model",transport=httpx.MockTransport(handler))
    result=await provider.generate(instructions="Help",input_text="Question",
        safety_identifier="a"*64,max_output_tokens=80)

    assert result.text == "Safe answer"
    assert [request.url.path for request in requests] == [
        "/v1/moderations","/v1/responses","/v1/moderations"]


@pytest.mark.asyncio(loop_scope="function")
async def test_provider_blocks_flagged_input_before_paid_generation():
    """Catches unsafe input reaching the Responses endpoint."""
    from backend.providers.openai_provider import AIUnsafeError, OpenAIResponsesProvider

    calls=[]
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200,json={"results":[{"flagged":True}]})

    provider=OpenAIResponsesProvider("key","model",transport=httpx.MockTransport(handler))
    with pytest.raises(AIUnsafeError,match="AI_UNSAFE_INPUT"):
        await provider.generate(instructions="Help",input_text="Unsafe",
            safety_identifier="b"*64,max_output_tokens=80)
    assert calls == ["/v1/moderations"]
