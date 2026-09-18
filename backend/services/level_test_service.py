import uuid

from fastapi import HTTPException

from backend.models.course import LevelChoices
from backend.models.level_test import LevelTest, LevelTestAttempt, LevelTestQuestion
from backend.models.user_language import UserLanguage
from backend.repositories.level_test_repo import LevelTestRepository
from backend.schemas.level_test_schema import (LevelTestCreate,LevelTestQuestionCreate,
    LevelTestQuestionUpdate,LevelTestSubmit,LevelTestUpdate)


LEVELS = [LevelChoices.A1,LevelChoices.A2,LevelChoices.B1,
          LevelChoices.B2,LevelChoices.C1,LevelChoices.C2]


class LevelTestService:
    def __init__(self,repository: LevelTestRepository):
        self.repository = repository

    async def get_tests(self,language_id: int | None = None):
        return await self.repository.get_tests(language_id)

    async def get_test(self,test_id: uuid.UUID):
        return await self.repository.get_test(test_id)

    async def create_test(self,data: LevelTestCreate):
        if not data.is_placement and data.target_level is None:
            raise HTTPException(status_code=422,detail="Completion test requires target_level")
        if data.is_placement and data.target_level is not None:
            raise HTTPException(status_code=422,detail="Placement test cannot have target_level")
        return await self.repository.create_test(LevelTest(**data.model_dump()))

    async def update_test(self,test_id: uuid.UUID,data: LevelTestUpdate):
        test = await self.repository.get_test(test_id)
        if not test:
            return None
        for key,value in data.model_dump(exclude_unset=True).items():
            setattr(test,key,value)
        if not test.is_placement and test.target_level is None:
            raise HTTPException(status_code=422,detail="Completion test requires target_level")
        return await self.repository.update_test(test)

    async def delete_test(self,test_id: uuid.UUID):
        test = await self.repository.get_test(test_id)
        if not test:
            return False
        await self.repository.delete_test(test)
        return True

    async def create_question(self,test_id: uuid.UUID,data: LevelTestQuestionCreate):
        test = await self.repository.get_test(test_id)
        if not test:
            return None
        question = LevelTestQuestion(test_id=test_id,**data.model_dump())
        return await self.repository.create_question(question)

    async def update_question(self,question_id: int,data: LevelTestQuestionUpdate):
        question = await self.repository.get_question(question_id)
        if not question:
            return None
        for key,value in data.model_dump(exclude_unset=True).items():
            setattr(question,key,value)
        return await self.repository.update_question(question)

    async def delete_question(self,question_id: int):
        question = await self.repository.get_question(question_id)
        if not question:
            return False
        await self.repository.delete_question(question)
        return True

    async def get_questions(self,test_id: uuid.UUID):
        return await self.repository.get_questions(test_id)

    async def start_placement(self,user_id: uuid.UUID,language_id: int):
        test = await self.repository.get_active_test(language_id,True)
        if not test:
            raise HTTPException(status_code=404,detail="Active placement test not found")
        return await self._create_attempt(user_id,test)

    async def start_completion(self,user_id: uuid.UUID,language_id: int,level: LevelChoices):
        user_language = await self.repository.get_user_language(user_id,language_id)
        if not user_language or not user_language.placement_completed:
            raise HTTPException(status_code=403,detail="Placement test must be completed first")
        if user_language.level != level:
            raise HTTPException(status_code=403,detail="Completion test is available only for your current level")
        if not await self.repository.are_level_lessons_completed(user_id,language_id,level):
            raise HTTPException(status_code=403,detail="Complete all lessons of this level first")
        test = await self.repository.get_active_test(language_id,False,level)
        if not test:
            raise HTTPException(status_code=404,detail="Active completion test not found")
        return await self._create_attempt(user_id,test)

    async def _create_attempt(self,user_id: uuid.UUID,test: LevelTest):
        questions = await self.repository.get_questions(test.id)
        if not questions:
            raise HTTPException(status_code=400,detail="Test has no questions")
        attempt = LevelTestAttempt(test_id=test.id,user_id=user_id,language_id=test.language_id)
        attempt = await self.repository.create_attempt(attempt)
        return attempt,test,questions

    async def submit_attempt(self,user_id: uuid.UUID,attempt_id: uuid.UUID,data: LevelTestSubmit):
        attempt = await self.repository.get_attempt(attempt_id)
        if not attempt:
            raise HTTPException(status_code=404,detail="Test attempt not found")
        if attempt.user_id != user_id:
            raise HTTPException(status_code=403,detail="Access denied")
        if attempt.completed_at is not None:
            raise HTTPException(status_code=400,detail="Test attempt is already completed")

        test = await self.repository.get_test(attempt.test_id)
        questions = await self.repository.get_questions(test.id)
        answers = {item.question_id:item.answer for item in data.answers}
        expected_ids = {question.id for question in questions}
        if set(answers) != expected_ids:
            raise HTTPException(status_code=422,detail="Answer every test question exactly once")

        correct_by_level = {level:[0,0] for level in LEVELS}
        correct_total = 0
        for question in questions:
            correct_by_level[question.level][1] += 1
            if self._normalize(answers[question.id]) == self._normalize(question.correct_answer):
                correct_total += 1
                correct_by_level[question.level][0] += 1

        score = round(correct_total / len(questions) * 100,2)
        if test.is_placement:
            result_level = self._placement_level(correct_by_level,test.passing_score)
            passed = True
            user_language = await self.repository.get_user_language(user_id,test.language_id)
            if not user_language:
                user_language = UserLanguage(user_id=user_id,language_id=test.language_id)
                user_language.level = result_level
                user_language.placement_completed = True
                await self.repository.create_user_language(user_language)
            else:
                user_language.level = result_level
                user_language.placement_completed = True
                await self.repository.update_user_language(user_language)
        else:
            passed = score >= test.passing_score
            result_level = self._next_level(test.target_level) if passed else test.target_level
            if passed:
                user_language = await self.repository.get_user_language(user_id,test.language_id)
                user_language.level = result_level
                await self.repository.update_user_language(user_language)

        return await self.repository.complete_attempt(attempt,score,passed,result_level)

    def _placement_level(self,correct_by_level,passing_score: int):
        result = LevelChoices.A1
        for level in LEVELS:
            correct,total = correct_by_level[level]
            if total and correct / total * 100 >= passing_score:
                result = level
            else:
                break
        return result

    def _next_level(self,level: LevelChoices):
        index = LEVELS.index(level)
        if index == len(LEVELS) - 1:
            return level
        return LEVELS[index + 1]

    def _normalize(self,value):
        if isinstance(value,str):
            return value.strip().lower()
        if isinstance(value,dict):
            return {self._normalize(key):self._normalize(item) for key,item in value.items()}
        if isinstance(value,list):
            return [self._normalize(item) for item in value]
        return value
