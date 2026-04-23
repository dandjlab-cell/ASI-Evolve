#!/usr/bin/env python3
"""
Rule-based editorial scorer.

Scores a pipeline edit (or annotation JSON) against Dan's editorial rules.
Unlike score.py (which checks clip-level matching), this checks whether
the edit respects editorial logic:

  Rule 1: Anchor shot — is there a clear best-take driving each section?
  Rule 2: Dump sequence camera hold — no rapid F→O→F→O during ingredient runs
  Rule 3: MOGRT duration vs text readability — hold time correlates with text length
  Rule 4: Organic flourishes — speed ramps on unattended transformations

Usage:
    python score_rules.py annotations/basil_pesto.json
    python score_rules.py --dir annotations/
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


def get_camera(beat: dict) -> str:
    """Extract camera string from a beat's camera field (may be str or dict)."""
    cam = beat.get("camera", "unknown")
    if isinstance(cam, dict):
        return cam.get("choice", "unknown")
    return str(cam)


def find_dump_sequences(beats: List[dict]) -> List[List[int]]:
    """Find consecutive runs of ingredient-dump beats.

    A dump sequence is consecutive beats where beat_type is 'ingredient'
    or the beat has MOGRT ingredient text overlays. Beauty openers are
    excluded even if they have title card overlays. Non-ingredient beats
    break the sequence — no sandwiching.
    """
    sequences = []
    current_run = []

    for i, beat in enumerate(beats):
        # Skip beauty openers — they have MOGRTs (title cards) but aren't dumps
        if beat.get("beat_type") == "beauty_opener":
            if len(current_run) >= 2:
                sequences.append(current_run)
            current_run = []
            continue

        is_ingredient = (
            beat.get("beat_type") == "ingredient"
            or "ingredient dump" in str(beat.get("recipe_section", "")).lower()
        )

        if is_ingredient:
            current_run.append(i)
        else:
            if len(current_run) >= 2:
                sequences.append(current_run)
            current_run = []

    if len(current_run) >= 2:
        sequences.append(current_run)

    return sequences


def score_dump_camera_hold(beats: List[dict]) -> dict:
    """Rule 2: Camera should hold during ingredient dump sequences.

    Penalty for rapid alternation (switching every 1-2 beats).
    No penalty for holds or for switching after 3+ beats on same camera.

    Returns:
        score: 0.0-1.0 (1.0 = no rapid alternation)
        violations: list of violation descriptions
        dump_sequences: the sequences found
    """
    sequences = find_dump_sequences(beats)

    if not sequences:
        return {"score": 1.0, "violations": [], "dump_sequences": []}

    total_transitions = 0
    rapid_alternations = 0
    violations = []
    seq_details = []

    for seq_idx, seq in enumerate(sequences):
        cameras = [get_camera(beats[i]) for i in seq]
        seq_detail = {
            "beats": [beats[i].get("beat_index", i) for i in seq],
            "cameras": cameras,
            "rapid_switches": [],
        }

        # Two-pass approach:
        # Pass 1: identify justified switches (flourish/nested)
        # Pass 2: check remaining switches for rapid alternation
        justified = set()
        for j in range(1, len(cameras)):
            if cameras[j] != cameras[j - 1]:
                beat_j = beats[seq[j]]
                effects = str(beat_j.get("effects", beat_j.get("effects_info", ""))).lower()
                filename = str(beat_j.get("filename", "")).lower()
                is_nested = "[nest]" in filename or beat_j.get("nested", False)
                has_speed_ramp = "speed" in effects and "ramp" in effects

                if has_speed_ramp or is_nested:
                    justified.add(j)
                    seq_detail.setdefault("justified_switches", []).append({
                        "beat": beat_j.get("beat_index", seq[j]),
                        "reason": "flourish (speed ramp)" if has_speed_ramp else "nested sequence",
                    })

        # Build effective camera sequence (skip justified-switch beats)
        effective = [(j, cameras[j]) for j in range(len(cameras)) if j not in justified]

        eff_run_length = 1
        eff_switch_count = 0
        for k in range(1, len(effective)):
            j_curr, cam_curr = effective[k]
            j_prev, cam_prev = effective[k - 1]

            if cam_curr != cam_prev:
                total_transitions += 1
                eff_switch_count += 1

                is_alternation = (
                    k >= 2
                    and cam_curr == effective[k - 2][1]
                    and cam_curr != cam_prev
                )
                too_frequent = eff_switch_count >= 2 and eff_run_length <= 1

                if is_alternation or too_frequent:
                    rapid_alternations += 1
                    beat_idx = beats[seq[j_curr]].get("beat_index", seq[j_curr])
                    prev_idx = beats[seq[j_prev]].get("beat_index", seq[j_prev])
                    violations.append(
                        f"Dump seq {seq_idx + 1}: rapid alternation {cam_prev}→{cam_curr} "
                        f"at beat {prev_idx}→{beat_idx} (held only {eff_run_length} beat{'s' if eff_run_length > 1 else ''})"
                    )
                    seq_detail["rapid_switches"].append(beat_idx)
                eff_run_length = 1
            else:
                eff_run_length += 1

        seq_details.append(seq_detail)

    if total_transitions == 0:
        score = 1.0
    else:
        score = 1.0 - (rapid_alternations / total_transitions)
        score = max(0.0, score)

    return {
        "score": round(score, 4),
        "violations": violations,
        "total_transitions": total_transitions,
        "rapid_alternations": rapid_alternations,
        "dump_sequences": seq_details,
    }


