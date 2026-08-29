import json
from nodes.supervisor import supervisor

with open("eval/test_set.json") as f:
    test_set = json.load(f)

correct = 0
total = len(test_set)

for test in test_set:
    result = supervisor({"question":test["question"]})
    actual = result["route"]
    expected = test["expected_route"]
    match = "true" if actual == expected else "false"
    print(f"{match} Q:{test['question']} |expected={expected}|got={actual}")
    if actual == expected:
        correct +=1

print(f"\nRouting accuracy:{correct}/{total} ({round(correct/total*100)}%)")