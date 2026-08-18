from graph.build_graph  import graph

query = "How much vikram spent?"

queries = [
    ("SQL","How much has Arjun Mehta spent and what order"),
    ("RAG","What is refund policy"),
]

for label,q in queries:
    result =  graph.invoke({
    "question":q,
    "route":None,
    "sql_result":None,
    "rag_result":None,
    "answer":None
})
    print(f"\n[{label}]{q}")
    print(f"Route:{result['route']}")
    print(f"Answer:{result['answer']}")
