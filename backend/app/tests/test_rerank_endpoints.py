import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
from fastapi.testclient import TestClient

from ..main import app
from ..schemas import WorkSummary, WorksSearchResponse

# -------------------------------------------------
# Helpers for logging
# -------------------------------------------------
# ... üstteki importlar aynı kalsın

def group_member_ids(target_group: str) -> List[str]:
    """
    Returns all paper ids within target group
    """
    ids = []
    for p in DATASET:
        if paper_group(p) == target_group:
            ids.append(p["id"])
    return ids


def top_k_ids(returned_results: List[dict], k: int) -> List[str]:
    """
    Returns ids within top k results
    """
    ids = []
    for w in (returned_results[:k] if k > 0 else []):
        wid = w.get("id")
        if wid:
            ids.append(wid)
    return ids


def missing_relevant_ids_in_top_k(
    returned_results: List[dict],
    target_group: str,
    query_id: str,
    k: int,
) -> List[str]:
    """
    It returns the IDs that are in the relevant set (target_group - query_id) but not visible in the top-k.    
    """
    if k <= 0:
        return []

    relevant_ids = set(group_member_ids(target_group))
    relevant_ids.discard(query_id)  # query paper hariç
    top_ids = set(top_k_ids(returned_results, k=k))

    missing = sorted(relevant_ids - top_ids)
    return missing

# -------------------------------------------------
# 1) Grouping rules (4 grup) - SINGLE membership
# -------------------------------------------------
# 1-7   => G1_01_07
# 8-14  => G2_08_14
# 15-20 => G3_15_20
# 21-30 => G4_21_30

RESULT_ROWS = []

QUERY_VARIANTS = ["kw_only", "kw_plus_abs"]

GROUPS: List[Tuple[str, int, int]] = [
    ("G1_01_07", 1, 7),
    ("G2_08_14", 8, 14),
    ("G3_15_20", 15, 20),
    ("G4_21_30", 21, 30),
]

P_THRESHOLD = 0.6

# -----------------------------
# 2) Load fixture
# -----------------------------
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "birkan_papers.json"


def load_dataset() -> List[dict]:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise AssertionError("birkan_papers.json must be a list of objects")

    for p in data:
        if "id" not in p:
            raise AssertionError("Each paper must have an 'id'")
        p.setdefault("title", "")
        p.setdefault("abstract", "")
        p.setdefault("keywords", "")
        p.setdefault("labels", [])
        p.setdefault("query", "")
        p.setdefault("index", 10**9)

    return data


DATASET = load_dataset()
DATASET_BY_ID = {p["id"]: p for p in DATASET}


# -----------------------------
# 3) Single-group membership (by index range)
# -----------------------------
def paper_group(p: dict) -> str:
    """
    Her paper EXACTLY ONE group alır, index aralığına göre (predefined).
    """
    idx = p.get("index")
    if not isinstance(idx, int):
        pid = str(p.get("id", ""))
        m = re.search(r"(\d+)$", pid)
        idx = int(m.group(1)) if m else 10**9

    for gname, lo, hi in GROUPS:
        if lo <= idx <= hi:
            return gname

    raise AssertionError(f"Paper index out of supported ranges: id={p.get('id')} index={idx}")


GROUP_COUNTS: Dict[str, int] = {g[0]: 0 for g in GROUPS}
for p in DATASET:
    GROUP_COUNTS[paper_group(p)] += 1


def dynamic_k(target_group: str, returned_len: int) -> int:
    """
    K = (total number of papers in the group - 1) [because query paper is removed from search space]
    """
    relevant_count = GROUP_COUNTS[target_group] - 1
    if relevant_count < 1:
        return 0
    return min(relevant_count, returned_len)


def pick_two_queries_per_group(dataset: List[dict]) -> Dict[str, List[dict]]:
    grouped: Dict[str, List[dict]] = {g[0]: [] for g in GROUPS}

    for p in dataset:
        g = paper_group(p)
        grouped[g].append(p)

    for g in grouped:
        grouped[g] = sorted(grouped[g], key=lambda x: (x.get("index", 10**9), x.get("title", "")))

    missing = [g for g, arr in grouped.items() if len(arr) < 2]
    if missing:
        counts = {g: len(grouped[g]) for g in grouped}
        raise AssertionError(f"Some groups have <2 papers: {missing}. Counts={counts}")

    return {g: grouped[g][:2] for g in grouped}


def build_test_cases(dataset: List[dict]) -> List[Tuple[str, str]]:
    selected = pick_two_queries_per_group(dataset)
    cases: List[Tuple[str, str]] = []
    for group, papers in selected.items():
        for qp in papers:
            cases.append((group, qp["id"]))
    return cases


TEST_CASES = build_test_cases(DATASET)


# -----------------------------
# 4) Query -> keywords list ONLY
# e.g. "MC + Nanonet + Channel Modeling (7)" -> ["MC","Nanonet","Channel Modeling"]
# -----------------------------
def query_to_keywords_list(q: str) -> List[str]:
    q = (q or "").strip()
    if not q:
        return []
    q = re.sub(r"\(\s*\d+\s*\)\s*$", "", q).strip()
    parts = [p.strip() for p in q.split("+")]
    return [p for p in parts if p]


