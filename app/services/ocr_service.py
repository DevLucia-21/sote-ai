# app/service/ocr_service.py
import uuid
from fastapi import UploadFile, HTTPException
from google.cloud import vision, storage
from google.oauth2 import service_account
from app.core.config import settings

# GCP 인증
credentials = service_account.Credentials.from_service_account_file(
    settings.GOOGLE_APPLICATION_CREDENTIALS
)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials)

# GCS 버킷 (필요 시 .env에서 관리)
BUCKET_NAME = "sote-diary-uploads-2025"

async def run_ocr_preview(file: UploadFile):
    """
    1) 이미지를 GCS에 업로드
    2) Google Vision OCR 수행
    3) 결과를 '미리보기'로만 반환 (Spring 저장은 하지 않음)
    """
    try:
        # 파일명 생성
        ext = (file.filename or "img").split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        # 1) GCS 업로드
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_file(file.file, content_type=file.content_type)
        image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        # 2) Vision OCR
        content = blob.download_as_bytes()
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)
        annotations = response.text_annotations
        text = annotations[0].description.strip() if annotations else ""

        # 3) 저장하지 않고 그대로 반환
        return {
            "message": "OCR preview generated",
            "content": text,          
            "imageUrl": image_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {repr(e)}")


