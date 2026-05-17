"""RAFT signed-peak-distance × beat_type test (N=42).

Tests Dan's hypothesis: "I cut just before the action happens, and cut when it ends."

The original Exp #5 used `min_dist_dan_raft_s = min(|cut - peak|)` — an UNSIGNED
distance that can't distinguish cut-before-peak from cut-after-peak. This script
recomputes the same alignment with a SIGNED delta:

    signed_delta = cut_out_s - nearest_peak_time_s
       < 0  → cut happened BEFORE peak (action not yet at maximum motion)
       > 0  → cut happened AFTER peak (action has finished)
       = 0  → cut on the peak

"Nearest peak" is the peak that minimizes |cut - peak|, same as exp05's choice.

Uses the existing cached RAFT curves at .cache/exp05_curves/{recipe}/{clip}.json
and the per_beat records in runs/20260514T193913Z/exp05_results.json (which carry
recipe, beat_index, source_id, cut_out_s for the 42 qualifying beats).

Matches exp05_raft_subject_vs_camera.py peak-detection config exactly:
    prominence_percentile = 75
    scipy.signal.find_peaks(curve, prominence=np.percentile(curve, 75))

Outputs:
    runs/<UTC>/exp05_signed_delta.json
    runs/<UTC>/exp05_signed_delta.md
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

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
CURVES_DIR = REPO / "experiments" / "offline_validation" / ".cache" / "exp05_curves"
RUNS_ROOT = REPO / "experiments" / "offline_validation" / "runs"

PROMINENCE_PERCENTILE = 75  # matches exp05_raft_subject_vs_camera.py:53


def _load_beat_types() -> dict[tuple[str, int], str]:
    out: dict[tuple[str, int], str] = {}
    for path in sorted(ANNOTATIONS.glob("*.json")):
        doc = json.loads(path.read_text())
        for b in doc["beats"]:
            out[(doc["recipe"], b["beat_index"])] = (
                b.get("beat_type") or ""
            ) or "UNTYPED"
    return out


def _peak_times(curve: list[float], t_midpoints: list[float]) -> np.ndarray:
    """Same as exp05's _peak_times: percentile-based prominence threshold."""
    curve_a = np.asarray(curve, dtype=float)
    t_a = np.asarray(t_midpoints, dtype=float)
    prom = float(np.percentile(curve_a, PROMINENCE_PERCENTILE))
    peaks, _ = find_peaks(curve_a, prominence=prom)
    return t_a[peaks]


def _signed_nearest(cut_time: float, peaks: np.ndarray) -> float | None:
    """signed_delta = cut - nearest_peak (sign carries before/after)."""
    if len(peaks) == 0:
        return None
    idx = int(np.argmin(np.abs(peaks - cut_time)))
    return float(cut_time - peaks[idx])


def _summarize(records: list[dict]) -> dict:
    signed = [r["signed_delta"] for r in records if r["signed_delta"] is not None]
    if not signed:
        return {"n_beats": 0}
    by_recipe: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r["signed_delta"] is not None:
            by_recipe[r["recipe"]].append(r["signed_delta"])
    n_before = sum(1 for d in signed if d < 0)
    n_after = sum(1 for d in signed if d > 0)
    n_zero = sum(1 for d in signed if d == 0)
    return {
        "n_beats": len(signed),
        "n_recipes": len(by_recipe),
        "median_signed_delta_s": statistics.median(signed),
        "mean_signed_delta_s": statistics.fmean(signed),
        "n_cut_before_peak": n_before,
        "n_cut_after_peak": n_after,
        "n_cut_on_peak": n_zero,
        "pct_cut_before": round(100 * n_before / len(signed), 1),
        "pct_cut_after": round(100 * n_after / len(signed), 1),
        "per_recipe_median": {r: statistics.median(v) for r, v in by_recipe.items()},
        "per_recipe_n": {r: len(v) for r, v in by_recipe.items()},
    }


