from typing import TypedDict,Literal,Optional

class AgentState(TypedDict):
    question:str
    route : Optional[Literal["sql","rag","both"]]
    sql_result : Optional[str]
    rag_result : Optional[str]
    answer : Optional [str]