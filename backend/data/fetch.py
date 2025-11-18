# data/fetch.py
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .client import OpenAlexClient


# --------- helpers ------------------------------------------------------
def _quote(s: str) -> str:
    s = s.strip().replace('"', r"\"")
    return f"\"{s}\"" if s else ""


def _or_join(terms: Optional[List[str]]) -> Optional[str]:
    if not terms:
        return None
    parts = [_quote(t) for t in (t.strip() for t in terms) if t and t.strip()]
    return " OR ".join(parts) if parts else None


def build_filter(
    *,
    keywords: Optional[List[str]] = None,   # searched in title+abstract
    abstracts: Optional[List[str]] = None,  # searched in abstract only
    start_date: Optional[str] = None,       # YYYY-MM-DD
    end_date: Optional[str] = None,         # YYYY-MM-DD
    language: Optional[str] = None,         # e.g., "en"
    is_oa: Optional[bool] = None,           # True/False
    exact_no_stem: bool = False,            # use .no_stem variants
) -> str:
    """
    Compose an OpenAlex filter string by AND independent filters with commas.
    Terms inside each fielded search are OR.
    """
    filters: List[str] = []

    kw_or = _or_join(keywords)
    if kw_or:
        field = "title_and_abstract.search.no_stem" if exact_no_stem else "title_and_abstract.search"
        filters.append(f"{field}:({kw_or})")

    abs_or = _or_join(abstracts)
    if abs_or:
        field = "abstract.search.no_stem" if exact_no_stem else "abstract.search"
        filters.append(f"{field}:({abs_or})")

    if start_date:
        filters.append(f"from_publication_date:{start_date}")
    if end_date:
        filters.append(f"to_publication_date:{end_date}")
    if language:
        filters.append(f"language:{language}")
    if is_oa is not None:
        filters.append(f"is_oa:{str(is_oa).lower()}")

    return ",".join(filters)


# --------- single-page + iterator -------------------------------------------
def works_page(
    client: OpenAlexClient,
    *,
    filter_str: Optional[str] = None,
    search: Optional[str] = None,                 # optional generic search
    page: int = 1,
    per_page: int = 20,                           # 1..200
    sort: str = "relevance_score:desc",
    select: Optional[str] = None,                  # comma-separated fields
) -> Dict:
    """
    Fetch a single page from /works. Provide either `filter_str` and/or `search`.
    Returns the raw response dict with 'meta' and 'results'.
    """
    params: Dict[str, object] = {"page": page, "per-page": per_page, "sort": sort}
    if filter_str:
        params["filter"] = filter_str
    if search:
        params["search"] = search
    if select:
        params["select"] = select
    return client.get_json("works", params)


def iterate_works(
    client: OpenAlexClient,
    *,
    filter_str: str,
    per_page: int = 200,
    sort: str = "relevance_score:desc",
    select: Optional[str] = None,
    max_pages: Optional[int] = None,  # safety cap
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
            select=select,
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
    language: Optional[str] = None,
    is_oa: Optional[bool] = None,
    exact_no_stem: bool = False,
    per_page: int = 200,
    sort: str = "relevance_score:desc",
    select: Optional[str] = None,
    max_pages: Optional[int] = None,
) -> Iterable[Dict]:
    """
    Build a fielded-search filter from lists, then stream results.
    """
    filt = build_filter(
        keywords=keywords,
        abstracts=abstracts,
        start_date=start_date,
        end_date=end_date,
        language=language,
        is_oa=is_oa,
        exact_no_stem=exact_no_stem,
    )
    yield from iterate_works(
        client,
        filter_str=filt,
        per_page=per_page,
        sort=sort,
        select=select,
        max_pages=max_pages,
    )
