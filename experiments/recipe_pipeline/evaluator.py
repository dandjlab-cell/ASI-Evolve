#!/usr/bin/env python3
"""
Evaluator for recipe pipeline evolution experiment.

Takes a candidate config module (Python file), loads it, and scores it
against approved edits using score.py.

Usage:
    python evaluator.py <code_file> <results_json>
"""

import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path


def load_config(code_path: str) -> dict:
    """Dynamically import a config module and return its CONFIG dict."""
    # Copy to .py temp file if needed (ASI-Evolve writes code without extension)
    code_path = str(code_path)
    if not code_path.endswith(".py"):
        import shutil
        tmp_py = code_path + ".py"
        shutil.copy2(code_path, tmp_py)
        code_path = tmp_py

    spec = importlib.util.spec_from_file_location("candidate_config", code_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "CONFIG"):
        raise ValueError("Config module must define a CONFIG dict")

    config = module.CONFIG
    _validate_config(config)
    return config


def _validate_config(config: dict):
    """Validate config constraints."""
    required_keys = [
        "text_match_prompt", "beauty_pick_prompt",
        "content_sim_weight", "bigram_weight", "chrono_weight", "step_match_weight",
        "crew_positive_bonus", "crew_redo_penalty", "last_keeper_bonus",
        "target_dur", "min_clip_duration", "max_gap_sec", "quality_threshold",
        "beauty_tail_region",
    ]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key: {key}")

    if not (2.0 <= config["target_dur"] <= 10.0):
        raise ValueError(f"target_dur must be 2.0-10.0, got {config['target_dur']}")
    if not (1.0 <= config["min_clip_duration"] <= 4.0):
        raise ValueError(f"min_clip_duration must be 1.0-4.0, got {config['min_clip_duration']}")

    for key in ["content_sim_weight", "bigram_weight", "chrono_weight", "step_match_weight"]:
        if config[key] < 0:
            raise ValueError(f"{key} must be non-negative, got {config[key]}")


def evaluate(code_path: str, results_path: str):
    """Run evaluation and write results."""
    start = time.time()
    experiment_dir = Path(__file__).parent

    try:
        config = load_config(code_path)
    except Exception as e:
        _write_error(results_path, f"Config load error: {e}", time.time() - start)
        return

    # Score against approved edits
    approved_dir = experiment_dir / "approved_edits"
    approved_files = sorted(approved_dir.glob("*.json"))

    if not approved_files:
        _write_error(results_path, "No approved edits found", time.time() - start)
        return

    # For now: score the pipeline's existing manifests against approved edits.
    # TODO: Once slim runner is built, run pipeline with evolved config here.
    cached_dir = experiment_dir / "cached_recipes"

    from score import score_all_recipes
    try:
        result = score_all_recipes(str(cached_dir), str(approved_dir))
    except Exception as e:
        _write_error(results_path, f"Scoring error: {e}\n{traceback.format_exc()}", time.time() - start)
        return

    elapsed = time.time() - start

    output = {
        "success": True,
        "eval_score": result["train_score"],
        "composite": result["train_score"],
        "train_count": result["train_count"],
        "per_recipe": result["per_recipe"],
        "eval_time": round(elapsed, 2),
        "complexity": len(json.dumps(config)),
        "temp": {
            "config_keys": list(config.keys()),
        },
    }

    if "holdout_score" in result:
        output["holdout_score"] = result["holdout_score"]

    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)


def _write_error(results_path: str, error: str, elapsed: float):
    output = {
        "success": False,
        "eval_score": 0.0,
        "composite": 0.0,
        "eval_time": round(elapsed, 2),
        "complexity": 0,
        "temp": {"error": error},
    }
    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <code_file> <results_json>")
        sys.exit(1)
    evaluate(sys.argv[1], sys.argv[2])
