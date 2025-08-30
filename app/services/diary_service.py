import httpx
import json
from app.schemas.diary import DiaryCreateRequest, DiaryResponse

SPRING_API_URL = "http://localhost:8080/api/diaries/ocr"

async def save_diary(request: DiaryCreateRequest, token: str = None) -> DiaryResponse:
    payload = json.loads(request.model_dump_json())

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(SPRING_API_URL, json=payload, headers=headers)
        except httpx.ConnectError:
            raise Exception("Spring 서버에 연결할 수 없습니다. (연결 실패)")
        except httpx.ReadTimeout:
            raise Exception("Spring 서버 응답 시간이 초과되었습니다.")

    if response.status_code == 401:
        raise Exception("인증 실패: 잘못된 토큰이거나 로그인 필요")
    elif response.status_code == 403:
        raise Exception("권한 없음: 해당 사용자로 접근 불가")
    elif response.status_code >= 500:
        raise Exception(f"Spring 서버 내부 오류: {response.text}")

    return DiaryResponse(**response.json())
