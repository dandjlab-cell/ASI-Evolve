#!/usr/bin/env python3
"""
manifest_to_prproj.py — Round 1 prproj-direct writer.

Takes a recipe manifest (e.g. basil_pesto_manifest.json) and emits a Premiere
.prproj with bins, media imports, an empty sequence at the manifest's fps and
resolution, and V1 clips placed at the manifest's timeline positions cutting
from the manifest's source ranges.

Round 1 scope: V1 only. No V2, no MOGRTs, no effects. See plan at
Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md §"Round 1".

Approach: template-mutation.
  - Load SEQ_FLAT.prproj as the seed (full project boilerplate + 1 working V1
    clip in an "Sequence 01" sequence).
  - Strip the existing single VideoClipTrackItem on V1 + its template assets.
  - Append fresh media-chain blocks for every unique V1 source.
  - Append fresh VideoClipTrackItem + subclip VideoClip per timeline entry.
  - Build 2 bins (1_CUTS, 2_FOOTAGE) under root; reparent items.
  - Renumber all assigned IDs to avoid collision with the seed.
  - Gzip and write.

Verification:
  - python prproj_reader.py <out.prproj> must succeed.
  - Open in Premiere: bins visible, sequence at right fps/res, V1 clips on
    timeline matching manifest within 1 frame.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import xml.etree.ElementTree as ET

# Support both module and script invocation:
#   python -m experiments.recipe_pipeline.manifest_to_prproj.manifest_to_prproj …
#   python experiments/recipe_pipeline/manifest_to_prproj/manifest_to_prproj.py …
# When invoked as a script, __package__ is empty and sibling modules need a
# path-based import. Prepending the package directory to sys.path makes both
# work without conditional imports.
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "manifest_to_prproj"  # type: ignore[name-defined]

from .core import (  # noqa: E402
    CID_BIN_PROJECT_ITEM,
    CID_CLIP_PROJECT_ITEM,
    CID_MASTER_CLIP,
    CID_MEDIA,
    CID_VIDEO_STREAM,
    CID_VIDEO_MEDIA_SOURCE,
    CID_CLIP_LOGGING_INFO,
    CID_VIDEO_CLIP,
    CID_VIDEO_CLIP_TRACK_ITEM,
    CID_CLIP_CHANNEL_GROUP_VECTOR_SERIALIZER,
    CID_MARKERS,
    CID_SUB_CLIP,
    CID_VIDEO_COMPONENT_CHAIN,
    CID_VIDEO_FILTER_COMPONENT,
    CID_VIDEO_COMPONENT_PARAM,
    CID_VIDEO_COMPONENT_PARAM_BOOL,
    CID_VIDEO_COMPONENT_PARAM_CLAMPED,
    CID_POINT_COMPONENT_PARAM,
    TICKS_PER_SECOND,
    START_KEYFRAME_TICK,
    FRAMERATE_TICKS_23_976,
    timecode_to_seconds,
    seconds_to_ticks,
    start_keyframe as _start_keyframe,
)
from .core.seed_loader import (  # noqa: E402
    SEED_PRPROJ,
    OUTPUTS_ROOT,
    IdFactory,
    parse_xml,
    find_max_object_id,
    collect_used_uids,
    find_premiere_data,
)
from .core.serializer import (  # noqa: E402
    write_prproj_bytes,
    integrity_check,
)
from .core.bins import (  # noqa: E402
    build_bin,
    find_root_project_item,
    find_v1_clip_track,
    find_existing_vcti,
    replace_root_bin_items,
    replace_v1_clip_items,
    remove_existing_vcti,
    classify_root_clip_project_item,
)
from .core.media_chain import (  # noqa: E402
    MediaMeta,
    ffprobe,
    build_media_chain,
)

logger = logging.getLogger("manifest_to_prproj")


def _slugify(s: str) -> str:
    """Filesystem-safe lowercase slug. 'Basil Pesto' -> 'basil_pesto'."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "recipe"


# ──────────────────────────────────────────────────────────────────────────
# Element builders — each emits a fresh subtree with new IDs/UIDs
# ──────────────────────────────────────────────────────────────────────────


