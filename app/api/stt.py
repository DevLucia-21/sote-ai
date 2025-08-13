from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Query
from app.services.stt_service import transcribe_audio
from app.schemas.stt import STTResponse
import tempfile
from pathlib import Path
from app.core.config import settings
from typing import Optional
import shutil

router = APIRouter(prefix="/ai/stt", tags=["stt"])

@router.post("/transcribe", response_model=STTResponse)
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    model_name: Optional[str] = Query(None, description="강제 모델 이름"),
    do_vad: bool = Query(False, description="간단 무음 제거 수행 여부"),
    low_conf_retranscribe: bool = Query(True, description="base 결과 저신뢰 구간만 재추론"),
    low_conf_threshold: float = Query(-1.0, description="저신뢰 임계값(avg_logprob)"),
    timeout_seconds: float = Query(30.0, description="prefer 모델 시도 타임아웃(초)"),
):
    """
    파일 업로드 -> 서버 전사
    모바일(DEPLOY_TARGET=mobile 또는 헤더 x-client-platform: mobile):
      - base-first (prefer_first=False) + 저신뢰 재추론
    데스크톱/서버:
      - small-first (prefer_first=True) -> 실패 시 base
    """
    # 0) 간단한 MIME 검사 (audio/* 만 허용)
    if not (file.content_type and file.content_type.startswith("audio/")):
        raise HTTPException(status_code=415, detail=f"지원하지 않는 파일 타입: {file.content_type or 'unknown'}")

    # 1) 임시 파일로 스트리밍 저장 (대용량 대비)
    suffix = Path(file.filename or "").suffix or ".bin"
    try:
        with tempfile.NamedTemporaryFile(prefix="stt_", suffix=suffix, delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # 업로드 스트림을 청크 단위로 저장
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                tmp.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {e}")

    # 2) 모바일 감지 -> 실행 정책 결정
    header_platform = (request.headers.get("x-client-platform") or "").lower()
    is_mobile_client = str(getattr(settings, "DEPLOY_TARGET", "")).lower() == "mobile" or header_platform == "mobile"

    effective_model = model_name
    prefer_first_flag = True
    if is_mobile_client:
        effective_model = "base"      # 모바일: base-first
        prefer_first_flag = False

    try:
        text = transcribe_audio(
            str(tmp_path),
            model_name=effective_model,
            do_vad=do_vad,
            low_conf_retranscribe=low_conf_retranscribe,
            low_conf_threshold=low_conf_threshold,
            timeout_seconds=timeout_seconds,
            prefer_first=prefer_first_flag,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {e}")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    return STTResponse(text=text)
