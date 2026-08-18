from langgraph.graph import StateGraph,START,END
from graph.state import AgentState
from nodes.supervisor import supervisor
from nodes.sql_agent import sql_agent_node
from nodes.rag_agent import rag_agent_node
from nodes.synthesize import synthesize_node

def route_decision(state:AgentState) -> str:
    return state["route"]

def route_after_sql(state:AgentState) -> str:
    if state["route"] == "both":
        return "rag_agent"
    return "synthesize"

builder = StateGraph(AgentState)

builder.add_node("supervisor",supervisor)
builder.add_node("sql_agent",sql_agent_node)
builder.add_node("rag_agent",rag_agent_node)
builder.add_node("synthesize",synthesize_node)

builder.set_entry_point("supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_decision,
    {
        "sql":"sql_agent",
        "rag":"rag_agent",
        "both":"sql_agent"
    },
)

builder.add_conditional_edges(
    "sql_agent",
    route_after_sql,
    {
        "rag_agent":"rag_agent",
        "synthesize":"synthesize"
    },
)

builder.add_edge("rag_agent","synthesize")
builder.add_edge("synthesize",END)

graph = builder.compile()
