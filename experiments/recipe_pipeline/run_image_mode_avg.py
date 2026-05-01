"""3-run avg image mode across the 5-recipe corpus."""
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

from runners.beauty_pick_runner import run_beauty_pick_variant_image_mode
from scorers.beauty_pick import score_beauty_picks

CORPUS = {
    "basil_pesto": "basil_pesto",
    "chicken_thighs": "chicken_thighs",
    "korean_fried_chicken": "korean_fried_chicken",
    "creamy_potato_soup": "creamy_potato_soup",
    "easy_banana_muffins": "banana_muffins",
}
TRUTH_DIR = REPO / "truth_sets"


def load_truth(slug):
    return json.loads((TRUTH_DIR / slug / "beauty.json").read_text())["picks"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default=str(REPO / "prompts/beauty_pick_image.jinja2"))
    ap.add_argument("-n", "--runs", type=int, default=3)
    args = ap.parse_args()

    prompt = Path(args.prompt).read_text()

    def one_eval(prompt, runs_name, ann_slug):
        t0 = time.time()
        result = run_beauty_pick_variant_image_mode(prompt, runs_name)
        truth = load_truth(ann_slug)
        score = score_beauty_picks(result["picks"], truth)
        score["elapsed_s"] = round(time.time() - t0, 1)
        return runs_name, score, len(result["picks"])

    per_recipe = {r: [] for r in CORPUS}
    for run_i in range(args.runs):
        print(f"\n=== Run {run_i + 1}/{args.runs} ===", flush=True)
        with ThreadPoolExecutor(max_workers=len(CORPUS)) as pool:
            futures = {
                pool.submit(one_eval, prompt, runs_name, ann_slug): runs_name
                for runs_name, ann_slug in CORPUS.items()
            }
            for fut in as_completed(futures):
                runs_name, score, n_picks = fut.result()
                per_recipe[runs_name].append(score)
                print(f"  {runs_name:>26}: composite={score['composite']:.3f} "
                      f"clip={score['clip_overlap']:.2f} time={score['time_match']:.2f} "
                      f"({n_picks} picks, {score['elapsed_s']:.0f}s)", flush=True)

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
              f"(clip={statistics.mean(clips):.2f}, time={statistics.mean(times):.2f}, "
              f"cat={statistics.mean(cats):.2f}) runs=[{', '.join(f'{c:.2f}' for c in comps)}]")
    print(f"\n  CORPUS AVG: {statistics.mean(composites):.3f}")


if __name__ == "__main__":
    sys.exit(main())
