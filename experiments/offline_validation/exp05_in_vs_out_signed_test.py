"""RAFT signed-delta for BOTH cut-in and cut-out × beat_type (N=42).

Tests the symmetric hypothesis (Dan's exact words):
  *"The clip starts just before the peak of the action. So I cut INTO a shot
  just moments before the action happens, and cut OUT when it ends."*

Operationalization:
  in_signed_delta  = in_point_s  − nearest_peak_time_s
  out_signed_delta = cut_out_s   − nearest_peak_time_s

  in_signed_delta < 0  → clip STARTED before peak (consistent with "cut in just before action")
  out_signed_delta > 0 → clip ENDED after peak   (consistent with "cut out when action ends")

If the hypothesis holds, we expect both halves to show the predicted sign and
the per-beat asymmetry: median IN negative-small, median OUT positive-small.

Uses cached RAFT curves at .cache/exp05_curves/{recipe}/{clip}.json.
Joins exp05 per_beat records with annotation in_point.seconds on (recipe, beat_index).

Matches exp05 peak config exactly: prominence_percentile = 75.

Outputs:
    runs/<UTC>/exp05_in_vs_out_signed.json
    runs/<UTC>/exp05_in_vs_out_signed.md
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

PROMINENCE_PERCENTILE = 75


def _load_annotations() -> dict[tuple[str, int], dict]:
    """Pull beat_type + in_point + duration per (recipe, beat_index)."""
    out: dict[tuple[str, int], dict] = {}
    for path in sorted(ANNOTATIONS.glob("*.json")):
        doc = json.loads(path.read_text())
        for b in doc["beats"]:
            ip = (b.get("in_point") or {}).get("seconds")
            dur = (b.get("duration") or {}).get("seconds")
            out[(doc["recipe"], b["beat_index"])] = {
                "beat_type": (b.get("beat_type") or "") or "UNTYPED",
                "in_point_s": ip,
                "duration_s": dur,
                "out_point_s": ip + dur
                if (ip is not None and dur is not None)
                else None,
            }
    return out


def _peak_times(curve: list[float], t_midpoints: list[float]) -> np.ndarray:
    curve_a = np.asarray(curve, dtype=float)
    t_a = np.asarray(t_midpoints, dtype=float)
    prom = float(np.percentile(curve_a, PROMINENCE_PERCENTILE))
    peaks, _ = find_peaks(curve_a, prominence=prom)
    return t_a[peaks]


def _signed_nearest(cut_time: float, peaks: np.ndarray) -> float | None:
    if len(peaks) == 0:
        return None
    idx = int(np.argmin(np.abs(peaks - cut_time)))
    return float(cut_time - peaks[idx])


def _summarize(records: list[dict], field: str) -> dict:
    vals = [r[field] for r in records if r.get(field) is not None]
    if not vals:
        return {"n": 0}
    by_recipe: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r.get(field) is not None:
            by_recipe[r["recipe"]].append(r[field])
    n_before = sum(1 for v in vals if v < 0)
    n_after = sum(1 for v in vals if v > 0)
    n_zero = sum(1 for v in vals if v == 0)
    return {
        "n": len(vals),
        "n_recipes": len(by_recipe),
        "median_s": statistics.median(vals),
        "mean_s": statistics.fmean(vals),
        "n_before": n_before,
        "n_after": n_after,
        "n_on": n_zero,
        "pct_before": round(100 * n_before / len(vals), 1),
        "pct_after": round(100 * n_after / len(vals), 1),
        "per_recipe_median": {r: statistics.median(v) for r, v in by_recipe.items()},
        "per_recipe_n": {r: len(v) for r, v in by_recipe.items()},
    }


def run() -> tuple[Path, Path]:
    exp05 = json.loads(EXP05_RESULTS.read_text())
    ann = _load_annotations()

    curve_cache: dict[tuple[str, str], np.ndarray] = {}
    records: list[dict] = []
    n_missing_curve = n_no_peaks = n_missing_in_point = 0

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

        meta = ann.get((pb["recipe"], pb["beat_index"]))
        if meta is None:
            continue
        in_s = meta["in_point_s"]
        out_s = pb["cut_out_s"]  # already in source-clip coords

        in_signed = _signed_nearest(in_s, peaks) if in_s is not None else None
        out_signed = _signed_nearest(out_s, peaks)

        if in_s is None:
            n_missing_in_point += 1

        records.append(
            {
                "recipe": pb["recipe"],
                "beat_index": pb["beat_index"],
                "source_id": pb["source_id"],
                "in_point_s": in_s,
                "cut_out_s": out_s,
                "duration_s": meta["duration_s"],
                "in_signed_delta": in_signed,
                "out_signed_delta": out_signed,
                "beat_type": meta["beat_type"],
            }
        )

    by_type: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_type[r["beat_type"]].append(r)

    overall_in = _summarize(records, "in_signed_delta")
    overall_out = _summarize(records, "out_signed_delta")

    out_dir = RUNS_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir.mkdir(parents=True, exist_ok=True)

    by_type_summary = {
        bt: {
            "in": _summarize(rs, "in_signed_delta"),
            "out": _summarize(rs, "out_signed_delta"),
        }
        for bt, rs in by_type.items()
    }

    json_path = out_dir / "exp05_in_vs_out_signed.json"
    json_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scope": "directional smell test only; N=42 from basil_pesto + chicken_thighs",
                "hypothesis_under_test": (
                    "The clip starts just before the peak of the action. "
                    "So I cut INTO a shot just moments before the action happens, "
                    "and cut OUT when it ends."
                ),
                "predicted_signs": {
                    "in_signed_delta_median": "NEGATIVE (clip starts before peak)",
                    "out_signed_delta_median": "POSITIVE (clip ends after peak)",
                },
                "source": str(EXP05_RESULTS.relative_to(REPO)),
                "prominence_percentile": PROMINENCE_PERCENTILE,
                "n_beats": len(records),
                "n_missing_curve": n_missing_curve,
                "n_no_peaks": n_no_peaks,
                "n_missing_in_point": n_missing_in_point,
                "caveats": [
                    "samples per beat_type are tiny (1-21); statistical conclusions not supported",
                    "'nearest peak' can flip sign if the cut lands equidistant between two peaks",
                    "peaks computed with prominence = 75th percentile (same as exp05); peaks are dense (often a peak every ~1-2s)",
                    "in-point and out-point may share the same nearest peak when the beat is short; that's the case the hypothesis predicts",
                    "real test requires (a) RAFT curves for 16 missing recipes, (b) 329 untyped beats labeled",
                ],
                "overall": {"in": overall_in, "out": overall_out},
                "by_beat_type": by_type_summary,
                "per_beat": records,
            },
            indent=2,
        )
    )

    def _row(label: str, s: dict) -> str:
        if s.get("n", 0) == 0:
            return f"| {label} | 0 | — | — | — | — |"
        return (
            f"| {label} | {s['n']} | {s['median_s']:+.3f} | "
            f"{s['pct_before']}% | {s['pct_after']}% | {s['n_before']}/{s['n_after']} |"
        )

    md = [
        "# RAFT signed-delta — cut-IN vs cut-OUT × beat_type (N=42)",
        "",
        f"_Generated {datetime.now(timezone.utc).isoformat()}_",
        "",
        "**Hypothesis under test:** *The clip starts just before the peak of the action. So I cut INTO a shot just moments before the action happens, and cut OUT when it ends.*",
        "",
        "## Predicted vs observed signs",
        "",
        "| signal | predicted | observed (median) | direction |",
        "|---|---|---|---|",
        f"| `in_signed_delta`  | NEGATIVE (cut-in before peak) | {overall_in['median_s']:+.3f}s | {'consistent' if overall_in['median_s'] < 0 else 'opposite' if overall_in['median_s'] > 0 else 'zero'} |",
        f"| `out_signed_delta` | POSITIVE (cut-out after peak) | {overall_out['median_s']:+.3f}s | {'consistent' if overall_out['median_s'] > 0 else 'opposite' if overall_out['median_s'] < 0 else 'zero'} |",
        "",
        "## Overall (all 42 beats)",
        "",
        "**Cut IN** (clip start):",
        f"- median {overall_in['median_s']:+.3f}s",
        f"- before peak: {overall_in['n_before']}/{overall_in['n']} ({overall_in['pct_before']}%)",
        f"- after peak:  {overall_in['n_after']}/{overall_in['n']} ({overall_in['pct_after']}%)",
        "",
        "**Cut OUT** (clip end):",
        f"- median {overall_out['median_s']:+.3f}s",
        f"- before peak: {overall_out['n_before']}/{overall_out['n']} ({overall_out['pct_before']}%)",
        f"- after peak:  {overall_out['n_after']}/{overall_out['n']} ({overall_out['pct_after']}%)",
        "",
        "## By beat_type — cut-IN signed-delta",
        "",
        "| beat_type | n | median (s) | % before | % after | before/after |",
        "|---|---|---|---|---|---|",
    ]
    for bt, sub in sorted(
        by_type_summary.items(), key=lambda kv: -kv[1]["in"].get("n", 0)
    ):
        md.append(_row(f"`{bt}`", sub["in"]))

    md += [
        "",
        "## By beat_type — cut-OUT signed-delta",
        "",
        "| beat_type | n | median (s) | % before | % after | before/after |",
        "|---|---|---|---|---|---|",
    ]
    for bt, sub in sorted(
        by_type_summary.items(), key=lambda kv: -kv[1]["out"].get("n", 0)
    ):
        md.append(_row(f"`{bt}`", sub["out"]))

    md += [
        "",
        "## Per-beat side-by-side (sorted by beat_type, then recipe)",
        "",
        "| recipe | beat | beat_type | in_signed (s) | out_signed (s) | duration (s) |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(
        records, key=lambda x: (x["beat_type"], x["recipe"], x["beat_index"])
    ):
        in_str = (
            f"{r['in_signed_delta']:+.2f}" if r["in_signed_delta"] is not None else "—"
        )
        out_str = (
            f"{r['out_signed_delta']:+.2f}"
            if r["out_signed_delta"] is not None
            else "—"
        )
        dur_str = f"{r['duration_s']:.2f}" if r["duration_s"] is not None else "—"
        md.append(
            f"| {r['recipe']} | {r['beat_index']} | `{r['beat_type']}` | "
            f"{in_str} | {out_str} | {dur_str} |"
        )

    md += [
        "",
        "## How to read the directional finding",
        "",
        "**If Dan's hypothesis holds at this sample size:**",
        "- `in_signed_delta` median should be NEGATIVE and `% before` > 50% (clips START before peaks).",
        "- `out_signed_delta` median should be POSITIVE and `% after` > 50% (clips END after peaks).",
        "- The two signs together form an *envelope around the peak*: clip brackets the action.",
        "",
        "**Caveats specific to this operationalization:**",
        "- 'Nearest peak' for the IN-point and the OUT-point may be the SAME peak when the beat is short. That's actually what the hypothesis predicts — the clip wraps a single action peak.",
        "- For beats spanning multiple peaks, IN's nearest peak ≠ OUT's nearest peak; the signs are then independent.",
        "- At prominence=75th-percentile, peaks are dense; small signed_deltas dominate.",
        "",
        "## What this does NOT prove",
        "",
        "- Same N=42 limit. Per-beat_type samples are 1-21.",
        "- Cannot distinguish 'cut into a shot before this action' from 'cut into a shot after the previous action' in dense-peak regions.",
        "- VLM `motion_phase` × `beat_type` is the cleaner-but-different signal at larger N (7 recipes / 149 beats). This RAFT-based test is the only existing-data way to read the IN/OUT-vs-peak axis directly.",
        "",
        "## What unblocks the real test",
        "",
        "1. **RAFT curves for the 16 missing recipes** (`run_exp05_modal.py` + expanded `DRIVE_FOLDER_IDS`).",
        "2. **329 untyped beats labeled** via the Beat Review UI.",
        "",
        "Then re-run this same script on N ≈ 600 with proper per-beat_type sample sizes.",
    ]
    md_path = out_dir / "exp05_in_vs_out_signed.md"
    md_path.write_text("\n".join(md) + "\n")

    print(f"[in-vs-out] wrote {json_path.relative_to(REPO)}")
    print(f"[in-vs-out] wrote {md_path.relative_to(REPO)}")
    print(
        f"[in-vs-out] n={len(records)}, missing_curve={n_missing_curve}, "
        f"no_peaks={n_no_peaks}, missing_in_point={n_missing_in_point}"
    )
    return json_path, md_path


if __name__ == "__main__":
    run()
