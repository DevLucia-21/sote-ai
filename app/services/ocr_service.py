import uuid
import os
from fastapi import UploadFile, HTTPException
from google.cloud import vision, storage
from google.oauth2 import service_account

BUCKET_NAME = "sote-diary-uploads-2025"
CREDENTIAL_PATH = "/app/config/gcp-ocr.json"


# ------------------------------------------
# 1) 매 요청마다 GCP Client 생성 (정석)
# ------------------------------------------
def create_clients():
    if not os.path.exists(CREDENTIAL_PATH):
        raise RuntimeError(
            f"GCP credential file not found: {CREDENTIAL_PATH}"
        )

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIAL_PATH
    )

    vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    storage_client = storage.Client(credentials=credentials)

    return vision_client, storage_client


# ------------------------------------------
# 2) OCR 실행
# ------------------------------------------
async def run_ocr_preview(file: UploadFile):
    try:
        vision_client, storage_client = create_clients()

        # 파일명 생성
        ext = (file.filename or "img").split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        # 파일 바이트 읽기
        file_bytes = await file.read()

        # GCS 업로드
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(file_bytes, content_type=file.content_type)

        image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        # OCR 실행
        image = vision.Image(content=file_bytes)
        response = vision_client.text_detection(image=image)

        if response.error.message:
            raise RuntimeError(response.error.message)

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


# ------------------------------------------
# 3) OCR 이미지 삭제
# ------------------------------------------
async def delete_ocr_image(filename: str):
    try:
        _, storage_client = create_clients()

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        if blob.exists():
            blob.delete()
            return True
        return False

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR delete failed: {repr(e)}")