def score_mogrt_text_readability(beats: List[dict]) -> dict:
    """Rule 3: MOGRT hold duration should correlate with text length.

    Longer ingredient names need longer holds. We check:
    - Is there variance in MOGRT beat durations? (all same = not adapting)
    - Do longer text overlays get longer holds?

    Returns:
        score: 0.0-1.0
        details: correlation info
    """
    mogrt_beats = []
    for beat in beats:
        overlaps = beat.get("mogrt_overlaps", [])
        if not overlaps:
            continue
        dur = beat.get("duration", 0)
        if isinstance(dur, dict):
            dur = dur.get("seconds", 0)
        dur = float(dur) if dur else 0

        # Estimate text length from overlay description
        # MOGRTs are formatted like "K SEO_Ingredient Text_MOGRT/... (3.9s-5.2s)"
        # We use the overlay duration as proxy for text length
        total_overlay_dur = 0
        for o in overlaps:
            # Parse "(3.9s-5.2s)" pattern
            import re
            m = re.search(r'\((\d+\.?\d*)s-(\d+\.?\d*)s\)', o)
            if m:
                o_dur = float(m.group(2)) - float(m.group(1))
                total_overlay_dur += o_dur

        if total_overlay_dur > 0:
            mogrt_beats.append({
                "beat_index": beat.get("beat_index"),
                "duration": dur,
                "overlay_duration": total_overlay_dur,
                "ratio": dur / total_overlay_dur if total_overlay_dur > 0 else 0,
            })

    if len(mogrt_beats) < 3:
        return {"score": 1.0, "mogrt_beats": len(mogrt_beats),
                "detail": "Too few MOGRT beats to assess"}

    # Check duration variance — all identical = not adapting to text
    durations = [b["duration"] for b in mogrt_beats]
    avg_dur = sum(durations) / len(durations)
    variance = sum((d - avg_dur) ** 2 for d in durations) / len(durations)

    # Check correlation between overlay duration and clip duration
    # Simple: do longer overlays get longer clips?
    sorted_by_overlay = sorted(mogrt_beats, key=lambda b: b["overlay_duration"])
    concordant = 0
    discordant = 0
    for i in range(len(sorted_by_overlay)):
        for j in range(i + 1, len(sorted_by_overlay)):
            if sorted_by_overlay[j]["duration"] > sorted_by_overlay[i]["duration"]:
                concordant += 1
            elif sorted_by_overlay[j]["duration"] < sorted_by_overlay[i]["duration"]:
                discordant += 1

    total_pairs = concordant + discordant
    if total_pairs > 0:
        # Kendall's tau-like measure
        correlation = (concordant - discordant) / total_pairs
    else:
        correlation = 0.0

    # Score: reward variance (adapting) and positive correlation
    variance_score = min(variance / 0.1, 1.0)  # 0.1s² variance = full marks
    correlation_score = max(0, (correlation + 1) / 2)  # -1..1 → 0..1
    score = 0.4 * variance_score + 0.6 * correlation_score

    return {
        "score": round(score, 4),
        "mogrt_beats": len(mogrt_beats),
        "duration_variance": round(variance, 4),
        "text_duration_correlation": round(correlation, 4),
        "avg_duration": round(avg_dur, 2),
        "details": mogrt_beats,
    }


