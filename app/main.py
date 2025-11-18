# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from fastapi.staticfiles import StaticFiles

import os

# -------------------------------------------
# 반드시 필요한 GCP Credentials 경로 지정
# Dockerfile에서 생성하는 경로와 동일해야 함
# -------------------------------------------
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/config/gcp-ocr.json"

# 라우터 임포트
from app.api.stt import router as stt_router
from app.api.analysis import router as analysis_router
from app.api.ocr import router as ocr_router 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sote.main")

# FastAPI 앱 초기화
app = FastAPI(title="Sote AI API")

# CORS 설정
# CORS 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://sote.kr",
    "https://app.sote.kr",
    "https://fastapi.sote.kr",
]

# 운영/개발 구분
if settings.ENVIRONMENT != "production":
    allow_origins = ["*"]
else:
    allow_origins = origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=r"https://.*\.vercel\.app$", 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(stt_router)
app.include_router(analysis_router)
app.include_router(ocr_router)

# 헬스체크
@app.get("/")
def root():
    return {"status": "ok", "service": "sote-ai"}
