import os

from fastapi import Header, HTTPException, status


async def verify_internal_ai_key(
    x_sote_ai_key: str | None = Header(default=None),
):
    """
    Spring Boot 백엔드에서 보낸 내부 요청만 FastAPI AI 서버를 사용할 수 있게 검증한다.
    요청 헤더:
    X-SOTE-AI-KEY: <SOTE_AI_INTERNAL_KEY>
    """
    internal_key = os.getenv("SOTE_AI_INTERNAL_KEY")

    if not internal_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI internal key is not configured",
        )

    if x_sote_ai_key != internal_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid AI internal key",
        )