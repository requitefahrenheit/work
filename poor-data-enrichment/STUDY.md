# Poor Data Enrichment Study
## Mining Poor-Quality Translations from SBCUSD Production Output

**Author:** Jeremy Fischer (`jfischer`)  
**Date:** March 2026  
**Machines:** `c-jfischer3` (orchestration), `gpu-a6002` (inference)  
**Working directory:** `~jfischer/claude/work/poor-data-enrichment/`  
**Repo:** `requitefahrenheit/work` → `poor-data-enrichment/`  
**Visualizations:** See `figures.html` in this directory

---

## 2. Background & Motivation

MTQE (Machine Translation Quality Estimation) models predict translation quality without reference translations. They are trained on human-labeled data with three classes: **Good**, **Adequate**, and **Poor**. In practice, Poor-quality translations are rare in production output from well-performing MT systems, so labeled datasets are heavily skewed toward Good and Adequate.

Models trained on imbalanced data systematically underpredict Poor, reducing their utility as quality gatekeepers — precisely the use case where they matter most.

This study uses MetricX scores as a surrogate signal to identify likely-Poor translations in a large unlabeled production corpus, producing candidates for injection into MTQE training and evaluation sets.

---

## 3. Hypothesis

MetricX score is a reliable enough proxy for human Poor labels that a threshold on MX score can identify a high-precision subset of Poor translations from unlabeled production data. The threshold is calibrated against a human-labeled dataset in the same domain.

---

## 4. Data Sources

### 4.1 Source Sentences (Input to Translation)

| Direction | File | Lines |
|-----------|------|-------|
| es→en | `/home/sdeneefe/work/customer/sbcusd/random_rest.spa` | 74,250 |
| en→es | `/home/sdeneefe/work/customer/sbcusd/random_rest.eng` | 74,250 |

These files are the **unlabeled remainder** of the SBCUSD corpus after 1,338 segments were carved out for human annotation. They represent genuine production-domain content: school district communications including board minutes, IEPs, LCAP documents, and parent-facing materials.

`random_rest` was confirmed to have **zero source-sentence overlap** with the evaluation sets, meaning it is a clean held-out population.

### 4.2 Evaluation / Calibration Sets (Human-Labeled)

#### en→es (Primary — has Poor labels)

| File | Segments | Labels |
|------|----------|--------|
| `~jfischer/labels-vs-metricx/es.label` | 25,496 | Good / Adequate / Poor |
| `~jfischer/labels-vs-metricx/es.score` | 25,496 | MetricX predictions (JSONL) |

Label breakdown: Good 9,518 · Adequate 9,759 · Poor 6,219

This is the **only dataset with Poor labels** and is therefore the sole basis for threshold calibration.

#### es→en (Secondary — Good/Adequate only)

| File | Segments | Labels |
|------|----------|--------|
| `/.aws/lw-data/datarepo/mtqe/domain/transformed/es-en/es,en,domain,dev.jsonl` | 338 | Good / Adequate |
| `/.aws/lw-data/datarepo/mtqe/domain/transformed/es-en/es,en,domain,test.jsonl` | 1,000 | Good / Adequate |

No Poor labels exist for es→en. These sets cannot be used for threshold calibration in that direction. The en→es threshold is used as a proxy for es→en on the assumption of domain consistency.

**Domain verification:** Both eval sets and both `random_rest` files were confirmed to be SBCUSD school district content. The eval sets are literally the 1,338 segments sampled from the same corpus before `random_rest` was formed.

---

## 5. Translation

### 5.1 Infrastructure

Translations were generated using a **Cohere model** served locally inside Docker on `gpu-a6002`. The container loaded safetensor checkpoint shards at startup. Once running, it accepted batches of source sentences via HTTP and returned translations.

The translation server was managed via the `twix` orchestration framework, which validated dataset paths and configuration schemas before launch.

### 5.2 Scripts

