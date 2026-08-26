from nodes.guardrails import input_guardrails

result = input_guardrails({"question": "What is the refund policy?"})
print(result)

result = input_guardrails({"question": "DROP TABLE customers"})
print(result)
