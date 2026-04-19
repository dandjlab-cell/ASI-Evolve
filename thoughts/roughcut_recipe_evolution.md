# RoughCut Recipe Pipeline Evolution — Design Sketch

## What Gets Evolved

The "code" ASI-Evolve generates is a **config module** — a Python file containing:

1. **LLM prompt templates** for text_match, beauty_pick, and beat_generation
2. **Scoring weights** for V1/V2 pairing, audio quality, beauty scoring
3. **Timing constants** (target_dur, min_clip, max_gap, etc.)

```python
# Example evolved artifact — this is what ASI-Evolve mutates each generation
CONFIG = {
    # --- Prompt templates (the big levers) ---
    "text_match_prompt": """You are assigning clips to beats for a recipe video.
    Prefer clips where the action is clearly visible and centered.
    When two clips show the same step, prefer the tighter framing.
    {context}""",

    "beauty_pick_prompt": """Select the best hero shots for a recipe finale.
    Prioritize: steam/motion > static plating > wide shots.
    {context}""",

    # --- V1/V2 pairing weights ---
    "content_sim_weight": 0.4,      # unigram Jaccard contribution
    "bigram_weight": 0.6,           # bigram Jaccard contribution
    "chrono_weight": 0.3,           # temporal proximity bonus
    "step_match_weight": 0.25,      # same-step bonus

    # --- Audio quality modifiers ---
    "crew_positive_bonus": 0.3,
    "crew_redo_penalty": -0.4,
    "last_keeper_bonus": 0.5,

    # --- Timing ---
    "target_dur": 5.0,
    "min_clip_duration": 2.0,
    "max_gap_sec": 12.0,
    "quality_threshold": 4,

    # --- Beauty trigger ---
    "beauty_tail_region": 0.80,     # last N% of shoot opens tail
}
```

Each generation, ASI-Evolve's Researcher mutates this config — changes prompt wording, adjusts weights, shifts thresholds. The Analyzer learns which changes helped ("increasing chrono_weight improved camera pairing on 4/6 recipes").

## What Gets Cached (Run Once)

These stages are expensive but deterministic. Run once per recipe, cache forever:

```
Per recipe (cached in roughcut-ai/projects/{recipe}/):
├── scan.json              — VLM frame descriptions (DINO + Qwen)
├── paired_scan.json       — Fused dual-camera descriptions
├── audio_sync.json        — V1/V2 temporal alignment
├── audio_cues.json        — Whisper transcripts + crew signals
├── shot_catalog.json      — Rule-based candidates
├── media_index.json       — File durations, resolutions
└── clip_narratives.json   — Deduplicated frame descriptions per clip
```

Total cache per recipe: ~5-15MB. One-time cost: ~30 min per recipe.

## What Runs Per Generation (The Eval Loop)

The eval script loads cached data, applies the evolved config, runs only the decision stages:

```
For each recipe in training set:
  1. Load cached scan, audio, shot_catalog, clip_narratives
  2. Generate beats (LLM call with evolved prompt)         ~30s
  3. Run text_match (LLM call with evolved prompt)         ~60s
  4. Run beauty_pick (LLM call with evolved prompt)        ~30s
  5. Run V1/V2 pairing (evolved weights, no LLM)           ~1s
  6. Build manifest (assembly logic, evolved timing)        ~1s
  7. Diff manifest against Dan's approved XML               ~1s
  8. Score the diff                                        ~1s
                                                    Total: ~2 min/recipe
```

With 6 recipes: ~12 min per generation.
With 20 generations: ~4 hours total.

Compare to re-running the full pipeline: 6 recipes x 45 min x 20 generations = 90 hours.

## The Scoring Function

`eval.sh` runs the pipeline subset, then scores against approved edits:

```python
def score_generation(manifests, approved_xmls):
    """Score across all recipes. Returns 0-100."""
    scores = []
    for manifest, xml in zip(manifests, approved_xmls):
        diff = manifest_diff(manifest, xml)

        # Precision: what % of proposed clips did Dan keep?
        precision = diff.clips_kept / diff.clips_proposed

        # Recall: what % of Dan's final clips were in the manifest?
        recall = diff.clips_kept / diff.clips_in_final

        # Timing accuracy: avg error in seconds for kept clips
        timing = 1.0 - min(diff.avg_inpoint_error / 5.0, 1.0)

        # Camera match: right V1/V2 pairing rate
        camera = diff.camera_matches / diff.total_paired

        # Weighted composite
        score = (
            precision * 35 +
            recall * 30 +
            timing * 20 +
            camera * 15
        )
        scores.append(score)

    # Average across recipes — prevents overfitting to one
    return sum(scores) / len(scores)
```

