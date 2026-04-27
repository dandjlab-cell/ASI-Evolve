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
| 0.13–0.21s | V2 |  | Lumetri Color |  |  |  |
| 0.21–0.29s | V2 |  | Lumetri Color |  |  |  |
| 0.29–0.38s | V2 |  | Lumetri Color |  |  |  |
| 0.38–0.46s | V2 |  | Lumetri Color |  |  |  |
| 0.46–0.54s | V2 |  | Lumetri Color |  |  |  |
| 0.54–0.63s | V2 |  | Lumetri Color |  |  |  |
| 0.63–0.67s | V2 |  | Lumetri Color |  |  |  |
| 0.67–0.75s | V2 |  | Lumetri Color |  |  |  |
| 0.75–0.83s | V2 |  | Lumetri Color |  |  |  |
| 0.83–0.92s | V2 |  | Lumetri Color |  |  |  |
| 0.92–1.00s | V2 |  | Lumetri Color |  |  |  |
| 1.00–1.08s | V2 |  | Lumetri Color |  |  |  |
| 1.08–1.17s | V2 |  | Lumetri Color |  |  |  |
| 1.17–1.71s | V2 |  | Lumetri Color |  |  |  |
| 1.71–3.34s | V1 |  | — |  |  |  |
| 3.34–4.55s | V2 |  | — |  |  |  |
| 3.34–36.45s | V6 | ADJ | Lumetri Color |  |  |  |
| 3.34–32.78s | V7 |  | — |  |  |  |
| 3.34–4.55s | V8 |  | Text (English cucumber) |  |  |  |
| 4.55–5.80s | V1 |  | — |  |  |  |
| 5.80–6.63s | V2 |  | — |  |  |  |
| 6.63–6.72s | V2 |  | — |  |  |  |
| 6.72–6.80s | V2 |  | — |  |  |  |
| 6.80–6.88s | V2 |  | — |  |  |  |
| 6.88–6.97s | V2 |  | — |  |  |  |
| 6.97–7.05s | V2 |  | — |  |  |  |
| 7.05–7.13s | V2 |  | — |  |  |  |
| 7.13–7.59s | V2 |  | — |  |  |  |
| 7.59–8.76s | V1 |  | — |  |  |  |
| 7.59–8.76s | V8 |  | Text (Kosher salt) |  |  |  |
| 8.76–10.18s | V1 |  | — |  |  |  |
| 10.18–12.64s | V1 |  | — |  |  |  |
| 10.18–12.64s | V8 |  | Graphic Parameters | Let cucumbers drain,\r30 minutes to 1 hour |  |  |
| 12.64–13.85s | V2 |  | — |  |  |  |
| 12.64–13.85s | V8 |  | Text (Cream cheese) |  |  |  |
| 13.85–14.81s | V1 |  | — |  |  |  |
| 13.85–14.81s | V8 |  | Text (Fresh dill) |  |  |  |
| 14.81–16.02s | V1 |  | — |  |  |  |
| 14.81–16.02s | V8 |  | Text (Fresh chives) |  |  |  |
| 16.02–17.10s | V1 |  | — |  |  |  |
| 16.02–17.10s | V8 |  | Text (Mayonnaise) |  |  |  |
| 17.10–18.10s | V1 |  | — |  |  |  |
| 17.10–18.10s | V8 |  | Text (Kosher salt) |  |  |  |
| 18.10–19.06s | V1 |  | — |  |  |  |
| 18.10–19.06s | V8 |  | Text (Freshly ground black pepper) |  |  |  |
| 19.06–19.94s | V1 |  | — |  |  |  |
| 19.94–20.60s | V1 |  | — |  |  |  |
| 20.60–21.77s | V1 |  | — |  |  |  |
| 21.77–22.94s | V2 |  | Lumetri Color |  |  |  |
| 21.77–22.94s | V8 |  | Text (White sandwich bread) |  |  |  |
| 22.94–23.82s | V1 |  | — |  |  |  |
| 22.94–24.61s | V8 |  | Text (Cream cheese mixture) |  |  |  |
| 23.82–24.61s | V2 |  | Lumetri Color |  |  |  |
| 24.61–24.73s | V2 |  | Lumetri Color |  |  |  |
| 24.73–24.82s | V2 |  | Lumetri Color |  |  |  |
| 24.82–24.90s | V2 |  | Lumetri Color |  |  |  |
| 24.90–24.98s | V2 |  | Lumetri Color |  |  |  |
| 24.98–25.07s | V2 |  | Lumetri Color |  |  |  |
| 25.07–25.15s | V2 |  | Lumetri Color |  |  |  |
| 25.15–25.23s | V2 |  | Lumetri Color |  |  |  |
| 25.23–25.28s | V2 |  | Lumetri Color |  |  |  |
| 25.28–25.36s | V2 |  | Lumetri Color |  |  |  |
| 25.36–25.44s | V2 |  | Lumetri Color |  |  |  |
| 25.44–25.53s | V2 |  | Lumetri Color |  |  |  |
| 25.53–25.61s | V2 |  | Lumetri Color |  |  |  |
| 25.61–25.69s | V2 |  | Lumetri Color |  |  |  |
| 25.69–25.78s | V2 |  | Lumetri Color |  |  |  |
| 25.78–26.61s | V2 |  | Lumetri Color |  |  |  |
| 26.61–27.36s | V1 |  | — |  |  |  |
| 27.36–28.11s | V1 |  | — |  |  |  |
| 28.11–28.95s | V1 |  | — |  |  |  |
| 28.95–29.74s | V1 |  | — |  |  |  |
| 29.74–30.78s | V1 |  | — |  |  |  |
| 30.78–32.78s | V1 |  | — |  |  |  |
| 32.78–36.45s | V1 |  | — |  |  |  |
| 32.78–36.45s | V7 |  | — |  |  |  |

