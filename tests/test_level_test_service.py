from backend.models.course import LevelChoices
from backend.services.level_test_service import LevelTestService


def test_placement_level_requires_each_previous_level_to_pass():
    service = LevelTestService(None)
    answers = {
        LevelChoices.A1: [2, 2],
        LevelChoices.A2: [2, 2],
        LevelChoices.B1: [1, 2],
        LevelChoices.B2: [0, 0],
        LevelChoices.C1: [0, 0],
        LevelChoices.C2: [0, 0],
    }

    assert service._placement_level(answers,70) == LevelChoices.A2


def test_next_level_does_not_go_past_c2():
    service = LevelTestService(None)

    assert service._next_level(LevelChoices.A2) == LevelChoices.B1
    assert service._next_level(LevelChoices.C2) == LevelChoices.C2


def test_answer_normalization_ignores_case_and_spaces():
    service = LevelTestService(None)

    assert service._normalize({"Word":"  HELLO "}) == {"word":"hello"}
