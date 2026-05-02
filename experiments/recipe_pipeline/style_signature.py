#!/usr/bin/env python3
"""
style_signature.py — Phase 2 master plan: aggregate Dan's editorial patterns
across the annotated recipe corpus into structured distributions.

Reads every annotation JSON in `experiments/recipe_pipeline/annotations/`
(currently 18 recipes, ~600 beats), computes core distributions, flags
recipes that deviate from corpus median, emits two artifacts:

  1. JSON sidecar (raw distributions, downstream-friendly)
       experiments/recipe_pipeline/style_signature_v1.json
  2. Markdown vault note (human-readable summary + anomaly flags)
       ~/DevApps/Brain/Projects/ASI-Evolve/Editing Agent — Style Signature v1.md

V1 dimensions (all cleanly mineable from the annotation JSON schema):
  - Beat count per recipe
  - Beat-type distribution (corpus + per-recipe)
  - Camera distribution by beat_type
  - Duration percentiles (overall + by beat_type)
  - Camera run lengths (consecutive same-camera spans)
  - Outlier recipes per dimension (Tukey 1.5×IQR fence)

Deferred to v2 (require XML re-parse or schema work not in JSON):
  - Speed-ramp taxonomy
  - Nest (nested sequence) usage
  - Stop-motion / appearance-compilation per-segment stats
  - Title-card / beauty_close placement timing

See ~/DevApps/Brain/Projects/ASI-Evolve/Editing Agent - Roadmap.md Phase 2.
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
ANNOTATIONS_DIR = REPO_ROOT / "annotations"
JSON_OUT = REPO_ROOT / "style_signature_v1.json"
VAULT_NOTE = (
    Path.home() / "DevApps/Brain/Projects/ASI-Evolve/Editing Agent — Style Signature v1.md"
)

logger = logging.getLogger("style_signature")


# ---------------------------------------------------------------------------
# Beat-field accessors (tolerant of schema drift across 18 recipes)
# ---------------------------------------------------------------------------

def get_camera(beat: dict) -> str:
    """Camera choice as a normalized lowercase string. 'unknown' if missing/None."""
    cam = beat.get("camera")
    if isinstance(cam, dict):
        choice = cam.get("choice")
    else:
        choice = cam
    if not choice:
        return "unknown"
    return str(choice).strip().lower() or "unknown"


def get_beat_type(beat: dict) -> str:
    """Beat type, normalized. 'unlabeled' if missing/empty."""
    bt = beat.get("beat_type")
    if not bt:
        return "unlabeled"
    return str(bt).strip().lower()


def get_duration_seconds(beat: dict) -> float | None:
    """Duration in seconds, or None if not derivable."""
    dur = beat.get("duration")
    if isinstance(dur, dict):
        s = dur.get("seconds")
    else:
        s = dur
    if s is None:
        # Fall back to in/out diff
        ip = beat.get("in_point")
        op = beat.get("out_point")
        try:
            ips = ip.get("seconds") if isinstance(ip, dict) else ip
            ops = op.get("seconds") if isinstance(op, dict) else op
            if ips is not None and ops is not None:
                return float(ops) - float(ips)
        except (AttributeError, TypeError, ValueError):
            return None
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Distribution primitives
# ---------------------------------------------------------------------------

def percentiles(values: list[float], ps=(10, 25, 50, 75, 90)) -> dict[str, float]:
    """Return {p10: ..., p25: ..., p50: ..., p75: ..., p90: ...}. Empty -> all 0."""
    if not values:
        return {f"p{p}": 0.0 for p in ps}
    s = sorted(values)
    out = {}
    for p in ps:
        # Linear interpolation between two nearest ranks (matches numpy default)
        k = (len(s) - 1) * (p / 100.0)
        f = int(k)
        c = min(f + 1, len(s) - 1)
        d = k - f
        out[f"p{p}"] = round(s[f] + (s[c] - s[f]) * d, 3)
    return out


def tukey_fence_outliers(by_key: dict[str, float]) -> dict[str, Any]:
    """1.5×IQR fence outlier detection across a {label: scalar} mapping.

    Returns:
      {
        "median": ..., "p25": ..., "p75": ..., "iqr": ...,
        "low_fence": ..., "high_fence": ...,
        "low": [{"recipe": ..., "value": ...}, ...],
        "high": [...]
      }
    """
    if len(by_key) < 4:
        return {"median": 0, "p25": 0, "p75": 0, "iqr": 0,
                "low_fence": 0, "high_fence": 0, "low": [], "high": []}
    values = sorted(by_key.values())
    p25, p75 = percentiles(values, (25, 75)).values()
    iqr = p75 - p25
    low_fence = p25 - 1.5 * iqr
    high_fence = p75 + 1.5 * iqr
    low = [{"recipe": k, "value": v} for k, v in by_key.items() if v < low_fence]
    high = [{"recipe": k, "value": v} for k, v in by_key.items() if v > high_fence]
    return {
        "median": round(statistics.median(values), 3),
        "p25": round(p25, 3),
        "p75": round(p75, 3),
        "iqr": round(iqr, 3),
        "low_fence": round(low_fence, 3),
        "high_fence": round(high_fence, 3),
        "low": sorted(low, key=lambda x: x["value"]),
        "high": sorted(high, key=lambda x: -x["value"]),
    }


def consecutive_runs(items: list[str]) -> list[tuple[str, int]]:
    """Group consecutive identical items. ['a','a','b','a'] -> [('a',2),('b',1),('a',1)]."""
    if not items:
        return []
    runs = []
    cur, n = items[0], 1
    for x in items[1:]:
        if x == cur:
            n += 1
        else:
            runs.append((cur, n))
            cur, n = x, 1
    runs.append((cur, n))
    return runs


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_annotations(annotations_dir: Path) -> dict[str, dict]:
    """Load every JSON in the annotations dir keyed by recipe slug (file stem)."""
    out: dict[str, dict] = {}
    for f in sorted(annotations_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            logger.error("skipping %s: %s", f.name, e)
            continue
        slug = f.stem
        out[slug] = d
        logger.debug("loaded %s: %d beats", slug, len(d.get("beats", [])))
    return out


# ---------------------------------------------------------------------------
# Aggregators (each returns one slice of the signature)
# ---------------------------------------------------------------------------

def beat_count_signature(annotations: dict[str, dict]) -> dict:
    by_recipe = {slug: len(d.get("beats", [])) for slug, d in annotations.items()}
    return {
        "per_recipe": dict(sorted(by_recipe.items(), key=lambda kv: kv[1])),
        "total_beats": sum(by_recipe.values()),
        "outliers": tukey_fence_outliers(by_recipe),
    }


def beat_type_signature(annotations: dict[str, dict]) -> dict:
    corpus_counts: Counter = Counter()
    per_recipe: dict[str, dict] = {}
    for slug, d in annotations.items():
        c: Counter = Counter()
        for b in d.get("beats", []):
            c[get_beat_type(b)] += 1
        corpus_counts.update(c)
        per_recipe[slug] = dict(c.most_common())

    # Outliers per beat_type — recipes with disproportionate share of any type
    type_outliers: dict[str, dict] = {}
    for bt in corpus_counts:
        by_recipe_share = {}
        for slug, recipe_counts in per_recipe.items():
            total = sum(recipe_counts.values()) or 1
            share = recipe_counts.get(bt, 0) / total
            by_recipe_share[slug] = round(share, 4)
        type_outliers[bt] = tukey_fence_outliers(by_recipe_share)

    return {
        "corpus": dict(corpus_counts.most_common()),
        "per_recipe": per_recipe,
        "share_outliers_by_type": type_outliers,
    }


def camera_coverage_per_recipe(annotations: dict[str, dict]) -> dict[str, dict]:
    """Per-recipe camera labeling coverage. A recipe is 'labeled' if it has at
    least one beat with a non-unknown camera. Otherwise 'unlabeled' (excluded
    from camera-by-beat-type aggregates because every beat is unknown).
    """
    out = {}
    for slug, d in annotations.items():
        beats = d.get("beats", [])
        cams = Counter(get_camera(b) for b in beats)
        labeled_n = sum(v for k, v in cams.items() if k != "unknown")
        out[slug] = {
            "beats": len(beats),
            "labeled": labeled_n,
            "unknown": cams.get("unknown", 0),
            "coverage": round(labeled_n / len(beats), 3) if beats else 0.0,
        }
    return out


def camera_by_beat_type_signature(annotations: dict[str, dict]) -> dict:
    """Camera-by-beat-type aggregates restricted to recipes with non-zero
    camera-label coverage. The unlabeled recipes are reported separately so
    they don't contaminate the proportions.
    """
    coverage = camera_coverage_per_recipe(annotations)
    labeled_recipes = {s for s, c in coverage.items() if c["labeled"] > 0}
    unlabeled_recipes = sorted(set(annotations) - labeled_recipes)

    out: dict[str, Counter] = defaultdict(Counter)
    overall: Counter = Counter()
    for slug, d in annotations.items():
        if slug not in labeled_recipes:
            continue
        for b in d.get("beats", []):
            bt = get_beat_type(b)
            cam = get_camera(b)
            out[bt][cam] += 1
            overall[cam] += 1
    return {
        "labeled_recipes": sorted(labeled_recipes),
        "unlabeled_recipes": unlabeled_recipes,
        "coverage_per_recipe": coverage,
        "overall_camera": dict(overall.most_common()),
        "by_beat_type": {bt: dict(c.most_common()) for bt, c in out.items()},
    }


def duration_signature(annotations: dict[str, dict]) -> dict:
    overall: list[float] = []
    by_type: dict[str, list[float]] = defaultdict(list)
    by_recipe: dict[str, list[float]] = defaultdict(list)
    for slug, d in annotations.items():
        for b in d.get("beats", []):
            dur = get_duration_seconds(b)
            if dur is None or dur <= 0:
                continue
            overall.append(dur)
            by_type[get_beat_type(b)].append(dur)
            by_recipe[slug].append(dur)
    median_per_recipe = {
        slug: round(statistics.median(durs), 3)
        for slug, durs in by_recipe.items() if durs
    }
    return {
        "overall_percentiles": percentiles(overall),
        "overall_n": len(overall),
        "by_beat_type": {
            bt: {**percentiles(durs), "n": len(durs)}
            for bt, durs in by_type.items()
        },
        "median_per_recipe": median_per_recipe,
        "median_outliers": tukey_fence_outliers(median_per_recipe),
    }


def camera_run_signature(annotations: dict[str, dict]) -> dict:
    """Distribution of consecutive same-camera run lengths.

    Restricted to recipes with non-zero camera-label coverage. All-unknown
    recipes would otherwise produce a single run of length N == beat_count,
    polluting the `unknown` bucket with the recipe's full length.
    """
    coverage = camera_coverage_per_recipe(annotations)
    labeled = {s for s, c in coverage.items() if c["labeled"] > 0}
    by_camera: dict[str, list[int]] = defaultdict(list)
    by_recipe: dict[str, dict[str, list[int]]] = {}
    for slug, d in annotations.items():
        if slug not in labeled:
            continue
        cams = [get_camera(b) for b in d.get("beats", [])]
        runs = consecutive_runs(cams)
        per_recipe_cam: dict[str, list[int]] = defaultdict(list)
        for cam, length in runs:
            by_camera[cam].append(length)
            per_recipe_cam[cam].append(length)
        by_recipe[slug] = {cam: lengths for cam, lengths in per_recipe_cam.items()}

    summary = {}
    for cam, lengths in by_camera.items():
        summary[cam] = {
            "n_runs": len(lengths),
            "max_run": max(lengths) if lengths else 0,
            **percentiles(lengths, (25, 50, 75, 90)),
        }

    # Per-recipe max run length — outliers = recipes with unusually long camera holds
    max_run_per_recipe = {}
    for slug, cam_runs in by_recipe.items():
        if not cam_runs:
            continue
        all_lens = [n for lens in cam_runs.values() for n in lens]
        max_run_per_recipe[slug] = max(all_lens) if all_lens else 0

    return {
        "by_camera_summary": summary,
        "max_run_per_recipe": dict(sorted(max_run_per_recipe.items(), key=lambda kv: -kv[1])),
        "max_run_outliers": tukey_fence_outliers(max_run_per_recipe),
    }


# ---------------------------------------------------------------------------
# Top-level signature build
# ---------------------------------------------------------------------------

def build_signature(annotations: dict[str, dict]) -> dict:
    return {
        "schema_version": 1,
        "generated_at": date.today().isoformat(),
        "scope": {
            "recipe_count": len(annotations),
            "recipes": sorted(annotations.keys()),
        },
        "beat_count": beat_count_signature(annotations),
        "beat_type_distribution": beat_type_signature(annotations),
        "camera_by_beat_type": camera_by_beat_type_signature(annotations),
        "duration": duration_signature(annotations),
        "camera_runs": camera_run_signature(annotations),
        "deferred_v2": [
            "speed-ramp taxonomy (requires Premiere XML re-parse)",
            "nested sequence usage (XML re-parse)",
            "stop-motion segment-level stats (need per-segment frame counts)",
            "title-card / beauty_close placement timing (need timeline_in coords)",
        ],
    }


# ---------------------------------------------------------------------------
# Markdown writer
# ---------------------------------------------------------------------------

def fmt_pct(n: int, total: int) -> str:
    return f"{(100*n/total):.1f}%" if total else "—"


def render_markdown(sig: dict) -> str:
    out: list[str] = []
    out.append("---")
    out.append("project: ASI-Evolve")
    out.append("type: signature")
    out.append("date: " + sig["generated_at"])
    out.append("status: v1")
    out.append("tags: [asi-evolve, style-signature, editing-agent, distributions]")
    out.append("source: experiments/recipe_pipeline/style_signature.py")
    out.append("related:")
    out.append('  - "[[Editing Agent - Roadmap]]"')
    out.append('  - "[[Editorial Rules - Dan\'s Camera Logic]]"')
    out.append('  - "[[Recipe Pipeline Evolution - Design Sketch]]"')
    out.append("---")
    out.append("")
    out.append("# Editing Agent — Style Signature v1")
    out.append("")
    scope = sig["scope"]
    out.append(
        f"Aggregate distributions across {scope['recipe_count']} annotated recipes "
        f"({sig['beat_count']['total_beats']} beats total). Computed by "
        f"`experiments/recipe_pipeline/style_signature.py`. Raw distributions live "
        f"in the JSON sidecar (`style_signature_v1.json`); this note is the "
        f"human-readable summary + anomaly callouts."
    )
    out.append("")
    out.append("This is the Phase 2 deliverable in [[Editing Agent - Roadmap]] — the "
               "first artifact that captures Dan's pattern-language across the "
               "corpus rather than recipe-by-recipe. Feeds Phase 3 (discrimination "
               "test against constructed bad variants), Phase 5 (rule extension), "
               "and the medium-horizon M2 critic-fine-tune training data.")
    out.append("")
    out.append("## Corpus snapshot")
    out.append("")
    bc = sig["beat_count"]
    out.append(f"- Recipes: {scope['recipe_count']}")
    out.append(f"- Total beats: {bc['total_beats']}")
    out.append(f"- Median beats per recipe: {bc['outliers']['median']:.0f} "
               f"(p25 {bc['outliers']['p25']:.0f}, p75 {bc['outliers']['p75']:.0f}, "
               f"IQR {bc['outliers']['iqr']:.0f})")
    overall_p = sig["duration"]["overall_percentiles"]
    out.append(f"- Beat duration percentiles (s): "
               f"p10 {overall_p['p10']}, p25 {overall_p['p25']}, "
               f"**p50 {overall_p['p50']}**, p75 {overall_p['p75']}, p90 {overall_p['p90']}")
    out.append(f"- Beat-duration sample size: {sig['duration']['overall_n']} beats with valid duration")
    out.append("")

    # ---- Beat count per recipe table ----
    out.append("## Beat count per recipe")
    out.append("")
    out.append("| Recipe | Beats | Note |")
    out.append("|---|---|---|")
    high_flags = {x["recipe"]: "high" for x in bc["outliers"]["high"]}
    low_flags = {x["recipe"]: "low" for x in bc["outliers"]["low"]}
    for slug, n in sorted(bc["per_recipe"].items(), key=lambda kv: -kv[1]):
        flag = ""
        if slug in high_flags:
            flag = f"⚠️ above 1.5×IQR fence ({bc['outliers']['high_fence']:.0f})"
        elif slug in low_flags:
            flag = f"⚠️ below 1.5×IQR fence ({bc['outliers']['low_fence']:.0f})"
        out.append(f"| {slug} | {n} | {flag} |")
    out.append("")

    # ---- Beat-type distribution ----
    btd = sig["beat_type_distribution"]
    total = sum(btd["corpus"].values())
    out.append("## Beat-type distribution (corpus)")
    out.append("")
    out.append("| Beat type | Count | % |")
    out.append("|---|---|---|")
    for bt, n in btd["corpus"].items():
        out.append(f"| `{bt}` | {n} | {fmt_pct(n, total)} |")
    out.append("")
    out.append("Note: `unlabeled` reflects beats whose `beat_type` field is missing "
               "or null in the annotation JSON. Future passes can backfill these "
               "by inference from `recipe_section` text or visual context.")
    out.append("")

    # ---- Camera distribution overall + by beat_type ----
    cbt = sig["camera_by_beat_type"]
    overall_cam_total = sum(cbt["overall_camera"].values())
    out.append("## Camera distribution")
    out.append("")
    n_labeled = len(cbt["labeled_recipes"])
    unlabeled = cbt["unlabeled_recipes"]
    if unlabeled:
        out.append(f"**Coverage gap.** {len(unlabeled)} of {scope['recipe_count']} "
                   "recipes have NO camera labels at all (every beat's `camera.choice` is null). "
                   "Camera-by-beat-type aggregates below restrict to the "
                   f"{n_labeled} fully-labeled recipes only. Unlabeled recipes:")
        out.append("")
        for slug in unlabeled:
            cov = cbt["coverage_per_recipe"][slug]
            out.append(f"- `{slug}` ({cov['beats']} beats, all unknown)")
        out.append("")
        out.append("These are the 5 recipes that overlap with the ASI beauty-pick "
                   "corpus — they were re-annotated during the beauty-pick session "
                   "via a flow that didn't populate `camera.choice`. Backfilling is "
                   "a one-shot pass over `analyze_editorial_judgment.py` (or its "
                   "successor) once the camera-detection bug noted in the roadmap "
                   "is resolved.")
        out.append("")
    out.append(f"**Overall** (across the {n_labeled} labeled recipes):")
    out.append("")
    out.append("| Camera | Count | % |")
    out.append("|---|---|---|")
    for cam, n in cbt["overall_camera"].items():
        out.append(f"| `{cam}` | {n} | {fmt_pct(n, overall_cam_total)} |")
    out.append("")

    out.append("**By beat type** (camera proportions per beat type):")
    out.append("")
    cam_order = list(cbt["overall_camera"].keys())
    header = "| Beat type | n | " + " | ".join(f"`{c}`" for c in cam_order) + " |"
    sep = "|---|---|" + "|".join("---" for _ in cam_order) + "|"
    out.append(header)
    out.append(sep)
    for bt in btd["corpus"].keys():
        cams = cbt["by_beat_type"].get(bt, {})
        n = sum(cams.values())
        cells = []
        for c in cam_order:
            v = cams.get(c, 0)
            cells.append(f"{v} ({fmt_pct(v, n)})" if n else "—")
        out.append(f"| `{bt}` | {n} | " + " | ".join(cells) + " |")
    out.append("")

    # ---- Duration percentiles by beat_type ----
    out.append("## Beat duration percentiles (seconds)")
    out.append("")
    out.append("**Overall:**")
    op = sig["duration"]["overall_percentiles"]
    out.append("")
    out.append("| p10 | p25 | p50 | p75 | p90 | n |")
    out.append("|---|---|---|---|---|---|")
    out.append(f"| {op['p10']} | {op['p25']} | **{op['p50']}** | {op['p75']} | {op['p90']} | {sig['duration']['overall_n']} |")
    out.append("")
    out.append("**By beat type:**")
    out.append("")
    out.append("| Beat type | p10 | p25 | p50 | p75 | p90 | n |")
    out.append("|---|---|---|---|---|---|---|")
    for bt in btd["corpus"].keys():
        p = sig["duration"]["by_beat_type"].get(bt)
        if not p:
            continue
        out.append(f"| `{bt}` | {p['p10']} | {p['p25']} | **{p['p50']}** | {p['p75']} | {p['p90']} | {p['n']} |")
    out.append("")
    dout = sig["duration"]["median_outliers"]
    if dout["high"] or dout["low"]:
        out.append("**Per-recipe median-duration outliers** "
                   f"(median {dout['median']}s, fence "
                   f"[{dout['low_fence']}, {dout['high_fence']}]s):")
        out.append("")
        for x in dout["low"]:
            out.append(f"- `{x['recipe']}` median {x['value']}s — unusually fast")
        for x in dout["high"]:
            out.append(f"- `{x['recipe']}` median {x['value']}s — unusually slow")
        out.append("")

    # ---- Camera run lengths ----
    cr = sig["camera_runs"]
    out.append("## Camera run lengths (consecutive same-camera holds)")
    out.append("")
    out.append("Long runs of one camera = sustained editorial intent (e.g. an extended "
               "ingredient-dump on overhead). Frequent short runs = rapid alternation, "
               "which Editorial Rule 2 explicitly discourages during dump sequences.")
    out.append("")
    out.append("| Camera | n runs | max | p25 | p50 | p75 | p90 |")
    out.append("|---|---|---|---|---|---|---|")
    for cam, s in cr["by_camera_summary"].items():
        out.append(f"| `{cam}` | {s['n_runs']} | {s['max_run']} | "
                   f"{s['p25']} | {s['p50']} | {s['p75']} | {s['p90']} |")
    out.append("")
    out.append("**Longest run per recipe** (top 5):")
    out.append("")
    out.append("| Recipe | Max consecutive same-camera beats |")
    out.append("|---|---|")
    for slug, m in list(cr["max_run_per_recipe"].items())[:5]:
        out.append(f"| {slug} | {m} |")
    out.append("")
    mout = cr["max_run_outliers"]
    if mout["high"]:
        out.append(f"**Outliers** (above fence {mout['high_fence']:.0f}):")
        out.append("")
        for x in mout["high"]:
            out.append(f"- `{x['recipe']}` max-run {x['value']} beats")
        out.append("")

    # ---- Deferred ----
    out.append("## Deferred to v2")
    out.append("")
    for d in sig["deferred_v2"]:
        out.append(f"- {d}")
    out.append("")

    # ---- Where this feeds ----
    out.append("## What this enables")
    out.append("")
    p50 = sig["duration"]["overall_percentiles"]["p50"]
    out.append(f"- **Phase 3 discrimination test**: bad-variant construction now has "
               f"concrete numeric thresholds to violate (e.g. \"break the median "
               f"{p50}s beat duration by setting all beats to 0.3s\" — well below "
               f"the corpus p10). Expected scorer response becomes measurable "
               f"rather than directional.")
    out.append("- **Phase 5 rule extension**: any recipe-pattern that survives across "
               "the corpus median (with low IQR) is a candidate for promotion to a "
               "scorer rule. Patterns that show wide IQR are recipe-specific and "
               "should NOT become scorer rules — they should become per-candidate or "
               "per-recipe metadata. (Same categorical lesson as the beauty-pick work: "
               "[[Per-Candidate Tags Beat Per-Corpus Rules]].)")
    out.append("- **M2 critic training**: per-beat (context, decision) pairs already "
               "exist in the annotation JSONs. This signature defines the *baseline* "
               "the critic must beat — predicting Dan's choices better than corpus-median.")
    out.append("")
    out.append("## How to regenerate")
    out.append("")
    out.append("```bash")
    out.append("cd ~/DevApps/ASI-Evolve")
    out.append("python3 experiments/recipe_pipeline/style_signature.py")
    out.append("```")
    out.append("")
    out.append("Re-runs are deterministic given the annotations directory. To target a "
               "different output dir or skip the vault note, see `--help`.")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--annotations-dir", type=Path, default=ANNOTATIONS_DIR)
    p.add_argument("--json-out", type=Path, default=JSON_OUT)
    p.add_argument("--vault-note", type=Path, default=VAULT_NOTE,
                   help="Markdown summary path. Pass empty string to skip.")
    p.add_argument("--no-vault-note", action="store_true",
                   help="Skip writing the vault note (JSON only).")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if not args.annotations_dir.is_dir():
        logger.error("annotations dir not found: %s", args.annotations_dir)
        return 2

    annotations = load_annotations(args.annotations_dir)
    if not annotations:
        logger.error("no annotations loaded")
        return 2
    logger.info("loaded %d annotations, %d total beats",
                len(annotations),
                sum(len(d.get("beats", [])) for d in annotations.values()))

    sig = build_signature(annotations)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(sig, indent=2, sort_keys=False))
    logger.info("wrote JSON: %s (%d bytes)",
                args.json_out, args.json_out.stat().st_size)

    if not args.no_vault_note:
        md = render_markdown(sig)
        args.vault_note.parent.mkdir(parents=True, exist_ok=True)
        args.vault_note.write_text(md)
        logger.info("wrote vault note: %s (%d bytes)",
                    args.vault_note, args.vault_note.stat().st_size)

    return 0


if __name__ == "__main__":
    sys.exit(main())
