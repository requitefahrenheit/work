import json

in_file = '/home/jfischer/claude/work/poor-data-enrichment/output-engesl.jsonl'
out_file = '/home/jfischer/sentinel/guardians-mt-eval/results/translations/parts/mx/mx-input-engesl.jsonl'

n = 0
with open(in_file) as f, open(out_file, 'w') as o:
    for line in f:
        d = json.loads(line)
        o.write(json.dumps({'source': d['src_seg'], 'hypothesis': d['tgt_seg']}) + '\n')
        n += 1

print(f'{n} lines written to {out_file}')
