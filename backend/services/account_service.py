import os
from pathlib import Path
import uuid

from fastapi import UploadFile
from PIL import Image,UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import UserProfile
from backend.repositories.auth_repo import AuthRepository
from backend.repositories.user_repo import UserRepository


MAX_AVATAR_BYTES = 5 * 1024 * 1024
AVATAR_CHUNK_BYTES = 64 * 1024
MAX_AVATAR_PIXELS = 4096 * 4096
ALLOWED_AVATAR_EXTENSIONS = {".jpg",".jpeg",".png",".webp"}
AVATAR_FORMAT_EXTENSIONS = {"JPEG":".jpg","PNG":".png","WEBP":".webp"}


class AccountService:
    def __init__(self,session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.auth = AuthRepository(session)

    async def deactivate(self,user_id: uuid.UUID) -> None:
        user = await self.users.get_by_id(user_id)
        if user is None:
            return
        try:
            await self.users.set_active(user,False,commit=False)
            await self.auth.delete_refresh_tokens_for_user(user_id,commit=False)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def save_avatar(
        self,
        user: UserProfile,
        file: UploadFile,
        directory: Path,
    ) -> str:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_AVATAR_EXTENSIONS:
            await file.close()
            raise ValueError("UNSAFE_AVATAR_EXTENSION")

        directory = directory.resolve()
        directory.mkdir(parents=True,exist_ok=True)
        temporary = directory / f".{uuid.uuid4().hex}.upload"
        final_path = None

        try:
            size = 0
            with temporary.open("xb") as destination:
                while chunk := await file.read(AVATAR_CHUNK_BYTES):
                    size += len(chunk)
                    if size > MAX_AVATAR_BYTES:
                        raise ValueError("AVATAR_TOO_LARGE")
                    destination.write(chunk)

            try:
                with Image.open(temporary) as image:
                    if image.width * image.height > MAX_AVATAR_PIXELS:
                        raise ValueError("INVALID_AVATAR")
                    image.verify()
                    image_format = image.format
            except (OSError,UnidentifiedImageError,Image.DecompressionBombError):
                raise ValueError("INVALID_AVATAR")

            verified_suffix = AVATAR_FORMAT_EXTENSIONS.get(image_format)
            if verified_suffix is None:
                raise ValueError("INVALID_AVATAR")

            final_path = directory / f"{uuid.uuid4().hex}{verified_suffix}"
            os.replace(temporary,final_path)
            user.avatar = str(final_path)
            await self.session.commit()
            await self.session.refresh(user)
            return str(final_path)
        except Exception:
            await self.session.rollback()
            temporary.unlink(missing_ok=True)
            if final_path is not None:
                final_path.unlink(missing_ok=True)
            raise
        finally:
            await file.close()
