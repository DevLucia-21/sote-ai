# app/schemas/stt.py
from typing import Optional, List
from pydantic import BaseModel

class Segment(BaseModel):
    start: float                    # 시작(초)
    end: float                      # 종료(초)
    text: str                       # 인식 텍스트
    avg_logprob: Optional[float] = None     # 로그 확률 평균 (옵션)
    no_speech_prob: Optional[float] = None  # 무음일 확률(옵션)

# JSON 바디로 STT를 호출할 때 사용
class STTRequest(BaseModel):
    audio_path: Optional[str] = None
    audio_base64: Optional[str] = None
    model_name: Optional[str] = None
    language: Optional[str] = "auto"
    do_vad: Optional[bool] = None
    low_conf_retranscribe: Optional[bool] = None
    low_conf_threshold: Optional[float] = None
    prefer_first: Optional[bool] = None
    compute_type: Optional[str] = None

# STT 결과 응답
class STTResponse(BaseModel):
    text: str
    model_name: Optional[str] = None
    device: Optional[str] = None
    compute_type: Optional[str] = None
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    segments: Optional[List[Segment]] = None
    note: Optional[str] = None
    audio_url: Optional[str] = None
