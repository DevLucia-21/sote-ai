import uuid
from fastapi import UploadFile, HTTPException
from google.cloud import vision, storage
from google.oauth2 import service_account
from app.core.config import settings

# ----------------------------
# GCP 인증
# ----------------------------
credentials = service_account.Credentials.from_service_account_file(
    settings.GOOGLE_APPLICATION_CREDENTIALS
)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials)

BUCKET_NAME = "sote-diary-uploads-2025"


# ----------------------------
# OCR 미리보기 실행 함수
# ----------------------------
async def run_ocr_preview(file: UploadFile):
    """
    1) 이미지를 GCS에 업로드 (공개 URL 생성)
    2) Google Vision OCR 수행
    3) 결과 반환 (Spring 저장 X)
    """
    try:
        # 파일명 생성
        ext = (file.filename or "img").split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        # GCS 업로드
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_file(file.file, content_type=file.content_type)

        # ✅ 업로드한 객체만 공개 처리
        blob.make_public()
        image_url = blob.public_url

        # OCR 수행
        content = blob.download_as_bytes()
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)

        if response.error.message:
            raise Exception(response.error.message)

        annotations = response.text_annotations
        result_text = annotations[0].description.strip() if annotations else ""

        # 결과 반환
        return {
            "status": "success",
            "text": result_text or "",
            "imageUrl": image_url,
            "filename": filename,  # ✅ 삭제용
        }

    except Exception as e:
        print(f"[OCR ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR failed: {repr(e)}")


# ----------------------------
# OCR 이미지 삭제 함수
# ----------------------------
async def delete_ocr_image(filename: str):
    """일기 삭제 시 GCS 이미지 삭제"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        if blob.exists():
            blob.delete()
            print(f"[OCR DELETE] {filename} deleted from GCS.")
            return True
        else:
            print(f"[OCR DELETE] {filename} not found in GCS.")
            return False

    except Exception as e:
        print(f"[OCR DELETE ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"OCR image delete failed: {repr(e)}")
