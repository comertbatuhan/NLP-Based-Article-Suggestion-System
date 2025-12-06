# backend/app/services/semantic_rerank_service.py
from functools import lru_cache
from typing import List, Dict

from sentence_transformers import SentenceTransformer, util, CrossEncoder

from ..schemas import WorksSearchResponse, WorksSearchRequest
 

"""@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    # Load once per process
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")"""

@lru_cache(maxsize=1)
def get_model():
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


"""def rerank_works_by_query(searchRequest: WorksSearchRequest, workList: WorksSearchResponse) -> WorksSearchResponse:

    search_space = build_search_space_representation(workList) #Dict
    query_space = build_query_space_representation(searchRequest) #List[str]

    model = get_model()
    query_emb = model.encode(query_space, convert_to_tensor=True) #dim: abstract_num x embed_dim

    search_space_list = [item for item in search_space.values()]
    search_emb = model.encode(search_space_list, convert_to_tensor=True) #dim: #_of_results_from_openalex x embed_dim

    scores = util.cos_sim(query_emb, search_emb).max(dim=0).values  # shape: (_of_results_from_openalex,)

    work_ids = list(search_space.keys())
    work_lookup = {work.id: work for work in workList.results}
    scored_works = sorted(zip(work_ids, scores.tolist()), key=lambda x: x[1], reverse=True)

    sorted_results = [
        work_lookup[work_id] 
        for work_id, _ in scored_works 
        if work_id in work_lookup
    ]

    return WorksSearchResponse(results=sorted_results)"""

def rerank_works_by_query(searchRequest: WorksSearchRequest, workList: WorksSearchResponse) -> WorksSearchResponse:
    model = get_model()

    # 1. Prepare the Query String
    # (Using your fallback logic from before)
    query_str = " ".join(k.strip().lower() for k in searchRequest.keywords)
    if searchRequest.abstracts:
         # If you have abstracts in the request, you might concatenate them, 
         # but usually, the query should be short and specific. 
         # Let's assume the query is the keywords for best results.
         pass 

    # 2. Prepare Pairs: [(Query, Doc1), (Query, Doc2), ...]
    # We compare the Query against the Abstract (or Title + Abstract) of the work.
    ranking_pairs = []
    work_ids_ordered = []

    for work in workList.results:
        # Construct the document text. 
        # TIP: Title is often more important than abstract. Put it first.
        doc_text = f"{work.title} {work.abstract}".strip()
        
        ranking_pairs.append([query_str, doc_text])
        work_ids_ordered.append(work.id)

    if not ranking_pairs:
        return workList

    # 3. Predict Scores
    # The model returns an array of scores, e.g., [4.5, -1.2, 0.8...]
    scores = model.predict(ranking_pairs)

    # 4. Sort and Reconstruct
    work_lookup = {work.id: work for work in workList.results}
    
    # Zip IDs with scores
    scored_works = sorted(zip(work_ids_ordered, scores), key=lambda x: x[1], reverse=True)

    sorted_results = [
        work_lookup[work_id] 
        for work_id, _ in scored_works 
        if work_id in work_lookup
    ]

    return WorksSearchResponse(results=sorted_results)