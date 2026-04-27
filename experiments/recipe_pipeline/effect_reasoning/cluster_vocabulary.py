#!/usr/bin/env python3
"""
cluster_vocabulary.py — Take all 17 OBSERVATIONS sections from the
effect-reasoning corpus and ask Opus to cluster the recurring editorial
intents into a vocabulary that the manifest schema can encode.

Output:
  /Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Editorial Intents Vocabulary v1.md
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ANNOTATIONS_DIR = Path("/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Annotations")
OUTPUT_PATH = Path("/Users/dandj/DevApps/Brain/Projects/ASI-Evolve/Editorial Intents Vocabulary v1.md")


def extract_observations(md_text: str) -> str:
    """Pull the OBSERVATIONS section (case-insensitive, ## or ### header)."""
    m = re.search(r"^#{2,3}\s+OBSERVATIONS\s*$(.+?)(?=^#|\Z)",
                  md_text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def load_corpus_observations() -> dict[str, str]:
    out: dict[str, str] = {}
    for fp in sorted(ANNOTATIONS_DIR.glob("* — Effect Reasoning (image mode).md")):
        recipe = fp.stem.split(" — ")[0]
        if recipe == "steak_taco":
            continue  # legacy duplicate of steak_tacos
        obs = extract_observations(fp.read_text())
        if obs:
            out[recipe] = obs
    return out


PROMPT = """**This is an analysis task — return the vocabulary directly as your response. Do NOT use plan mode, do NOT write to a plan file, do NOT ask for approval. Just output the markdown vocabulary doc.**

You're synthesizing an editorial-intent vocabulary from observations made on 17 of Dan's recipe edits.

## Goal

Produce a small (10-20 entries) vocabulary of recurring **editorial intents**. Each intent is a NAMED reusable decision that Dan's edits make over and over. The vocabulary is the input to a manifest schema — when the agent generates a future recipe edit, it will read intent tags and translate them into the right effects/cuts/grades.

## Method

1. Read ALL 17 sets of OBSERVATIONS below.
2. Find patterns that recur in **2 or more** recipes. Single-recipe quirks don't make the cut (note them as "candidates" only).
3. For each recurring pattern, write a vocabulary entry with:
   - **Name** (short, evocative — e.g. `phrase-binding-adj-transform` or `hands-absent-breath`)
   - **Definition** (1-2 sentences — what the intent IS, in editorial language)
   - **Realization** (1-2 sentences — what effects/cuts/timings encode it in Premiere)
   - **Recipes where it appears** (slug list, with one-phrase context per recipe)
   - **Counter-examples / when NOT to use** (if visible from observations — e.g. "absent in puppy_chow because…")
4. Group entries into ~5-7 categories. **Stop-Motion MUST be its own dedicated category** (not merged with Composition) — it's a distinctive Dan signature that deserves separate vocabulary entries for its sub-modes (no-hands appearance, micro-cut compilation, ingredient-stacking sequences, etc.). **Speed Ramp / Time Manipulation MUST also have entries** (look for `speed_ramp`, `playback_speed`, RAMP markers, or any mention of slow-mo / speed change / time remapping in the OBSERVATIONS).

## Quality bar

- **Specific, not vague.** Bad: "uses zooms." Good: "single animated Position+Scale on an adjustment layer that spans 2-4 consecutive same-angle ingredient beats, drifting/pushing slowly across the cuts."
- **Recipe-cited.** Every entry must list the recipes where it was observed.
- **Realization-grounded.** Each entry must say what the manifest writer would emit (e.g. "Transform on V3 adj-layer; animated Position keyframes from [0.5,0.5] to [0.5,0.55±0.05]; duration spanning N consecutive cuts").
- **No editorial commentary.** This is a reference doc, not analysis prose.

## Output format

```markdown
# Editorial Intents Vocabulary v1

## Category: {name}

### `intent-slug-name`

**Definition:** {1-2 sentences}

**Realization:** {what to emit in the prproj — effect type, track, params, timing}

**Recipes:** `recipe_a` (one-phrase context); `recipe_b` (one-phrase context); …

**Counter-examples / when not:** {if visible}

---
```

End with a **Vocabulary Coverage Audit** section listing:
- Patterns that appeared in only 1 recipe (candidates for next iteration)
- Observations that don't fit any vocabulary entry yet (gaps to investigate)

## Inputs follow

{observations_block}
"""


def call_claude(prompt: str, model: str = "claude-opus-4-7") -> str:
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    cmd = ["claude", "-p", "--output-format", "json",
           "--strict-mcp-config", "--model", model,
           "--permission-mode", "acceptEdits"]
    print(f"  Calling claude CLI ({model}, prompt={len(prompt)} chars)...", file=sys.stderr)
    result = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                            cwd="/tmp", env=env, timeout=900)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:500]}", file=sys.stderr)
        return ""
    try:
        return json.loads(result.stdout).get("result", "")
    except json.JSONDecodeError:
        return result.stdout


def main():
    obs = load_corpus_observations()
    print(f"Loaded {len(obs)} recipe OBSERVATIONS sections")
    if not obs:
        print("ERROR: no observations found", file=sys.stderr); sys.exit(1)

    block = ""
    for recipe, body in obs.items():
        block += f"\n\n### {recipe}\n\n{body}\n"

    prompt = PROMPT.replace("{observations_block}", block)
    print(f"Prompt size: {len(prompt)} chars")

    workdir = Path(__file__).parent
    (workdir / "vocabulary.prompt.md").write_text(prompt)

    if "--dry-run" in sys.argv:
        print("--dry-run; skipping Claude call")
        return

    response = call_claude(prompt)
    if not response:
        sys.exit(2)

    header = ("---\n"
              "project: ASI-Evolve\n"
              "type: working-file\n"
              "source: \"vocabulary clustering Opus pass over 17 recipe OBSERVATIONS\"\n"
              "date: 2026-04-26\n"
              "status: draft\n"
              "tags: [pipeline, editorial-vocabulary, asi-evolve, manifest-schema-input]\n"
              "---\n\n")
    OUTPUT_PATH.write_text(header + response)
    print(f"Wrote vocabulary to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
