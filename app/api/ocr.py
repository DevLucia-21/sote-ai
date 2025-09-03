# app/api/ocr.py
from fastapi import APIRouter, UploadFile, Form, HTTPException
from app.services.ocr_service import run_ocr_preview

router = APIRouter(prefix="/ocr", tags=["ocr"])

@router.post("/preview")
async def ocr_preview(
    file: UploadFile,
    diary_date: str = Form(...),   # form-data에서 날짜 받기
):
    """
    OCR 미리보기만 수행.
    - 저장은 하지 않음
    - 반환값: { text, imageUrl, diaryDate }
    """
    try:
        result = await run_ocr_preview(file, diary_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 처리 실패: {e}")
