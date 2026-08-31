from utils.cache import cache

#Store
cache.set("How much asha spend?",{"route":"sql","answer":"1650"})

#Exact match
print(cache.get("How much asha spend?"))

#Similar
print(cache.get("What is asha total spend?"))

print(cache.get("What is the refund policy?"))