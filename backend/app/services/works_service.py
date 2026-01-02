# backend/app/services/works_service.py
from ...data.fetch import search_from_lists
from ...data.client import OpenAlexClient
from ..schemas import WorksSearchRequest, WorksSearchResponse, WorkSummary
from functools import lru_cache
from ..cache import get_cache_dir
from keybert import KeyBERT
from typing import List
from .semantic_rerank_service import get_sentence_transformer

SELECT_FIELDS = "id,display_name,concepts,abstract_inverted_index,publication_year,authorships"

def extract_keywords_from_text(text: str, top_n: int = 5) -> List[str]:
    kw_model = KeyBERT(model=get_sentence_transformer())
    keywords = kw_model.extract_keywords(text, top_n=top_n)
    return [k[0] for k in keywords]

def run_search(payload: WorksSearchRequest, client: OpenAlexClient, discovery_mode: bool = True) -> WorksSearchResponse:
    
    abstract_keywords = []
    if discovery_mode:
        if payload.abstracts:
            for abstract_text in payload.abstracts:
                extracted = extract_keywords_from_text(abstract_text)
                print(f"\nKeywords extracted via KeyBERT: {extracted}\n")
                abstract_keywords.extend(extracted)
        results = search_from_lists(
            client,
            keywords=payload.keywords,
            abstracts=abstract_keywords,
            start_date=payload.start_date,
            end_date=payload.end_date,
            select_fields=SELECT_FIELDS,
        )
    else:
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
