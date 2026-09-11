import uuid
from datetime import datetime

from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.gamification import XPHistory
from backend.models.leaderboard import Leaderboard


class LeaderboardRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Leaderboard]:
        result = await self.session.execute(
            select(Leaderboard)
            .order_by(Leaderboard.rank)
        )
        return list(result.scalars().all())

    async def get_top(self,limit: int = 10) -> list[Leaderboard]:
        result = await self.session.execute(
            select(Leaderboard)
            .order_by(Leaderboard.rank,Leaderboard.xp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_user(self,user_id: uuid.UUID) -> Leaderboard | None:
        result = await self.session.execute(
            select(Leaderboard).where(Leaderboard.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_total_xp(self,user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(XPHistory.xp),0)).where(
                XPHistory.user_id == user_id
            )
        )
        return result.scalar_one()

    async def get_user_rank(self,user_id: uuid.UUID) -> int | None:
        total = await self.get_user_total_xp(user_id)

        if total <= 0:
            return None

        result = await self.session.execute(
            select(func.count())
            .select_from(
                select(XPHistory.user_id)
                .group_by(XPHistory.user_id)
                .having(func.sum(XPHistory.xp) > total)
                .subquery()
            )
        )

        return result.scalar_one() + 1

    async def upsert_user(self,user_id: uuid.UUID) -> Leaderboard:
        total = await self.get_user_total_xp(user_id)
        rank = await self.get_user_rank(user_id)

        if rank is None:
            rank = 999999

        entry = await self.get_user(user_id)

        if entry is None:
            entry = Leaderboard(
                user_id=user_id,
                xp=total,
                rank=rank,
                updated_at=datetime.utcnow()
            )

            self.session.add(entry)
        else:
            entry.xp = total
            entry.rank = rank
            entry.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(entry)

        return entry

    async def recompute_all(self) -> int:
        result = await self.session.execute(
            select(XPHistory.user_id,func.sum(XPHistory.xp).label("total"))
            .group_by(XPHistory.user_id)
            .order_by(func.sum(XPHistory.xp).desc())
        )

        rows = result.all()

        for index,row in enumerate(rows,start=1):
            entry = await self.get_user(row.user_id)

            if entry is None:
                self.session.add(
                    Leaderboard(
                        user_id=row.user_id,
                        xp=row.total,
                        rank=index,
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                entry.xp = row.total
                entry.rank = index
                entry.updated_at = datetime.utcnow()

        await self.session.commit()

        return len(rows)