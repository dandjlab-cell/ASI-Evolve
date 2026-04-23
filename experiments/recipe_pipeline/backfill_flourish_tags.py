#!/usr/bin/env python3
"""
Backfill [flourish: organic|functional] verdict tags onto existing annotation
JSONs. Only touches beats whose `effects` string contains a speed ramp; for each,
if no tag is already present in `effects_reasoning`, calls Claude CLI once with
a short classification prompt and appends the tag.

Preserves all other beat data unchanged. Saves back to the same JSON path.

Run:
    python backfill_flourish_tags.py --dir annotations/
    python backfill_flourish_tags.py annotations/sweet_potato_pie.json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


TAG_RE = re.compile(r"\[flourish:\s*(organic|functional)\s*\]", re.IGNORECASE)

CLASSIFY_PROMPT = """You are classifying a speed-ramp decision in a recipe video edit.

Rule: An **organic flourish** is a speed ramp applied to an unattended transformation — butter melting, sauce pooling, steam rising, chocolate dripping, liquid spreading. The camera catches something changing on its own and slows or stretches that moment to savor it.

A **functional** speed ramp is a timing tool — a 1-3% nudge to hit a musical beat, a stretch to fit a phrase, or any ramp applied to an attended human-driven action (hands pouring, stirring, pressing, cutting).

Beat description: {description}
Effects applied: {effects}
Editor's reasoning: {reasoning}

Answer with exactly one token on one line: either `[flourish: organic]` or `[flourish: functional]`. No other text.
"""


def has_speed_ramp(beat: dict) -> bool:
    fx = str(beat.get("effects", beat.get("effects_info", ""))).lower()
    return "speed" in fx or "ramp" in fx


def already_tagged(reasoning: str) -> bool:
    return bool(TAG_RE.search(reasoning or ""))


def call_claude(prompt: str, model: str = "opus") -> str:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--model", model,
    ]
    result = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True,
        env=env, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed: {result.stderr[:300]}")
    data = json.loads(result.stdout)
    # Claude CLI wraps the response; grab the assistant's text
    if isinstance(data, dict):
        return data.get("result", data.get("response", "")) or ""
    return str(data)


def classify(beat: dict, model: str = "opus") -> str:
    """Return 'organic' or 'functional' for one beat's speed ramp."""
    prompt = CLASSIFY_PROMPT.format(
        description=beat.get("beat_description", "")[:300],
        effects=str(beat.get("effects", ""))[:300],
        reasoning=str(beat.get("effects_reasoning", ""))[:500],
    )
    response = call_claude(prompt, model=model)
    m = TAG_RE.search(response)
    if not m:
        # Try to extract from unstructured response as last resort
        if "organic" in response.lower() and "functional" not in response.lower():
            return "organic"
        if "functional" in response.lower() and "organic" not in response.lower():
            return "functional"
        raise ValueError(f"Could not parse verdict from response: {response[:200]}")
    return m.group(1).lower()


def process_file(path: Path, model: str = "opus") -> dict:
    """Backfill tags on one annotation JSON. Returns summary dict."""
    data = json.loads(path.read_text())
    beats = data.get("beats", [])
    added = 0
    skipped = 0
    tagged_details = []

    for beat in beats:
        if not has_speed_ramp(beat):
            continue
        reasoning = beat.get("effects_reasoning", "") or ""
        if already_tagged(reasoning):
            skipped += 1
            continue

        verdict = classify(beat, model=model)
        # Append the tag — keep on the same line so the existing reasoning flows.
        tag = f"[flourish: {verdict}]"
        new_reasoning = reasoning.rstrip()
        if new_reasoning and not new_reasoning.endswith((".", "!", "?")):
            new_reasoning += "."
        new_reasoning = f"{new_reasoning} {tag}".strip()
        beat["effects_reasoning"] = new_reasoning

        added += 1
        tagged_details.append({
            "beat_index": beat.get("beat_index"),
            "verdict": verdict,
            "effects": str(beat.get("effects", ""))[:80],
        })
        print(f"  Beat {beat.get('beat_index'):2} → [flourish: {verdict}]  ({beat.get('beat_description', '')[:60]})")

    path.write_text(json.dumps(data, indent=2))
    return {"recipe": data.get("recipe", path.stem), "added": added, "skipped": skipped, "details": tagged_details}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", help="Path to single annotation JSON")
    ap.add_argument("--dir", help="Process all *.json in directory")
    ap.add_argument("--model", default="opus")
    args = ap.parse_args()

    if args.dir:
        jsons = sorted(Path(args.dir).glob("*.json"))
    elif args.input:
        jsons = [Path(args.input)]
    else:
        ap.print_help()
        sys.exit(1)

    summary = []
    for p in jsons:
        print(f"\n=== {p.name} ===")
        result = process_file(p, model=args.model)
        summary.append(result)
        print(f"  added={result['added']}  skipped={result['skipped']}")

    print(f"\n--- Summary ---")
    total_added = sum(r["added"] for r in summary)
    total_skipped = sum(r["skipped"] for r in summary)
    print(f"Tags added: {total_added}   Already tagged (skipped): {total_skipped}")


if __name__ == "__main__":
    main()
