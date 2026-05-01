"""Beauty pick runner — calls Opus on a prompt variant against cached candidates.

The bridge between ASI's prompt mutation loop and the scorer:
  prompt + recipe → picks → score

Workflow per recipe:
  1. Load cached scan.json + audio_cues.json + beats.json from
     ~/DevApps/roughcut-ai/runs/modal/{recipe}/
  2. Reproduce production candidate filtering (TRIGGER + QUALITY patterns,
     score, top-80) by importing roughcut-ai's beauty_pick module — keeps
     the candidate pool BYTE-IDENTICAL to production so we're optimizing
     the prompt, not the candidate selection.
  3. Build the candidates_block in production format.
  4. Substitute into the variant prompt template via simple {{var}} replace.
  5. Invoke Opus via Claude CLI subprocess (subscription auth, no API key).
  6. Parse the JSON response → list of picks.
  7. Resolve candidate_index → clip_id, t, camera (matching beauty_picks.json
     output shape so the scorer can consume it directly).

This runner does NOT modify roughcut-ai. It imports its candidate-building
code as a library to reproduce the exact production candidate pool, then
swaps the LLM call from Gemini to Opus.

Usage:
    from runners.beauty_pick_runner import run_beauty_pick_variant
    picks = run_beauty_pick_variant(prompt_text, recipe_slug="korean_fried_chicken")

The corpus name (runs/modal/{name}) may differ from the annotation slug
(annotations/{slug}.json — used for truth set lookup). The runner takes the
runs/modal name; truth-set lookup is the scorer's job.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

ROUGHCUT_ROOT = Path("/Users/dandj/DevApps/roughcut-ai")
RUNS_ROOT = ROUGHCUT_ROOT / "runs/modal"
MANIFEST_GEN = ROUGHCUT_ROOT / "tools/manifest_gen"
ROUGHCUT_SRC = ROUGHCUT_ROOT / "src"

# Candidate cap. Production beauty_pick.py v2 (post-VLM-beauty_score) uses
# CANDIDATE_CAP=300 with no per-clip cap — top-K by VLM beauty_score. We match
# that here so ASI iteration measures what production actually ships.
# PER_CLIP_CAP only applies to the legacy regex path.
CANDIDATE_CAP = 300
PER_CLIP_CAP = 30

# Extra "static beauty" patterns the production TRIGGER_PATTERNS regex
# misses. Production patterns expect action verbs (fork lifting, hand
# pouring, sauce drizzling). Editors also pick STILL hero shots — a bowl
# of finished pasta sitting on marble, garnished plate at rest, ingredients
# on a cutting board. These descriptions are passive and slip through the
# action-verb gate. Diagnostic on the 5-recipe corpus: 2 of 9 truth-pick
# misses were exactly this pattern. Adding the missing cues here promotes
# them to candidates without touching roughcut-ai.
import re as _re
EXTRA_STILL_LIFE_PATTERNS = [
    _re.compile(p, _re.IGNORECASE) for p in [
        r"\b(bowl|plate|platter|board|skillet|pot|pan)\b.*\b(filled|of|with|holding|containing)\b",
        r"\bshown\b|\brest(s|ing)?\b|\bsit(s|ting)?\b\s+on\b|\bpresented\b|\bdisplayed\b|\bplaces?\b\s+\w+\s+on(to)?\b",
        r"\bcooked\s+(spaghetti|pasta|noodles|rice|chicken|meat|vegetables?|potatoes?)\b",
        r"\b(peeled|chopped|sliced|diced)\s+\w+\s+(on|in)\b",  # prep ingredients staged
        r"\b(finished|completed|ready)\s+(dish|plate|meal|food)\b",
    ]
]

# Transcript window — asymmetric because audio is a LAGGING indicator.
# Crew reactions ("that was great", "perfect", "do it again") happen AFTER
# the take they're commenting on. So the keeper-signal for a candidate at
# source-time t lives in the window [t - LAG_BEFORE_S, t + LAG_AFTER_S],
# weighted toward AFTER. Redo requests propagate forward (the NEXT take is
# the keeper); positive reactions propagate backward (the take that just
# finished is the keeper). The prompt instructs the LLM how to read this.
TRANSCRIPT_LAG_BEFORE_S = 1.0
TRANSCRIPT_LAG_AFTER_S = 8.0


def _ensure_roughcut_imports() -> None:
    """Add roughcut-ai paths to sys.path so we can import beauty_pick code."""
    for p in (str(MANIFEST_GEN), str(ROUGHCUT_SRC)):
        if p not in sys.path:
            sys.path.insert(0, p)


def _scan_has_beauty_score(scan: dict) -> bool:
    """Detect whether the scan was produced by the v2 VLM that emits beauty_score per frame."""
    for clip in scan.get("clips", {}).values():
        for frame in clip.get("frames", []):
            if frame.get("beauty_score") is not None:
                return True
    return False


# Threshold matches production beauty_pick.py:_score_candidate v2 path.
BEAUTY_SCORE_THRESHOLD = 0.3

# Hero-band non-max-suppression (production fd64830). VLM saturation puts
# many adjacent frames at >=0.9 across a sustained beauty moment; NMS drops
# all but the peak within a window, freeing cap slots for distinct moments.
# Tuned offline by roughcut-ai against KFC + banana truth sets.
NMS_WINDOW_S = 1.5
NMS_MIN_SCORE = 0.9


def _nms_hero_band(candidates: list[dict]) -> list[dict]:
    """Non-max-suppress continuous high-score sequences within each clip."""
    above = [c for c in candidates if c["score"] >= NMS_MIN_SCORE]
    below = [c for c in candidates if c["score"] < NMS_MIN_SCORE]
    by_clip: dict[str, list[dict]] = {}
    for c in above:
        by_clip.setdefault(c["clip_id"], []).append(c)
    survivors: list[dict] = []
    for group in by_clip.values():
        group.sort(key=lambda c: -c["score"])
        suppressed = [False] * len(group)
        for i, c in enumerate(group):
            if suppressed[i]:
                continue
            survivors.append(c)
            for j in range(i + 1, len(group)):
                if not suppressed[j] and abs(group[j]["t"] - c["t"]) <= NMS_WINDOW_S:
                    suppressed[j] = True
    return survivors + below


def _build_production_candidates(recipe_slug: str) -> tuple[list[dict], dict]:
    """Reproduce production candidate filtering on cached scan/audio/beats.

    Returns (candidates_list, metadata_dict). metadata carries beats list
    and any other context the prompt template needs.

    v2 path (scan has beauty_score): top-K by VLM score, no regex, no stratification,
        no transcript injection, no per-clip cap. Production gate does this natively
        as of roughcut-ai feat/recipe-vlm-beauty-score.
    Legacy path: regex + time-stratification + transcript injection (for older
        cached scans that don't carry beauty_score).
    """
    _ensure_roughcut_imports()
    from beauty_pick import _score_candidate, TRIGGER_PATTERNS  # noqa: F401

    run_dir = RUNS_ROOT / recipe_slug
    if not run_dir.exists():
        raise FileNotFoundError(f"No cached run at {run_dir}")

    scan = json.loads((run_dir / "scan.json").read_text())
    # audio_cues optional — many cached runs are missing it (the brief flagged
    # this as a known bug, out of scope for prompt iteration). Falls back to {}.
    audio_path = run_dir / "audio_cues.json"
    audio_cues = json.loads(audio_path.read_text()) if audio_path.exists() else {}
    beats_doc = json.loads((run_dir / "beats.json").read_text()) if (run_dir / "beats.json").exists() else {}
    # Normalize beats: accept legacy list-shape OR new dict-shape ({beats: [...]})
    if isinstance(beats_doc, dict):
        beats = beats_doc.get("beats", [])
        ingredients_from_beats = beats_doc.get("ingredients", [])
    elif isinstance(beats_doc, list):
        beats = beats_doc
        ingredients_from_beats = []
    else:
        beats = []
        ingredients_from_beats = []

    # Production scan.json shape: {"clips": {clip_id: {file, duration, camera, frames[]}}}
    clip_scores = scan.get("clips", {})
    clips_info = scan.get("clips_info", {}) or clip_scores  # fallback

    if not clip_scores:
        return [], {"beats": beats, "scan": scan}

    # v2 path: VLM-rated frames. Skip the entire regex + stratification + transcript
    # pipeline — production gate handles those concerns natively now. Just take the
    # top-K frames by beauty_score above threshold.
    if _scan_has_beauty_score(scan):
        v2_candidates: list[dict] = []
        for clip_id, clip_data in clip_scores.items():
            camera = clip_data.get("camera", "v1")
            clip_dur = clip_data.get("duration") or 0.0
            for frame in clip_data.get("frames", []):
                bs = frame.get("beauty_score")
                if bs is None or bs < BEAUTY_SCORE_THRESHOLD:
                    continue
                v2_candidates.append({
                    "clip_id": clip_id,
                    "t": frame.get("t", 0),
                    "camera": camera,
                    "score": float(bs),
                    "vlm_description": frame.get("description", "") or "",
                    "beauty_kind": frame.get("beauty_kind"),
                    "clip_duration": clip_dur,
                })
        v2_candidates = _nms_hero_band(v2_candidates)
        v2_candidates.sort(key=lambda c: c["score"], reverse=True)
        # Per-clip cap on v2 path TESTED 2026-05-02 and reverted. Tradeoffs:
        #   cap=8:  reachability 74% → 63% (too tight, drops truth picks)
        #   cap=15: corpus 0.274 → 0.270 (tied), but KFC stdev exploded
        #           ±0.029 → ±0.208 — KFC's truth picks concentrated on
        #           B19I6339 sometimes survive the cap, sometimes don't.
        # Conclusion: editor patterns differ per recipe. KFC = many picks on
        # one clip (cap hurts), chicken_thighs = picks across many clips
        # (cap might help). A single global per-clip cap can't satisfy both.
        # Skipping for now; revisit when we have recipe-aware cap logic.
        v2_candidates = v2_candidates[:CANDIDATE_CAP]
        # Audio kept ON — it's a real signal in the pipeline. The two earlier
        # shapes (raw transcripts, structured flags + signal text) overwhelmed
        # the picker; this minimal shape only attaches the boolean flag, no
        # raw text in the candidates_block. Picker treats it as a hint, not
        # an instruction.
        _attach_audio_signals(v2_candidates, audio_cues)
        return v2_candidates, {
            "beats": beats,
            "scan": scan,
            "audio_cues": audio_cues,
            "ingredients": ingredients_from_beats,
        }

    # Legacy path: production beauty_pick.py uses a position-aware tail-region heuristic
    # that restricts eligible clips to the last 20% of shoot order. That works
    # for KFC/recipes where the hero is shot last, but fails when the editor
    # uses cold-open clips shot earlier (banana_muffins, creamy_potato_soup).
    # The TRIGGER_PATTERNS regex on per-frame VLM descriptions is already a
    # strong gate — open eligibility to all clips, let scoring + cap decide.
    eligible_clips = set(clip_scores.keys())

    # Pass 2: score frames within eligible clips. Production scoring uses
    # TRIGGER_PATTERNS (action verbs) as a strict gate — frames not matching
    # score 0 and never become candidates. We supplement with EXTRA_STILL_LIFE_PATTERNS
    # for static beauty shots ("bowl of spaghetti shown", "garnished plate
    # at rest") that the production regex misses. Score is uniform 1.0 for
    # these (no position bonus) so they don't dominate; just enough to let
    # them enter the pool and be considered alongside action-driven candidates.
    candidates: list[dict] = []
    for clip_id in eligible_clips:
        clip_data = clip_scores.get(clip_id, {})
        frames = clip_data.get("frames", [])
        clip_dur = clip_data.get("duration") or 0.0
        camera = clip_data.get("camera", "v1")
        for frame in frames:
            score = _score_candidate(frame, clip_id, clip_scores, audio_cues, clip_dur)
            if score == 0:
                # Action-verb regex didn't match — try still-life patterns.
                desc = frame.get("description", "") or ""
                if any(p.search(desc) for p in EXTRA_STILL_LIFE_PATTERNS):
                    score = 1.0
            if score > 0:
                candidates.append({
                    "clip_id": clip_id,
                    "t": frame.get("t", 0),
                    "camera": camera,
                    "score": score,
                    "vlm_description": frame.get("description", "") or "",
                    "clip_duration": clip_dur,
                })

    # Stratify by clip + by TIME so the editor's actual moment isn't lost.
    # Production beauty_pick.py's position bonus (+0.2 if t > 70% of clip
    # duration) pushes late-clip frames to the top of any score sort. After
    # global cap=N, the pool fills with late frames and mid-clip beauty
    # picks (e.g. creamy_potato_soup AI2I4942 at 29s in a 68s clip — 43% in)
    # get cut. Two-step fix:
    #   1. Per clip, take PER_CLIP_CAP evenly-spaced samples by TIME.
    #   2. Round-robin interleave across clips up to CANDIDATE_CAP so every
    #      clip's stratified samples make it into the pool. Score-sort
    #      happens at end purely for display ordering.
    by_clip: dict[str, list[dict]] = {}
    for c in candidates:
        by_clip.setdefault(c["clip_id"], []).append(c)
    per_clip_samples: dict[str, list[dict]] = {}
    for cid, group in by_clip.items():
        if len(group) <= PER_CLIP_CAP:
            per_clip_samples[cid] = sorted(group, key=lambda c: c["t"])
        else:
            group_by_time = sorted(group, key=lambda c: c["t"])
            step = len(group_by_time) / PER_CLIP_CAP
            per_clip_samples[cid] = [group_by_time[int(i * step)]
                                     for i in range(PER_CLIP_CAP)]

    # Round-robin: pull one frame at a time from each clip's stratified
    # samples until the budget is full. Guarantees every clip is represented
    # before any single clip dominates.
    stratified: list[dict] = []
    cursors = {cid: 0 for cid in per_clip_samples}
    while len(stratified) < CANDIDATE_CAP:
        progress = False
        for cid in list(per_clip_samples.keys()):
            if cursors[cid] >= len(per_clip_samples[cid]):
                continue
            stratified.append(per_clip_samples[cid][cursors[cid]])
            cursors[cid] += 1
            progress = True
            if len(stratified) >= CANDIDATE_CAP:
                break
        if not progress:
            break  # all clips exhausted

    stratified.sort(key=lambda c: c["score"], reverse=True)
    candidates = stratified
    # Inject transcript windows from per-clip transcript_*.json (audio_cues.json
    # is empty for most cached recipes — known parser bug — but the transcripts
    # are intact and carry the keeper-vs-mid-take signal directly).
    _inject_transcript_windows(candidates, run_dir)
    return candidates, {
        "beats": beats,
        "scan": scan,
        "audio_cues": audio_cues,
        "ingredients": ingredients_from_beats,
    }


AUDIO_LAG_BEFORE_S = 2.0   # crew_redo / direction can come slightly BEFORE the take
AUDIO_LAG_AFTER_S = 8.0    # crew_positive lags the take by up to ~8s

# Audio cue types from roughcut-ai/audio_cue_extraction prompt.
KEEPER_TYPES = {"crew_positive"}
REJECT_TYPES = {"crew_redo"}


def _attach_audio_signals(candidates: list[dict], audio_cues: dict) -> None:
    """Attach REJECT-only audio signals.

    Empirical finding (2026-05-02): crew_positive is baseline noise — the crew
    is positive on ~90% of takes whether they're keepers or not. So a positive
    cue near a candidate doesn't actually predict editor choice. Editors often
    pick takes with NO audio context at all (silent shooting moments).

    crew_redo is the high-signal cue: it explicitly means "the take that just
    finished was NOT the keeper — try again". A candidate with crew_redo in
    the AFTER window is by definition mid-take, not final.

    Logic:
      audio_reject = True iff a crew_redo cue exists within AFTER window.
      audio_signals = list of redo events for diagnostics.
      No audio_keeper flag — that signal is too noisy to use.
    """
    for c in candidates:
        cid = c["clip_id"]
        t = float(c["t"])
        cues = audio_cues.get(cid) or []
        win_lo = t - AUDIO_LAG_BEFORE_S
        win_hi = t + AUDIO_LAG_AFTER_S
        nearby = [cue for cue in cues
                  if isinstance(cue, dict)
                  and cue.get("t") is not None
                  and win_lo <= float(cue["t"]) <= win_hi]
        reject = any((cue.get("type") in REJECT_TYPES) for cue in nearby)
        c["audio_reject"] = reject
        c["audio_signals"] = [
            {"t": round(float(cue["t"]) - t, 1),
             "type": cue.get("type"),
             "text": (cue.get("text", "") or "")[:80]}
            for cue in nearby
            if cue.get("type") in REJECT_TYPES
        ][:2]


def _inject_transcript_windows(candidates: list[dict], run_dir: Path) -> None:
    """For each candidate, slice the per-clip transcript file to the window
    [t - LAG_BEFORE, t + LAG_AFTER] and stitch it into candidate['transcript_window'].

    Audio is a lagging indicator: the crew's keeper/redo reaction comes AFTER
    the take, so the window is heavily weighted toward AFTER the candidate's
    source-time. The prompt template tells the LLM how to read this.
    """
    transcript_cache: dict[str, list[dict]] = {}
    for c in candidates:
        cid = c["clip_id"]
        if cid not in transcript_cache:
            tpath = run_dir / f"transcript_{cid}.json"
            if not tpath.exists():
                transcript_cache[cid] = []
                continue
            try:
                tdoc = json.loads(tpath.read_text())
                transcript_cache[cid] = tdoc.get("segments", []) or []
            except (json.JSONDecodeError, OSError):
                transcript_cache[cid] = []
        segments = transcript_cache[cid]
        if not segments:
            continue
        t = float(c["t"])
        win_lo = t - TRANSCRIPT_LAG_BEFORE_S
        win_hi = t + TRANSCRIPT_LAG_AFTER_S
        # Whisper segments span [start, end]. Include any that overlap the window.
        chunks = []
        for seg in segments:
            s_start = seg.get("start")
            s_end = seg.get("end")
            if s_start is None or s_end is None:
                continue
            if s_end < win_lo or s_start > win_hi:
                continue
            text = (seg.get("text") or "").strip()
            if text:
                # Tag each segment with relative time so the LLM can tell
                # before-vs-after the candidate moment.
                rel = round(s_start - t, 1)
                marker = "PRE" if rel < 0 else "POST"
                chunks.append(f"[{marker}{rel:+.1f}s] {text}")
        c["transcript_window"] = " | ".join(chunks) if chunks else ""


def _build_leave_one_out_examples(
    held_out_recipe: str,
    truth_dir: Path,
    runs_root: Path,
    n_examples: int = 4,
) -> str:
    """Build few-shot examples from OTHER recipes' truth sets.

    Held-out / leave-one-out: when evaluating recipe X, the few-shot block
    contains examples from recipes ≠ X. Prevents truth leakage. Each example
    shows the editor's actual pick in the same candidate-line format the
    prompt uses, so Opus learns the mapping pattern (clip+t+VLM+audio →
    is/isn't a beauty pick).

    Returns formatted block ready to substitute into {{few_shot_block}}.
    Empty string if no examples can be assembled.
    """
    # Map runs_modal name → annotation slug for truth lookup. Hardcoded
    # because creamy_potato_soup vs banana_muffins-vs-easy_banana_muffins.
    name_map = {
        "basil_pesto": "basil_pesto",
        "chicken_thighs": "chicken_thighs",
        "korean_fried_chicken": "korean_fried_chicken",
        "creamy_potato_soup": "creamy_potato_soup",
        "easy_banana_muffins": "banana_muffins",
    }

    # Pool examples from all recipes except the held-out one.
    examples: list[dict] = []
    for runs_name, ann_slug in name_map.items():
        if runs_name == held_out_recipe:
            continue
        truth_file = truth_dir / ann_slug / "beauty.json"
        if not truth_file.exists():
            continue
        try:
            picks = json.loads(truth_file.read_text()).get("picks", [])
        except (json.JSONDecodeError, OSError):
            continue
        # Find each pick's matching candidate (for VLM + transcript context).
        try:
            cands, _ = _build_production_candidates(runs_name)
        except Exception:
            continue
        for p in picks:
            cid = p["clip_id"]
            t_in = float(p["t_in"])
            t_out = float(p.get("t_out", t_in))
            # Find the closest candidate within the editor's used span.
            in_span = [c for c in cands if c["clip_id"] == cid
                       and (t_in - 1) <= c["t"] <= (t_out + 1)]
            if not in_span:
                continue
            cand = min(in_span, key=lambda c: abs(c["t"] - (t_in + t_out) / 2))
            examples.append({
                "recipe": runs_name,
                "category": p.get("category", "?"),
                "clip_id": cid,
                "t": cand["t"],
                "camera": cand.get("camera", "?"),
                "vlm": cand.get("vlm_description", ""),
                "audio": cand.get("transcript_window", ""),
                "label": p.get("label", ""),
            })

    if not examples:
        return ""

    # Pick a balanced sample: prefer alternating open/final + recipe variety.
    # Sort: opens first, then finals, then by recipe so we get diverse coverage.
    examples.sort(key=lambda e: (e["category"] != "open", e["recipe"]))
    seen_recipes: set[str] = set()
    chosen: list[dict] = []
    # First pass: one per recipe, alternating category if possible.
    for e in examples:
        if e["recipe"] in seen_recipes:
            continue
        chosen.append(e)
        seen_recipes.add(e["recipe"])
        if len(chosen) >= n_examples:
            break
    # Pad with repeats if we have fewer recipes than n_examples requested.
    if len(chosen) < n_examples:
        for e in examples:
            if e in chosen:
                continue
            chosen.append(e)
            if len(chosen) >= n_examples:
                break

    lines = ["Examples from OTHER recipes — what the editor actually picked. "
             "Use these to calibrate; the input recipe will look different but "
             "the PATTERN (which moment in which clip + audio context = a "
             "keeper) is the same:"]
    for i, e in enumerate(chosen, 1):
        audio = f"\n     Audio: {e['audio']}" if e["audio"] else ""
        lines.append(
            f"  Example {i} ({e['recipe']}, category={e['category']}):\n"
            f"     clip={e['clip_id']} t={e['t']:.1f}s camera={e['camera']}\n"
            f"     VLM: {e['vlm']}{audio}\n"
            f"     Editor's note: {e['label']}"
        )
    return "\n".join(lines)


def _format_candidates_block(candidates: list[dict]) -> str:
    """Match production beauty_pick._build_prompt's candidates_block format.

    Audio flag is REJECT-only (crew_redo in lag window). crew_positive is
    treated as baseline noise — too prevalent to be a real keeper signal.
    """
    lines = []
    for i, c in enumerate(candidates):
        flag_str = " [audio: REDO]" if c.get("audio_reject") else ""
        sig_lines = ""
        for sig in (c.get("audio_signals") or [])[:1]:
            sig_lines += f"\n      crew @ {sig['t']:+.1f}s: \"{sig['text']}\""
        lines.append(
            f"  [{i}] clip={c['clip_id']} t={c['t']:.1f}s camera={c['camera']} "
            f"score={c['score']}{flag_str}\n"
            f"    VLM: {c['vlm_description']}{sig_lines}"
        )
    return "\n".join(lines)


def _resolve_dish_name(beats: list[dict], recipe_slug: str) -> str:
    if not beats:
        return recipe_slug.replace("_", " ").title()
    for b in reversed(beats):
        if (b.get("type") or "").lower() == "beauty":
            name = b.get("beat") or ""
            if name:
                return name
    return (beats[-1].get("beat") if beats else None) or recipe_slug.replace("_", " ").title()


def _substitute(template: str, variables: dict) -> str:
    out = template
    for k, v in variables.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


# Image-mode constants. Lower cap because each frame is ~1500 tokens of image
# input plus Opus must Read each file via the CLI's tool path. 30 frames keeps
# context dense without hammering the session.
IMAGE_MODE_CAP = 10


def _frame_path_for_candidate(c: dict, recipe_slug: str) -> Optional[Path]:
    """Resolve a candidate's clip_id+t to the dino-extracted JPEG.

    Convention from fast_scan.py: frames extracted at DINO_FPS=1.0 to
    scan_frames/scan_frames/_dino_<clip_id>/frame_NNNN.jpg (1-indexed).
    Round candidate.t to the nearest second. Falls back to nearest existing
    frame if the rounded number isn't on disk (clips that started mid-second
    or had partial frame extraction).
    """
    # Some recipes have scan_frames/_dino_<cid>/ (single nesting), others
    # have scan_frames/scan_frames/_dino_<cid>/ (double nesting from a
    # tarball-extraction quirk). Try both.
    recipe_root = RUNS_ROOT / recipe_slug / "scan_frames"
    candidates_roots = [
        recipe_root / f"_dino_{c['clip_id']}",
        recipe_root / "scan_frames" / f"_dino_{c['clip_id']}",
    ]
    base = next((p for p in candidates_roots if p.exists()), None)
    if base is None:
        return None
    # 1-indexed: t=0 → frame_0001, t=10 → frame_0011
    target_n = int(round(c["t"])) + 1
    target = base / f"frame_{target_n:04d}.jpg"
    if target.exists():
        return target
    # Fall back to nearest neighbor — handle off-by-one in rounding edge cases
    candidates = sorted(base.glob("frame_*.jpg"))
    if not candidates:
        return None
    nearest = min(candidates, key=lambda p: abs(int(p.stem.split("_")[1]) - target_n))
    return nearest


def _call_opus_cli_freeform(prompt_text: str, timeout_s: int = 300, add_dirs: Optional[list[Path]] = None) -> str:
    """Call Opus without forcing JSON. Returns full free-form response.

    JSON-only mode brittle when picker needs to reason. This call lets Opus
    write reasoning + JSON or whatever shape the prompt asks for. Parser
    handles extraction downstream.
    """
    cmd = [
        "claude", "-p", prompt_text,
        "--model", "claude-opus-4-7",
        "--output-format", "text",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--exclude-dynamic-system-prompt-sections",
    ]
    if add_dirs:
        for d in add_dirs:
            cmd.extend(["--add-dir", str(d)])
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout_s,
        check=False, cwd=tempfile.gettempdir(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed (rc={result.returncode}): {result.stderr[:500]}")
    return result.stdout


def _call_opus_cli(prompt_text: str, timeout_s: int = 300, add_dirs: Optional[list[Path]] = None) -> str:
    """Invoke Opus via Claude CLI in non-interactive mode.

    Uses the user's subscription auth — no ANTHROPIC_API_KEY required.
    Runs from a clean tmp cwd to avoid CLAUDE.md / project-context
    contamination (Claude Code in a project dir interprets `-p <text>` as
    a Claude Code task, not a raw LLM completion). Disables slash commands,
    excludes dynamic system-prompt sections, no session persistence — we
    want the lightest possible LLM-completion behavior.

    Returns raw stdout text. Caller parses JSON.
    """
    cmd = [
        "claude", "-p", prompt_text,
        "--model", "claude-opus-4-7",
        "--output-format", "text",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--exclude-dynamic-system-prompt-sections",
        "--append-system-prompt",
        "You are a JSON-emitting LLM endpoint. Do NOT plan, ask "
        "clarifying questions, or write commentary. Read the user "
        "prompt, follow its instructions, and emit ONLY the requested "
        "JSON object as your entire response. No prose before, after, "
        "or around the JSON. No code fences.",
    ]
    if add_dirs:
        for d in add_dirs:
            cmd.extend(["--add-dir", str(d)])
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            cwd=tempfile.gettempdir(),
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Opus call timed out after {timeout_s}s") from e
    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed (rc={result.returncode}): {result.stderr[:500]}"
        )
    return result.stdout


def _parse_picks_response(raw: str, candidates: list[dict]) -> list[dict]:
    """Parse Opus JSON response, resolve candidate_index → clip metadata.

    Output shape matches beauty_picks.json `picks[]`: clip_id, t, camera,
    category, label, confidence, reasoning, vlm_description.
    """
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    cleaned = re.sub(r"```json\s*", "", cleaned)
    cleaned = re.sub(r"```\s*", "", cleaned)
    # Find the first top-level JSON object — Opus may wrap with prose.
    m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    raw_picks = data.get("picks") if isinstance(data, dict) else (data if isinstance(data, list) else [])

    out = []
    for p in raw_picks or []:
        if not isinstance(p, dict):
            continue
        idx = p.get("candidate_index")
        if not isinstance(idx, int) or idx < 0 or idx >= len(candidates):
            continue
        cand = candidates[idx]
        cat = p.get("category", "")
        if cat not in ("open", "final"):
            cat = ""  # tolerate v1 prompts that don't emit category
        out.append({
            "label": p.get("label", "beauty"),
            "category": cat,
            "clip_id": cand["clip_id"],
            "t": float(cand["t"]),
            "camera": cand["camera"],
            "confidence": float(p.get("confidence", 0.5) or 0.5),
            "reasoning": p.get("reasoning", ""),
            "vlm_description": cand.get("vlm_description", ""),
        })
    return out


BATCH_SIZE = 60   # candidates per call; cognitive-load sweet spot
PICKS_PER_BATCH = 3   # ask picker to nominate 3 from each batch


def _parse_picks_freeform(raw: str, candidates: list[dict]) -> tuple[list[dict], str]:
    """Extract picks JSON from a free-form response. Return (picks, full_reasoning_text).

    Free-form means the picker may write reasoning before/after the JSON. We
    locate the JSON block (first `{...}` containing "picks") and parse just
    that. Everything outside the JSON block is treated as reasoning prose.
    """
    # Find the picks JSON block — non-greedy, look for "picks" key
    json_match = re.search(r"\{[^{}]*\"picks\"\s*:\s*\[.*?\]\s*\}", raw, flags=re.DOTALL)
    if not json_match:
        # Fallback: any top-level JSON object
        json_match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    reasoning = raw
    picks_data = []
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            picks_data = parsed.get("picks") if isinstance(parsed, dict) else parsed
            if not isinstance(picks_data, list):
                picks_data = []
            # Reasoning = response with the JSON block stripped out
            reasoning = (raw[:json_match.start()] + raw[json_match.end():]).strip()
        except json.JSONDecodeError:
            pass

    out = []
    for p in picks_data or []:
        if not isinstance(p, dict):
            continue
        idx = p.get("candidate_index")
        if not isinstance(idx, int) or idx < 0 or idx >= len(candidates):
            continue
        cand = candidates[idx]
        cat = p.get("category", "")
        if cat not in ("open", "final"):
            cat = ""
        out.append({
            "label": p.get("label", "beauty"),
            "category": cat,
            "clip_id": cand["clip_id"],
            "t": float(cand["t"]),
            "camera": cand["camera"],
            "confidence": float(p.get("confidence", 0.5) or 0.5),
            "reasoning": p.get("reasoning", ""),
            "vlm_description": cand.get("vlm_description", ""),
        })
    return out, reasoning


def run_beauty_pick_variant_batched(
    prompt_template: str,
    recipe_slug: str,
    candidates: Optional[list[dict]] = None,
    metadata: Optional[dict] = None,
    batch_size: int = BATCH_SIZE,
    picks_per_batch: int = PICKS_PER_BATCH,
) -> dict:
    """Batched picker — splits candidates into smaller groups, picks N per batch.

    Reduces cognitive load: each call sees ~60 candidates instead of 300, asks
    for 3 best from THIS batch. Picks union across batches. Free-form output
    preserves reasoning per batch for debugging.

    Output:
      picks: union across batches (deduped by clip_id+t within ±2s)
      reasoning: list of per-batch full responses (for debug)
      candidate_count: total candidates across batches
    """
    if candidates is None or metadata is None:
        candidates, metadata = _build_production_candidates(recipe_slug)
    if not candidates:
        return {"picks": [], "reasoning": [], "candidate_count": 0}

    # Sort by score descending so best candidates are in earliest batches
    candidates.sort(key=lambda c: c["score"], reverse=True)
    batches = [candidates[i:i + batch_size] for i in range(0, len(candidates), batch_size)]

    dish_name = _resolve_dish_name(metadata.get("beats", []), recipe_slug)
    ingredients = metadata.get("ingredients") or []
    ingredients_str = ", ".join(ingredients) if ingredients else "(none)"

    # Few-shot computed once and reused across batches
    few_shot_block = ""
    if "{{few_shot_block}}" in prompt_template:
        truth_dir = Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/truth_sets")
        few_shot_block = _build_leave_one_out_examples(
            held_out_recipe=recipe_slug, truth_dir=truth_dir, runs_root=RUNS_ROOT,
        )

    all_picks: list[dict] = []
    all_reasoning: list[dict] = []

    for batch_idx, batch in enumerate(batches):
        candidates_block = _format_candidates_block(batch)
        # Inject batch-specific framing into the candidates block intro so the
        # picker knows it's seeing one slice of the corpus.
        batch_intro = (f"BATCH {batch_idx + 1} of {len(batches)} — "
                       f"these are {len(batch)} of {len(candidates)} total "
                       f"candidates for this recipe, selected from highest VLM "
                       f"beauty score downward.\n")
        prompt_text = _substitute(prompt_template, {
            "dish_name": dish_name,
            "ingredients_list": ingredients_str,
            "candidates_block": batch_intro + candidates_block,
            "num_candidates": str(len(batch)),
            "few_shot_block": few_shot_block,
            "picks_per_batch": str(picks_per_batch),
        })
        raw = _call_opus_cli_freeform(prompt_text, timeout_s=240)
        picks, reasoning_text = _parse_picks_freeform(raw, batch)
        all_picks.extend(picks)
        all_reasoning.append({
            "batch_idx": batch_idx,
            "batch_size": len(batch),
            "n_picks": len(picks),
            "reasoning": reasoning_text,
            "raw_response": raw,
        })

    # Dedupe picks across batches: same clip_id within ±2s = duplicate
    deduped: list[dict] = []
    for p in all_picks:
        is_dup = any(
            d["clip_id"] == p["clip_id"] and abs(d["t"] - p["t"]) <= 2.0
            for d in deduped
        )
        if not is_dup:
            deduped.append(p)

    return {
        "picks": deduped,
        "reasoning": all_reasoning,
        "candidate_count": len(candidates),
        "batch_count": len(batches),
    }


def run_beauty_pick_variant_image_mode(
    prompt_template: str,
    recipe_slug: str,
    candidates: Optional[list[dict]] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Image-mode picker — Opus reads frame JPEGs alongside metadata.

    Top IMAGE_MODE_CAP candidates by VLM beauty_score get their JPEG paths
    resolved + listed in the prompt with explicit "Read frame_NNNN.jpg"
    instructions. Opus uses its Read tool to ingest the images, then
    judges beauty visually instead of relying on prose descriptions.

    Trade-off: smaller pool (30 vs 300) but visual judgment per frame.
    """
    if candidates is None or metadata is None:
        candidates, metadata = _build_production_candidates(recipe_slug)
    if not candidates:
        return {"picks": [], "prompt_text": "", "raw_response": "", "candidate_count": 0}

    # Take the top IMAGE_MODE_CAP by score, resolve JPEG paths
    top = candidates[:IMAGE_MODE_CAP]
    enriched = []
    add_dirs = set()
    for c in top:
        path = _frame_path_for_candidate(c, recipe_slug)
        if path is None:
            continue
        enriched.append({**c, "frame_path": str(path)})
        # The dino-frames root is the first --add-dir we need
        add_dirs.add(path.parent.parent)
    if not enriched:
        return {"picks": [], "prompt_text": "", "raw_response": "no frames resolved",
                "candidate_count": 0}

    # Format candidates with explicit image references
    cand_lines = []
    for i, c in enumerate(enriched):
        audio = f"\n    Audio: {c['transcript_window']}" if c.get("transcript_window") else ""
        bk = f" [kind={c['beauty_kind']}]" if c.get("beauty_kind") else ""
        cand_lines.append(
            f"  [{i}] frame_path={c['frame_path']}\n"
            f"    clip={c['clip_id']} t={c['t']:.1f}s camera={c['camera']} score={c['score']:.2f}{bk}\n"
            f"    VLM: {c.get('vlm_description', '')}{audio}"
        )
    candidates_block = "\n".join(cand_lines)

    dish_name = _resolve_dish_name(metadata.get("beats", []), recipe_slug)
    ingredients = metadata.get("ingredients") or []
    ingredients_str = ", ".join(ingredients) if ingredients else "(none)"

    few_shot_block = ""
    if "{{few_shot_block}}" in prompt_template:
        truth_dir = REPO_ROOT / "truth_sets" if False else Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/truth_sets")
        few_shot_block = _build_leave_one_out_examples(
            held_out_recipe=recipe_slug, truth_dir=truth_dir, runs_root=RUNS_ROOT,
        )

    prompt_text = _substitute(prompt_template, {
        "dish_name": dish_name,
        "ingredients_list": ingredients_str,
        "candidates_block": candidates_block,
        "num_candidates": str(len(enriched)),
        "few_shot_block": few_shot_block,
    })

    raw = _call_opus_cli(prompt_text, timeout_s=600, add_dirs=list(add_dirs))
    picks = _parse_picks_response(raw, enriched)

    return {
        "picks": picks,
        "prompt_text": prompt_text,
        "raw_response": raw,
        "candidate_count": len(enriched),
    }


def run_beauty_pick_variant(
    prompt_template: str,
    recipe_slug: str,
    candidates: Optional[list[dict]] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Run one prompt variant against one recipe's cached candidates.

    Args:
      prompt_template: jinja-ish template text with {{dish_name}},
                       {{ingredients_list}}, {{candidates_block}},
                       {{num_candidates}} placeholders.
      recipe_slug: runs/modal/{slug} dir name (e.g. korean_fried_chicken).
      candidates: optional pre-built candidates list (skips re-derivation).
      metadata: optional pre-built {beats, scan, audio_cues}.

    Returns {picks, prompt_text, raw_response, candidate_count}.
    """
    if candidates is None or metadata is None:
        candidates, metadata = _build_production_candidates(recipe_slug)
    if not candidates:
        return {"picks": [], "prompt_text": "", "raw_response": "", "candidate_count": 0}

    candidates_block = _format_candidates_block(candidates)
    dish_name = _resolve_dish_name(metadata.get("beats", []), recipe_slug)
    ingredients = (
        metadata.get("ingredients")
        or (metadata.get("scan") or {}).get("scan_config", {}).get("ingredients")
        or []
    )
    ingredients_str = ", ".join(ingredients) if ingredients else "(none)"

    # Few-shot leave-one-out examples — only if the prompt template includes
    # the {{few_shot_block}} marker (so prompts can opt in/out).
    few_shot_block = ""
    if "{{few_shot_block}}" in prompt_template:
        truth_dir = Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline/truth_sets")
        few_shot_block = _build_leave_one_out_examples(
            held_out_recipe=recipe_slug, truth_dir=truth_dir, runs_root=RUNS_ROOT,
        )

    prompt_text = _substitute(prompt_template, {
        "dish_name": dish_name,
        "ingredients_list": ingredients_str,
        "candidates_block": candidates_block,
        "num_candidates": str(len(candidates)),
        "few_shot_block": few_shot_block,
    })

    raw = _call_opus_cli(prompt_text)
    picks = _parse_picks_response(raw, candidates)

    return {
        "picks": picks,
        "prompt_text": prompt_text,
        "raw_response": raw,
        "candidate_count": len(candidates),
    }


def run_corpus(prompt_template: str, recipes: list[str]) -> dict[str, dict]:
    """Run a prompt variant against multiple recipes. Returns {recipe: result}."""
    out = {}
    for recipe in recipes:
        try:
            out[recipe] = run_beauty_pick_variant(prompt_template, recipe)
        except Exception as e:
            out[recipe] = {"error": str(e), "picks": [], "candidate_count": 0}
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--prompt", required=True, help="Path to prompt template (jinja2)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    template = Path(args.prompt).read_text()
    result = run_beauty_pick_variant(template, args.recipe)
    out_text = json.dumps({
        "recipe": args.recipe,
        "candidate_count": result["candidate_count"],
        "n_picks": len(result["picks"]),
        "picks": result["picks"],
    }, indent=2)
    if args.output:
        Path(args.output).write_text(out_text)
        print(f"Wrote {args.output}")
    else:
        print(out_text)
