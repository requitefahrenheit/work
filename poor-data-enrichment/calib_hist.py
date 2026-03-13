import json
from collections import defaultdict

labels_file = '/home/jfischer/labels-vs-metricx/es.label'
scores_file = '/home/jfischer/labels-vs-metricx/es.score'

labels = [l.strip() for l in open(labels_file)]
scores = [json.loads(l)['prediction'] for l in open(scores_file)]

assert len(labels) == len(scores)

buckets = defaultdict(lambda: [0]*26)
for lbl, s in zip(labels, scores):
    b = min(int(s), 25)
    buckets[lbl][b] += 1

for lbl in ['Good', 'Adequate', 'Poor']:
    print(lbl, json.dumps(buckets[lbl]))
