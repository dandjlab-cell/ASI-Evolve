"""Beauty-pick scorer.

Scores a beauty_pick prompt's output against the editor's actual choices.
Loss function (matches the handoff brief):

    composite = 0.5 * clip_overlap
              + 0.4 * time_match
              + 0.1 * category_balance

Where:
- clip_overlap = fraction of pick clip_ids that appear in the truth clip set
- time_match   = fraction of picks within ±TIME_TOLERANCE_S of a truth pick's
                 source time (paired by clip_id)
- category_balance = 1 - |pick_final_ratio - truth_final_ratio|

Pure function. No I/O. The runner wires up the file reads.

Truth shape (from truth_sets/{recipe}/beauty.json):
    {"picks": [{"category": "open"|"final", "clip_id": "B19I6339", "t": 75.4, ...}]}

Predicted shape (from beauty_picks.json):
    {"picks": [{"category": "open"|"final", "clip_id": "B19I6339", "t": 73.0, ...}]}
"""

from __future__ import annotations

TIME_TOLERANCE_S = 5.0


def _final_ratio(picks: list[dict]) -> float:
    if not picks:
        return 0.5  # neutral when no picks — avoids 0 vs anything = 0
    final = sum(1 for p in picks if (p.get("category") or "").lower() == "final")
    return final / len(picks)


def score_beauty_picks(picks: list[dict], truth: list[dict]) -> dict:
    """Score predicted picks against editor truth.

    Both args are lists of dicts with at least {clip_id, t, category}.
    Returns {clip_overlap, time_match, category_balance, composite,
             matched_picks, total_picks}.
    """
    if not picks:
        return {
            "clip_overlap": 0.0,
            "time_match": 0.0,
            "category_balance": 0.0,
            "composite": 0.0,
            "matched_picks": 0,
            "total_picks": 0,
        }

    truth_clips: set[str] = {str(t["clip_id"]) for t in truth if t.get("clip_id")}
    # Group truth spans by clip_id. The editor used each beauty beat over a
    # source-time SPAN (t_in → t_out). A pick anywhere inside the span (or
    # within ±TIME_TOLERANCE_S of either edge) is a match. Older truth files
    # without t_out fall back to point-match against `t`.
    truth_spans_by_clip: dict[str, list[tuple[float, float]]] = {}
    for t in truth:
        cid = str(t.get("clip_id") or "")
        if not cid:
            continue
        t_in = float(t.get("t_in") if t.get("t_in") is not None else (t.get("t") or 0.0))
        t_out = t.get("t_out")
        t_out = float(t_out) if t_out is not None else t_in  # fallback: point
        truth_spans_by_clip.setdefault(cid, []).append((t_in, t_out))

    # clip_overlap
    n_overlap = sum(1 for p in picks if str(p.get("clip_id") or "") in truth_clips)
    clip_overlap = n_overlap / len(picks)

    # time_match: pick is "matched" if its source-time falls within
    # [t_in - tol, t_out + tol] of any truth span on the SAME clip_id. Picks
    # on clips the editor didn't use can't time-match by definition.
    n_time_match = 0
    for p in picks:
        cid = str(p.get("clip_id") or "")
        pt = float(p.get("t") or 0.0)
        for (t_in, t_out) in truth_spans_by_clip.get(cid, []):
            if (t_in - TIME_TOLERANCE_S) <= pt <= (t_out + TIME_TOLERANCE_S):
                n_time_match += 1
                break
    time_match = n_time_match / len(picks)

    # category_balance — tolerance for ratio drift
    pick_final = _final_ratio(picks)
    truth_final = _final_ratio(truth) if truth else 0.5
    category_balance = max(0.0, 1.0 - abs(pick_final - truth_final))

    composite = 0.5 * clip_overlap + 0.4 * time_match + 0.1 * category_balance

    return {
        "clip_overlap": round(clip_overlap, 4),
        "time_match": round(time_match, 4),
        "category_balance": round(category_balance, 4),
        "composite": round(composite, 4),
        "matched_picks": n_time_match,
        "total_picks": len(picks),
        "truth_picks": len(truth),
    }


def score_corpus(per_recipe: dict[str, dict]) -> dict:
    """Aggregate per-recipe scores into a corpus-level result.

    per_recipe = {recipe_slug: score_dict_from_score_beauty_picks}
    """
    if not per_recipe:
        return {"composite": 0.0, "n_recipes": 0}
    composites = [r["composite"] for r in per_recipe.values()]
    return {
        "composite": round(sum(composites) / len(composites), 4),
        "n_recipes": len(per_recipe),
        "min": round(min(composites), 4),
        "max": round(max(composites), 4),
        "per_recipe": {r: per_recipe[r]["composite"] for r in per_recipe},
    }
