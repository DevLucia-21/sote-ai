import httpx
import json
from app.schemas.diary import DiaryCreateRequest, DiaryResponse
from app.core.config import settings

async def save_ocr_diary(request: DiaryCreateRequest, token: str = None) -> DiaryResponse:
    payload = json.loads(request.model_dump_json())
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 🔍 로그 출력
    print(f"[DEBUG] Authorization: {headers.get('Authorization')}")
    print(f"[DEBUG] Spring OCR URL: {settings.SPRING_OCR_URL}")
    print(f"[DEBUG] Payload: {payload}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(settings.SPRING_OCR_URL, json=payload, headers=headers)
        except httpx.ConnectError:
            raise Exception("Spring 서버에 연결할 수 없습니다.")
        except httpx.ReadTimeout:
            raise Exception("Spring 서버 응답 시간이 초과되었습니다.")

    if response.status_code == 401:
        raise Exception("인증 실패: 잘못된 토큰이거나 로그인 필요")
    elif response.status_code == 403:
        raise Exception("권한 없음: 해당 사용자 접근 불가")
    elif response.status_code >= 500:
        raise Exception(f"Spring 서버 내부 오류: {response.text}")

    return DiaryResponse(**response.json())
