# app/schemas/analysis.py

from typing import Optional, List
from pydantic import BaseModel, Field

# 요청 DTO
class AnalysisRequest(BaseModel):
    text: str
    year: int                                      # 출생연도 추가
    user_preferred_genres: Optional[List[str]] = None  # 대분류 장르 리스트 (예: ["pop", "jazz"])

# 감정 결과
class EmotionResult(BaseModel):
    label: str                                     # 감정 라벨 (기쁨/슬픔/화남/무기력/예민)
    score: float                                   # 감정 점수 (0.0 ~ 1.0)
    reason: str                                    # 구어체 설명 (~했구나 / ~인 것 같아)

# 추천 음악 트랙
class MusicTrack(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    genre: Optional[str] = None                    # 항상 "대분류/소분류" 형식
    tempo: Optional[str] = None                    # "느림/중간/빠름 + BPM"
    mood: Optional[str] = None
    track_summary: Optional[str] = None
    reason: Optional[str] = None                   # 일기와 연결 이유 (접두사 금지)

# 응답 DTO
class AnalysisResponse(BaseModel):
    emotion: EmotionResult
    # 서버가 'music_candidates'로 내려줘도 'music'으로 매핑 가능
    music: List[MusicTrack] = Field(..., validation_alias="music_candidates")
    # 대표 추천 1곡 (선택)
    top_track: Optional[MusicTrack] = None