def score_flourish_detection(beats: List[dict]) -> dict:
    """Rule 4: Organic flourishes — speed ramps on transformation moments.

    Checks whether speed ramps are used on beats that describe
    unattended transformations (melting, sizzling, browning, pouring settling).

    Returns:
        score: 0.0-1.0 (proportion of speed ramps that are organic flourishes)
        details: per-ramp assessment
    """
    speed_ramp_beats = []
    for beat in beats:
        effects = str(beat.get("effects", beat.get("effects_info", "")))
        if "speed" not in effects.lower() and "ramp" not in effects.lower():
            continue

        desc = str(beat.get("beat_description", "")).lower()
        reasoning = str(beat.get("effects_reasoning", "")).lower()

        # Prefer the structured verdict token if present: [flourish: organic|functional].
        # Keyword matching is a fallback for legacy annotations that pre-date the token.
        tag_match = re.search(r"\[flourish:\s*(organic|functional)\s*\]", reasoning)
        if tag_match:
            verdict = tag_match.group(1)
            is_flourish = verdict == "organic"
            is_functional = verdict == "functional"
        else:
            flourish_signals = [
                "melt", "sizzl", "brown", "caramel", "bubble", "steam",
                "pour", "drip", "pool", "spread", "settle", "dissolve",
                "slide", "cascade", "flow", "stream", "hold", "jar",
                "scrape", "scrap", "beauty", "hero", "plat", "present",
                "slow", "luxur", "savor", "reveal",
            ]
            functional_signals = [
                "compress", "fit", "musical", "phrase", "beat", "rhythm",
                "tempo", "accelerat",
            ]

            is_flourish = any(s in desc or s in reasoning for s in flourish_signals)
            is_functional = any(s in desc or s in reasoning for s in functional_signals)

        speed_ramp_beats.append({
            "beat_index": beat.get("beat_index"),
            "description": beat.get("beat_description", "")[:60],
            "effects": effects[:60],
            "is_flourish": is_flourish,
            "is_functional": is_functional,
            "classification": "flourish" if is_flourish else ("functional" if is_functional else "unknown"),
        })

    # Binary reward with neutral floor:
    # - At least one organic flourish → 1.0 (Dan's rule 4 aspiration met)
    # - Zero organic flourishes (no ramps, OR all ramps functional) → 0.7 neutral
    # Rationale: flourishes are great to have but sometimes legitimately missed
    # (footage didn't contain a slow-reveal moment, or editor used ramps only
    # for timing). The 0.3 gradient rewards evolved edits that find flourish
    # opportunities without punishing edits that don't.
    flourishes = sum(1 for b in speed_ramp_beats if b["is_flourish"])

    if not speed_ramp_beats:
        return {
            "score": 0.7,
            "speed_ramp_count": 0,
            "flourish_count": 0,
            "detail": "No speed ramps — neutral (no flourish present, but none attempted)",
        }

    score = 1.0 if flourishes >= 1 else 0.7

    return {
        "score": round(score, 4),
        "speed_ramp_count": len(speed_ramp_beats),
        "flourish_count": flourishes,
        "functional_count": sum(1 for b in speed_ramp_beats if b["is_functional"]),
        "detail": (
            f"{flourishes} organic flourish(es) present — aspiration met"
            if flourishes >= 1
            else "All speed ramps are functional timing tools — neutral, no flourish found"
        ),
        "details": speed_ramp_beats,
    }


