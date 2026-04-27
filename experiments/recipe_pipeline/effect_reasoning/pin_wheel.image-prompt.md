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
| 0.92–2.00s | V1 |  | — |  |  |  |
| 2.00–3.34s | V1 |  | — |  |  |  |
| 3.34–4.71s | V1 |  | — |  |  |  |
| 3.34–63.73s | V9 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |  |
| 3.34–70.15s | V10 | ADJ | Lumetri Color |  |  |  |
| 3.34–67.03s | V11 |  | — |  |  |  |
| 3.34–4.71s | V12 |  | Text (Unsalted butter) |  |  |  |
| 4.71–6.17s | V1 |  | — |  |  | 50% |
| 4.71–6.17s | V12 |  | Text (Granulated sugar) |  |  |  |
| 6.17–7.51s | V1 |  | — |  |  | 50% |
| 6.17–7.51s | V12 |  | Text (Powdered sugar) |  |  |  |
| 7.51–8.84s | V1 |  | — |  |  | 50% |
| 7.51–8.84s | V12 |  | Text (Vanilla extract) |  |  |  |
| 8.84–10.05s | V1 |  | — |  |  | 50% |
| 8.84–10.05s | V12 |  | Text (Kosher salt) |  |  |  |
| 10.05–10.72s | V1 |  | — |  |  | RAMP (6 keyframes) |
| 10.72–11.64s | V1 |  | — |  |  |  |
| 11.64–12.72s | V1 |  | — |  |  |  |
| 12.72–15.89s | V1 |  | — |  |  |  |
| 12.72–13.76s | V12 |  | Text (All-purpose flour ) |  |  |  |
| 13.76–14.76s | V12 |  | Text (Baking powder) |  |  |  |
| 15.89–17.43s | V1 |  | — |  |  |  |
| 15.89–17.43s | V12 |  | Text (Flour mixture) |  |  |  |
| 17.43–18.39s | V1 |  | — |  |  |  |
| 18.39–19.89s | V1 |  | — |  |  |  |
| 18.85–19.89s | V2 |  | Mask2 (02) |  | static 4-vertex mask |  |
| 18.85–19.89s | V3 |  | Mask2 (02) |  | static 4-vertex mask |  |
| 19.27–19.89s | V4 |  | Mask2 (02) |  | static 4-vertex mask |  |
| 19.27–19.89s | V5 |  | Mask2 (01) |  | static 4-vertex mask |  |
| 19.89–20.77s | V1 |  | — |  |  |  |
| 19.89–22.40s | V12 |  | Text (Red gel food coloring) |  |  |  |
| 20.77–21.40s | V1 |  | — |  |  |  |
| 21.40–22.40s | V1 |  | — |  |  |  |
| 22.40–23.31s | V1 |  | — |  |  |  |
| 22.40–24.94s | V12 |  | Text (Green gel food coloring) |  |  |  |
| 23.31–24.94s | V1 |  | — |  |  |  |
| 24.94–25.69s | V1 |  | — |  |  |  |
| 25.69–26.36s | V1 |  | — |  |  |  |
| 26.36–27.11s | V1 |  | — |  |  |  |
| 27.11–27.78s | V1 |  | — |  |  |  |
| 27.78–28.74s | V1 |  | — |  |  |  |
| 28.74–29.36s | V1 |  | — |  |  |  |
| 29.36–30.28s | V1 |  | — |  |  |  |
| 30.28–32.78s | V1 |  | — |  |  |  |
| 30.28–32.78s | V2 |  | — |  |  |  |
| 30.28–32.78s | V3 |  | — |  |  |  |
| 30.28–32.78s | V12 |  | Shape (Shape 01) |  |  |  |
| 30.28–32.78s | V13 |  | Shape (Shape 01) |  |  |  |
| 31.70–32.78s | V14 |  | Graphic Parameters |  |  |  |
| 32.78–33.83s | V1 |  | — |  |  |  |
| 32.78–33.83s | V12 |  | Text (All-purpose flour) |  |  |  |
| 33.83–34.37s | V1 |  | — |  |  |  |
| 34.37–35.29s | V1 |  | — |  |  |  |
| 35.29–36.29s | V1 |  | — |  |  |  |
| 36.29–37.62s | V1 |  | — |  |  |  |
| 37.62–38.62s | V1 |  | — |  |  |  |
| 38.62–39.66s | V1 |  | — |  |  |  |
| 39.66–40.54s | V1 |  | — |  |  |  |
| 40.54–41.83s | V1 |  | — |  |  |  |
| 41.83–45.05s | V1 |  | — |  |  |  |
| 45.05–46.88s | V1 |  | — |  |  |  |
| 46.88–48.38s | V1 |  | — |  |  |  |
| 48.38–50.01s | V1 |  | — |  |  |  |
| 50.01–51.80s | V1 |  | — |  |  |  |
| 50.59–51.80s | V12 |  | Graphic Parameters | Refrigerate for 1 hour |  |  |
| 51.80–52.76s | V1 |  | — |  |  |  |
| 52.76–53.05s | V1 |  | — |  |  |  |
| 53.05–53.22s | V1 |  | — |  |  |  |
| 53.22–53.64s | V1 |  | — |  |  |  |
| 53.64–54.93s | V1 |  | — |  |  |  |
| 54.93–55.39s | V1 |  | — |  |  |  |
| 55.39–56.22s | V1 |  | — |  |  |  |
| 56.22–56.43s | V1 |  | — |  |  |  |
| 56.43–56.51s | V1 |  | — |  |  |  |
| 56.51–56.60s | V1 |  | — |  |  |  |
| 56.60–56.68s | V1 |  | — |  |  |  |
| 56.68–56.77s | V1 |  | — |  |  |  |
| 56.77–56.85s | V1 |  | — |  |  |  |
| 56.85–56.93s | V1 |  | — |  |  |  |
| 56.93–57.02s | V1 |  | — |  |  |  |
| 57.02–57.10s | V1 |  | — |  |  |  |
| 57.10–57.27s | V1 |  | — |  |  |  |
| 57.18–57.27s | V2 |  | Mask2 (01) |  | static 4-vertex mask |  |
| 57.18–57.27s | V3 |  | Mask2 (01) |  | static 4-vertex mask |  |
| 57.27–57.35s | V1 |  | — |  |  |  |
| 57.35–57.93s | V1 |  | — |  |  |  |
| 57.93–61.02s | V1 |  | — |  |  |  |
| 58.68–61.02s | V12 |  | Graphic Parameters | Bake at 350°F until cookies spread\r        slightly, about 10 minutes |  |  |
| 61.02–62.52s | V1 |  | — |  |  |  |
| 62.52–63.73s | V1 |  | Lumetri Color |  |  |  |
| 63.73–65.52s | V1 |  | Lumetri Color |  |  |  |
| 63.73–70.15s | V9 | ADJ | Lumetri Color (Green), Lumetri Color |  |  |  |
| 65.52–67.03s | V1 |  | Lumetri Color |  |  |  |
| 67.03–70.15s | V1 |  | — |  |  |  |
| 67.03–70.15s | V11 |  | — |  |  |  |

