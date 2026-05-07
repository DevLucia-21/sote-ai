# app/core/config.py

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").strip()
candidate_env = BASE_DIR / f".env.{ENVIRONMENT}"
env_path = candidate_env if candidate_env.exists() else (BASE_DIR / ".env")

load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret")

    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ENABLE_OPENAI: bool = os.getenv("ENABLE_OPENAI", "false").lower() == "true"

    # Whisper 공통
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "auto")
    DEPLOY_TARGET: str = os.getenv("DEPLOY_TARGET", "auto")
    MIN_RAM_FOR_SMALL_GB: int = int(os.getenv("MIN_RAM_FOR_SMALL_GB", 8))

    STT_PROVIDER: Optional[str] = None

    # faster-whisper 전용
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "auto")
    WHISPER_COMPUTE_TYPE: Optional[str] = os.getenv("WHISPER_COMPUTE_TYPE")

    # STT 런타임 기본 동작 튜닝
    STT_DEFAULT_TIMEOUT_SECONDS: float = float(
        os.getenv("STT_DEFAULT_TIMEOUT_SECONDS", 30.0)
    )
    STT_VAD_DEFAULT: bool = os.getenv("STT_VAD_DEFAULT", "false").lower() == "true"
    STT_LOW_CONF_RETRANSCRIBE: bool = (
        os.getenv("STT_LOW_CONF_RETRANSCRIBE", "true").lower() == "true"
    )
    STT_LOW_CONF_THRESHOLD: float = float(
        os.getenv("STT_LOW_CONF_THRESHOLD", -1.0)
    )

    # Spring 서버 연동
    SPRING_SERVER_URL: str = os.getenv("SPRING_SERVER_URL", "http://localhost:8080")
    SPRING_BOOT_URL: str = os.getenv(
        "SPRING_BOOT_URL",
        "http://localhost:8080/api/stt/results",
    )

    SPRING_OCR_URL: str = os.getenv(
        "SPRING_OCR_URL",
        "http://localhost:8080/api/ocr/results",
    )
    SPRING_STT_URL: str = os.getenv(
        "SPRING_STT_URL",
        "http://localhost:8080/api/stt/results",
    )

    # GCP 인증
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    # 플래그
    SEND_STT_TO_SPRING: bool = (
        os.getenv("SEND_STT_TO_SPRING", "false").lower() == "true"
    )
    SEND_OCR_TO_SPRING: bool = (
        os.getenv("SEND_OCR_TO_SPRING", "false").lower() == "true"
    )

    # ffmpeg 실행 파일 경로
    FFMPEG_BIN: str = os.getenv("FFMPEG_BIN", "ffmpeg")

    # 현재 환경
    ENVIRONMENT: str = ENVIRONMENT

    class Config:
        env_file = env_path
        env_file_encoding = "utf-8"


settings = Settings()

logger.info("ENVIRONMENT=%s, using env file: %s", settings.ENVIRONMENT, env_path)

logger.info(
    "DEPLOY_TARGET=%s, WHISPER_MODEL=%s, MIN_RAM_FOR_SMALL_GB=%s, "
    "WHISPER_DEVICE=%s, WHISPER_COMPUTE_TYPE=%s, FFMPEG_BIN=%s",
    settings.DEPLOY_TARGET,
    settings.WHISPER_MODEL,
    settings.MIN_RAM_FOR_SMALL_GB,
    settings.WHISPER_DEVICE,
    settings.WHISPER_COMPUTE_TYPE,
    settings.FFMPEG_BIN,
)

if settings.OPENAI_API_KEY and settings.ENABLE_OPENAI:
    logger.warning("OpenAI API enabled — costs may apply.")
else:
    logger.info("Running in LOCAL-only mode. OpenAI is disabled.")