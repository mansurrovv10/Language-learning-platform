from io import BytesIO
from pathlib import Path
import uuid

import pytest
from fastapi import HTTPException,UploadFile
from PIL import Image
from sqlalchemy import func,select

from backend.models.gamification import Hearts
from backend.models.user import RefreshToken,UserProfile
from backend.services.auth_ser import AuthService


pytestmark = [pytest.mark.integration,pytest.mark.asyncio(loop_scope="session")]


def upload(filename: str,data: bytes) -> UploadFile:
    return UploadFile(file=BytesIO(data),filename=filename)


def png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB",(8,8),(30,120,200)).save(buffer,format="PNG")
    return buffer.getvalue()


async def test_deactivation_preserves_state_and_revokes_tokens(db_session):
    from backend.services.account_service import AccountService

    auth = AuthService(db_session)
    email = f"deactivate-{uuid.uuid4().hex}@example.com"
    user = await auth.register(
        email,f"deactivate_{uuid.uuid4().hex}","password123"
    )
    tokens = await auth.login(email,"password123")

    service = AccountService(db_session)
    await service.deactivate(user.id)
    await service.deactivate(user.id)

    stored_user = await db_session.get(UserProfile,user.id)
    hearts_count = await db_session.scalar(
        select(func.count()).select_from(Hearts).where(Hearts.user_id == user.id)
    )
    token_count = await db_session.scalar(
        select(func.count()).select_from(RefreshToken).where(
            RefreshToken.users_id == user.id
        )
    )

    assert stored_user is not None
    assert stored_user.is_active is False
    assert hearts_count == 1
    assert token_count == 0

    with pytest.raises(HTTPException) as login_error:
        await auth.login(email,"password123")
    assert login_error.value.status_code == 403

    with pytest.raises(HTTPException) as refresh_error:
        await auth.refresh(tokens["refresh_token"])
    assert refresh_error.value.status_code == 401


@pytest.mark.parametrize(
    ("filename","data","code"),
    [
        ("avatar.svg",b"<svg xmlns='http://www.w3.org/2000/svg'></svg>","UNSAFE_AVATAR_EXTENSION"),
        ("avatar.png",b"not an image","INVALID_AVATAR"),
        ("avatar.png",b"x" * (5 * 1024 * 1024 + 1),"AVATAR_TOO_LARGE"),
        ("avatar.exe",png_bytes(),"UNSAFE_AVATAR_EXTENSION"),
    ],
    ids=["svg","invalid-bytes","oversized","unsafe-extension"],
)
async def test_avatar_rejects_unsafe_files(
    db_session,tmp_path,filename,data,code
):
    from backend.services.account_service import AccountService

    user = await AuthService(db_session).register(
        f"avatar-bad-{uuid.uuid4().hex}@example.com",
        f"avatar_bad_{uuid.uuid4().hex}",
        "password123",
    )

    with pytest.raises(ValueError,match=code):
        await AccountService(db_session).save_avatar(
            user,upload(filename,data),tmp_path
        )

    assert list(tmp_path.iterdir()) == []


async def test_avatar_uses_verified_format_and_generated_name(db_session,tmp_path):
    from backend.services.account_service import AccountService

    user = await AuthService(db_session).register(
        f"avatar-good-{uuid.uuid4().hex}@example.com",
        f"avatar_good_{uuid.uuid4().hex}",
        "password123",
    )
    original_name = "../../my-profile.png"

    stored = await AccountService(db_session).save_avatar(
        user,upload(original_name,png_bytes()),tmp_path
    )
    stored_path = tmp_path / Path(stored).name

    assert stored_path.parent.resolve() == tmp_path.resolve()
    assert stored_path.suffix == ".png"
    assert stored_path.name != Path(original_name).name
    assert stored_path.exists()
    assert stored == f"/uploads/avatars/{stored_path.name}"
    assert user.avatar == stored
