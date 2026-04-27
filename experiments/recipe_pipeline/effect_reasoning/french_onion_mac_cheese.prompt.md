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
| 0.88–1.84s | V1 |  | — |  |  |
| 1.84–3.34s | V1 |  | — |  |  |
| 3.34–4.63s | V1 |  | — |  |  |
| 3.34–61.73s | V3 | ADJ | Lumetri Color |  |  |
| 3.34–58.31s | V4 |  | — |  |  |
| 3.34–4.63s | V5 |  | Graphic Parameters | Olive oil |  |
| 4.63–5.88s | V2 |  | Lumetri Color, Mask2 (01), Lumetri Color, Mask2 |  | static 4-vertex mask |
| 4.63–5.88s | V5 |  | Graphic Parameters | Yellow onions |  |
| 5.88–7.13s | V1 |  | Lumetri Color |  |  |
| 5.88–7.13s | V5 |  | Graphic Parameters | Kosher salt |  |
| 7.13–8.38s | V1 |  | Lumetri Color |  |  |
| 8.38–10.18s | V2 |  | — |  |  |
| 8.38–10.18s | V5 |  | Graphic Parameters | Cook undisturbed for 5 minutes |  |
| 10.18–11.34s | V1 |  | — |  |  |
| 11.34–12.35s | V2 |  | — |  |  |
| 12.35–13.22s | V2 |  | — |  |  |
| 13.22–14.31s | V2 |  | — |  |  |
| 14.31–15.68s | V1 |  | — |  |  |
| 14.31–15.68s | V5 |  | Graphic Parameters | Panko breadcrumbs |  |
| 15.68–16.98s | V1 |  | — |  |  |
| 15.68–16.98s | V5 |  | Graphic Parameters | Melted butter |  |
| 16.98–18.52s | V1 |  | — |  |  |
| 18.52–20.31s | V2 |  | — |  |  |
| 18.52–20.31s | V5 |  | Graphic Parameters | Elbow macaroni |  |
| 20.31–22.02s | V1 |  | — |  |  |
| 22.02–23.48s | V2 |  | — |  |  |
| 22.02–23.48s | V5 |  | Graphic Parameters | Beef broth |  |
| 23.48–24.90s | V1 |  | — |  |  |
| 23.48–24.90s | V5 |  | Graphic Parameters | Dry white wine |  |
| 24.90–26.15s | V1 |  | — |  |  |
| 26.15–28.40s | V2 |  | — |  |  |
| 28.40–29.82s | V1 |  | — |  |  |
| 28.40–29.82s | V5 |  | Graphic Parameters | Unsalted butter |  |
| 29.82–31.41s | V2 |  | — |  |  |
| 29.82–31.41s | V5 |  | Graphic Parameters | All-purpose flour |  |
| 31.41–32.49s | V1 |  | — |  |  |
| 32.49–33.74s | V1 |  | — |  |  |
| 33.74–34.91s | V2 |  | — |  |  |
| 33.74–34.91s | V5 |  | Graphic Parameters | Whole milk |  |
| 34.91–36.08s | V2 |  | — |  |  |
| 36.08–37.70s | V1 |  | — |  |  |
| 36.08–37.70s | V5 |  | Graphic Parameters | Gruyère cheese |  |
| 37.70–38.83s | V1 |  | — |  |  |
| 38.83–39.75s | V1 |  | — |  |  |
| 39.75–40.50s | V1 |  | — |  |  |
| 39.75–40.50s | V5 |  | Graphic Parameters |  |  |
| 40.50–41.88s | V1 |  | — |  |  |
| 40.50–41.88s | V5 |  | Graphic Parameters | Freshly ground black pepper |  |
| 41.88–42.92s | V2 |  | — |  |  |
| 42.92–43.67s | V2 |  | — |  |  |
| 43.67–44.38s | V1 |  | — |  |  |
| 43.67–44.54s | V5 |  | Graphic Parameters | Caramelized onions |  |
| 44.38–44.46s | V1 |  | — |  |  |
| 44.38–44.54s | V2 |  | Mask2 (01), Mask2 |  | static rect-like mask |
| 44.46–44.54s | V1 |  | — |  |  |
| 44.54–45.63s | V1 |  | — |  |  |
| 45.63–46.59s | V1 |  | — |  |  |
| 46.59–47.92s | V1 |  | — |  |  |
| 46.59–47.92s | V5 |  | Graphic Parameters |  Elbow macaroni |  |
| 47.92–50.26s | V2 |  | — |  |  |
| 49.13–50.26s | V5 |  | Graphic Parameters | More caramelized onions |  |
| 50.26–51.43s | V1 |  | — |  |  |
| 50.26–51.43s | V5 |  | Graphic Parameters |  |  |
| 51.43–52.59s | V1 |  | — |  |  |
| 51.43–52.59s | V5 |  | Graphic Parameters |  |  |
| 52.59–54.89s | V2 |  | — |  |  |
| 53.09–54.89s | V5 |  | Graphic Parameters |    Bake at 475ºF until cheese is\rgolden brown, about 15 minutes |  |
| 54.89–56.18s | V1 |  | — |  |  |
| 56.18–57.43s | V1 |  | — |  |  |
| 57.43–58.31s | V2 |  | — |  |  |
| 58.31–61.73s | V1 |  | — |  |  |
| 58.31–61.73s | V4 |  | — |  |  |

---

### FRAME_ANALYSIS

(no frame analysis found at /Users/dandj/DevApps/storyboard-gen/docs/watch-video/pass1_french_onion_mac_cheese*.md)

---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
