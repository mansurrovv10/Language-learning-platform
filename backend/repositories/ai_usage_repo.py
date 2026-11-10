import uuid
from datetime import datetime

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.ai_usage import AIUsage
from backend.services.daily_goal_service import bishkek_day_bounds


class AIQuotaExceededError(RuntimeError):
    pass


class AIUsageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def reserve(self, user_id: uuid.UUID, request_type: str,
                      model: str, at: datetime | None = None) -> AIUsage:
        start_at,end_at,_ = bishkek_day_bounds(at)
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
            {"key":f"ai:{user_id}"})
        count = int(await self.session.scalar(
            select(func.count()).select_from(AIUsage).where(
                AIUsage.user_id == user_id,
                AIUsage.created_at >= start_at,
                AIUsage.created_at < end_at,
                or_(AIUsage.successful.is_(True),AIUsage.error_code == "PENDING"))) or 0)
        if count >= settings.AI_DAILY_QUOTA:
            await self.session.rollback()
            raise AIQuotaExceededError("AI_QUOTA_EXCEEDED")
        usage=AIUsage(user_id=user_id,request_type=request_type,model=model,
                      successful=False,error_code="PENDING")
        self.session.add(usage)
        await self.session.commit()
        return usage

    async def finish(self, usage_id: uuid.UUID, *, successful: bool,
                     input_tokens: int = 0, output_tokens: int = 0,
                     error_code: str | None = None):
        await self.session.execute(update(AIUsage).where(AIUsage.id == usage_id).values(
            successful=successful,input_tokens=input_tokens,
            output_tokens=output_tokens,error_code=error_code))
        await self.session.commit()
