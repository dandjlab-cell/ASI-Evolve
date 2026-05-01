#!/usr/bin/env python3
"""
nbq_writer.py — NBQ Round 1 prproj writer.

First slice: takes the v4 NBQ manifest + sync_groups and emits a Premiere
.prproj with ALL footage organized in bins + the manifest's primary takes
sliced per beat-segment placed on the main sequence's V1.

Round 1 scope (intentionally minimal — verify the foundation opens cleanly):
  - Import every studio + R5 video file as a MasterClip into bins
  - One sequence at the manifest's fps/resolution
  - V1 cuts per cluster's primary_take, sliced to v6_segments from trim_air

NOT in this round (later rounds):
  - Multicam sub-sequences (build with A_cam at angle 0 + B_cam angle 1
    + ext_audio synced to ext_audio_offset_s)
  - V6 IsMulticam picks (replace V1 placements once multicam sub-sequences exist)
  - V7 paired adjustment-layer with Geometry2 per beat mode
  - V3-V5 below-V6 graphics (definition_card, list_card, etc.)
  - V8+ MOGRT clips (Capsule textEditValue text-fields)
  - .mov drop-in cues (main_title, transition_section, like_and_subscribe, …)
  - Per-clip effect stacks on V6 (Lumetri + Ultra Key + Drop Shadow)
  - Audio media chains for ext_audio (.WAV)
  - V20 brand-bug full-episode static

Usage:
    python -m manifest_to_prproj.nbq_writer <manifest.json> <sync_groups.json>
    [-o output.prproj]

Companion:
  ~/DevApps/Brain/Projects/RoughCut/NBQ Pipeline v4.md  (architecture)
  ~/DevApps/Brain/Knowledge/API Integration/Premiere prproj Multicam Detection.md
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Support module + script invocation, same trick as manifest_to_prproj.py
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "manifest_to_prproj"  # type: ignore[name-defined]

from .core import seconds_to_ticks  # noqa: E402
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
from .core.placement import (  # noqa: E402
    build_clip_placement,
)


# Use the same logger name as the recipe writer + core modules so their log
# lines (integrity_check, etc.) flow through the handlers we set up below.
logger = logging.getLogger("manifest_to_prproj")


def setup_logging(out_path: Path, verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
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


def collect_video_sources(sync_groups: dict) -> dict[str, dict]:
    """Walk sync_groups; return {basename: {role, sg_id}} for every video file
    referenced by any sync_group. role ∈ {"a_cam", "b_cam"}.
    """
    out: dict[str, dict] = {}
    for g in sync_groups.get("groups", []):
        a = g.get("a_cam")
        b = g.get("b_cam")
        if a:
            out[a] = {"role": "a_cam", "sg_id": g["group_id"]}
        if b:
            out[b] = {"role": "b_cam", "sg_id": g["group_id"]}
    return out


def collect_placements_from_timeline(
    timeline: list[dict],
    sync_groups: dict,
) -> list[dict]:
    """Walk the manifest's timeline (per cluster); produce flat placement
    entries — one per beat-segment — with timeline + source ranges + the
    a_cam basename to source from.

    Each cluster's primary_take comes from a specific sync_group; that
    sync_group's a_cam is the file we cut from. The beat's v6_segments
    give the (source-time) sub-cuts inside the take. We lay them back-to-
    back inside the cluster's [timeline_in_s, timeline_out_s] window.
    """
    sg_to_a_cam: dict[str, str] = {
        g["group_id"]: g["a_cam"]
        for g in sync_groups.get("groups", [])
        if g.get("a_cam")
    }
    placements: list[dict] = []
    for cluster in timeline:
        primary = cluster.get("primary_take")
        if not primary:
            continue
        beats = cluster.get("beats") or []
        sg_id = primary.get("sync_group_id")
        a_cam = sg_to_a_cam.get(sg_id)
        if not a_cam:
            logger.warning("cluster %s sg=%s has no a_cam — skipping", cluster.get("cluster_id"), sg_id)
            continue
        cluster_in_s = float(cluster["timeline_in_s"])
        timeline_cursor_s = cluster_in_s
        for beat in beats:
            for seg in beat.get("v6_segments") or []:
                src_in_s = float(seg["in_s"])
                src_out_s = float(seg["out_s"])
                duration_s = src_out_s - src_in_s
                if duration_s <= 0:
                    continue
                placements.append({
                    "cluster_id": cluster.get("cluster_id"),
                    "beat_id": beat.get("beat_id"),
                    "file": a_cam,
                    "source_in_s": src_in_s,
                    "source_out_s": src_out_s,
                    "timeline_in_s": timeline_cursor_s,
                    "timeline_out_s": timeline_cursor_s + duration_s,
                })
                timeline_cursor_s += duration_s
    return placements


def preflight(unique_files: list[str], footage_folder: Path) -> dict[str, MediaMeta]:
    """ffprobe every file. Fail loudly if any is missing."""
    metas: dict[str, MediaMeta] = {}
    errors = []
    for basename in unique_files:
        path = footage_folder / basename
        if not path.exists():
            errors.append(f"missing: {path}")
            continue
        try:
            m = ffprobe(path)
            metas[basename] = m
            logger.info("  %s: %.3fs %dx%d %.3ffps codec=%s",
                        basename, m.duration_seconds, m.width, m.height, m.fps, m.codec_name)
        except Exception as e:
            errors.append(f"ffprobe {path}: {e}")
    if errors:
        for e in errors:
            logger.error(e)
        raise RuntimeError(f"preflight failed: {len(errors)} errors")
    return metas


def write_nbq_prproj(
    manifest_path: Path,
    sync_groups_path: Path,
    out_path: Path,
    footage_folder_override: Optional[Path] = None,
) -> None:
    logger.info("manifest: %s", manifest_path)
    logger.info("sync_groups: %s", sync_groups_path)
    manifest = json.loads(manifest_path.read_text())
    sync_groups = json.loads(sync_groups_path.read_text())

    seq = manifest["sequence_settings"]
    fps = float(seq["fps"])
    width = int(seq["width"])
    height = int(seq["height"])
    timeline = manifest.get("timeline") or []
    logger.info("sequence: %dx%d @ %s fps  clusters=%d", width, height, fps, len(timeline))

    footage_folder = footage_folder_override or Path(manifest["footage_folder"])
    logger.info("footage folder: %s", footage_folder)

    # Catalog every video file referenced by any sync_group + run ffprobe
    video_sources = collect_video_sources(sync_groups)
    logger.info("video sources from sync_groups: %d files", len(video_sources))
    for basename, info in sorted(video_sources.items()):
        logger.debug("  %s  role=%s  sg=%s", basename, info["role"], info["sg_id"])
    metas = preflight(sorted(video_sources.keys()), footage_folder)
    logger.info("preflight ok: %d files probed", len(metas))

    # Compute placements (per beat-segment, V1-only for Round 1)
    placements_spec = collect_placements_from_timeline(timeline, sync_groups)
    logger.info("placements: %d cuts across %d clusters",
                len(placements_spec),
                len({p["cluster_id"] for p in placements_spec}))

    # Sanity: the placements should reference files we've probed
    referenced_files = sorted({p["file"] for p in placements_spec})
    missing_in_metas = [f for f in referenced_files if f not in metas]
    if missing_in_metas:
        raise RuntimeError(f"placements reference unprobed files: {missing_in_metas}")

    # ────────────────────────────────────────────────────────────────────
    # Load seed (recipe writer's SEQ_FLAT) and bootstrap IdFactory
    # ────────────────────────────────────────────────────────────────────
    logger.info("loading seed: %s", SEED_PRPROJ)
    with gzip.open(SEED_PRPROJ, "rb") as fp:
        seed_xml = fp.read()
    tree = parse_xml(seed_xml)
    pdata = find_premiere_data(tree)
    seed_masterclip_count = sum(
        1 for el in pdata if el.tag == "MasterClip" and "ObjectUID" in el.attrib
    )
    logger.debug("seed masterclip count: %d", seed_masterclip_count)

    max_id = find_max_object_id(pdata)
    used_uids = collect_used_uids(pdata)
    ids = IdFactory(next_object_id=max_id + 1, used_uids=set(used_uids))
    logger.info("seed scan: max ObjectID=%d, %d ObjectUIDs in use", max_id, len(used_uids))

    # ────────────────────────────────────────────────────────────────────
    # Build media chains for every video source
    # ────────────────────────────────────────────────────────────────────
    media_by_file: dict[str, dict] = {}
    for basename in sorted(metas.keys()):
        chain = build_media_chain(metas[basename], ids)
        media_by_file[basename] = chain
        for el in chain["elements"]:
            pdata.append(el)
        logger.info("media chain: %s -> ClipProjectItem ObjectUID=%s",
                    basename, chain["clip_project_item_uid"])

    # Drop the seed's V1 placeholder VCTI (we replace with our own placements)
    existing_vcti = find_existing_vcti(pdata)
    if existing_vcti is not None:
        logger.info("removing seed VCTI ObjectID=%s", existing_vcti.get("ObjectID"))
        remove_existing_vcti(pdata)

    # ────────────────────────────────────────────────────────────────────
    # Build placements (V1, no effects, no multicam yet)
    # ────────────────────────────────────────────────────────────────────
    placements: list[dict] = []
    for i, p in enumerate(placements_spec):
        chain = media_by_file[p["file"]]
        tl_in = seconds_to_ticks(p["timeline_in_s"])
        tl_out = seconds_to_ticks(p["timeline_out_s"])
        src_in = seconds_to_ticks(p["source_in_s"])
        src_out = seconds_to_ticks(p["source_out_s"])
        placement = build_clip_placement(
            chain, tl_in, tl_out, src_in, src_out, ids,
        )
        placements.append(placement)
        for el in placement["elements"]:
            pdata.append(el)
        if i < 8 or i % 25 == 0:
            logger.info(
                "placed[%03d] %s  cluster=%s  beat=%s  tl=%.2f-%.2fs  src=%.2f-%.2fs  vcti=%s",
                i, p["file"], p["cluster_id"], p["beat_id"],
                p["timeline_in_s"], p["timeline_out_s"],
                p["source_in_s"], p["source_out_s"], placement["vcti_id"],
            )

    # Re-link V1 ClipTrack to all our new VCTIs
    v1_track = find_v1_clip_track(pdata)
    replace_v1_clip_items(v1_track, [p["vcti_id"] for p in placements])
    logger.info("V1 track: linked %d VCTIs", len(placements))

    # ────────────────────────────────────────────────────────────────────
    # Build bins
    # ────────────────────────────────────────────────────────────────────
    root_bin = find_root_project_item(pdata)
    container = root_bin.find("ProjectItemContainer")
    items = container.find("Items")
    existing_root_urefs = [it.get("ObjectURef") for it in items]
    sequence_urefs = []
    for u in existing_root_urefs:
        if classify_root_clip_project_item(u, pdata) == "sequence":
            sequence_urefs.append(u)

    # Footage bins partitioned by role: A_CAM, B_CAM, R5 (everything not A/B).
    a_cam_uids: list[str] = []
    b_cam_uids: list[str] = []
    r5_uids: list[str] = []
    for basename, chain in media_by_file.items():
        info = video_sources.get(basename, {})
        role = info.get("role")
        if role == "a_cam":
            # A611C* studio + 0X3A5325 R5 cold-open both technically have role=a_cam
            # in their respective sync_groups. Distinguish by prefix.
            if basename.startswith("0X3A"):
                r5_uids.append(chain["clip_project_item_uid"])
            else:
                a_cam_uids.append(chain["clip_project_item_uid"])
        elif role == "b_cam":
            b_cam_uids.append(chain["clip_project_item_uid"])

    cuts_bin, cuts_uid = build_bin("1_CUTS", ids, sequence_urefs)
    footage_a_bin, footage_a_uid = build_bin("2_FOOTAGE_A_CAM", ids, a_cam_uids)
    footage_b_bin, footage_b_uid = build_bin("2_FOOTAGE_B_CAM", ids, b_cam_uids)
    footage_r5_bin, footage_r5_uid = build_bin("2_FOOTAGE_R5", ids, r5_uids)
    pdata.append(cuts_bin)
    pdata.append(footage_a_bin)
    pdata.append(footage_b_bin)
    pdata.append(footage_r5_bin)
    logger.info("bins: 1_CUTS=%s, 2_FOOTAGE_A_CAM=%s (%d), 2_FOOTAGE_B_CAM=%s (%d), 2_FOOTAGE_R5=%s (%d)",
                cuts_uid, footage_a_uid, len(a_cam_uids),
                footage_b_uid, len(b_cam_uids),
                footage_r5_uid, len(r5_uids))

    replace_root_bin_items(
        root_bin,
        [cuts_uid, footage_a_uid, footage_b_uid, footage_r5_uid],
    )

    # ────────────────────────────────────────────────────────────────────
    # Serialize + integrity check
    # ────────────────────────────────────────────────────────────────────
    uncompressed_bytes = write_prproj_bytes(pdata, out_path)
    out_size = out_path.stat().st_size
    logger.info("wrote %s (%d gzipped bytes, %d uncompressed, %d ObjectIDs assigned)",
                out_path, out_size, uncompressed_bytes, ids.next_object_id - max_id - 1)
    integrity_check(
        out_path,
        expected_vcti=len(placements),
        expected_new_masterclips=len(media_by_file),
        seed_masterclips=seed_masterclip_count,
    )


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path, help="Path to <project>_v4_manifest.json")
    p.add_argument("sync_groups", type=Path, help="Path to <project>_sync_groups.json")
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="Output prproj path. Default: experiments/PREMIERE PROJECTS/OUTPUTS/<project>/<project>_round1.prproj")
    p.add_argument("--footage-folder", type=Path, default=None,
                   help="Override the manifest's footage_folder")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    if args.output is None:
        manifest_data = json.loads(args.manifest.read_text())
        slug = manifest_data.get("project_name") or args.manifest.stem
        slug = slug.lower().replace(" ", "_")
        args.output = OUTPUTS_ROOT / slug / f"{slug}_nbq_round1.prproj"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(args.output, args.verbose)

    try:
        write_nbq_prproj(args.manifest, args.sync_groups, args.output, args.footage_folder)
    except Exception:
        logger.exception("write_nbq_prproj failed")
        raise


if __name__ == "__main__":
    main()
