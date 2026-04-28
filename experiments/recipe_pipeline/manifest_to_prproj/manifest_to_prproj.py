#!/usr/bin/env python3
"""
manifest_to_prproj.py — Round 1 prproj-direct writer (CLI orchestrator).

Takes a recipe manifest and emits a Premiere .prproj with bins, media imports,
an empty sequence at the manifest's fps/resolution, and V1 clips placed at the
manifest's timeline positions cutting from the manifest's source ranges.

Round 1 scope: V1 only. No V2, no MOGRTs, no effects beyond per-clip
PlaybackSpeed (static slow-mo) and Motion.Scale (resolution fit).

This file is the CLI entry point and the orchestrator (`write_prproj`). The
actual XML emission lives in the `core/` and `effects/` subpackages — each
module documents its own scope. See `core/__init__.py` for the component map
and Decision 3 in Brain/Projects/RoughCut/Architecture — Lessons from Claude
Code Paper.md for the rationale behind the split.

Companion docs:
  - Brain/Projects/ASI-Evolve/Prproj-Direct Writer Plan.md — round-by-round plan
  - Brain/Projects/ASI-Evolve/Manifest-to-Prproj Writer — Build Notes.md — operational handoff
  - Brain/Knowledge/API Integration/Premiere prproj Media Chain and Clip Placement Graph.md — XML reference
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional

# Support both module and script invocation:
#   python -m experiments.recipe_pipeline.manifest_to_prproj.manifest_to_prproj …
#   python experiments/recipe_pipeline/manifest_to_prproj/manifest_to_prproj.py …
# When invoked as a script, __package__ is empty and sibling modules need a
# path-based import. Prepending the package's parent directory to sys.path
# makes both work without conditional imports.
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "manifest_to_prproj"  # type: ignore[name-defined]

from .core import (  # noqa: E402
    TICKS_PER_SECOND,
    timecode_to_seconds,
    seconds_to_ticks,
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
from .core.placement import (  # noqa: E402
    build_clip_placement,
)
from .effects.motion import (  # noqa: E402
    build_motion_filter,
)


logger = logging.getLogger("manifest_to_prproj")


def _slugify(s: str) -> str:
    """Filesystem-safe lowercase slug. 'Basil Pesto' -> 'basil_pesto'."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "recipe"


def setup_logging(out_path: Path, verbose: bool, quiet: bool) -> None:
    """Two sinks: stderr at INFO/DEBUG/WARNING per flags, sidecar .log at DEBUG."""
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
    """Top-level orchestrator. Loads the seed, mutates it per the manifest, writes the result."""
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
        # 4K (2160h) -> 1080p sequence: scale = 50%. Same-resolution: no Motion
        # override emitted; chain stays default. The factory pattern lets
        # build_clip_placement allocate its own IDs first, then invoke this
        # callable — preserving pre-refactor ID allocation order so ObjectID
        # values stay byte-identical.
        meta = metas[basename]
        motion_filter_factory = None
        if meta.height != height:
            motion_scale_pct = (height / meta.height) * 100.0
            logger.info(
                "timeline[%d] %s: source %dx%d in %dx%d sequence → Motion.Scale=%.2f%%",
                i, basename, meta.width, meta.height, width, height, motion_scale_pct,
            )
            if abs(motion_scale_pct - 100.0) > 1e-6:
                motion_filter_factory = (
                    lambda ids_, _scale=motion_scale_pct: build_motion_filter(_scale, ids_)
                )

        p = build_clip_placement(
            chain, tl_in, tl_out, src_in, src_out, ids,
            playback_speed=playback_speed,
            motion_filter_factory=motion_filter_factory,
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
