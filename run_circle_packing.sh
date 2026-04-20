#!/bin/bash
# Run circle packing demo — 2-step validation
# Execute from terminal (not Claude Code) due to nested CLI restriction
set -e

cd "$(dirname "$0")"
source .venv/bin/activate

export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1

EVAL_SCRIPT="$(pwd)/experiments/circle_packing_demo/eval.sh"
chmod +x "$EVAL_SCRIPT"

echo "=== ASI-Evolve Circle Packing Demo ==="
echo "Steps: ${1:-2}"
echo "Eval script: $EVAL_SCRIPT"
echo ""

python main.py \
  --experiment circle_packing_demo \
  --steps "${1:-2}" \
  --sample-n 3 \
  --eval-script "$EVAL_SCRIPT"
