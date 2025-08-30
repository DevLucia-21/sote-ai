from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import ocr

app = FastAPI()

# 업로드 폴더 static으로 제공 (선택)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# OCR 라우터 등록
app.include_router(ocr.router, prefix="/ocr")
