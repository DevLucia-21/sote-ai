# app/api/ocr.py
from fastapi import APIRouter, UploadFile, Form, HTTPException, Header, Depends
from app.services.ocr_service import run_ocr_preview
from datetime import date
import jwt
from redis.asyncio import Redis
from app.core.config import settings


# ----------------------------
# Redis 연결
# ----------------------------
redis = Redis(host="localhost", port=6379, decode_responses=True)

router = APIRouter(prefix="/ocr", tags=["ocr"])


# ----------------------------
# JWT 토큰에서 userId(sub) 추출
# ----------------------------
def get_current_user_id(authorization: str = Header(...)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="잘못된 인증 형식")

    token = authorization.split(" ")[1].strip()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,        # Spring과 같은 시크릿 키
            algorithms=["HS256"]
        )
        user_id = payload.get("sub") or payload.get("userId")
        if not user_id:
            raise HTTPException(status_code=401, detail="userId(sub) 없음")

        return int(user_id)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰 만료")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

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
