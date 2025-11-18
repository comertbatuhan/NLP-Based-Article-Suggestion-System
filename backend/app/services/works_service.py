from ...data.fetch import search_from_lists
from ...data.client import OpenAlexClient
from ..schemas import WorksSearchRequest, WorksSearchResponse


def run_search(payload: WorksSearchRequest, client: OpenAlexClient) -> WorksSearchResponse:
    results = search_from_lists(
        client,
        keywords=payload.keywords,
        abstracts=payload.abstracts,
        start_date=payload.start_date,
        end_date=payload.end_date,
        per_page=payload.per_page,
    )
    return WorksSearchResponse(results=list(results))