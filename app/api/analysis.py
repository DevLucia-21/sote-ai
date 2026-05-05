from fastapi import APIRouter, Depends

from app.core.security import verify_internal_ai_key
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import analyze_text

router = APIRouter(
    prefix="/api/analysis",
    tags=["Analysis"],
    dependencies=[Depends(verify_internal_ai_key)],
)


@router.post("/result", response_model=AnalysisResponse)
async def analyze_result(req: AnalysisRequest):
    return analyze_text(req.text, req.year, req.user_preferred_genres)