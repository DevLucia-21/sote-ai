# app/core/config.py

import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").strip()
candidate_env = BASE_DIR / f".env.{ENVIRONMENT}"
env_path = candidate_env if candidate_env.exists() else (BASE_DIR / ".env")

load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # OpenAI (로컬 추론만 쓰면 False 유지)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ENABLE_OPENAI: bool = os.getenv("ENABLE_OPENAI", "false").lower() == "true"

    # Whisper 공통
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "auto")         # "auto" | "tiny" | "base" | "small" ...
    DEPLOY_TARGET: str = os.getenv("DEPLOY_TARGET", "auto")         # "auto" | "mobile" | "desktop" | "server"
    MIN_RAM_FOR_SMALL_GB: int = int(os.getenv("MIN_RAM_FOR_SMALL_GB", 8))     # small 시도 최소 가용 RAM(GB)

    STT_PROVIDER: Optional[str] = None
    
    # faster-whisper 전용 (없으면 자동 선택)
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "auto")       # "auto" | "cpu" | "cuda"
    WHISPER_COMPUTE_TYPE: Optional[str] = os.getenv("WHISPER_COMPUTE_TYPE")
    # 예: "int8", "int8_float16", "float16" (None이면 디바이스/RAM 보고 자동 결정)

    # STT 런타임 기본 동작 튜닝
    STT_DEFAULT_TIMEOUT_SECONDS: float = float(os.getenv("STT_DEFAULT_TIMEOUT_SECONDS", 30.0))  # prefer 모델 타임아웃
    STT_VAD_DEFAULT: bool = os.getenv("STT_VAD_DEFAULT", "false").lower() == "true"             # 간단 무음 제거 기본값
    STT_LOW_CONF_RETRANSCRIBE: bool = os.getenv("STT_LOW_CONF_RETRANSCRIBE", "true").lower() == "true"       # 저신뢰 구간 재추론 기본값
    STT_LOW_CONF_THRESHOLD: float = float(os.getenv("STT_LOW_CONF_THRESHOLD", -1.0))            # avg_logprob 임계값

    # 현재 환경
    ENVIRONMENT: str = ENVIRONMENT

    class Config:
        env_file = env_path
        env_file_encoding = "utf-8"

settings = Settings()

print(f"ENVIRONMENT={settings.ENVIRONMENT}, using env file: {env_path}")
print(
    f"DEPLOY_TARGET={settings.DEPLOY_TARGET}, "
    f"WHISPER_MODEL={settings.WHISPER_MODEL}, "
    f"MIN_RAM_FOR_SMALL_GB={settings.MIN_RAM_FOR_SMALL_GB}, "
    f"WHISPER_DEVICE={settings.WHISPER_DEVICE}, "
    f"WHISPER_COMPUTE_TYPE={settings.WHISPER_COMPUTE_TYPE}"
)
if settings.OPENAI_API_KEY and settings.ENABLE_OPENAI:
    print("⚠️ OpenAI API enabled — costs may apply.")
else:
    print("Running in LOCAL-only mode (OpenAI disabled).")
