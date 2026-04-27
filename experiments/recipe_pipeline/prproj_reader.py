#!/usr/bin/env python3
"""
prproj_reader.py — Extract full editorial fidelity from a Premiere .prproj.

Reads gzip-compressed XML, walks the ObjectRef/ObjectURef graph, and emits a
JSON dump per the schema in:
  Brain/Knowledge/API Integration/Premiere Effect Pattern Library — Recipe Corpus.md

Usage:
  python prproj_reader.py <input.prproj> [-o output.json]

Established context for this format lives in:
  Brain/Knowledge/API Integration/Premiere prproj Reverse Engineering Method.md
  Brain/Knowledge/API Integration/Premiere Speed Ramp via prproj.md
  Brain/Knowledge/API Integration/Premiere Export Format Fidelity.md
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TICKS_PER_SECOND = 254_016_000_000

# ClassIDs we care about (extend as new effects show up in the corpus).
CID_VIDEO_CLIP_TRACK_ITEM = "368b0406-29e3-4923-9fcd-094fbf9a1089"
CID_VIDEO_CLIP = "9308dbef-2440-4acb-9ab2-953b9a4e82ec"
CID_VIDEO_FILTER_COMPONENT = "d10da199-beea-4dd1-b941-ed3a78766d50"
CID_VIDEO_COMPONENT_CHAIN = "0970e08a-f58f-4108-b29a-1a717b8e12e2"
CID_VIDEO_TRACK_GROUP = "9e9abf7a-0918-49c2-91ae-991b5dde77bb"
CID_SEQUENCE = "6a15d903-8739-11d5-af2d-9b7855ad8974"
CID_VIDEO_CLIP_TRACK = "f68dcd81-8805-11d5-af2d-9bfa89d4ddd4"

# Media type UIDs (the <First> field in a Sequence's TrackGroups list).
MEDIA_TYPE_VIDEO = "228cda18-3625-4d2d-951e-348879e4ed93"
MEDIA_TYPE_AUDIO = "80b8e3d5-6dca-4195-aefb-cb5f407ab009"

CID_POINT_PARAM = "ca81d347-309b-44d2-acc7-1c572efb973c"
CID_TIME_PARAM = "278ae1f9-ab7b-4dff-a53c-21029a399a9d"

# Param-value flavors we've seen on VideoComponentParam (all carry scalar/bool):
#   fe47129e... = float, cc12343e... = bool, a4ff2d6e... = clamped float
PARAM_TAGS = {"PointComponentParam", "VideoComponentParam", "TimeComponentParam"}


def ticks_to_seconds(ticks: int | str) -> float:
    return int(ticks) / TICKS_PER_SECOND


def parse_value(raw: str):
    """Decode a single keyframe value field.

    PointComponentParam: 'X:Y' colon-separated pair (e.g. '0.5:0.5').
    VideoComponentParam: scalar like '50.', '100.', 'true', 'false'.
    TimeComponentParam:  source-time scalar.
    """
    raw = raw.strip()
    if raw == "true":
        return True
    if raw == "false":
        return False
    if ":" in raw:
        return [float(x) for x in raw.split(":")]
    if raw.endswith("."):
        raw = raw + "0"
    try:
        return float(raw)
    except ValueError:
        return raw


def parse_keyframe_field(s: str) -> dict:
    """Parse one comma-separated keyframe record.

    Layout: tick, value(s), interp, [trailing zeros / bezier handles ...]
    For PointComponentParam, value is 'X:Y' (one comma-field).
    For everything else, value is a single scalar field.
    """
    parts = s.split(",")
    if len(parts) < 3:
        return {"raw": s}
    tick = int(parts[0])
    value = parse_value(parts[1])
    try:
        interp = int(parts[2])
    except ValueError:
        interp = parts[2]
    return {
        "t": ticks_to_seconds(tick),
        "tick": tick,
        "value": value,
        "interp": interp,
    }


def parse_keyframes(raw: str) -> list[dict]:
    """Parse the semicolon-delimited Keyframes string."""
    if raw is None:
        return []
    out = []
    for chunk in raw.strip().rstrip(";").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        out.append(parse_keyframe_field(chunk))
    return out


def child_text(elem: ET.Element, tag: str) -> str | None:
    node = elem.find(tag)
    return node.text if node is not None else None


def child_int(elem: ET.Element, tag: str) -> int | None:
    txt = child_text(elem, tag)
    return int(txt) if txt is not None else None


def child_seconds(elem: ET.Element, tag: str) -> float | None:
    val = child_int(elem, tag)
    return ticks_to_seconds(val) if val is not None else None


class IdIndex:
    """ObjectID/ObjectUID lookup that handles non-unique numeric ObjectIDs.

    The numeric ObjectID space is scoped per file section, so the same ID can
    appear on multiple unrelated elements (e.g. ID 386 = TimecodeColumn AND
    VideoTrackGroup). UUIDs (`ObjectUID`) appear to be globally unique.

    Usage:
        idx = IdIndex(root)
        elem = idx.get_id(ref, expect=("VideoFilterComponent",))
        elem = idx.get_uid(uref, expect=("VideoClipTrack",))
    """

    def __init__(self, root: ET.Element) -> None:
        self.by_id: dict[str, list[ET.Element]] = {}
        self.by_uid: dict[str, list[ET.Element]] = {}
        for elem in root.iter():
            oid = elem.get("ObjectID")
            if oid:
                self.by_id.setdefault(oid, []).append(elem)
            uid = elem.get("ObjectUID")
            if uid:
                self.by_uid.setdefault(uid, []).append(elem)

    def get_id(self, ref: str | None, expect: tuple[str, ...] | None = None) -> ET.Element | None:
        if not ref:
            return None
        candidates = self.by_id.get(ref, [])
        if not candidates:
            return None
        if expect is None:
            return candidates[0]
        for c in candidates:
            if c.tag in expect:
                return c
        return None

    def get_uid(self, ref: str | None, expect: tuple[str, ...] | None = None) -> ET.Element | None:
        if not ref:
            return None
        candidates = self.by_uid.get(ref, [])
        if not candidates:
            return None
        if expect is None:
            return candidates[0]
        for c in candidates:
            if c.tag in expect:
                return c
        return None

    def collisions(self) -> dict:
        """Stats on numeric ObjectID collisions across element types."""
        n_keys = len(self.by_id)
        n_collisions = sum(1 for v in self.by_id.values() if len(v) > 1)
        return {
            "object_id_total": n_keys,
            "object_id_with_collisions": n_collisions,
            "object_uid_total": len(self.by_uid),
        }


# --- Resolvers --------------------------------------------------------------

def decode_mask_path_payload(raw: bytes) -> list[dict] | None:
    """Decode an AE.ADBE AEMask2 'Path' base64 payload into a vertex list.

    Format (verified 2026-04-26 against rectangle-mask A/B test):
      25-byte header (version flags + vertex count at offset 17)
      Per vertex: 24 bytes (6 LE float32: anchor_x, anchor_y, in_x, in_y, out_x, out_y)
                  + 4-byte separator (zeros) — but no separator before the first vertex
      1-byte trailer

    Coordinates are normalized 0..1 within the source frame.
    Sharp corners store identical (anchor, in, out) values; curved corners offset the tangent handles.
    """
    if len(raw) < 26:
        return None
    # Vertex count is the int32 at offset 17 (verified via 4-vertex rectangle test).
    try:
        n_verts = struct.unpack_from("<i", raw, 17)[0]
    except Exception:
        return None
    if not (1 <= n_verts <= 256):
        return None
    vertices: list[dict] = []
    cursor = 25
    for i in range(n_verts):
        if cursor + 24 > len(raw):
            return None
        floats = struct.unpack_from("<6f", raw, cursor)
        ax, ay, ix, iy, ox, oy = floats
        vertices.append({
            "anchor": [ax, ay],
            "in_tangent": [ix, iy],
            "out_tangent": [ox, oy],
            "is_corner": (ax == ix == ox) and (ay == iy == oy),
        })
        cursor += 24
        if i < n_verts - 1:
            cursor += 4  # inter-vertex separator
    return vertices


def decode_arb_payload(param_elem: ET.Element, owner_match_name: str | None = None,
                       param_name: str | None = None) -> dict | None:
    """Decode the base64 payload(s) inside an ArbVideoComponentParam.

    Three known payload kinds:
      - Lumetri "Blob": UTF-8 XML (`<Lumetri>...</Lumetri>`) — shader stack only.
        Numeric grade values live as named VideoComponentParams, NOT here.
      - Essential Graphics (AE.ADBE Capsule, name="TEXT"): UTF-16-LE JSON-ish with `textEditValue`.
      - AE.ADBE AEMask2 (name="Path"): packed LE float32 vertex list (see decode_mask_path_payload).
    """
    import base64 as _b64
    out = {}
    for sub in param_elem.iter():
        if sub.get("Encoding") != "base64" or not sub.text:
            continue
        try:
            raw = _b64.b64decode(sub.text.strip())
        except Exception:
            continue
        # Mask2 Path → vertex list
        if owner_match_name == "AE.ADBE AEMask2" and param_name == "Path":
            verts = decode_mask_path_payload(raw)
            if verts:
                out.setdefault("mask_vertices", verts)
                continue
        # Lumetri Blob → XML
        try:
            s = raw.decode("utf-8")
            if "<Lumetri>" in s:
                out.setdefault("lumetri_blob_xml", s)
                continue
        except UnicodeDecodeError:
            pass
        # Essential Graphics text → UTF-16-LE JSON-ish
        try:
            s = raw.decode("utf-16-le", errors="replace")
            import re as _re
            text_matches = _re.findall(r'"textEditValue"\s*:\s*"([^"]*)"', s)
            if text_matches:
                out.setdefault("text_edit_values", text_matches)
        except Exception:
            pass
    return out or None


def resolve_param(param_elem: ET.Element) -> dict:
    """Parse a *ComponentParam element into a structured dict."""
    out = {
        "tag": param_elem.tag,
        "object_id": param_elem.get("ObjectID"),
        "class_id": param_elem.get("ClassID"),
        "name": child_text(param_elem, "Name"),
        "parameter_id": child_text(param_elem, "ParameterID"),
    }
    start_kf = child_text(param_elem, "StartKeyframe")
    kfs = child_text(param_elem, "Keyframes")
    if start_kf is not None:
        out["start_keyframe"] = parse_keyframe_field(start_kf)
    if kfs is not None:
        kf_list = parse_keyframes(kfs)
        out["animated"] = True
        out["keyframes"] = kf_list
    else:
        out["animated"] = False
    for opt in ("LowerBound", "UpperBound", "UpperUIBound", "CurrentValue"):
        val = child_text(param_elem, opt)
        if val is not None:
            try:
                out[opt.lower()] = float(val)
            except ValueError:
                out[opt.lower()] = val
    return out


def resolve_param_with_owner(param_elem: ET.Element, owner_match: str | None) -> dict:
    """Like resolve_param but threads owner MatchName for ArbVideoComponentParam decoders."""
    out = resolve_param(param_elem)
    if param_elem.tag == "ArbVideoComponentParam":
        decoded = decode_arb_payload(param_elem, owner_match_name=owner_match,
                                      param_name=out.get("name"))
        if decoded:
            out["decoded"] = decoded
    return out


def resolve_filter_component(filter_elem: ET.Element, idx: IdIndex, origin: str = "timeline") -> dict:
    """Parse a VideoFilterComponent: params + recursively any SubComponents (e.g. masks)."""
    component = filter_elem.find("Component")
    display_name = child_text(component, "DisplayName") if component is not None else None
    instance_name = child_text(component, "InstanceName") if component is not None else None
    intrinsic_text = child_text(component, "Intrinsic") if component is not None else None
    intrinsic = (intrinsic_text or "").strip().lower() == "true"
    match_name = child_text(filter_elem, "MatchName")
    params_block = component.find("Params") if component is not None else None
    params: list[dict] = []
    if params_block is not None:
        for p in params_block.findall("Param"):
            ref = p.get("ObjectRef")
            target = idx.get_id(ref, expect=("PointComponentParam", "VideoComponentParam",
                                              "TimeComponentParam", "ArbVideoComponentParam"))
            entry = {"index": int(p.get("Index", -1)), "object_ref": ref}
            if target is not None and target.tag in PARAM_TAGS | {"ArbVideoComponentParam"}:
                entry.update(resolve_param_with_owner(target, match_name))
            params.append(entry)

    # Nested SubComponents — masks applied to this effect.
    sub_components: list[dict] = []
    sub_block = filter_elem.find("SubComponents")
    if sub_block is not None:
        for sc in sub_block.findall("SubComponent"):
            ref = sc.get("ObjectRef")
            target = idx.get_id(ref, expect=("VideoFilterComponent",))
            if target is not None:
                sub_components.append(resolve_filter_component(target, idx, origin="sub_component"))

    return {
        "object_id": filter_elem.get("ObjectID"),
        "class_id": filter_elem.get("ClassID"),
        "origin": origin,
        "display_name": display_name,
        "instance_name": instance_name,
        "intrinsic": intrinsic,
        "match_name": match_name,
        "video_filter_type": child_text(filter_elem, "VideoFilterType"),
        "params": params,
        "sub_components": sub_components,
    }


def resolve_clip_track_item(item_elem: ET.Element, idx: IdIndex) -> dict:
    """Parse a VideoClipTrackItem: timeline span + components + source clip."""
    cti = item_elem.find("ClipTrackItem")
    track_item = cti.find("TrackItem") if cti is not None else None

    start_seconds = child_seconds(track_item, "Start") if track_item is not None else None
    end_seconds = child_seconds(track_item, "End") if track_item is not None else None

    # SubClip → VideoClip (the SubClip ObjectRef points to the VideoClip directly).
    subclip_ref = None
    sub_clip = cti.find("SubClip") if cti is not None else None
    if sub_clip is not None:
        subclip_ref = sub_clip.get("ObjectRef")
    video_clip_elem = idx.get_id(subclip_ref, expect=("VideoClip", "SubClip"))
    # Some prproj versions wrap the VideoClip inside a SubClip element first.
    if video_clip_elem is not None and video_clip_elem.tag == "SubClip":
        sc_inner = video_clip_elem.find("Clip")
        if sc_inner is not None:
            ref2 = sc_inner.get("ObjectRef")
            resolved = idx.get_id(ref2, expect=("VideoClip",))
            if resolved is not None:
                video_clip_elem = resolved
    is_adjustment = False
    source_ref = None
    in_point_ticks = None
    out_point_ticks = None
    speed_ramp = None
    playback_speed = None
    if video_clip_elem is not None and video_clip_elem.tag == "VideoClip":
        adj = video_clip_elem.find("AdjustmentLayer")
        is_adjustment = (adj is not None and (adj.text or "").strip().lower() == "true")
        clip_inner = video_clip_elem.find("Clip")
        if clip_inner is not None:
            src = clip_inner.find("Source")
            if src is not None:
                source_ref = src.get("ObjectRef")
            in_point_ticks = child_int(clip_inner, "InPoint")
            out_point_ticks = child_int(clip_inner, "OutPoint")
            ps = child_text(clip_inner, "PlaybackSpeed")
            if ps is not None:
                try:
                    playback_speed = float(ps)
                except ValueError:
                    pass
            tr = clip_inner.find("TimeRemapping")
            if tr is not None:
                tr_target = idx.get_id(tr.get("ObjectRef"), expect=("TimeRemapping",))
                if tr_target is not None:
                    kf_ref_node = tr_target.find("Keyframes")
                    if kf_ref_node is not None:
                        tcp = idx.get_id(kf_ref_node.get("ObjectRef"), expect=("TimeComponentParam",))
                        if tcp is not None:
                            speed_ramp = resolve_param(tcp)

    def walk_chain(chain_ref: str | None, origin: str) -> list[dict]:
        chain_elem = idx.get_id(chain_ref, expect=("VideoComponentChain",))
        out: list[dict] = []
        if chain_elem is None:
            return out
        cc = chain_elem.find("ComponentChain")
        if cc is None:
            return out
        comp_list = cc.find("Components")
        if comp_list is None:
            return out
        for c in comp_list.findall("Component"):
            ref = c.get("ObjectRef")
            target = idx.get_id(ref, expect=("VideoFilterComponent",))
            if target is not None:
                out.append(resolve_filter_component(target, idx, origin=origin))
        return out

    # Primary timeline chain.
    chain_ref = None
    owner = cti.find("ComponentOwner") if cti is not None else None
    if owner is not None:
        comps = owner.find("Components")
        if comps is not None:
            chain_ref = comps.get("ObjectRef")
    filter_components: list[dict] = walk_chain(chain_ref, origin="timeline")

    # Selection chain — Premiere puts mask effects here when added via the Effects panel
    # selection workflow rather than as ordinary chain entries.
    sel = item_elem.find("SelectionComponents")
    if sel is not None:
        filter_components.extend(walk_chain(sel.get("ObjectRef"), origin="selection"))

    # Normalize keyframe times: subtract source InPoint to get clip-relative seconds,
    # then add the clip's timeline start to get the absolute timeline time. Recurses
    # into sub_components so masks and other nested effects get the same normalization.
    if in_point_ticks is not None and start_seconds is not None:
        in_point_seconds = ticks_to_seconds(in_point_ticks)

        def normalize(fc_list: list[dict]) -> None:
            for fc in fc_list:
                for p in fc["params"]:
                    for kf in p.get("keyframes", []):
                        if "t" not in kf:
                            continue  # malformed keyframe (parser fallback)
                        kf["clip_t"] = round(kf["t"] - in_point_seconds, 6)
                        kf["timeline_t"] = round(start_seconds + kf["clip_t"], 6)
                    sk = p.get("start_keyframe")
                    if sk and "t" in sk:
                        sk["clip_t"] = round(sk["t"] - in_point_seconds, 6)
                normalize(fc.get("sub_components", []))

        normalize(filter_components)

    # Normalize speed ramp keyframes too (same in_point convention)
    if speed_ramp is not None and in_point_ticks is not None and start_seconds is not None:
        in_point_seconds_local = ticks_to_seconds(in_point_ticks)
        for kf in speed_ramp.get("keyframes", []):
            if "t" in kf:
                kf["clip_t"] = round(kf["t"] - in_point_seconds_local, 6)
                kf["timeline_t"] = round(start_seconds + kf["clip_t"], 6)
        sk = speed_ramp.get("start_keyframe")
        if sk and "t" in sk:
            sk["clip_t"] = round(sk["t"] - in_point_seconds_local, 6)

    return {
        "track_item_object_id": item_elem.get("ObjectID"),
        "video_clip_object_id": video_clip_elem.get("ObjectID") if video_clip_elem is not None else None,
        "in_seconds": start_seconds,
        "out_seconds": end_seconds,
        "duration_seconds": (end_seconds - start_seconds) if (start_seconds is not None and end_seconds is not None) else None,
        "is_adjustment_layer": is_adjustment,
        "source_object_ref": source_ref,
        "source_in_point_ticks": in_point_ticks,
        "source_out_point_ticks": out_point_ticks,
        "playback_speed": playback_speed,
        "speed_ramp": speed_ramp,
        "filter_components": filter_components,
    }


def resolve_track(track_elem: ET.Element, idx: IdIndex) -> dict:
    """Parse a VideoClipTrack: list of clip track items."""
    inner_track = track_elem.find("ClipTrack/Track")
    track_index = child_int(inner_track, "Index") if inner_track is not None else None

    clip_items_block = track_elem.find("ClipTrack/ClipItems/TrackItems")
    items: list[dict] = []
    if clip_items_block is not None:
        for ti in clip_items_block.findall("TrackItem"):
            ref = ti.get("ObjectRef")
            target = idx.get_id(ref, expect=("VideoClipTrackItem",))
            if target is not None:
                resolved = resolve_clip_track_item(target, idx)
                resolved["track_item_index"] = int(ti.get("Index", -1))
                items.append(resolved)
    return {
        "object_uid": track_elem.get("ObjectUID"),
        "track_index": track_index,
        "label": f"V{(track_index or 0) + 1}",
        "clip_items": items,
    }


def find_video_track_group(seq_elem: ET.Element, idx: IdIndex) -> ET.Element | None:
    """Resolve the Sequence's video TrackGroup via the TrackGroups/TrackGroup/Second chain."""
    tgs = seq_elem.find("TrackGroups")
    if tgs is None:
        return None
    for tg in tgs.findall("TrackGroup"):
        first = tg.find("First")
        if first is None or (first.text or "").strip() != MEDIA_TYPE_VIDEO:
            continue
        second = tg.find("Second")
        if second is None:
            continue
        ref = second.get("ObjectRef")
        target = idx.get_id(ref, expect=("VideoTrackGroup",))
        if target is not None:
            return target
    return None


