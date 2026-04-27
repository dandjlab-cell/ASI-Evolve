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
| 1.29–2.50s | V1 |  | — |  |  |
| 2.50–3.84s | V1 |  | — |  |  |
| 3.84–4.92s | V1 |  | — |  |  |
| 3.84–51.72s | V8 |  | — |  |  |
| 3.84–6.21s | V9 |  | Text (Kosher salt) |  |  |
| 4.92–6.21s | V1 |  | — |  |  |
| 6.21–8.22s | V1 |  | — |  |  |
| 6.21–8.22s | V9 |  | Text (Trimmed green beans) |  |  |
| 8.22–10.09s | V1 |  | — |  |  |
| 10.09–11.26s | V1 |  | — |  |  |
| 11.26–13.43s | V1 |  | — |  |  |
| 13.43–14.89s | V1 |  | — |  |  |
| 14.89–14.97s | V1 |  | — |  |  |
| 14.97–15.06s | V1 |  | — |  |  |
| 15.06–15.14s | V1 |  | — |  |  |
| 15.14–15.22s | V1 |  | — |  |  |
| 15.22–16.35s | V1 |  | — |  |  |
| 16.35–17.43s | V1 |  | — |  |  |
| 16.35–17.43s | V9 |  | Text (Unsalted butter) |  |  |
| 17.43–18.73s | V1 |  | — |  |  |
| 18.73–20.31s | V1 |  | — |  |  |
| 18.73–20.31s | V9 |  | Text (Sliced garlic) |  |  |
| 20.31–20.77s | V1 |  | — |  |  |
| 20.77–21.90s | V1 |  | — |  |  |
| 21.90–23.11s | V1 |  | — |  |  |
| 23.11–25.36s | V1 |  | — |  |  |
| 25.36–26.94s | V1 |  | — |  |  |
| 25.36–26.94s | V9 |  | Text (Minced garlic) |  |  |
| 26.94–27.94s | V1 |  | — |  |  |
| 27.94–28.90s | V1 |  | — |  |  |
| 28.90–29.24s | V1 |  | — |  |  |
| 29.24–29.32s | V1 |  | — |  |  |
| 29.32–29.40s | V1 |  | — |  |  |
| 29.40–29.49s | V1 |  | — |  |  |
| 29.49–29.57s | V1 |  | — |  |  |
| 29.57–29.65s | V1 |  | — |  |  |
| 29.65–29.90s | V1 |  | — |  |  |
| 29.90–31.78s | V1 |  | — |  |  |
| 31.78–33.87s | V1 |  | — |  |  |
| 31.78–33.87s | V9 |  | Text (Kosher salt) |  |  |
| 33.87–35.41s | V1 |  | Lumetri Color |  |  |
| 35.41–37.00s | V1 |  | Lumetri Color |  |  |
| 37.00–38.50s | V1 |  | — |  |  |
| 37.00–38.50s | V9 |  | Text (Parmesan cheese) |  |  |
| 38.50–39.16s | V1 |  | — |  |  |
| 39.16–40.42s | V1 |  | — |  |  |
| 40.42–41.92s | V1 |  | — |  |  |
| 41.92–42.83s | V1 |  | — |  |  |
| 42.83–44.29s | V1 |  | — |  |  |
| 42.83–55.76s | V6 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |
| 44.29–46.46s | V1 |  | — |  |  |
| 44.29–46.46s | V9 |  | Text (Parmesan cheese) |  |  |
| 46.46–47.84s | V1 |  | — |  |  |
| 46.46–47.84s | V9 |  | Text (Garlic chips) |  |  |
| 47.84–49.38s | V1 |  | — |  |  |
| 49.38–50.47s | V1 |  | — |  |  |
| 50.47–51.76s | V1 |  | — |  |  |
| 51.72–55.76s | V8 |  | — |  |  |
| 51.76–55.76s | V1 |  | — |  |  |

---

### FRAME_ANALYSIS

(no frame analysis found at /Users/dandj/DevApps/storyboard-gen/docs/watch-video/pass1_sauteed_green_beans*.md)

---

### EXISTING_ANNOTATION

(intentionally omitted for this run — derive editorial reasoning purely from PRPROJ_EFFECTS and FRAME_ANALYSIS)
