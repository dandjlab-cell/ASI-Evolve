#!/usr/bin/env python3
"""
karaoke_watcher.py — Watch a .prproj on disk; on every change, parse the
embedded transcript and write /tmp/karaoke_words.json for the UXP panel to
consume.

Run this in a terminal. Leave it running while editing in Premiere.

Usage:
  python3 karaoke_watcher.py "/path/to/PROJECT.prproj"
  python3 karaoke_watcher.py "/path/to/PROJECT.prproj" --output /tmp/foo.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Reuse the parser
sys.path.insert(0, str(Path(__file__).parent))
from parse_transcript import load_blob, parse_transcript_blob

POLL_INTERVAL_S = 0.25
sys.stdout.reconfigure(line_buffering=True)


def write_json(words: list[dict], output: Path) -> None:
    """Write the words list to the output JSON file (atomic via temp + rename)."""
    payload = {
        "version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "words": words,
    }
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(output)


def main() -> None:
    ap = argparse.ArgumentParser(description="Watch .prproj, write transcript JSON on change")
    ap.add_argument("prproj", type=Path)
    ap.add_argument("--output", type=Path, default=Path("/tmp/karaoke_words.json"))
    ap.add_argument("--interval", type=float, default=POLL_INTERVAL_S)
    args = ap.parse_args()

    if not args.prproj.exists():
        sys.exit(f"[err] not found: {args.prproj}")

    print(f"[info] watching {args.prproj}")
    print(f"[info] writing  {args.output}")
    print(f"[info] poll interval: {args.interval}s")
    print(f"[info] In Premiere: edit the transcript, then Cmd+S. The JSON refreshes on every save.")
    print(f"[info] In UXP panel: click '15. Load' to re-read the JSON; loop will pick up new words on next DIRTY.")
    print()

    last_mtime = 0.0

    # Initial read so the JSON exists from the start
    try:
        blob = load_blob(args.prproj)
        words = parse_transcript_blob(blob)
        write_json(words, args.output)
        last_mtime = args.prproj.stat().st_mtime
        print(f"[init] parsed {len(words)} words from {args.prproj.name}")
        if words:
            print(f"  first: {words[0]['text']!r} @ {words[0]['start']}s")
            print(f"  last:  {words[-1]['text']!r} @ {words[-1]['start']}s")
    except Exception as e:
        print(f"[warn] initial parse failed: {e} — will retry on next change")

    while True:
        try:
            mtime = args.prproj.stat().st_mtime
        except FileNotFoundError:
            time.sleep(args.interval)
            continue

        if mtime != last_mtime:
            last_mtime = mtime
            ts = time.strftime("%H:%M:%S", time.localtime(mtime))
            try:
                blob = load_blob(args.prproj)
                words = parse_transcript_blob(blob)
                write_json(words, args.output)
                print(f"[{ts}] mtime changed → parsed {len(words)} words → wrote {args.output.name}")
                if words:
                    sample = ", ".join(f"{w['text']!r}@{w['start']}s" for w in words[:5])
                    print(f"  first 5: {sample}")
            except Exception as e:
                print(f"[{ts}] mtime changed but parse failed: {e}")

        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[info] stopped")
            return


if __name__ == "__main__":
    main()
