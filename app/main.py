# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 앱 설정
from app.core.config import settings

# Router import
from app.api.stt import router as stt_router
from app.api.analysis import router as analysis_router
from app.api.ocr import router as ocr_router
from app.api.debug import router as debug_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sote.main")

# FastAPI 초기화
app = FastAPI(title="Sote AI API")

# ======================================================
# CORS 설정 — 운영/개발 동일하게 허용
# ======================================================
allow_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    # 사용자 프론트
    "https://sote.kr",
    "https://app.sote.kr",

    # FastAPI 서브도메인
    "https://fastapi.sote.kr",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# 라우터 등록
# ======================================================
app.include_router(stt_router)
app.include_router(analysis_router)
app.include_router(ocr_router)
app.include_router(debug_router)

# ======================================================
# 헬스 체크
# ======================================================
@app.get("/")
def root():
    return {"status": "ok", "service": "sote-ai"}
