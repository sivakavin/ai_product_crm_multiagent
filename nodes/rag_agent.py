from graph.state import AgentState
from utils.llm import call_llm
from utils.reranker import rerank
from utils.prompt_loader import build_prompt
from utils.vectorstore import load_retriver

MAX_RETRIES = 2

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
    base_retriver = load_retriver()
    # retriver = rerank(base_retriver)
    
    for attempt in range(MAX_RETRIES+1):
        docs = base_retriver.invoke(q)
        docs = rerank(q,docs)
        context = "\n\n".join(doc.page_content for doc in docs)

        if check_relevance(q,context):
            break

        if attempt < MAX_RETRIES:
            print(f"[RAG] Retry {attempt+1}:rephrasing query")
            q = rephrase_query(state["question"])

    prompt = build_prompt("rag_agent",context=context,question=q)
    answer = call_llm(prompt,tier="rag")
    return {"rag_result":answer}