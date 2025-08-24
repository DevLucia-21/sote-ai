# app/schemas/analysis.py

from typing import Optional, List
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    text: str
    user_preferred_genres: Optional[List[str]] = None

class EmotionResult(BaseModel):
    label: str
    score: float
    reason: str

class MusicTrack(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    genre: Optional[str] = None
    tempo: Optional[str] = None
    mood: Optional[str] = None
    track_summary: Optional[str] = None
    reason: Optional[str] = None

class AnalysisResponse(BaseModel):
    emotion: EmotionResult
    # 서버가 'music_candidates'로 내려줘도 'music'로 검증 통과
    music: List[MusicTrack] = Field(..., validation_alias="music_candidates")
    # 선택: 대표 추천 1곡을 추가로 제공하고 싶다면
    top_track: Optional[MusicTrack] = None