def run() -> tuple[Path, Path]:
    exp05 = json.loads(EXP05_RESULTS.read_text())
    beat_types = _load_beat_types()

    # Pre-compute peak times per (recipe, source_id) — same curve serves many beats
    curve_cache: dict[tuple[str, str], np.ndarray] = {}

    per_beat_signed: list[dict] = []
    n_missing_curve = 0
    n_no_peaks = 0
    for pb in exp05["per_beat"]:
        key = (pb["recipe"], pb["source_id"])
        if key not in curve_cache:
            cp = CURVES_DIR / pb["recipe"] / f"{pb['source_id']}.json"
            if not cp.is_file():
                n_missing_curve += 1
                continue
            d = json.loads(cp.read_text())
            curve_cache[key] = _peak_times(d["subject_motion"], d["t_midpoints_s"])
        peaks = curve_cache[key]
        if len(peaks) == 0:
            n_no_peaks += 1
            continue
        signed = _signed_nearest(pb["cut_out_s"], peaks)
        bt = beat_types.get((pb["recipe"], pb["beat_index"]), "NO_MATCH")
        per_beat_signed.append(
            {
                "recipe": pb["recipe"],
                "beat_index": pb["beat_index"],
                "source_id": pb["source_id"],
                "cut_out_s": pb["cut_out_s"],
                "signed_delta": signed,
                "abs_delta": abs(signed),
                "beat_type": bt,
                "n_peaks_in_clip": int(len(peaks)),
            }
        )

    by_type: dict[str, list[dict]] = defaultdict(list)
    for r in per_beat_signed:
        by_type[r["beat_type"]].append(r)

    summary = {bt: _summarize(rs) for bt, rs in by_type.items()}
    overall = _summarize(per_beat_signed)

    out_dir = RUNS_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "exp05_signed_delta.json"
    json_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "directional smell test only; N=42 from basil_pesto + chicken_thighs",
                "hypothesis_under_test": "Dan cuts just before the action happens, and cut when it ends",
                "interpretation": {
                    "signed_delta_negative": "cut BEFORE peak (action not yet at maximum motion)",
                    "signed_delta_positive": "cut AFTER peak (action has finished)",
                    "signed_delta_zero": "cut on the peak (during maximum motion)",
                },
                "source": str(EXP05_RESULTS.relative_to(REPO)),
                "prominence_percentile": PROMINENCE_PERCENTILE,
                "n_beats_in_exp05": len(exp05["per_beat"]),
                "n_beats_signed": len(per_beat_signed),
                "n_missing_curve": n_missing_curve,
                "n_no_peaks": n_no_peaks,
                "caveats": [
                    "samples per beat_type are tiny (1-21); statistical conclusions not supported",
                    "'nearest peak' uses |cut - peak|; if Dan cuts equidistant between two peaks, sign is determined by floating-point tiebreak",
                    "peaks computed with prominence = 75th percentile of subject_motion curve, matching exp05 config",
                    "real test requires (a) RAFT curves for 16 missing recipes, (b) 329 untyped beats labeled",
                ],
                "overall": overall,
                "by_beat_type": summary,
                "per_beat": per_beat_signed,
            },
            indent=2,
        )
    )

    md = [
        "# RAFT signed-peak-distance × beat_type (N=42)",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()}_",
        "",
        "**Hypothesis under test:** *Dan cuts just before the action happens, and cuts when it ends.*",
        "",
        "## Method",
        "",
        "Recomputed peak distance with sign: `signed_delta = cut_out_s − nearest_peak_time_s`.",
        "",
        "- **Negative** signed_delta → cut happened BEFORE peak (action not yet at maximum motion)",
        "- **Positive** signed_delta → cut happened AFTER peak (action has finished)",
        "- **Zero** → cut on the peak",
        "",
        f"Peaks detected via `scipy.signal.find_peaks(curve, prominence=np.percentile(curve, {PROMINENCE_PERCENTILE}))` — same config as exp05_raft_subject_vs_camera.py:53.",
        "",
        "**Status: DIRECTIONAL ONLY.** N=42 across 2 recipes; per-beat_type samples 1-21.",
        "",
        "## Overall (all 42 beats)",
        "",
        f"- Median signed_delta: **{overall['median_signed_delta_s']:+.3f}s**",
        f"- Cut BEFORE peak: {overall['n_cut_before_peak']} of {overall['n_beats']} ({overall['pct_cut_before']}%)",
        f"- Cut AFTER peak: {overall['n_cut_after_peak']} of {overall['n_beats']} ({overall['pct_cut_after']}%)",
        f"- Cut ON peak: {overall['n_cut_on_peak']}",
        "",
        "## By beat_type",
        "",
        "| beat_type | n | median signed_delta (s) | % before | % after | per-recipe medians |",
        "|---|---|---|---|---|---|",
    ]
    for bt, s in sorted(summary.items(), key=lambda kv: -kv[1]["n_beats"]):
        per_recipe = ", ".join(
            f"{r}={s['per_recipe_median'][r]:+.2f}s (n={s['per_recipe_n'][r]})"
            for r in sorted(s["per_recipe_median"])
        )
        md.append(
            f"| `{bt}` | {s['n_beats']} | {s['median_signed_delta_s']:+.3f} | "
            f"{s['pct_cut_before']}% | {s['pct_cut_after']}% | {per_recipe} |"
        )

    md += [
        "",
        "## Reading guide",
        "",
        "If Dan's hypothesis holds, we'd expect:",
        "",
        "- A **bimodal** distribution overall — many cuts well before peaks (cut-before) AND many cuts well after peaks (cut-after), with FEW cuts on the peak itself.",
        "- For **action-heavy beat_types** (ingredient drops, technique work): cuts cluster AFTER peaks (`% after` high, median positive) — *cut when the action ends*.",
        "- For **anticipatory beat_types** (beauty_opener establishing a shot before the action arrives): cuts cluster BEFORE peaks (`% before` high, median negative) — *cut just before the action happens*.",
        "",
        "## What this does NOT prove",
        "",
        "- Same N=42 limit as the unsigned smell test. Tiny per-type samples.",
        "- 'Nearest peak' can flip sign for a cut that lands equidistant between two peaks. With prominence=75th-percentile and dense peaks (e.g. 148 peaks in 204s for basil_pesto AI2I5202), inter-peak intervals are short and this is a real source of noise.",
        "- Does not distinguish 'cut before THIS action's start' vs 'cut after PREVIOUS action's end' when the cut lands in dead time between two motion peaks. Operationalization needs work.",
        "",
        "## What this could suggest (if directions hold)",
        "",
        "- A median signed_delta significantly different from zero (in either direction) for a beat_type with n ≥ ~10 would be the first hint that the cut-before/cut-after axis is editorially structured.",
        "- A `% before` or `% after` skewed strongly away from 50/50 for a beat_type means cuts are temporally biased relative to peaks — directional support for the hypothesis.",
        "- Per-recipe medians agreeing in sign within a beat_type strengthens the directional read.",
        "",
        "## What unblocks the real test",
        "",
        "1. **RAFT curves for the 16 missing recipes.** Existing `run_exp05_modal.py`, expand `DRIVE_FOLDER_IDS`.",
        "2. **329 untyped beats labeled** via the Beat Review UI.",
        "",
        "After both, re-run with this same operationalization on N ≈ 600.",
    ]
    md_path = out_dir / "exp05_signed_delta.md"
    md_path.write_text("\n".join(md) + "\n")

    print(f"[signed-delta] wrote {json_path.relative_to(REPO)}")
    print(f"[signed-delta] wrote {md_path.relative_to(REPO)}")
    print(
        f"[signed-delta] n_signed={len(per_beat_signed)}, "
        f"missing_curve={n_missing_curve}, no_peaks={n_no_peaks}"
    )
    return json_path, md_path


if __name__ == "__main__":
    run()
