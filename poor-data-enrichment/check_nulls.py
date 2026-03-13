import json, os
f = os.path.expanduser('~/sentinel/guardians-mt-eval/results/translations/parts/mx/mx-input-engesl.jsonl')
nulls = []
for i, l in enumerate(open(f)):
    d = json.loads(l)
    if d.get('source') is None or d.get('hypothesis') is None:
        nulls.append((i, d))
print(f'total nulls: {len(nulls)}')
for i, r in nulls[:5]:
    print(i, r)
