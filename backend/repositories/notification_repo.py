import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import Notification,NotificationType


class NotificationRepository:
    def __init__(self,session: AsyncSession):
        self.session = session

    async def get_by_user(self,user_id: uuid.UUID) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self,notification_id: int) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        message: str
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            is_read=False
        )

        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

        return notification

    async def update(self,notification: Notification) -> Notification:
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def delete(self,notification: Notification) -> None:
        await self.session.delete(notification)
        await self.session.commit()