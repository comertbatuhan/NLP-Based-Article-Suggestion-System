# backend/app/services/works_service.py
from ...data.fetch import search_from_lists
from ...data.client import OpenAlexClient
from ..schemas import WorksSearchRequest, WorksSearchResponse, WorkSummary
from functools import lru_cache
from keybert import KeyBERT
from typing import List, Set
from .semantic_rerank_service import get_sentence_transformer
from ..cache import get_model_cache_dir


SELECT_FIELDS = "id,display_name,concepts,abstract_inverted_index,publication_year,authorships"

# ----------- helpers --------------------
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

@lru_cache(maxsize=1)
def get_keybert_model():
    """
    KeyBERT caches the model.
    This prevents the model from being reloaded in each abstract cycle (saving RAM and CPU).
    """
    return KeyBERT(model=get_sentence_transformer())

def extract_keywords_from_text(text: str, top_n: int = 8) -> List[str]:
    kw_model = get_keybert_model()
    keywords = kw_model.extract_keywords(text, top_n=top_n)
    return [k[0] for k in keywords]


# --------------------- openalex search function ----------------------------
def run_search(payload: WorksSearchRequest, client: OpenAlexClient, discovery_mode: bool = True) -> WorksSearchResponse:
    
    # Protection: if keywords are too much, take the first 6 because it increases exponentially in the search logic
    keywords_to_use = payload.keywords
    if keywords_to_use and len(keywords_to_use) > 5:
        keywords_to_use = keywords_to_use[:5]

    extracted_abstract_keywords = []
    fetch_limit = 40

    total_kw = len(keywords_to_use)
    start_match = max(1, total_kw - 1)

    if payload.abstracts:
            unique_keywords_set: Set[str] = set()
            
            for abstract_text in payload.abstracts:
                if not abstract_text or len(abstract_text.split()) < 3:
                    continue
                # max 5 keywords per abstract    
                extracted = extract_keywords_from_text(abstract_text, top_n=10)
                unique_keywords_set.update(extracted)
            
            print(f"\nTotal Unique Keywords Extracted: {unique_keywords_set}\n")
            extracted_abstract_keywords = list(unique_keywords_set)[:9]            

    for match_count in range(start_match, 0, -1):
            print(f"Trying search with min_match_count: {match_count} (Total KW: {total_kw})")
            results_gen = search_from_lists(
                client,
                keywords=keywords_to_use,
                abstracts=extracted_abstract_keywords,
                start_date=payload.start_date,
                end_date=payload.end_date,
                select_fields=SELECT_FIELDS,
                per_page=fetch_limit,
                min_match_count=match_count,
            )
            
            results = list(results_gen)
            
            if results:
                print(f"Found {len(results)} results with match count {match_count}")
                break # Result is found, exit the loop
            else:
                print(f"No results for match count {match_count}, decreasing strictness...")

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