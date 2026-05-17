"""Beat Review UI preflight.

4 sequential gates, idempotent and resume-safe:
  1. mount check     — verify /Volumes/2TB Footage is mounted
  2. map             — build experiments/review_ui/recipe_export_map.json
  3. extract         — re-encode beat slices into .cache/beat_clips/{recipe}/
  4. index           — write .cache/beat_index.json (flat array for the UI)

Step 4 runs without the volume mounted. Steps 1-3 hard-fail if the volume is missing.

Usage:
    python preflight.py                  # run all 4 steps
    python preflight.py --index-only     # just rebuild beat_index.json
    python preflight.py --map-only       # mount + map
    python preflight.py --recipe SLUG --extract   # mount + map + extract one recipe
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
ANNOTATIONS_DIR = REPO / "experiments" / "recipe_pipeline" / "annotations"
FRAMES_DIR = REPO / "experiments" / "recipe_pipeline" / "frames"
RAFT_CURVES_DIR = (
    REPO / "experiments" / "offline_validation" / ".cache" / "exp05_curves"
)
CACHE_DIR = REPO / "experiments" / "offline_validation" / ".cache"
BEAT_CLIPS_DIR = CACHE_DIR / "beat_clips"
BEAT_INDEX_PATH = CACHE_DIR / "beat_index.json"

REVIEW_UI_DIR = REPO / "experiments" / "review_ui"
RECIPE_EXPORT_MAP_PATH = REVIEW_UI_DIR / "recipe_export_map.json"
EXTRACT_MANIFEST_PATH = REVIEW_UI_DIR / ".extract_manifest.json"

VOLUME_ROOT = Path("/Volumes/2TB Footage")
EXPORTS_ROOT = VOLUME_ROOT / "01_Projects" / "Kitchn" / "2026_March" / "04 Exports"


# ─── Step 4: build beat_index.json (works without /Volumes) ─────────────────


def _list_clip_ids(recipe: str) -> set[str]:
    """RAFT curves cached as .cache/exp05_curves/{recipe}/{clip_id}.json."""
    d = RAFT_CURVES_DIR / recipe
    if not d.is_dir():
        return set()
    return {p.stem for p in d.glob("*.json")}


def _recipe_has_frames(recipe: str) -> bool:
    d = FRAMES_DIR / recipe
    return d.is_dir() and any(d.glob("frame_*.jpg"))


def _clip_id_from_filename(filename: str | None) -> str | None:
    """basil_pesto beat 0 has filename 'B19I6413.mov' — clip id is the stem."""
    if not filename:
        return None
    return Path(filename).stem


def _clip_exists(recipe: str, beat_index: int) -> bool:
    return (BEAT_CLIPS_DIR / recipe / f"{beat_index:04d}.mp4").is_file()


def build_beat_index() -> dict[str, Any]:
    """Flatten all 18 annotation files into one denormalized array."""
    files = sorted(ANNOTATIONS_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No annotation files in {ANNOTATIONS_DIR}")

    beats: list[dict[str, Any]] = []
    recipes_summary: list[dict[str, Any]] = []

    for path in files:
        with path.open() as f:
            doc = json.load(f)
        slug = doc["recipe"]
        raft_clip_ids = _list_clip_ids(slug)
        has_frames = _recipe_has_frames(slug)

        n_total = 0
        n_typed = 0
        n_mogrt = 0
        for b in doc["beats"]:
            n_total += 1
            beat_type = b.get("beat_type", "") or ""
            if beat_type:
                n_typed += 1
            mogrt = b.get("mogrt_overlaps") or []
            if mogrt:
                n_mogrt += 1
            clip_id = _clip_id_from_filename(b.get("filename"))
            beats.append(
                {
                    "recipe": slug,
                    "beat_index": b["beat_index"],
                    "in": (b.get("in_point") or {}).get("seconds"),
                    "out": (b.get("out_point") or {}).get("seconds"),
                    "duration": (b.get("duration") or {}).get("seconds"),
                    "filename": b.get("filename"),
                    "clip_id": clip_id,
                    "camera": (b.get("camera") or {}).get("choice"),
                    "recipe_section": b.get("recipe_section", ""),
                    "beat_type_source": beat_type,
                    "mogrt_overlaps": mogrt,
                    "beat_description": b.get("beat_description"),
                    "correction": b.get("correction"),
                    "effects": b.get("effects"),
                    "verdict": b.get("verdict"),
                    "pipeline_info": b.get("pipeline_info"),
                    "confidence": b.get("confidence"),
                    "has_clip": _clip_exists(slug, b["beat_index"]),
                    "has_frames": has_frames,
                    "has_motion_curve": bool(clip_id and clip_id in raft_clip_ids),
                }
            )

        recipes_summary.append(
            {
                "slug": slug,
                "n_beats": n_total,
                "n_typed_source": n_typed,
                "n_untyped_source": n_total - n_typed,
                "n_with_mogrt": n_mogrt,
                "has_frames": has_frames,
                "has_motion_curves": bool(raft_clip_ids),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_recipes": len(recipes_summary),
        "n_beats_total": len(beats),
        "n_beats_typed_source": sum(r["n_typed_source"] for r in recipes_summary),
        "n_beats_untyped_source": sum(r["n_untyped_source"] for r in recipes_summary),
        "recipes": recipes_summary,
        "beats": beats,
    }


def write_beat_index() -> Path:
    payload = build_beat_index()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BEAT_INDEX_PATH.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(payload, f, indent=2)
    tmp.replace(BEAT_INDEX_PATH)
    print(
        f"[index] wrote {BEAT_INDEX_PATH} — "
        f"{payload['n_recipes']} recipes, "
        f"{payload['n_beats_total']} beats "
        f"({payload['n_beats_typed_source']} typed, "
        f"{payload['n_beats_untyped_source']} untyped)"
    )
    return BEAT_INDEX_PATH


# ─── Steps 1-3 stubs (volume-dependent; filled in next task) ────────────────


def check_mount() -> bool:
    """TODO: real check + helpful failure message. For now just probe existence."""
    return VOLUME_ROOT.is_dir()


def build_recipe_export_map() -> None:
    raise NotImplementedError("Steps 1-3 land in task #7; volume not mounted yet")


def extract_all() -> None:
    raise NotImplementedError("Steps 1-3 land in task #7; volume not mounted yet")


# ─── CLI ────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--index-only", action="store_true", help="just rebuild beat_index.json"
    )
    p.add_argument(
        "--map-only", action="store_true", help="mount check + recipe_export_map.json"
    )
    p.add_argument(
        "--extract", action="store_true", help="run extraction (needs volume mounted)"
    )
    p.add_argument("--recipe", help="restrict extract to a single recipe slug")
    args = p.parse_args(argv)

    if args.index_only:
        write_beat_index()
        return 0

    if args.map_only or args.extract:
        if not check_mount():
            print(
                f"[mount] FAIL — {VOLUME_ROOT} is not mounted.\n"
                f"  In Finder: ⌘K → smb://<server>/2TB%20Footage\n"
                f"  Or: open 'smb://<server>/2TB Footage'",
                file=sys.stderr,
            )
            return 2

    if args.map_only:
        build_recipe_export_map()
        return 0

    if args.extract:
        build_recipe_export_map()
        extract_all()
        write_beat_index()
        return 0

    # default: try the full pipeline if volume is mounted, else just index
    if check_mount():
        build_recipe_export_map()
        extract_all()
    else:
        print(f"[mount] {VOLUME_ROOT} not mounted — running index step only.")
    write_beat_index()
    return 0


if __name__ == "__main__":
    sys.exit(main())
