import uuid
from datetime import datetime,timedelta

from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.gamification import XPHistory, Streak, Hearts
from backend.repositories.leaderboard_repo import LeaderboardRepository
from backend.config import MAX_HEARTS, HEART_REGEN_MINUTES
from backend.time import utc_now


class GamificationRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_xp_history(self,user_id: uuid.UUID):
        result = await self.session.execute(select(XPHistory)
            .where(XPHistory.user_id == user_id)
            .order_by(XPHistory.created_at.desc()))
        return result.scalars().all()

    async def add_xp(self,user_id: uuid.UUID,xp: int,reason: str,commit: bool = True):
        xp_history = XPHistory(user_id=user_id,xp=xp,reason=reason)

        self.session.add(xp_history)
        await self.session.flush()

        await LeaderboardRepository(self.session).upsert_user(user_id,commit=False)

        if commit:
            await self.session.commit()
            await self.session.refresh(xp_history)

        return xp_history

    async def get_streak(self,user_id: uuid.UUID):
        result = await self.session.execute(
            select(Streak).where(Streak.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_streak(self,user_id: uuid.UUID,commit: bool = True):
        streak = Streak(user_id=user_id,current_streak=0)

        self.session.add(streak)
        if commit:
            await self.session.commit()
            await self.session.refresh(streak)
        else:
            await self.session.flush()

        return streak

    async def update_streak(self,streak,commit: bool = True):
        self.session.add(streak)
        if commit:
            await self.session.commit()
            await self.session.refresh(streak)
        else:
            await self.session.flush()

        return streak

    async def get_hearts(
        self,user_id: uuid.UUID,lock: bool = False,commit: bool = True):
        statement = select(Hearts).where(Hearts.user_id == user_id)

        if lock:
            statement = statement.with_for_update()

        result = await self.session.execute(statement)
        hearts = result.scalar_one_or_none()

        if not hearts:
            await self.session.execute(
                pg_insert(Hearts)
                .values(user_id=user_id,hearts=MAX_HEARTS)
                .on_conflict_do_nothing(index_elements=["user_id"]))
            if commit:
                await self.session.commit()
            else:
                await self.session.flush()
            result = await self.session.execute(statement)
            hearts = result.scalar_one()

        return hearts

    def _apply_regen(self,hearts: Hearts,now: datetime) -> bool:
        if hearts.hearts >= MAX_HEARTS:
            changed = hearts.hearts != MAX_HEARTS or hearts.last_heart_lost_at is not None
            hearts.hearts = MAX_HEARTS
            hearts.last_heart_lost_at = None
            return changed

        if not hearts.last_heart_lost_at:
            hearts.last_heart_lost_at = now
            return True

        elapsed_minutes = int(
            (now - hearts.last_heart_lost_at).total_seconds() // 60
        )
        recovered = elapsed_minutes // HEART_REGEN_MINUTES

        if recovered <= 0:
            return False

        hearts.hearts = min(MAX_HEARTS,hearts.hearts + recovered)

        if hearts.hearts >= MAX_HEARTS:
            hearts.last_heart_lost_at = None
        else:
            hearts.last_heart_lost_at = (
                hearts.last_heart_lost_at
                + timedelta(minutes=recovered * HEART_REGEN_MINUTES)
            )

        return True

    def seconds_to_next_heart(self,hearts: Hearts) -> int:
        if hearts.hearts >= MAX_HEARTS or not hearts.last_heart_lost_at:
            return 0

        elapsed = (utc_now() - hearts.last_heart_lost_at).total_seconds()
        remaining = HEART_REGEN_MINUTES * 60 - elapsed

        return max(0,int(remaining))

    def next_heart_at(self,hearts: Hearts) -> datetime | None:
        if hearts.hearts >= MAX_HEARTS or not hearts.last_heart_lost_at:
            return None
        return hearts.last_heart_lost_at + timedelta(minutes=HEART_REGEN_MINUTES)

    async def get_current_hearts(self,user_id: uuid.UUID,commit: bool = True):
        hearts = await self.get_hearts(user_id,lock=True,commit=commit)

        if self._apply_regen(hearts,utc_now()):
            if commit:
                await self.session.commit()
                await self.session.refresh(hearts)
            else:
                await self.session.flush()

        return hearts

    async def lose_heart(self,user_id: uuid.UUID,commit: bool = True) -> int:
        await self.get_current_hearts(user_id,commit=commit)

        # last_heart_lost_at өзгөрбөйт, эгер буга чейин коюлган болсо.
        # Таймер 5 -> 4 болгон учурда гана башталат.
        result = await self.session.execute(
            update(Hearts)
            .where(Hearts.user_id == user_id,Hearts.hearts > 0)
            .values(
                hearts=Hearts.hearts - 1,
                last_heart_lost_at=func.coalesce(
                    Hearts.last_heart_lost_at,utc_now()))
            .returning(Hearts.hearts))

        remaining = result.scalar_one_or_none()

        if remaining is None:
            if commit:
                await self.session.rollback()
            return 0

        if commit:
            await self.session.commit()
        else:
            await self.session.flush()

        return remaining

    async def refill_due_hearts(self) -> int:
        due_by = utc_now() - timedelta(minutes=HEART_REGEN_MINUTES)

        result = await self.session.execute(
            select(Hearts.user_id).where(
                Hearts.hearts < MAX_HEARTS,
                Hearts.last_heart_lost_at.isnot(None),
                Hearts.last_heart_lost_at <= due_by))
        user_ids = [user_id for user_id, in result.all()]

        for user_id in user_ids:
            await self.get_current_hearts(user_id)

        return len(user_ids)

    async def get_hearts_status(self,user_id: uuid.UUID,commit: bool = True):
        hearts = await self.get_current_hearts(user_id,commit=commit)

        return {
            "hearts": hearts.hearts,
            "max_hearts": MAX_HEARTS,
            "seconds_to_next_heart": self.seconds_to_next_heart(hearts),
            "next_heart_at": self.next_heart_at(hearts),
        }
