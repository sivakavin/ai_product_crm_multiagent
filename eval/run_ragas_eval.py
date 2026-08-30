from utils.llm import call_llm
from utils.vectorstore import load_retriver
from utils.reranker import rerank
from nodes.rag_agent import rag_agent_node

test_cases = [
    {
        "question": "What is the refund policy?",
        "ground_truth": "Refunds are accepted within 30 days of purchase for unopened items."
    },
    {
        "question": "How long does standard shipping take?",
        "ground_truth": "Standard shipping takes 2 to 3 business days."
    },
    {
        "question": "What benefits do premium members get?",
        "ground_truth": "Premium members get priority support, free shipping, and faster refunds."
    }
]

def score_faithfulness(answer:str,context:str)->float:
    prompt =f"""Score how well this answer is supported by the context.
    Return ONLY a number between 0.0 and 1.0
    1.0 = fully supported  , 0.0 = not supported at all.
    
    Context:{context}
    Answer :{answer}
Score:"""

    try:
        return float(call_llm(prompt=prompt,tier="router").strip())
    except:
        return 0.0

retriver = load_retriver()

score = {"faithfulness":[]}
print("RAG Evaluation\n")

for tc in test_cases:
    question = tc["question"]
    ground_truth = tc["ground_truth"]

    docs = retriver.invoke(question)
    docs = rerank(question,docs)
    context = "\n\n".join(doc.page_content for doc in docs)

    result = rag_agent_node({"question":question})
    answer = result["rag_result"]

    f = score_faithfulness(answer,context)

    score["faithfulness"].append(f)

print("--------Summary-----------")
print(score)