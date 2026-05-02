"""Shot-type diagnostic — does the picker's choice distribution match the editor's?

For each truth pick, classify the shot type from the corresponding scan-frame's
VLM description. Build editor's shot-type histogram per beauty category. Then
classify the picker's actual choices the same way and compare.

If picker's distribution diverges from editor's, the picker has a shot-type bias
that's a structural prompt-encoded fix.

Shot type classification (from VLM prose):
  close   — "close-up", "tight", "macro", "close shot", "close-up of"
  overhead — "overhead", "top-down", "from above", "bird's eye"
  medium  — "medium shot", "shoulder", "frame", neutral angle (default)
  wide    — "wide", "from a distance", "establishing", "platter and surroundings"

This runs against cached pool data — no LLM calls — so it's fast and free.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline")
sys.path.insert(0, str(REPO))

from runners.beauty_pick_runner import _build_production_candidates, RUNS_ROOT  # noqa: E402

CORPUS = {
    "basil_pesto": "basil_pesto",
    "chicken_thighs": "chicken_thighs",
    "korean_fried_chicken": "korean_fried_chicken",
    "creamy_potato_soup": "creamy_potato_soup",
    "easy_banana_muffins": "banana_muffins",
}

# Patterns ordered most-specific first
SHOT_PATTERNS = [
    ("overhead", re.compile(r"\b(overhead|top[- ]down|from above|bird'?s?[- ]?eye|aerial|looking down)\b", re.I)),
    ("close",    re.compile(r"\b(close[- ]up|close shot|tight|macro|close)\b", re.I)),
    ("wide",     re.compile(r"\b(wide|from a distance|establishing|platter.*surroundings|full spread|whole set)\b", re.I)),
    ("medium",   re.compile(r"\b(medium|shoulder|over the shoulder|three[- ]quarter)\b", re.I)),
]


def classify_shot(vlm_description: str) -> str:
    """Map a VLM frame description to a shot type. Defaults to 'medium' if no
    explicit cue — most VLM descriptions don't call out shot framing.
    """
    if not vlm_description:
        return "unknown"
    for shot_type, pat in SHOT_PATTERNS:
        if pat.search(vlm_description):
            return shot_type
    return "medium"  # default — most prose just describes the action


def find_scan_frame(scan: dict, clip_id: str, t: float) -> dict | None:
    """Find the scan frame nearest to (clip_id, t)."""
    clip = (scan.get("clips") or {}).get(clip_id)
    if not clip:
        return None
    frames = clip.get("frames") or []
    if not frames:
        return None
    return min(frames, key=lambda f: abs((f.get("t") or 0) - t))


def main() -> int:
    print("Shot-type distribution: editor truth vs candidate pool\n")
    print(f"{'recipe':<22} {'cat':<6} {'shot':<10} {'truth':>6}  {'pool':>6}")
    print("-" * 60)

    editor_global: Counter = Counter()
    pool_global: Counter = Counter()

    for runs_name, ann_slug in CORPUS.items():
        run_dir = RUNS_ROOT / runs_name
        scan = json.loads((run_dir / "scan.json").read_text())
        truth = json.loads((REPO / "truth_sets" / ann_slug / "beauty.json").read_text())["picks"]
        cands, _ = _build_production_candidates(runs_name)

        editor_dist: dict[str, Counter] = defaultdict(Counter)  # category → shot → count
        for p in truth:
            frame = find_scan_frame(scan, p["clip_id"], p["t_in"])
            desc = (frame.get("description") if frame else "") or ""
            shot = classify_shot(desc)
            cat = p.get("category", "?")
            editor_dist[cat][shot] += 1
            editor_global[shot] += 1

        # Pool distribution for the same recipe — what the picker has access to
        pool_dist: Counter = Counter()
        for c in cands:
            shot = classify_shot(c.get("vlm_description", "") or "")
            pool_dist[shot] += 1
            pool_global[shot] += 1

        all_shots = sorted(set(list(editor_dist.get("open", {}).keys()) +
                              list(editor_dist.get("final", {}).keys()) +
                              list(pool_dist.keys())))
        for cat in ("open", "final"):
            for shot in all_shots:
                t_count = editor_dist[cat].get(shot, 0)
                p_count = pool_dist.get(shot, 0)
                if t_count == 0 and p_count == 0:
                    continue
                print(f"{runs_name:<22} {cat:<6} {shot:<10} {t_count:>6}  {p_count:>6}")
        print()

    print("=" * 60)
    print(f"{'GLOBAL':<22} {'':<6} {'shot':<10} {'truth':>6}  {'pool':>6}")
    all_global_shots = sorted(set(list(editor_global.keys()) + list(pool_global.keys())))
    e_total = sum(editor_global.values())
    p_total = sum(pool_global.values())
    for shot in all_global_shots:
        t = editor_global[shot]
        p = pool_global[shot]
        t_pct = 100*t/e_total if e_total else 0
        p_pct = 100*p/p_total if p_total else 0
        print(f"{'':<22} {'':<6} {shot:<10} {t:>3} ({t_pct:>3.0f}%)  {p:>5} ({p_pct:>3.0f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
