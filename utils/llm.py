from litellm import completion
from config import settings
from utils.logger import get_logger
import litellm
# litellm._turn_on_debug()
## MODEL Switching
#To calling llm model and switching model

log = get_logger(__name__)

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
        log.info("Calling %s tier -> %s", tier, model)

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
        return content
        
    except Exception:
        # Primary model failed — fall back to a stronger/simpler model.
        fallback_model = get_llm("fallback")
        log.warning("Model %s failed; falling back to %s", model, fallback_model)
        log.exception("LLM call error")
        response = litellm.completion(
            model=fallback_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content
        log.info("Fallback model %s succeeded", fallback_model)
        return content