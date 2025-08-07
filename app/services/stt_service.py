import whisper
from pathlib import Path
from app.core.config import settings

_model = None

def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(settings.WHISPER_MODEL)
    return _model

def transcribe_audio(file_path: str) -> str:
    model = get_model()
    result = model.transcribe(file_path)
    return result["text"]
