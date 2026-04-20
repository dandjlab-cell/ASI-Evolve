# Task: Optimize Recipe Video Edit Pipeline

You are evolving a configuration module for a recipe video editing pipeline.
The pipeline takes cooking footage from two cameras (front + overhead) and
produces an edit timeline that matches clips to editorial beats.

Your config controls:
1. LLM prompts that assign clips to beats and select hero shots
2. Scoring weights for camera pairing (V1/V2)
3. Audio quality modifiers (crew speech signals)
4. Timing constants (target duration, min clip length, max gap)

The eval function runs your config against finished recipes and scores how
closely the pipeline's output matches the editor's approved edit.

Higher score = the pipeline made better editorial decisions.

## What makes a good recipe edit:
- Right clips for the action described (precision)
- Don't miss important moments the editor kept (recall)
- In-points should land on the start of action, not the aftermath
- Camera choice: overhead for plating/pouring, front for technique/hands
- Beauty shots should capture the finished dish at its most appealing
- Duration should match the complexity of the action

## Config structure:
Your output must be a valid Python file defining a CONFIG dict with these keys:

```python
CONFIG = {
    # Prompt templates
    "text_match_prompt": "...",
    "beauty_pick_prompt": "...",

    # V1/V2 pairing weights (positive floats)
    "content_sim_weight": 0.4,
    "bigram_weight": 0.6,
    "chrono_weight": 0.3,
    "step_match_weight": 0.25,

    # Audio quality modifiers
    "crew_positive_bonus": 0.3,
    "crew_redo_penalty": -0.4,
    "last_keeper_bonus": 0.5,

    # Timing (target_dur: 2.0-10.0, min_clip: 1.0-4.0)
    "target_dur": 5.0,
    "min_clip_duration": 2.0,
    "max_gap_sec": 12.0,
    "quality_threshold": 4,

    # Beauty trigger
    "beauty_tail_region": 0.80,
}
```

## Constraints:
- Prompts must remain general (no recipe-specific clip references)
- Weights must be positive floats
- target_dur must be between 2.0 and 10.0
- min_clip_duration must be between 1.0 and 4.0