**Stacked adjustment-layer composites (overlapping adj clips on different tracks):**
- **3.34–70.15s**: V10 (Lumetri Color) stacked over V9 (Lumetri Color (Green), Lumetri Color)
- **3.34–70.15s**: V10 (Lumetri Color) stacked over V9 (Lumetri Color (Green), Lumetri Color)

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=2.00s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_2fps/frame_0005.jpg`

**t=3.34s** — events: V1 cut out; V1 cut in; V9 cut (adj) in; Lumetri Color(Green) starts; Lumetri Color starts; V10 cut (adj) in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0007.jpg`

**t=4.71s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Unsalted butter) ends; V12 cut in; Text(Granulated sugar) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0024.jpg`

**t=6.17s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Granulated sugar) ends; V12 cut in; Text(Powdered sugar) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0041.jpg`

**t=7.51s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Powdered sugar) ends; V12 cut in; Text(Vanilla extract) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0057.jpg`

**t=8.84s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Vanilla extract) ends; V12 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0073.jpg`

**t=10.05s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Kosher salt) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0088.jpg`

**t=10.72s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0096.jpg`

**t=11.64s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0107.jpg`

**t=12.72s** — events: V1 cut out; V1 cut in; V12 cut in; Text(All-purpose flour ) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0120.jpg`

**t=13.76s** — events: V12 cut out; Text(All-purpose flour ) ends; V12 cut in; Text(Baking powder) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0132.jpg`

**t=14.76s** — events: V12 cut out; Text(Baking powder) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0144.jpg`

**t=15.89s** — events: V1 cut out; V1 cut in; V12 cut in; Text(Flour mixture) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0158.jpg`

**t=17.43s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Flour mixture) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0176.jpg`

**t=18.39s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0188.jpg`

**t=18.85s** — events: V2 cut in; Mask2(02) starts; V3 cut in; Mask2(02) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0193.jpg`

**t=19.27s** — events: V4 cut in; Mask2(02) starts; V5 cut in; Mask2(01) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0198.jpg`

**t=19.89s** — events: V1 cut out; V1 cut in; V2 cut out; Mask2(02) ends; V3 cut out; Mask2(02) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0206.jpg`

**t=20.77s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0216.jpg`

**t=21.40s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0224.jpg`

**t=22.40s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Red gel food coloring) ends; V12 cut in; Text(Green gel food coloring) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0236.jpg`

**t=23.31s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0247.jpg`

**t=24.94s** — events: V1 cut out; V1 cut in; V12 cut out; Text(Green gel food coloring) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0266.jpg`

**t=30.28s** — events: V1 cut out; V1 cut in; V2 cut in; V3 cut in; V12 cut in; Shape(Shape 01) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0330.jpg`

**t=32.78s** — events: V1 cut out; V1 cut in; V2 cut out; V3 cut out; V12 cut out; Shape(Shape 01) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0360.jpg`

**t=33.83s** — events: V1 cut out; V1 cut in; V12 cut out; Text(All-purpose flour) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0373.jpg`

**t=51.80s** — events: V1 cut out; V1 cut in; V12 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0589.jpg`

**t=52.76s** — events: V1 cut out; V1 cut in; V1 cut out; V1 cut in; V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0600.jpg`

**t=56.22s** — events: V1 cut out; V1 cut in; V1 cut out; V1 cut in; V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0642.jpg`

**t=61.02s** — events: V1 cut out; V1 cut in; V12 cut out; Graphic Parameters ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0699.jpg`

**t=62.52s** — events: V1 cut out; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0717.jpg`

**t=63.73s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts; V9 cut (adj) out; Lumetri Color(Green) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0732.jpg`

**t=65.52s** — events: V1 cut out; Lumetri Color ends; V1 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0753.jpg`

**t=67.03s** — events: V1 cut out; Lumetri Color ends; V1 cut in; V11 cut out; V11 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0771.jpg`

**t=70.15s** — events: V1 cut out; V9 cut (adj) out; Lumetri Color(Green) ends; Lumetri Color ends; V10 cut (adj) out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/pin_wheel_frames_12fps/frame_0807.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
