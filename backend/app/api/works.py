#backend/app/api/works.py
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import WorksSearchRequest, WorksSearchResponse
from ..services.works_service import run_search
from ...data.client import OpenAlexClient, OpenAlexError

router = APIRouter()

def get_client():
    return OpenAlexClient()

@router.post("/search", response_model=WorksSearchResponse)
def search_works(payload: WorksSearchRequest, client: OpenAlexClient = Depends(get_client)):
    try:
        return run_search(payload, client)
    except OpenAlexError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
