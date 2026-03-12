#!/bin/bash
source ~/claude/env.sh

export CO_API_URL=http://sdeneefe-g7:8080/chat
export GEN_LP=/home/sdeneefe/work/evolve-config-processor/llm-configs/SpaEng_Pro_LLM_3_0_x_0

TWIX=/home/sdeneefe/work/twix/.venv/bin/twix
INPUT=/home/sdeneefe/work/customer/sbcusd/random_rest.spa

$TWIX decode $INPUT \
  --lp $GEN_LP \
  --input-format txt \
  --attempt-type translation \
  --report-every 1 >output.jsonl 2> >(tee output.log >&2)
