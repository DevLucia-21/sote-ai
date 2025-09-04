# app/api/ocr.py
from fastapi import APIRouter, UploadFile, Form, HTTPException, Header, Depends
from app.services.ocr_service import run_ocr_preview
from datetime import date
import jwt
from redis.asyncio import Redis

# ----------------------------
# Redis 연결
# ----------------------------
redis = Redis(host="localhost", port=6379, decode_responses=True)

router = APIRouter(prefix="/ocr", tags=["ocr"])


# ----------------------------
# JWT 토큰에서 userId(sub) 추출
# ----------------------------
def get_current_user_id(authorization: str = Header(...)) -> int:
    """
    Authorization 헤더에서 JWT 파싱 후 sub(사용자 ID) 추출
    - 예: "Authorization: Bearer <token>"
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="잘못된 인증 형식")
    token = authorization.replace("Bearer ", "")

    try:
        # ⚠️ verify_signature=False → 테스트/개발용
        # 운영에서는 반드시 시크릿 키 검증 필요
        payload = jwt.decode(token, options={"verify_signature": False})
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="sub 없음")
        return int(sub)  # "1" → 1
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 파싱 실패")


# ----------------------------
# OCR 하루 1회 제한 함수 (Redis)
# ----------------------------
async def check_ocr_limit(user_id: int):
    today = date.today().isoformat()
    key = f"ocr:{user_id}:{today}"

    exists = await redis.exists(key)
    if exists:
        raise HTTPException(
            status_code=403,
            detail="오늘은 이미 OCR을 실행했습니다. 하루 1회만 가능합니다."
        )

    # TTL = 24시간
    await redis.set(key, "1", ex=60 * 60 * 24)


# ----------------------------
# OCR Preview API
# ----------------------------
@router.post("/preview")
async def ocr_preview(
    file: UploadFile,
    diary_date: str = Form(...),
    user_id: int = Depends(get_current_user_id),  # JWT에서 userId 추출
):
    """
    OCR 미리보기 (하루 1회 제한 적용, Redis 기반)
    - 저장은 하지 않음
    - 반환값: { text, imageUrl, diaryDate }
    """
    # 하루 1회 제한 체크
    await check_ocr_limit(user_id)

    try:
        result = await run_ocr_preview(file, diary_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 처리 실패: {e}")
