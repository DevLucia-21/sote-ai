# app/api/stt.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Query
from app.services.stt_service import transcribe_audio
from app.schemas.stt import STTResponse
import tempfile
from pathlib import Path
from app.core.config import settings
from typing import Optional

router = APIRouter(prefix="/ai/stt", tags=["stt"])

@router.post("/transcribe", response_model=STTResponse)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    model_name: Optional[str] = Query(None),
    do_vad: bool = Query(False),
    low_conf_retranscribe: bool = Query(True),
    low_conf_threshold: float = Query(-1.0),
    timeout_seconds: float = Query(30.0),
):
    if not (file.content_type and file.content_type.startswith("audio/")):
        raise HTTPException(status_code=415, detail=f"지원하지 않는 파일 타입: {file.content_type or 'unknown'}")

    suffix = Path(file.filename or "").suffix or ".bin"
    try:
        with tempfile.NamedTemporaryFile(prefix="stt_", suffix=suffix, delete=False) as tmp:
            tmp_path = Path(tmp.name)
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {e}")

    # note 메시지 모음
    notes = []

    # 모바일 환경 감지
    header_platform = (request.headers.get("x-client-platform") or "").lower()
    is_mobile_client = str(getattr(settings, "DEPLOY_TARGET", "")).lower() == "mobile" or header_platform == "mobile"

    effective_model = model_name
    prefer_first_flag = True

    # VAD 사용 여부 기록
    if do_vad:
        notes.append("무음 구간 제거 활성화")

    try:
        result = transcribe_audio(
            str(tmp_path),
            model_name=effective_model,
            do_vad=do_vad,
            low_conf_retranscribe=low_conf_retranscribe,
            low_conf_threshold=low_conf_threshold,
            timeout_seconds=timeout_seconds,
            prefer_first=prefer_first_flag,
        )

        # 최종 모델명 가져오기 (result 안에 있다고 가정)
        final_model = result.get("model_name") or effective_model or "unknown"
        re_model = result.get("retranscribe_model")

        # 모델명 기록
        if not model_name:  # 요청에서 안 넘긴 경우
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
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    # note 최종 문자열 합치기
    note_text = "; ".join(notes) if notes else None

    result["note"] = note_text
    return STTResponse(**result)
