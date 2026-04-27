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

**Timeline (cuts + effects + masks + MOGRT text + speed, ordered by in-time):**

| Timeline | Track | Adj | Effects | Text overlay | Mask | Speed |
|---|---|---|---|---|---|---|
| 1.21–2.54s | V1 |  | — |  |  |  |
| 2.54–4.21s | V1 |  | — |  |  |  |
| 4.21–6.01s | V1 |  | — |  |  |  |
| 4.21–45.55s | V8 |  | — |  |  |  |
| 4.21–6.01s | V9 |  | Text (Rice Chex cereal) |  |  |  |
| 6.01–11.01s | V2 |  | — |  |  |  |
| 6.42–7.55s | V9 |  | Text (Unsalted butter) |  |  |  |
| 7.55–8.80s | V9 |  | Text (Semisweet chocolate chips) |  |  |  |
| 8.80–9.97s | V9 |  | Text (Smooth peanut butter) |  |  |  |
| 9.97–11.01s | V9 |  | Text (Kosher salt) |  |  |  |
| 11.01–11.97s | V1 |  | — |  |  |  |
| 11.97–12.76s | V1 |  | — |  |  |  |
| 11.97–15.43s | V10 |  | Graphic Parameters | Microwave until almost melted,\rabout 2 minutes |  |  |
| 12.76–13.89s | V1 |  | — |  |  |  |
| 13.89–15.43s | V2 |  | — |  |  |  |
| 15.43–16.89s | V1 |  | — |  |  |  |
| 16.89–17.81s | V1 |  | — |  |  |  |
| 17.81–19.69s | V1 |  | — |  |  |  |
| 19.69–21.44s | V2 |  | — |  |  |  |
| 19.69–21.44s | V9 |  | Text (Vanilla extract) |  |  |  |
| 21.44–22.81s | V2 |  | — |  |  |  |
| 22.81–24.02s | V1 |  | — |  |  |  |
| 24.02–24.98s | V1 |  | — |  |  |  |
| 24.98–26.23s | V1 |  | — |  |  |  |
| 26.23–27.11s | V1 |  | — |  |  |  |
| 27.11–28.36s | V1 |  | — |  |  |  |
| 28.36–30.16s | V1 |  | — |  |  |  |
| 28.36–30.16s | V9 |  | Text (Powdered sugar) |  |  |  |
| 30.16–31.07s | V1 |  | — |  |  |  |
| 30.16–31.07s | V9 |  | Text (Cereal mixture) |  |  |  |
| 31.07–32.16s | V1 |  | — |  |  |  |
| 32.16–33.28s | V1 |  | — |  |  |  |
| 33.28–34.33s | V1 |  | — |  |  |  |
| 34.33–35.45s | V1 |  | — |  |  |  |
| 35.45–36.37s | V1 |  | — |  |  |  |
| 36.37–37.75s | V1 |  | — |  |  |  |
| 37.75–39.04s | V2 |  | — |  |  |  |
| 39.04–40.75s | V2 |  | — |  |  |  |
| 40.75–42.54s | V1 |  | — |  |  |  |
| 42.54–44.17s | V1 |  | — |  |  |  |
| 44.17–48.97s | V2 |  | — |  |  |  |
| 45.55–48.97s | V8 |  | — |  |  |  |

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=2.54s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0006.jpg`

**t=4.21s** — events: V1 cut out; V1 cut in; V8 cut in; V9 cut in; Text(Rice Chex cereal) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0007.jpg`

**t=6.01s** — events: V1 cut out; V2 cut in; V9 cut out; Text(Rice Chex cereal) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0013.jpg`

**t=6.42s** — events: V9 cut in; Text(Unsalted butter) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0034.jpg`

**t=7.55s** — events: V9 cut out; Text(Unsalted butter) ends; V9 cut in; Text(Semisweet chocolate chips) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0047.jpg`

**t=8.80s** — events: V9 cut out; Text(Semisweet chocolate chips) ends; V9 cut in; Text(Smooth peanut butter) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0062.jpg`

**t=9.97s** — events: V9 cut out; Text(Smooth peanut butter) ends; V9 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0076.jpg`

**t=11.01s** — events: V1 cut in; V2 cut out; V9 cut out; Text(Kosher salt) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0089.jpg`

**t=11.97s** — events: V1 cut out; V1 cut in; V10 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0100.jpg`

**t=12.76s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0110.jpg`

**t=13.89s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0117.jpg`

**t=15.43s** — events: V1 cut in; V2 cut out; V10 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0032.jpg`

**t=16.89s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0035.jpg`

**t=17.81s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0037.jpg`

**t=19.69s** — events: V1 cut out; V2 cut in; V9 cut in; Text(Vanilla extract) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0040.jpg`

**t=21.44s** — events: V2 cut out; V2 cut in; V9 cut out; Text(Vanilla extract) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0044.jpg`

**t=22.81s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0047.jpg`

**t=24.02s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0049.jpg`

**t=24.98s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0051.jpg`

**t=26.23s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0053.jpg`

**t=27.11s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0055.jpg`

**t=28.36s** — events: V1 cut out; V1 cut in; V9 cut in; Text(Powdered sugar) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0058.jpg`

**t=30.16s** — events: V1 cut out; V1 cut in; V9 cut out; Text(Powdered sugar) ends; V9 cut in; Text(Cereal mixture) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0124.jpg`

**t=31.07s** — events: V1 cut out; V1 cut in; V9 cut out; Text(Cereal mixture) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0135.jpg`

**t=32.16s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0141.jpg`

**t=33.28s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0068.jpg`

**t=34.33s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0070.jpg`

**t=35.45s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0072.jpg`

**t=36.37s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0074.jpg`

**t=37.75s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0076.jpg`

**t=39.04s** — events: V2 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0079.jpg`

**t=40.75s** — events: V1 cut in; V2 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0082.jpg`

**t=42.54s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_2fps/frame_0086.jpg`

**t=44.17s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0148.jpg`

**t=45.55s** — events: V8 cut out; V8 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/puppy_chow_frames_12fps/frame_0165.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
