import uuid
from fastapi import UploadFile, HTTPException
from google.cloud import vision, storage
from google.oauth2 import service_account
import httpx
from app.core.config import settings

# GCP 인증
credentials = service_account.Credentials.from_service_account_file(
    settings.GOOGLE_APPLICATION_CREDENTIALS
)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials)

# GCS 버킷 & Spring Boot 서버
BUCKET_NAME = "sote-diary-uploads-2025"
SPRING_SERVER_URL = settings.SPRING_SERVER_URL


# OCR + 업로드 + Spring Boot 저장
async def run_ocr_preview(file: UploadFile, diary_date: str, token: str):
    try:
        # 파일명 생성
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        # GCS 업로드
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_file(file.file, content_type=file.content_type)
        image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        # Vision OCR 실행
        content = blob.download_as_bytes()
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)
        annotations = response.text_annotations
        text = annotations[0].description.strip() if annotations else ""

        # OCR 결과 Spring Boot 저장 (사용자 JWT 그대로 전달)
        headers = {"Authorization": f"Bearer {token}"}
        ocr_payload = {
            "imageUrl": image_url,
            "text": text,
            "diaryDate": diary_date
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{SPRING_SERVER_URL}/api/ocr/results",
                json=ocr_payload,
                headers=headers
            )

        if res.status_code != 200:
            raise HTTPException(
                status_code=res.status_code,
                detail=f"OCR 저장 실패: {res.text}"
            )

        return {
            "message": "OCR success",
            "text": text,
            "imageUrl": image_url,
            "diaryDate": diary_date
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {repr(e)}")
