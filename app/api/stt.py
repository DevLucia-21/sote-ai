# app/api/stt.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Request
from app.services.stt_service import transcribe_audio
from app.schemas.stt import STTResponse
from app.core.config import settings
from typing import Optional
import requests
import io
import os
import tempfile
import uuid
import subprocess
import json

router = APIRouter(prefix="/ai/stt", tags=["stt"])

# Spring Boot API URL (환경에 맞게 수정)
SPRING_BOOT_URL = "http://localhost:8080/api/stt/results"

def convert_m4a_to_wav(input_bytes: bytes) -> bytes:
    tmp_input = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.m4a")
    tmp_output = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.wav")
    with open(tmp_input, "wb") as f:
        f.write(input_bytes)
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_input, "-ac", "1", "-ar", "16000", tmp_output],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
    with open(tmp_output, "rb") as f:
        wav_bytes = f.read()
    os.remove(tmp_input)
    os.remove(tmp_output)
    return wav_bytes

@router.post("/transcribe", response_model=STTResponse)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    stt_provider: Optional[str] = Query(None, description="whisper 또는 openai"),
    model_name: Optional[str] = Query(None),
    do_vad: bool = Query(False),
    low_conf_retranscribe: bool = Query(True),
    low_conf_threshold: float = Query(-1.0),
    timeout_seconds: float = Query(30.0),
):
    # 오디오 파일 MIME 타입 확인
    if not (file.content_type and file.content_type.startswith("audio/")):
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일 타입: {file.content_type or 'unknown'}"
        )
    
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="업로드된 오디오가 비어있음")

        if file.filename and file.filename.lower().endswith(".m4a"):
            audio_bytes = convert_m4a_to_wav(audio_bytes)

        audio_stream = io.BytesIO(audio_bytes)

        result = transcribe_audio(
            audio_stream,
            model_name=model_name,
            do_vad=do_vad,
            low_conf_retranscribe=low_conf_retranscribe,
            low_conf_threshold=low_conf_threshold,
            timeout_seconds=timeout_seconds,
            prefer_first=True,
            stt_provider=stt_provider
        )
        
        # note 메시지 모음
        notes = []

        # VAD 사용 여부 기록
        if do_vad:
            notes.append("무음 구간 제거 활성화")

        final_model = result.get("model_name") or model_name or "unknown"
        re_model = result.get("retranscribe_model")

        if not model_name:
            notes.append(f"모델 자동 선택: {final_model}")
        elif final_model != model_name:
            notes.append(f"모델 변경: {model_name} → {final_model}")
        else:
            notes.append(f"모델: {final_model}")

        if low_conf_retranscribe:
            if re_model:
                notes.append(f"저신뢰 구간 재추론 (모델: {re_model}, threshold={low_conf_threshold})")
            else:
                notes.append(f"저신뢰 구간 재추론 활성화 (threshold={low_conf_threshold})")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {e}")
    
    finally:
        # 메모리 해제
        if 'audio_stream' in locals():
            audio_stream.close()
        if 'audio_bytes' in locals():
            del audio_bytes
        if 'audio_stream' in locals():
            del audio_stream

    # note 최종 문자열 합치기
    result["note"] = "; ".join(notes) if notes else None

    # 2) Spring Boot로 text 전송
    try:
        # FastAPI 요청 헤더에서 JWT 추출
        auth_header = request.headers.get("Authorization")
        
        payload = {
            "text": str(result.get("text", ""))
        }
        headers = {}
        if auth_header:  # JWT가 있으면 그대로 붙여줌
            headers["Authorization"] = auth_header
            headers["Content-Type"] = "application/json"

        res = requests.post(SPRING_BOOT_URL, data=json.dumps(payload, ensure_ascii=False), headers=headers, timeout=5)
        res.raise_for_status()
    except requests.RequestException as e:
        print(f"[STT → Spring Boot 전송 실패] {e}")

    return STTResponse(**result)
