# app/core/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

settings = Settings()
