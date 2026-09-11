import uuid

from backend.models.notification import NotificationType
from backend.repositories.notification_repo import NotificationRepository


class NotificationService:
    def __init__(self,repository: NotificationRepository):
        self.repository = repository

    async def get_user_notifications(self,user_id: uuid.UUID):
        return await self.repository.get_by_user(user_id)

    async def create(
        self,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        message: str
    ):
        return await self.repository.create(
            user_id=user_id,
            type=type,
            title=title,
            message=message
        )

    async def mark_as_read(
        self,
        notification_id: int,
        user_id: uuid.UUID
    ):
        notification = await self.repository.get_by_id(notification_id)

        if not notification:
            return None

        if notification.user_id != user_id:
            return False

        notification.is_read = True
        return await self.repository.update(notification)

    async def mark_all_read(self,user_id: uuid.UUID):
        notifications = await self.repository.get_by_user(user_id)
        updated = 0

        for notification in notifications:
            if not notification.is_read:
                notification.is_read = True
                await self.repository.update(notification)
                updated += 1

        return {"updated": updated}

    async def delete(
        self,
        notification_id: int,
        user_id: uuid.UUID
    ):
        notification = await self.repository.get_by_id(notification_id)

        if not notification:
            return None

        if notification.user_id != user_id:
            return False

        await self.repository.delete(notification)
        return True