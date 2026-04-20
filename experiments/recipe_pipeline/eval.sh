#!/bin/bash
# Recipe Pipeline Evolution — Evaluation Script
# Called by ASI-Evolve Engineer agent for each candidate config.
set -e
set -o pipefail

STEP_DIR="$(pwd)"
if [[ "$STEP_DIR" == */steps/step_* ]]; then
    EXPERIMENT_DIR="$(dirname "$(dirname "$STEP_DIR")")"
else
    EXPERIMENT_DIR="$(dirname "$STEP_DIR")"
fi

SRC_CODE_FILE="${STEP_DIR}/code"
RESULT_JSON="${STEP_DIR}/results.json"
LOG_FILE="${STEP_DIR}/eval.log"
EVALUATOR_PY="${EXPERIMENT_DIR}/evaluator.py"

handle_error() {
    local exit_code=$?
    echo "ERROR: Evaluation failed (Exit Code: $exit_code)" >&2
    cat > "$RESULT_JSON" << EOF
{
    "success": false,
    "eval_score": 0.0,
    "composite": 0.0,
    "eval_time": 0.0,
    "complexity": 0,
    "temp": {"error": "Evaluation failed. See eval.log."}
}
EOF
    exit 0
}
trap 'if [ $? -ne 0 ]; then handle_error; fi' EXIT

echo "=== Recipe Pipeline Evaluation ===" > "$LOG_FILE"
echo "Step Directory: ${STEP_DIR}" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

if [ ! -f "$SRC_CODE_FILE" ]; then
    echo "ERROR: Code file not found: ${SRC_CODE_FILE}" >> "$LOG_FILE"
    exit 1
fi

echo "Running evaluation..." >> "$LOG_FILE"
cd "$EXPERIMENT_DIR"
python3 "$EVALUATOR_PY" "$SRC_CODE_FILE" "$RESULT_JSON" >> "$LOG_FILE" 2>&1
cd "$STEP_DIR"

echo "Evaluation complete." >> "$LOG_FILE"

if [ -f "$RESULT_JSON" ]; then
    score=$(python3 -c "import json; print(json.load(open('$RESULT_JSON')).get('eval_score', 0.0))")
    echo "  Composite score: ${score}"
fi

exit 0
