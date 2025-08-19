# app/schemas/analysis.py

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AnalysisRequest(BaseModel):
    text: str
    user_preferred_genres: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    emotion: Dict[str, Any]
    music: Dict[str, Any]
