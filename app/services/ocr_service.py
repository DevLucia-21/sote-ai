import uuid
from fastapi import UploadFile, HTTPException
from google.cloud import vision, storage
from google.oauth2 import service_account
import os

BUCKET_NAME = "sote-diary-uploads-2025"
CREDENTIAL_PATH = "/app/config/gcp-ocr.json"


# ------------------------------------------
# GCP 클라이언트 지연 초기화 (lazy initialization)
#    → 파일 생성 후에만 로딩하도록 변경
# ------------------------------------------
_vision_client = None
_storage_client = None


def get_clients():
    global _vision_client, _storage_client

    if _vision_client and _storage_client:
        return _vision_client, _storage_client

    if not os.path.exists(CREDENTIAL_PATH):
        raise RuntimeError(
            f"GCP credential file not found (loaded too early): {CREDENTIAL_PATH}"
        )

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIAL_PATH
    )

    _vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    _storage_client = storage.Client(credentials=credentials)

    return _vision_client, _storage_client


# ----------------------------
# OCR 실행
# ----------------------------
async def run_ocr_preview(file: UploadFile):
    try:
        vision_client, storage_client = get_clients()

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
        raise HTTPException(status_code=500, detail=f"OCR failed: {repr(e)}")


# ----------------------------
# OCR 이미지 삭제
# ----------------------------
async def delete_ocr_image(filename: str):
    try:
        _, storage_client = get_clients()

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        if blob.exists():
            blob.delete()
            return True
        else:
            return False

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR delete failed: {repr(e)}")
