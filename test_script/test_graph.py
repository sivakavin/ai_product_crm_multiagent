from graph.build_graph  import graph

query = "How much vikram spent?"

queries = [
    ("mask","Hi, my name is Siva Kavin. My email is sivakavin.test@example.com and my phone number is +91 98765 43210.")
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
