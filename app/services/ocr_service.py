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
    1) 이미지를 GCS에 업로드 (Uniform Access 정책 호환)
    2) Google Vision OCR 수행 (로컬 메모리 기반)
    3) 결과 반환 (Spring 저장 X)
    """
    try:
        # 파일명 생성
        ext = (file.filename or "img").split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        # 파일을 메모리에 먼저 로드 (ACL 충돌 방지)
        file_bytes = await file.read()

        # GCS 업로드 (Uniform access에서도 정상 작동)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(file_bytes, content_type=file.content_type)

        # 공개 URL 직접 구성 (blob.make_public() 호출 X)
        image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        # Vision API는 업로드된 파일 대신 메모리 데이터를 사용
        image = vision.Image(content=file_bytes)
        response = vision_client.text_detection(image=image)

        # Vision API 오류 처리
        if response.error.message:
            raise Exception(response.error.message)

        # OCR 결과 텍스트 추출
        annotations = response.text_annotations
        result_text = annotations[0].description.strip() if annotations else ""

        # 결과 반환
        return {
            "status": "success",
            "text": result_text or "",
            "imageUrl": image_url,
            "filename": filename,  # 삭제용으로 전달
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
