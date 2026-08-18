from nodes.synthesize import synthesize

state = {
    "question":"why vikram is unhappy and what has he orderd",
    "sql_result":"[2,999.0,'refunded'],[4,300.0,'cancelled']",
    "rag_result":"Refund accepeted within 30days.Processing taking 5-7 business days"
}

result = synthesize(state)
print(result["answer"])