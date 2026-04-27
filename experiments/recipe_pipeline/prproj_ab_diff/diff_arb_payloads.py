#!/usr/bin/env python3
"""
diff_arb_payloads.py — A/B diff helper for decoding ArbVideoComponentParam blobs.

Use this to surface how Premiere encodes effects whose params live as opaque
base64 payloads (Lumetri Color, Essential Graphics text content, Mask2 shape
vertices, etc.).

Workflow (per the established reverse-engineering method):
  1. In Premiere, save TWO copies of a minimal project that differ ONLY by the
     attribute under investigation (e.g. Saturation = 0 vs Saturation = 50).
  2. Run:  python diff_arb_payloads.py project_a.prproj project_b.prproj
  3. The script decompresses both, walks every ArbVideoComponentParam, decodes
     its base64 payload, and reports byte-level diffs between A and B for any
     param where the payload changed.

Output: a per-param diff report (offset, A bytes, B bytes, ASCII/UTF-16
interpretation) so you can identify which bytes encode which attribute.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def decompress(path: Path) -> str:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return f.read()


def collect_arb_params(xml_text: str) -> dict[str, dict]:
    """Map each ArbVideoComponentParam by ObjectID → {owner_match, owner_param_index, name, payloads}."""
    root = ET.fromstring(xml_text)

    # Reverse-index: for every VideoFilterComponent, record which ObjectRefs its
    # Params point to and the param index. ArbVideoComponentParams are siblings
    # of their owning VFC in the XML, only linked via ObjectRef in <Params>.
    param_owner: dict[str, tuple[str | None, int]] = {}
    for vfc in root.iter("VideoFilterComponent"):
        mn = vfc.find("MatchName")
        owner_match = mn.text if mn is not None else None
        params_block = vfc.find("Component/Params")
        if params_block is None:
            continue
        for p in params_block.findall("Param"):
            ref = p.get("ObjectRef")
            if ref:
                param_owner[ref] = (owner_match, int(p.get("Index", -1)))

    out: dict[str, dict] = {}
    for elem in root.iter("ArbVideoComponentParam"):
        oid = elem.get("ObjectID") or ""
        if not oid:
            continue
        owner_match, owner_idx = param_owner.get(oid, (None, -1))

        payloads: list[tuple[str, bytes]] = []
        for sub in elem.iter():
            enc = sub.get("Encoding")
            if enc == "base64" and sub.text:
                try:
                    payloads.append((sub.tag, base64.b64decode(sub.text.strip())))
                except Exception as e:
                    payloads.append((sub.tag, f"<decode-error: {e}>".encode()))
        name_node = elem.find("Name")
        out[oid] = {
            "name": name_node.text if name_node is not None else None,
            "owner_match": owner_match,
            "owner_param_index": owner_idx,
            "payloads": payloads,
        }
    return out


def first_diff_offset(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else -1


def hex_window(data: bytes, offset: int, span: int = 32) -> str:
    lo = max(0, offset - span // 2)
    hi = min(len(data), lo + span)
    return data[lo:hi].hex(" ")


def utf16_window(data: bytes, offset: int, span: int = 64) -> str:
    lo = max(0, offset - span // 2)
    hi = min(len(data), lo + span)
    snippet = data[lo:hi]
    try:
        # UTF-16-LE is what Premiere uses for text in MOGRT payloads
        return snippet.decode("utf-16-le", errors="replace").replace("\x00", "·")
    except Exception:
        return repr(snippet)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project_a", help="First .prproj")
    ap.add_argument("project_b", help="Second .prproj")
    ap.add_argument("--match-name", help="Filter to ArbVideoComponentParams owned by this effect MatchName (e.g. 'AE.ADBE Lumetri', 'AE.ADBE Capsule')")
    ap.add_argument("--max-diffs", type=int, default=20, help="Cap on number of differing params to report")
    args = ap.parse_args()

    a = collect_arb_params(decompress(Path(args.project_a)))
    b = collect_arb_params(decompress(Path(args.project_b)))

    print(f"A: {len(a)} ArbVideoComponentParam entries")
    print(f"B: {len(b)} ArbVideoComponentParam entries")

    # We don't expect ObjectIDs to be stable across saves — match by
    # (owner_match, name, payload-tag, position-within-effect) instead.
    def fingerprint(entry: dict) -> tuple:
        return (
            entry["owner_match"],
            entry["owner_param_index"],
            entry["name"],
            tuple(tag for tag, _ in entry["payloads"]),
        )

    by_fp_a: dict[tuple, list[tuple[str, dict]]] = {}
    by_fp_b: dict[tuple, list[tuple[str, dict]]] = {}
    for oid, e in a.items():
        by_fp_a.setdefault(fingerprint(e), []).append((oid, e))
    for oid, e in b.items():
        by_fp_b.setdefault(fingerprint(e), []).append((oid, e))

    diffs_reported = 0
    for fp, a_entries in by_fp_a.items():
        if args.match_name and fp[0] != args.match_name:
            continue
        b_entries = by_fp_b.get(fp, [])
        if not b_entries:
            continue
        # Pair by index within the same fingerprint bucket.
        for (a_oid, a_entry), (b_oid, b_entry) in zip(a_entries, b_entries):
            for (a_tag, a_bytes), (b_tag, b_bytes) in zip(a_entry["payloads"], b_entry["payloads"]):
                if a_bytes == b_bytes:
                    continue
                off = first_diff_offset(a_bytes, b_bytes)
                if diffs_reported >= args.max_diffs:
                    print(f"\n... (truncated at {args.max_diffs} diffs; pass --max-diffs to see more)")
                    return
                diffs_reported += 1
                print(f"\n--- DIFF #{diffs_reported}")
                print(f"  Owner MatchName: {fp[0]}")
                print(f"  Param Index: {fp[1]}")
                print(f"  Param Name: {fp[2]!r}")
                print(f"  Payload tag: {a_tag}")
                print(f"  Lengths: A={len(a_bytes)}  B={len(b_bytes)}  first_diff_offset={off}")
                print(f"  A hex @ off:  {hex_window(a_bytes, off)}")
                print(f"  B hex @ off:  {hex_window(b_bytes, off)}")
                print(f"  A utf-16 @ off:  {utf16_window(a_bytes, off)!r}")
                print(f"  B utf-16 @ off:  {utf16_window(b_bytes, off)!r}")

    if diffs_reported == 0:
        print("\nNo differing payloads found. Possible causes:")
        print("  - The change wasn't saved into the .prproj (e.g. opened but not modified)")
        print("  - The attribute lives outside ArbVideoComponentParam (try grep on the decompressed XML)")
        print("  - --match-name filter excluded the right effect")
    else:
        print(f"\nTotal diffs: {diffs_reported}")


if __name__ == "__main__":
    sys.exit(main())
