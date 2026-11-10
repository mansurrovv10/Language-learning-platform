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
