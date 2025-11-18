# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/config/gcp-ocr.json"

from app.api.stt import router as stt_router
from app.api.analysis import router as analysis_router
from app.api.ocr import router as ocr_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sote.main")

app = FastAPI(title="Sote AI API")

# ==============================
# CORS — 운영/개발 상관없이 통일
# ==============================
allow_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://sote.kr",
    "https://app.sote.kr",
    "https://fastapi.sote.kr",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=r"https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Router 등록
# ==============================
app.include_router(stt_router)
app.include_router(analysis_router)
app.include_router(ocr_router)

@app.get("/")
def root():
    return {"status": "ok", "service": "sote-ai"}
