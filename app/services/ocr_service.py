import base64
import json
import os
import uuid

from fastapi import HTTPException, UploadFile
from google.cloud import storage, vision
from google.oauth2 import service_account


BUCKET_NAME = os.getenv("GCP_OCR_BUCKET", "sote-diary-uploads-2025")


# ------------------------------------------
# 1) GCP Credentials 로딩
# ------------------------------------------
def load_google_credentials():
    """
    Render:
    - GCP_OCR_JSON_BASE64 환경변수 사용

    Local:
    - GOOGLE_APPLICATION_CREDENTIALS 파일 경로 사용
    """
    encoded = os.getenv("GCP_OCR_JSON_BASE64")

    if encoded:
        try:
            info = json.loads(base64.b64decode(encoded).decode("utf-8"))
            return service_account.Credentials.from_service_account_info(info)
        except Exception as e:
            raise RuntimeError(f"GCP_OCR_JSON_BASE64 로딩 실패: {repr(e)}")

    credential_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if credential_path:
        if not os.path.exists(credential_path):
            raise RuntimeError(f"GCP credential file not found: {credential_path}")

        return service_account.Credentials.from_service_account_file(
            credential_path
        )

    raise RuntimeError(
        "GCP_OCR_JSON_BASE64 또는 GOOGLE_APPLICATION_CREDENTIALS 환경변수가 필요합니다."
    )


# ------------------------------------------
# 2) 매 요청마다 GCP Client 생성
# ------------------------------------------
def create_clients():
    credentials = load_google_credentials()

    vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    storage_client = storage.Client(
        credentials=credentials,
        project=credentials.project_id,
    )

    return vision_client, storage_client


# ------------------------------------------
# 3) OCR 실행
# ------------------------------------------
async def run_ocr_preview(file: UploadFile):
    try:
        vision_client, storage_client = create_clients()

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
# 4) OCR 이미지 삭제
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