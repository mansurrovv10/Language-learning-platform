from backend.models.exercise import Exercise
from backend.repositories.exercise_repo import ExerciseRepository
from backend.schemas.exercise_schema import ExerciseCreate, ExerciseUpdate, ExerciseResult, ExerciseSubmit


class ExerciseService:
    def __init__(self, repository: ExerciseRepository):
        self.repository = repository

    async def get_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, exercise_id: int):
        return await self.repository.get_by_id(exercise_id)

    async def get_by_lesson(self, lesson_id: int):
        return await self.repository.get_by_lesson(lesson_id)

    async def create(self, data: ExerciseCreate):
        exercise = Exercise(**data.model_dump())
        return await self.repository.create(exercise)

    async def update(self, exercise_id: int, data: ExerciseUpdate):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return None

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(exercise, key, value)

        return await self.repository.update(exercise)

    async def delete(self, exercise_id: int):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return False

        await self.repository.delete(exercise)
        return True

    async def submit_exercise(self, exercise_id: int, data: ExerciseSubmit):
        exercise = await self.repository.get_by_id(exercise_id)

        if not exercise:
            return None

        correct = self._check_answer(exercise, data.answer)
        return ExerciseResult(correct=correct, score=10 if correct else 0)

    def _normalize(self, value):
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, dict):
            return {self._normalize(k): self._normalize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._normalize(item) for item in value]
        return value

    def _check_answer(self, exercise: Exercise, answer):
        expected = self._normalize(exercise.correct_answer)
        actual = self._normalize(answer)
        return actual == expected