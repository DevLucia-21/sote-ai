import uuid
from fastapi import UploadFile, HTTPException
from google.cloud import vision, storage
from google.oauth2 import service_account
from app.core.config import settings
import os

# ===========================
# GCP Credentials (File 방식)
# ===========================

CREDENTIAL_PATH = "/app/config/gcp-ocr.json"

if not os.path.exists(CREDENTIAL_PATH):
    raise RuntimeError(f"GCP credential file not found: {CREDENTIAL_PATH}")

credentials = service_account.Credentials.from_service_account_file(
    CREDENTIAL_PATH
)

vision_client = vision.ImageAnnotatorClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials)

BUCKET_NAME = "sote-diary-uploads-2025"


# ----------------------------
# OCR 미리보기 실행 함수
# ----------------------------
async def run_ocr_preview(file: UploadFile):
    try:
        ext = (file.filename or "img").split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        file_bytes = await file.read()

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(file_bytes, content_type=file.content_type)

        image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        image = vision.Image(content=file_bytes)
        response = vision_client.text_detection(image=image)

        if response.error.message:
            raise Exception(response.error.message)

        annotations = response.text_annotations
        result_text = annotations[0].description.strip() if annotations else ""

        return {
            "status": "success",
            "text": result_text or "",
            "imageUrl": image_url,
            "filename": filename,
        }

    except Exception as e:
        print(f"[OCR ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR failed: {repr(e)}")


# ----------------------------
# OCR 이미지 삭제 함수
# ----------------------------
async def delete_ocr_image(filename: str):
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        if blob.exists():
            blob.delete()
            print(f"[OCR DELETE] Deleted: {filename}")
            return True
        else:
            print(f"[OCR DELETE] Not found: {filename}")
            return False

    except Exception as e:
        print(f"[OCR DELETE ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR delete failed: {repr(e)}")