| Script | Purpose |
|--------|---------|
| `run-sbcusd-spaeng.sh` | Translates `random_rest.spa` (es→en), 74,250 lines |
| `run-sbcusd-engesl.sh` | Translates `random_rest.eng` (en→es), 74,250 lines |

### 5.3 Output Files

| File | Lines | Size | Notes |
|------|-------|------|-------|
| `output-spaeng.jsonl` | 74,250 | ~25MB | es→en translations |
| `output-engesl.jsonl` | 74,250 | ~26MB | en→es translations |

### 5.4 Output Schema

Each JSONL line contains:
```
src_seg, constraints, fully_matched_by_constraint, tgt_seg, n_shot, nmt_seg
```

**Critical field note:**
- **SpaEng (es→en):** translation is in `nmt_seg`
- **EngEsl (en→es):** translation is in `tgt_seg` — `nmt_seg` is null throughout

This asymmetry must be respected in all downstream processing.

---

## 6. MetricX Evaluation

### 6.1 What is MetricX

MetricX is a neural translation evaluation model that requires **no reference translation**. It takes a source sentence and a translation hypothesis and outputs a scalar quality score. Higher scores indicate worse quality. The scale runs from 0 to 25, with 25 being a hard ceiling.

MetricX was run in GPU batches for efficiency using the `go-mx` wrapper script.

### 6.2 Infrastructure

All MetricX jobs were run on `gpu-a6002` from:
```
~/sentinel/guardians-mt-eval/results/translations/parts/mx/
```
Using the `go-mx` script:
```bash
go-mx <input_file> <CUDA_VISIBLE_DEVICES>
```
Output is written to `./input_file-scores` in JSONL format.

**Critical gotcha:** The input JSONL must **not** contain a `label` field — this conflicts with HuggingFace internals. Rename any human label field to `human_label` before passing to MetricX.

### 6.3 Input Preparation

For EngEsl (en→es), `prep_mx_engesl.py` was used to convert `output-engesl.jsonl` into MX input format, correctly extracting `tgt_seg` as the translation hypothesis.

Null checks were performed with `check_nulls.py` before launching inference jobs.

### 6.4 Jobs Run

| Job | Input | Output | GPU | Status |
|-----|-------|--------|-----|--------|
| SpaEng 74k | `mx-input-spaeng.jsonl` | `mx-input-spaeng.jsonl-scores` | 3 | ✅ Done |
| EngEsl 74k | `mx-input-engesl.jsonl` | `mx-input-engesl.jsonl-scores` | 0 | ✅ Done |
| SpaEng dev | `mx-input-spaeng-dev.jsonl` | `mx-input-spaeng-dev.jsonl-scores` | — | ✅ Done |
| SpaEng test | `mx-input-spaeng-test.jsonl` | `mx-input-spaeng-test.jsonl-scores` | — | ✅ Done |
| EngEsl calib | `labels-vs-metricx/es.score` | (pre-existing) | — | ✅ Done |

Note: The EngEsl 74k job OOM'd on GPU 3 (PID 132137) and was relaunched on GPU 0 (48GB free, PID 136899). Completed at ~12:05 AM Pacific, 74,250/74,250 lines.

### 6.5 Score Output Schema

Each line of a `-scores` file is JSONL:
```json
{"source": "...", "hypothesis": "...", "prediction": 1.234}
```

---

## 7. Score Distributions

### 7.1 Production 74k Sets

| Set | n | Mean | Notes |
|-----|---|------|-------|
| en→es (EngEsl) | 74,250 | 1.442 | Cleaner system, lower tail |
| es→en (SpaEng) | 74,250 | 1.856 | Fatter right tail |

Both distributions are heavily right-skewed. Most segments score 0–2. The hard ceiling of 25.0 is hit by verbatim-copy outputs, dropped content, and already-English source sentences.

### 7.2 Calibration Set (en→es, human-labeled)

| Label | n | Mean | Median |
|-------|---|------|--------|
| Good | 9,518 | 1.07 | ~0.8 |
| Adequate | 9,759 | 1.54 | ~1.4 |
| Poor | 6,219 | 2.89 | ~3.0 |

