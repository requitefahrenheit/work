#!/bin/bash
cd ~/claude/work/poor-data-enrichment

LD_LIBRARY_PATH=/home/nbuild/pub/xmt/17.0.52/lib \
CO_API_URL=http://sdeneefe-g7:8080 \
CO_API_KEY='string-not-empty' \
~/miniconda3/envs/twix/bin/twix decode \
  /home/sdeneefe/work/customer/sbcusd/random_rest.eng \
  --lp ~/work/twix/llm-configs/EngEsl_COHERE_LLM_0_0_x_0 \
  --input-format txt \
  --attempt-type translation \
  --n-shot 0 \
  --report-every 1 \
  > output-engesl.jsonl 2> >(tee output-engesl.log >&2)
