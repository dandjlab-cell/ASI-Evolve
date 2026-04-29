#!/usr/bin/env python3
"""
crack_transcript_fb.py — Reverse-engineer the V216 transcript FlatBuffers schema.

Strategy: find every length-prefixed string in the blob (FlatBuffers strings
are uint32-length + UTF-8 bytes + null terminator), then for each one, scan
the surrounding bytes for float patterns that look like word timestamps.

Usage:
  python3 crack_transcript_fb.py SOURCE.mfdc                 # inspect one file
  python3 crack_transcript_fb.py SOURCE.mfdc --strings       # just dump strings + offsets
  python3 crack_transcript_fb.py SOURCE.mfdc --windows       # dump byte windows around words
  python3 crack_transcript_fb.py *.mfdc --consensus          # cross-validate offsets across files
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

# Words that are obviously NOT transcribed content — language codes, speaker labels, etc.
META_WORDS = {"en-us", "Unknown", "filler"}


def load(path: Path) -> bytes:
    return path.read_bytes()


def find_strings(blob: bytes, min_len: int = 2, max_len: int = 40) -> list[dict]:
    """Find every plausible FlatBuffers length-prefixed string in the blob.

    FlatBuffers strings: 4-byte LE uint32 length, then `length` UTF-8 bytes,
    then a null terminator. We scan every byte-aligned position for a length
    prefix that produces printable text.
    """
    found = []
    n = len(blob)
    for off in range(0, n - 5):
        # Read 4-byte length (little-endian uint32)
        length = struct.unpack_from('<I', blob, off)[0]
        if length < min_len or length > max_len:
            continue
        end = off + 4 + length
        if end + 1 > n:
            continue
        text_bytes = blob[off + 4:end]
        # All printable ASCII?
        if not all(0x20 <= b < 0x7f for b in text_bytes):
            continue
        # Must be followed by null terminator (FlatBuffers convention)
        if blob[end] != 0:
            continue
        try:
            text = text_bytes.decode('ascii')
        except UnicodeDecodeError:
            continue
        found.append({
            "offset": off,        # offset of length prefix
            "length": length,
            "text": text,
            "data_offset": off + 4,  # offset of the actual text bytes
        })
    return found


def candidate_floats_around(blob: bytes, center: int, radius: int = 64) -> list[dict]:
    """Scan a window around `center` for plausible time-floats.

    Returns every offset in [center-radius, center+radius-8] where:
      - reading 4 bytes as LE float32 → finite value in [0.0, 3600.0]
      - OR reading 8 bytes as LE float64 → finite value in [0.0, 3600.0]
    """
    out = []
    lo = max(0, center - radius)
    hi = min(len(blob) - 8, center + radius)
    for off in range(lo, hi + 1):
        # Try float32
        try:
            v = struct.unpack_from('<f', blob, off)[0]
            if 0.0 <= v < 3600.0 and v == v:  # NaN check via self-equality
                # Filter out near-zero noise (likely structural ints, not timestamps)
                if v >= 0.001 or off == center:
                    out.append({"off": off, "type": "f32", "value": v, "delta_from_center": off - center})
        except struct.error:
            pass
        # Try float64
        try:
            v = struct.unpack_from('<d', blob, off)[0]
            if 0.0 <= v < 3600.0 and v == v:
                if v >= 0.001 or off == center:
                    out.append({"off": off, "type": "f64", "value": v, "delta_from_center": off - center})
        except struct.error:
            pass
    return out


def cmd_strings(blob: bytes) -> None:
    strs = find_strings(blob)
    print(f"Found {len(strs)} length-prefixed strings:")
    for s in strs:
        marker = " (META)" if s["text"] in META_WORDS else ""
        print(f"  off={s['offset']:5d}  len={s['length']:3d}  text={s['text']!r}{marker}")


def cmd_windows(blob: bytes, only_words: bool = True) -> None:
    """For each non-meta string, dump the surrounding bytes + float candidates."""
    strs = find_strings(blob)
    word_strs = [s for s in strs if s["text"] not in META_WORDS] if only_words else strs
    print(f"Inspecting {len(word_strs)} word strings (skipping meta):\n")
    for s in word_strs[:25]:  # cap output
        print(f"━━━ word {s['text']!r} at off={s['offset']} ━━━")
        # Show 16 bytes before and after
        lo = max(0, s["offset"] - 16)
        hi = min(len(blob), s["offset"] + 4 + s["length"] + 16)
        chunk = blob[lo:hi]
        # Hex dump in 16-byte rows
        for i in range(0, len(chunk), 16):
            row = chunk[i:i+16]
            hex_str = " ".join(f"{b:02x}" for b in row)
            ascii_str = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in row)
            abs_off = lo + i
            mark = " <-- " if (s["offset"] >= abs_off and s["offset"] < abs_off + 16) else "     "
            print(f"  {abs_off:5d}{mark}{hex_str:<48s}  |{ascii_str}|")
        # Float candidates in window around this word
        cands = candidate_floats_around(blob, s["offset"], radius=48)
        if cands:
            print(f"  float candidates (Δ from word offset):")
            for c in cands[:8]:
                print(f"    Δ={c['delta_from_center']:+4d}  {c['type']}  value={c['value']:.4f}")
        print()


def cmd_consensus(paths: list[Path]) -> None:
    """For each file, compute the offset DELTA between each word's string and the
    'most plausible' adjacent float. If multiple files show the same delta-pattern,
    we've likely found the timestamp field's offset relative to each word."""
    print(f"Cross-validating timestamp offsets across {len(paths)} files...\n")
    for path in paths:
        blob = load(path)
        strs = [s for s in find_strings(blob) if s["text"] not in META_WORDS]
        if len(strs) < 3:
            print(f"  {path.name}: only {len(strs)} word strings — skipping")
            continue
        # For each word, find the closest "small monotonic float" in [0, 60]
        word_times = []
        for s in strs[:30]:
            cands = candidate_floats_around(blob, s["offset"], radius=32)
            # Filter to plausible audio timestamps
            cands = [c for c in cands if 0.0 < c["value"] < 60.0]
            if not cands:
                word_times.append((s["text"], None, None))
                continue
            # Pick the candidate closest to the word's position
            best = min(cands, key=lambda c: abs(c["delta_from_center"]))
            word_times.append((s["text"], best["delta_from_center"], best["value"]))
        # Print
        print(f"━━━ {path.name} ━━━")
        for text, delta, val in word_times[:20]:
            if delta is None:
                print(f"  {text:<20s}  (no plausible float nearby)")
            else:
                print(f"  {text:<20s}  Δ={delta:+4d}  t={val:.3f}s")
        print()


def main() -> None:
    ap = argparse.ArgumentParser(description="V216 transcript FlatBuffers cracker")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--strings", action="store_true", help="just dump all strings")
    ap.add_argument("--windows", action="store_true", help="dump byte windows around words")
    ap.add_argument("--consensus", action="store_true", help="cross-validate timestamp offsets across files")
    args = ap.parse_args()

    if args.consensus:
        cmd_consensus(args.files)
        return

    for path in args.files:
        if not path.exists():
            print(f"[err] {path} not found", file=sys.stderr); continue
        blob = load(path)
        print(f"\n═══ {path.name}  ({len(blob)} bytes) ═══")
        if args.strings:
            cmd_strings(blob)
        elif args.windows:
            cmd_windows(blob)
        else:
            # Default: show overview + sample windows
            cmd_strings(blob)
            print()
            print("=== Sample byte windows around first 5 word strings ===\n")
            cmd_windows(blob)


if __name__ == "__main__":
    main()
