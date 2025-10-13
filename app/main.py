# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from fastapi.staticfiles import StaticFiles

# 라우터 임포트
from app.api.stt import router as stt_router
from app.api.analysis import router as analysis_router
from app.api.ocr import router as ocr_router 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sote.main")

# FastAPI 앱 초기화
app = FastAPI(title="Sote AI API")

# CORS 설정
# 개발 환경에서는 모든 Origin 허용 ("*")
# 운영 환경에서는 반드시 도메인 지정 권장 (예: ["https://sote.app"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT != "production" else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  라우터 등록
# stt_router 내부에 이미 prefix="/ai/stt" 존재하므로,
# 여기서는 prefix를 추가하지 않아야 함 (중복 방지)
app.include_router(stt_router)
app.include_router(analysis_router)
app.include_router(ocr_router)

# 정적 파일 서빙

app.mount("/static", StaticFiles(directory="static"), name="static")

#  헬스체크

@app.get("/")
def root():
    return {"status": "ok", "service": "sote-ai"}
