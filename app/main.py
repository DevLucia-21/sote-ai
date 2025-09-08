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

app = FastAPI(title="Sote AI API")

# -----------------------
# CORS 설정
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"] if settings.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(stt_router)
app.include_router(analysis_router)
app.include_router(ocr_router)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"status": "ok", "service": "sote-ai"}
