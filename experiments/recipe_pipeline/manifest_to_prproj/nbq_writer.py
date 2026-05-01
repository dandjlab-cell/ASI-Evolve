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
    find_a1_clip_track,
    find_existing_vcti,
    replace_root_bin_items,
    replace_v1_clip_items,
    replace_a1_clip_items,
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
    build_audio_clip_placement,
    build_link_element,
)
from .effects.motion import (  # noqa: E402
    build_motion_filter,
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


def collect_placements_from_manifest_timeline(
    timeline: list[dict],
    sync_groups: dict,
) -> list[dict]:
    """Map manifest.timeline[].primary_take → .prproj cuts. ONE cut per
    cluster, take's full source range. The composer (cluster_to_beats.py
    in roughcut-ai) already chose the primary take per cluster via
    _select_primary; the writer just maps those choices to the timeline.

    Cluster ordering and timeline_in/out come from the manifest.
    """
    sg_to_a_cam = {
        g["group_id"]: g["a_cam"]
        for g in sync_groups.get("groups", [])
        if g.get("a_cam")
    }
    placements: list[dict] = []
    for cluster in timeline:
        primary = cluster.get("primary_take") or {}
        sg_id = primary.get("sync_group_id")
        if not sg_id:
            continue  # cluster has no primary (e.g. cutdown_pickups)
        a_cam = sg_to_a_cam.get(sg_id)
        if not a_cam:
            logger.warning("cluster %s sg=%s has no a_cam — skipping",
                           cluster.get("cluster_id"), sg_id)
            continue
        src_in_s = float(primary["start_s"])
        src_out_s = float(primary["end_s"])
        if src_out_s <= src_in_s:
            continue
        placements.append({
            "cluster_id": cluster.get("cluster_id"),
            "primary_pid": cluster.get("cluster_id"),  # for log compat
            "file": a_cam,
            "source_in_s": src_in_s,
            "source_out_s": src_out_s,
            "timeline_in_s": float(cluster.get("timeline_in_s", 0.0)),
            "timeline_out_s": float(cluster.get("timeline_out_s", 0.0)),
        })
    return placements


def _paragraph_sort_key(pid: str) -> tuple[int, str]:
    """[P09] sorts before [P10]; non-numeric paragraphs go to the end."""
    try:
        return (int(pid.lstrip("P").lstrip("p")), pid)
    except ValueError:
        return (10**9, pid)


def _natural_take_bounds(
    take_in_s: float,
    take_out_s: float,
    sg_words: list[dict],
    silence_s: float = 1.0,
    max_lookback_s: float = 5.0,
) -> tuple[float, float]:
    """Extend a take's [start_s, end_s] to the natural utterance boundaries
    using Whisper word timestamps.

    script_align's take.start_s is the first SCRIPT-MATCHED word. Anna may
    have said preamble words ("OK, um, today...") that don't match the
    script and got skipped — we want the cut to begin at the natural
    sentence start, not the matched word.

    Algorithm:
      - Walk backward from take_in_s through Whisper words. Include each
        word whose preceding silence < silence_s (1s). Stop when a >1s
        silence is hit OR we've gone back max_lookback_s. That's the
        natural utterance start.
      - Same forward from take_out_s for natural end.

    Returns the extended [start, end] in source-time seconds.
    """
    if not sg_words:
        return take_in_s, take_out_s

    # Backward scan: find earliest word still in this utterance
    new_start = take_in_s
    for i in range(len(sg_words) - 1, -1, -1):
        w = sg_words[i]
        if w["start"] >= take_in_s:
            continue  # word is at/after take's matched start; not preamble
        if take_in_s - w["start"] > max_lookback_s:
            break
        prev = sg_words[i - 1] if i > 0 else None
        gap = (w["start"] - prev["end"]) if prev else 999.0
        if gap > silence_s:
            # This word follows a real silence — it's the start of an utterance
            new_start = max(0.0, w["start"] - 0.05)
            break
        # Otherwise this word is part of the same utterance as the take's start
        new_start = max(0.0, w["start"] - 0.05)

    # Forward scan: find last word still in this utterance
    new_end = take_out_s
    for i, w in enumerate(sg_words):
        if w["end"] <= take_out_s:
            continue
        if w["start"] - take_out_s > max_lookback_s:
            break
        prev = sg_words[i - 1]
        gap = w["start"] - prev["end"]
        if gap > silence_s:
            break  # silence before this word — utterance ended
        new_end = w["end"] + 0.05

    return new_start, new_end


def _split_take_at_real_gaps(
    take_in_s: float,
    take_out_s: float,
    take_words: list[dict],
    real_gap_s: float = 1.0,
) -> list[dict]:
    """Split a take into segments only where Whisper found a >real_gap_s
    silence. Breaths (<1s pauses) are KEPT inside the segment. Returns
    [{in_s, out_s}, ...] — one entry if no real gaps, multiple if dead air
    inside the take.
    """
    if not take_words:
        return [{"in_s": take_in_s, "out_s": take_out_s}]
    segs: list[dict] = []
    seg_start = max(take_in_s, take_words[0]["start"] - 0.05)
    prev = take_words[0]
    for w in take_words[1:]:
        gap = w["start"] - prev["end"]
        if gap > real_gap_s:
            seg_end = min(prev["end"] + 0.05, take_out_s)
            if seg_end > seg_start:
                segs.append({"in_s": round(seg_start, 3), "out_s": round(seg_end, 3)})
            seg_start = max(w["start"] - 0.05, seg_end)
        prev = w
    final_end = min(prev["end"] + 0.05, take_out_s)
    if final_end > seg_start:
        segs.append({"in_s": round(seg_start, 3), "out_s": round(final_end, 3)})
    return segs or [{"in_s": take_in_s, "out_s": take_out_s}]


def collect_placements_by_script_order(
    trimmed_takes_path: Path,
    take_visuals_path: Path,
    sync_groups: dict,
    transcripts_path: Optional[Path] = None,
    real_gap_s: float = 1.0,
) -> list[dict]:
    """Walk trimmed takes in script-paragraph order; pick the best take per
    paragraph; place its segments back-to-back on the timeline.

    Simpler than the cluster→beat→segment model: just follow the script,
    air already removed by trim_air, one take per paragraph.

    Selection per paragraph:
      - exclude pickups (coverage < 0.4 — short re-do reads)
      - rank by combined_score = 0.6 × confidence + 0.4 × (visual_score / 3)
      - pick highest

    De-dupes by source range so a take covering multiple paragraphs is
    placed exactly once (not once per paragraph it covers).
    """
    trimmed = json.loads(trimmed_takes_path.read_text())
    takes = trimmed.get("takes", [])
    transcripts_data: dict = {}
    if transcripts_path and transcripts_path.exists():
        transcripts_data = json.loads(transcripts_path.read_text())
    visuals_idx: dict[tuple, int] = {}
    if take_visuals_path.exists():
        vis = json.loads(take_visuals_path.read_text())
        for s in vis.get("scores", []):
            if s.get("visual_score") is not None:
                key = (s["sync_group_id"], round(float(s["start_s"]), 2),
                       round(float(s["end_s"]), 2))
                visuals_idx[key] = int(s["visual_score"])

    sg_to_a_cam = {
        g["group_id"]: g["a_cam"]
        for g in sync_groups.get("groups", [])
        if g.get("a_cam")
    }

    def _combined_score(take: dict) -> float:
        conf = float(take.get("confidence") or 0.0)
        key = (take.get("sync_group_id"), round(float(take["start_s"]), 2),
               round(float(take["end_s"]), 2))
        v = visuals_idx.get(key, 0) or 0
        return 0.6 * conf + 0.4 * (v / 3.0)

    # Group takes by their FIRST paragraph (a take spanning multiple paragraphs
    # is bound to its earliest one in script order).
    by_paragraph: dict[str, list[dict]] = {}
    for t in takes:
        if t.get("type") == "pickup":
            continue
        paragraphs = t.get("paragraphs") or []
        if not paragraphs:
            continue
        primary_pid = sorted(paragraphs, key=_paragraph_sort_key)[0]
        by_paragraph.setdefault(primary_pid, []).append(t)

    # Pick best take per paragraph
    chosen_takes: list[dict] = []
    seen_ranges: set[tuple] = set()
    for pid in sorted(by_paragraph.keys(), key=_paragraph_sort_key):
        candidates = by_paragraph[pid]
        candidates.sort(key=_combined_score, reverse=True)
        best = candidates[0]
        rng = (best["sync_group_id"], round(float(best["start_s"]), 2),
               round(float(best["end_s"]), 2))
        if rng in seen_ranges:
            continue
        seen_ranges.add(rng)
        chosen_takes.append({"primary_pid": pid, "take": best})

    placements: list[dict] = []
    timeline_cursor_s = 0.0
    # ONE cut per take = take.start_s..take.end_s. No trim_air segment
    # splitting (which cut at every 0.3s breath, producing mid-sentence
    # cuts). Each cut = one continuous Anna delivery from the take's
    # first matched word to its last matched word, exactly as script_align
    # found it. Take's natural pauses inside stay in the audio.
    file_source_cursor: dict[str, float] = {}
    for entry in chosen_takes:
        take = entry["take"]
        sg_id = take["sync_group_id"]
        a_cam = sg_to_a_cam.get(sg_id)
        if not a_cam:
            logger.warning("take from sg=%s has no a_cam — skipping", sg_id)
            continue
        src_in_s = float(take["start_s"])
        src_out_s = float(take["end_s"])

        # Extend to natural utterance boundaries via Whisper words. The take's
        # matched start may be mid-sentence if SW skipped non-script preamble
        # ("OK, um, today..."). Walk backward through transcript to find the
        # nearest word AFTER a >1s silence — that's the natural sentence start.
        sg_words = transcripts_data.get(sg_id, {}).get("words", [])
        if sg_words:
            src_in_s, src_out_s = _natural_take_bounds(
                src_in_s, src_out_s, sg_words, silence_s=real_gap_s,
            )

        # Per-file cursor: trim leading overlap with previous take from same
        # file (adjacent script paragraphs often share aligned words).
        cursor = file_source_cursor.get(a_cam, 0.0)
        if src_in_s < cursor:
            src_in_s = cursor
        if src_out_s <= src_in_s:
            continue
        duration_s = src_out_s - src_in_s
        if duration_s < 0.5:
            continue

        # Split the take at real-air gaps (>real_gap_s silences) so dead air
        # inside the take is removed but breaths (<1s pauses) are kept.
        if sg_words:
            take_words = [
                w for w in sg_words
                if src_in_s <= w.get("start", 0) <= src_out_s
            ]
            sub_segments = _split_take_at_real_gaps(
                src_in_s, src_out_s, take_words, real_gap_s=real_gap_s,
            )
        else:
            sub_segments = [{"in_s": src_in_s, "out_s": src_out_s}]

        for seg in sub_segments:
            seg_in = float(seg["in_s"])
            seg_out = float(seg["out_s"])
            seg_dur = seg_out - seg_in
            if seg_dur < 0.5:
                continue
            placements.append({
                "primary_pid": entry["primary_pid"],
                "paragraphs": list(take.get("paragraphs") or []),
                "file": a_cam,
                "source_in_s": seg_in,
                "source_out_s": seg_out,
                "timeline_in_s": timeline_cursor_s,
                "timeline_out_s": timeline_cursor_s + seg_dur,
            })
            timeline_cursor_s += seg_dur
            file_source_cursor[a_cam] = seg_out
    return placements


def write_choices_report(
    trimmed_takes_path: Path,
    take_visuals_path: Path,
    out_path: Path,
) -> None:
    """Write a human-readable report of per-paragraph take choices, showing
    every available take, score, and which was picked. Lets the user spot
    bad picks immediately.
    """
    from collections import defaultdict
    trimmed = json.loads(trimmed_takes_path.read_text())
    visuals_idx: dict[tuple, int] = {}
    if take_visuals_path.exists():
        vis = json.loads(take_visuals_path.read_text())
        for s in vis.get("scores", []):
            if s.get("visual_score") is not None:
                visuals_idx[(s["sync_group_id"],
                             round(float(s["start_s"]), 2),
                             round(float(s["end_s"]), 2))] = int(s["visual_score"])

    def combined(t):
        conf = float(t.get("confidence") or 0.0)
        v = visuals_idx.get((t["sync_group_id"],
                             round(float(t["start_s"]), 2),
                             round(float(t["end_s"]), 2)), 0) or 0
        return 0.6 * conf + 0.4 * (v / 3.0)

    by_pid = defaultdict(list)
    for t in trimmed.get("takes", []):
        for p in (t.get("paragraphs") or []):
            by_pid[p].append(t)

    def pid_sort(p):
        try:
            return int(p.lstrip("P"))
        except Exception:
            return 10**9

    lines: list[str] = []
    lines.append("# Per-paragraph take choices (✓ = chosen, EXC = excluded as pickup)")
    lines.append("")
    for pid in sorted(by_pid.keys(), key=pid_sort):
        options = sorted(by_pid[pid], key=combined, reverse=True)
        nonpickup = [t for t in options if t.get("type") != "pickup"]
        chosen = nonpickup[0] if nonpickup else None
        lines.append(f"## {pid} ({len(options)} candidates)")
        for t in options:
            mark = "✓" if t is chosen else ("EXC" if t.get("type") == "pickup" else "  ")
            score = combined(t)
            v = visuals_idx.get((t["sync_group_id"],
                                 round(float(t["start_s"]), 2),
                                 round(float(t["end_s"]), 2)), "?")
            lines.append(
                f"  {mark} {t['sync_group_id']} {t['start_s']:>7.2f}-{t['end_s']:<7.2f}s  "
                f"type={t['type']:<8} cov={t.get('coverage', 0):.2f} "
                f"conf={t.get('confidence', 0):.2f} vis={v} score={score:.3f}"
            )
        lines.append("")
    out_path.write_text("\n".join(lines))


def self_check_placements(placements: list[dict]) -> list[str]:
    """Return a list of warning strings for likely errors. Empty = clean."""
    warnings: list[str] = []

    # 1. Exact source-range duplicates
    seen: dict[tuple, int] = {}
    for i, p in enumerate(placements):
        key = (p["file"], round(p["source_in_s"], 2), round(p["source_out_s"], 2))
        if key in seen:
            warnings.append(
                f"DUP source range placed twice: idx {seen[key]} and {i} "
                f"({p['file']} {p['source_in_s']:.2f}-{p['source_out_s']:.2f}s)"
            )
        else:
            seen[key] = i

    # 2. Micro-cuts (mid-word stubs from trim_air leftovers)
    durations = [p["timeline_out_s"] - p["timeline_in_s"] for p in placements]
    if durations:
        too_short = [(i, d) for i, d in enumerate(durations) if d < 0.25]
        if too_short:
            warnings.append(
                f"{len(too_short)} placements shorter than 0.25s "
                f"(possible mid-word cuts): "
                + ", ".join(f"idx{i}={d:.2f}s" for i, d in too_short[:5])
            )

    # 3. Backward source jumps within the same file — replays earlier
    # footage, which is almost always wrong for scripted talking-head.
    last_src_out_per_file: dict[str, float] = {}
    last_idx_per_file: dict[str, int] = {}
    backward = []
    for i, p in enumerate(placements):
        f = p["file"]
        cur_in = p["source_in_s"]
        prev_out = last_src_out_per_file.get(f)
        if prev_out is not None and cur_in < prev_out - 0.1:
            backward.append((last_idx_per_file[f], i, prev_out, cur_in, f))
        last_src_out_per_file[f] = p["source_out_s"]
        last_idx_per_file[f] = i
    if backward:
        warnings.append(
            f"{len(backward)} backward source jumps within same file "
            "(replays earlier footage): "
            + "; ".join(
                f"idx{prev}→{cur}: {f[:18]} prev_out={po:.2f} → cur_in={ci:.2f} (backward {po-ci:.2f}s)"
                for prev, cur, po, ci, f in backward[:3]
            )
        )

    # 4. Timeline gaps or overlaps
    for i in range(1, len(placements)):
        prev = placements[i-1]
        cur = placements[i]
        gap = cur["timeline_in_s"] - prev["timeline_out_s"]
        if abs(gap) > 0.001:
            warnings.append(
                f"Timeline {'gap' if gap > 0 else 'overlap'} "
                f"between idx {i-1} and {i}: {gap*1000:.1f}ms"
            )
            break  # one warning is enough; don't flood
    return warnings


def collect_placements_from_timeline(
    timeline: list[dict],
    sync_groups: dict,
) -> list[dict]:
    """Walk the manifest's timeline (per cluster); produce flat placement
    entries — one per source segment — with timeline + source ranges + the
    a_cam basename to source from.

    Each cluster's primary_take comes from a specific sync_group; that
    sync_group's a_cam is the file we cut from. We use the PRIMARY TAKE's
    segments list once per cluster, NOT the per-beat v6_segments lists,
    because the v4 composer's `_segments_inside_paragraph_range` currently
    returns the full take segments for EVERY beat (TODO marked in
    cluster_to_beats.py: real per-beat slicing requires word-level
    paragraph-time mapping). Iterating beats × segments would duplicate
    each segment N times (N = beat count). Iterating segments per cluster
    gives the correct one-cut-per-trim_air-segment timeline.

    Beat-level granularity will become important in Round 2 when V6+V7
    are paired and each beat carries its own mode (Position+Scale_H).
    Until then, V1 placement is per-cluster.
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
        # Walk beats × v6_segments — composer's per-paragraph slicing means
        # beats now have UNIQUE segments (no duplication across beats inside
        # a cluster). Each segment becomes one cut on V1.
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
    motion_scale_pct: float = 50.0,
    trimmed_takes_path: Optional[Path] = None,
    take_visuals_path: Optional[Path] = None,
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

    # The manifest already chose primary takes per cluster (composer's
    # _select_primary). Writer's job: map manifest.timeline[].primary_take
    # to .prproj cuts. ONE cut per cluster, take's full source range,
    # placed at cluster's timeline_in_s..timeline_out_s.
    placements_spec = collect_placements_from_manifest_timeline(
        timeline, sync_groups,
    )
    logger.info("placements: %d cuts (one per cluster with a primary_take)",
                len(placements_spec))

    # Self-check for errors
    warnings = self_check_placements(placements_spec)
    for w in warnings:
        logger.warning("self-check: %s", w)
    if not warnings:
        logger.info("self-check: clean (no duplicate ranges, no mid-word cuts)")

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
    # Build media chains for every video source. with_audio=True so each
    # .mp4's embedded audio gets a parallel AudioMediaSource + AudioStream
    # + AudioClip + channel routing — drag-to-timeline brings audio with it
    # the way Premiere does for native imports.
    # ────────────────────────────────────────────────────────────────────
    media_by_file: dict[str, dict] = {}
    for basename in sorted(metas.keys()):
        chain = build_media_chain(metas[basename], ids, with_audio=True)
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
    # Build placements (V1, no multicam yet). Motion.Scale defaults to 50%
    # per NBQ V6 multicam-talent convention (talent shrunk in the composite
    # to leave room for BG plate + L/R MOGRTs). Override via --motion-scale
    # for episodes with different framing. Set to 100 to disable.
    # ────────────────────────────────────────────────────────────────────
    placements: list[dict] = []  # video placements
    audio_placements: list[dict] = []  # audio placements (1:1 paired with video)
    for i, p in enumerate(placements_spec):
        chain = media_by_file[p["file"]]
        tl_in = seconds_to_ticks(p["timeline_in_s"])
        tl_out = seconds_to_ticks(p["timeline_out_s"])
        src_in = seconds_to_ticks(p["source_in_s"])
        src_out = seconds_to_ticks(p["source_out_s"])
        motion_filter_factory = None
        if abs(motion_scale_pct - 100.0) > 1e-6:
            motion_filter_factory = (
                lambda ids_, _scale=motion_scale_pct: build_motion_filter(_scale, ids_)
            )
        placement = build_clip_placement(
            chain, tl_in, tl_out, src_in, src_out, ids,
            motion_filter_factory=motion_filter_factory,
        )
        placements.append(placement)
        for el in placement["elements"]:
            pdata.append(el)

        # Paired audio placement on A1 — uses the same source range as video
        # so the linked-selection group stays in sync.
        audio_placement = build_audio_clip_placement(
            chain, tl_in, tl_out, src_in, src_out, ids,
        )
        audio_placements.append(audio_placement)
        for el in audio_placement["elements"]:
            pdata.append(el)

        # Link element pairs the V1 + A1 placements (matches the default
        # behavior of dragging a video-with-audio clip into the timeline).
        link_el = build_link_element(placement["vcti_id"], audio_placement["acti_id"], ids)
        pdata.append(link_el)

        if i < 12 or i % 25 == 0:
            logger.info(
                "placed[%03d] %s  pid=%s  tl=%.2f-%.2fs  src=%.2f-%.2fs  vcti=%s  acti=%s",
                i, p["file"], p.get("primary_pid", "?"),
                p["timeline_in_s"], p["timeline_out_s"],
                p["source_in_s"], p["source_out_s"],
                placement["vcti_id"], audio_placement["acti_id"],
            )

    # Re-link V1 ClipTrack to all our new VCTIs and A1 ClipTrack to all ACTIs
    v1_track = find_v1_clip_track(pdata)
    replace_v1_clip_items(v1_track, [p["vcti_id"] for p in placements])
    a1_track = find_a1_clip_track(pdata)
    replace_a1_clip_items(a1_track, [a["acti_id"] for a in audio_placements])
    logger.info("V1 track: %d VCTIs; A1 track: %d ACTIs",
                len(placements), len(audio_placements))

    # ────────────────────────────────────────────────────────────────────
    # Build bins. Root layout:
    #   1_CUTS/        — sequence(s) from the seed
    #   2_FOOTAGE/     — parent bin containing per-camera sub-bins
    #     A CAM/       — studio A611C* clips
    #     B CAM/       — studio C166C* clips
    #     R5/          — non-studio R5 clips (e.g. cold-open kitchen)
    #   3_AUDIO/       — empty placeholder (audio import not yet decoded;
    #                    AudioMediaSource/AudioStream ClassIDs needed)
    # Bin nesting: a bin's children are URefs — Premiere doesn't care if the
    # target is a media item or another bin. Build sub-bins first; pass their
    # UIDs as children of the parent.
    # ────────────────────────────────────────────────────────────────────
    root_bin = find_root_project_item(pdata)
    container = root_bin.find("ProjectItemContainer")
    items = container.find("Items")
    existing_root_urefs = [it.get("ObjectURef") for it in items]
    sequence_urefs = []
    for u in existing_root_urefs:
        if classify_root_clip_project_item(u, pdata) == "sequence":
            sequence_urefs.append(u)

    a_cam_uids: list[str] = []
    b_cam_uids: list[str] = []
    r5_uids: list[str] = []
    for basename, chain in media_by_file.items():
        info = video_sources.get(basename, {})
        role = info.get("role")
        if role == "a_cam":
            # Both A611C* studio and 0X3A5325 R5 cold-open are role=a_cam in
            # their respective sync_groups. Split by prefix to put R5 in its
            # own sub-bin.
            if basename.startswith("0X3A"):
                r5_uids.append(chain["clip_project_item_uid"])
            else:
                a_cam_uids.append(chain["clip_project_item_uid"])
        elif role == "b_cam":
            b_cam_uids.append(chain["clip_project_item_uid"])

    a_cam_bin, a_cam_uid = build_bin("A CAM", ids, a_cam_uids)
    b_cam_bin, b_cam_uid = build_bin("B CAM", ids, b_cam_uids)
    r5_bin, r5_uid = build_bin("R5", ids, r5_uids)
    pdata.append(a_cam_bin)
    pdata.append(b_cam_bin)
    pdata.append(r5_bin)

    cuts_bin, cuts_uid = build_bin("1_CUTS", ids, sequence_urefs)
    footage_bin, footage_uid = build_bin(
        "2_FOOTAGE", ids, [a_cam_uid, b_cam_uid, r5_uid],
    )
    audio_bin, audio_uid = build_bin("3_AUDIO", ids, [])
    pdata.append(cuts_bin)
    pdata.append(footage_bin)
    pdata.append(audio_bin)

    logger.info(
        "bins: 1_CUTS=%s (%d sequences), 2_FOOTAGE=%s (A CAM=%d, B CAM=%d, R5=%d), 3_AUDIO=%s (empty — audio import is a follow-up)",
        cuts_uid, len(sequence_urefs),
        footage_uid, len(a_cam_uids), len(b_cam_uids), len(r5_uids),
        audio_uid,
    )

    replace_root_bin_items(root_bin, [cuts_uid, footage_uid, audio_uid])

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
    p.add_argument("--motion-scale", type=float, default=50.0,
                   help="Motion.Scale percentage applied to every placed clip "
                        "(NBQ V6 talent default is 50%%; set to 100 to disable). "
                        "Per-clip Geometry2 transforms still apply on top via V7.")
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
        write_nbq_prproj(
            args.manifest, args.sync_groups, args.output,
            args.footage_folder,
            motion_scale_pct=args.motion_scale,
        )
    except Exception:
        logger.exception("write_nbq_prproj failed")
        raise


if __name__ == "__main__":
    main()
