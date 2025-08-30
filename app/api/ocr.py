from fastapi import APIRouter, UploadFile, Form, Header
from app.services.ocr_service import run_ocr_preview

router = APIRouter()

@router.post("/preview")
async def ocr_preview(
    file: UploadFile,
    diary_date: str = Form(...),
    authorization: str = Header(...)
):
    # 사용자 토큰 받기
    token = authorization.replace("Bearer ", "")
    result = await run_ocr_preview(file, diary_date, token)
    return result