def build_motion_filter(scale_pct: float, ids: IdFactory) -> tuple[ET.Element, list[ET.Element], str]:
    """Build a Motion VideoFilterComponent with custom Scale + default everything else.

    Returns (filter_element, param_elements, filter_object_id). All elements
    must be appended to PremiereData root.

    Param layout (from steak_tacos reference, IDs 924-934):
      0 Position (point)        — default 0.5,0.5
      1 Scale (scalar)           — set per call
      2 Scale Width (scalar)     — default 100 (ignored when uniform=true)
      3 Uniform Scale (bool)     — true
      4 Rotation (scalar)        — default 0
      5 Anchor Point (point)     — default 0.5,0.5
      6 Anti-flicker (clamped)   — default 0
      7 Crop Left (scalar)       — default 0
      8 Crop Top (scalar)        — default 0
      9 Crop Right (scalar)      — default 0
      10 Crop Bottom (scalar)    — default 0
    """
    filter_id = ids.fresh_id()
    pids = [ids.fresh_id() for _ in range(11)]

    elements: list[ET.Element] = []

    # The Motion VideoFilterComponent
    f = ET.Element("VideoFilterComponent", {
        "ObjectID": filter_id,
        "ClassID": CID_VIDEO_FILTER_COMPONENT,
        "Version": "9",
    })
    comp = ET.SubElement(f, "Component", {"Version": "7"})
    params = ET.SubElement(comp, "Params", {"Version": "1"})
    for i, pid in enumerate(pids):
        ET.SubElement(params, "Param", {"Index": str(i), "ObjectRef": pid})
    ET.SubElement(comp, "ID").text = "1"
    ET.SubElement(comp, "DisplayName").text = "Motion"
    ET.SubElement(comp, "Intrinsic").text = "true"
    # PremiereFilterPrivateData copied from steak_tacos's Motion (the "ARM=" blob is harmless)
    pfpd = ET.SubElement(f, "PremiereFilterPrivateData", {
        "Encoding": "base64",
        "BinaryHash": "4b0b6857-bf41-31a9-a7e7-0ca80000000e",
    })
    pfpd.text = "ARM="
    ET.SubElement(f, "MatchName").text = "AE.ADBE Motion"
    ET.SubElement(f, "VideoFilterType").text = "2"
    elements.append(f)

    # The 11 params
    def make_scalar_param(pid: str, name: str, parameter_id: int, start_value: str,
                           upper_ui: str, lower: str, upper: str) -> ET.Element:
        p = ET.Element("VideoComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_VIDEO_COMPONENT_PARAM,
            "Version": "10",
        })
        ET.SubElement(p, "Name").text = name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "UpperUIBound").text = upper_ui
        ET.SubElement(p, "StartKeyframe").text = _start_keyframe(start_value)
        ET.SubElement(p, "LowerBound").text = lower
        ET.SubElement(p, "UpperBound").text = upper
        return p

    def make_point_param(pid: str, name: str, parameter_id: int, x: float, y: float) -> ET.Element:
        p = ET.Element("PointComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_POINT_COMPONENT_PARAM,
            "Version": "4",
        })
        ET.SubElement(p, "Name").text = name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "StartKeyframe").text = (
            f"{START_KEYFRAME_TICK},{x}:{y},0,0,0,0,0,0,5,4,0,0,0,0"
        )
        return p

    def make_bool_param(pid: str, parameter_id: int, value: bool) -> ET.Element:
        p = ET.Element("VideoComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_VIDEO_COMPONENT_PARAM_BOOL,
            "Version": "10",
        })
        ET.SubElement(p, "Name")  # empty name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "StartKeyframe").text = _start_keyframe("true" if value else "false")
        return p

    def make_clamped_param(pid: str, name: str, parameter_id: int, start_value: str) -> ET.Element:
        p = ET.Element("VideoComponentParam", {
            "ObjectID": pid,
            "ClassID": CID_VIDEO_COMPONENT_PARAM_CLAMPED,
            "Version": "10",
        })
        ET.SubElement(p, "Name").text = name
        ET.SubElement(p, "ParameterID").text = str(parameter_id)
        ET.SubElement(p, "StartKeyframe").text = _start_keyframe(start_value)
        return p

    elements.append(make_point_param(pids[0], "Position", 1, 0.5, 0.5))
    elements.append(make_scalar_param(pids[1], "Scale", 2, f"{scale_pct}.", "200", "0", "10000"))
    elements.append(make_scalar_param(pids[2], "Scale Width", 3, "100.", "200", "0", "10000"))
    elements.append(make_bool_param(pids[3], 4, True))
    elements.append(make_scalar_param(pids[4], "Rotation", 5, "0.", "360", "-3.40282346638528860e+38", "3.40282346638528860e+38"))
    elements.append(make_point_param(pids[5], "Anchor Point", 6, 0.5, 0.5))
    elements.append(make_clamped_param(pids[6], "Anti-flicker Filter", 7, "0."))
    elements.append(make_scalar_param(pids[7], "Crop Left", 8, "0.", "100", "0", "100"))
    elements.append(make_scalar_param(pids[8], "Crop Top", 9, "0.", "100", "0", "100"))
    elements.append(make_scalar_param(pids[9], "Crop Right", 10, "0.", "100", "0", "100"))
    elements.append(make_scalar_param(pids[10], "Crop Bottom", 11, "0.", "100", "0", "100"))

    return f, elements, filter_id


