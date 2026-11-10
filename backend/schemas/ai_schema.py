import json
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints, field_validator

BoundedText = Annotated[
    str, StringConstraints(strip_whitespace=True,min_length=1,max_length=2000)
]
BoundedHistoryText = Annotated[
    str, StringConstraints(strip_whitespace=True,min_length=1,max_length=1000)
]


class ExerciseAnswerRequest(BaseModel):
    exercise_id: int
    answer: Any

    @field_validator("answer")
    @classmethod
    def bound_answer(cls,value):
        if value is None:
            raise ValueError("answer is required")
        if isinstance(value,str):
            value = value.strip()
            if not value:
                raise ValueError("answer is required")
        if len(json.dumps(value,ensure_ascii=False,allow_nan=False)) > 2000:
            raise ValueError("answer is too long")
        return value


class ExerciseRequest(BaseModel):
    exercise_id: int


class ExamplesRequest(ExerciseRequest):
    count: int = Field(default=3,ge=1,le=5)


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: BoundedHistoryText


class AIChatRequest(BaseModel):
    message: BoundedText
    history: list[ChatTurn] = Field(default_factory=list,max_length=10)


class EvaluationRequest(BaseModel):
    exercise_id: int
    answer: BoundedText


class ExplanationResponse(BaseModel):
    explanation: str


class HintResponse(BaseModel):
    hint: str


class ReplyResponse(BaseModel):
    reply: str


class ExamplesResponse(BaseModel):
    examples: list[str]


class ReviewResponse(BaseModel):
    tasks: list[str]


class EvaluationResponse(BaseModel):
    accepted: bool
    score: float = Field(ge=0,le=1)
    feedback: str