def resolve_sequence(seq_elem: ET.Element, idx: IdIndex) -> dict:
    """Parse a Sequence: resolve its video TrackGroup, walk tracks → clip items."""
    name = child_text(seq_elem, "Name")

    vtg = find_video_track_group(seq_elem, idx)
    tracks: list[dict] = []
    if vtg is not None:
        tracks_block = vtg.find("TrackGroup/Tracks")
        if tracks_block is not None:
            for t in tracks_block.findall("Track"):
                tref = t.get("ObjectURef")
                track_target = idx.get_uid(tref, expect=("VideoClipTrack",))
                if track_target is not None:
                    tracks.append(resolve_track(track_target, idx))

    return {
        "object_uid": seq_elem.get("ObjectUID"),
        "name": name,
        "tracks": tracks,
    }


# --- Top-level entry --------------------------------------------------------

def find_primary_sequence(root: ET.Element, idx: IdIndex) -> ET.Element | None:
    """Return the sequence with the most VideoClipTrackItems referenced."""
    best, best_count = None, -1
    for seq in root.iter("Sequence"):
        if seq.get("ClassID") != CID_SEQUENCE:
            continue
        vtg = find_video_track_group(seq, idx)
        count = 0
        if vtg is not None:
            tracks_block = vtg.find("TrackGroup/Tracks")
            if tracks_block is not None:
                for t in tracks_block.findall("Track"):
                    track = idx.get_uid(t.get("ObjectURef"), expect=("VideoClipTrack",))
                    if track is None:
                        continue
                    items = track.find("ClipTrack/ClipItems/TrackItems")
                    if items is not None:
                        count += sum(1 for _ in items.findall("TrackItem"))
        if count > best_count:
            best, best_count = seq, count
    return best


