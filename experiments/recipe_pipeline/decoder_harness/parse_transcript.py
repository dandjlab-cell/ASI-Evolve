#!/usr/bin/env python3
"""
parse_transcript.py — Decode Premiere's V216 transcript FlatBuffers blob into
word-level data with timing.

Schema (cracked 2026-04-29 by reverse-engineering the
SERIALIZED_TRANSCRIPT_FLAT_BUFFERV216 format):

  WordTable (36-byte table, 5–8 fields visible in vtables):
    vtable_offset  6:  byte    (flag/bool, often 0x01)
    vtable_offset  7:  byte    (flag/bool, often 0x01)
    vtable_offset  8:  uoffset_t to text string (uint32, relative)
    vtable_offset 12:  float32 confidence
    vtable_offset 16:  uint64  start_time_ticks (Premiere ticks: 1s = 254,016,000,000)
    vtable_offset 24:  uint64  duration_ticks

Storage is reverse-temporal: the file lists words newest-first, oldest-last.
We sort by start_time at the end.

Usage:
  python3 parse_transcript.py BLOB.mfdc                 # parse one cache file
  python3 parse_transcript.py PROJECT.prproj            # parse a .prproj's embedded blob
  python3 parse_transcript.py BLOB.mfdc --json          # emit JSON
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import struct
import sys
from pathlib import Path

TICKS_PER_SECOND = 254_016_000_000  # Premiere's universal time unit

# Strings that indicate metadata, not transcribed words
META_STRINGS = {"en-us", "Unknown", "filler"}

# Vtable offsets (from the cracked schema)
VT_OFF_TEXT       = 8
VT_OFF_CONFIDENCE = 12
VT_OFF_START      = 16
VT_OFF_DURATION   = 24


def load_blob(path: Path) -> bytes:
    """Load the FlatBuffers blob from either a .mfdc cache file or a .prproj."""
    raw = path.read_bytes()
    # Heuristic: .prproj is gzipped XML, .mfdc is the raw FlatBuffers
    if raw[:2] == b'\x1f\x8b':  # gzip magic
        xml_bytes = gzip.decompress(raw)
        m = re.search(rb'<TranscriptData[^>]*Encoding="base64"[^>]*>([^<]+)</TranscriptData>', xml_bytes)
        if not m:
            raise ValueError("No <TranscriptData> found in .prproj")
        return base64.b64decode(m.group(1).strip())
    # Otherwise assume it's already the FlatBuffers blob
    return raw


def find_strings(blob: bytes, min_len: int = 1, max_len: int = 60) -> list[dict]:
    """Find all FlatBuffers length-prefixed strings (length, bytes, null)."""
    found = []
    n = len(blob)
    for off in range(0, n - 5):
        length = struct.unpack_from('<I', blob, off)[0]
        if length < min_len or length > max_len:
            continue
        end = off + 4 + length
        if end + 1 > n or blob[end] != 0:
            continue
        text_bytes = blob[off + 4:end]
        if not all(0x20 <= b < 0x7f for b in text_bytes):
            continue
        try:
            text = text_bytes.decode('ascii')
        except UnicodeDecodeError:
            continue
        found.append({"offset": off, "length": length, "text": text})
    return found


def _read_vtable(blob: bytes, vtable_off: int) -> list[int] | None:
    """Read field-offsets from a vtable. Returns None if vtable looks invalid."""
    if vtable_off < 0 or vtable_off + 4 > len(blob):
        return None
    vt_size, _table_size = struct.unpack_from('<HH', blob, vtable_off)
    if vt_size < 4 or vt_size > 256 or vt_size % 2 != 0:
        return None
    n_fields = (vt_size - 4) // 2
    if n_fields < 1 or vtable_off + vt_size > len(blob):
        return None
    return [
        struct.unpack_from('<H', blob, vtable_off + 4 + i * 2)[0]
        for i in range(n_fields)
    ]


def find_table_for_string_ref(blob: bytes, ref_off: int) -> tuple[int, list[int]] | None:
    """Given the offset of a uoffset_t field that points to a string, find the
    enclosing table's start offset and its vtable's field-offset list.

    Searches backward from ref_off for an int32 soffset_t that points to a valid
    vtable where one of the field offsets equals (ref_off - candidate_start).
    """
    # The string-uoffset field is at vtable_offset = (ref_off - table_start)
    # For Adobe transcript tables, this seen as 4 (Type B compact) or 8 (Type A with flags)
    for vt_off_for_str_field in (4, 8, 6, 12, 16, 20):
        candidate_start = ref_off - vt_off_for_str_field
        if candidate_start < 0 or candidate_start + 4 > len(blob):
            continue
        soffset = struct.unpack_from('<i', blob, candidate_start)[0]
        vtable_off = candidate_start - soffset
        if vtable_off < 0 or vtable_off >= len(blob):
            continue
        field_offsets = _read_vtable(blob, vtable_off)
        if field_offsets is None:
            continue
        if vt_off_for_str_field in field_offsets:
            return candidate_start, field_offsets
    return None


def parse_word_table(blob: bytes, table_start: int, field_offsets: list[int]) -> dict | None:
    """Read one word table given its start offset and vtable field-offset list.

    Returns dict with text, start, end, duration, confidence — or None if
    the table doesn't look like a word table.
    """
    sorted_fos = sorted(field_offsets)
    # Within a single table, fields are stored at the offsets listed in the vtable.
    # Adobe uses two known layouts:
    #   Type A: [6, 7, 8, 12, 16, 24]      → text@8,  conf@12, start@16, dur@24
    #   Type B: [4, 8, 12, 20]             → text@4,  conf@8,  start@12, dur@20
    #
    # General rule: the string-uoffset is the FIRST 4-byte field; confidence is
    # the next 4-byte field; start is the next 8-byte field; duration is the
    # next 8-byte field after that. Skip any 1-byte flag fields at low offsets.

    # Identify field widths by their offset gaps
    def width_at(offset_idx: int) -> int:
        """Width of the field at sorted_fos[offset_idx], inferred from next field offset."""
        if offset_idx + 1 < len(sorted_fos):
            return sorted_fos[offset_idx + 1] - sorted_fos[offset_idx]
        return 8  # last field — assume 8

    # Find the first 4-byte field (text uoffset)
    text_off = conf_off = start_off = dur_off = None
    for i, fo in enumerate(sorted_fos):
        w = width_at(i)
        if w == 4 and text_off is None:
            text_off = fo
        elif w == 4 and text_off is not None and conf_off is None:
            conf_off = fo
        elif w == 8 and start_off is None:
            start_off = fo
        elif w == 8 and start_off is not None and dur_off is None:
            dur_off = fo

    if text_off is None or start_off is None:
        return None

    # Read text
    text_field_abs = table_start + text_off
    if text_field_abs + 4 > len(blob):
        return None
    text_uoffset = struct.unpack_from('<I', blob, text_field_abs)[0]
    str_off = text_field_abs + text_uoffset
    if str_off + 4 > len(blob):
        return None
    str_len = struct.unpack_from('<I', blob, str_off)[0]
    if str_len < 1 or str_len > 100 or str_off + 4 + str_len + 1 > len(blob):
        return None
    text_bytes = blob[str_off + 4:str_off + 4 + str_len]
    if not all(0x20 <= b < 0x7f for b in text_bytes):
        return None
    text = text_bytes.decode('utf-8', errors='replace')

    # Read confidence
    confidence = 0.0
    if conf_off is not None and table_start + conf_off + 4 <= len(blob):
        confidence = struct.unpack_from('<f', blob, table_start + conf_off)[0]

    # Read start time (uint64 ticks)
    if table_start + start_off + 8 > len(blob):
        return None
    start_ticks = struct.unpack_from('<Q', blob, table_start + start_off)[0]
    start_s = start_ticks / TICKS_PER_SECOND

    # Read duration
    duration_s = 0.0
    if dur_off is not None and table_start + dur_off + 8 <= len(blob):
        duration_ticks = struct.unpack_from('<Q', blob, table_start + dur_off)[0]
        duration_s = duration_ticks / TICKS_PER_SECOND

    return {
        "text": text,
        "start": round(start_s, 4),
        "end": round(start_s + duration_s, 4),
        "duration": round(duration_s, 4),
        "confidence": round(confidence, 4),
    }


def parse_transcript_blob(blob: bytes) -> list[dict]:
    """Top-level: find every word table in the blob and return word records sorted by start time."""
    # Find every string. For each non-meta string, find its referencing table.
    strings = find_strings(blob)
    word_records = []
    seen_texts = []  # to dedupe word table re-discovery

    for s in strings:
        if s["text"] in META_STRINGS:
            continue
        # Find the field that points to this string.
        for f in range(0, len(blob) - 4):
            v = struct.unpack_from('<I', blob, f)[0]
            if 0 < v < len(blob) and (f + v) == s["offset"]:
                # Found a reference at offset f. Find the enclosing table.
                table_info = find_table_for_string_ref(blob, f)
                if table_info is None:
                    break
                table_start, field_offsets = table_info
                word = parse_word_table(blob, table_start, field_offsets)
                if word and word["text"] == s["text"]:
                    word_records.append(word)
                break  # one reference per string

    # Sort by start time (storage is reverse-temporal)
    word_records.sort(key=lambda w: w["start"])
    return word_records


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse Premiere V216 transcript FlatBuffers")
    ap.add_argument("source", type=Path)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of human-readable")
    ap.add_argument("--limit", type=int, default=0, help="show only first N words (0=all)")
    args = ap.parse_args()

    blob = load_blob(args.source)
    print(f"# Source: {args.source.name}", file=sys.stderr)
    print(f"# Blob size: {len(blob)} bytes", file=sys.stderr)

    words = parse_transcript_blob(blob)
    print(f"# Extracted {len(words)} word records", file=sys.stderr)

    show = words[:args.limit] if args.limit else words
    if args.json:
        print(json.dumps(show, indent=2))
    else:
        # Human readable
        print(f"\n{'idx':>4}  {'start':>8}  {'end':>8}  {'dur':>6}  {'conf':>5}  text")
        for i, w in enumerate(show):
            print(f"{i:>4}  {w['start']:>8.3f}  {w['end']:>8.3f}  {w['duration']:>6.3f}  {w['confidence']:>5.2f}  {w['text']!r}")


if __name__ == "__main__":
    main()
