from graph.state import AgentState
from utils.llm import call_llm
from utils.prompt_loader import build_prompt
from utils.vectorstore import load_retriver

def rag_agent_node(state:AgentState)->dict:
    q = state["question"]
    retriver = load_retriver()
    docs = retriver.invoke(q)
    context = "\n\n".join(doc.page_content for doc in docs)
    prompt = build_prompt("rag_agent",context=context,question=q)
    answer = call_llm(prompt,tier="rag")
    return {"rag_result":answer}