def score_camera_run_quality(beats: List[dict]) -> dict:
    """Overall camera switching quality — not just dump sequences.

    Checks:
    - Are there meaningful camera runs (not all single-beat)?
    - Is there variety (not all one camera)?
    - Does the edit end with a front-camera run (beauty close pattern)?
    """
    cameras = [get_camera(b) for b in beats]
    if not cameras:
        return {"score": 0.0, "detail": "No beats"}

    # Build runs
    runs = []
    run_start = 0
    for i in range(1, len(cameras)):
        if cameras[i] != cameras[i - 1]:
            runs.append({"camera": cameras[run_start], "length": i - run_start,
                         "start_beat": beats[run_start].get("beat_index", run_start)})
            run_start = i
    runs.append({"camera": cameras[run_start], "length": len(cameras) - run_start,
                 "start_beat": beats[run_start].get("beat_index", run_start)})

    run_lengths = [r["length"] for r in runs]
    single_beat_runs = sum(1 for l in run_lengths if l == 1)
    multi_beat_runs = sum(1 for l in run_lengths if l >= 2)

    # Score components
    # 1. Run variety: not all single-beat (too choppy) and not all one run (too static)
    if len(runs) <= 1:
        variety_score = 0.3  # only one camera = minimal variety
    else:
        variety_score = multi_beat_runs / len(runs)

    # 2. Camera balance: neither all-front nor all-overhead
    front_count = sum(1 for c in cameras if "front" in c)
    balance = 1.0 - abs(front_count / len(cameras) - 0.6)  # 60% front is ideal
    balance_score = max(0, balance)

    # 3. Ending pattern: front-camera run at end (beauty close)
    ends_front = "front" in cameras[-1]
    end_run_length = runs[-1]["length"] if runs else 0
    ending_score = 1.0 if ends_front and end_run_length >= 2 else 0.5

    score = 0.4 * variety_score + 0.3 * balance_score + 0.3 * ending_score

    return {
        "score": round(score, 4),
        "total_runs": len(runs),
        "single_beat_runs": single_beat_runs,
        "multi_beat_runs": multi_beat_runs,
        "avg_run_length": round(sum(run_lengths) / len(run_lengths), 1),
        "max_run_length": max(run_lengths),
        "front_pct": round(front_count / len(cameras) * 100, 1),
        "ends_front": ends_front,
        "end_run_length": end_run_length,
        "runs": runs,
    }


def score_duration_compensation(beats: List[dict]) -> dict:
    """Rule 3 addendum: beats after a camera switch should be slightly longer.

    When the editor switches camera during a dump sequence, the post-switch
    beat is held longer to give the viewer re-orientation time. This checks
    whether that pattern exists.
    """
    sequences = find_dump_sequences(beats)
    if not sequences:
        return {"score": 1.0, "detail": "No dump sequences"}

    post_switch_durations = []
    held_run_durations = []

    for seq in sequences:
        cameras = [get_camera(beats[i]) for i in seq]
        for j in range(len(cameras)):
            beat = beats[seq[j]]
            dur = beat.get("duration", 0)
            if isinstance(dur, dict):
                dur = dur.get("seconds", 0)
            dur = float(dur) if dur else 0

            if j > 0 and cameras[j] != cameras[j - 1]:
                post_switch_durations.append(dur)
            elif j > 0:
                held_run_durations.append(dur)

    if not post_switch_durations or not held_run_durations:
        return {"score": 1.0, "post_switch_count": len(post_switch_durations),
                "held_count": len(held_run_durations),
                "detail": "Not enough data to compare"}

    avg_post_switch = sum(post_switch_durations) / len(post_switch_durations)
    avg_held = sum(held_run_durations) / len(held_run_durations)

    # Score: post-switch should be >= held. Reward if it is.
    if avg_post_switch >= avg_held:
        score = 1.0
    else:
        # How much shorter? Penalize proportionally
        ratio = avg_post_switch / avg_held if avg_held > 0 else 1.0
        score = max(0.0, ratio)

    return {
        "score": round(score, 4),
        "avg_post_switch_dur": round(avg_post_switch, 3),
        "avg_held_run_dur": round(avg_held, 3),
        "post_switch_count": len(post_switch_durations),
        "held_count": len(held_run_durations),
        "compensating": avg_post_switch >= avg_held,
    }


