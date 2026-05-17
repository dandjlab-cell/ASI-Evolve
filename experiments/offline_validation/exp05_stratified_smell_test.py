"""RAFT × beat_type smell test (N=42, basil_pesto + chicken_thighs only).

NOT a confirmatory experiment. Joins the existing exp05_results.json:per_beat
(42 beats from 2 recipes) with annotation beat_types and computes raft_delta
medians per beat_type. Sample sizes per type range from 1 to 21 — this is a
directional smell test to see whether the conditional pattern that holds for
VLM motion_phase × beat_type plausibly also holds for RAFT × beat_type.

Real stratified RAFT analysis requires:
- RAFT curves for the 16 missing recipes (one-shot Modal job)
- 329 untyped beats labeled via the Beat Review UI (in progress)

Outputs:
  runs/<UTC>/exp05_stratified_smell.json
  runs/<UTC>/exp05_stratified_smell.md
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ANNOTATIONS = REPO / "experiments" / "recipe_pipeline" / "annotations"
EXP05_RESULTS = (
    REPO
    / "experiments"
    / "offline_validation"
    / "runs"
    / "20260514T193913Z"
    / "exp05_results.json"
)
RUNS_ROOT = REPO / "experiments" / "offline_validation" / "runs"


def _load_beat_types() -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    for path in sorted(ANNOTATIONS.glob("*.json")):
        with path.open() as f:
            doc = json.load(f)
        for b in doc["beats"]:
            out[(doc["recipe"], b["beat_index"])] = {
                "beat_type": (b.get("beat_type") or "") or "UNTYPED",
                "recipe_section": b.get("recipe_section", ""),
                "verdict": b.get("verdict", ""),
                "duration_s": (b.get("duration") or {}).get("seconds"),
            }
    return out


def _bucket(per_beat: list[dict], beat_types: dict) -> dict:
    """Group exp05 per_beat by beat_type and recipe."""
    by_type: dict[str, list[dict]] = defaultdict(list)
    for pb in per_beat:
        key = (pb["recipe"], pb["beat_index"])
        meta = beat_types.get(key)
        if meta is None:
            continue
        by_type[meta["beat_type"]].append(
            {
                "recipe": pb["recipe"],
                "beat_index": pb["beat_index"],
                "raft_delta": pb["raft_delta"],
                "dino_delta": pb["dino_delta"],
            }
        )
    return by_type


def _summarize(beats: list[dict]) -> dict:
    deltas = [b["raft_delta"] for b in beats]
    by_recipe: dict[str, list[float]] = defaultdict(list)
    for b in beats:
        by_recipe[b["recipe"]].append(b["raft_delta"])
    return {
        "n_beats": len(beats),
        "n_recipes": len(by_recipe),
        "median_raft_delta_s": statistics.median(deltas) if deltas else None,
        "mean_raft_delta_s": statistics.fmean(deltas) if deltas else None,
        "per_recipe_median": {r: statistics.median(v) for r, v in by_recipe.items()},
        "per_recipe_n": {r: len(v) for r, v in by_recipe.items()},
        "all_negative": all(d < 0 for d in deltas) if deltas else None,
        "all_positive": all(d > 0 for d in deltas) if deltas else None,
    }


def run() -> tuple[Path, Path]:
    exp05 = json.loads(EXP05_RESULTS.read_text())
    beat_types = _load_beat_types()
    buckets = _bucket(exp05["per_beat"], beat_types)

    summary = {bt: _summarize(beats) for bt, beats in buckets.items()}

    out_dir = RUNS_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "exp05_stratified_smell.json"
    json_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "directional smell test only; N=42 from basil_pesto + chicken_thighs",
                "source": str(EXP05_RESULTS.relative_to(REPO)),
                "n_beats_in_exp05": len(exp05["per_beat"]),
                "n_beats_joinable": sum(s["n_beats"] for s in summary.values()),
                "notes": [
                    "raft_delta = min_dist_dan_raft_s - median_random_raft_s",
                    "negative delta means Dan's cut-out lands closer to a RAFT peak than random",
                    "samples per beat_type are tiny (1-21); statistical conclusions not supported",
                    "real stratification requires (a) RAFT curves for 16 missing recipes, (b) 329 untyped beats labeled",
                ],
                "by_beat_type": summary,
            },
            indent=2,
        )
    )

    md_lines = [
        "# RAFT × beat_type smell test (N=42)",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()}_",
        "",
        "**Status: DIRECTIONAL ONLY.** N=42 across 2 recipes (basil_pesto, chicken_thighs); per-beat_type samples range from 1 to 21. Not a confirmatory result.",
        "",
        "## Method",
        "",
        f"- Joined `{EXP05_RESULTS.relative_to(REPO)}:per_beat` (42 beats) with annotation `beat_type` on `(recipe, beat_index)`",
        "- `raft_delta = min_dist_dan_raft_s − median_random_raft_s` (from existing exp05 output)",
        "- **Negative** delta = Dan's cut-out lands *closer* to a RAFT motion-magnitude peak than random",
        "- **Positive** delta = Dan's cut-out lands *farther* from a RAFT peak than random",
        "",
        "## Results by beat_type",
        "",
        "| beat_type | n | recipes | median raft_delta (s) | direction | per-recipe medians |",
        "|---|---|---|---|---|---|",
    ]
    for bt, s in sorted(summary.items(), key=lambda kv: -kv[1]["n_beats"]):
        direction = (
            "closer (all)"
            if s["all_negative"]
            else "farther (all)"
            if s["all_positive"]
            else "mixed"
        )
        per_recipe = ", ".join(
            f"{r}={s['per_recipe_median'][r]:+.2f} (n={s['per_recipe_n'][r]})"
            for r in sorted(s["per_recipe_median"])
        )
        md_val = s["median_raft_delta_s"]
        md_lines.append(
            f"| `{bt}` | {s['n_beats']} | {s['n_recipes']} | "
            f"{md_val:+.3f} | {direction} | {per_recipe} |"
        )

    md_lines += [
        "",
        "## What this does NOT prove",
        "",
        "- Nothing about whether RAFT *as a categorical feature extractor* would give a blanket rule. That's a different experiment (threshold RAFT magnitude into phase labels, then test).",
        "- Nothing about the conditional pattern at the population level. With only 2 recipes and 1-3 beats in most named types, recipe-conditional variance is indistinguishable from beat_type signal.",
        "- Nothing about whether RAFT would outperform VLM `motion_phase` as the underlying signal feeding the stratified rule.",
        "",
        "## What it does suggest",
        "",
        "- Whether the median raft_delta differs *in sign* across beat_types within this thin sample.",
        "- Whether the per-recipe split inside a beat_type is wide (consistent with the recipe-conditional finding) or narrow.",
        "",
        "## What unblocks the real experiment",
        "",
        "1. **RAFT curves for the 16 missing recipes** (one-shot Modal job using existing `run_exp05_modal.py` + expanded `DRIVE_FOLDER_IDS`). ~30-60 min L4 time.",
        "2. **329 untyped beats labeled** via the Beat Review UI currently being built (plan: `~/.claude/plans/asi-evolve-handoff-written-misty-clock.md`).",
        "",
        "Once both land, re-run this script across the full 18-recipe / 618-beat corpus instead of N=42.",
    ]
    md_path = out_dir / "exp05_stratified_smell.md"
    md_path.write_text("\n".join(md_lines) + "\n")

    print(f"[smell-test] wrote {json_path.relative_to(REPO)}")
    print(f"[smell-test] wrote {md_path.relative_to(REPO)}")
    return json_path, md_path


if __name__ == "__main__":
    run()
