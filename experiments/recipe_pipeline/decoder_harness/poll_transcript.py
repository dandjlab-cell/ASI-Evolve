#!/usr/bin/env python3
"""
poll_transcript.py — Watch a .prproj on disk and report transcript changes.

Tells us a few critical things experimentally:
  1. Does Premiere flush transcript edits to disk on every keystroke,
     only on save (Cmd+S), or somewhere in between?
  2. What's the byte-level shape of "the transcript changed" — do we see
     a full FlatBuffers rewrite or partial deltas?
  3. What words are extractable from the FlatBuffers blob via simple
     ASCII-string scanning (vs. needing full schema decode)?

USAGE
  python3 poll_transcript.py "/path/to/x.prproj"

  Then in Premiere: edit the transcript in the Text panel.
  Leave this running; it prints a line each time the file changes.

OUTPUT
  Each change shows:
    - timestamp
    - mtime delta from last change
    - new blob hash (first 12 chars of sha1)
    - new blob size in bytes
    - new word strings extracted from the blob
"""

from __future__ import annotations

import gzip
import hashlib
import re
import base64
import sys
import time
from pathlib import Path

# Line-buffer stdout so output appears immediately when piped/redirected.
sys.stdout.reconfigure(line_buffering=True)

POLL_INTERVAL_S = 0.25
TRANSCRIPT_RE = re.compile(rb'<TranscriptData[^>]*Encoding="base64"[^>]*>([^<]+)</TranscriptData>', re.S)


def extract_transcript_blobs(prproj: Path) -> list[bytes]:
    """Return the decoded FlatBuffers payloads from every TranscriptData
    element in the file. A prproj can have multiple if multiple master clips
    have transcripts attached.
    """
    try:
        raw = gzip.decompress(prproj.read_bytes())
    except Exception as e:
        print(f"[err] cannot read/gunzip {prproj}: {e}", file=sys.stderr)
        return []
    blobs = []
    for m in TRANSCRIPT_RE.finditer(raw):
        try:
            blobs.append(base64.b64decode(m.group(1).strip()))
        except Exception:
            pass
    return blobs


def visible_words(blob: bytes) -> list[str]:
    """Extract printable ASCII runs of length >= 2 from the blob — naive but
    surfaces transcribed words alongside FlatBuffers metadata noise.
    """
    runs = re.findall(rb'[A-Za-z][A-Za-z\'\.,!\?\-]{1,30}', blob)
    return [r.decode('ascii', errors='replace') for r in runs]


def fmt_words(words: list[str], cap: int = 25) -> str:
    if not words:
        return "<none>"
    out = " ".join(words[:cap])
    if len(words) > cap:
        out += f"  ...+{len(words) - cap} more"
    return out


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: poll_transcript.py <path/to/x.prproj>")
    target = Path(sys.argv[1])
    if not target.exists():
        sys.exit(f"[err] not found: {target}")

    print(f"[info] polling {target}")
    print(f"[info] interval: {POLL_INTERVAL_S}s")
    print("[info] Now go edit the transcript in Premiere. Ctrl+C here to stop.\n")

    last_mtime = 0.0
    last_change_t = 0.0
    last_blob_hashes: list[str] = []

    while True:
        try:
            mtime = target.stat().st_mtime
        except FileNotFoundError:
            time.sleep(POLL_INTERVAL_S)
            continue

        if mtime != last_mtime:
            now = time.time()
            delta = now - last_change_t if last_change_t else 0.0
            last_mtime = mtime
            last_change_t = now

            blobs = extract_transcript_blobs(target)
            new_hashes = [hashlib.sha1(b).hexdigest()[:12] for b in blobs]

            ts = time.strftime("%H:%M:%S", time.localtime(now))
            file_size = target.stat().st_size
            print(f"[{ts}] mtime changed (Δ={delta:.2f}s)  prproj={file_size}B  transcript_blobs={len(blobs)}")
            for i, (b, h) in enumerate(zip(blobs, new_hashes)):
                changed = "NEW" if h not in last_blob_hashes else "same"
                print(f"    blob[{i}] sha1={h} size={len(b)}B  [{changed}]")
                if h not in last_blob_hashes:
                    print(f"        words: {fmt_words(visible_words(b))}")
            last_blob_hashes = new_hashes
            print()

        try:
            time.sleep(POLL_INTERVAL_S)
        except KeyboardInterrupt:
            print("\n[info] stopped")
            return


if __name__ == "__main__":
    main()
