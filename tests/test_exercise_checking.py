from types import SimpleNamespace

from backend.services.exercise_service import ExerciseService


def make_service():
    return ExerciseService(None, None, None, None)


def make_exercise(correct_answer):
    return SimpleNamespace(correct_answer=correct_answer)


def test_choice_answer_normalization():
    service = make_service()
    exercise = make_exercise("an")

    assert service._check_answer(exercise, " An  ") is True
    assert service._check_answer(exercise, "a") is False


def test_translate_answer_case_insensitive():
    service = make_service()
    exercise = make_exercise("Я люблю программирование")

    assert service._check_answer(exercise, "я люблю программирование") is True


def test_fill_gap_trim():
    service = make_service()
    exercise = make_exercise("drink")

    assert service._check_answer(exercise, "  drink ") is True
    assert service._check_answer(exercise, "coffee") is False


def test_match_pairs_normalization():
    service = make_service()
    exercise = make_exercise({
        "Apple": "Яблоко",
        "Dog": "Собака"
    })

    assert service._check_answer(
        exercise,
        {"apple": "яблоко", "dog": "собака"}
    ) is True

    assert service._check_answer(
        exercise,
        {"apple": "кот"}
    ) is False


def test_non_string_answer():
    service = make_service()
    exercise = make_exercise(7)

    assert service._check_answer(exercise, 7) is True
    assert service._check_answer(exercise, 8) is False