from fastapi import APIRouter, Depends, HTTPException

from app.agent.agent_service import AgentService
from app.api.dependencies import get_agent_service
from app.api.dependencies import get_chroma_retriever
from app.rag.retriever import ChromaRetriever
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, FieldAnalysisRequest, FieldAnalysisResponse
from app.schemas.rag import RagRetrieveRequest, RagRetrieveResponse, RagVerifyResponse


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


@router.post("/api/v1/analyze/field", response_model=FieldAnalysisResponse)
async def analyze_field(
    request: FieldAnalysisRequest,
    service: AgentService = Depends(get_agent_service),
) -> FieldAnalysisResponse:
    try:
        return await service.analyze_field(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/v1/rag/verify", response_model=RagVerifyResponse)
async def verify_rag(
    field: str | None = None,
    limit: int = 10,
    retriever: ChromaRetriever = Depends(get_chroma_retriever),
) -> RagVerifyResponse:
    result = retriever.verify(limit=limit, field=field)
    return RagVerifyResponse(**result)


@router.post("/api/v1/rag/retrieve", response_model=RagRetrieveResponse)
async def retrieve_rag(
    request: RagRetrieveRequest,
    retriever: ChromaRetriever = Depends(get_chroma_retriever),
) -> RagRetrieveResponse:
    results = await retriever.retrieve(query=request.query, top_k=request.top_k, field=request.field)
    return RagRetrieveResponse(
        query=request.query,
        results=[
            {
                "chunk_id": item.chunk_id,
                "source": item.source,
                "distance": item.distance,
                "metadata": item.metadata,
                "content": item.content,
            }
            for item in results
        ],
    )
