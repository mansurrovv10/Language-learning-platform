import uuid
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.gamification import XPHistory
from backend.models.leaderboard import Leaderboard
from backend.time import utc_now


class LeaderboardRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_all(self):
        result = await self.session.execute(select(Leaderboard).order_by(Leaderboard.rank))
        return list(result.scalars().all())

    async def get_top(self,limit: int = 10):
        result = await self.session.execute(select(Leaderboard)
            .order_by(Leaderboard.rank,Leaderboard.xp.desc()).limit(limit))
        return list(result.scalars().all())

    async def get_user(self,user_id: uuid.UUID):
        result = await self.session.execute(
            select(Leaderboard).where(Leaderboard.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_user_total_xp(self,user_id: uuid.UUID):
        result = await self.session.execute(
            select(func.coalesce(func.sum(XPHistory.xp),0)).where(
                XPHistory.user_id == user_id))
        return result.scalar_one()

    async def get_user_rank(self,user_id: uuid.UUID):
        total = await self.get_user_total_xp(user_id)

        if total <= 0:
            return None

        result = await self.session.execute(
            select(func.count())
            .select_from(
                select(XPHistory.user_id)
                .group_by(XPHistory.user_id)
                .having(func.sum(XPHistory.xp) > total)
                .subquery()))

        return result.scalar_one() + 1

    async def upsert_user(self,user_id: uuid.UUID,commit: bool = True):
        entries = await self._sync_from_xp_history()
        entry = next(
            (item for item in entries if item.user_id == user_id),None
        )
        if entry is None:
            entry = Leaderboard(
                user_id=user_id,
                xp=0,
                rank=999999,
                updated_at=utc_now())
            self.session.add(entry)

        if commit:
            await self.session.commit()
            await self.session.refresh(entry)
        else:
            await self.session.flush()

        return entry

    async def _sync_from_xp_history(self) -> list[Leaderboard]:
        result = await self.session.execute(
            select(XPHistory.user_id,func.sum(XPHistory.xp).label("total"))
            .group_by(XPHistory.user_id)
            .order_by(func.sum(XPHistory.xp).desc()))

        rows = result.all()
        entries = []
        previous_total = None
        rank = 0

        for index,row in enumerate(rows,start=1):
            if row.total != previous_total:
                rank = index
                previous_total = row.total
            entry = await self.get_user(row.user_id)

            if entry is None:
                entry = Leaderboard(
                    user_id=row.user_id,
                    xp=row.total,
                    rank=rank,
                    updated_at=utc_now())
                self.session.add(entry)
            else:
                entry.xp = row.total
                entry.rank = rank
                entry.updated_at = utc_now()
            entries.append(entry)

        await self.session.flush()
        return entries

    async def recompute_all(self) -> int:
        entries = await self._sync_from_xp_history()

        await self.session.commit()

        return len(entries)
