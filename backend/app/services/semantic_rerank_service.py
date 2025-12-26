# backend/app/services/semantic_rerank_service.py
from functools import lru_cache
from typing import List, Dict
import numpy as np

from sentence_transformers import SentenceTransformer, util, CrossEncoder

from ..schemas import WorksSearchResponse, WorksSearchRequest

@lru_cache(maxsize=1)
def get_sentence_transformer() -> SentenceTransformer:
    # Load once per process
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

@lru_cache(maxsize=1)
def get_cross_encoder():
    # Load once per process
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def build_search_space_representation(workList: WorksSearchResponse) -> Dict:
    search_space ={}
    for work in workList.results:
        keywords = work.keywords.strip().lower() 
        abstract = work.abstract.strip().lower()
        search_space[work.id] = keywords + " " + abstract
    return search_space


def build_query_space_representation(searchRequest: WorksSearchRequest) -> List[str]:
    query_space = []
    keywords = " ".join(k.strip().lower() for k in searchRequest.keywords)
    if searchRequest.abstracts:
        for abstract in searchRequest.abstracts:
            query_space.append(keywords + " " + abstract.strip().lower())
    if not query_space and keywords:
        query_space.append(keywords)

    return query_space


def rerank_works_by_query_sentence_transformer(searchRequest: WorksSearchRequest, workList: WorksSearchResponse) -> WorksSearchResponse:

    search_space = build_search_space_representation(workList) #Dict
    query_space = build_query_space_representation(searchRequest) #List[str]

    model = get_sentence_transformer()
    query_emb = model.encode(query_space, convert_to_tensor=True) #dim: abstract_num x embed_dim

    search_space_list = [item for item in search_space.values()]
    search_emb = model.encode(search_space_list, convert_to_tensor=True) #dim: #_of_results_from_openalex x embed_dim

    scores = util.cos_sim(query_emb, search_emb).mean(dim=0)  # shape: (# of_results_from_openalex,)

    work_ids = list(search_space.keys())
    work_lookup = {work.id: work for work in workList.results}
    scored_works = sorted(zip(work_ids, scores.tolist()), key=lambda x: x[1], reverse=True)

    sorted_results = [
        work_lookup[work_id] 
        for work_id, _ in scored_works 
        if work_id in work_lookup
    ]

    return WorksSearchResponse(results=sorted_results)

def rerank_works_by_query_cross_encoder(searchRequest: WorksSearchRequest, workList: WorksSearchResponse) -> WorksSearchResponse:
    model = get_cross_encoder()

    query_str = " ".join(k.strip().lower() for k in searchRequest.keywords)
    if searchRequest.abstracts:
        query_pairs = [query_str + " " + abstract.strip().lower() for abstract in searchRequest.abstracts]
    else:
        query_pairs = [query_str]
    len_query_pairs = len(query_pairs)
    ranking_pairs = []
    work_ids_ordered = []

    for work in workList.results:
        doc_text = f"{work.title} {work.abstract}".strip()
        for query in query_pairs:
            ranking_pairs.append([query, doc_text])
        work_ids_ordered.append(work.id)

    if not ranking_pairs:
        return workList

    scores = model.predict(ranking_pairs)
    scores_final = []
    i=0
    while i<len_query_pairs:
        scores_final.append(np.mean(scores[i:i+len_query_pairs]))
        i+=len_query_pairs
    work_lookup = {work.id: work for work in workList.results}
    scored_works = sorted(zip(work_ids_ordered, scores), key=lambda x: x[1], reverse=True)

    sorted_results = [
        work_lookup[work_id] 
        for work_id, _ in scored_works 
        if work_id in work_lookup
    ]

    return WorksSearchResponse(results=sorted_results)