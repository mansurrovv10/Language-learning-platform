from backend.models.exercise import ExerciseType
from backend.services.exercise_service import ExerciseService


class ExerciseAnswer:
    def __init__(self,exercise_type,correct_answer):
        self.type = exercise_type
        self.correct_answer = correct_answer


def service():
    return ExerciseService(None,None,None,None,None)


def test_choice_normalizes_case_and_whitespace():
    exercise = ExerciseAnswer(ExerciseType.CHOICE,"  Hello  ")

    assert service()._check_answer(exercise,"hello") is True


def test_translate_preserves_word_order():
    exercise = ExerciseAnswer(ExerciseType.TRANSLATE,["i","love","you"])

    assert service()._check_answer(exercise,["you","love","i"]) is False


def test_fill_gap_preserves_answer_order():
    exercise = ExerciseAnswer(ExerciseType.FILL_GAP,["am","learning"])

    assert service()._check_answer(exercise,["learning","am"]) is False


def test_match_accepts_the_same_pairs_in_another_order():
    exercise = ExerciseAnswer(
        ExerciseType.MATCH,
        [["cat","кошка"],["dog","собака"]],
    )

    assert service()._check_answer(
        exercise,
        [["dog","собака"],["cat","кошка"]],
    ) is True


def test_null_answer_never_counts_as_correct():
    exercise = ExerciseAnswer(ExerciseType.CHOICE,None)

    assert service()._check_answer(exercise,None) is False
