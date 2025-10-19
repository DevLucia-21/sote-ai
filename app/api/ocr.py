# app/api/ocr.py
from fastapi import APIRouter, UploadFile, Form, HTTPException
from app.services.ocr_service import run_ocr_preview
from datetime import date
from redis.asyncio import Redis
from datetime import datetime, timedelta
from app.core.config import settings

# ----------------------------
# Redis 연결
# ----------------------------
redis = Redis(host="localhost", port=6379, decode_responses=True)

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

    # 현재 시각 기준으로 자정까지 남은 초 계산
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
    user_id: int = Form(...),   # JWT 대신 Form 데이터로 uid 받음
):
    """
    OCR 미리보기 (하루 1회 제한 적용, Redis 기반)
    - OCR 실패 시에는 제한 카운트되지 않음
    - 성공 시에만 Redis에 등록
    - 반환값: { text, imageUrl }
    """
    # 이미 실행했는지 먼저 확인
    if await has_ocr_limit(user_id):
        raise HTTPException(
            status_code=403,
            detail="오늘은 이미 OCR을 실행했습니다. 하루 1회만 가능합니다."
        )

    try:
        # OCR 실행
        result = await run_ocr_preview(file)
        result["userId"] = user_id

        # OCR 성공 시에만 하루 제한 등록
        await mark_ocr_done(user_id)

        return result

    except Exception as e:
        # 실패 시 제한 미적용
        print(f"[OCR ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR 처리 실패: {e}")
