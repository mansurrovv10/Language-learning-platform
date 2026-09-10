from pydantic import BaseModel, ConfigDict


class LanguageCreate(BaseModel):
    code: str
    name: str
    is_active: bool = False


class LanguageUpdate(BaseModel):
    code: str
    name: str
    is_active: bool


class LanguageResponse(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)