def read_prproj(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        xml_text = f.read()
    root = ET.fromstring(xml_text)

    idx = IdIndex(root)

    primary = find_primary_sequence(root, idx)
    if primary is None:
        raise RuntimeError("No Sequence found in prproj")

    sequence = resolve_sequence(primary, idx)

    # Compute timeline duration from max clip-item out-time across all tracks.
    max_out = 0.0
    for t in sequence["tracks"]:
        for ci in t["clip_items"]:
            if ci.get("out_seconds") is not None:
                max_out = max(max_out, ci["out_seconds"])

    # Collect distinct effect MatchNames + ClassIDs (recursive into sub_components).
    effect_match_names: dict[str, int] = {}
    param_class_ids: dict[str, str] = {}

    def visit(fc_list: list[dict]) -> None:
        for fc in fc_list:
            mn = fc.get("match_name") or fc.get("display_name") or fc["class_id"]
            effect_match_names[mn] = effect_match_names.get(mn, 0) + 1
            for p in fc["params"]:
                cid = p.get("class_id")
                if cid:
                    param_class_ids.setdefault(cid, p.get("tag") or "")
            visit(fc.get("sub_components", []))

    for t in sequence["tracks"]:
        for ci in t["clip_items"]:
            visit(ci["filter_components"])

    return {
        "source_path": str(path),
        "decompressed_xml_bytes": len(xml_text),
        "id_index_stats": idx.collisions(),
        "primary_sequence": sequence,
        "duration_seconds": round(max_out, 6),
        "encountered_effect_match_names": effect_match_names,
        "encountered_param_class_ids": param_class_ids,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="Path to .prproj")
    ap.add_argument("-o", "--output", help="Output JSON path (default: prproj_dumps/<basename>_effects.json)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if args.output:
        out_path = Path(args.output)
    else:
        out_dir = Path(__file__).parent / "prproj_dumps"
        out_dir.mkdir(exist_ok=True)
        slug = re.sub(r"\W+", "_", in_path.stem.lower()).strip("_")
        out_path = out_dir / f"{slug}_effects.json"

    print(f"Reading {in_path}")
    data = read_prproj(in_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {out_path}")

    # Brief summary to stdout.
    seq = data["primary_sequence"]
    print(f"\nSequence: {seq.get('name')}")
    print(f"Duration: {data['duration_seconds']:.2f}s")
    print(f"Tracks: {len(seq['tracks'])}")
    total_items = sum(len(t["clip_items"]) for t in seq["tracks"])
    adj_items = sum(1 for t in seq["tracks"] for ci in t["clip_items"] if ci["is_adjustment_layer"])
    print(f"Clip items: {total_items} ({adj_items} adjustment-layer)")
    print(f"Effect types encountered (MatchName → count):")
    for mn, count in sorted(data["encountered_effect_match_names"].items(), key=lambda x: -x[1]):
        print(f"  {mn}: {count}")
    print(f"Param ClassIDs encountered: {len(data['encountered_param_class_ids'])}")
    for cid, tag in data["encountered_param_class_ids"].items():
        print(f"  {cid}  {tag}")


if __name__ == "__main__":
    sys.exit(main())
