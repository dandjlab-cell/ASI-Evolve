#!/usr/bin/env python3
"""
derive_camera_mapping.py — derive a recipe's prefix → camera mapping from
Pass 1 visual classification + approved_edits timeline.

Pass 1 markdown (e.g. `pass1_basil_pesto.md`) is itself a visual classification
of FINAL.mp4 frames by /watch-video. Each frame has a FRONT/OVERHEAD label
matching Dan's vocabulary. Approved edits JSON has each timeline cut's source
filename + FINAL timeline_in_sec.

We walk approved_edits' timeline, look up the Pass 1 frame nearest each cut's
FINAL position, and tally votes per filename prefix. Majority wins → that
prefix's camera label for this recipe.

This is the per-recipe visual derivation the camera-detection bug requires
(per `~/.claude/projects/.../memory/feedback_camera_detection_per_recipe.md`).

Output is printed for the human to review before being merged into
`camera_mapping.json`. Use `--write` to merge in place.

Usage:
    python3 experiments/recipe_pipeline/derive_camera_mapping.py basil_pesto
    python3 experiments/recipe_pipeline/derive_camera_mapping.py basil_pesto --write
    python3 experiments/recipe_pipeline/derive_camera_mapping.py --all
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
APPROVED_DIR = REPO_ROOT / "approved_edits"
PASS1_DIR = Path.home() / "DevApps/storyboard-gen/docs/watch-video"
CACHE_PATH = REPO_ROOT / "camera_mapping.json"

logger = logging.getLogger("derive_camera_mapping")


def load_pass1(recipe_slug: str) -> list[dict]:
    """Pass 1 markdown table → list of {time_sec, camera, subject, notes}."""
    path = PASS1_DIR / f"pass1_{recipe_slug}.md"
    if not path.is_file():
        raise FileNotFoundError(f"pass1 markdown not found: {path}")
    frames: list[dict] = []
    with path.open() as f:
        for line in f:
            s = line.strip()
            if not s.startswith("|") or s.startswith("| Frame") or s.startswith("|---"):
                continue
            parts = [p.strip() for p in s.split("|")]
            parts = [p for p in parts if p]
            if len(parts) < 4:
                continue
            try:
                _ = int(parts[0])
            except ValueError:
                continue
            tstr = parts[1]
            if ":" in tstr:
                mm, ss = tstr.split(":", 1)
                t = float(mm) * 60 + float(ss)
            else:
                t = float(tstr)
            frames.append({
                "time_sec": t,
                "camera": parts[2].strip().lower(),
                "subject": parts[3] if len(parts) > 3 else "",
                "notes": parts[4] if len(parts) > 4 else "",
            })
    frames.sort(key=lambda f: f["time_sec"])
    return frames


def load_approved(recipe_slug: str) -> dict:
    path = APPROVED_DIR / f"{recipe_slug}.json"
    if not path.is_file():
        raise FileNotFoundError(f"approved_edits not found: {path}")
    return json.loads(path.read_text())


def derive(recipe_slug: str, prefix_len: int = 5) -> dict:
    """Returns {prefix: {camera: count, ...}, ...} from voting Pass 1 cameras
    against approved_edits timeline cuts."""
    pass1 = load_pass1(recipe_slug)
    approved = load_approved(recipe_slug)

    pass1_times = [f["time_sec"] for f in pass1]
    pass1_cameras = [f["camera"] for f in pass1]
    n = len(pass1_times)

    def closest_camera(t: float) -> str:
        # Binary-search-ish nearest-neighbor; pass1 is sorted.
        if not pass1_times:
            return "unknown"
        # linear is fine — pass1 ~250 entries
        best_i = 0
        best_d = abs(pass1_times[0] - t)
        for i in range(1, n):
            d = abs(pass1_times[i] - t)
            if d < best_d:
                best_d = d
                best_i = i
        return pass1_cameras[best_i]

    votes: dict[str, Counter] = defaultdict(Counter)
    for entry in approved.get("timeline", []):
        v1 = entry.get("v1") or {}
        fn = v1.get("file") or ""
        if not fn:
            continue
        prefix = fn[:prefix_len]
        # Use timeline_in_sec — could be on the entry or under v1
        t = entry.get("timeline_in_sec")
        if t is None and isinstance(v1, dict):
            t = v1.get("timeline_in_sec")
        if t is None:
            continue
        cam = closest_camera(float(t))
        if cam in ("front", "overhead"):
            votes[prefix][cam] += 1
        else:
            votes[prefix]["other"] += 1
    return dict(votes)


def fmt_votes(votes: dict[str, Counter]) -> str:
    lines = []
    for prefix, c in sorted(votes.items()):
        total = sum(c.values())
        winner, _ = c.most_common(1)[0]
        breakdown = ", ".join(f"{k}={v}" for k, v in c.most_common())
        confidence = c[winner] / total if total else 0
        lines.append(f"  {prefix}: → {winner}  ({breakdown}, conf={confidence:.0%}, n={total})")
    return "\n".join(lines)


def merge_into_cache(recipe_slug: str, mapping: dict[str, str], cache_path: Path) -> None:
    """Append/update mapping in cache_path with provenance."""
    cache = json.loads(cache_path.read_text())
    cache.setdefault("mappings", {})
    today = date.today().isoformat()
    entry = {**mapping,
             "_verified_at": today,
             "_verified_via": "derive_camera_mapping.py — Pass 1 vote against approved_edits timeline"}
    cache["mappings"][recipe_slug] = entry
    cache_path.write_text(json.dumps(cache, indent=2))
    logger.info("wrote %s mapping to %s", recipe_slug, cache_path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("recipe", nargs="?", help="Recipe slug (e.g. basil_pesto)")
    p.add_argument("--all", action="store_true",
                   help="Derive for every recipe with both pass1 + approved_edits.")
    p.add_argument("--write", action="store_true",
                   help="Merge derived mapping into camera_mapping.json (uses majority winner).")
    p.add_argument("--cache", type=Path, default=CACHE_PATH)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if args.all:
        # Find recipes with both Pass1 + approved_edits
        recipes = []
        for path in sorted(APPROVED_DIR.glob("*.json")):
            slug = path.stem
            if (PASS1_DIR / f"pass1_{slug}.md").is_file():
                recipes.append(slug)
        if not recipes:
            logger.error("no recipes with both Pass 1 + approved_edits")
            return 2
        logger.info("derivable recipes: %s", recipes)
    elif args.recipe:
        recipes = [args.recipe]
    else:
        p.print_help()
        return 2

    for slug in recipes:
        try:
            votes = derive(slug)
        except FileNotFoundError as e:
            logger.error("%s: %s", slug, e)
            continue
        if not votes:
            logger.warning("%s: no votes computed (empty timeline?)", slug)
            continue
        print(f"\n{slug}:")
        print(fmt_votes(votes))

        if args.write:
            mapping = {prefix: c.most_common(1)[0][0] for prefix, c in votes.items()
                       if c.most_common(1)[0][0] in ("front", "overhead")}
            if mapping:
                merge_into_cache(slug, mapping, args.cache)
                print(f"  (merged into {args.cache.name})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
