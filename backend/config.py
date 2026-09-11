from pydantic_settings import BaseSettings,SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")

class Settings(BaseSettings):
    DATABASE_URL:str
    REDIS_URL:str="redis://localhost:6379/0"

    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings=Settings()
ALGORITHM="HS256"
ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7