def build_query_payload(qp: dict, variant: str) -> dict:
    keywords_list = query_to_keywords_list(qp.get("query", ""))

    if variant == "kw_only":
        abstracts = []
    elif variant == "kw_plus_abs":
        abs_text = (qp.get("abstract") or "").strip()
        abstracts = [abs_text] if abs_text else []
    else:
        raise ValueError(f"Unknown variant: {variant}")

    return {
        "keywords": keywords_list,
        "abstracts": abstracts,
        "start_date": None,
        "end_date": None,
    }


# -----------------------------
# 5) Build WorksSearchResponse for search space
# -----------------------------
def build_search_space(excluding_id: str, dataset: List[dict]) -> WorksSearchResponse:
    results: List[WorkSummary] = []
    for p in dataset:
        if p["id"] == excluding_id:
            continue
        results.append(
            WorkSummary(
                id=p["id"],
                title=p.get("title") or "",
                keywords=p.get("keywords") or "",
                abstract=p.get("abstract") or "",
                publication_year=p.get("year") or p.get("publication_year"),
            )
        )
    return WorksSearchResponse(results=results)


def count_hits_in_top_k(returned_results: List[dict], target_group: str, k: int) -> int:
    """
    İlk k sonuç içinde target_group'tan kaç tane geldi?
    """
    if k <= 0:
        return 0
    top = returned_results[:k]
    if not top:
        return 0

    hit = 0
    for w in top:
        wid = w.get("id")
        if not wid or wid not in DATASET_BY_ID:
            continue
        if paper_group(DATASET_BY_ID[wid]) == target_group:
            hit += 1
    return hit


def p_at_k(hit: int, k: int) -> float:
    if k <= 0:
        return 0.0
    return hit / k


# -----------------------------
# 6) TestClient
# -----------------------------
@pytest.fixture(scope="session")
def client():
    return TestClient(app)


# -----------------------------
# 7) Tests (8 suite per model => 16 tests)
# (4 grup * 2 query) = 8 case for each model
# -----------------------------
@pytest.mark.parametrize("group,query_id", TEST_CASES)
@pytest.mark.parametrize("variant", QUERY_VARIANTS)
def test_sentence_transformer_rerank(group, query_id, variant, client: TestClient):
    qp = DATASET_BY_ID[query_id]

    payload = {
        "query": build_query_payload(qp, variant),
        "works": build_search_space(excluding_id=query_id, dataset=DATASET).model_dump(),
    }

    r = client.post("/api/__test__/rerank_only_sentence_transformer", json=payload)
    assert r.status_code == 200, r.text

    results = r.json().get("results") or []
    assert len(results) == len(payload["works"]["results"])

    k_dyn = dynamic_k(target_group=group, returned_len=len(results))
    hit = count_hits_in_top_k(results, target_group=group, k=k_dyn)
    pk = p_at_k(hit=hit, k=k_dyn)

    missing_ids = missing_relevant_ids_in_top_k(
        returned_results=results,
        target_group=group,
        query_id=query_id,
        k=k_dyn,
    )
    missing_str = ";".join(missing_ids)

    RESULT_ROWS.append({
        "model": "sentence_transformer",
        "variant": variant,
        "group": group,
        "query_id": query_id,
        "k": k_dyn,
        "hit_in_top_k": hit,
        "missing_in_top_k": missing_str,
        "p_at_k": pk,
        "threshold": P_THRESHOLD,
        "pass": pk >= P_THRESHOLD,
    })

    assert pk >= P_THRESHOLD, (
        f"[{variant}] P@{k_dyn} too low: {pk:.2f} "
        f"(hit={hit}/{k_dyn}) group={group} query={query_id}"
    )


@pytest.mark.parametrize("group,query_id", TEST_CASES)
@pytest.mark.parametrize("variant", QUERY_VARIANTS)
def test_cross_encoder_rerank(group, query_id, variant, client: TestClient):
    qp = DATASET_BY_ID[query_id]

    payload = {
        "query": build_query_payload(qp, variant),
        "works": build_search_space(excluding_id=query_id, dataset=DATASET).model_dump(),
    }

    r = client.post("/api/__test__/rerank_only_cross_encoder", json=payload)
    assert r.status_code == 200, r.text

    results = r.json().get("results") or []
    assert len(results) == len(payload["works"]["results"])

    k_dyn = dynamic_k(target_group=group, returned_len=len(results))
    hit = count_hits_in_top_k(results, target_group=group, k=k_dyn)
    pk = p_at_k(hit=hit, k=k_dyn)

    missing_ids = missing_relevant_ids_in_top_k(
        returned_results=results,
        target_group=group,
        query_id=query_id,
        k=k_dyn,
    )
    missing_str = ";".join(missing_ids)

    RESULT_ROWS.append({
        "model": "cross_encoder",
        "variant": variant,
        "group": group,
        "query_id": query_id,
        "k": k_dyn,
        "hit_in_top_k": hit,
        "missing_in_top_k": missing_str,
        "p_at_k": pk,
        "threshold": P_THRESHOLD,
        "pass": pk >= P_THRESHOLD,
    })

    assert pk >= P_THRESHOLD, (
        f"[{variant}] P@{k_dyn} too low: {pk:.2f} "
        f"(hit={hit}/{k_dyn}) group={group} query={query_id}"
    )