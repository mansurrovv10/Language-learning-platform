import uuid

from fastapi import HTTPException

from backend.models.course import LevelChoices
from backend.repositories.learning_path_repo import LearningPathRepository


LEVELS = [LevelChoices.A1,LevelChoices.A2,LevelChoices.B1,
          LevelChoices.B2,LevelChoices.C1,LevelChoices.C2]


class LearningPathService:
    def __init__(self,repository: LearningPathRepository):
        self.repository = repository

    async def get_path(self,user_id: uuid.UUID,language_id: int):
        user_language = await self.repository.get_user_language(user_id,language_id)
        level = user_language.level if user_language else None
        placement_completed = user_language.placement_completed if user_language else False
        courses = await self.repository.get_courses(language_id)
        result = []
        for course in courses:
            is_unlocked = placement_completed and self._is_unlocked(course.level,level)
            result.append({
                "id":course.id,
                "language_id":course.language_id,
                "title":course.title,
                "description":course.description,
                "level":course.level,
                "order":course.order,
                "is_unlocked":is_unlocked,
                "lessons":await self.repository.get_lessons(course.id) if is_unlocked else []
            })
        return {"language_id":language_id,"level":level,
            "placement_completed":placement_completed,"courses":result}

    def _is_unlocked(self,course_level,student_level):
        if student_level is None:
            return False
        return LEVELS.index(course_level) <= LEVELS.index(student_level)

    async def ensure_course_access(self,user_id: uuid.UUID,course_id: int):
        course = await self.repository.get_course(course_id)
        if not course:
            raise HTTPException(status_code=404,detail="Course not found")
        user_language = await self.repository.get_user_language(user_id,course.language_id)
        if not user_language or not user_language.placement_completed:
            raise HTTPException(status_code=403,detail="Complete placement test first")
        if not self._is_unlocked(course.level,user_language.level):
            raise HTTPException(status_code=403,detail="Course is locked for your current level")
        return course

    async def ensure_lesson_access(self,user_id: uuid.UUID,lesson_id: int):
        course = await self.repository.get_course_by_lesson(lesson_id)
        if not course:
            raise HTTPException(status_code=404,detail="Lesson not found")
        return await self.ensure_course_access(user_id,course.id)