---

### FRAME_ANALYSIS

Below are the rendered final-cut frames at every meaningful editorial boundary in this recipe.

**You MUST read each image with the Read tool before reasoning about its moment.** Do not skip frames — the visual evidence is the point of this analysis.


**t=0.13s** — events: V2 cut in; Lumetri Color starts; V2 cut out; Lumetri Color ends; V2 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0003.jpg`

**t=1.71s** — events: V1 cut in; V2 cut out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0022.jpg`

**t=3.34s** — events: V1 cut out; V2 cut in; V6 cut (adj) in; Lumetri Color starts; V7 cut in; V8 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0038.jpg`

**t=4.55s** — events: V1 cut in; V2 cut out; V8 cut out; Text(English cucumber) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0053.jpg`

**t=5.80s** — events: V1 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0062.jpg`

**t=6.63s** — events: V2 cut out; V2 cut in; V2 cut out; V2 cut in; V2 cut out; V2 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0072.jpg`

**t=7.59s** — events: V1 cut in; V2 cut out; V8 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0084.jpg`

**t=8.76s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Kosher salt) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0095.jpg`

**t=10.18s** — events: V1 cut out; V1 cut in; V8 cut in; Graphic Parameters starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0021.jpg`

**t=12.64s** — events: V1 cut out; V2 cut in; V8 cut out; Graphic Parameters ends; V8 cut in; Text(Cream cheese) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0096.jpg`

**t=13.85s** — events: V1 cut in; V2 cut out; V8 cut out; Text(Cream cheese) ends; V8 cut in; Text(Fresh dill) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0102.jpg`

**t=14.81s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Fresh dill) ends; V8 cut in; Text(Fresh chives) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0114.jpg`

**t=16.02s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Fresh chives) ends; V8 cut in; Text(Mayonnaise) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0033.jpg`

**t=17.10s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Mayonnaise) ends; V8 cut in; Text(Kosher salt) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0120.jpg`

**t=18.10s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Kosher salt) ends; V8 cut in; Text(Freshly ground black pepper) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0126.jpg`

**t=19.06s** — events: V1 cut out; V1 cut in; V8 cut out; Text(Freshly ground black pepper) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0138.jpg`

**t=19.94s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0041.jpg`

**t=20.60s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0042.jpg`

**t=21.77s** — events: V1 cut out; V2 cut in; Lumetri Color starts; V8 cut in; Text(White sandwich bread) starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0144.jpg`

**t=22.94s** — events: V1 cut in; V2 cut out; Lumetri Color ends; V8 cut out; Text(White sandwich bread) ends; V8 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0150.jpg`

**t=23.82s** — events: V1 cut out; V2 cut in; Lumetri Color starts
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0161.jpg`

**t=24.61s** — events: V2 cut out; Lumetri Color ends; V2 cut in; Lumetri Color starts; V8 cut out; Text(Cream cheese mixture) ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0170.jpg`

**t=26.61s** — events: V1 cut in; V2 cut out; Lumetri Color ends
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0194.jpg`

**t=27.36s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_12fps/frame_0200.jpg`

**t=28.11s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0057.jpg`

**t=28.95s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0059.jpg`

**t=29.74s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0060.jpg`

**t=30.78s** — events: V1 cut out; V1 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0063.jpg`

**t=32.78s** — events: V1 cut out; V1 cut in; V7 cut out; V7 cut in
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0067.jpg`

**t=36.45s** — events: V1 cut out; V6 cut (adj) out; Lumetri Color ends; V7 cut out
  Read this frame: `/Users/dandj/DevApps/storyboard-gen/docs/watch-video/cucumber_tea_frames_2fps/frame_0073.jpg`

---

### EXISTING_ANNOTATION

(intentionally omitted — derive editorial reasoning from PRPROJ_EFFECTS and the EMBEDDED FRAME IMAGES you Read above)
