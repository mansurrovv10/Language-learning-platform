from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PublicUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str