**Overfitting prevention:**
- Score is averaged across ALL recipes, not per-recipe
- Hold out 1-2 recipes as validation (never used for scoring)
- Prompt mutations are general ("prefer tighter framing") not specific ("for Chicken Thighs use clip AI2I4672")

## ASI-Evolve Experiment Structure

```
experiments/recipe_pipeline/
├── config.yaml              — ASI-Evolve config (opus, 20 steps, etc.)
├── input.md                 — Task description for the Researcher
├── initial_program           — Starting config (current pipeline defaults)
├── eval.sh                  — Runs pipeline subset + scoring
├── prompts/
│   ├── researcher.jinja2    — "Evolve the recipe pipeline config"
│   └── analyzer.jinja2      — "What editorial patterns improved?"
├── cached_recipes/
│   ├── chicken_thighs/      — Cached scan, audio, narratives
│   ├── melting_sweet_potatoes/
│   ├── crispy_rice/
│   ├── sheet_pan_salmon/
│   ├── one_pot_pasta/
│   └── lemon_bars/
├── approved_edits/
│   ├── chicken_thighs.xml   — Dan's final Premiere XML
│   ├── melting_sweet_potatoes.xml
│   └── ... (one per recipe)
└── holdout/
    ├── banana_bread/         — Never scored, used for validation
    └── banana_bread.xml
```

## input.md (Task Description for the Researcher)

```markdown
# Task: Optimize Recipe Video Edit Pipeline

You are evolving a configuration module for a recipe video editing pipeline.
The pipeline takes cooking footage (two cameras) and produces an edit timeline.

Your config controls:
1. LLM prompts that assign clips to beats and select hero shots
2. Scoring weights for camera pairing
3. Audio quality modifiers
4. Timing constants

The eval function runs your config against 6 finished recipes and scores
how closely the pipeline's output matches the editor's approved edit.

Higher score = the pipeline made better editorial decisions.

## What makes a good recipe edit:
- Right clips for the action described (precision)
- Don't miss important moments (recall)
- In-points should land on the start of action, not the aftermath
- Camera choice: overhead for plating/pouring, front for technique/hands
- Beauty shots should capture the finished dish at its most appealing
- Duration should match the complexity of the action (simple = short, complex = longer)

## Constraints:
- Prompts must remain general — no recipe-specific references
- Weights must be positive floats
- target_dur must be between 2.0 and 10.0
- min_clip_duration must be between 1.0 and 4.0
```

## What the Researcher Evolves

Each generation, the Researcher sees:
- The current best config (from parent node)
- Analyzer lessons from previous runs ("increasing bigram_weight to 0.7 improved camera pairing but hurt timing accuracy")
- Cognition items (accumulated knowledge across all generations)

It produces a mutated config. Typical mutations:
- Rephrase a prompt section ("prefer the tighter framing" → "choose the camera angle that fills more of the frame with the cooking action")
- Shift a weight (chrono_weight 0.3 → 0.4)
- Adjust timing (target_dur 5.0 → 4.5)

## What the Analyzer Learns

After each generation is scored, the Analyzer sees:
- The config that was used
- Per-recipe scores (precision, recall, timing, camera)
- The diff details (which clips were wrong, what Dan changed)

It produces lessons like:
- "Reducing target_dur from 5.0 to 4.2 improved precision by 8% — the pipeline was proposing clips that were too long, and Dan was trimming them"
- "Adding 'prefer overhead for ingredient additions' to text_match_prompt improved camera matching on 4/6 recipes"
- "Increasing crew_positive_bonus to 0.5 had no measurable effect — audio cues are a weak signal for recipe content"

These lessons feed into the cognition base and inform future Researcher mutations.

## Implementation Steps

### Phase 1: Cache Infrastructure
1. Identify 6-8 finished recipes where we have (or can re-generate) pipeline cache
2. Export Dan's final Premiere XMLs for each
3. Build the cache extraction script (pulls scan, audio, narratives from existing pipeline artifacts)

### Phase 2: Slim Pipeline Runner
4. Extract the decision stages from build_editlist.py into a standalone runner
5. Runner takes: cached data + config module → manifest.json
6. This is the "code" ASI-Evolve's Engineer runs

### Phase 3: Scoring
7. Extend manifest_diff to output numeric scores (precision, recall, timing, camera)
8. Build eval.sh: loops recipes, runs slim pipeline, diffs, averages scores

### Phase 4: Wire to ASI-Evolve
9. Create the experiment directory structure
10. Write researcher/analyzer prompts
11. Set initial_program to current pipeline defaults
12. Run first evolution (5-10 steps to validate the loop)

### Phase 5: Scale
13. Expand to 20+ generations
14. Validate against holdout recipes
15. Apply winning config back to production pipeline
