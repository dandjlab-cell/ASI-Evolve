# Effect Reasoning Prompt — Recipe Edit Analysis

You are analyzing a Premiere Pro edit of a Kitchn recipe video that Dan de Jesus cut. Your job is to reason about *why* he made each editorial decision — not to assign decisions to a pre-existing taxonomy. We want your fresh observations so we can later cluster recurring intents into vocabulary.

## What you have

Three inputs, in this order:

1. **`PRPROJ_EFFECTS`** — a compact list of every editorial event in the timeline: cuts (clip in/out per track), adjustment-layer effects (Transform, Lumetri, Mirror, Replicate, Mask), per-clip Lumetri grades, MOGRT text overlays, masks, and stacked-adjustment-layer composites. Times are in timeline seconds.

2. **`FRAME_ANALYSIS`** — a per-frame visual description of the rendered video at 2fps. Each row tells you which camera angle is on screen (FRONT, OVERHEAD, etc.), what's happening (subject, action, hands, ingredients), and any overlay text.

3. **`EXISTING_ANNOTATION`** — Dan-validated editorial reasoning that's already been done on this recipe at the cut/beat/rhythm level. Treat this as ground truth for the structural analysis. Your job adds the *why-this-effect-here* layer.

## What we want from you

For each meaningful editorial choice in the edit — every cut, every effect, every angle change — explain what's happening and offer a hypothesis about why Dan might have made that choice. Pay specific attention to:

- **Where cuts land relative to the action.** Does the cut come on a beat (visible action peak), before the action (anticipation), after (reaction), or in the middle (compression)?
- **Why one angle transitions to another.** What does FRONT show that OVERHEAD doesn't? When Dan moves OVERHEAD → FRONT or vice versa, what's the editorial reason?
- **Each effect's contribution.** A Transform punch-in adds what the underlying clip lacks — what specifically? A Lumetri grade does what to the mood? A Mirror+Replicate kaleidoscope marks what kind of moment?
- **Stacked composites.** When two or more adjustment layers overlap (e.g., a Zoom Transform on V5 atop a Mirror+Replicate on V3), what makes that combination the right answer rather than either effect alone?
- **Hand-presence vs hand-absence.** When the frame analysis says "no hands in frame" or describes the ingredient/object simply *appearing* (vs. a hand pouring/dropping/manipulating), that's a deliberate **stop-motion / found-object** beat with a different vibe than a hand-action shot. Pairs of consecutive overhead beats where one shows action and the next shows no hands are common — call this out specifically; it is one of Dan's signature mood shifts.
- **Absence of an adjustment-layer effect ≠ static / locked-off.** Before describing a section as "still" or "static-feeling" because no Transform/effect is applied, READ THE FRAME ANALYSIS for in-shot action (steak flipping, sizzling, hand entering frame, smoke rising, motion blur, etc.). If the underlying shot is already kinetic — the cooking sizzle, a hand placing a hero, a slicing motion — that's why no effect was needed. The shot is doing the motion work. Only call something static when the frames themselves describe a held/locked composition with minimal change.
- **What the alternative would have been.** If Dan hadn't done this — straight cut instead of zoom, FRONT instead of OVERHEAD, no kaleidoscope — what would have been lost?

## What we don't want

- **Don't assign tags from a fixed vocabulary.** No "energy bump" / "sectional emphasis" labels. Use natural language — explain in your own words what's happening editorially.
- **Don't moralize or grade the edit.** No "this is a great cut" / "this could be tighter." We want analysis, not critique.
- **Don't restate the structural analysis from EXISTING_ANNOTATION.** That layer is done. Add the effect-and-angle layer on top.
- **Don't speculate about ingredients or recipe content.** Stay editorial.

## Output format

**Be terse.** Bullets, not paragraphs. No flowing analysis prose. Reader should be able to scan a section in 5 seconds. Cut every "this is interesting because" / "notably" / "what's happening here is" — just state the thing.

Markdown. Walk the edit roughly in timeline order. Group observations by editorial moment (a cluster of cuts/effects that belong together — e.g., "marinade build" or "onion-toss accent"). For each moment, use this exact structure — one short bullet per field, no paragraphs:

```
### {timeline range} — {short descriptive title}

- **Screen:** {one short line — angle + key action; flag "no hands" / stop-motion appearance if relevant}
- **Cuts/angles:** {one line on cut count, angle sequence, rhythm}
- **Effects:** {what's active, with key params}
- **Why:** {one short bullet — the editorial logic, not flowing prose}
- **Without:** {what the alternative would lose, in 1–2 short clauses}
```

If a section is uneventful, collapse it to one or two bullets — don't pad.

End with an **OBSERVATIONS** section — 5–10 bullet points listing patterns that recur or seem like Dan's signatures. Each bullet 1–2 sentences max. These will be the input to vocabulary-clustering across recipes, so be specific (not "uses zooms" but "uses slow Position+Scale on adjustment layers over multi-clip ingredient-dump sections to add motion energy without recutting").

## Inputs follow

---

### PRPROJ_EFFECTS

**Timeline (cuts + effects + masks + MOGRT text, ordered by in-time):**

