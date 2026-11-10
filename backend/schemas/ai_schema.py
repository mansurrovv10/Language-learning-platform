import json
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator

BoundedText = Annotated[str, Field(min_length=1,max_length=2000)]


class ExerciseAnswerRequest(BaseModel):
    exercise_id: int
    answer: Any

    @field_validator("answer")
    @classmethod
    def bound_answer(cls,value):
        if len(json.dumps(value,ensure_ascii=False,allow_nan=False)) > 2000:
            raise ValueError("answer is too long")
        return value


class ExerciseRequest(BaseModel):
    exercise_id: int


class ExamplesRequest(ExerciseRequest):
    count: int = Field(default=3,ge=1,le=5)


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1,max_length=1000)


class AIChatRequest(BaseModel):
    message: BoundedText
    history: list[ChatTurn] = Field(default_factory=list,max_length=10)


class TextResponse(BaseModel):
    text: str


class ExamplesResponse(BaseModel):
    examples: list[str]


class ReviewResponse(BaseModel):
    tasks: list[str]


class EvaluationResponse(BaseModel):
    accepted: bool
    score: float = Field(ge=0,le=1)
    feedback: str
