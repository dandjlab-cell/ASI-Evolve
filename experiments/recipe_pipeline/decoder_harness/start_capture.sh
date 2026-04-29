#!/usr/bin/env bash
# start_capture.sh — start fs_usage in background, write PID to /tmp/.fs_usage_pid
# Reads capture dir from /tmp/.harness_capture_dir (Claude wrote it during snapshot).

set -uo pipefail

OUT_DIR=$(cat /tmp/.harness_capture_dir 2>/dev/null)
if [[ -z "$OUT_DIR" || ! -d "$OUT_DIR" ]]; then
  echo "[err] no capture dir found at /tmp/.harness_capture_dir" >&2
  exit 1
fi

LOG="$OUT_DIR/fs_usage.log"
echo "[info] capture dir: $OUT_DIR"
echo "[info] log file:    $LOG"
echo "[info] starting fs_usage (sudo) ..."

sudo fs_usage -w -f filesys "Adobe Premiere Pro 2026" > "$LOG" 2>&1 &
PID=$!
echo "$PID" > /tmp/.fs_usage_pid
echo "[ok] fs_usage running, PID=$PID"
echo
echo "Now in Premiere:"
echo "  1. Window > Text > Captions & Transcription > Transcribe Sequence"
echo "  2. Wait for transcription to finish"
echo "  3. Cmd+S to save"
echo
echo "Then come back and tell Claude 'done' — it will stop the watcher and diff."