| Timeline | Track | Adj | Effects | Text overlay | Mask |
|---|---|---|---|---|---|
| 1.63–3.34s | V1 |  | — |  |  |
| 3.34–4.55s | V1 |  | — |  |  |
| 3.34–50.84s | V7 |  | — |  |  |
| 3.34–4.55s | V8 |  | Text (Lobster tail) |  |  |
| 4.55–4.80s | V2 |  | — |  |  |
| 4.80–4.88s | V2 |  | — |  |  |
| 4.88–4.96s | V2 |  | — |  |  |
| 4.96–5.38s | V2 |  | — |  |  |
| 5.38–6.76s | V1 |  | — |  |  |
| 5.38–9.30s | V8 |  | Graphic Parameters | Cut top shell lengthwise,\rstopping at the tail |  |
| 6.76–9.30s | V2 |  | — |  |  |
| 9.30–11.14s | V1 |  | — |  |  |
| 9.30–11.14s | V8 |  | Graphic Parameters | Gently pry the meat away |  |
| 11.14–12.97s | V1 |  | — |  |  |
| 11.14–12.97s | V8 |  | Graphic Parameters |  Cut the tail meat in half |  |
| 12.97–16.89s | V1 |  | — |  |  |
| 12.97–14.89s | V8 |  | Graphic Parameters | Open the tail up like a book |  |
| 16.89–18.77s | V1 |  | — |  |  |
| 16.89–18.77s | V8 |  | Graphic Parameters | Press down to flatten slightly |  |
| 18.77–19.77s | V1 |  | — |  |  |
| 19.77–21.40s | V2 |  | — |  |  |
| 19.77–21.40s | V8 |  | Text (Water) |  |  |
| 21.40–22.73s | V1 |  | — |  |  |
| 22.73–23.73s | V1 |  | — |  |  |
| 23.73–24.07s | V2 |  | — |  |  |
| 24.07–24.15s | V2 |  | — |  |  |
| 24.07–24.15s | V3 |  | Mask2 (02) [animated: Path, Position, Anchor Point] |  | static 8-vertex mask |
| 24.15–24.23s | V2 |  | — |  |  |
| 24.23–24.65s | V2 |  | — |  |  |
| 24.65–25.40s | V2 |  | — |  |  |
| 25.40–28.28s | V1 |  | — |  |  |
| 26.15–28.28s | V8 |  | Graphic Parameters | Bake at 425ºF until cooked\rthrough, 20 to 27 minutes |  |
| 28.28–30.28s | V2 |  | — |  |  |
| 28.28–30.28s | V8 |  | Text (Unsalted butter) |  |  |
| 30.28–31.66s | V1 |  | — |  |  |
| 30.28–31.66s | V8 |  | Text (Garlic) |  |  |
| 31.66–32.78s | V1 |  | — |  |  |
| 32.78–33.62s | V2 |  | — |  |  |
| 33.62–35.03s | V1 |  | — |  |  |
| 33.62–35.03s | V8 |  | Text (Fresh parsley) |  |  |
| 35.03–36.16s | V1 |  | — |  |  |
| 36.16–37.50s | V1 |  | — |  |  |
| 36.16–37.50s | V8 |  | Text (Lemon juice) |  |  |
| 37.50–38.83s | V1 |  | — |  |  |
| 37.50–38.83s | V8 |  | Text (Kosher salt) |  |  |
| 38.83–40.12s | V2 |  | — |  |  |
| 40.12–41.50s | V1 |  | — |  |  |
| 41.50–43.25s | V1 |  | — |  |  |
| 43.25–44.92s | V2 |  | — |  |  |
| 44.92–45.96s | V1 |  | — |  |  |
| 45.96–47.34s | V1 |  | — |  |  |
| 47.34–48.55s | V1 |  | — |  |  |
| 48.55–50.84s | V2 |  | — |  |  |
| 50.84–54.64s | V1 |  | — |  |  |
| 50.84–54.64s | V7 |  | — |  |  |
| 369.49–371.75s | V1 |  | — |  |  |
| 371.75–375.71s | V1 |  | — |  |  |
| 375.71–382.92s | V1 |  | — |  |  |
| 397.02–399.94s | V1 |  | — |  |  |
| 443.11–445.24s | V1 |  | — |  |  |
| 445.24–447.32s | V1 |  | — |  |  |
| 447.32–448.61s | V1 |  | — |  |  |
| 452.29–454.45s | V1 |  | — |  |  |
| 454.45–458.37s | V1 |  | — |  |  |
| 461.88–464.67s | V1 |  | — |  |  |
| 469.43–480.23s | V1 |  | — |  |  |
| 527.99–530.28s | V1 |  | — |  |  |
| 530.28–534.62s | V1 |  | — |  |  |
| 673.01–675.59s | V1 |  | — |  |  |
| 675.59–679.22s | V1 |  | — |  |  |
| 736.32–775.11s | V1 |  | — |  |  |

---

### FRAME_ANALYSIS

(no frame analysis found at /Users/dandj/DevApps/storyboard-gen/docs/watch-video/pass1_baked_lobster_tails*.md)

---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
