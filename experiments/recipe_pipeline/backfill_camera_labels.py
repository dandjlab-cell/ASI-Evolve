#!/usr/bin/env python3
"""
backfill_camera_labels.py — populate `camera.choice` on annotation JSONs
using the per-recipe prefix→camera cache at `camera_mapping.json`.

The cache is the source of truth. Camera convention does NOT generalize
across shoots, so the legacy global filename-prefix rule
(`analyze_editorial_judgment.detect_camera`) is NOT used here. Each
recipe's prefix→camera mapping must be verified visually and recorded
in the cache before backfill runs (see `derive_camera_mapping.py` for
the Pass 1 + approved_edits derivation path, or hand-edit the cache for
recipes that lack those inputs). See:

  ~/.claude/projects/.../memory/feedback_camera_detection_per_recipe.md

Behavior per beat:
  - filename starts with "[NEST" or is None  → leave as "unknown"
  - prefix found in cache for this recipe    → set camera.choice
  - prefix NOT in cache                       → log + leave unchanged
  - existing non-null camera.choice           → preserved (never overwritten)

Usage:
    python3 experiments/recipe_pipeline/backfill_camera_labels.py
    python3 experiments/recipe_pipeline/backfill_camera_labels.py --dry-run
    python3 experiments/recipe_pipeline/backfill_camera_labels.py --recipe basil_pesto
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ANNOTATIONS_DIR = REPO_ROOT / "annotations"
CACHE_PATH = REPO_ROOT / "camera_mapping.json"

REASONING = (
    "backfilled {date} via per-recipe prefix→camera cache "
    "(camera_mapping.json[{recipe}][{prefix}])"
)

logger = logging.getLogger("backfill_camera_labels")


def load_cache(path: Path) -> dict[str, dict[str, str]]:
    """Load the cache and return only the {recipe: {prefix: camera, ...}} core,
    stripped of provenance keys (those starting with `_`).
    """
    raw = json.loads(path.read_text())
    out: dict[str, dict[str, str]] = {}
    for recipe, entry in raw.get("mappings", {}).items():
        clean = {k: v for k, v in entry.items() if not k.startswith("_")}
        out[recipe] = clean
    return out


def backfill_one(annotation: dict, recipe_slug: str,
                 prefix_camera: dict[str, str], force: bool = False) -> dict:
    counts: Counter = Counter()
    backfilled: list[int] = []
    skipped_nested: list[int] = []
    skipped_no_filename: list[int] = []
    skipped_unmapped_prefix: list[tuple[int, str]] = []
    preserved_existing: list[int] = []
    overwrote_disagreement: list[tuple[int, str, str]] = []  # (idx, old, new)
    today = date.today().isoformat()

    for b in annotation.get("beats", []):
        idx = b.get("beat_index")
        filename = b.get("filename") or ""
        cam = b.get("camera")
        if not isinstance(cam, dict):
            cam = {"choice": None, "reasoning": ""}
            b["camera"] = cam

        existing = cam.get("choice")
        if not force and existing not in (None, "", "unknown"):
            preserved_existing.append(idx)
            counts["preserved_existing"] += 1
            continue

        if not filename:
            cam["choice"] = "unknown"
            cam["reasoning"] = f"backfilled {today}: no source filename (title_card / nested / wrapper)"
            skipped_no_filename.append(idx)
            counts["out:unknown_no_filename"] += 1
            continue

        if filename.startswith("[NEST"):
            cam["choice"] = "unknown"
            cam["reasoning"] = f"backfilled {today}: nested-sequence wrapper, no single source camera"
            skipped_nested.append(idx)
            counts["out:unknown_nested"] += 1
            continue

        prefix = filename[:5]
        camera = prefix_camera.get(prefix)
        if camera is None:
            skipped_unmapped_prefix.append((idx, prefix))
            counts[f"unmapped:{prefix}"] += 1
            continue

        if existing and existing != camera and existing != "unknown":
            overwrote_disagreement.append((idx, existing, camera))
            counts[f"overwrote:{existing}->{camera}"] += 1
        cam["choice"] = camera
        cam["reasoning"] = REASONING.format(date=today, recipe=recipe_slug, prefix=prefix)
        backfilled.append(idx)
        counts[f"out:{camera}"] += 1

    return {
        "recipe": recipe_slug,
        "counts": dict(counts),
        "backfilled_n": len(backfilled),
        "preserved_existing_n": len(preserved_existing),
        "skipped_nested_n": len(skipped_nested),
        "skipped_no_filename_n": len(skipped_no_filename),
        "unmapped_prefixes": skipped_unmapped_prefix,
        "overwrote_disagreement": overwrote_disagreement,
    }


def run(targets: list[str], annotations_dir: Path, cache: dict,
        dry_run: bool, force: bool) -> int:
    summary = []
    missing_in_cache = []
    for slug in targets:
        if slug not in cache:
            missing_in_cache.append(slug)
            continue
        path = annotations_dir / f"{slug}.json"
        if not path.is_file():
            logger.error("missing annotation: %s", path)
            continue
        ann = json.loads(path.read_text())
        n_beats = len(ann.get("beats", []))
        stats = backfill_one(ann, slug, cache[slug], force=force)
        if not dry_run:
            path.write_text(json.dumps(ann, indent=2))
            logger.info("wrote %s (%d beats, %d backfilled)",
                        path.name, n_beats, stats["backfilled_n"])
        else:
            logger.info("DRY-RUN %s (%d beats, would backfill %d)",
                        path.name, n_beats, stats["backfilled_n"])
        summary.append(stats)

    print()
    print("Backfill summary")
    print("================")
    for s in summary:
        c = s["counts"]
        front = c.get("out:front", 0)
        overhead = c.get("out:overhead", 0)
        unknown = sum(v for k, v in c.items() if k.startswith("out:unknown"))
        unmapped = sum(v for k, v in c.items() if k.startswith("unmapped:"))
        n_overwrote = len(s.get("overwrote_disagreement", []))
        print(f"  {s['recipe']:25s} "
              f"front={front:>3} overhead={overhead:>3} unknown={unknown:>2} "
              f"unmapped_prefix={unmapped:>2} preserved={s['preserved_existing_n']:>2} "
              f"overwrote={n_overwrote:>2}")
        if s["unmapped_prefixes"]:
            print(f"      unmapped: {s['unmapped_prefixes']}")
        if n_overwrote:
            shifts: Counter = Counter()
            for _, old, new in s["overwrote_disagreement"]:
                shifts[f"{old}→{new}"] += 1
            print(f"      reconciled: {dict(shifts)}")

    if missing_in_cache:
        print()
        print("Recipes NOT in camera_mapping.json (skipped):")
        for r in missing_in_cache:
            print(f"  {r}")
        print(f"\nTo add a recipe to the cache, see derive_camera_mapping.py "
              f"(Pass 1 + approved_edits) or hand-edit camera_mapping.json.")

    return 0 if not missing_in_cache else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--annotations-dir", type=Path, default=ANNOTATIONS_DIR)
    p.add_argument("--cache", type=Path, default=CACHE_PATH)
    p.add_argument("--recipe", action="append", default=None,
                   help="Restrict to one or more recipes (repeatable). "
                        "Default: every recipe in the cache.")
    p.add_argument("--dry-run", action="store_true",
                   help="Compute and report but do not write files.")
    p.add_argument("--force", action="store_true",
                   help="Reconcile mode: overwrite existing non-null camera labels "
                        "when they disagree with the cache. Use after derive-all "
                        "to bring stale legacy-rule labels in line with the cache.")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if not args.cache.is_file():
        logger.error("cache not found: %s", args.cache)
        return 2
    cache = load_cache(args.cache)
    targets = args.recipe or sorted(cache.keys())
    return run(targets, args.annotations_dir, cache, args.dry_run, args.force)


if __name__ == "__main__":
    sys.exit(main())
