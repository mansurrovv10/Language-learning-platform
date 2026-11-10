import uuid

import pytest

from backend.config import settings
from backend.repositories.ai_usage_repo import AIQuotaExceededError, AIUsageRepository
from backend.services.auth_ser import AuthService

pytestmark=[pytest.mark.integration,pytest.mark.asyncio(loop_scope="session")]


async def test_ai_quota_reservation_is_atomic_and_failures_release_capacity(
    db_session,monkeypatch):
    """Catches concurrent reservations exceeding quota or failed calls consuming it."""
    monkeypatch.setattr(settings,"AI_DAILY_QUOTA",1)
    user=await AuthService(db_session).register(
        f"ai-{uuid.uuid4().hex}@example.com",f"ai_{uuid.uuid4().hex}","password123")
    user_id=user.id
    repository=AIUsageRepository(db_session)
    failed=await repository.reserve(user_id,"hint","model")
    failed_id=failed.id
    with pytest.raises(AIQuotaExceededError,match="AI_QUOTA_EXCEEDED"):
        await repository.reserve(user_id,"hint","model")
    await repository.finish(failed_id,successful=False,error_code="AI_PROVIDER_ERROR")
    succeeded=await repository.reserve(user_id,"hint","model")
    succeeded_id=succeeded.id
    await repository.finish(succeeded_id,successful=True,input_tokens=1,output_tokens=1)
    with pytest.raises(AIQuotaExceededError,match="AI_QUOTA_EXCEEDED"):
        await repository.reserve(user_id,"hint","model")
