"""Build per-recipe shot-type cache.

For each candidate in the v2 pool (top-300 by VLM beauty_score), Opus reads
the JPEG and classifies it as close / medium / wide / overhead / macro / reveal.
Result cached to truth_sets/{recipe}/shot_types.json keyed by clip_id+rounded_t.

Reused by the runner — no per-iteration cost. ~25 min one-time wall.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline")
sys.path.insert(0, str(REPO))

from runners.beauty_pick_runner import (  # noqa: E402
    _build_production_candidates, _frame_path_for_candidate, RUNS_ROOT,
)

CORPUS = {
    "basil_pesto": "basil_pesto",
    "chicken_thighs": "chicken_thighs",
    "korean_fried_chicken": "korean_fried_chicken",
    "creamy_potato_soup": "creamy_potato_soup",
    "easy_banana_muffins": "banana_muffins",
}

CACHE_DIR = REPO / "truth_sets"
BATCH_SIZE = 25  # frames per Opus call

CLASSIFY_PROMPT = """\
You are classifying frames from a food video by SHOT TYPE only — not by content.

For each frame at the listed file path, choose the shot type that best describes
the camera framing:

  close       — close-up; tight on hands or food, fills most of the frame
  medium      — medium shot; hands + tool + food, typical action shot
  wide        — wide shot; multiple objects with surrounding space, establishing
  overhead    — looking down from above (top-down / bird's eye view)
  macro       — extreme close-up; single texture or detail, single ingredient
  reveal      — pull-back / pull-out shot showing a finished thing entering frame

Read each frame_path with the Read tool. Be decisive — pick one shot type per
frame. Emit JSON only:

{
  "shots": [
    {"index": 0, "shot": "close" | "medium" | "wide" | "overhead" | "macro" | "reveal"}
  ]
}

FRAMES TO CLASSIFY:
"""


def _call_opus(prompt: str, add_dirs: list[Path], timeout_s: int = 300) -> str:
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
        raise RuntimeError(f"CLI failed (rc={result.returncode}): {result.stderr[:300]}")
    return result.stdout


def _parse_shots(raw: str) -> dict[int, str]:
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    return {int(e["index"]): e["shot"]
            for e in data.get("shots", [])
            if isinstance(e, dict) and "index" in e and "shot" in e}


def _key(c: dict) -> str:
    return f"{c['clip_id']}@{int(round(c['t']))}"


def classify_candidates(recipe_slug: str, candidates: list[dict]) -> dict[str, str]:
    """Returns {key: shot_type} for the candidates, batching across Opus calls."""
    add_dirs: set[Path] = set()
    enriched: list[dict] = []
    for c in candidates:
        path = _frame_path_for_candidate(c, recipe_slug)
        if path is None:
            continue
        enriched.append({**c, "frame_path": str(path), "_key": _key(c)})
        add_dirs.add(path.parent.parent)

    out: dict[str, str] = {}
    for batch_start in range(0, len(enriched), BATCH_SIZE):
        batch = enriched[batch_start:batch_start + BATCH_SIZE]
        block = "\n".join(
            f"  [{i}] frame_path={c['frame_path']}  ({c['clip_id']} @ t={c['t']:.1f}s)"
            for i, c in enumerate(batch)
        )
        prompt = CLASSIFY_PROMPT + block + "\n"
        t0 = time.time()
        raw = _call_opus(prompt, list(add_dirs))
        shots = _parse_shots(raw)
        for i, c in enumerate(batch):
            shot = shots.get(i, "?")
            out[c["_key"]] = shot
        print(f"  batch {batch_start//BATCH_SIZE + 1}/{(len(enriched)+BATCH_SIZE-1)//BATCH_SIZE}: "
              f"{sum(1 for s in shots.values() if s != '?')}/{len(batch)} classified ({time.time()-t0:.0f}s)",
              flush=True)
    return out


def main() -> int:
    for runs_name, ann_slug in CORPUS.items():
        cache_path = CACHE_DIR / ann_slug / "shot_types.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if cache_path.exists():
            existing = json.loads(cache_path.read_text())
        else:
            existing = {}

        cands, _ = _build_production_candidates(runs_name)
        # Filter to only those not already cached
        to_classify = [c for c in cands if _key(c) not in existing]
        print(f"\n=== {runs_name}: {len(cands)} cands, {len(to_classify)} need classification "
              f"({len(existing)} cached) ===", flush=True)

        if to_classify:
            new = classify_candidates(runs_name, to_classify)
            existing.update(new)
            cache_path.write_text(json.dumps(existing, indent=2))
            print(f"  wrote {cache_path} ({len(existing)} entries total)")
        else:
            print(f"  all cached; skipping")

    return 0


if __name__ == "__main__":
    sys.exit(main())
