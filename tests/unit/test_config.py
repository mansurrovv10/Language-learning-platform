import pytest
from pydantic import ValidationError

from backend.config import Settings


def test_settings_reject_blank_secret_key():
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test",
            SECRET_KEY="",
        )


@pytest.mark.parametrize("secret",["short","change-me-in-production"])
def test_settings_reject_weak_or_placeholder_secret_key(secret):
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/test",
            SECRET_KEY=secret,
        )
