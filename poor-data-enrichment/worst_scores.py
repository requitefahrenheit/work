import json
path = '/home/jfischer/sentinel/guardians-mt-eval/results/translations/parts/mx/mx-input-spaeng.jsonl-scores'
rows = [json.loads(l) for l in open(path)]
scores = [r['prediction'] for r in rows]
worst = sorted(range(len(rows)), key=lambda i: -scores[i])[:10]
print(f'max={max(scores):.4f}  mean={sum(scores)/len(scores):.4f}  min={min(scores):.4f}')
print()
for i in worst:
    r = rows[i]
    print(f'line {i}: score={r["prediction"]:.4f}')
    print(f'  src: {r["source"][:100]}')
    print(f'  hyp: {r["hypothesis"][:100]}')
