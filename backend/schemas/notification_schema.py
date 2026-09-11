import uuid
from datetime import datetime

from pydantic import BaseModel,ConfigDict

from backend.models.notification import NotificationType


class NotificationCreate(BaseModel):
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str


class NotificationResponse(BaseModel):
    id: int
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)