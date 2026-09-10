from backend.models.exercise import Exercise
from backend.repositories.exercise import ExerciseRepository
from backend.schemas.exercise import ExerciseCreate, ExerciseUpdate


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