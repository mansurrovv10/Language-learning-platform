import pytest
from pydantic import ValidationError


def test_ai_routes_and_input_bounds_are_stable():
    """Catches missing capabilities or unbounded user-controlled AI input."""
    from backend.schemas.ai_schema import AIChatRequest, ChatTurn, ExamplesRequest
    from main import duolingo

    paths=duolingo.openapi()["paths"]
    for path in ("/ai/explain","/ai/hint","/ai/examples","/ai/chat",
                 "/ai/review","/ai/evaluate"):
        assert "post" in paths[path]
    with pytest.raises(ValidationError):
        AIChatRequest(message="x"*2001)
    with pytest.raises(ValidationError):
        AIChatRequest(message="ok",history=[ChatTurn(role="user",content="x")]*11)
    with pytest.raises(ValidationError):
        ExamplesRequest(exercise_id=1,count=6)


def test_ai_text_contracts_trim_and_reject_invalid_evaluation_input():
    from backend.schemas.ai_schema import (
        AIChatRequest,
        ChatTurn,
        EvaluationRequest,
        ExplanationResponse,
        HintResponse,
        ReplyResponse,
    )

    assert AIChatRequest(message="  hello  ").message == "hello"
    assert ChatTurn(role="user", content="  hi  ").content == "hi"
    assert ExplanationResponse(explanation="why").model_dump() == {
        "explanation": "why"
    }
    assert HintResponse(hint="think").model_dump() == {"hint": "think"}
    assert ReplyResponse(reply="hello").model_dump() == {"reply": "hello"}

    for payload in ("   ", None, 42, {"text": "answer"}):
        with pytest.raises(ValidationError):
            EvaluationRequest(exercise_id=1, answer=payload)

    with pytest.raises(ValidationError):
        AIChatRequest(message="   ")
    with pytest.raises(ValidationError):
        ChatTurn(role="user", content="   ")


def _run_immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("test coroutine unexpectedly required an event loop")


def test_ai_exercise_routes_enforce_access_and_hint_omits_answer():
    from types import SimpleNamespace

    from backend.api import ai as ai_api
    from backend.models.user import UserRole
    from backend.schemas.ai_schema import (
        EvaluationRequest,
        ExamplesRequest,
        ExerciseAnswerRequest,
        ExerciseRequest,
    )

    exercise = SimpleNamespace(
        id=7,
        lesson_id=9,
        question="Choose the greeting",
        options={"items": ["hello", "bye"]},
        correct_answer="hello",
    )

    class Session:
        async def get(self, model, exercise_id):
            return exercise

    class Access:
        def __init__(self):
            self.calls = []

        async def ensure_lesson_access(self, user_id, lesson_id):
            self.calls.append((user_id, lesson_id))

    class AIService:
        def __init__(self):
            self.calls = []

        async def generate(self, user_id, kind, instructions, input_text, **kwargs):
            self.calls.append((kind, input_text))
            if kind == "evaluate":
                return '{"accepted":true,"score":1,"feedback":"ok"}'
            return "one\ntwo"

    user = SimpleNamespace(id="user-1", role=UserRole.USER)
    access = Access()
    service = AIService()
    session = Session()

    _run_immediate(ai_api.explain(
        ExerciseAnswerRequest(exercise_id=7, answer="bye"),
        user,
        service,
        session,
        access,
    ))
    _run_immediate(ai_api.hint(
        ExerciseRequest(exercise_id=7), user, service, session, access
    ))
    _run_immediate(ai_api.examples(
        ExamplesRequest(exercise_id=7, count=2), user, service, session, access
    ))
    _run_immediate(ai_api.evaluate(
        EvaluationRequest(exercise_id=7, answer="hello"),
        user,
        service,
        session,
        access,
    ))

    assert access.calls == [("user-1", 9)] * 4
    hint_prompt = next(prompt for kind, prompt in service.calls if kind == "hint")
    assert '"expected"' not in hint_prompt
