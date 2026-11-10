import hashlib
import uuid

from backend.providers.openai_provider import AIUnsafeError
from backend.repositories.ai_usage_repo import AIQuotaExceededError


class AIError(RuntimeError):
    pass


class AIService:
    def __init__(self, provider, usage_repository):
        self.provider = provider
        self.usage_repository = usage_repository

    async def generate(
        self,
        user_id: uuid.UUID,
        request_type: str,
        instructions: str,
        input_text: str,
        *,
        max_output_tokens: int = 300,
        structured: bool = False,
    ) -> str:
        if self.provider is None:
            raise AIError("AI_UNAVAILABLE")
        try:
            usage = await self.usage_repository.reserve(
                user_id, request_type, self.provider.model)
        except AIQuotaExceededError as error:
            raise AIError("AI_QUOTA_EXCEEDED") from error
        safety_identifier = hashlib.sha256(str(user_id).encode()).hexdigest()
        try:
            result = await self.provider.generate(
                instructions=instructions,
                input_text=input_text,
                safety_identifier=safety_identifier,
                max_output_tokens=max_output_tokens,
                structured=structured,
            )
        except AIUnsafeError as error:
            code = str(error)
            await self.usage_repository.finish(
                usage.id, successful=False, error_code=code)
            raise AIError(code) from error
        except Exception as error:
            await self.usage_repository.finish(
                usage.id, successful=False, error_code="AI_PROVIDER_ERROR"
            )
            raise AIError("AI_PROVIDER_ERROR") from error
        await self.usage_repository.finish(
            usage.id,
            successful=True,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )
        return result.text
