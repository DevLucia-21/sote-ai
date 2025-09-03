import uuid
from fastapi import UploadFile, HTTPException
from google.cloud import vision, storage
from google.oauth2 import service_account
from app.core.config import settings
import requests, json

# GCP 인증
credentials = service_account.Credentials.from_service_account_file(
    settings.GOOGLE_APPLICATION_CREDENTIALS
)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials)

BUCKET_NAME = "sote-diary-uploads-2025"

async def run_ocr_preview(file: UploadFile, diary_date: str, auth_header: str = None):
    try:
        ext = (file.filename or "img").split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_file(file.file, content_type=file.content_type)
        image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        content = blob.download_as_bytes()
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)
        annotations = response.text_annotations
        text = annotations[0].description.strip() if annotations else ""

        result = {
            "message": "OCR preview generated",
            "text": text,
            "imageUrl": image_url,
            "diaryDate": diary_date
        }

        # ✅ Spring 저장 (옵션)
        if getattr(settings, "SEND_OCR_TO_SPRING", False):
            headers = {"Content-Type": "application/json"}
            if auth_header:
                headers["Authorization"] = auth_header

            payload = {
                "content": text,
                "imageUrl": image_url,
                "date": diary_date
            }

            # 🔍 로그 출력
            print(f"[DEBUG] Authorization: {headers.get('Authorization')}")
            print(f"[DEBUG] Spring OCR 저장 URL: {settings.SPRING_OCR_URL}")
            print(f"[DEBUG] Spring OCR payload: {payload}")

            try:
                requests.post(
                    settings.SPRING_OCR_URL,
                    data=json.dumps(payload, ensure_ascii=False),
                    headers=headers,
                    timeout=5
                ).raise_for_status()
            except requests.RequestException as e:
                print(f"[OCR → Spring 저장 실패] {e}")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {repr(e)}")
