import os
from config import settings

#check env vars are set
print("TRACING:",settings.langchain_tracing_v2)



import litellm

litellm.success_callback = ["langsmith"]
litellm.failure_callback = ["langsmith"]

print("SUCCESS CB:",litellm.success_callback)
print("FAILURE CB:",litellm.failure_callback)
