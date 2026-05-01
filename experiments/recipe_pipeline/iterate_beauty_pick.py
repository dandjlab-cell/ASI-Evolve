"""Beauty-pick prompt iteration driver.

End-to-end loop:
  1. Load seed prompt from prompts/beauty_pick_text.jinja2.
  2. Evaluate against the 5-recipe corpus (runner + scorer).
  3. Ask Opus to mutate it — produce K variants targeting the lowest-scoring
     recipes' failure modes.
  4. Evaluate each variant on the corpus.
  5. Keep the best-composite-so-far. Repeat until plateau or max_generations.

Output:
  iteration_history.json — per-variant scores, kept best per generation.
  Each prompt variant saved to prompts/iter/{generation}_{variant_id}.jinja2.

Usage:
    # Benchmark seed only (no mutation)
    python iterate_beauty_pick.py --benchmark

    # Run N generations of mutation
    python iterate_beauty_pick.py --generations 3 --variants-per-gen 2

    # Single variant test (debug)
    python iterate_beauty_pick.py --benchmark --recipes korean_fried_chicken
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path("/Users/dandj/DevApps/ASI-Evolve/experiments/recipe_pipeline")
sys.path.insert(0, str(REPO_ROOT))

from runners.beauty_pick_runner import run_beauty_pick_variant, _call_opus_cli  # noqa: E402
from scorers.beauty_pick import score_beauty_picks, score_corpus  # noqa: E402

# Recipe slug mapping: runs/modal name → annotation slug (for truth lookup)
CORPUS = {
    "basil_pesto": "basil_pesto",
    "chicken_thighs": "chicken_thighs",
    "korean_fried_chicken": "korean_fried_chicken",
    "creamy_potato_soup": "creamy_potato_soup",
    "easy_banana_muffins": "banana_muffins",
}

PROMPTS_DIR = REPO_ROOT / "prompts"
ITER_DIR = PROMPTS_DIR / "iter"
SEED_PATH = PROMPTS_DIR / "beauty_pick_text.jinja2"
TRUTH_DIR = REPO_ROOT / "truth_sets"
HISTORY_PATH = REPO_ROOT / "runs" / "beauty_pick_iteration_history.json"


def load_truth(annotation_slug: str) -> list[dict]:
    return json.loads((TRUTH_DIR / annotation_slug / "beauty.json").read_text())["picks"]


def _eval_one_recipe(prompt_template: str, runs_name: str, ann_slug: str) -> tuple[str, dict]:
    """Worker for parallel evaluation. Returns (recipe_name, score_dict)."""
    t0 = time.time()
    try:
        result = run_beauty_pick_variant(prompt_template, runs_name)
        truth = load_truth(ann_slug)
        score = score_beauty_picks(result["picks"], truth)
        score["elapsed_s"] = round(time.time() - t0, 1)
        score["n_picks"] = len(result["picks"])
        return runs_name, score
    except Exception as e:
        return runs_name, {
            "composite": 0.0, "error": str(e), "elapsed_s": round(time.time() - t0, 1),
        }


def evaluate_prompt(prompt_template: str, recipes: dict[str, str], max_parallel: int = 5) -> dict:
    """Run prompt against corpus in parallel, return per-recipe scores + composite.

    recipes = {runs_modal_name: annotation_slug}
    Each recipe spawns its own claude CLI subprocess; the bottleneck is the
    LLM round-trip, not local CPU. Threads (not processes) are appropriate —
    we're I/O-bound on subprocess.run().
    """
    per_recipe: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {
            pool.submit(_eval_one_recipe, prompt_template, runs_name, ann_slug): runs_name
            for runs_name, ann_slug in recipes.items()
        }
        for fut in as_completed(futures):
            runs_name, score = fut.result()
            per_recipe[runs_name] = score
            if "error" in score:
                print(f"  {runs_name}: ERROR — {score['error']}", flush=True)
            else:
                print(
                    f"  {runs_name:>26}: composite={score['composite']:.3f} "
                    f"clip={score['clip_overlap']:.2f} time={score['time_match']:.2f} "
                    f"cat={score['category_balance']:.2f} "
                    f"({score.get('n_picks', '?')} picks, {score['elapsed_s']:.0f}s)",
                    flush=True,
                )
    corpus = score_corpus({r: per_recipe[r] for r in per_recipe if "error" not in per_recipe[r]})
    return {"per_recipe": per_recipe, "corpus": corpus}


MUTATION_META_PROMPT = """\
You are tuning a prompt for a food-video editor's beauty-pick selection LLM.
The prompt picks "beauty moments" (open-cooking and final-plated hero shots)
from a candidate pool of frames. Picks are scored against the editor's actual
prproj choices using:

    composite = 0.5 * clip_overlap   (did the LLM pick the right CLIP)
              + 0.4 * time_match     (was the pick within the editor's used SPAN, ±5s)
              + 0.1 * category_balance (open/final ratio match)

CURRENT BEST PROMPT (composite={current_score:.3f}):
─── BEGIN PROMPT ───
{current_prompt}
─── END PROMPT ───

PER-RECIPE SCORES:
{per_recipe_table}

EDITOR TRUTH FOR LOWEST-SCORING RECIPE ({worst_recipe}, composite={worst_score:.3f}):
{worst_truth}

LAST PICKS THIS PROMPT MADE FOR {worst_recipe} (selected from 80 candidates):
{worst_picks}

Generate {n_variants} mutated prompt variants. Each must:
1. Be a complete prompt with the same {{{{dish_name}}}}, {{{{ingredients_list}}}},
   {{{{candidates_block}}}}, {{{{num_candidates}}}} placeholders.
2. Address the specific failure mode you identified (be explicit in your
   reasoning about WHAT you're changing and WHY).
3. NOT exceed 500 words.

Reply with JSON only:
{{
  "variants": [
    {{
      "id": "v2_<short_descriptor>",
      "rationale": "<one sentence on what you changed>",
      "prompt": "<full prompt text>"
    }}
  ]
}}
"""


def format_per_recipe_table(per_recipe: dict) -> str:
    lines = []
    for r, s in sorted(per_recipe.items(), key=lambda x: x[1].get("composite", 0)):
        lines.append(
            f"  {r:>26}: {s.get('composite', 0):.3f} "
            f"(clip={s.get('clip_overlap', 0):.2f}, time={s.get('time_match', 0):.2f})"
        )
    return "\n".join(lines)


def format_truth(truth: list[dict]) -> str:
    return "\n".join(
        f"  {p.get('category', '?'):>5}: {p['clip_id']} @ {p.get('t_in', p.get('t', '?'))}s"
        f"–{p.get('t_out', '?')}s — {p.get('label', '')}"
        for p in truth
    )


def format_picks(picks: list[dict], limit: int = 10) -> str:
    if not picks:
        return "  (no picks)"
    return "\n".join(
        f"  {p.get('category', '?'):>5}: {p['clip_id']} @ {p['t']:.1f}s — {p.get('label', '')}"
        for p in picks[:limit]
    )


def request_mutations(current_prompt: str, eval_result: dict, n_variants: int) -> list[dict]:
    """Ask Opus to generate n mutated prompt variants targeting failures."""
    per_recipe = eval_result["per_recipe"]
    worst = min(per_recipe.items(), key=lambda x: x[1].get("composite", 0))
    worst_recipe, worst_score_dict = worst
    ann_slug = CORPUS.get(worst_recipe, worst_recipe)
    worst_truth = load_truth(ann_slug)

    # Re-run worst recipe to get current picks (cheap — we just had this)
    print(f"  Re-running {worst_recipe} to capture current picks for diagnosis...", flush=True)
    re_result = run_beauty_pick_variant(current_prompt, worst_recipe)
    worst_picks = re_result["picks"]

    meta = MUTATION_META_PROMPT.format(
        current_score=eval_result["corpus"]["composite"],
        current_prompt=current_prompt,
        per_recipe_table=format_per_recipe_table(per_recipe),
        worst_recipe=worst_recipe,
        worst_score=worst_score_dict["composite"],
        worst_truth=format_truth(worst_truth),
        worst_picks=format_picks(worst_picks),
        n_variants=n_variants,
    )

    print(f"  Asking Opus for {n_variants} mutations targeting {worst_recipe}...", flush=True)
    raw = _call_opus_cli(meta, timeout_s=300)

    # Parse — find the first JSON object
    import re as _re
    m = _re.search(r"\{.*\}", raw, flags=_re.DOTALL)
    if not m:
        print(f"    WARNING: no JSON in mutation response: {raw[:300]}")
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        print(f"    WARNING: malformed mutation JSON: {e}")
        return []
    variants = data.get("variants") or []
    return [v for v in variants if isinstance(v, dict) and v.get("prompt")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", action="store_true",
                    help="Score seed prompt only, no mutation")
    ap.add_argument("--generations", type=int, default=0)
    ap.add_argument("--variants-per-gen", type=int, default=2)
    ap.add_argument("--recipes", help="Comma-separated subset (default: all 5)")
    ap.add_argument("--seed-prompt", default=str(SEED_PATH))
    args = ap.parse_args()

    if args.recipes:
        wanted = set(args.recipes.split(","))
        recipes = {k: v for k, v in CORPUS.items() if k in wanted}
    else:
        recipes = CORPUS

    print(f"Corpus: {list(recipes)}\n")

    seed_prompt = Path(args.seed_prompt).read_text()
    print(f"=== Generation 0 (seed: {Path(args.seed_prompt).name}) ===", flush=True)
    seed_result = evaluate_prompt(seed_prompt, recipes)
    print(f"  CORPUS COMPOSITE: {seed_result['corpus']['composite']:.3f}\n", flush=True)

    history = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "corpus": list(recipes),
        "generations": [
            {
                "gen": 0,
                "id": "seed_v1",
                "rationale": "Seed prompt (recovered from roughcut-ai dd8e727).",
                "prompt": seed_prompt,
                "result": seed_result,
            }
        ],
    }
    best = {"id": "seed_v1", "prompt": seed_prompt, "composite": seed_result["corpus"]["composite"]}

    if args.benchmark:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(json.dumps(history, indent=2))
        print(f"\nWrote {HISTORY_PATH}")
        return 0

    ITER_DIR.mkdir(parents=True, exist_ok=True)
    for gen in range(1, args.generations + 1):
        print(f"\n=== Generation {gen} ===", flush=True)
        variants = request_mutations(best["prompt"], seed_result if gen == 1 else last_result,
                                      args.variants_per_gen)
        if not variants:
            print(f"  No variants returned. Stopping.")
            break

        gen_results = []
        for v in variants:
            vid = v.get("id", f"gen{gen}_unnamed")
            rationale = v.get("rationale", "")
            prompt_text = v["prompt"]
            (ITER_DIR / f"{gen:02d}_{vid}.jinja2").write_text(prompt_text)
            print(f"\n--- Variant {vid} — {rationale} ---", flush=True)
            r = evaluate_prompt(prompt_text, recipes)
            print(f"  CORPUS COMPOSITE: {r['corpus']['composite']:.3f}", flush=True)
            entry = {"gen": gen, "id": vid, "rationale": rationale,
                     "prompt": prompt_text, "result": r}
            history["generations"].append(entry)
            gen_results.append(entry)

            if r["corpus"]["composite"] > best["composite"]:
                print(f"  NEW BEST (was {best['composite']:.3f})", flush=True)
                best = {"id": vid, "prompt": prompt_text, "composite": r["corpus"]["composite"]}

        # Use winning result of this gen for next gen's mutation
        last_result = max(gen_results, key=lambda e: e["result"]["corpus"]["composite"])["result"]

        # Persist after each generation in case we get interrupted
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(json.dumps(history, indent=2))

    print(f"\n=== DONE ===")
    print(f"Best: {best['id']} composite={best['composite']:.3f}")
    HISTORY_PATH.write_text(json.dumps(history, indent=2))
    print(f"History: {HISTORY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
