# app/schemas/stt.py

from typing import Optional
from pydantic import BaseModel

# 단일 세그먼트(구간) 정보
class Segment(BaseModel):
    start: float                    # 시작(초)
    end: float                      # 종료(초)
    text: str                       # 인식 텍스트
    avg_logprob: Optional[float] = None     # 로그 확률 평균 (옵션)
    no_speech_prob: Optional[float] = None  # 무음일 확률(옵션)

# JSON 바디로 STT를 호출할 때 사용 (멀티파트 업로드면 생략 가능)
class STTRequest(BaseModel):
    audio_path: Optional[str] = None         # 서버 경로 사용 시(허용 시 반드시 검증)
    audio_base64: Optional[str] = None       # base64 인코딩 오디오
    model_name: Optional[str] = None         # "base", "small" 등
    language: Optional[str] = "auto"         # 언어 힌트 (None이면 자동)
    do_vad: Optional[bool] = None            # 무음 제거 사용 여부
    low_conf_retranscribe: Optional[bool] = None      # 저신뢰 구간 재추론
    low_conf_threshold: Optional[float] = None         # avg_logprob 임계값
    prefer_first: Optional[bool] = None      # True: small-first, False: primary-first
    compute_type: Optional[str] = None       # "int8" 등(설정값 오버라이드용, 선택)
    user_id: Optional[int] = None    # 변경: UID 추가
    spring_id: Optional[int] = None  


# STT 결과 응답
class STTResponse(BaseModel):
    text: str
    model_name: Optional[str] = None   # 사용된 모델명 (선택 노출)
    note: Optional[str] = None         # 추가 메시지/디버그
    user_id: Optional[int] = None      # 요청한 UID (에코백)
    spring_id: Optional[int] = None    # Spring STT 전용 테이블 PK (저장 시에만 포함)
