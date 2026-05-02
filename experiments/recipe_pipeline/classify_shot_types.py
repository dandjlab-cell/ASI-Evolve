"""Visual shot-type classification — Opus reads actual JPEG frames for editor
truth picks AND picker's choices, aggregates the shot-type distribution.

Answers: does the picker pick a different shot-type mix than the editor?
If YES, we have a structural prompt fix. If NO, shot type isn't the bottleneck.

Per recipe:
  1. Resolve each truth pick's JPEG path (clip_id + t → scan_frames/_dino_<cid>/frame_NNNN.jpg)
  2. Batch all truth-pick frames in one Opus call, ask for shot type per frame
  3. Run picker (text mode), classify picker's picks the same way
  4. Output side-by-side distribution

Cost: ~5 Opus calls per recipe × 5 recipes = ~25 calls. Free under subscription.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline")
sys.path.insert(0, str(REPO))

from runners.beauty_pick_runner import (  # noqa: E402
    _frame_path_for_candidate, run_beauty_pick_variant, RUNS_ROOT,
)
from scorers.beauty_pick import score_beauty_picks  # noqa: E402

CORPUS = {
    "basil_pesto": "basil_pesto",
    "chicken_thighs": "chicken_thighs",
    "korean_fried_chicken": "korean_fried_chicken",
    "creamy_potato_soup": "creamy_potato_soup",
    "easy_banana_muffins": "banana_muffins",
}

CLASSIFY_PROMPT = """\
You are classifying frames from a food video by SHOT TYPE only — not by content.

Look at each frame at the listed file path. For each, choose the shot type that
best describes the camera framing:

  close       — close-up, tight on hands or food, fills most of the frame
  medium      — medium shot, hands + tool + food in frame, typical action shot
  wide        — wide shot, multiple objects with surrounding space, establishing
  overhead    — looking down from above (top-down / bird's eye)
  macro       — extreme close-up, single texture / detail / single ingredient
  reveal      — pull-back or pull-out shot showing a finished thing entering frame

Read each frame_path with the Read tool. Then emit JSON only:

{
  "shots": [
    {"index": 0, "shot": "close" | "medium" | "wide" | "overhead" | "macro" | "reveal"}
  ]
}

FRAMES TO CLASSIFY:
"""


def _call_opus(prompt: str, add_dirs: list[Path], timeout_s: int = 240) -> str:
    cmd = [
        "claude", "-p", prompt,
        "--model", "claude-opus-4-7",
        "--output-format", "text",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--exclude-dynamic-system-prompt-sections",
    ]
    for d in add_dirs:
        cmd.extend(["--add-dir", str(d)])
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=timeout_s, check=False,
                            cwd=tempfile.gettempdir())
    if result.returncode != 0:
        raise RuntimeError(f"CLI failed: {result.stderr[:300]}")
    return result.stdout


def _parse_shots(raw: str, n_frames: int) -> dict[int, str]:
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    shots = {}
    for entry in data.get("shots", []):
        if isinstance(entry, dict) and "index" in entry and "shot" in entry:
            shots[int(entry["index"])] = entry["shot"]
    return shots


def classify_frames(items: list[dict], recipe_slug: str) -> dict[int, str]:
    """items: [{clip_id, t, ...}]. Returns {index: shot_type}."""
    enriched = []
    add_dirs = set()
    for i, c in enumerate(items):
        path = _frame_path_for_candidate(c, recipe_slug)
        if path is None:
            continue
        enriched.append({**c, "_idx": i, "frame_path": str(path)})
        add_dirs.add(path.parent.parent)
    if not enriched:
        return {}

    block = "\n".join(
        f"  [{e['_idx']}] frame_path={e['frame_path']}\n      ({e['clip_id']} @ t={e['t']:.1f}s)"
        for e in enriched
    )
    prompt = CLASSIFY_PROMPT + block + "\n"
    raw = _call_opus(prompt, list(add_dirs))
    return _parse_shots(raw, len(items))


def main() -> int:
    print("Classifying shot types — editor truth picks vs picker's actual picks\n")

    editor_dist: dict[str, Counter] = defaultdict(Counter)   # category → shot → count
    picker_dist: dict[str, Counter] = defaultdict(Counter)
    per_recipe_log = []

    # Load fewshot prompt once
    fewshot_prompt = (REPO / "prompts/beauty_pick_text_fewshot.jinja2").read_text()

    for runs_name, ann_slug in CORPUS.items():
        print(f"=== {runs_name} ===", flush=True)
        truth = json.loads((REPO / "truth_sets" / ann_slug / "beauty.json").read_text())["picks"]

        # Editor side: classify each truth pick's frame
        truth_items = [{"clip_id": p["clip_id"], "t": p["t_in"], "category": p.get("category", "?")}
                       for p in truth]
        t0 = time.time()
        truth_shots = classify_frames(truth_items, runs_name)
        print(f"  editor truth: {len(truth_shots)}/{len(truth_items)} classified ({time.time()-t0:.0f}s)")
        for i, item in enumerate(truth_items):
            shot = truth_shots.get(i, "?")
            editor_dist[item["category"]][shot] += 1

        # Picker side: run picker, classify its picks
        t0 = time.time()
        result = run_beauty_pick_variant(fewshot_prompt, runs_name)
        print(f"  picker: {len(result['picks'])} picks in {time.time()-t0:.0f}s")

        pick_items = [{"clip_id": p["clip_id"], "t": p["t"], "category": p.get("category", "?")}
                      for p in result["picks"]]
        if pick_items:
            t0 = time.time()
            pick_shots = classify_frames(pick_items, runs_name)
            print(f"  picker shots: {len(pick_shots)}/{len(pick_items)} classified ({time.time()-t0:.0f}s)")
            for i, item in enumerate(pick_items):
                shot = pick_shots.get(i, "?")
                picker_dist[item["category"]][shot] += 1

        per_recipe_log.append({
            "recipe": runs_name,
            "truth_count": len(truth_items),
            "picker_count": len(pick_items),
        })
        print()

    # Print the comparison
    print("\n" + "=" * 70)
    print(f"{'category':<8} {'shot':<10} {'editor':>8}  {'picker':>8}  {'editor%':>8}  {'picker%':>8}")
    print("-" * 70)
    all_shots = set()
    for d in (editor_dist, picker_dist):
        for cat_counter in d.values():
            all_shots.update(cat_counter.keys())

    for cat in ("open", "final", "?"):
        e_total = sum(editor_dist[cat].values())
        p_total = sum(picker_dist[cat].values())
        if e_total == 0 and p_total == 0:
            continue
        for shot in sorted(all_shots):
            e = editor_dist[cat].get(shot, 0)
            p = picker_dist[cat].get(shot, 0)
            if e == 0 and p == 0:
                continue
            e_pct = (100*e/e_total) if e_total else 0
            p_pct = (100*p/p_total) if p_total else 0
            print(f"{cat:<8} {shot:<10} {e:>8}  {p:>8}  {e_pct:>7.0f}%  {p_pct:>7.0f}%")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
