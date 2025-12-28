# backend/app/services/works_service.py
from ...data.fetch import search_from_lists
from ...data.client import OpenAlexClient
from ..schemas import WorksSearchRequest, WorksSearchResponse, WorkSummary

SELECT_FIELDS = "id,display_name,concepts,abstract_inverted_index,publication_year,authorships"

def run_search(payload: WorksSearchRequest, client: OpenAlexClient) -> WorksSearchResponse:
    results = search_from_lists(
        client,
        keywords=payload.keywords,
        abstracts=payload.abstracts,
        start_date=payload.start_date,
        end_date=payload.end_date,
        select_fields=SELECT_FIELDS,
    )
    summaries = []
    for r in results:
        summaries.append(
            WorkSummary(
                id=r.get("id", ""),
                title=r.get("display_name", ""),
                keywords=_concepts_to_keywords(r.get("concepts", [])),
                abstract=_inverted_index_to_abstract(r.get("abstract_inverted_index")),
                publication_year=r.get("publication_year"),
                authorships=r.get("authorships", []),
            )
        )
    return WorksSearchResponse(results=summaries)

def _inverted_index_to_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""
    
    max_index = max(idx for indices in inverted_index.values() for idx in indices)
    
    words = [""] * (max_index + 1)
    
    for word, indices in inverted_index.items():
        for idx in indices:
            words[idx] = word
            
    return " ".join(words)

def _concepts_to_keywords(concepts: list) -> str:
    if not concepts:
        return ""
    
    return ", ".join([c['display_name'] for c in concepts if 'display_name' in c])
