# app/schemas/ocr_request.py
from pydantic import BaseModel

class OcrRequest(BaseModel):
    imageUrl: str
    diary_date: str