def build_clip_placement(
    media_chain: dict,
    timeline_in_ticks: int,
    timeline_out_ticks: int,
    source_in_ticks: int,
    source_out_ticks: int,
    ids: IdFactory,
    playback_speed: Optional[float] = None,
    motion_scale_pct: Optional[float] = None,
) -> dict:
    """Build VideoClipTrackItem + SubClip element + subclip VideoClip for one placement.

    Reference graph (per SEQ_FLAT):
      VideoClipTrackItem
        └─ SubClip ObjectRef ──▶ SubClip element (own ClassID)
                                  ├─ Clip ObjectRef ──▶ VideoClip (with InPoint/OutPoint)
                                  └─ MasterClip ObjectURef ──▶ MasterClip
    """
    vcti_id = ids.fresh_id()
    subclip_element_id = ids.fresh_id()
    video_clip_id = ids.fresh_id()
    components_id = ids.fresh_id()

    elements: list[ET.Element] = []

    # 1. VideoClipTrackItem
    vcti = ET.Element("VideoClipTrackItem", {
        "ObjectID": vcti_id,
        "ClassID": CID_VIDEO_CLIP_TRACK_ITEM,
        "Version": "8",
    })
    cti = ET.SubElement(vcti, "ClipTrackItem", {"Version": "8"})
    co = ET.SubElement(cti, "ComponentOwner", {"Version": "1"})
    ET.SubElement(co, "Components", {"ObjectRef": components_id})
    ti = ET.SubElement(cti, "TrackItem", {"Version": "4"})
    ET.SubElement(ti, "Start").text = str(timeline_in_ticks)
    ET.SubElement(ti, "End").text = str(timeline_out_ticks)
    ET.SubElement(cti, "SubClip", {"ObjectRef": subclip_element_id})
    ET.SubElement(vcti, "PixelAspectRatio").text = "1,1"
    ET.SubElement(vcti, "ToneMapSettings").text = '{"peak":-1,"version":3}'
    ET.SubElement(vcti, "FrameRect").text = "0,0,1920,1080"
    elements.append(vcti)

    # 2. SubClip element (the indirection layer between VCTI and VideoClip)
    sub = ET.Element("SubClip", {
        "ObjectID": subclip_element_id,
        "ClassID": CID_SUB_CLIP,
        "Version": "6",
    })
    ET.SubElement(sub, "Clip", {"ObjectRef": video_clip_id})
    ET.SubElement(sub, "MasterClip", {"ObjectURef": media_chain["master_clip_uid"]})
    ET.SubElement(sub, "Name").text = media_chain["name"]
    ET.SubElement(sub, "OrigChGrp").text = "0"
    elements.append(sub)

    # 3. VideoClip (the subclip on timeline; has InPoint/OutPoint into the source)
    vc = ET.Element("VideoClip", {
        "ObjectID": video_clip_id,
        "ClassID": CID_VIDEO_CLIP,
        "Version": "11",
    })
    clip = ET.SubElement(vc, "Clip", {"Version": "18"})
    cnode = ET.SubElement(clip, "Node", {"Version": "1"})
    cprops = ET.SubElement(cnode, "Properties", {"Version": "1"})
    ET.SubElement(cprops, "asl.clip.label.name").text = "BE.Prefs.LabelColors.0"
    ET.SubElement(cprops, "asl.clip.label.color").text = "11405886"
    mowner = ET.SubElement(clip, "MarkerOwner", {"Version": "1"})
    ET.SubElement(mowner, "Markers", {"ObjectRef": media_chain["markers_id"]})
    ET.SubElement(clip, "Source", {"ObjectRef": media_chain["video_media_source_id"]})
    ET.SubElement(clip, "InPoint").text = str(source_in_ticks)
    ET.SubElement(clip, "OutPoint").text = str(source_out_ticks)
    if playback_speed is not None and abs(playback_speed - 1.0) > 1e-6:
        # Recompute from actual source/timeline tick ranges for tick-exact ratio.
        # This guarantees Premiere's internal "natural duration on timeline"
        # ((OutPoint-InPoint)/PlaybackSpeed) matches End-Start exactly — otherwise
        # any rounding shows as zebra bars at the clip's tail edge.
        tl_dur_ticks = timeline_out_ticks - timeline_in_ticks
        src_dur_ticks = source_out_ticks - source_in_ticks
        if tl_dur_ticks > 0:
            playback_speed = src_dur_ticks / tl_dur_ticks
        # Use full Python float precision (~17 digits) — `:.6f` truncates to ~µs.
        ET.SubElement(clip, "PlaybackSpeed").text = repr(playback_speed)
    ET.SubElement(clip, "ClipID").text = ids.fresh_uid()
    elements.append(vc)

    # 4. VideoComponentChain (target of VCTI's Components ObjectRef).
    # Required even when the clip carries no effects — Premiere silently
    # refuses to render the timeline if this dangles.
    vcc = ET.Element("VideoComponentChain", {
        "ObjectID": components_id,
        "ClassID": CID_VIDEO_COMPONENT_CHAIN,
        "Version": "3",
    })

    if motion_scale_pct is not None and abs(motion_scale_pct - 100.0) > 1e-6:
        # Custom Motion override: emit a full Motion VideoFilterComponent + 11 params.
        _, motion_elements, motion_filter_id = build_motion_filter(motion_scale_pct, ids)
        elements.extend(motion_elements)
        # Chain shape matches steak_tacos's custom-motion clips: no DefaultMotion
        # field, no MZ.ComponentChain props, just a Components list with the filter.
        ET.SubElement(vcc, "DefaultOpacity").text = "true"
        ET.SubElement(vcc, "DefaultOpacityComponentID").text = "2"
        cc = ET.SubElement(vcc, "ComponentChain", {"Version": "3"})
        comps = ET.SubElement(cc, "Components", {"Version": "1"})
        ET.SubElement(comps, "Component", {"Index": "0", "ObjectRef": motion_filter_id})
    else:
        ET.SubElement(vcc, "DefaultMotion").text = "true"
        ET.SubElement(vcc, "DefaultOpacity").text = "true"
        ET.SubElement(vcc, "DefaultMotionComponentID").text = "1"
        ET.SubElement(vcc, "DefaultOpacityComponentID").text = "2"
        cc = ET.SubElement(vcc, "ComponentChain", {"Version": "3"})
        ccnode = ET.SubElement(cc, "Node", {"Version": "1"})
        ccprops = ET.SubElement(ccnode, "Properties", {"Version": "1"})
        ET.SubElement(ccprops, "MZ.ComponentChain.ActiveComponentID").text = "2"
        ET.SubElement(ccprops, "MZ.ComponentChain.ActiveComponentParamIndex").text = "4294967295"
    elements.append(vcc)

    return {"elements": elements, "vcti_id": vcti_id}


