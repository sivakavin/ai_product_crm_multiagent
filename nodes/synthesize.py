from graph.state import AgentState
from utils.llm import call_llm
from utils.prompt_loader import build_prompt
from utils.logger import get_logger

log = get_logger(__name__)

def synthesize_node(state:AgentState) -> dict:
    log.info("Synthesize: combining results into final answer")
    prompt = build_prompt(
        "synthesize",
        question = state["question"],
        sql_result = state.get("sql_result") or "Not avilable",
        rag_result = state.get("rag_result") or "Not avilable",
    )

    answer = call_llm(prompt,tier="synthesize")
    log.info("Synthesize: final answer ready")
    return {"answer":answer}
