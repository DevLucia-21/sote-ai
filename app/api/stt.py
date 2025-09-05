from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Request
from app.services.stt_service import transcribe_audio
from app.schemas.stt import STTResponse
from app.core.config import settings
from typing import Optional
import io
import os
import shutil
import tempfile
import uuid
import subprocess
from pathlib import Path
from datetime import date
import requests
import json

router = APIRouter(prefix="/ai/stt", tags=["stt"])

# ffmpeg 경로 설정 (.env > PATH > fallback)
FFMPEG_BIN = settings.FFMPEG_BIN or shutil.which("ffmpeg") or "ffmpeg"


def convert_to_wav_16k_mono(input_bytes: bytes, in_ext: str) -> bytes:
    """모든 포맷을 16kHz mono WAV로 변환"""
    tmp_dir = tempfile.gettempdir()
    in_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.{(in_ext or 'bin').lower()}")
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

        wav_bytes = Path(out_path).read_bytes()
        return wav_bytes
    finally:
        try: os.remove(in_path)
        except FileNotFoundError: pass
        try: os.remove(out_path)
        except FileNotFoundError: pass


@router.post("/transcribe", response_model=STTResponse)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),   # 반드시 form-data → file 로 업로드
    diary_date: Optional[str] = Form(None),
    stt_provider: Optional[str] = Query(None, description="whisper 또는 openai"),
    model_name: Optional[str] = Query(None),
    do_vad: bool = Query(False),
    low_conf_retranscribe: bool = Query(True),
    low_conf_threshold: float = Query(-1.0),
    timeout_seconds: float = Query(30.0),
):
    """
    STT 변환 (파일 업로드 필수)
    FastAPI → STT 변환 → Spring /stt/results 저장
    Diary 저장은 자동으로 하지 않음 (사용자 수정 후 별도 호출)
    """
    content_type = (file.content_type or "").lower()
    allowed_types = {
        "audio/wav", "audio/x-wav", "audio/m4a", "audio/mp4",
        "audio/mpeg", "audio/ogg", "application/octet-stream"
    }
    if content_type not in allowed_types:
        raise HTTPException(status_code=415, detail=f"지원하지 않는 파일 타입: {file.content_type or 'unknown'}")

    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="업로드된 오디오가 비어있음")

        ext = (file.filename or "").split(".")[-1].lower()
        is_wav_ct = content_type in {"audio/wav", "audio/x-wav", "audio/wave"}
        is_wav_ext = ext == "wav"
        need_convert = not (is_wav_ct or is_wav_ext)

        if need_convert:
            audio_bytes = convert_to_wav_16k_mono(audio_bytes, ext or "bin")

        audio_stream = io.BytesIO(audio_bytes)

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

        # Spring /stt/results 저장
        if getattr(settings, "SEND_STT_TO_SPRING", False):
            auth_header = request.headers.get("Authorization")
            headers = {"Content-Type": "application/json"}
            if auth_header:
                headers["Authorization"] = auth_header
            try:
                payload = {
                    "text": str(result.get("text", "")),
                    "diaryDate": diary_date or str(date.today())
                }
                requests.post(
                    settings.SPRING_STT_URL,
                    data=json.dumps(payload, ensure_ascii=False),
                    headers=headers,
                    timeout=5
                ).raise_for_status()
            except requests.RequestException as e:
                print(f"[STT → Spring 저장 실패] {e}")

        result["note"] = result.get("note", "") + " | DEBUG: STT 변환 및 Spring 저장 완료"

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {e}")
    finally:
        if 'audio_stream' in locals():
            audio_stream.close()

    return result
