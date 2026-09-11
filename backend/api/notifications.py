from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.database.db import get_session
from backend.models.user import UserProfile
from backend.repositories.notification_repo import NotificationRepository
from backend.schemas.notification_schema import NotificationResponse
from backend.services.notification_service import NotificationService


router = APIRouter(prefix="/notifications",tags=["Notifications"])


def get_notification_service(session: AsyncSession = Depends(get_session)):
    repository = NotificationRepository(session)
    return NotificationService(repository)


@router.get("",response_model=list[NotificationResponse])
async def get_notifications(
    service: NotificationService = Depends(get_notification_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.get_user_notifications(current_user.id)


@router.patch("/read-all")
async def mark_all_read(
    service: NotificationService = Depends(get_notification_service),
    current_user: UserProfile = Depends(get_current_user)
):
    return await service.mark_all_read(current_user.id)


@router.patch("/{notification_id}/read",response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
    current_user: UserProfile = Depends(get_current_user)
):
    result = await service.mark_as_read(notification_id,current_user.id)

    if result is None:
        raise HTTPException(status_code=404,detail="Notification not found")

    if result is False:
        raise HTTPException(status_code=403,detail="Access denied")

    return result


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
    current_user: UserProfile = Depends(get_current_user)
):
    result = await service.delete(notification_id,current_user.id)

    if result is None:
        raise HTTPException(status_code=404,detail="Notification not found")

    if result is False:
        raise HTTPException(status_code=403,detail="Access denied")

    return {"message":"Notification deleted"}