The Good and Adequate distributions overlap substantially. Poor is shifted right with a long flat tail extending to ~12.

---

## 8. Threshold Analysis

Two rule-of-thumb thresholds were evaluated based on the score distributions and the calibration data. Formal F1-maximizing threshold calibration (via `calibrate_threshold.py`) is pending.

### 8.1 MX > 6 (Conservative)

| Set | Candidates | % of total |
|-----|-----------|------------|
| es→en (SpaEng) | 1,637 | 2.20% |
| en→es (EngEsl) | 832 | 1.12% |
| **Combined** | **2,469** | **1.66%** |

### 8.2 MX > 4 (Liberal)

| Set | Candidates | % of total |
|-----|-----------|------------|
| es→en (SpaEng) | 6,664 | 9.0% |
| en→es (EngEsl) | 3,773 | 5.1% |
| **Combined** | **10,437** | **7.0%** |

### 8.3 Interpretation

The 4–6 range sits above the Poor mean (~2.9) but is well within the Poor distribution. It also overlaps with the upper tail of Adequate. Using MX > 4 yields ~4× more candidates at the cost of likely including genuine Adequates. MX > 6 is higher precision but thin yield.

The recommended next step is to run `calibrate_threshold.py` against the en→es calibration set to find the F1-maximizing threshold, then apply that to both 74k score files.

---

## 9. Conclusions & Next Steps

### What we established

1. Both 74k translation jobs completed successfully with confirmed line counts.
2. All MetricX scoring jobs completed.
3. The en→es calibration set provides a usable signal for threshold calibration (Good/Adequate/Poor well-separated in MX space).
4. The es→en eval set has no Poor labels and cannot be used for calibration directly.
5. SpaEng yields nearly 2× the Poor candidates of EngEsl at any threshold — consistent with its higher mean MX score.
6. At MX > 4: ~10k combined candidates. At MX > 6: ~2.5k combined candidates.

### Pending

- [ ] Run `calibrate_threshold.py` to find F1-maximizing threshold on en→es calib set
- [ ] Apply calibrated threshold to both 74k MX score files
- [ ] Extract Poor candidate rows (src + hypothesis pairs) for each direction
- [ ] Human spot-check sample to validate precision at chosen threshold
- [ ] Inject candidates into MTQE training/eval data pipeline
- [ ] Quadrant analysis: Sentinel difficulty scores vs MetricX scores

---

## 10. Files in This Directory

| File | Description |
|------|-------------|
| `STUDY.md` | This document |
| `figures.html` | Four count-scaled KDE visualizations (see §11) |
| `run-sbcusd-spaeng.sh` | Translation job script, es→en |
| `run-sbcusd-engesl.sh` | Translation job script, en→es |
| `calibrate_threshold.py` | F1-maximizing threshold sweep over en→es calib set |
| `prep_mx_engesl.py` | Converts EngEsl output JSONL to MetricX input format |
| `check_nulls.py` | Validates no null src/hypothesis before MX inference |
| `histogram.py` | Score bucket counts for histogram analysis |
| `calib_hist.py` | Per-label bucket counts from labels-vs-metricx |
| `worst_scores.py` | Top-N worst MX scores with src/hypothesis for inspection |

---

## 11. Visualizations (see figures.html)

Four count-scaled KDE plots are included as an HTML addendum (`figures.html`).

Count-scaled KDE means the area under each curve is proportional to the number of samples in that group — unlike normalized density plots where all curves integrate to 1. This allows direct visual comparison of both shape and absolute counts.

| Figure | Description |
|--------|-------------|
| 1 | en→es 74k production scores — single distribution, n=74,250 |
| 2 | es→en 74k production scores — single distribution, n=74,250 |
| 3 | en→es eval set by label — Good / Adequate / Poor |
| 4 | es→en eval set by label — Good / Adequate only (no Poor labels exist) |
