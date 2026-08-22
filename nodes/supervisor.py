#nodes/supervisor.py
from utils.llm import call_llm
from graph.state import AgentState
from utils.prompt_loader import build_prompt
from utils.logger import get_logger

log = get_logger(__name__)

def supervisor(state:AgentState)-> dict:
    log.info("Supervisor: routing question -> %r", state["question"])

    prompt = build_prompt("supervisor",question=state["question"])
    route = call_llm(prompt,tier="router").strip().lower() # cheap model

    if route not in {"sql","rag","both"}:
        log.warning("Invalid route %r from model; defaulting to 'both'", route)
        route = "both"

    log.info("Supervisor: route = %s", route)
    return {"route":route}

# def synthesize(state):
#     answer = call_llm(prompt,tier="synthesize")
#     return {"answer":answer}