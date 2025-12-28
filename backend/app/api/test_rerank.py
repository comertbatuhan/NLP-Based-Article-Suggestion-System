# backend/app/api/test_rerank.py
from fastapi import APIRouter
from pydantic import BaseModel

from ..schemas import WorksSearchRequest, WorksSearchResponse
from ..services.semantic_rerank_service import (
    rerank_works_by_query_sentence_transformer,
    rerank_works_by_query_cross_encoder,
)

router = APIRouter(prefix="/__test__", tags=["__test__"])

class RerankOnlyPayload(BaseModel):
    query: WorksSearchRequest
    works: WorksSearchResponse


@router.post("/rerank_only_sentence_transformer", response_model=WorksSearchResponse)
def rerank_only_sentence_transformer(payload: RerankOnlyPayload):
    return rerank_works_by_query_sentence_transformer(
        searchRequest=payload.query,
        workList=payload.works,
    )


@router.post("/rerank_only_cross_encoder", response_model=WorksSearchResponse)
def rerank_only_cross_encoder(payload: RerankOnlyPayload):
    return rerank_works_by_query_cross_encoder(
        searchRequest=payload.query,
        workList=payload.works,
    )