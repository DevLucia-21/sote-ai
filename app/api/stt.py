# app/api/stt.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.stt_service import transcribe_audio
from app.schemas.stt import STTResponse
import tempfile
from pathlib import Path

router = APIRouter(prefix="/ai/stt", tags=["stt"])

@router.post("/transcribe", response_model=STTResponse)
async def transcribe(file: UploadFile = File(...)):
    # 1) 플랫폼 독립 임시경로 결정
    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / file.filename

    # 2) 파일 저장
    try:
        content = await file.read()
        tmp_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 실패: {e}")

    # 3) Whisper 변환
    try:
        text = transcribe_audio(str(tmp_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {e}")

    # (선택) 4) 저장한 임시파일 삭제
    try:
        tmp_path.unlink()
    except:
        pass

    return STTResponse(text=text)
