from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_ID: int
    API_HASH: str
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///app.db"

    class Config:
        env_file = ".env"

settings = Settings()