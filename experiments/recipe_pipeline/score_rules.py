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

        # Count transitions and detect rapid alternation
        # Rapid alternation = switching back and forth (F→O→F or O→F→O)
        # A single switch in a short sequence is fine — alternation is the problem
        run_length = 1
        switch_count_in_seq = 0
        for j in range(1, len(cameras)):
            if cameras[j] != cameras[j - 1]:
                total_transitions += 1
                switch_count_in_seq += 1
                # Check for alternation: did we switch back to the camera
                # we were just on? (i.e., A→B→A pattern)
                is_alternation = (
                    j >= 2 and cameras[j] == cameras[j - 2]
                    and cameras[j] != cameras[j - 1]
                )
                # Or: too many switches relative to sequence length
                too_frequent = switch_count_in_seq >= 2 and run_length <= 1

                if is_alternation or too_frequent:
                    rapid_alternations += 1
                    beat_idx = beats[seq[j]].get("beat_index", seq[j])
                    prev_idx = beats[seq[j - 1]].get("beat_index", seq[j - 1])
                    violations.append(
                        f"Dump seq {seq_idx + 1}: rapid alternation {cameras[j-1]}→{cameras[j]} "
                        f"at beat {prev_idx}→{beat_idx} (held only {run_length} beat{'s' if run_length > 1 else ''})"
                    )
                    seq_detail["rapid_switches"].append(beat_idx)
                run_length = 1
            else:
                run_length += 1

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
        effects = str(beat.get("effects_info", ""))
        if "speed" not in effects.lower() and "ramp" not in effects.lower():
            continue

        desc = str(beat.get("beat_description", "")).lower()
        reasoning = ""
        r = beat.get("reasoning", {})
        if isinstance(r, dict):
            reasoning = str(r.get("effects_reasoning", "")).lower()

        # Check if this looks like an organic flourish
        flourish_signals = [
            "melt", "sizzl", "brown", "caramel", "bubble", "steam",
            "pour", "drip", "pool", "spread", "settle", "dissolve",
            "slide", "cascade", "flow", "stream",
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

    if not speed_ramp_beats:
        return {"score": 1.0, "speed_ramp_count": 0,
                "detail": "No speed ramps to assess"}

    flourishes = sum(1 for b in speed_ramp_beats if b["is_flourish"])
    score = flourishes / len(speed_ramp_beats)

    return {
        "score": round(score, 4),
        "speed_ramp_count": len(speed_ramp_beats),
        "flourish_count": flourishes,
        "functional_count": sum(1 for b in speed_ramp_beats if b["is_functional"]),
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

    # Weighted composite
    # Dump hold is the most important (Dan's strongest rule)
    composite = (
        dump_hold["score"] * 0.35 +
        camera_runs["score"] * 0.25 +
        mogrt_text["score"] * 0.20 +
        flourish["score"] * 0.20
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
