#backend/app/api/works.py
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import WorksSearchRequest, WorksSearchResponse
from ..services.works_service import run_search
from ..services.semantic_rerank_service import rerank_works_by_query_sentence_transformer, rerank_works_by_query_cross_encoder
from ...data.client import OpenAlexClient, OpenAlexError

router = APIRouter()

def get_client():
    return OpenAlexClient()

@router.post("/search", response_model=WorksSearchResponse)
def search_works(payload: WorksSearchRequest, client: OpenAlexClient = Depends(get_client)):
    try:
        response = run_search(payload, client, discovery_mode = False)
        results = response.results
        if len(results)>20:
            return WorksSearchResponse(results=results[:20])
        else:
            return response
    except OpenAlexError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@router.post("/rerank_search_sentence_transformer", response_model=WorksSearchResponse)
def search_and_rerank(payload: WorksSearchRequest, client: OpenAlexClient = Depends(get_client)):
    try:
        response = run_search(payload, client)
        return rerank_works_by_query_sentence_transformer(searchRequest=payload, workList=response)
    except OpenAlexError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    
@router.post("/rerank_search_cross_encoder", response_model=WorksSearchResponse)
def search_and_rerank(payload: WorksSearchRequest, client: OpenAlexClient = Depends(get_client)):
    try:
        response = run_search(payload, client)
        return rerank_works_by_query_cross_encoder(searchRequest=payload, workList=response)
    except OpenAlexError as exc:
        raise HTTPException(status_code=502, detail=str(exc))