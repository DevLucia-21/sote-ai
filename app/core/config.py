# app/core/config.py
import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings(BaseSettings):
    # OpenAI API (감정 분석 등 API 호출용)
    OPENAI_API_KEY: Optional[str] = None

    # Whisper 로컬 추론 모델 이름 (tiny, base, small, medium, large 등)
    WHISPER_MODEL: str = "base"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"

settings = Settings()
