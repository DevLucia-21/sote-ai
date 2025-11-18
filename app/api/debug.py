from fastapi import APIRouter
import os

router = APIRouter(prefix="/debug")

@router.get("/gcp")
def check():
    path = "/app/config/gcp-ocr.json"
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    return {
        "exists": exists,
        "size": size,
    }
