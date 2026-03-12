# Poor Data Enrichment

Mines bona fide **Poor**-quality translations from SBCUSD production data using MetricX as a
surrogate quality signal. Goal: inject Poor-class examples into MTQE training/eval sets to
address class imbalance at the Poor/Adequate boundary.

## Approach

1. Translate monolingual SBCUSD source text using the Cohere LLM server
2. Run MetricX on (source, hypothesis) pairs to get quality scores
3. Calibrate MetricX thresholds against labeled SpaEng data (Rosetta Stone)
4. Extract sentences scoring above the Poor threshold as Poor candidates

## Translation Jobs

### Prerequisites

- Run from **gpu-a6002** (ssh there; `~/claude` is mounted)
- Use the `twix` conda env: `~/miniconda3/envs/twix/bin/twix`
- Cohere LP configs live in `~/work/twix/llm-configs/`
- The Cohere LLM server must be running on `sdeneefe-g7:8080`
- `LD_LIBRARY_PATH=/home/nbuild/pub/xmt/17.0.52/lib` is required to load the twix env

### Run scripts

```bash
# From gpu-a6002:
nohup bash ~/claude/work/poor-data-enrichment/run-sbcusd-spaeng.sh </dev/null &>/dev/null &
nohup bash ~/claude/work/poor-data-enrichment/run-sbcusd-engesl.sh </dev/null &>/dev/null &
```

Check progress:
```bash
wc -l ~/claude/work/poor-data-enrichment/output-*.jsonl
tail -f ~/claude/work/poor-data-enrichment/output-spaeng.log
```

### Input files

| Job | Source file | LP | Output |
|-----|------------|-----|--------|
| SpaEng | `/home/sdeneefe/work/customer/sbcusd/random_rest.spa` | `SpaEng_COHERE_LLM_0_0_x_0` | `output-spaeng.jsonl` |
| EngEsl | `/home/sdeneefe/work/customer/sbcusd/random_rest.eng` | `EngEsl_COHERE_LLM_0_0_x_0` | `output-engesl.jsonl` |

Both input files are 74,250 lines. Output is JSONL with `src_seg` and `tgt_seg` fields.

## Why `LD_LIBRARY_PATH`?

The `twix` conda env has `languageweaver` (XMT bindings) installed, which loads
`libxmt_shared.so` at import time. Without the correct library path the env fails to
start entirely — even for subcommands like `decode` that don't use XMT at all.
Setting `LD_LIBRARY_PATH=/home/nbuild/pub/xmt/17.0.52/lib` satisfies the loader.

## Next Steps

- [ ] Run MetricX on completed JSONL outputs
- [ ] Calibrate Poor/Adequate/Good thresholds against labeled SpaEng data
- [ ] Extract Poor candidates and inject into MTQE training/eval sets
