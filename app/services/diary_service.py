import httpx
import json
from app.schemas.diary import DiaryCreateRequest, DiaryResponse
from app.core.config import settings

async def save_ocr_diary(request: DiaryCreateRequest, token: str = None) -> DiaryResponse:
    payload = json.loads(request.model_dump_json())
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(settings.SPRING_OCR_URL, json=payload, headers=headers)
        except httpx.ConnectError:
            raise Exception("Spring 서버 연결 실패")
        except httpx.ReadTimeout:
            raise Exception("Spring 서버 응답 지연")

    if response.status_code == 401:
        raise Exception("인증 실패")
    elif response.status_code == 403:
        raise Exception("권한 없음")
    elif response.status_code >= 500:
        raise Exception(f"Spring 오류: {response.text}")

    return DiaryResponse(**response.json())
