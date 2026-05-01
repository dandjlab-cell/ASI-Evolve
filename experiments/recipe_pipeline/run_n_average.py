"""Run a prompt N times and average the composites — denoise the score.

Single-run scoring has ~±0.05 noise from Opus non-determinism, which masks
real prompt-quality differences. Running each variant N times and taking the
mean cuts noise by ~sqrt(N).

Usage:
    python run_n_average.py --prompt prompts/beauty_pick_text_fewshot.jinja2 -n 3
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline")
sys.path.insert(0, str(REPO))

from runners.beauty_pick_runner import run_beauty_pick_variant  # noqa: E402
from scorers.beauty_pick import score_beauty_picks  # noqa: E402

CORPUS = {
    "basil_pesto": "basil_pesto",
    "chicken_thighs": "chicken_thighs",
    "korean_fried_chicken": "korean_fried_chicken",
    "creamy_potato_soup": "creamy_potato_soup",
    "easy_banana_muffins": "banana_muffins",
}

TRUTH_DIR = REPO / "truth_sets"


def load_truth(slug: str) -> list[dict]:
    return json.loads((TRUTH_DIR / slug / "beauty.json").read_text())["picks"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("-n", "--runs", type=int, default=3)
    args = ap.parse_args()

    prompt_text = Path(args.prompt).read_text()
    print(f"Prompt: {args.prompt}\nRuns per recipe: {args.runs}\n")

    def _one_eval(prompt: str, runs_name: str, ann_slug: str) -> tuple[str, dict, int]:
        t0 = time.time()
        result = run_beauty_pick_variant(prompt, runs_name)
        truth = load_truth(ann_slug)
        score = score_beauty_picks(result["picks"], truth)
        score["elapsed_s"] = round(time.time() - t0, 1)
        return runs_name, score, len(result["picks"])

    per_recipe: dict[str, list[dict]] = {r: [] for r in CORPUS}
    for run_i in range(args.runs):
        print(f"=== Run {run_i + 1}/{args.runs} ===", flush=True)
        # Fan out all 5 recipes in parallel — each call is I/O-bound on
        # subprocess.run(claude); threads handle this fine.
        with ThreadPoolExecutor(max_workers=len(CORPUS)) as pool:
            futures = {
                pool.submit(_one_eval, prompt_text, runs_name, ann_slug): runs_name
                for runs_name, ann_slug in CORPUS.items()
            }
            for fut in as_completed(futures):
                runs_name, score, n_picks = fut.result()
                per_recipe[runs_name].append(score)
                print(f"  {runs_name:>26}: composite={score['composite']:.3f} "
                      f"clip={score['clip_overlap']:.2f} time={score['time_match']:.2f} "
                      f"({n_picks} picks, {score['elapsed_s']:.0f}s)",
                      flush=True)

    print(f"\n=== AVERAGED ACROSS {args.runs} RUNS ===")
    composites = []
    for runs_name in CORPUS:
        runs = per_recipe[runs_name]
        comps = [r["composite"] for r in runs]
        clips = [r["clip_overlap"] for r in runs]
        times = [r["time_match"] for r in runs]
        cats = [r["category_balance"] for r in runs]
        mean = statistics.mean(comps)
        stdev = statistics.stdev(comps) if len(comps) > 1 else 0.0
        composites.append(mean)
        print(f"  {runs_name:>26}: {mean:.3f} ±{stdev:.3f}  "
              f"(clip={statistics.mean(clips):.2f}, "
              f"time={statistics.mean(times):.2f}, "
              f"cat={statistics.mean(cats):.2f}) "
              f"runs=[{', '.join(f'{c:.2f}' for c in comps)}]")
    corpus_mean = statistics.mean(composites)
    print(f"\n  CORPUS AVG: {corpus_mean:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
