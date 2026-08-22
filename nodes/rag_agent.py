from graph.state import AgentState
from utils.llm import call_llm
from utils.reranker import rerank
from utils.prompt_loader import build_prompt
from utils.vectorstore import load_retriver
from utils.logger import get_logger
import asyncio
from fastmcp import Client

log = get_logger(__name__)

MAX_RETRIES = 2
RAG_SERVER = "mcp_server/rag_server.py"

async def _call_mcp(question:str)->str:
    async with Client(RAG_SERVER) as client:
        result = await client.call_tool("search_docs",{"question":question})
        return result[0].text

def check_relevance(question:str,context:str)->bool:
    prompt = f"""Is this context relevant to the question?
    RETURN ONLY yes or no.

    Question :{question}
    Context : {context}
    Relevant:   """
    result = call_llm(prompt,tier="router").strip().lower()
    return "yes" in result

def rephrase_query(question:str)->str:
    prompt =f""" Rephrase this question differently to improve search results.
    Return ONLY the repharased question.
    
    Original:{question}
Rephrased :"""
    result = call_llm(prompt,tier="router").strip().lower()
    return call_llm(prompt,tier="router").strip()
    

def rag_agent_node(state:AgentState)->dict:
    q = state["question"]
    log.info("RAG agent: retrieving for question -> %r", q)
    base_retriver = load_retriver()
    # retriver = rerank(base_retriver)

    for attempt in range(MAX_RETRIES+1):
        # docs = base_retriver.invoke(q)
        # docs = rerank(q,docs)
        # context = "\n\n".join(doc.page_content for doc in docs)
        context = asyncio.run(_call_mcp(q))

        if check_relevance(q,context):
            log.debug("RAG agent: context relevant on attempt %d", attempt+1)
            break

        if attempt < MAX_RETRIES:
            log.info("RAG agent: retry %d, rephrasing query", attempt+1)
            q = rephrase_query(state["question"])

    prompt = build_prompt("rag_agent",context=context,question=q)
    answer = call_llm(prompt,tier="rag")
    log.info("RAG agent: answer generated")
    return {"rag_result":answer}