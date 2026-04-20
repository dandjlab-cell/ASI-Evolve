#!/usr/bin/env python3
"""
Score a pipeline manifest against an approved edit (ground truth).

Computes 4 metrics:
  - Precision (35%): what % of proposed clips Dan kept
  - Recall (30%): what % of Dan's clips the pipeline found
  - Timing (20%): in-point accuracy for matched clips
  - Camera (15%): V1/V2 pairing match rate

Usage:
    python score.py pipeline_manifest.json approved_manifest.json
    python score.py --dir cached_recipes/ approved_edits/  # score all recipes
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Scoring weights
W_PRECISION = 0.35
W_RECALL = 0.30
W_TIMING = 0.20
W_CAMERA = 0.15

# Timing tolerance: clips within this many seconds count as "matched"
TIMING_MATCH_TOLERANCE = 3.0
# Max timing error for scoring (errors above this get 0 timing score)
TIMING_MAX_ERROR = 5.0


def score_manifest_pair(
    pipeline_manifest: Dict,
    approved_manifest: Dict,
) -> Dict:
    """Score a pipeline manifest against an approved edit.

    Both manifests must have a "timeline" key with entries containing:
        {"v1": {"file": "X.mov", "in": 12.0}, "v2": {"file": "Y.mov", "in": 39.0}}

    Returns dict with per-metric scores and composite score (0-100).
    """
    pipeline_clips = _extract_clips(pipeline_manifest)
    approved_clips = _extract_clips(approved_manifest)

    if not approved_clips:
        return _empty_score("No clips in approved edit")

    # Match pipeline clips to approved clips by filename
    matches = _match_clips(pipeline_clips, approved_clips)

    # Precision: what fraction of pipeline's proposed clips appear in approved edit
    if pipeline_clips:
        precision = len(matches) / len(pipeline_clips)
    else:
        precision = 0.0

    # Recall: what fraction of approved clips were proposed by pipeline
    recall = len(matches) / len(approved_clips)

    # Timing: average in-point accuracy for matched clips
    timing_errors = []
    for p_clip, a_clip in matches:
        error = abs(p_clip["in"] - a_clip["in"])
        timing_errors.append(error)

    if timing_errors:
        avg_error = sum(timing_errors) / len(timing_errors)
        timing = 1.0 - min(avg_error / TIMING_MAX_ERROR, 1.0)
    else:
        timing = 0.0

    # Camera: V1/V2 pairing match rate
    camera = _score_camera_pairing(pipeline_manifest, approved_manifest)

    # Composite
    composite = (
        precision * W_PRECISION +
        recall * W_RECALL +
        timing * W_TIMING +
        camera * W_CAMERA
    ) * 100

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "timing": round(timing, 4),
        "camera": round(camera, 4),
        "composite": round(composite, 2),
        "matched_clips": len(matches),
        "pipeline_clips": len(pipeline_clips),
        "approved_clips": len(approved_clips),
        "avg_timing_error_sec": round(avg_error, 3) if timing_errors else None,
    }


def _extract_clips(manifest: Dict) -> List[Dict]:
    """Extract flat list of clips from a manifest timeline."""
    clips = []
    for entry in manifest.get("timeline", []):
        for track in ("v1", "v2"):
            clip = entry.get(track)
            if clip and isinstance(clip, dict) and clip.get("file"):
                clips.append({
                    "file": clip["file"],
                    "in": clip.get("in", 0.0),
                    "out": clip.get("out", 0.0),
                    "track": track,
                    "beat_index": entry.get("beat_index"),
                })
    return clips


def _match_clips(
    pipeline_clips: List[Dict],
    approved_clips: List[Dict],
) -> List[Tuple[Dict, Dict]]:
    """Match pipeline clips to approved clips by filename + proximity.

    A pipeline clip matches an approved clip if:
    1. Same filename
    2. In-points within TIMING_MATCH_TOLERANCE seconds
    """
    matches = []
    used_approved = set()

    for p_clip in pipeline_clips:
        best_match = None
        best_error = float("inf")

        for i, a_clip in enumerate(approved_clips):
            if i in used_approved:
                continue
            if p_clip["file"] != a_clip["file"]:
                continue

            error = abs(p_clip["in"] - a_clip["in"])
            if error <= TIMING_MATCH_TOLERANCE and error < best_error:
                best_error = error
                best_match = (i, a_clip)

        if best_match is not None:
            used_approved.add(best_match[0])
            matches.append((p_clip, best_match[1]))

    return matches


def _score_camera_pairing(
    pipeline_manifest: Dict,
    approved_manifest: Dict,
) -> float:
    """Score camera selection accuracy.

    Premiere XMLs export all clips on a single track, so we can't compare
    track assignment. Instead, we infer camera identity from filename prefix
    (e.g. B19I = front/V1, AI2I = overhead/V2) and check whether the
    pipeline chose the same camera the editor chose for each matched moment.

    We detect the V1 prefix from the pipeline manifest (which has explicit
    v1/v2 tracks), then classify approved clips by the same prefix.
    """
    # Learn V1 prefix from pipeline manifest (it has explicit track info)
    v1_prefix = _detect_v1_prefix(pipeline_manifest)
    if not v1_prefix:
        return 0.0

    # Build approved clip list with camera labels
    approved_clips = []
    for entry in approved_manifest.get("timeline", []):
        for track in ("v1", "v2"):
            clip = entry.get(track)
            if clip and isinstance(clip, dict) and clip.get("file"):
                is_v1 = clip["file"].startswith(v1_prefix)
                approved_clips.append({
                    "file": clip["file"],
                    "in": clip.get("in", 0.0),
                    "camera": "v1" if is_v1 else "v2",
                })

    if not approved_clips:
        return 0.0

    # Build pipeline clip list with camera labels from track assignment
    pipeline_clips = []
    for entry in pipeline_manifest.get("timeline", []):
        for track in ("v1", "v2"):
            clip = entry.get(track)
            if clip and isinstance(clip, dict) and clip.get("file"):
                pipeline_clips.append({
                    "file": clip["file"],
                    "in": clip.get("in", 0.0),
                    "camera": track,
                })

    # For each matched clip pair, check if camera matches
    matches = 0
    total = 0
    used = set()

    for a_clip in approved_clips:
        for i, p_clip in enumerate(pipeline_clips):
            if i in used:
                continue
            if a_clip["file"] != p_clip["file"]:
                continue
            if abs(a_clip["in"] - p_clip["in"]) > TIMING_MATCH_TOLERANCE:
                continue
            # Found a match — does the camera assignment agree?
            used.add(i)
            total += 1
            if a_clip["camera"] == p_clip["camera"]:
                matches += 1
            break

    return matches / total if total > 0 else 0.0


def _detect_v1_prefix(manifest: Dict) -> Optional[str]:
    """Detect V1 camera prefix from a pipeline manifest with explicit tracks."""
    for entry in manifest.get("timeline", []):
        v1 = entry.get("v1")
        if v1 and isinstance(v1, dict) and v1.get("file"):
            # Return first 4 chars as prefix (e.g. "B19I")
            return v1["file"][:4]
    return None


def _empty_score(reason: str) -> Dict:
    return {
        "precision": 0.0,
        "recall": 0.0,
        "timing": 0.0,
        "camera": 0.0,
        "composite": 0.0,
        "matched_clips": 0,
        "pipeline_clips": 0,
        "approved_clips": 0,
        "avg_timing_error_sec": None,
        "error": reason,
    }


def score_all_recipes(
    pipeline_dir: str,
    approved_dir: str,
    holdout: Optional[List[str]] = None,
) -> Dict:
    """Score all recipes, return aggregate + per-recipe scores.

    Args:
        pipeline_dir: Directory with {recipe}_manifest.json files
        approved_dir: Directory with {recipe}.json approved manifests
        holdout: Recipe names to exclude from training score
    """
    holdout = set(holdout or [])
    pipeline_path = Path(pipeline_dir)
    approved_path = Path(approved_dir)

    train_scores = []
    holdout_scores = []
    per_recipe = {}

    for approved_file in sorted(approved_path.glob("*.json")):
        recipe_name = approved_file.stem
        approved = json.loads(approved_file.read_text())

        # Find matching pipeline manifest (flat or inside subdirectory)
        pipeline_file = pipeline_path / f"{recipe_name}_manifest.json"
        if not pipeline_file.exists():
            pipeline_file = pipeline_path / f"{recipe_name}.json"
        if not pipeline_file.exists():
            pipeline_file = pipeline_path / recipe_name / f"{recipe_name}_manifest.json"
        if not pipeline_file.exists():
            # Search subdirectory for any manifest
            subdir = pipeline_path / recipe_name
            if subdir.is_dir():
                manifests = sorted(subdir.glob("*_manifest.json")) + sorted(subdir.glob("*manifest*.json"))
                if manifests:
                    pipeline_file = manifests[-1]  # most recent
        if not pipeline_file.exists():
            per_recipe[recipe_name] = _empty_score(f"No pipeline manifest for {recipe_name}")
            continue

        pipeline = json.loads(pipeline_file.read_text())
        score = score_manifest_pair(pipeline, approved)
        per_recipe[recipe_name] = score

        if recipe_name in holdout:
            holdout_scores.append(score["composite"])
        else:
            train_scores.append(score["composite"])

    result = {
        "train_score": round(sum(train_scores) / len(train_scores), 2) if train_scores else 0.0,
        "train_count": len(train_scores),
        "per_recipe": per_recipe,
    }

    if holdout_scores:
        result["holdout_score"] = round(sum(holdout_scores) / len(holdout_scores), 2)
        result["holdout_count"] = len(holdout_scores)

    return result


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} pipeline_manifest.json approved_manifest.json")
        print(f"       {sys.argv[0]} --dir pipeline_dir/ approved_dir/ [--holdout recipe1,recipe2]")
        sys.exit(1)

    if sys.argv[1] == "--dir":
        holdout = None
        if "--holdout" in sys.argv:
            idx = sys.argv.index("--holdout")
            holdout = sys.argv[idx + 1].split(",")
        result = score_all_recipes(sys.argv[2], sys.argv[3], holdout)
    else:
        pipeline = json.loads(Path(sys.argv[1]).read_text())
        approved = json.loads(Path(sys.argv[2]).read_text())
        result = score_manifest_pair(pipeline, approved)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
