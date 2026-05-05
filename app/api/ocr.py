from fastapi import APIRouter, UploadFile, Form, HTTPException, Query, Depends
from app.services.ocr_service import run_ocr_preview, delete_ocr_image
from app.core.security import verify_internal_ai_key

from datetime import date, datetime, timedelta
import os
from redis.asyncio import Redis

# ----------------------------
# Redis 연결
# ----------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis = Redis.from_url(
    REDIS_URL,
    decode_responses=True
)

router = APIRouter(prefix="/ocr", tags=["ocr"])

# ----------------------------
# OCR 하루 1회 제한 관련 함수 (Redis)
# ----------------------------
async def has_ocr_limit(user_id: int) -> bool:
    """이미 OCR을 실행한 적이 있는지 확인"""
    today = date.today().isoformat()
    key = f"ocr:{user_id}:{today}"
    return await redis.exists(key)


async def mark_ocr_done(user_id: int):
    """OCR 성공 시 자정까지 제한"""
    today = date.today().isoformat()
    key = f"ocr:{user_id}:{today}"

    now = datetime.now()
    midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    seconds_until_midnight = int((midnight - now).total_seconds())

    await redis.set(key, "1", ex=seconds_until_midnight)
    print(f"[OCR LIMIT] {key} 저장 완료 (자정까지 {seconds_until_midnight}초 TTL)")


# ----------------------------
# OCR Preview API
# ----------------------------
@router.post("/preview")
async def ocr_preview(
    file: UploadFile,
    user_id: int = Form(...),
):
    """
    OCR 미리보기 (하루 1회 제한 적용, Redis 기반)
    - OCR 실패 시에는 제한 카운트되지 않음
    - 성공 시에만 Redis에 등록
    - 반환값: { text, imageUrl, filename }
    """
    if await has_ocr_limit(user_id):
        raise HTTPException(
            status_code=403,
            detail="오늘은 이미 OCR을 실행했습니다. 하루 1회만 가능합니다."
        )

    try:
        result = await run_ocr_preview(file)
        result["userId"] = user_id

        await mark_ocr_done(user_id)

        print(f"[OCR PREVIEW DONE] user_id={user_id}, text_len={len(result.get('text', ''))}")
        return result

    except Exception as e:
        print(f"[OCR ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 처리 실패: {e}")


# ----------------------------
# OCR 이미지 삭제 API
# ----------------------------
@router.delete("/delete")
async def ocr_delete(
    filename: str = Query(..., description="삭제할 이미지 파일명 (예: 1234abcd.jpg)"),
):
    """
    GCS에서 OCR 이미지 삭제
    - Spring 일기 삭제 시 filename을 함께 전달하면 GCS에서도 자동 삭제 가능
    - 삭제 성공 시 { deleted: true }
    """
    try:
        deleted = await delete_ocr_image(filename)
        if deleted:
            return {"status": "success", "deleted": True, "filename": filename}
        else:
            return {"status": "not_found", "deleted": False, "filename": filename}
    except Exception as e:
        print(f"[OCR DELETE ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 삭제 실패: {e}")