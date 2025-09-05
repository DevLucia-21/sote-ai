from pydantic import BaseModel
from datetime import date

class DiaryCreateRequest(BaseModel):
    content: str
    date: date

class DiaryResponse(BaseModel):
    id: int
    content: str
    date: date
    writeType: str
    emotionType: str | None = None
