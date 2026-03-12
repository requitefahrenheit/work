# Poor Data Enrichment

## Problem

MTQE (Machine Translation Quality Estimation) models are trained on labeled data scored
Poor | Adequate | Good. The **Poor** class is chronically underrepresented in both training
and eval sets — partly because genuine poor translations are hard to source at scale, and
partly because human annotation campaigns tend to over-index on the middle and upper tiers.

This imbalance degrades model performance, especially at the critical Poor/Adequate
boundary where the highest-stakes decisions are made (e.g., whether a translation goes
directly to print or gets flagged for post-editing).

## Approach

Mine **bona fide Poor translations from LDX (Language Office) production data** using
MetricX as a surrogate quality signal — without requiring human labels on the new data.

MetricX (Google, 0–25 scale, lower = better) provides a reference-based quality signal
that has shown strong correlation with human judgments across language pairs. The plan:

1. **Run MetricX on LDX data** to score source/hypothesis pairs
2. **Threshold by score** to identify candidates in the Poor range
3. **Calibrate thresholds using labeled data as a Rosetta Stone** — map MetricX score
   ranges to Poor/Adequate/Good labels using any existing annotated sets for the LP
4. **Extract and validate** a set of confirmed Poor examples for training/eval injection

This avoids the cost of fresh human annotation while grounding the surrogate signal in
actual label space via calibration.

## Current Work: SpaEng / SBCUSD

Initial pilot on Spanish→English using SBCUSD (San Bernardino City Unified School
District) customer data.

### Input Files
```
/home/sdeneefe/work/customer/sbcusd/random_rest.spa   # source (Spanish), 74,250 lines
/home/sdeneefe/work/customer/sbcusd/random_rest.eng   # reference (English), 74,250 lines
```

### Translation Step

Generate MT output using the Cohere Pro LLM via `twix`:

```bash
export CO_API_URL=http://sdeneefe-g7:8080/chat
export GEN_LP=/home/sdeneefe/work/evolve-config-processor/llm-configs/SpaEng_Pro_LLM_3_0_x_0

/home/sdeneefe/work/twix/.venv/bin/twix decode \
  /home/sdeneefe/work/customer/sbcusd/random_rest.spa \
  --lp $GEN_LP \
  --input-format txt \
  --attempt-type translation \
  --report-every 1 >output.jsonl 2> >(tee output.log >&2)
```

See `run-sbcusd-spaeng.sh` for a ready-to-run wrapper.

### LLM Server
- **Host:** `sdeneefe-g7`
- **Port:** `8080`
- **Endpoint:** `http://sdeneefe-g7:8080/chat`

### LP Configs
Located at `/home/sdeneefe/work/evolve-config-processor/llm-configs/`:
| LP | Config |
|----|--------|
| SpaEng | `SpaEng_Pro_LLM_3_0_x_0` |
| EngEsl | `EngEsl_Pro_LLM_3_0_x_0` |

### Next Steps
- [ ] Run twix on SBCUSD spa input → get MT hypothesis output
- [ ] Run MetricX on (source, hypothesis, reference) triples
- [ ] Establish score distribution; identify Poor threshold candidates
- [ ] Cross-reference against any available labeled SpaEng data for calibration
- [ ] Extract Poor candidate set for downstream MTQE training/eval use

## Tools & Paths

| Tool | Path |
|------|------|
| twix binary | `/home/sdeneefe/work/twix/.venv/bin/twix` |
| twix repo | `/home/sdeneefe/work/twix/` |
| LP configs | `/home/sdeneefe/work/evolve-config-processor/llm-configs/` |
| MetricX | See `/home/jfischer/` MetricX setup (XLM-R, COMET-QE, MetricX-24) |

## Notes

- MetricX scores 0–25, lower = better. Rough mapping to Poor/Adequate/Good TBD via
  calibration; expect Poor above ~10–12 pending labeled data analysis.
- MetricX known issues: length bias, tokenizer byte fallback warnings, batch_size > 1
  tensor errors (use batch_size=1 for now).
- The labeled data Rosetta Stone step is critical — surrogate thresholds without
  calibration will produce noisy class boundaries.
