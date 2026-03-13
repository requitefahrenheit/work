#!/usr/bin/env python3
"""
Calibrate MetricX threshold for Poor/not-Poor classification.
Usage: python calibrate_threshold.py <input.jsonl> <scores>
  input.jsonl: lines with {human_label, source, hypothesis}
  scores:      lines with {prediction}
"""
import json, sys, numpy as np
from collections import Counter

def load(input_file, scores_file):
    rows = [json.loads(l) for l in open(input_file)]
    scores = [json.loads(l)['prediction'] for l in open(scores_file)]
    assert len(rows) == len(scores), f"Length mismatch: {len(rows)} vs {len(scores)}"
    for r, s in zip(rows, scores):
        r['mx_score'] = s
    return rows

def calibrate(rows, label_field='human_label', poor_label='Poor'):
    labels = [r[label_field] for r in rows]
    scores = [r['mx_score'] for r in rows]
    binary = [1 if l == poor_label else 0 for l in labels]

    print(f"Total: {len(rows)}  Label dist: {Counter(labels)}")
    print(f"MX score stats: min={min(scores):.3f} max={max(scores):.3f} mean={np.mean(scores):.3f} std={np.std(scores):.3f}")
    print()

    # Per-label MX score stats
    for lbl in sorted(set(labels)):
        s = [r['mx_score'] for r in rows if r[label_field] == lbl]
        print(f"  {lbl:10s} n={len(s):4d}  mean={np.mean(s):.3f}  median={np.median(s):.3f}  std={np.std(s):.3f}")
    print()

    # Sweep thresholds, maximize F1 for Poor class
    best_f1, best_thresh = 0, None
    thresholds = np.percentile(scores, range(5, 96, 1))
    for t in thresholds:
        pred = [1 if s >= t else 0 for s in scores]
        tp = sum(p == 1 and g == 1 for p, g in zip(pred, binary))
        fp = sum(p == 1 and g == 0 for p, g in zip(pred, binary))
        fn = sum(p == 0 and g == 1 for p, g in zip(pred, binary))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        if f1 > best_f1:
            best_f1, best_thresh = f1, t
            best_prec, best_rec = prec, rec

    print(f"Best threshold: {best_thresh:.4f}")
    print(f"  F1={best_f1:.3f}  Precision={best_prec:.3f}  Recall={best_rec:.3f}")
    return best_thresh

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    rows = load(sys.argv[1], sys.argv[2])
    calibrate(rows)
