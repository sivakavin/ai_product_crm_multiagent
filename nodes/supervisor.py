#nodes/supervisor.py
from utils.llm import call_llm
from graph.state import AgentState
from utils.prompt_loader import build_prompt

def supervisor(state:AgentState)-> dict:
    # q = state["question"]

    prompt = build_prompt("supervisor",question=state["question"])
    # print("\n===== PROMPT SENT TO LLM =====")
    # print(prompt)
    # print("==============================\n")
    route = call_llm(prompt,tier="router").strip().lower() # cheap model

    if route not in {"sql","rag","both"}:
        route = "both"
        
    return {"route":route}

# def synthesize(state):
#     answer = call_llm(prompt,tier="synthesize")
#     return {"answer":answer}