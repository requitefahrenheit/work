import json
path = '/home/jfischer/sentinel/guardians-mt-eval/results/translations/parts/mx/mx-input-spaeng.jsonl-scores'
scores = [json.loads(l)['prediction'] for l in open(path)]
buckets = [0] * 26
for s in scores:
    b = min(int(s), 25)
    buckets[b] += 1
print(json.dumps(buckets))
