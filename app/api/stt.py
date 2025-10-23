from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Request
from app.services.stt_service import transcribe_audio
from app.core.config import settings
from typing import Optional
from datetime import datetime, timedelta, date, timezone
import io, os, shutil, tempfile, uuid, subprocess, requests
from pathlib import Path
from redis.asyncio import Redis

router = APIRouter(prefix="/ai/stt", tags=["stt"])

# ----------------------------
# ffmpeg 경로 설정
# ----------------------------
FFMPEG_BIN = settings.FFMPEG_BIN or shutil.which("ffmpeg") or "ffmpeg"

# ----------------------------
# Redis 연결
# ----------------------------
redis = Redis(host="localhost", port=6379, decode_responses=True)


# ----------------------------
# STT 하루 1회 제한 (Redis)
# ----------------------------
async def check_stt_limit(user_id: int):
    today = date.today().isoformat()
    key = f"stt:{user_id}:{today}"

    exists = await redis.exists(key)
    if exists:
        raise HTTPException(status_code=403, detail="오늘은 이미 STT를 실행했습니다. 하루 1회만 가능합니다.")

    # 한국시간(KST) 기준 자정까지 TTL 계산
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=KST)
    seconds_until_midnight = int((midnight - now).total_seconds())

    await redis.set(key, "1", ex=seconds_until_midnight)
    print(f"[STT LIMIT] {key} 저장 완료 (자정까지 {seconds_until_midnight}초 TTL)")


# ----------------------------
# 오디오 변환
# ----------------------------
def convert_to_wav_16k_mono(input_bytes: bytes, in_ext: str) -> bytes:
    """모든 포맷을 16kHz mono WAV로 변환"""
    tmp_dir = tempfile.gettempdir()
    in_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.{in_ext}")
    out_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.wav")

    try:
        with open(in_path, "wb") as f:
            f.write(input_bytes)

        proc = subprocess.run(
            [FFMPEG_BIN, "-y", "-i", in_path, "-ac", "1", "-ar", "16000", out_path],
            capture_output=True, text=True
        )
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {proc.stderr.strip() or proc.stdout.strip()}")

        return Path(out_path).read_bytes()
    finally:
        for path in (in_path, out_path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


# ----------------------------
# STT 변환 API (JWT 없음)
# ----------------------------
@router.post("/transcribe")
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Form(..., description="사용자 UID 직접 전달"),
    diary_date: Optional[str] = Form(None),
    stt_provider: Optional[str] = Query(None),
    model_name: Optional[str] = Query(None),
    do_vad: bool = Query(False),
    low_conf_retranscribe: bool = Query(True),
    low_conf_threshold: float = Query(-1.0),
    timeout_seconds: float = Query(30.0)
):
    """
    STT 변환 (JWT 불필요)
    - UID는 프론트에서 Form으로 직접 전달
    - FastAPI → Spring: userId, text, diaryDate 전송
    """
    await check_stt_limit(user_id)

    # 파일 타입 검증
    content_type = (file.content_type or "").lower()
    allowed_types = {
        "audio/wav", "audio/x-wav", "audio/m4a", "audio/mp4",
        "audio/mpeg", "audio/ogg", "audio/webm", "application/octet-stream"
    }
    if content_type not in allowed_types:
        raise HTTPException(status_code=415, detail=f"지원하지 않는 파일 타입: {file.content_type}")

    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="업로드된 오디오가 비어있음")

        ext = (file.filename or "").split(".")[-1].lower()
        if ext not in ["wav"]:
            audio_bytes = convert_to_wav_16k_mono(audio_bytes, ext)

        audio_stream = io.BytesIO(audio_bytes)

        # STT 수행
        print(f"[STT START] user_id={user_id}, model={model_name or 'default'}, file={file.filename}")
        result = transcribe_audio(
            audio_stream,
            model_name=model_name,
            do_vad=do_vad,
            low_conf_retranscribe=low_conf_retranscribe,
            low_conf_threshold=low_conf_threshold,
            timeout_seconds=timeout_seconds,
            prefer_first=True,
            stt_provider=(stt_provider or "openai").lower(),
        )
        print(f"[STT DONE] 텍스트 길이={len(result.get('text', ''))}")

        # Spring 서버로 결과 전송
        if getattr(settings, "SEND_STT_TO_SPRING", False):
            payload = {
                "userId": user_id,
                "text": str(result.get("text", "")),
                "diaryDate": diary_date or str(date.today())
            }
            print(f"[STT→Spring] 전송 시작: {settings.SPRING_STT_URL}")
            try:
                r = requests.post(
                    settings.SPRING_STT_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=(3, 10)
                )
                print(f"[STT→Spring] 응답 코드: {r.status_code}")
                r.raise_for_status()
                print(f"[STT→Spring] 저장 완료 user_id={user_id}")
            except requests.Timeout:
                print("[STT→Spring] ❌ 요청 시간 초과")
                raise HTTPException(status_code=504, detail="[STT → Spring] 요청 시간 초과")
            except requests.RequestException as e:
                print(f"[STT→Spring] ❌ 실패: {e}")
                raise HTTPException(status_code=500, detail=f"[STT → Spring 저장 실패] {e}")

    
        return {
            "text": result.get("text", ""),
            "note": result.get("note", "") + " | DEBUG: STT 변환 및 Spring 저장 완료"
        }

    except Exception as e:
        print(f"[STT ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {e}")

    finally:
        if 'audio_stream' in locals():
            audio_stream.close()
