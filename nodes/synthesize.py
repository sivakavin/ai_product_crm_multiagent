from graph.state import AgentState
from utils.llm import call_llm
from utils.prompt_loader import build_prompt

def synthesize_node(state:AgentState) -> dict:
    prompt = build_prompt(
        "synthesize",
        question = state["question"],
        sql_result = state.get("sql_result") or "Not avilable",
        rag_result = state.get("rag_result") or "Not avilable",
    )

    answer = call_llm(prompt,tier="synthesize")
    return {"answer":answer}