# ──────────────────────────────────────────────────────────────────────────
# Mutator: surgically modify the seed
# ──────────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────


def setup_logging(out_path: Path, verbose: bool, quiet: bool) -> None:
    level = logging.DEBUG if verbose else (logging.WARNING if quiet else logging.INFO)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(level)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    log_path = out_path.with_suffix(out_path.suffix + ".log")
    fh = logging.FileHandler(log_path, mode="w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.info("logging to %s", log_path)


def preflight(timeline: list, footage_folder: Path, fps: float) -> dict[str, MediaMeta]:
    """Resolve every unique V1 source, run ffprobe, sanity-check durations."""
    unique = sorted({t["v1"]["file"] for t in timeline if t.get("v1")})
    logger.info("preflight: %d unique V1 sources to probe", len(unique))

    metas: dict[str, MediaMeta] = {}
    errors = []
    for basename in unique:
        path = footage_folder / basename
        if not path.exists():
            errors.append(f"missing: {path}")
            continue
        try:
            m = ffprobe(path)
            metas[basename] = m
            logger.info(
                "  %s: dur=%.3fs %dx%d fps=%.3f codec=%s audio=%s",
                basename, m.duration_seconds, m.width, m.height, m.fps, m.codec_name, m.audio_layout,
            )
        except Exception as e:
            errors.append(f"ffprobe {path}: {e}")

    # Check max adjusted_out per file vs duration
    max_used: dict[str, float] = {}
    for t in timeline:
        if not t.get("v1"):
            continue
        f = t["v1"]["file"]
        out = float(t["v1"].get("adjusted_out", t["v1"].get("out", 0)))
        max_used[f] = max(max_used.get(f, 0.0), out)
    for f, mx in max_used.items():
        if f not in metas:
            continue
        if mx > metas[f].duration_seconds + 0.05:
            logger.warning(
                "source %s: manifest references up to %.3fs but ffprobe duration is %.3fs",
                f, mx, metas[f].duration_seconds,
            )
    if errors:
        for e in errors:
            logger.error(e)
        raise RuntimeError(f"preflight failed: {len(errors)} errors")
    return metas


def write_prproj(manifest_path: Path, out_path: Path, footage_folder_override: Optional[Path]) -> None:
    logger.info("manifest: %s", manifest_path)
    manifest = json.loads(manifest_path.read_text())
    seq = manifest["sequence_settings"]
    fps = float(seq["fps"])
    width = int(seq["width"])
    height = int(seq["height"])
    timeline = manifest["timeline"]
    logger.info("sequence: %dx%d @ %s fps  timeline_entries=%d",
                width, height, fps, len(timeline))

    footage_folder = footage_folder_override or Path(manifest["footage_folder"])
    logger.info("footage folder: %s", footage_folder)

    metas = preflight(timeline, footage_folder, fps)
    logger.info("preflight ok: %d sources probed", len(metas))

    # Load seed
    logger.info("loading seed: %s", SEED_PRPROJ)
    with gzip.open(SEED_PRPROJ, "rb") as fp:
        seed_xml = fp.read()
    tree = parse_xml(seed_xml)
    pdata = find_premiere_data(tree)
    seed_masterclip_count = sum(
        1 for el in pdata if el.tag == "MasterClip" and "ObjectUID" in el.attrib
    )
    logger.debug("seed masterclip count: %d", seed_masterclip_count)

    # ID factory bootstrapped above max in seed
    max_id = find_max_object_id(pdata)
    used_uids = collect_used_uids(pdata)
    ids = IdFactory(next_object_id=max_id + 1, used_uids=set(used_uids))
    logger.info("seed scan: max ObjectID=%d, %d ObjectUIDs in use", max_id, len(used_uids))

    # Build media chains
    media_by_file: dict[str, dict] = {}
    for basename, meta in metas.items():
        chain = build_media_chain(meta, ids)
        media_by_file[basename] = chain
        for el in chain["elements"]:
            pdata.append(el)
        logger.info("media chain: %s -> ClipProjectItem ObjectUID=%s",
                    basename, chain["clip_project_item_uid"])

    # Remove existing VCTI from V1
    existing_vcti = find_existing_vcti(pdata)
    if existing_vcti is not None:
        logger.info("removing existing VCTI ObjectID=%s from seed", existing_vcti.get("ObjectID"))
        remove_existing_vcti(pdata)

    # Build placements
    placements: list[dict] = []
    for i, entry in enumerate(timeline):
        v1 = entry.get("v1")
        if not v1:
            logger.warning("timeline[%d]: no v1, skipping", i)
            continue
        basename = v1["file"]
        chain = media_by_file[basename]
        try:
            tl_in = seconds_to_ticks(timecode_to_seconds(entry["timeline_in"], fps))
            tl_out = seconds_to_ticks(timecode_to_seconds(entry["timeline_out"], fps))
        except Exception as e:
            logger.error("timeline[%d]: timecode parse failed: %s", i, e)
            raise
        src_in = seconds_to_ticks(float(v1.get("adjusted_in", v1["in"])))
        src_out = seconds_to_ticks(float(v1.get("adjusted_out", v1["out"])))

        tl_dur_s = (tl_out - tl_in) / TICKS_PER_SECOND
        src_dur_s = (src_out - src_in) / TICKS_PER_SECOND
        playback_speed: Optional[float] = None
        if abs(tl_dur_s - src_dur_s) > 0.05 and tl_dur_s > 0:
            playback_speed = src_dur_s / tl_dur_s
            logger.info(
                "timeline[%d] %s: src=%.3fs tl=%.3fs → PlaybackSpeed=%.4f (%.0f%%)",
                i, basename, src_dur_s, tl_dur_s, playback_speed, playback_speed * 100,
            )

        # Per-clip scale fits source into the sequence frame using height ratio.
        # 4K (2160h) -> 1080p sequence: scale = 50%. Same-resolution: scale = 100
        # (no Motion override emitted; chain stays default).
        meta = metas[basename]
        motion_scale_pct: Optional[float] = None
        if meta.height != height:
            motion_scale_pct = (height / meta.height) * 100.0
            logger.info(
                "timeline[%d] %s: source %dx%d in %dx%d sequence → Motion.Scale=%.2f%%",
                i, basename, meta.width, meta.height, width, height, motion_scale_pct,
            )

        p = build_clip_placement(
            chain, tl_in, tl_out, src_in, src_out, ids,
            playback_speed=playback_speed,
            motion_scale_pct=motion_scale_pct,
        )
        placements.append(p)
        for el in p["elements"]:
            pdata.append(el)
        logger.info(
            "placed[%d] %s tl=%s→%s (%d→%d t) src=%.3f→%.3fs (%d→%d t) vcti=%s",
            i, basename, entry["timeline_in"], entry["timeline_out"],
            tl_in, tl_out, src_in / TICKS_PER_SECOND, src_out / TICKS_PER_SECOND,
            src_in, src_out, p["vcti_id"],
        )

    # Re-link V1 ClipTrack to all new VCTIs
    v1_track = find_v1_clip_track(pdata)
    replace_v1_clip_items(v1_track, [p["vcti_id"] for p in placements])
    logger.info("V1 track: linked %d VCTIs", len(placements))

    # Build bins. 1_CUTS holds the existing Sequence(s); 2_FOOTAGE holds all new
    # media. Seed-leftover source-media ClipProjectItems are orphaned (not
    # referenced by any bin) so they don't clutter Premiere's project panel.
    root_bin = find_root_project_item(pdata)
    container = root_bin.find("ProjectItemContainer")
    items = container.find("Items")
    existing_root_urefs = [it.get("ObjectURef") for it in items]
    logger.info("existing root items: %d -> %s", len(existing_root_urefs), existing_root_urefs)

    sequence_urefs = []
    orphaned_urefs = []
    for u in existing_root_urefs:
        kind = classify_root_clip_project_item(u, pdata)
        logger.info("  root item %s -> kind=%s", u, kind)
        if kind == "sequence":
            sequence_urefs.append(u)
        else:
            orphaned_urefs.append(u)

    cuts_bin, cuts_uid = build_bin("1_CUTS", ids, sequence_urefs)
    footage_bin, footage_uid = build_bin(
        "2_FOOTAGE", ids,
        [c["clip_project_item_uid"] for c in media_by_file.values()],
    )
    pdata.append(cuts_bin)
    pdata.append(footage_bin)
    logger.info(
        "bins: 1_CUTS=%s (sequences=%d), 2_FOOTAGE=%s (sources=%d), seed_orphaned=%d",
        cuts_uid, len(sequence_urefs), footage_uid, len(media_by_file), len(orphaned_urefs),
    )

    # Reparent: root now has only the two bins
    replace_root_bin_items(root_bin, [cuts_uid, footage_uid])

    # Serialize + gzip
    uncompressed_bytes = write_prproj_bytes(pdata, out_path)
    out_size = out_path.stat().st_size
    logger.info("wrote %s (%d gzipped bytes, %d uncompressed, %d ObjectIDs assigned)",
                out_path, out_size, uncompressed_bytes, ids.next_object_id - max_id - 1)

    # Round-trip
    integrity_check(
        out_path,
        expected_vcti=len(placements),
        expected_new_masterclips=len(media_by_file),
        seed_masterclips=seed_masterclip_count,
    )


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="Output prproj path. Default: "
                        "experiments/PREMIERE PROJECTS/OUTPUTS/<recipe>/<recipe>_round1.prproj")
    p.add_argument("--footage-folder", type=Path, default=None,
                   help="Override the manifest's footage_folder (e.g. for testing on a copy)")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("-q", "--quiet", action="store_true")
    args = p.parse_args(argv)

    if args.output is None:
        manifest_data = json.loads(args.manifest.read_text())
        recipe_slug = _slugify(manifest_data.get("project_name") or args.manifest.stem)
        args.output = OUTPUTS_ROOT / recipe_slug / f"{recipe_slug}_round1.prproj"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(args.output, args.verbose, args.quiet)

    try:
        write_prproj(args.manifest, args.output, args.footage_folder)
    except Exception:
        logger.exception("write_prproj failed")
        raise


if __name__ == "__main__":
    main()