def score_annotation(annotation: dict) -> dict:
    """Score a full annotation JSON against all editorial rules.

    Returns per-rule scores and a weighted composite.
    """
    beats = annotation.get("beats", [])
    recipe = annotation.get("recipe", "unknown")

    if not beats:
        return {"recipe": recipe, "error": "No beats", "composite": 0.0}

    dump_hold = score_dump_camera_hold(beats)
    mogrt_text = score_mogrt_text_readability(beats)
    flourish = score_flourish_detection(beats)
    camera_runs = score_camera_run_quality(beats)
    dur_comp = score_duration_compensation(beats)

    # Weighted composite
    # Dump hold is the most important (Dan's strongest rule)
    composite = (
        dump_hold["score"] * 0.30 +
        camera_runs["score"] * 0.20 +
        mogrt_text["score"] * 0.20 +
        flourish["score"] * 0.15 +
        dur_comp["score"] * 0.15
    )

    return {
        "recipe": recipe,
        "beat_count": len(beats),
        "composite": round(composite * 100, 2),
        "rules": {
            "dump_camera_hold": dump_hold,
            "camera_run_quality": camera_runs,
            "mogrt_text_readability": mogrt_text,
            "flourish_detection": flourish,
            "duration_compensation": dur_comp,
        },
    }


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} annotation.json")
        print(f"       {sys.argv[0]} --dir annotations/")
        sys.exit(1)

    if sys.argv[1] == "--dir":
        ann_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("annotations")
        results = {}
        for f in sorted(ann_dir.glob("*.json")):
            annotation = json.loads(f.read_text())
            result = score_annotation(annotation)
            results[f.stem] = result
            print(f"\n{'=' * 60}")
            print(f"  {f.stem}: {result['composite']}/100")
            print(f"{'=' * 60}")
            for rule_name, rule_result in result["rules"].items():
                score_val = rule_result["score"]
                bar = "█" * int(score_val * 20) + "░" * (20 - int(score_val * 20))
                print(f"  {rule_name:30s} {bar} {score_val:.2f}")
                for v in rule_result.get("violations", []):
                    print(f"    ⚠ {v}")
            print()

        # Aggregate
        if results:
            avg = sum(r["composite"] for r in results.values()) / len(results)
            print(f"Average composite: {avg:.1f}/100")

        if "--json" in sys.argv:
            print(json.dumps(results, indent=2))

    else:
        annotation = json.loads(Path(sys.argv[1]).read_text())
        result = score_annotation(annotation)

        print(f"\n{'=' * 60}")
        print(f"  {result['recipe']}: {result['composite']}/100")
        print(f"{'=' * 60}")
        for rule_name, rule_result in result["rules"].items():
            score_val = rule_result["score"]
            bar = "█" * int(score_val * 20) + "░" * (20 - int(score_val * 20))
            print(f"  {rule_name:30s} {bar} {score_val:.2f}")
            for v in rule_result.get("violations", []):
                print(f"    ⚠ {v}")
        print()

        if "--json" in sys.argv:
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
