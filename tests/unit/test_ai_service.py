import uuid

import pytest


class _UsageRepository:
    def __init__(self):
        self.reserved = []
        self.finished = []

    async def reserve(self, user_id, request_type, model, at=None):
        usage = type("Usage", (), {"id": uuid.uuid4()})()
        self.reserved.append((user_id, request_type, model))
        return usage

    async def finish(self, usage_id, *, successful, input_tokens=0,
                     output_tokens=0, error_code=None):
        self.finished.append((successful, error_code))


class _Provider:
    model = "test-model"

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    async def generate(self, *, instructions, input_text, safety_identifier,
                       max_output_tokens, structured=False):
        self.calls.append((instructions,input_text,safety_identifier,
                           max_output_tokens,structured))
        if self.error:
            raise self.error
        return type("Result", (), {
            "text":"Helpful answer","input_tokens":12,"output_tokens":5})()


class _QuotaRepository(_UsageRepository):
    async def reserve(self, user_id, request_type, model, at=None):
        from backend.repositories.ai_usage_repo import AIQuotaExceededError

        raise AIQuotaExceededError("AI_QUOTA_EXCEEDED")


def _run_immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("test coroutine unexpectedly required an event loop")


def test_missing_ai_key_is_controlled_and_does_not_reserve_quota():
    """Catches optional AI configuration breaking ordinary learning."""
    from backend.services.ai_service import AIError, AIService

    usage = _UsageRepository()
    with pytest.raises(AIError, match="AI_UNAVAILABLE"):
        _run_immediate(AIService(None,usage).generate(
            uuid.uuid4(),"hint","system","question"))
    assert usage.reserved == []


def test_ai_uses_hashed_safety_id_and_audits_success():
    """Catches raw identifiers being sent or successful calls escaping audit."""
    from backend.services.ai_service import AIService

    user_id = uuid.uuid4()
    usage = _UsageRepository()
    provider = _Provider()
    result = _run_immediate(AIService(provider,usage).generate(
        user_id,"hint","Give a hint","Question",max_output_tokens=80))

    safety_id = provider.calls[0][2]
    assert result == "Helpful answer"
    assert str(user_id) not in safety_id
    assert len(safety_id) == 64
    assert usage.finished == [(True,None)]


def test_provider_failure_is_stable_and_does_not_consume_success_quota():
    """Catches provider exceptions leaking or being counted as successful calls."""
    from backend.services.ai_service import AIError, AIService

    usage = _UsageRepository()
    provider = _Provider(error=TimeoutError())
    with pytest.raises(AIError, match="AI_PROVIDER_ERROR"):
        _run_immediate(AIService(provider,usage).generate(
            uuid.uuid4(),"explain","Explain","Answer"))
    assert usage.finished == [(False,"AI_PROVIDER_ERROR")]


def test_quota_error_is_exposed_without_calling_provider():
    """Catches atomic quota exhaustion being reported as a provider outage."""
    from backend.services.ai_service import AIError, AIService

    provider = _Provider()
    with pytest.raises(AIError, match="AI_QUOTA_EXCEEDED"):
        _run_immediate(AIService(provider,_QuotaRepository()).generate(
            uuid.uuid4(),"chat","Chat","Hello"))
    assert provider.calls == []
