# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from fastapi.staticfiles import StaticFiles

# 라우터 임포트 (stt는 필수로 포함)
from app.api.stt import router as stt_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sote.main")

app = FastAPI(title="Sote AI API")

# -----------------------
# CORS 설정 (필요에 맞게 수정)
# -----------------------
# 개발 중엔 모든 오리진 허용이 편리하지만, 운영 환경에선 엄격히 제한하세요.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"] if settings.ENVIRONMENT == "production" else ["*"],            # 운영환경에서는 도메인 지정 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 라우터 등록
app.include_router(stt_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"status": "ok", "service": "sote-ai"}
