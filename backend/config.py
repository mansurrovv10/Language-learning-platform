from pydantic_settings import BaseSettings,SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")

class Settings(BaseSettings):
    DATABASE_URL:str
    REDIS_URL:str="redis://localhost:6379/0"
    ALLOWED_ORIGINS:str="http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,https://lingo-app.vercel.app"
    HOST:str="127.0.0.1"
    PORT:int=8001
    MAX_HEARTS:int=5
    HEART_REGEN_MINUTES:int=30
    HEART_REFILL_INTERVAL_SECONDS:int=30

    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self):
        return [o.strip().rstrip("/") for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

settings=Settings()
ALGORITHM="HS256"
ACCESS_TOKEN_LIFETIME=30
REFRESH_TOKEN_LIFETIME=7
MAX_HEARTS=settings.MAX_HEARTS
HEART_REGEN_MINUTES=settings.HEART_REGEN_MINUTES
HEART_REFILL_INTERVAL_SECONDS=settings.HEART_REFILL_INTERVAL_SECONDS