from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from graph.build_graph import graph
# from utils.llm import get_usage_stats
from utils.cache import cache

app = FastAPI(title="CRM Multi-Agent API")

class QuertRequest(BaseModel):
    question : str

class QueryResponse(BaseModel):
    question:str
    route:str
    answer:str
    cached:bool

@app.post("/query",response_model=QueryResponse)
def quert_crm(request:QuertRequest):
    #check cache first
    cached_response = cache.get(request.question)

    if cached_response:
        return QueryResponse(
            question=request.question,
            route = cached_response["route"],
            answer = cached_response["answer"],
            cached=True
        )
    try:
        result = graph.invoke({
            "question":request.question,
            "route":None,
            "sql_result":None,
            "rag_result":None,
            "answer":None,
        })

        answer = result.get("answer") or result.get("sql_result") or result.get("rag_result") or "No answer found"
        route = result.get("route","unknown")

        #Store in cache
        cache.set(request.question,{"route":route,"answer":answer})

        return QueryResponse(
                question=request.question,
                route = cached_response["route"],
                answer = cached_response["answer"],
                cached=False )
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@app.get("/health")
def health():
    return {"status":"ok"}

