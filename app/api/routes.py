from fastapi import APIRouter, Depends

from app.agent.agent_service import AgentService
from app.api.dependencies import get_agent_service
from app.schemas.analysis import AnalysisRequest, AnalysisResponse


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_stock(
    request: AnalysisRequest,
    service: AgentService = Depends(get_agent_service),
) -> AnalysisResponse:
    return await service.analyze(request)
