# data/fetch.py
from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterable, List, Optional
from itertools import combinations

from .client import OpenAlexClient


# --------- helpers ------------------------------------------------------
def _sanitize_term(s: str) -> str:
    if not s:
        return ""

    normalized = unicodedata.normalize("NFKD", s)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.replace(",", " ")

    cleaned = re.sub(r"[^A-Za-z0-9.\-\s]", " ", ascii_only)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned

def _quote(s: str) -> str:
    s = _sanitize_term(s).replace('"', r"\"")
    return f"\"{s}\"" if s else ""

def _or_join(terms: Optional[List[str]]) -> Optional[str]:
    if not terms:
        return None
    parts = [_quote(t) for t in (t.strip() for t in terms) if t and t.strip()]
    return " OR ".join(parts) if parts else None

def _combinatorial_join(terms: Optional[List[str]], min_match_count: int = 1) -> Optional[str]:
    """
    min_match_count: Determines the minimum number of words that must intersect. 
    Example: If there are 4 keywords, min_match_count=3 -> OR combinations of 4 and 3 keywords. 
    """
    if not terms:
        return None
    
    clean_terms = [t.strip() for t in terms if t and t.strip()]
    
    if not clean_terms:
        return None

    if len(clean_terms) == 1:
        return _quote(clean_terms[0])

    combined_parts = []

    r = max(2, min_match_count)

    for combo in combinations(clean_terms, r):
        quoted_combo = [_quote(t) for t in combo]
        group_str = f"({' AND '.join(quoted_combo)})"
        combined_parts.append(group_str)

    # If min_match_count is 1 (we are in "bring whatever you find" mode),
    # we must also add single words to the list (simple OR logic).        
    if min_match_count == 1:
        for term in clean_terms:
            combined_parts.append(_quote(term))
    
    return " OR ".join(combined_parts)

def build_filter(
    *,
    keywords: Optional[List[str]] = None,   # searched in title+abstract
    abstracts: Optional[List[str]] = None,  # searched in abstract only
    start_date: Optional[str] = None,       # YYYY-MM-DD
    end_date: Optional[str] = None,         # YYYY-MM-DD
    work_types: Optional[List[str]] = None,
    min_match_count: int = 1,
) -> str:
    """
    Compose an OpenAlex filter string.
    Keywords use combinatorial AND logic joined by OR.  
    """
    filters: List[str] = []

    kw_query = _combinatorial_join(keywords, min_match_count=min_match_count)
    if kw_query:
        field = "title_and_abstract.search"
        filters.append(f"{field}:{kw_query}")

    abs_query = _combinatorial_join(abstracts)
    if abs_query:
        field = "abstract.search"
        filters.append(f"{field}:({abs_query})")

    if start_date:
        filters.append(f"from_publication_date:{start_date}")
    if end_date:
        filters.append(f"to_publication_date:{end_date}")

    if work_types:
        types_str = "|".join([t.strip().lower() for t in work_types])
        filters.append(f"type:{types_str}")

    return ",".join(filters)


# --------- single-page + iterator -------------------------------------------
def works_page(
    client: OpenAlexClient,
    *,
    filter_str: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    sort: str = "relevance_score:desc",
    select_fields: Optional[str] = None,
) -> Dict:
    """
    Fetch a single page from /works. Provide either `filter_str` and/or `search`.
    Returns the raw response dict with 'meta' and 'results'.
    """
    params: Dict[str, object] = {"page": page, "per-page": per_page, "sort": sort}
    if filter_str:
        params["filter"] = filter_str
    if select_fields:
        params["select"] = select_fields
    return client.get_json("works", params)


def iterate_works(
    client: OpenAlexClient,
    *,
    filter_str: str,
    per_page: int = 20,
    sort: str = "relevance_score:desc",
    max_pages: int = 1,  # safety cap
    select_fields: Optional[str] = None,
) -> Iterable[Dict]:
    """
    Yield Work records across pages until the last short page (or `max_pages`).
    """
    page = 1
    fetched = 0
    while True:
        data = works_page(
            client,
            filter_str=filter_str,
            page=page,
            per_page=per_page,
            sort=sort,
            select_fields=select_fields,
        )
        results = data.get("results", []) or []
        for r in results:
            yield r

        if len(results) < per_page:
            break
        page += 1
        fetched += 1
        if max_pages is not None and fetched >= max_pages:
            break


# --------- convenience: build + iterate in one call --------------------------
def search_from_lists(
    client: OpenAlexClient,
    *,
    keywords: Optional[List[str]] = None,
    abstracts: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    per_page: int = 20,
    sort: str = "relevance_score:desc",
    max_pages: int = 1,
    select_fields: Optional[str] = None,
    work_types: List[str] = ["article", "preprint"],
    min_match_count: int = 1,
) -> Iterable[Dict]:
    """
    Build a fielded-search filter from lists, then stream results.
    """
    filt = build_filter(
        keywords=keywords,
        abstracts=abstracts,
        start_date=start_date,
        end_date=end_date,
        work_types=work_types,
        min_match_count=min_match_count,
    )
    yield from iterate_works(
        client,
        filter_str=filt,
        per_page=per_page,
        sort=sort,
        max_pages=max_pages,
        select_fields=select_fields,
    )
