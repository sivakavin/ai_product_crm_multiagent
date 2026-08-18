from litellm import completion
from config import settings
import litellm
# litellm._turn_on_debug()
## MODEL Switching
#To calling llm model and switching model

if settings.langchain_tracing_v2 == "true":
    litellm.success_callback = ["langsmith"]
    litellm.failure_callback = ["langsmith"]

def get_llm(tier:str ="router"):
    """ Return model based on task tier."""
    model_map = {
      "router" :settings.router_model,
      "sql_writter":settings.sql_model,
      "rag": settings.rag_model,
      "synthesize":settings.synthesize_model,
      "fallback":settings.fallback_model,
    }

    model = model_map.get(tier,settings.router_model)
    return model

def call_llm(prompt:str,tier:str="router")->str:
    """ Call llm with automatic fallback"""
    model = get_llm(tier)
    try:
        print(f"🔵 Calling {tier}: {model}")

        response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )
        content = response.choices[0].message.content
        # print("RAW RESPONSE:", repr(response))
        # print("PARSED ROUTE:", repr(content))
        return content
        
    except Exception as e:
        # Fallback to stronger model
        print(f"❌ LLM failed with model: {model}")
        print(f"❌ Error: {e}")
        response = litellm.completion(
            model = get_llm("fallback"),
            messages = [{"role":"user","content":prompt}],
            temperature=0
        )
        return response.choices[0].message.content