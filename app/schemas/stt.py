from pydantic import BaseModel

class STTRequest(BaseModel):
    # 로컬 파일 경로 혹은 base64 인코딩 스트링
    audio_path: str

class STTResponse(BaseModel):
    text: str
