from flashrank import Ranker,RerankRequest
from config import settings
from utils.logger import get_logger

log = get_logger(__name__)

ranker = Ranker(model_name=settings.reranker_model_name.strip())

def rerank(query:str,docs:list,top_k:int=None)->list:
    if not docs:
        return docs

    top_k = top_k or settings.retriver_k
    passages = [{"id":i,"text":doc.page_content} for i,doc in enumerate(docs)]

    rerank_request = RerankRequest(
        query=query,
        passages= passages,
    )
    log.debug("Reranking %d passage(s) for query: %s", len(passages), query)
    results = ranker.rerank(request=rerank_request)
    log.debug("Reranking complete")
    #Map scores back to original docs
    ranked_docs = []
    for result in results[:top_k]:
        idx = result["id"]
        ranked_docs.append(docs[idx])
    return ranked_docs
