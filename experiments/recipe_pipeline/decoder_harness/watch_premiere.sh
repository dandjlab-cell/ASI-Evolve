#!/usr/bin/env bash
#
# watch_premiere.sh — Capture everything Premiere does during one operation.
#
# Designed for the prproj reverse-engineering loop: start the watcher, perform
# ONE operation in Premiere (transcribe a clip, import audio, change a color),
# stop the watcher, get a clean log of every file Premiere read/wrote and an
# XML diff of any open .prproj you point at.
#
# USAGE
#   ./watch_premiere.sh <label> [--prproj <path>]
#
#     <label>          short tag for the output dir, e.g. "transcribe-30s"
#     --prproj <path>  optional .prproj to snapshot before/after for XML diff
#                      (Premiere must be saved first for the diff to be useful)
#
#   Output:  decoder_harness/captures/<timestamp>-<label>/
#
# FLOW
#   1. Snapshots the prproj XML (if given)
#   2. Starts fs_usage + fswatch
#   3. You perform the operation in Premiere
#   4. Press Enter when done
#   5. Stops watchers, snapshots prproj again, diffs
#   6. Prints a summary
#
# DEPS
#   fs_usage   built-in macOS, needs sudo (will prompt)
#   fswatch    optional; `brew install fswatch` if missing
#   gunzip     built-in

set -uo pipefail

# -------- args --------------------------------------------------------------
if [[ $# -lt 1 ]]; then
  echo "usage: $0 <label> [--prproj <path>]" >&2
  exit 2
fi
LABEL="$1"; shift
PRPROJ=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prproj) PRPROJ="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# -------- paths -------------------------------------------------------------
HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"
TS="$(date +%Y%m%d-%H%M%S)"
OUT="$HARNESS_DIR/captures/$TS-$LABEL"
mkdir -p "$OUT"

MEDIA_CACHE_FILES="$HOME/Library/Application Support/Adobe/Common/Media Cache Files"
MEDIA_CACHE_DB="$HOME/Library/Application Support/Adobe/Common/Media Cache"
PREMIERE_PROC_NAME="Adobe Premiere Pro 2026"

# -------- preflight ---------------------------------------------------------
HAVE_FSWATCH=0
if command -v fswatch >/dev/null 2>&1; then
  HAVE_FSWATCH=1
else
  echo "[warn] fswatch not installed (brew install fswatch). Continuing without it." >&2
fi

PIDS=$(pgrep -f "$PREMIERE_PROC_NAME" 2>/dev/null | tr '\n' ',' | sed 's/,$//')
if [[ -z "$PIDS" ]]; then
  echo "[err] no Premiere process matching '$PREMIERE_PROC_NAME'" >&2
  exit 1
fi
echo "[info] Premiere PIDs: $PIDS"
echo "[info] capture dir:  $OUT"

# -------- snapshot prproj BEFORE -------------------------------------------
if [[ -n "$PRPROJ" ]]; then
  if [[ ! -f "$PRPROJ" ]]; then
    echo "[err] prproj not found: $PRPROJ" >&2
    exit 1
  fi
  echo "[info] snapshotting prproj BEFORE"
  cp "$PRPROJ" "$OUT/before.prproj"
  gunzip -c "$PRPROJ" > "$OUT/before.xml" 2>/dev/null || true
fi

# -------- start watchers ----------------------------------------------------
echo "[info] starting fs_usage (will prompt for sudo)"
sudo fs_usage -w -f filesys "$PREMIERE_PROC_NAME" > "$OUT/fs_usage.log" 2>&1 &
FS_USAGE_PID=$!

FSWATCH_PID=""
if [[ $HAVE_FSWATCH -eq 1 ]]; then
  echo "[info] starting fswatch on Media Cache dirs"
  fswatch -t -x "$MEDIA_CACHE_FILES" "$MEDIA_CACHE_DB" > "$OUT/fswatch.log" 2>&1 &
  FSWATCH_PID=$!
fi

cleanup() {
  [[ -n "${FS_USAGE_PID:-}" ]] && sudo kill "$FS_USAGE_PID" 2>/dev/null
  [[ -n "${FSWATCH_PID:-}" ]] && kill "$FSWATCH_PID" 2>/dev/null
}
trap cleanup EXIT

sleep 1
echo
echo "============================================================"
echo "  Watchers running. Perform ONE operation in Premiere now."
echo "  In Premiere: save the project FIRST if you want the XML diff."
echo "  Then press ENTER here to stop."
echo "============================================================"
read -r _

# -------- stop watchers -----------------------------------------------------
sudo kill "$FS_USAGE_PID" 2>/dev/null
[[ -n "$FSWATCH_PID" ]] && kill "$FSWATCH_PID" 2>/dev/null
sleep 1

# -------- snapshot prproj AFTER + diff -------------------------------------
if [[ -n "$PRPROJ" ]]; then
  echo "[info] snapshotting prproj AFTER"
  cp "$PRPROJ" "$OUT/after.prproj"
  gunzip -c "$PRPROJ" > "$OUT/after.xml" 2>/dev/null || true
  diff -u "$OUT/before.xml" "$OUT/after.xml" > "$OUT/prproj.diff" 2>/dev/null || true
  DIFF_LINES=$(wc -l < "$OUT/prproj.diff" 2>/dev/null | tr -d ' ' || echo 0)
  echo "[info] prproj diff: $DIFF_LINES lines"
fi

# -------- summary -----------------------------------------------------------
echo
echo "=========================== SUMMARY ========================="
echo "Capture dir: $OUT"
[[ -f "$OUT/fs_usage.log" ]] && echo "fs_usage:    $(wc -l < "$OUT/fs_usage.log" | tr -d ' ') lines"
[[ -f "$OUT/fswatch.log" ]] && echo "fswatch:     $(wc -l < "$OUT/fswatch.log" | tr -d ' ') events"

if [[ -f "$OUT/fswatch.log" ]]; then
  echo
  echo "--- New / changed files in Media Cache (top 30 unique) ---"
  awk '{print $NF}' "$OUT/fswatch.log" | sort -u | head -30
fi

if [[ -f "$OUT/fs_usage.log" ]]; then
  echo
  echo "--- File extensions Premiere wrote (sorted by frequency) ---"
  grep -E "WrData|pwrite|open.*W" "$OUT/fs_usage.log" 2>/dev/null \
    | awk '{for(i=NF;i>=1;i--) if($i ~ /^\//){print $i; break}}' \
    | grep -oE '\.[a-zA-Z0-9]{2,8}$' \
    | sort | uniq -c | sort -rn | head -15

  echo
  echo "--- Likely-interesting paths (cfa/pek/transcript/json) ---"
  grep -iE "\.cfa|\.pek|transcript|\.json" "$OUT/fs_usage.log" 2>/dev/null \
    | awk '{for(i=NF;i>=1;i--) if($i ~ /^\//){print $i; break}}' \
    | sort -u | head -30
fi

echo
echo "Inspect with:"
echo "  less '$OUT/fs_usage.log'"
[[ -f "$OUT/fswatch.log" ]] && echo "  less '$OUT/fswatch.log'"
[[ -n "$PRPROJ" ]] && echo "  less '$OUT/prproj.diff'"
