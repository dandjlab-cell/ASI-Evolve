#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
python3 dashboard.py
